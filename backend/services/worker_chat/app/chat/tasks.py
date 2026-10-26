"""
worker_chat/app/chat/tasks.py

Chat task using the Gemini API (google-genai SDK) with the File Search tool.
Replaces the LangChain/ChromaDB retrieval chain entirely.

Key changes:
- Single generate_content() call handles retrieval + generation atomically
- Conversation history passed natively (no LangChain message wrappers)
- Token usage read from response.usage_metadata (no callback needed)
- Fine-tune rules injected directly into the system instruction
- Citations extracted from grounding_metadata and returned to the frontend
"""
import os
import re
import unicodedata
from urllib.parse import urlparse
from datetime import date, timedelta

from celery import shared_task
from google import genai

from app.database.supabase_client import fetch_all, supabase
from app.billing.services import BillingService
from app.logging_config import error_logger
from app.prompts import FINE_TUNE_RULE_PROMPT
from app.ai_models import CHAT_GEMINI_MODEL, billable_tokens
from app.knowledge.calendar import dedupe_events, source_rank
from app.knowledge.contact import contact_context


# Number of previous exchanges (user + AI message pairs) sent as context.
HISTORY_TURNS = int(os.getenv("CHAT_HISTORY_TURNS", "10"))
# Per-request timeout for the Gemini call, in milliseconds (google-genai unit).
GEMINI_TIMEOUT_MS = int(os.getenv("CHAT_GEMINI_TIMEOUT_MS", "90000"))

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            api_key=os.environ["GOOGLE_API_KEY"],
            http_options={"timeout": GEMINI_TIMEOUT_MS},
        )
    return _client


def _build_contents(chat_history_json: list, query: str) -> list:
    """
    Converts the chat history + current query into the google-genai contents format:
    [{"role": "user"|"model", "parts": [{"text": "..."}]}, ...]
    """
    contents = []
    for msg in chat_history_json:
        role = "user" if msg["type"] == "human" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    # Gemini requires the last message to be from "user"
    contents.append({"role": "user", "parts": [{"text": query}]})
    return contents


def _load_history(tenant_id: str, conversation_id: str) -> list:
    """
    Loads the last HISTORY_TURNS exchanges of this conversation from chat_logs.
    History is never taken from the client: a public caller could otherwise
    send megabytes of fake turns and bill the tenant owner for the tokens.
    """
    response = (
        supabase.table("chat_logs")
        .select("user_message, ai_message")
        .eq("tenant_id", str(tenant_id))
        .eq("conversation_id", str(conversation_id))
        .order("created_at", desc=True)
        .limit(HISTORY_TURNS)
        .execute()
    )
    history = []
    for row in reversed(response.data or []):
        history.append({"type": "human", "content": row["user_message"]})
        history.append({"type": "ai", "content": row["ai_message"]})
    return history


_WEEKDAY = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
# Upcoming dates per series given to the model; enough for "next" / "this week"
_UPCOMING_PER_SERIES = 4
_MAX_SERIES = 30


def _calendars_offered(tenant_config: dict) -> bool:
    # same rule as the public feed: on, enabled and not password-protected
    return bool(tenant_config.get("calendar_feeds")) and not tenant_config.get("test_password_hash") \
        and tenant_config.get("is_active") is not False


def _calendar_key(series: str, zone: str) -> str:
    """Same as app/knowledge/calendar.py calendar_key (that package isn't in this service)."""
    def slug(text):
        text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug(series) + (f"--{slug(zone)}" if zone else "")


