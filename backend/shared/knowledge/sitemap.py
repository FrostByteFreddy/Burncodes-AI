"""
knowledge/sitemap.py
The pages a website lists in its sitemap. Many sites have far more pages than
their menus link to (landing pages reached from ads and newsletters); the
sitemap is the only place that names them.
"""
import gzip
import re
from html import unescape
from urllib.parse import urljoin, urlparse

from app.security.url_guard import safe_client

MAX_URLS = 5000
MAX_SITEMAPS = 100
MAX_BYTES = 20 * 1024 * 1024
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BurnCodesBot/1.0; +https://ai.burn.codes)"}

_LOC = re.compile(r"<loc>\s*(?:<!\[CDATA\[)?\s*([^<\s\]]+)", re.I)


def parse_sitemap(xml: str) -> tuple[list[str], list[str]]:
    """(pages, further sitemaps) named by one sitemap file or sitemap index."""
    locs = [unescape(u) for u in _LOC.findall(xml)]
    if re.search(r"<sitemapindex\b", xml, re.I):
        return [], locs
    return locs, []


def sitemaps_in_robots(robots: str, base: str) -> list[str]:
    return [urljoin(base, m.strip()) for m in re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots)]


def _fetch(client, url: str) -> str | None:
    try:
        resp = client.get(url)
        if resp.status_code >= 400 or len(resp.content) > MAX_BYTES:
            return None
        data = resp.content
        if data[:2] == b"\x1f\x8b":   # sitemap.xml.gz
            data = gzip.decompress(data)[:MAX_BYTES]
        return data.decode("utf-8", "replace")
    except Exception:
        return None


def sitemap_urls(start_url: str) -> list[str]:
    """
    Every page the site's sitemaps list, in their order: the ones robots.txt
    names, else /sitemap.xml or /sitemap_index.xml. Best effort: an
    unreadable sitemap gives fewer pages, never an error.
    """
    parsed = urlparse(start_url)
    root = f"{parsed.scheme}://{parsed.netloc}/"
    pages: list[str] = []
    with safe_client(timeout=20.0, follow_redirects=True, headers=HEADERS) as client:
        queue = sitemaps_in_robots(_fetch(client, urljoin(root, "robots.txt")) or "", root)
        if not queue:
            queue = [urljoin(root, "sitemap.xml"), urljoin(root, "sitemap_index.xml")]
        seen: set[str] = set()
        while queue and len(seen) < MAX_SITEMAPS and len(pages) < MAX_URLS:
            url = queue.pop(0)
            if url in seen:
                continue
            seen.add(url)
            xml = _fetch(client, url)
            if not xml:
                continue
            found, nested = parse_sitemap(xml)
            pages += found
            queue += nested
    return list(dict.fromkeys(pages))[:MAX_URLS]
