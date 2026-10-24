"""
shared/knowledge/pdf_crosscheck.py

Second, independent reading of calendar grids in born-digital PDFs.

Gemini reads the page visually. That's mostly right, but it occasionally
invents a date or takes one from a neighbouring row. Born-digital PDFs
(InDesign, Word exports) carry every word with its position, which is enough
to verify each extracted date without knowing the layout:

  - find the header line with the month names (Jan, Februar, März, ...)
    → one column per month
  - each extracted date's day number must be printed in that month's column

Colour is deliberately not checked: designers don't reliably colour every
moved date (Zofingen prints the Good-Friday shift on 2 April 2026 in black).
Whether a date is an exception follows from the weekday instead.

Returns None when the PDF has no text layer or no month header line — then
only the weekday validation applies.
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


def printed_grid_dates(pdf_bytes: bytes) -> set[tuple[int, int]] | None:
    """{(month, day)} printed below a month header line, or None if there's no grid."""
    try:
        import pdfplumber
    except ImportError:
        return None
    cells: set[tuple[int, int]] = set()
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                words = page.extract_words()
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
                            cells.add((month, day))
                            break
    except Exception:
        return None
    return cells or None


def crosscheck_schedules(pdf_bytes: bytes, schedules: list[dict]) -> dict[int, list[str]] | None:
    """
    Returns {schedule_index: [ISO dates not printed in their month column]}
    for every schedule that comes from the grid ([] = all dates verified), or
    None if the PDF can't be checked. A series with *no* date in the grid
    isn't a grid series (e.g. a line of text under the calendar); it's left
    out of the result and handled by the weekday validation.
    """
    cells = printed_grid_dates(pdf_bytes)
    if cells is None:
        return None
    missing: dict[int, list[str]] = {}
    for i, series in enumerate(schedules):
        dates = []
        for entry in series.get("dates") or []:
            try:
                dates.append(date.fromisoformat(entry["date"][:10]))
            except (KeyError, ValueError):
                continue
        if not dates:
            continue
        absent = [d.isoformat() for d in dates if (d.month, d.day) not in cells]
        if len(absent) < len(dates):
            missing[i] = absent
    return missing
