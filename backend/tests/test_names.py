"""
Recognising the names a chat question means, also misspelled
("find our follow" → "find your flow! Festival 2026"), without false hits.
"""
from app.knowledge.names import mentioned

NAMES = [
    "find your flow! Festival 2026",
    "Find Your Flow Event 2019",
    "Enjoy This Life Event",
    "Joe Dispenza",
    "Eckhart Tolle",
    "Start des Online-Trainings",
    "Onlinetraining",
    "Kehricht",
]


def _names(question):
    return [n for n, _ in mentioned(NAMES, question, limit=5)]


def test_a_misspelled_name_is_recognised():
    hits = mentioned(NAMES, "Wann ist find our follow?")
    assert {n for n, _ in hits} == {"find your flow! Festival 2026", "Find Your Flow Event 2019"}
    assert all(0.82 <= score < 0.97 for _, score in hits)   # a typo, not an exact match


def test_names_of_people_with_typos():
    assert _names("Do you have a course by Joe Dispensa?") == ["Joe Dispenza"]
    assert _names("Infos zu Ekhart Tole bitte") == ["Eckhart Tolle"]


def test_exact_names_and_parts_score_higher_than_typos():
    assert mentioned(NAMES, "Wann ist Kehricht?") == [("Kehricht", 1.0)]
    assert mentioned(NAMES, "wann ist das find your flow festival")[0][1] == 0.97


def test_short_words_one_letter_apart_are_not_a_typo():
    # "live event" vs "life event": too short to tell a typo from another word
    assert _names("Wann ist das nächste Live-Event?") == []


def test_ordinary_questions_name_nothing():
    for q in ("Was kostet das?", "Kann ich mein Abo kündigen?", "Hallo", ""):
        assert _names(q) == []


def test_common_words_alone_do_not_make_a_typo_match():
    # "Onlinetraining" is a whole name here; "Start des Online-Trainings" must not count as its typo
    assert mentioned(NAMES, "Wie funktioniert das Onlinetraining?") == [("Onlinetraining", 1.0)]
