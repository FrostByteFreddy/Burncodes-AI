"""
shared/ai_models.py

Every model the backend uses, configurable via .env. Change a value and
restart the affected containers (env_file is read at container start).

  CHAT_GEMINI_MODEL       answers widget/chat messages (worker_chat)
  CHAT_THINKING_LEVEL     how long it thinks before answering: low (default),
                          medium or high; empty = the model's own default.
                          Thinking is billed as output and makes answers slower.
  INDEXING_GEMINI_MODEL   reads documents during indexing: structured
                          extraction of schedules/tables (worker_fast/heavy)
  TRIAGE_GEMINI_MODEL     sorts out pages and documents not worth learning
                          (archives, old versions) before the estimate
  REVIEW_GEMINI_MODEL     reviews finished conversations for unanswered
                          questions and pushback (worker_fast)
  EMBEDDING_GEMINI_MODEL  embeddings for new File Search stores. A store keeps
                          the model it was created with; changing this only
                          affects tenants whose store doesn't exist yet.

Billing is per role, not per model name, so swapping a model never silently
changes what tenants are charged. Rates are CHF per 1M tokens.
"""
import os


def _env(name: str, default: str) -> str:
    return (os.getenv(name) or default).strip()


def _rate(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


CHAT_GEMINI_MODEL = _env("CHAT_GEMINI_MODEL", "gemini-3.8-flash")
# 3.8 Flash at its default thinks for 1–2k tokens and takes 20–35 s per answer;
# "low" answered as well in 7–11 s at a sixth of the tokens (younity, 2026-10-30)
CHAT_THINKING_LEVEL = os.getenv("CHAT_THINKING_LEVEL", "low").strip()
INDEXING_GEMINI_MODEL = _env("INDEXING_GEMINI_MODEL", "gemini-4-argon")
EMBEDDING_GEMINI_MODEL = _env("EMBEDDING_GEMINI_MODEL", "gemini-embedding-2")
# simple jobs that don't need the chat model: the cheapest one
_LITE_MODEL = "gemini-3.1-flash-lite"
REVIEW_GEMINI_MODEL = _env("REVIEW_GEMINI_MODEL", _LITE_MODEL)
# sorts the list of found pages before learning (one cheap call per ~300 entries)
TRIAGE_GEMINI_MODEL = _env("TRIAGE_GEMINI_MODEL", _LITE_MODEL)

# role -> {"input": CHF/1M tokens, "output": CHF/1M tokens}
RATES = {
    "chat": {
        "input": _rate("CHAT_RATE_CHF_PER_1M_INPUT", 8.0),
        "output": _rate("CHAT_RATE_CHF_PER_1M_OUTPUT", 17.5),
    },
    "indexing": {
        # Embedding-only indexing (File Search) — one input rate.
        "input": _rate("INDEXING_RATE_CHF_PER_1M_TOKENS", 0.15),
        "output": 0.0,
    },
    "review": {
        # Reading finished conversations to find gaps in the knowledge.
        "input": _rate("REVIEW_RATE_CHF_PER_1M_INPUT", 8.0),
        "output": _rate("REVIEW_RATE_CHF_PER_1M_OUTPUT", 17.5),
    },
    "extraction": {
        # LLM reading documents (structured/schedule extraction).
        "input": _rate("EXTRACTION_RATE_CHF_PER_1M_INPUT", 8.0),
        "output": _rate("EXTRACTION_RATE_CHF_PER_1M_OUTPUT", 50.0),
    },
}


# ── Learning: the customer picks the model when confirming an estimate ───────
# Google's list prices in USD per 1M tokens (input, output), each from the date
# it applies (ai.google.dev/gemini-api/docs/pricing). Customers pay them times
# LEARNING_PRICE_FACTOR, converted at USD_TO_CHF; embedding the learned sections
# is charged the same way.
LEARNING_MODELS = {
    "lite": {
        "model": _env("LEARNING_LITE_MODEL", "gemini-3.1-flash-lite"),
        "prices": [("", 0.25, 1.50)],
    },
    "argon": {
        "model": _env("LEARNING_ARGON_MODEL", "gemini-4-argon"),
        "prices": [("", 2.00, 10.00), ("2026-12-01", 4.00, 20.00)],
    },
}
DEFAULT_LEARNING_MODEL = "argon"
EMBEDDING_USD_PER_1M = _rate("EMBEDDING_USD_PER_1M", 0.20)
LEARNING_PRICE_FACTOR = _rate("LEARNING_PRICE_FACTOR", 5.0)
USD_TO_CHF = _rate("USD_TO_CHF", 0.80)


def learning_model_key(key: str | None) -> str:
    """A known learning model key; anything else is the default."""
    return key if key in LEARNING_MODELS else DEFAULT_LEARNING_MODEL


def learning_rates(key: str | None, on: str | None = None) -> dict:
    """What the customer pays in CHF per 1M tokens for learning with this model: input, output, embed."""
    from datetime import date
    day = on or date.today().isoformat()
    prices = LEARNING_MODELS[learning_model_key(key)]["prices"]
    _, usd_in, usd_out = [p for p in sorted(prices) if p[0] <= day][-1]
    chf = LEARNING_PRICE_FACTOR * USD_TO_CHF
    return {"input": usd_in * chf, "output": usd_out * chf, "embed": EMBEDDING_USD_PER_1M * chf}


def billable_tokens(usage) -> tuple[int, int]:
    """
    (input, output) tokens as Google bills them, from a response's usage_metadata.
    Input includes what tools pulled in (File Search context); output includes
    the model's thinking, which is billed at the output rate.
    """
    if usage is None:
        return 0, 0
    get = lambda name: getattr(usage, name, 0) or 0
    return (get("prompt_token_count") + get("tool_use_prompt_token_count"),
            get("candidates_token_count") + get("thoughts_token_count"))


_count_client = None


def count_tokens(texts: list[str], model: str | None = None) -> int | None:
    """
    Exact token count from Gemini's count_tokens endpoint (free, no generation).
    Returns None if it can't be reached, so callers fall back to an estimate.
    """
    global _count_client
    texts = [t for t in texts if t]
    if not texts:
        return 0
    try:
        if _count_client is None:
            from google import genai
            _count_client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"], http_options={"timeout": 30_000})
        return _count_client.models.count_tokens(
            model=model or EMBEDDING_GEMINI_MODEL, contents=texts).total_tokens
    except Exception:
        return None