def _dates_context(tenant_id: str, today: date, offer_calendars: bool = False, sources_out: dict | None = None) -> str:
    """
    Today's date plus verified dates extracted at indexing time (tenant_events):
    the next few per series, or — when a series has no future dates — when its
    data ends, so the model doesn't present an expired calendar as current.
    """
    lines = [f"Today is {_WEEKDAY[today.weekday()]} {today.isoformat()}."]
    rows = fetch_all(lambda: (
        supabase.table("tenant_events")
        .select("series, zone, event_date, is_exception, notes, source_id")
        .eq("tenant_id", str(tenant_id))
        .gte("event_date", (today - timedelta(days=400)).isoformat())
        .lte("event_date", (today + timedelta(days=400)).isoformat())
        .order("event_date").order("id")
    ), max_rows=20_000)
    if not rows:
        return lines[0]

    # the same event read from several pages counts once; its source is the most specific page
    source_ids = list({r["source_id"] for r in rows if r.get("source_id")})
    source_rows = {}
    for i in range(0, len(source_ids), 200):
        for s in supabase.table("tenant_sources").select("id, title, source_location") \
                .in_("id", source_ids[i:i + 200]).execute().data or []:
            source_rows[s["id"]] = s

    rows = dedupe_events(rows, lambda r: source_rank(r, source_rows.get(r.get("source_id"))))

    series: dict[tuple[str, str], dict] = {}
    for r in rows:
        entry = series.setdefault((r["series"], r["zone"]), {"upcoming": [], "last": None, "notes": r.get("notes") or "",
                                                             "source_id": r.get("source_id")})
        d = date.fromisoformat(r["event_date"])
        if d >= today:
            if len(entry["upcoming"]) < _UPCOMING_PER_SERIES:
                entry["upcoming"].append(f"{_WEEKDAY[d.weekday()]} {d.isoformat()}" + (" (exception)" if r["is_exception"] else ""))
        else:
            entry["last"] = d

    sources = {sid: f"{(s.get('title') or '').strip()} {s['source_location']}".strip() for sid, s in source_rows.items()}
    if sources_out is not None:
        # series name -> (title, url), for the source fallback after answering
        for (name, _zone), entry in series.items():
            s = source_rows.get(entry["source_id"])
            if s:
                sources_out[name] = ((s.get("title") or s["source_location"]).strip(), s["source_location"])

    lines.append("Verified dates from this organisation's documents (use these for questions about dates; never invent dates):")
    for (name, zone), entry in list(series.items())[:_MAX_SERIES]:
        label = f"{name} ({zone})" if zone else name
        notes = f" [{entry['notes']}]" if entry["notes"] else ""
        if entry["upcoming"]:
            key = f" {{calendar: {_calendar_key(name, zone)}}}" if offer_calendars else ""
            source = f" {{source: {sources[entry['source_id']]}}}" if entry["source_id"] in sources else ""
            lines.append(f"- {label}{notes}{key}{source}: next {', '.join(entry['upcoming'])}")
        elif entry["last"]:
            lines.append(f"- {label}{notes}: no future dates known — the published schedule ends "
                         f"{entry['last'].isoformat()}; say so instead of guessing.")
    if offer_calendars:
        lines.append(
            "Residents can subscribe to these dates in their own calendar. When your answer gives dates "
            "of a series that has a {calendar: KEY}, add the line [[calendar:KEY]] at the very end of your "
            "answer, once per series you gave dates for (at most three). Never mention the key or this "
            "marker in your text; the chat turns it into a button."
        )
    return "\n".join(lines)


def _build_system_instruction(tenant_config: dict, fine_tune_rules: list) -> str:
    """
    Assembles the full system instruction from the tenant's RAG prompt template,
    persona, and fine-tune rules.
    """
    fine_tune_instructions = "\n".join([
        FINE_TUNE_RULE_PROMPT.format(
            trigger=rule["trigger"], instruction=rule["instruction"]
        )
        for rule in fine_tune_rules
    ])

    persona = tenant_config.get("system_persona") or ""
    template = _strip_legacy_placeholders(tenant_config.get("rag_prompt_template") or "")
    # The persona and rules must reach the model even if someone edited them out
    if "{persona}" not in template:
        template = "{persona}\n\n" + template
    if "{fine_tune_instructions}" not in template:
        template = template.replace("{persona}", "{persona}\n\n{fine_tune_instructions}", 1)

    system_text = (
        template
        .replace("{persona}", persona)
        .replace("{fine_tune_instructions}", fine_tune_instructions)
    )
    return re.sub(r"\n{3,}", "\n\n", system_text).strip()


_SOURCES_RULE = (
    "Sources: don't name or link the documents you used; links to them are added to your answer "
    "automatically. A link inside the answer is fine only for a form or page the visitor should open; "
    "take its address from that document's \"Quelle:\" line."
)

_UNKNOWN_RULE = (
    "When you don't know something: say so in one short sentence, without mentioning documents, sources "
    "or what you were given (never \"in den vorliegenden Dokumenten …\" or similar), then give the most "
    "fitting contact straight away: the office, its phone, email and opening hours if you know them. "
    "No apologies, no \"I recommend\"."
)

_MD_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


def _known_source_urls(tenant_id: str) -> dict[str, str]:
    """url → title of every source of the tenant (a dict, so `in` works like a set)."""
    rows = fetch_all(lambda: supabase.table("tenant_sources").select("source_location, title")
                     .eq("tenant_id", str(tenant_id)).order("id"))
    return {r["source_location"]: (r.get("title") or "") for r in rows if r.get("source_location")}


_QUOTES = str.maketrans({c: '"' for c in "„“”«»‹›‚‘’'"})
_MIN_TITLE_MATCH = 10   # shorter titles ("Papier", "Glas") would match by accident


