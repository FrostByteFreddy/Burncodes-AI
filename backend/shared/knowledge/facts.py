"""
shared/knowledge/facts.py

Facts extracted at learning time (tenant_facts: fees, phone numbers, figures)
matched to a chat question. File Search alone misses short facts ("3'883
Einwohner" sits next to the tax rates and loses the ranking) and on follow-ups
the model filled the gap from memory (a dog tax of 80 Fr. where the page says
100). The facts whose label shares a word with the question go to the model as
verified values.

Matching is by word stems, so "Einwohner" finds "Einwohnerzahl" and "Hund"
finds "Hundetaxe"; words in many labels (the municipality's own name) don't
count.
"""
import re
import unicodedata

MAX_FACTS = 12
_MIN_WORD = 4
_COMMON_SHARE = 0.05   # a word in more labels than this says nothing about the question
_STOP = {
    "wann", "wird", "werden", "gibt", "eine", "einen", "einer", "eines", "kann", "konnen", "sind", "viele",
    "haben", "nach", "mein", "meine", "meinen", "dass", "oder", "wenn", "auch", "noch", "bitte", "welche",
    "welcher", "welches", "warum", "dann", "aber", "darf", "muss", "brauche", "mochte", "where", "when",
    "what", "which", "does", "have", "with", "from", "this", "that", "there", "about", "your", "dort",
    "hier", "heute", "morgen", "dies", "diese", "dieser", "uber", "unter", "zwischen", "etwas", "alle",
}


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text)


def _stems(text: str) -> set[str]:
    """Question words cut to a stem: 'Einwohner' -> 'einwohn', 'kostet' -> 'koste'; short words stay whole."""
    out = set()
    for w in _fold(text).split():
        if len(w) >= _MIN_WORD and w not in _STOP and not w.isdigit():
            out.add(w if len(w) <= 5 else w[:-1] if len(w) == 6 else w[:-2])
    return out


def _hit(stem: str, text: str) -> bool:
    """The stem starts a word of the text, or (long enough to be safe) sits inside a compound."""
    return (" " + stem) in (" " + text) or (len(stem) >= 5 and stem in text)


def relevant_facts(facts: list[dict], text: str, limit: int = MAX_FACTS) -> list[dict]:
    """The facts whose label (mostly) or value matches the question's words, best first."""
    stems = _stems(text)
    if not stems or not facts:
        return []
    labels = [_fold(f.get("label")) for f in facts]
    common = {s for s in stems if sum(_hit(s, l) for l in labels) > max(3, _COMMON_SHARE * len(facts))}
    stems -= common
    if not stems:
        return []
    scored = []
    for i, (f, label) in enumerate(zip(facts, labels)):
        value = _fold(f.get("value"))
        hits = sum(_hit(s, label) for s in stems)
        if not hits:
            continue   # a word only in the value is too loose (every fee mentions "CHF")
        scored.append((-(3 * hits + sum(_hit(s, value) for s in stems)), i, f))
    scored.sort(key=lambda x: x[:2])
    return [f for _, _, f in scored[:limit]]


def facts_context(facts: list[dict], sources: dict) -> str:
    """The matched facts as a block for the chat's instructions ('' without any)."""
    if not facts:
        return ""
    lines = ["Verified facts from this organisation's documents (use these values exactly; "
             "if two facts disagree, give both with their page):"]
    for f in facts:
        src = sources.get(f.get("source_id"))
        lines.append(f"- {f['label']}: {f['value']}" + (f" {{source: {src[0]} {src[1]}}}" if src else ""))
    return "\n".join(lines)


def fact_mentioned(fact: dict, answer: str) -> bool:
    """Whether the answer uses the fact's value (its figures, or its opening words)."""
    digits = re.sub(r"\D", "", fact.get("value") or "")
    if len(digits) >= 3 and digits in re.sub(r"\D", "", answer):
        return True
    head = _fold(fact.get("value"))[:24].strip()
    return len(head) >= 8 and head in _fold(answer)
