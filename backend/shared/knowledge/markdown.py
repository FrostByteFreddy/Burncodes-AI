"""
shared/knowledge/markdown.py

Turns fetched pages and files into the text we fingerprint, estimate and hand
to Gemini.

HTML: the whole rendered page minus site chrome (header/nav/footer/cookie
banners, scripts, forms), converted to Markdown so tables and lists keep their
structure. Main-content extractors (trafilatura) drop teasers, news and event
lists — exactly what the importance assessment needs — so we don't use them
here.

The content hash runs on the normalised Markdown, not on raw bytes: CMS pages
embed session tokens, timestamps and rotating teasers, so a byte hash would
mark every page as changed on every crawl. Files are hashed on their raw bytes,
which are stable.
"""
import hashlib
import re

from bs4 import BeautifulSoup
from markdownify import markdownify

# Elements that never carry page content
_DROP_TAGS = [
    "script", "style", "noscript", "svg", "canvas", "iframe", "template",
    "form", "button", "input", "select", "textarea", "dialog",
    "header", "nav", "footer", "aside",
]
# role/id/class markers of site chrome
_CHROME_ROLES = {"navigation", "banner", "contentinfo", "search", "dialog"}
# Matched at the *start* of an id/class token: "cookie-banner" is chrome, but
# "show--consent" (a state class CMSs put on <html> while the banner is open)
# is not — matching anywhere in the name once deleted entire documents.
_CHROME_MARKERS = re.compile(
    r"^(cookie|consent|gdpr|onetrust|usercentrics|breadcrumb|skip-?link|"
    r"site-?header|site-?footer|main-?nav|off-?canvas|newsletter-?popup)",
    re.I,
)
# Containers that hold the content itself and are never removed
_NEVER_DROP = {"html", "body", "main", "article"}

# Rough characters per token for German/English text
_CHARS_PER_TOKEN = 4


def html_to_markdown(html: str) -> tuple[str, str]:
    """Returns (title, markdown) for an HTML page."""
    soup = BeautifulSoup(html or "", "lxml")
    title = (soup.title.get_text(" ", strip=True) if soup.title else "").strip()

    for tag in soup(_DROP_TAGS):
        tag.decompose()
    for el in soup.find_all(True):
        if el.decomposed or el.name in _NEVER_DROP:
            continue
        attrs = el.attrs or {}
        role = str(attrs.get("role", "")).lower()
        tokens = [str(attrs.get("id", ""))] + list(attrs.get("class", []) or [])
        if role in _CHROME_ROLES or any(t and _CHROME_MARKERS.match(t) for t in tokens):
            el.decompose()

    root = soup.find("main") or soup.find(attrs={"role": "main"}) or soup.body or soup
    md = markdownify(
        str(root),
        heading_style="ATX",
        bullets="-",
        strip=["img", "a"],  # keep link text, drop URLs and image noise
    )
    return title, normalize_markdown(md)


def normalize_markdown(md: str) -> str:
    """Stable text form: trimmed lines, no runs of blank lines or spaces."""
    lines = [re.sub(r"[ \t ]+", " ", line).strip() for line in (md or "").splitlines()]
    out, blank = [], False
    for line in lines:
        if not line:
            if not blank and out:
                out.append("")
            blank = True
            continue
        out.append(line)
        blank = False
    return "\n".join(out).strip()


def content_hash(content: str | bytes) -> str:
    data = content.encode("utf-8") if isinstance(content, str) else content
    return hashlib.sha256(data).hexdigest()


def estimate_tokens(text: str) -> int:
    return max(1, len(text or "") // _CHARS_PER_TOKEN)


def pdf_page_count(data: bytes) -> int:
    """Cheap page count without a PDF library; falls back to a size estimate."""
    count = len(re.findall(rb"/Type\s*/Page(?![s\w])", data or b""))
    if count:
        return count
    return max(1, len(data or b"") // 60_000)


def number_lines(md: str) -> str:
    """Prefixes each line with its 1-based number so Gemini can cite line ranges."""
    return "\n".join(f"{i}| {line}" for i, line in enumerate(md.splitlines(), start=1))


def slice_lines(md: str, start: int, end: int) -> str:
    lines = md.splitlines()
    start = max(1, int(start))
    end = min(len(lines), int(end))
    if end < start:
        return ""
    return "\n".join(lines[start - 1:end]).strip()
