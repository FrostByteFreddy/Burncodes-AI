"""
knowledge/url_scope.py
Which discovered links a crawl follows: the paths the customer left out, and
(optionally) only the language version the crawl started in.
"""
import re
from urllib.parse import parse_qs, urlparse


def site(host: str | None) -> str:
    """Host without a leading "www." — zofingen.ch and www.zofingen.ch are one site."""
    host = (host or "").lower()
    return host[4:] if host.startswith("www.") else host


def is_excluded(url: str, excluded: list[str]) -> bool:
    """
    Entries are paths ("/de", "/shop/cart"), full URLs or hosts with an optional
    path ("shop.example.com"). A URL is excluded when it is the entry or lies below it.
    """
    parsed = urlparse(url)
    host, path = site(parsed.hostname), parsed.path.rstrip("/").lower()
    for entry in excluded:
        entry = str(entry).strip().lower()
        as_path = entry.startswith("/") and not entry.startswith("//")
        entry = re.sub(r"^(https?:)?//", "", entry).strip("/")
        if not entry:
            continue
        first, _, rest = entry.partition("/")
        if not as_path and "." in first:   # starts with a host
            if site(first) != host:
                continue
            entry = rest
        prefix = "/" + entry if entry else ""
        if not prefix or path == prefix or path.startswith(prefix + "/"):
            return True
    return False


# ISO 639-1 codes; a first path segment like "de", "en-us" or "fr_CH" names a language
_LANGUAGES = set(
    "aa ab ae af ak am an ar as av ay az ba be bg bh bi bm bn bo br bs ca ce ch co cr cs cu cv cy "
    "da de dv dz ee el en eo es et eu fa ff fi fj fo fr fy ga gd gl gn gu gv ha he hi ho hr ht hu "
    "hy hz ia id ie ig ii ik io is it iu ja jv ka kg ki kj kk kl km kn ko kr ks ku kv kw ky la lb "
    "lg li ln lo lt lu lv mg mh mi mk ml mn mr ms mt my na nb nd ne ng nl nn no nr nv ny oc oj om "
    "or os pa pi pl ps pt qu rm rn ro ru rw sa sc sd se sg si sk sl sm sn so sq sr ss st su sv sw "
    "ta te tg th ti tk tl tn to tr ts tt tw ty ug uk ur uz ve vi vo wa wo xh yi yo za zh zu".split()
)
_LANGUAGE_SEGMENT = re.compile(r"^([a-z]{2})(?:[-_][a-z]{2,4})?$")
_LANGUAGE_PARAMS = ("lang", "language", "locale", "hl")


def language_of(url: str) -> str | None:
    """Language a URL is in, from its path (/de/…, /en-us/…) or a ?lang= parameter; None if it names none."""
    parsed = urlparse(url)
    candidates = [parsed.path.strip("/").split("/", 1)[0]]
    query = parse_qs(parsed.query)
    candidates += [v for p in _LANGUAGE_PARAMS for v in query.get(p, [])]
    for value in candidates:
        m = _LANGUAGE_SEGMENT.match(value.lower())
        if m and m.group(1) in _LANGUAGES:
            return m.group(1)
    return None


def other_language(url: str, start_url: str) -> bool:
    """
    True when `url` is a different language version than `start_url`:
    starting at example.com/ skips /de/…, /fr/…; starting at /de/ skips /en/…
    but keeps pages without a language in their address.
    """
    lang = language_of(url)
    return lang is not None and lang != language_of(start_url)


# Steps of a sign-up or sales funnel that carry nothing to answer from: the
# thank-you, confirmation and error pages after a form, paid-ads copies of a
# page, carts and accounts. Matched against the last part of the path.
_FUNNEL_PAGE = re.compile(
    r"^(thanks?|thank-?you|danke|vielen-dank|merci)([-_].*)?$"      # thanks-start, danke-fuer-…
    r"|^(confirm|confirmation|bestaetigung|bestätigung|fehler|error|success|erfolg|checkout|cart|"
    r"warenkorb|kasse|login|logout|register|registrieren|anmelden|abmelden|unsubscribe|opt-?out(-\d+)?|"
    r"password|passwort|account|konto)$"
    r"|.*[-_](ppc|ads)$"
)


def is_funnel_page(url: str) -> bool:
    """A thank-you, confirmation, error, ad-copy, cart or account page (see _FUNNEL_PAGE)."""
    last = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1].lower()
    return bool(last) and bool(_FUNNEL_PAGE.match(last))
