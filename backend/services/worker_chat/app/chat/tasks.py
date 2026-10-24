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
from datetime import date, timedelta

from celery import shared_task
from google import genai

from app.database.supabase_client import fetch_all, supabase
from app.billing.services import BillingService
from app.logging_config import error_logger
from app.prompts import FINE_TUNE_RULE_PROMPT
from app.ai_models import CHAT_GEMINI_MODEL


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

    source_ids = list({e["source_id"] for e in series.values() if e["source_id"]})
    source_rows = {
        s["id"]: s for s in (supabase.table("tenant_sources").select("id, title, source_location")
                             .in_("id", source_ids).execute().data or [])
    } if source_ids else {}
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
    "Sources: whenever your answer uses information from a document (dates, phone numbers, opening hours, "
    "fees, anything), end with one short line naming it as a "
    "markdown link, e.g. \"Quelle: [Abfallkalender 2026](https://…)\" (in the reply language). Take the address "
    "only from the document's \"Quelle:\" line or from a {source: …} given with the dates; never make one up. "
    "Link each document at most once, at most three documents."
)

_MD_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


def _known_source_urls(tenant_id: str) -> set[str]:
    rows = fetch_all(lambda: supabase.table("tenant_sources").select("source_location")
                     .eq("tenant_id", str(tenant_id)).order("id"))
    return {r["source_location"] for r in rows if r.get("source_location")}


def _keep_known_links(answer: str, known: set[str]) -> str:
    """Links to anything but the organisation's own sources become plain text (no invented URLs)."""
    return _MD_LINK.sub(lambda m: m.group(0) if m.group(2) in known else m.group(1), answer)


_QUELLE = re.compile(r"Quelle:\s*(https?://\S+)")


def _retrieved_sources(response) -> list[tuple[str, str]]:
    """(title, url) of the documents File Search handed the model, from their "Quelle:" line."""
    found = []
    try:
        for chunk in response.candidates[0].grounding_metadata.grounding_chunks or []:
            ctx = getattr(chunk, "retrieved_context", None)
            m = _QUELLE.search(getattr(ctx, "text", None) or "") if ctx else None
            if m:
                title = (getattr(ctx, "title", None) or m.group(1)).split(" — ")[0].strip()
                found.append((title, m.group(1)))
    except (AttributeError, IndexError, TypeError):
        pass
    return found


def _ensure_source(answer: str, candidates: list[tuple[str, str]], known: set[str]) -> str:
    """Every answer drawn from documents ends with a link to one, even if the model forgot."""
    if any(m.group(2) in known for m in _MD_LINK.finditer(answer)):
        return answer
    seen, links = set(), []
    for title, url in candidates:
        if url in known and url not in seen:
            seen.add(url)
            links.append(f"[{title.replace(']', ')')}]({url})")
    if not links:
        return answer
    # before any calendar markers, which have to stay last
    body, markers = re.match(r"(.*?)((?:\s*\[\[calendar:[a-z0-9-]+\]\])*)\s*$", answer, re.S).groups()
    return f"{body.rstrip()}\n\n↗ {', '.join(links[:3])}{markers}"


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
        system_instruction += "\n\n" + _SOURCES_RULE + "\n\n" + _language_rule()

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
            ai_message = _keep_known_links(ai_message, known)
            mentioned = [src for name, src in date_sources.items() if name.lower() in ai_message.lower()]
            ai_message = _ensure_source(ai_message, _retrieved_sources(response) + mentioned, known)
        except Exception as e:
            error_logger.warning("chat_task: source links skipped for tenant %s: %s", tenant_id, e)

        # --- Token usage ---
        usage = getattr(response, "usage_metadata", None)
        if usage:
            input_tokens = getattr(usage, "prompt_token_count", 0) or 0
            output_tokens = getattr(usage, "candidates_token_count", 0) or 0
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
