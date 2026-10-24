"""
shared/knowledge/pdf_crosscheck.py

Second, independent reading of calendar grids in born-digital PDFs.

Gemini reads the page visually. That's mostly right, but a wrong date that the
model also flags as an "exception" passes the weekday rule. Born-digital PDFs
(InDesign, Word exports) carry every word with its position and fill colour,
which is enough to verify each extracted date without knowing the layout:

  - find month header words (Jan, Februar, März, ...) → one column per month
  - each extracted date's day number must be printed in that month's column
  - a date flagged as exception must be printed in a non-black colour there

Returns no verdict (None) when the PDF has no text layer or no month headers —
then only the weekday validation applies.
"""
import io
import re
from datetime import date

_MONTHS = {
    1: ["jan", "januar", "january", "janvier", "janv"],
    2: ["feb", "februar", "february", "février", "fevrier", "févr"],
    3: ["mär", "märz", "maerz", "mar", "march", "mars"],
    4: ["apr", "april", "avril", "avr"],
    5: ["mai", "may"],
    6: ["jun", "juni", "june", "juin"],
    7: ["jul", "juli", "july", "juillet", "juil"],
    8: ["aug", "august", "août", "aout"],
    9: ["sep", "sept", "september", "septembre"],
    10: ["okt", "oktober", "oct", "october", "octobre"],
    11: ["nov", "november", "novembre"],
    12: ["dez", "dezember", "dec", "december", "décembre", "déc"],
}
_MONTH_OF = {name: m for m, names in _MONTHS.items() for name in names}
_DAY = re.compile(r"^(\d{1,2})\.?$")


def _is_black(color) -> bool:
    if color is None:
        return True
    c = tuple(color) if isinstance(color, (list, tuple)) else (color,)
    if len(c) == 1:          # gray: 0 = black
        return c[0] <= 0.35
    if len(c) == 3:          # RGB
        return max(c) <= 0.35
    if len(c) == 4:          # CMYK: black = high K or all inks dark
        cy, m, y, k = c
        return k >= 0.65 or (cy > 0.6 and m > 0.6 and y > 0.6)
    return True


def _page_columns(words: list[dict]) -> list[tuple[int, float, float, float]] | None:
    """Finds one header row of 12 month names → [(month, x_from, x_to, header_bottom)]."""
    # Month names also occur in running text ("…30. April, 2. Mai"), and words
    # aren't returned in reading order — so pick the *line* that holds the most
    # distinct month names, not the first occurrence of each.
    lines: dict[int, dict[int, dict]] = {}
    for w in words:
        m = _MONTH_OF.get(w["text"].strip(".,").lower())
        if m:
            lines.setdefault(round(w["top"] / 3), {}).setdefault(m, w)
    if not lines:
        return None
    headers = max(lines.values(), key=len)
    if len(headers) < 10:
        return None
    row = sorted(headers.items())
    xs = [((w["x0"] + w["x1"]) / 2) for _, w in row]
    cols = []
    for i, (m, w) in enumerate(row):
        left = (xs[i - 1] + xs[i]) / 2 if i else xs[i] - (xs[1] - xs[0]) / 2
        right = (xs[i] + xs[i + 1]) / 2 if i + 1 < len(xs) else xs[i] + (xs[i] - xs[i - 1]) / 2
        cols.append((m, left, right, w["bottom"]))
    return cols


def crosscheck_schedules(pdf_bytes: bytes, schedules: list[dict]) -> dict[int, list[str]] | None:
    """
    Returns {schedule_index: [problems]} for schedules whose dates are not
    backed by the PDF's text layer, or None if the PDF can't be checked.
    """
    try:
        import pdfplumber
    except ImportError:
        return None

    cells: dict[tuple[int, int], list[bool]] = {}   # (month, day) -> [is_black, ...]
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                words = page.extract_words(extra_attrs=["non_stroking_color"])
                cols = _page_columns(words)
                if not cols:
                    continue
                header_bottom = max(c[3] for c in cols)
                for w in words:
                    match = _DAY.match(w["text"])
                    if not match or w["top"] <= header_bottom:
                        continue
                    day = int(match.group(1))
                    if not 1 <= day <= 31:
                        continue
                    xc = (w["x0"] + w["x1"]) / 2
                    for month, left, right, _ in cols:
                        if left <= xc < right:
                            cells.setdefault((month, day), []).append(_is_black(w.get("non_stroking_color")))
                            break
    except Exception:
        return None
    if not cells:
        return None

    problems: dict[int, list[str]] = {}
    for i, series in enumerate(schedules):
        found = []
        for entry in series.get("dates") or []:
            try:
                d = date.fromisoformat(entry["date"][:10])
            except (KeyError, ValueError):
                continue
            printed = cells.get((d.month, d.day))
            if not printed:
                found.append(f"{d.isoformat()} is not printed in the {d.month:02d} column of the PDF")
            elif entry.get("is_exception") and all(printed):
                found.append(f"{d.isoformat()} is flagged as exception but printed in black")
        if found:
            problems[i] = found
    return problems
