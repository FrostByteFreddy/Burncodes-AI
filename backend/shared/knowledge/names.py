"""
shared/knowledge/names.py

Which known names (event series, page titles) a chat question means, also
when it's misspelled: "wann ist find our follow" means "find your flow!
Festival 2026". The chat model searches with the visitor's words, and a typo
in a name finds nothing; told the probable name, it searches with that.

Matching compares the question's words with every run of 2–5 words of a name
(so "find your flow" inside "find your flow! Festival 2026" counts), letter
by letter. Runs made only of common words ("online training", "in der")
don't count. No AI call: 5–20 ms per question on 1000 names (letter-triple index).
"""
import re
import unicodedata
from difflib import SequenceMatcher
from functools import lru_cache

# similar enough to be a typo of the name ("find our follow" ~ "find your flow": 0.90)
TYPO_SIMILARITY = 0.82
_MIN_CHARS = 8          # a name part spelled exactly right
_MIN_TYPO_CHARS = 12    # misspelled: shorter parts match by chance ("live event" ~ "life event")
_MAX_RUN = 5
_COMMON = {
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem", "einer", "und", "oder",
    "mit", "von", "vom", "zum", "zur", "fur", "auf", "aus", "bei", "nach", "uber", "unter", "ins", "im",
    "in", "an", "am", "zu", "ist", "wann", "wie", "was", "wo", "wer", "gibt", "es", "mein", "meine",
    "dein", "deine", "the", "a", "an", "of", "for", "and", "to", "on", "at", "is", "my", "your", "with",
    "online", "training", "onlinetraining", "kurs", "course", "event", "events", "start", "neu", "neue",
    "neues", "new", "live", "teil", "lektion", "lesson", "bonus", "beitrag", "seite", "page",
    "trainings", "onlinetrainings", "kurse", "courses", "lektionen", "lessons", "seiten", "pages",
}


def fold(text: str) -> str:
    """Lowercase ASCII words: 'Find your Flow!' -> 'find your flow'."""
    text = unicodedata.normalize("NFKD", (text or "").lower()).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


@lru_cache(maxsize=20_000)
def _runs(name: str) -> tuple[str, ...]:
    """Every run of 2–5 consecutive words of a folded name that says something (not only common words or numbers)."""
    words = name.split()
    out = []
    for size in range(2, _MAX_RUN + 1):
        for i in range(len(words) - size + 1):
            run = words[i:i + size]
            if all(w in _COMMON or w.isdigit() for w in run):
                continue
            text = " ".join(run)
            if len(text) >= _MIN_CHARS:
                out.append(text)
    return tuple(out)


def _trigrams(text: str) -> set[str]:
    padded = f" {text} "
    return {padded[i:i + 3] for i in range(len(padded) - 2)}


# a typo keeps most letter triples: "find our follow" shares 9 of 15 with "find your flow"
_MIN_SHARED_TRIGRAMS = 0.4


@lru_cache(maxsize=64)
def _index(names: tuple[str, ...]):
    """Per name list (cached): folded names, name parts that may be misspelled, and a triple index over those parts."""
    folded = {}
    typo_runs: dict[str, list[str]] = {}   # part -> names it belongs to
    for name in names:
        f = fold(name)
        if not f:
            continue
        folded[name] = (f, _runs(f))
        for run in folded[name][1]:
            if len(run) >= _MIN_TYPO_CHARS:
                typo_runs.setdefault(run, []).append(name)
    runs = list(typo_runs)
    sizes = [len(_trigrams(r)) for r in runs]
    by_trigram: dict[str, list[int]] = {}
    for i, run in enumerate(runs):
        for t in _trigrams(run):
            by_trigram.setdefault(t, []).append(i)
    return folded, runs, sizes, typo_runs, by_trigram


def mentioned(names: list[str], question: str, limit: int = 3) -> list[tuple[str, float]]:
    """
    The names the question probably means, surest first: [(name, similarity)].
    1.0: the whole name, 0.97: part of it spelled right, below: a typo of a part.
    """
    q = fold(question)
    if not q:
        return []
    folded, runs, sizes, typo_runs, by_trigram = _index(tuple(dict.fromkeys(n for n in names if n)))
    padded, q_words = f" {q} ", q.split()

    best: dict[str, float] = {}
    for name, (f, name_runs) in folded.items():
        if f" {f} " in padded:
            best[name] = 1.0
        elif any(f" {run} " in padded for run in name_runs):
            best[name] = 0.97

    windows = {" ".join(q_words[i:i + w]) for w in range(1, _MAX_RUN + 2) for i in range(len(q_words) - w + 1)}
    matcher = SequenceMatcher(None)
    for window in windows:
        if len(window) < _MIN_TYPO_CHARS - 4:
            continue
        grams = _trigrams(window)
        shared: dict[int, int] = {}
        for t in grams:
            for i in by_trigram.get(t, ()):
                shared[i] = shared.get(i, 0) + 1
        matcher.set_seq2(window)
        for i, count in shared.items():
            run = runs[i]
            if count < _MIN_SHARED_TRIGRAMS * max(sizes[i], len(grams)):
                continue
            if 2 * min(len(run), len(window)) / (len(run) + len(window)) < TYPO_SIMILARITY:
                continue
            matcher.set_seq1(run)
            ratio = matcher.ratio()
            if ratio >= TYPO_SIMILARITY:
                ratio = min(ratio, 0.96)   # a typo; a part spelled right already scored 0.97
                for name in typo_runs[run]:
                    if ratio > best.get(name, 0):
                        best[name] = ratio

    scored = sorted(best.items(), key=lambda x: -x[1])
    return [(name, round(score, 3)) for name, score in scored[:limit]]
