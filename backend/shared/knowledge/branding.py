"""
knowledge/branding.py
A website's look for the chat widget: its brand colours, logo and name, read
from the start page and its stylesheets. The customer reviews the result in
the configurator before anything is saved.
"""
import base64
import colorsys
import re
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urljoin

from app.security.url_guard import safe_client

MAX_STYLESHEETS = 4
MAX_CSS_BYTES = 5_000_000
# the logo travels with every widget load
MAX_LOGO_BYTES = 400_000
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BurnCodesBot/1.0; +https://ai.burn.codes)"}


class _Page(HTMLParser):
    """Collects what the look is made of: meta tags, icons, stylesheets, inline CSS and logo candidates."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.icons: list[tuple[str, str, str]] = []      # (rel, sizes, href)
        self.stylesheets: list[str] = []
        self.css: list[str] = []
        self.images: list[tuple[int, str]] = []          # (score, src)
        self._stack: list[str] = []                      # attributes of open header/nav/a/div elements
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if a.get("style"):
            self.css.append(a["style"])
        if tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key and a.get("content"):
                self.meta.setdefault(key, a["content"].strip())
        elif tag == "link":
            rel = a.get("rel", "").lower()
            if "stylesheet" in rel and a.get("href"):
                self.stylesheets.append(a["href"])
            elif "icon" in rel and a.get("href"):
                self.icons.append((rel, a.get("sizes", ""), a["href"]))
        elif tag == "style":
            self._in_style = True
        elif tag == "img":
            src = a.get("src") or a.get("data-src") or ""
            if src and not src.startswith("data:image/gif"):
                self.images.append((self._logo_score(a), src))
        if tag in ("header", "nav", "a", "div", "span", "figure"):
            self._stack.append(f"{tag} {a.get('class', '')} {a.get('id', '')}".lower())

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False
        if tag in ("header", "nav", "a", "div", "span", "figure"):
            for i in range(len(self._stack) - 1, -1, -1):
                if self._stack[i].startswith(tag + " "):
                    del self._stack[i:]
                    break

    def handle_data(self, data):
        if self._in_style:
            self.css.append(data)

    def _logo_score(self, a: dict) -> int:
        own = " ".join(a.get(k, "") for k in ("src", "alt", "class", "id")).lower()
        around = " ".join(self._stack)
        score = 0
        if "logo" in own:
            score += 3
        if "logo" in around or "brand" in around:
            score += 2
        if any(s.startswith(("header", "nav")) or " header" in s for s in self._stack):
            score += 1
        return score


# ── Colours ──────────────────────────────────────────────────────────────

_HEX = re.compile(r"#([0-9a-f]{6}|[0-9a-f]{3})\b", re.I)
_RGB = re.compile(r"rgba?\(\s*(\d{1,3})[\s,]+(\d{1,3})[\s,]+(\d{1,3})", re.I)
_DECL = re.compile(r"([\w-]+)\s*:\s*([^;{}]+)")
# properties whose colour people actually see; a custom property named like a brand colour counts most
_VISIBLE = ("background", "background-color", "color", "border-color", "border", "fill", "outline-color")
_BRAND_VAR = re.compile(r"^--.*(primary|brand|accent|main|theme|highlight)", re.I)
# Stock colours of Bootstrap 4/5 and WordPress: present on countless sites, nobody's brand
_FRAMEWORK = {
    "#0D6EFD", "#6610F2", "#6F42C1", "#D63384", "#DC3545", "#FD7E14", "#FFC107", "#198754", "#20C997", "#0DCAF0",
    "#007BFF", "#28A745", "#17A2B8", "#6C757D", "#E83E8C",
    "#CF2E2E", "#FF6900", "#FCB900", "#7BDCB5", "#00D084", "#8ED1FC", "#0693E3", "#9B51E0", "#F78DA7", "#ABB8C3",
}


def _hex(value: str) -> str | None:
    m = _HEX.search(value)
    if m:
        h = m.group(1)
        return "#" + (h if len(h) == 6 else "".join(c * 2 for c in h)).upper()
    m = _RGB.search(value)
    if m:
        r, g, b = (min(255, int(x)) for x in m.groups())
        return f"#{r:02X}{g:02X}{b:02X}"
    return None


def _is_brand_like(hex_color: str) -> bool:
    """A real colour: not grey, not near-white, not near-black."""
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    _, light, sat = colorsys.rgb_to_hls(r, g, b)
    return sat >= 0.35 and 0.18 <= light <= 0.82


def _close(a: str, b: str) -> bool:
    return sum(abs(int(a[i:i + 2], 16) - int(b[i:i + 2], 16)) for i in (1, 3, 5)) < 48


def brand_colors(css: str, theme_color: str | None = None, limit: int = 4) -> list[str]:
    """The website's brand colours, most important first; near-identical shades count as one."""
    weights: Counter[str] = Counter()
    for prop, value in _DECL.findall(css):
        prop = prop.lower()
        color = _hex(value)
        if not color or color in _FRAMEWORK or not _is_brand_like(color):
            continue
        if _BRAND_VAR.match(prop):
            weights[color] += 5
        elif prop in _VISIBLE or prop.startswith("--"):
            weights[color] += 1
    theme = _hex(theme_color or "")
    if theme and _is_brand_like(theme):
        weights[theme] += 1000   # the site says which colour is its own
    picked: list[str] = []
    for color, _ in weights.most_common():
        if not any(_close(color, p) for p in picked):
            picked.append(color)
        if len(picked) == limit:
            break
    return picked


