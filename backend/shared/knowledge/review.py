"""
shared/knowledge/review.py

Reads finished conversations and reports what staff should act on:
questions the chatbot couldn't answer, answers people pushed back on or
corrected, and questions it misunderstood. Each finding says what went wrong
and what knowledge would fix it, written in the dashboard user's language.

Runs once a night. A conversation counts as finished after QUIET_MINUTES
without a message, and each conversation is reviewed once.
"""
import json
import os
from datetime import datetime, timedelta, timezone

from google import genai
from google.genai import types

from app.ai_models import RATES, REVIEW_GEMINI_MODEL
from app.database.supabase_client import supabase
from app.logging_config import error_logger

QUIET_MINUTES = int(os.getenv("REVIEW_QUIET_MINUTES", "30"))
LOOKBACK_DAYS = int(os.getenv("REVIEW_LOOKBACK_DAYS", "14"))
MAX_CONVERSATIONS_PER_RUN = int(os.getenv("REVIEW_MAX_CONVERSATIONS_PER_RUN", "200"))
# Long conversations are cut to their newest turns; plenty to judge them
MAX_TURNS = 30

KINDS = ("unanswered", "wrong", "pushback", "unclear")
LANGUAGE_NAMES = {"de": "German", "en": "English", "fr": "French", "it": "Italian"}

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"], http_options={"timeout": 60_000})
    return _client


_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "turn": {"type": "integer", "description": "Number of the turn the finding is about"},
                    "kind": {"type": "string", "enum": list(KINDS)},
                    "question": {"type": "string", "description": "The visitor's question, verbatim"},
                    "topic": {"type": "string", "description": "2-6 word topic in the visitor's language"},
                    "problem": {"type": "string"},
                    "suggestion": {"type": "string"},
                },
                "required": ["turn", "kind", "question", "problem", "suggestion"],
            },
        },
    },
    "required": ["findings"],
}

_INSTRUCTIONS = """You review conversations between visitors and an organisation's website chatbot.
The chatbot answers only from documents the organisation gave it. Your report goes to the staff
who maintain those documents, so only report what they can act on.

Report a turn when:
- unanswered: the chatbot said it doesn't know, has no information, or redirected without answering.
- wrong: the conversation itself shows the answer is wrong: it contradicts itself, contradicts what the
  visitor reports, or gives a date before today as upcoming. You cannot see the documents, so do not
  second-guess facts, dates or weekdays you cannot check.
- pushback: the visitor disagreed, corrected the chatbot, said it didn't help, or asked the same thing again.
- unclear: the chatbot misunderstood the question or answered something else.

Do not report greetings, small talk, thanks, test messages, abuse, or questions that were answered well.
If nothing needs attention, return an empty list.

For each finding:
- question: the visitor's question exactly as written.
- topic: what the question is about in 2-6 words, in the visitor's language
  (e.g. "Öffnungszeiten Freibad"). Staff use it as the trigger of a custom answer.
- problem: one short sentence (at most 20 words) on what went wrong.
- suggestion: one short sentence (at most 20 words) on what knowledge to add or fix,
  e.g. "Add the opening hours of the recycling centre".
Write problem and suggestion in {language}. Only review turns numbered {first_turn} and later; earlier turns are context.
Today is {today}."""


def _transcript(logs: list[dict]) -> str:
    lines = []
    for i, log in enumerate(logs, start=1):
        lines.append(f"[Turn {i}]\nVisitor: {(log.get('user_message') or '').strip()}\n"
                     f"Chatbot: {(log.get('ai_message') or '').strip()}")
    return "\n\n".join(lines)


def review_transcript(logs: list[dict], first_new: int, language: str) -> tuple[list[dict], int, int]:
    """
    logs: chat_logs rows (oldest first). first_new: index of the first row not
    reviewed before. Returns (findings with log_id, input_tokens, output_tokens).
    """
    prompt = _INSTRUCTIONS.format(
        language=LANGUAGE_NAMES.get(language, "English"),
        first_turn=first_new + 1,
        # with the weekday, so it doesn't "correct" a right one
        today=datetime.now(timezone.utc).strftime("%A, %Y-%m-%d"),
    )
    response = _get_client().models.generate_content(
        model=REVIEW_GEMINI_MODEL,
        contents=[prompt, "CONVERSATION:\n" + _transcript(logs)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=_SCHEMA,
            temperature=0,
            max_output_tokens=4096,
        ),
    )
    usage = getattr(response, "usage_metadata", None)
    in_tok = getattr(usage, "prompt_token_count", 0) or 0
    out_tok = getattr(usage, "candidates_token_count", 0) or 0
    try:
        raw = json.loads(response.text or "").get("findings") or []
    except (json.JSONDecodeError, TypeError, AttributeError):
        raw = []
    return _clean(raw, logs, first_new), in_tok, out_tok