def _named_page(line: str, known: dict) -> tuple[str, str] | None:
    """The page a line is about, if it names one by its title, e.g. an event listed on the home page."""
    text = line.translate(_QUOTES).lower()
    best = None
    for url, title in known.items():
        t = (title or "").translate(_QUOTES).lower().strip()
        if len(t) >= _MIN_TITLE_MATCH and t in text and urlparse(url).path not in ("", "/"):
            if best is None or len(t) > len(best[0]):
                best = (t, (title, url))
    return best[1] if best else None


def _keep_known_links(answer: str, known: set[str]) -> str:
    """Links to anything but the organisation's own sources become plain text (no invented URLs)."""
    return _MD_LINK.sub(lambda m: m.group(0) if m.group(2) in known else m.group(1), answer)


_QUELLE = re.compile(r"Quelle:\s*(https?://\S+)")


def _chunk_source(chunk) -> tuple[str, str] | None:
    """(title, url) of one File Search chunk: the url from the document's metadata, else its "Quelle:" line."""
    ctx = getattr(chunk, "retrieved_context", None)
    if not ctx:
        return None
    url = next((m.string_value for m in getattr(ctx, "custom_metadata", None) or []
                if getattr(m, "key", None) == "source_url" and m.string_value), None)
    if not url:
        m = _QUELLE.search(getattr(ctx, "text", None) or "")
        url = m.group(1) if m else None
    if not url:
        return None
    title = (getattr(ctx, "title", None) or url).split(" — ")[0].strip()
    return title, url


def _retrieved_sources(response) -> list[tuple[str, str]]:
    """
    (title, url) of the documents the answer actually rests on, in the order
    the answer uses them (grounding supports). Without supports: everything
    File Search handed the model.
    """
    try:
        meta = response.candidates[0].grounding_metadata
        chunks = meta.grounding_chunks or []
        supports = sorted(meta.grounding_supports or [],
                          key=lambda s: getattr(getattr(s, "segment", None), "start_index", 0) or 0)
        order = [i for s in supports for i in (s.grounding_chunk_indices or [])] or list(range(len(chunks)))
        found = [_chunk_source(chunks[i]) for i in order if 0 <= i < len(chunks)]
        return [f for f in found if f]
    except (AttributeError, IndexError, TypeError):
        return []


def _source_links(candidates: list[tuple[str, str]], known: set[str], limit: int = 3) -> list[str]:
    """Markdown links, each document once; the home page only when nothing more specific was used."""
    seen, picked = set(), []
    for title, url in candidates:
        if url in known and url not in seen:
            seen.add(url)
            picked.append((title, url))
    specific = [p for p in picked if urlparse(p[1]).path not in ("", "/")]
    return [_chip(t, u) for t, u in (specific or picked)[:limit]]


_SOURCES_MARKER = "[[sources]]"
# a source link in the answer: [short title](url "source: full title"); the widget shows it as a chip
_CHIP_TITLE_CHARS = 32


def _chip(title: str, url: str) -> str:
    title = " ".join(title.split()).replace("[", "(").replace("]", ")")
    short = title if len(title) <= _CHIP_TITLE_CHARS else title[:_CHIP_TITLE_CHARS - 1].rstrip() + "…"
    # only the markdown title needs its quotes swapped
    return f'[{short}]({url} "source: {title.replace(chr(34), chr(39))}")'


def _inline_sources(answer: str, response, known: set[str]) -> tuple[str, set[str]]:
    """
    Puts a link to the source at the end of each line that rests on it (from
    Gemini's grounding supports). Each document once, at its first use; the
    home page only where nothing more specific backs the line. Returns the
    answer and the urls linked.
    """
    try:
        meta = response.candidates[0].grounding_metadata
        chunks = meta.grounding_chunks or []
        supports = meta.grounding_supports or []
    except (AttributeError, IndexError, TypeError):
        return answer, set()
    if not supports or not chunks:
        return answer, set()
    raw = answer.encode("utf-8")
    by_line: dict[int, list[tuple[str, str]]] = {}
    linked: set[str] = set()
    for s in sorted(supports, key=lambda s: getattr(getattr(s, "segment", None), "end_index", 0) or 0):
        seg = getattr(s, "segment", None)
        if seg is None or (getattr(seg, "part_index", 0) or 0) != 0:
            continue
        sources = [_chunk_source(chunks[i]) for i in (s.grounding_chunk_indices or []) if 0 <= i < len(chunks)]
        sources = [x for x in sources if x and x[1] in known]
        specific = [x for x in sources if urlparse(x[1]).path not in ("", "/")]
        # segment offsets are bytes; the link goes at the end of that line
        end = len(raw[: getattr(seg, "end_index", 0) or 0].decode("utf-8", errors="ignore"))
        line_end = answer.find("\n", max(0, end - 1))
        line_end = len(answer) if line_end == -1 else line_end
        line_start = answer.rfind("\n", 0, line_end) + 1
        if not specific and isinstance(known, dict):
            # backed only by an overview (the home page): the line's own page, if it names one
            named = _named_page(answer[line_start:line_end], known)
            specific = [named] if named else []
        pick = next((x for x in (specific or sources) if x[1] not in linked), None)
        if not pick:
            continue
        if answer[line_start:line_end].lstrip().startswith("|"):
            continue   # a link after a table row would break the table
        if len(by_line.setdefault(line_end, [])) < 2:
            by_line[line_end].append(pick)
            linked.add(pick[1])
    for pos in sorted(by_line, reverse=True):
        chips = " ".join(_chip(t, u) for t, u in by_line[pos])
        answer = answer[:pos].rstrip() + " " + chips + answer[pos:]
    return answer, linked


