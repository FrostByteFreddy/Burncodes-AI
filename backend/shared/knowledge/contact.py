"""
shared/knowledge/contact.py

The organisation's contact card: address, phone, email and opening hours as
printed in the website footer. Page text leaves the footer out (it repeats on
every page), so municipal sites' most asked-for facts never reached the
chatbot. The card is read once per crawl from the start page, re-extracted
only when the footer changed, and given to the chat as a fixed fact with a
map link for the address.

Not billed: one small call per changed footer.
"""
import json
import re
from urllib.parse import quote_plus

from google.genai import types

from app.ai_models import TRIAGE_GEMINI_MODEL
from app.logging_config import error_logger

MAX_FOOTER_CHARS = 6_000
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")

_SCHEMA = {
    "type": "object",
    "properties": {
        "found": {"type": "boolean", "description": "false if the text holds no contact details of the organisation"},
        "name": {"type": "string"},
        "street": {"type": "string"},
        "postal_code": {"type": "string"},
        "city": {"type": "string"},
        "phone": {"type": "string"},
        "email": {"type": "string"},
        "opening_hours": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"days": {"type": "string"}, "hours": {"type": "string"}},
                "required": ["days", "hours"],
            },
        },
        "hours_note": {"type": "string", "description": "e.g. holiday closures or 'by appointment', else empty"},
    },
    "required": ["found", "name", "street", "postal_code", "city", "phone", "email", "opening_hours", "hours_note"],
}

_INSTRUCTIONS = """This is the footer of the website {site}. Extract the contact details of the
organisation the website belongs to (its main office, e.g. the municipal administration):
name, street, postal code, city, phone, email and opening hours.

Rules:
- Only what is literally in the text. Leave a field empty if it isn't there; never guess.
- Opening hours: one entry per group of days with the same hours, in the text's language,
  e.g. {{"days": "Montag, Dienstag, Donnerstag", "hours": "08:00–12:00 und 13:30–17:00 Uhr"}},
  {{"days": "Mittwoch", "hours": "geschlossen"}}. Keep days in their order.
- Only the organisation's own office hours, not those of a library, school or other facility.
- found = false if there are no contact details at all."""


def maps_url(card: dict) -> str | None:
    """A Google Maps search link for the card's address, or None without a street."""
    if not (card.get("street") and (card.get("postal_code") or card.get("city"))):
        return None
    address = ", ".join(p for p in (card.get("name"), card.get("street"),
                                    " ".join(x for x in (card.get("postal_code"), card.get("city")) if x)) if p)
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(address)


def extract_contact(footer_md: str, site: str) -> dict | None:
    """The contact card from footer text, or None if there is none. Never raises."""
    if not footer_md or len(footer_md) < 20:
        return None
    try:
        from app.knowledge.triage import _get_client   # here: the chat worker imports this module without it
        response = _get_client().models.generate_content(
            model=TRIAGE_GEMINI_MODEL,
            contents=[_INSTRUCTIONS.format(site=site), "FOOTER:\n" + footer_md[:MAX_FOOTER_CHARS]],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=_SCHEMA,
                temperature=0,
                max_output_tokens=2_000,
            ),
        )
        data = json.loads(response.text or "{}")
    except Exception as e:
        error_logger.warning("contact: extraction for %s failed: %s", site, e)
        return None
    if not data.get("found"):
        return None
    card = {k: (str(data.get(k) or "").strip()) for k in
            ("name", "street", "postal_code", "city", "phone", "email", "hours_note")}
    # sites hide addresses from spam bots in fragments ("g m nd r ch …"); half an address is worse than none
    if not _EMAIL.fullmatch(card["email"]):
        card["email"] = ""
    if len(re.sub(r"\D", "", card["phone"])) < 7:
        card["phone"] = ""
    card["opening_hours"] = [
        {"days": str(h.get("days") or "").strip(), "hours": str(h.get("hours") or "").strip()}
        for h in data.get("opening_hours") or [] if isinstance(h, dict) and h.get("days")
    ]
    if not any(card[k] for k in ("street", "phone", "email")) and not card["opening_hours"]:
        return None
    card["maps_url"] = maps_url(card)
    return card


def contact_context(card: dict | None) -> str:
    """The card as a fixed fact for the chat's instructions ('' without a card)."""
    if not card:
        return ""
    lines = ["Contact details and opening hours of the organisation (from its website; use these for "
             "questions about how to reach it, where it is or when it is open):"]
    if card.get("name"):
        lines.append(f"- Name: {card['name']}")
    address = ", ".join(p for p in (card.get("street"), " ".join(
        x for x in (card.get("postal_code"), card.get("city")) if x)) if p)
    if address:
        lines.append(f"- Address: {address}" + (f" (map: {card['maps_url']})" if card.get("maps_url") else ""))
    if card.get("phone"):
        lines.append(f"- Phone: {card['phone']}")
    if card.get("email"):
        lines.append(f"- Email: {card['email']}")
    for h in card.get("opening_hours") or []:
        lines.append(f"- Opening hours {h['days']}: {h['hours']}")
    if card.get("hours_note"):
        lines.append(f"- Note on opening hours: {card['hours_note']}")
    if card.get("maps_url"):
        lines.append("When you give the address, make it a markdown link to the map address above.")
    return "\n".join(lines)
