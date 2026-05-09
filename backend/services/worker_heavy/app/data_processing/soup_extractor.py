"""
soup_extractor.py
-----------------
Lightweight HTTP-only content fetcher and extractor for crawl_mode='soup'.

Strategy (in order of preference):
1. trafilatura  — purpose-built article/content extractor, strips navs/ads/boilerplate
2. BeautifulSoup fallback — removes known noise tags, returns body text

After extraction, a heuristic filter removes low-quality chunks before
they reach the vector store.
"""

import re
import httpx
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from app.logging_config import error_logger

# ---------------------------------------------------------------------------
# HTTP fetch
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; SwiftAnswerBot/1.0; "
        "+https://ai.burn.codes)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Tags that are almost never content
_NOISE_TAGS = [
    "script", "style", "noscript", "nav", "header", "footer",
    "aside", "form", "button", "iframe", "svg", "figure",
    "picture", "video", "audio", "canvas", "select", "option",
    "input", "textarea", "label", "fieldset",
]


def fetch_html(url: str, timeout: float = 15.0) -> tuple[str | None, int]:
    """
    Fetches a URL synchronously with httpx.
    Returns (html_text, status_code). html_text is None on failure.
    """
    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            resp = client.get(url)
            if resp.status_code >= 400:
                return None, resp.status_code
            return resp.text, resp.status_code
    except Exception as e:
        error_logger.warning("soup: fetch failed for %s: %s", url, e)
        return None, 0


# ---------------------------------------------------------------------------
# Content extraction
# ---------------------------------------------------------------------------

def extract_content(html: str, url: str) -> str:
    """
    Extracts clean body text from raw HTML.
    Tries trafilatura first (best quality), falls back to BeautifulSoup.
    """
    # --- 1. trafilatura (preferred) ---
    try:
        result = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=True,   # fewer but cleaner results
        )
        if result and len(result.strip()) > 100:
            return result.strip()
    except Exception as e:
        error_logger.debug("soup: trafilatura failed for %s: %s", url, e)

    # --- 2. BeautifulSoup fallback ---
    try:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(_NOISE_TAGS):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text.strip()
    except Exception as e:
        error_logger.warning("soup: bs4 fallback failed for %s: %s", url, e)

    return ""


# ---------------------------------------------------------------------------
# Heuristic chunk quality filter (used by both soup and playwright modes)
# ---------------------------------------------------------------------------

# Patterns that indicate a chunk is navigation/boilerplate, not content
_BOILERPLATE_PATTERNS = [
    re.compile(r"^(home|back|next|previous|skip to|cookie|privacy policy|terms of|all rights reserved)", re.I),
    re.compile(r"^\s*[\|•·–—]\s*$"),          # separator-only lines
    re.compile(r"^https?://\S+$"),              # bare URL only
]

_MIN_CHUNK_CHARS = 80          # chunks shorter than this are noise
_MAX_LINK_DENSITY = 0.6        # if >60% of chars are inside [...] it's a link list


def _is_low_quality(chunk: str) -> bool:
    """Returns True if the chunk looks like navigation/boilerplate."""
    stripped = chunk.strip()

    if len(stripped) < _MIN_CHUNK_CHARS:
        return True

    for pat in _BOILERPLATE_PATTERNS:
        if pat.match(stripped):
            return True

    # Link density heuristic: count chars inside markdown link syntax [text](url)
    link_chars = sum(len(m.group(0)) for m in re.finditer(r'\[.*?\]\(.*?\)', stripped))
    if len(stripped) > 0 and link_chars / len(stripped) > _MAX_LINK_DENSITY:
        return True

    # Mostly numbers/punctuation — e.g. a table of phone numbers
    alpha_ratio = sum(c.isalpha() for c in stripped) / max(len(stripped), 1)
    if alpha_ratio < 0.25:
        return True

    return False


def filter_chunks(chunks: list[str]) -> list[str]:
    """Removes low-quality chunks from a list of text chunks."""
    before = len(chunks)
    result = [c for c in chunks if not _is_low_quality(c)]
    dropped = before - len(result)
    if dropped:
        error_logger.debug("soup: heuristic filter dropped %d/%d chunks", dropped, before)
    return result


# ---------------------------------------------------------------------------
# Internal link discovery (for crawl graph, soup mode)
# ---------------------------------------------------------------------------

def extract_internal_links(html: str, base_url: str) -> list[str]:
    """
    Extracts all internal <a href> links from raw HTML.
    Returns absolute URLs on the same domain as base_url.
    """
    try:
        base_domain = urlparse(base_url).netloc
        soup = BeautifulSoup(html, "lxml")
        links = []
        for a in soup.find_all("a", href=True):
            href = urljoin(base_url, a["href"])
            parsed = urlparse(href)
            # Only same-domain, http/https, no fragments
            if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
                clean = href.split("#")[0].rstrip("/")
                if clean not in links:
                    links.append(clean)
        return links
    except Exception as e:
        error_logger.warning("soup: link extraction failed for %s: %s", base_url, e)
        return []