def _ensure_source(answer: str, candidates: list[tuple[str, str]], known: set[str]) -> str:
    """
    Fills the model's "Quelle: [[sources]]" line with the documents the answer
    used. If the model forgot the line, the links are appended anyway.
    """
    links = _source_links(candidates, known)
    if _SOURCES_MARKER in answer:
        if links:
            return answer.replace(_SOURCES_MARKER, " ".join(links), 1).replace(_SOURCES_MARKER, "")
        # nothing to link: drop the whole "Quelle: [[sources]]" line
        return re.sub(r"[^\n]*\[\[sources\]\][^\n]*\n?", "", answer).rstrip()
    if any(m.group(2) in known for m in _MD_LINK.finditer(answer)) or not links:
        return answer
    # before any calendar markers, which have to stay last
    body, markers = re.match(r"(.*?)((?:\s*\[\[calendar:[a-z0-9-]+\]\])*)\s*$", answer, re.S).groups()
    return f"{body.rstrip()}\n\n{' '.join(links[:3])}{markers}"


def _language_rule() -> str:
    """
    Always last, so it wins over a persona or template written in one language:
    answer in whatever language the visitor writes, not the documents' language.
    """
    return (
        "Language: always reply in the language of the user's most recent message, "
        "even when your documents and these instructions are in another language "
        "(e.g. a question in Ukrainian gets an answer in Ukrainian). Translate the content "
        "you found; keep names of places, streets, offices and documents as written, and "
        "give dates in the reply language. If the language of the message is unclear "
        "(only a name, number or single word), reply in the language of your documents."
    )


# Older templates carried LangChain-era slots; documents now come through
# File Search and the question is the user turn, so these would reach the
# model as literal text.
_LEGACY_CONTEXT = re.compile(r"<context>\s*\{context\}\s*</context>", re.IGNORECASE)
_LEGACY_INPUT_LINE = re.compile(r"^[^\n{]*\{input\}[^\n]*$", re.MULTILINE)


def _strip_legacy_placeholders(template: str) -> str:
    template = _LEGACY_CONTEXT.sub("", template)
    template = _LEGACY_INPUT_LINE.sub("", template)
    return template.replace("{context}", "")


def _extract_citations(response) -> list[dict]:
    """
    Pulls grounding metadata from the Gemini response.
    Returns a list of citation dicts with title, page_number, and snippet.
    """
    citations = []
    try:
        grounding = response.candidates[0].grounding_metadata
        if not grounding:
            return citations
        for chunk in grounding.grounding_chunks:
            ctx = getattr(chunk, "retrieved_context", None)
            if not ctx:
                continue
            citations.append({
                "title": getattr(ctx, "title", None),
                "page_number": getattr(ctx, "page_number", None),
                "snippet": (getattr(ctx, "text", None) or "")[:200] or None,
            })
    except (AttributeError, IndexError):
        pass
    return citations