def _clean(raw: list, logs: list[dict], first_new: int) -> list[dict]:
    """Keep findings about new turns with a known kind; attach the chat_logs id."""
    findings, seen = [], set()
    for f in raw:
        if not isinstance(f, dict) or f.get("kind") not in KINDS:
            continue
        try:
            turn = int(f.get("turn"))
        except (TypeError, ValueError):
            continue
        if not first_new < turn <= len(logs) or (turn, f["kind"]) in seen:
            continue
        seen.add((turn, f["kind"]))
        question = (f.get("question") or logs[turn - 1].get("user_message") or "").strip()
        problem = (f.get("problem") or "").strip()
        if not question or not problem:
            continue
        findings.append({
            "log_id": logs[turn - 1]["id"],
            "kind": f["kind"],
            "question": question[:1000],
            "topic": (f.get("topic") or "").strip()[:120],
            "problem": problem[:500],
            "suggestion": (f.get("suggestion") or "").strip()[:500],
        })
    return findings


def _owner_language(user_id: str) -> str:
    try:
        user = supabase.auth.admin.get_user_by_id(user_id).user
        return ((user.user_metadata or {}).get("language") or "en")[:2]
    except Exception:
        return "en"


def due_conversations(tenant_id: str, now: datetime | None = None) -> list[dict]:
    """
    Finished conversations that were never reviewed.
    Returns [{"conversation_id", "logs" (oldest first), "first_new"}].
    """
    now = now or datetime.now(timezone.utc)
    quiet_since = (now - timedelta(minutes=QUIET_MINUTES)).isoformat()
    since = (now - timedelta(days=LOOKBACK_DAYS)).isoformat()
    rows = (
        supabase.table("chat_logs")
        .select("id, conversation_id, user_message, ai_message, created_at")
        .eq("tenant_id", tenant_id).gte("created_at", since)
        .order("id").limit(20000).execute()
    ).data or []
    by_convo: dict[str, list[dict]] = {}
    for r in rows:
        by_convo.setdefault(r["conversation_id"], []).append(r)
    if not by_convo:
        return []
    # in batches: every id ends up in the request URL
    ids, reviewed = list(by_convo), set()
    for i in range(0, len(ids), 100):
        reviewed |= {
            r["conversation_id"] for r in (
                supabase.table("chat_reviews").select("conversation_id")
                .in_("conversation_id", ids[i:i + 100]).execute()
            ).data or []
        }
    due = []
    for convo, logs in by_convo.items():
        if convo in reviewed or logs[-1]["created_at"] > quiet_since:
            continue  # done before, or still going
        due.append({"conversation_id": convo, "logs": logs[-MAX_TURNS:], "first_new": 0})
    due.sort(key=lambda d: d["logs"][-1]["id"])
    return due[:MAX_CONVERSATIONS_PER_RUN]


def review_tenant(tenant_id: str, owner_id: str, charge) -> dict:
    """
    Reviews due conversations of one tenant. charge(owner_id, input, output) -> CHF
    deducts the cost. Returns counts for logging.
    """
    language = _owner_language(owner_id)
    done = found = 0
    for item in due_conversations(tenant_id):
        try:
            findings, in_tok, out_tok = review_transcript(item["logs"], item["first_new"], language)
        except Exception as e:
            error_logger.warning("review: conversation %s failed: %s", item["conversation_id"], e)
            continue
        cost = charge(owner_id, in_tok, out_tok)
        if findings:
            supabase.table("chat_findings").insert([
                {"tenant_id": tenant_id, "conversation_id": item["conversation_id"], **f} for f in findings
            ]).execute()
        supabase.table("chat_reviews").upsert({
            "conversation_id": item["conversation_id"],
            "tenant_id": tenant_id,
            "last_log_id": item["logs"][-1]["id"],
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "cost_chf": cost,
        }).execute()
        done += 1
        found += len(findings)
    return {"reviewed": done, "findings": found}


def estimate_chf_per_conversation() -> float:
    """Rough cost of one review (≈2k tokens in, 200 out), for the dashboard."""
    rate = RATES["review"]
    return 2000 / 1_000_000 * rate["input"] + 200 / 1_000_000 * rate["output"]
