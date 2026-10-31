"""
knowledge/audience.py
Who a chatbot answers: residents of a municipality, or the visitors of any
other website (a shop, a course platform, a club). The steps that decide what
is worth learning describe those people and their questions to Gemini.
"""
from app.database.supabase_client import supabase

AUDIENCES = ("municipality", "general")
DEFAULT = "municipality"

_WORDING = {
    "municipality": {
        "people": "residents",
        "questions": "opening hours, contacts, fees, services, forms, rules, collection dates, events, current projects",
        "core": "the core services of the administration, contacts, opening hours, waste collection, "
                "current events, current projects or forms",
    },
    "general": {
        "people": "visitors",
        "questions": "what is offered (products, services, courses, events), prices and conditions, dates, "
                     "how to sign up or buy, how things work, contacts, opening hours",
        "core": "the main offers and their descriptions, prices, dates, contacts, opening hours or how to "
                "sign up and buy",
    },
}


def wording(audience: str | None) -> dict[str, str]:
    """people / questions / core for the prompts; unknown values count as the default."""
    return _WORDING.get(audience or DEFAULT, _WORDING[DEFAULT])


def audience_of(tenant_id: str) -> str:
    """The chatbot's audience; the default when unset or unreadable."""
    try:
        row = supabase.table("tenants").select("audience").eq("id", str(tenant_id)).limit(1).execute().data
        value = row[0].get("audience") if row else None
    except Exception:
        value = None
    return value if value in AUDIENCES else DEFAULT