# ── Reading a website ────────────────────────────────────────────────────

def parse_page(html: str, page_url: str) -> dict:
    """Everything the start page itself tells; stylesheets and the logo still have to be fetched."""
    page = _Page()
    page.feed(html)
    images = sorted((img for img in page.images if img[0] > 0), key=lambda img: -img[0])
    # apple-touch-icon is a square, solid version of the logo; otherwise the largest icon
    icons = sorted(page.icons, key=lambda i: ("apple-touch-icon" in i[0], _icon_size(i[1])), reverse=True)
    return {
        "site_name": page.meta.get("og:site_name") or page.meta.get("application-name") or None,
        "theme_color": page.meta.get("theme-color") or page.meta.get("msapplication-tilecolor"),
        "css": "\n".join(page.css),
        "stylesheets": [urljoin(page_url, href) for href in page.stylesheets],
        "logo_url": urljoin(page_url, images[0][1]) if images else None,
        "icon_url": urljoin(page_url, icons[0][2]) if icons else None,
    }


def _icon_size(sizes: str) -> int:
    m = re.match(r"(\d+)", sizes or "")
    return int(m.group(1)) if m else 0


def _get(client, url: str, limit: int) -> tuple[bytes, str] | None:
    try:
        with client.stream("GET", url) as resp:
            if resp.status_code >= 400:
                return None
            data = b""
            for chunk in resp.iter_bytes():
                data += chunk
                if len(data) > limit:
                    return None
            return data, resp.headers.get("content-type", "").split(";")[0].strip().lower()
    except Exception:
        return None


def _data_url(client, url: str | None) -> str | None:
    if not url:
        return None
    got = _get(client, url, MAX_LOGO_BYTES)
    if not got:
        return None
    data, ctype = got
    if not ctype.startswith("image/"):
        ctype = "image/svg+xml" if url.lower().split("?")[0].endswith(".svg") else ""
    if not ctype or ctype == "image/x-icon" or ctype == "image/vnd.microsoft.icon":
        return None   # .ico files don't scale; better no logo than a blurry one
    return f"data:{ctype};base64,{base64.b64encode(data).decode()}"


def read_branding(url: str) -> dict:
    """
    Fetches the start page, its first stylesheets and its logo. Returns
    {"colors": [...], "logo": data URL or None, "site_name": str or None}.
    Raises UnsafeURLError / httpx errors when the page itself can't be read.
    """
    with safe_client(timeout=15.0, follow_redirects=True, headers=HEADERS) as client:
        resp = client.get(url)
        resp.raise_for_status()
        page_url = str(resp.url)
        info = parse_page(resp.text, page_url)
        css = [info["css"]]
        for sheet in info["stylesheets"][:MAX_STYLESHEETS]:
            got = _get(client, sheet, MAX_CSS_BYTES)
            if got:
                css.append(got[0].decode("utf-8", "replace"))
        logo = _data_url(client, info["logo_url"]) or _data_url(client, info["icon_url"])
    return {
        "colors": brand_colors("\n".join(css), info["theme_color"]),
        "logo": logo,
        "site_name": info["site_name"],
        "source_url": page_url,
    }