@shared_task(bind=True, queue="chat", soft_time_limit=110, time_limit=120)
def chat_task(self, tenant_id, query, chat_history_json, conversation_id, user_id=None):
    """
    Celery task to handle a chat turn using Gemini with the File Search tool.

    Returns:
        {
            "answer": str,
            "chat_history": [...],   # updated history including this turn
            "citations": [...],      # grounding sources used by the model
        }
    """
    try:
        client = _get_client()

        # --- Fetch tenant config ---
        tenant_response = (
            supabase.table("tenants")
            .select("*")
            .eq("id", str(tenant_id))
            .single()
            .execute()
        )
        if not tenant_response.data:
            raise Exception(f"Tenant '{tenant_id}' not found")
        tenant_config = tenant_response.data

        # --- Fetch fine-tune rules ---
        fine_tune_response = (
            supabase.table("tenant_fine_tune")
            .select("*")
            .eq("tenant_id", str(tenant_id))
            .execute()
        )
        fine_tune_rules = fine_tune_response.data or []

        # --- Build system instruction ---
        system_instruction = _build_system_instruction(tenant_config, fine_tune_rules)
        date_sources: dict[str, tuple[str, str]] = {}
        try:
            system_instruction += "\n\n" + _dates_context(
                tenant_id, date.today(), offer_calendars=_calendars_offered(tenant_config), sources_out=date_sources)
        except Exception as e:
            error_logger.warning("chat_task: dates context unavailable for tenant %s: %s", tenant_id, e)
        contact_card = tenant_config.get("contact_card") or None
        if contact_card:
            system_instruction += "\n\n" + contact_context(contact_card)
        system_instruction += "\n\n" + _SOURCES_RULE + "\n\n" + _UNKNOWN_RULE + "\n\n" + _language_rule()

        # --- Build tool config ---
        # Only attach file_search if the tenant has an indexed store
        tools = []
        store_name = tenant_config.get("gemini_file_store_name")
        if store_name:
            tools = [{"file_search": {"file_search_store_names": [store_name]}}]
        else:
            error_logger.info(
                "chat_task: no File Search store for tenant %s — answering from base knowledge",
                tenant_id,
            )

        # --- Build contents (conversation history + current query) ---
        # chat_history_json is ignored (kept in the signature for queued tasks
        # from older API versions); history comes from the database.
        chat_history_json = _load_history(tenant_id, conversation_id)
        # Strip leading model messages — Gemini requires first message to be "user"
        history = list(chat_history_json)
        while history and history[0].get("type") != "human":
            history.pop(0)

        contents = _build_contents(history, query)

        # --- Generate ---
        response = client.models.generate_content(
            model=CHAT_GEMINI_MODEL,
            contents=contents,
            config={
                "system_instruction": system_instruction,
                "tools": tools,
            },
        )

        ai_message = response.text or ""
        try:
            known = _known_source_urls(tenant_id)
            if contact_card and contact_card.get("maps_url"):
                known[contact_card["maps_url"]] = ""   # the address's map link is ours, not invented
            ai_message = _keep_known_links(ai_message, known)
            mentioned = [src for name, src in date_sources.items() if name.lower() in ai_message.lower()]
            ai_message, linked = _inline_sources(ai_message, response, known)
            if linked:
                ai_message = _ensure_source(ai_message, [], known)   # only drops a stray [[sources]] line
            else:
                # nothing to attach inline (e.g. an answer from the verified dates): one line at the end,
                # verified dates naming their document first
                ai_message = _ensure_source(ai_message, mentioned + _retrieved_sources(response), known)
        except Exception as e:
            error_logger.warning("chat_task: source links skipped for tenant %s: %s", tenant_id, e)

        # --- Token usage ---
        usage = getattr(response, "usage_metadata", None)
        if usage:
            # includes File Search context (input) and thinking (output), as billed
            input_tokens, output_tokens = billable_tokens(usage)
        else:
            # Fallback estimation
            input_tokens = len(query + str(chat_history_json)) // 4
            output_tokens = len(ai_message) // 4
            error_logger.warning("chat_task: usage_metadata unavailable for tenant %s — estimating", tenant_id)

        # --- Citations ---
        citations = _extract_citations(response)

        # --- Billing ---
        cost = 0.0
        if user_id and user_id != "None":
            cost = BillingService.deduct_cost(user_id, "chat", input_tokens, output_tokens)

        # --- Log to DB ---
        try:
            supabase.table("chat_logs").insert({
                "tenant_id": tenant_id,
                "conversation_id": conversation_id,
                "user_message": query,
                "ai_message": ai_message,
                "model_used": CHAT_GEMINI_MODEL,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_chf": cost,
            }).execute()
        except Exception as db_error:
            error_logger.error(
                "chat_task: DB log failed for tenant %s: %s", tenant_id, db_error, exc_info=True
            )

        # --- Build updated history ---
        updated_history = list(chat_history_json) + [
            {"type": "human", "content": query},
            {"type": "ai", "content": ai_message},
        ]

        return {
            "answer": ai_message,
            "chat_history": updated_history,
            "citations": citations,
        }

    except Exception as e:
        error_logger.error("chat_task: error for tenant %s: %s", tenant_id, e, exc_info=True)
        raise
