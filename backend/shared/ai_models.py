"""
shared/ai_models.py

Every model the backend uses, configurable via .env. Change a value and
restart the affected containers (env_file is read at container start).

  CHAT_GEMINI_MODEL       answers widget/chat messages (worker_chat)
  INDEXING_GEMINI_MODEL   reads documents during indexing: structured
                          extraction of schedules/tables (worker_fast/heavy)
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


CHAT_GEMINI_MODEL = _env("CHAT_GEMINI_MODEL", "gemini-3.1-flash-lite")
INDEXING_GEMINI_MODEL = _env("INDEXING_GEMINI_MODEL", "gemini-4-argon")
EMBEDDING_GEMINI_MODEL = _env("EMBEDDING_GEMINI_MODEL", "gemini-embedding-2")
REVIEW_GEMINI_MODEL = _env("REVIEW_GEMINI_MODEL", CHAT_GEMINI_MODEL)

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
        "output": _rate("EXTRACTION_RATE_CHF_PER_1M_OUTPUT", 17.5),
    },
}
