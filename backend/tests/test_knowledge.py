"""Knowledge pipeline building blocks: Markdown, hashing, validation, cross-check, estimate."""
from datetime import date

import pytest

from app.knowledge import jobs
from app.knowledge.markdown import (
    content_hash,
    html_to_markdown,
    number_lines,
    pdf_page_count,
    slice_lines,
)
from app.knowledge.understanding import section_documents, validate_schedule

PAGE = """<html><head><title>Entsorgung – Stadt Zofingen</title><script>var t=Date.now()</script></head>
<body>
  <header><nav><a href="/">Home</a> <a href="/a">A</a></nav></header>
  <div class="cookie-banner">Wir verwenden Cookies <button>OK</button></div>
  <main>
    <h1>Entsorgung</h1>
    <p>Der Werkhof ist <b>Mo–Fr 07.30–11.30 Uhr</b> geöffnet.</p>
    <table><tr><th>Sack</th><th>Preis</th></tr><tr><td>35 l</td><td>CHF 18.–</td></tr></table>
    <h2>Agenda</h2><ul><li>Repair Café am 24. Oktober</li></ul>
  </main>
  <footer>© Stadt Zofingen · Impressum</footer>
</body></html>"""


class TestMarkdown:
    def test_keeps_content_drops_chrome(self):
        title, md = html_to_markdown(PAGE)
        assert title == "Entsorgung – Stadt Zofingen"
        assert "Mo–Fr 07.30–11.30 Uhr" in md
        assert "Repair Café" in md          # teasers/agenda survive (trafilatura drops these)
        assert "| 35 l | CHF 18.– |" in md  # tables stay tables
        for chrome in ("Home", "Cookies", "Impressum", "Date.now"):
            assert chrome not in md

    def test_state_classes_on_root_do_not_remove_the_page(self):
        # zofingen.ch renders <html class="… show--consent …"> while the cookie banner is open
        page = PAGE.replace("<html>", '<html class="js show--consent">').replace("<body>", '<body class="has-cookie-banner">')
        _, md = html_to_markdown(page)
        assert "Mo–Fr 07.30–11.30 Uhr" in md

    def test_hash_ignores_script_and_whitespace_noise(self):
        a = PAGE
        b = PAGE.replace("var t=Date.now()", "var t=1730000000").replace("<p>", "<p>   ")
        assert content_hash(html_to_markdown(a)[1]) == content_hash(html_to_markdown(b)[1])

    def test_hash_changes_with_content(self):
        changed = PAGE.replace("07.30–11.30", "08.00–12.00")
        assert content_hash(html_to_markdown(PAGE)[1]) != content_hash(html_to_markdown(changed)[1])

    def test_line_numbers_round_trip(self):
        md = "a\nb\nc\nd"
        assert number_lines(md).splitlines()[2] == "3| c"
        assert slice_lines(md, 2, 3) == "b\nc"
        assert slice_lines(md, 3, 99) == "c\nd"
        assert slice_lines(md, 4, 2) == ""

    def test_pdf_page_count(self):
        assert pdf_page_count(b"<< /Type /Pages /Count 2 >> << /Type /Page >> << /Type/Page >>") == 2
        assert pdf_page_count(b"x" * 130_000) == 2  # no markers: size fallback


def _series(dates, weekday="Montag"):
    return {"name": "Kehricht", "zone": "Zone 1", "regular_weekday": weekday,
            "dates": [{"date": d, "is_exception": exc} for d, exc in dates]}


class TestScheduleValidation:
    def test_valid_series_with_exception(self):
        # 2025-04-14 Monday, 2025-04-23 Wednesday (exception after Easter)
        assert validate_schedule(_series([("2025-04-14", False), ("2025-04-23", True)])) == []

    def test_off_weekday_without_exception_flag(self):
        problems = validate_schedule(_series([("2025-05-30", False)]))
        assert problems and "not on the printed weekday" in problems[0]

    def test_exception_on_regular_weekday(self):
        problems = validate_schedule(_series([("2025-09-29", True)]))
        assert problems and "falls on the regular weekday" in problems[0]

    def test_duplicates_and_garbage(self):
        problems = validate_schedule(_series([("2025-04-14", False), ("2025-04-14", False), ("31.12.2025", False)]))
        assert any("duplicate" in p for p in problems)
        assert any("unparseable" in p for p in problems)

    def test_no_weekday_rule_for_unlabelled_series(self):
        assert validate_schedule(_series([("2025-02-23", False)], weekday="")) == []


class _FakePage:
    def __init__(self, words):
        self._words = words

    def extract_words(self, extra_attrs=None):
        return self._words


class _FakePdf:
    def __init__(self, words):
        self.pages = [_FakePage(words)]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _w(text, x, top, color=(0, 0, 0, 1)):
    return {"text": text, "x0": x - 5, "x1": x + 5, "top": top, "bottom": top + 8, "non_stroking_color": color}


MONTHS = ["Jan", "Feb", "März", "Apr", "Mai", "Juni", "Juli", "Aug", "Sept", "Okt", "Nov", "Dez"]


def _grid_words():
    words = [_w(m, 100 + i * 40, 80) for i, m in enumerate(MONTHS)]
    words += [_w("6.", 100, 98), _w("13.", 100, 110)]            # January
    words += [_w("23.", 100 + 3 * 40, 98, color=(0, 0.9, 0.8, 0))]  # April, red
    words += [_w("Mai", 300, 400)]                                 # "…2. Mai" in running text below
    return words


class TestPdfCrosscheck:
    @pytest.fixture(autouse=True)
    def fake_pdf(self, monkeypatch):
        import pdfplumber
        monkeypatch.setattr(pdfplumber, "open", lambda _: _FakePdf(_grid_words()))

    def test_matching_dates_pass(self):
        from app.knowledge.pdf_crosscheck import crosscheck_schedules
        sched = [{"dates": [{"date": "2025-01-06", "is_exception": False},
                            {"date": "2025-01-13", "is_exception": False},
                            {"date": "2025-04-23", "is_exception": True}]}]
        assert crosscheck_schedules(b"%PDF", sched) == {0: []}

    def test_invented_dates_are_reported_colour_is_ignored(self):
        from app.knowledge.pdf_crosscheck import crosscheck_schedules
        sched = [{"dates": [{"date": "2025-07-03", "is_exception": True},     # not printed at all
                            {"date": "2025-01-13", "is_exception": True}]}]   # printed (black) — fine
        assert crosscheck_schedules(b"%PDF", sched) == {0: ["2025-07-03"]}

    def test_series_outside_the_grid_is_not_judged(self):
        from app.knowledge.pdf_crosscheck import crosscheck_schedules
        # e.g. "Bottenstein: … und 7. Januar" printed as text below the grid
        assert crosscheck_schedules(b"%PDF", [{"dates": [{"date": "2025-01-07", "is_exception": False}]}]) == {}

    def test_no_month_header_means_no_verdict(self, monkeypatch):
        import pdfplumber
        from app.knowledge.pdf_crosscheck import crosscheck_schedules
        monkeypatch.setattr(pdfplumber, "open", lambda _: _FakePdf([_w("6.", 100, 98)]))
        assert crosscheck_schedules(b"%PDF", [{"dates": [{"date": "2025-01-06", "is_exception": False}]}]) is None


class TestSectionDocuments:
    def test_sections_carry_context_and_facts_doc_skips_unverified(self):
        result = {
            "title": "Abfallkalender 2025", "summary": "Abfuhrdaten der Stadt.",
            "sections": [{"heading": "Tarife", "text": "| Sack | Preis |"}, {"heading": "Leer", "text": ""}],
            "facts": [{"label": "Werkhof", "value": "Mo–Fr 07.30–11.30", "valid_from": "", "valid_to": ""}],
            "schedules": [
                {"name": "Kehricht", "zone": "Zone 1", "notes": "", "dates": [{"date": "2025-04-23", "is_exception": True}]},
                {"name": "Grüngut", "zone": "", "notes": "", "_problems": ["x"], "dates": [{"date": "2025-01-01", "is_exception": False}]},
            ],
            "single_events": [{"name": "Repair Café", "dates": ["2025-05-03"], "notes": ""}],
        }
        docs = section_documents(result, "https://x/kalender.pdf")
        assert len(docs) == 2  # one non-empty section + facts/dates
        assert "Kontext: Abfuhrdaten der Stadt." in docs[0][1] and "Quelle: https://x/kalender.pdf" in docs[0][1]
        facts = docs[1][1]
        assert "Werkhof: Mo–Fr 07.30–11.30" in facts
        assert "Kehricht Zone 1: 2025-04-23 (Ausnahme)" in facts
        assert "Grüngut" not in facts  # failed validation → not indexed as fact
        assert "Repair Café: 2025-05-03" in facts


class TestEstimate:
    def test_page_and_pdf_estimates(self):
        page_in, page_out, _ = jobs.estimate_source({"content_tokens": 1000, "file_pages": None})
        assert page_in == 2000 + 1300 and page_out == 500 + 600
        pdf_in, pdf_out, _ = jobs.estimate_source({"file_pages": 2})
        # calibrated on the real 2-page Abfallkalender: ~7.7k in / ~13k out
        assert 7000 <= pdf_in <= 8500 and 12000 <= pdf_out <= 14000


class TestChatDates:
    def test_upcoming_and_expired_series(self, monkeypatch):
        import importlib
        import sys
        sys.modules.setdefault("app.prompts", type(sys)("app.prompts"))
        sys.modules["app.prompts"].FINE_TUNE_RULE_PROMPT = "{trigger}{instruction}"
        # worker_chat's module isn't on the API path; load it by file
        spec = importlib.util.spec_from_file_location(
            "chat_tasks", __file__.replace("tests/test_knowledge.py", "services/worker_chat/app/chat/tasks.py"))
        chat = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(chat)

        rows = [
            {"series": "Kehricht", "zone": "Zone 1", "event_date": "2026-10-26", "is_exception": False, "notes": ""},
            {"series": "Kehricht", "zone": "Zone 1", "event_date": "2026-11-02", "is_exception": True, "notes": ""},
            {"series": "Grünabfuhr", "zone": "", "event_date": "2025-12-09", "is_exception": False, "notes": ""},
        ]

        class Q:
            def __getattr__(self, name):
                return lambda *a, **k: self

            def execute(self):
                return type("R", (), {"data": rows})()

        monkeypatch.setattr(chat, "supabase", type("S", (), {"table": lambda self, n: Q()})())
        text = chat._dates_context("t", date(2026, 10, 24))
        assert text.startswith("Today is Sat 2026-10-24.")
        assert "Kehricht (Zone 1): next Mon 2026-10-26, Mon 2026-11-02 (exception)" in text
        assert "Grünabfuhr: no future dates known — the published schedule ends 2025-12-09" in text


class TestSystemInstruction:
    @staticmethod
    def _chat():
        import importlib
        import sys
        sys.modules.setdefault("app.prompts", type(sys)("app.prompts"))
        sys.modules["app.prompts"].FINE_TUNE_RULE_PROMPT = "When {trigger}: {instruction}"
        spec = importlib.util.spec_from_file_location(
            "chat_tasks", __file__.replace("tests/test_knowledge.py", "services/worker_chat/app/chat/tasks.py"))
        chat = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(chat)
        return chat

    def test_legacy_template_slots_are_removed(self):
        chat = self._chat()
        cfg = {"system_persona": "Be polite.",
               "rag_prompt_template": "{persona}\n\n{fine_tune_instructions}\n\nAnswer from context.\n\n<context>\n{context}\n</context>\n\nFrage: {input}\n"}
        text = chat._build_system_instruction(cfg, [{"trigger": "asked about fees", "instruction": "link the fee list"}])
        assert text == "Be polite.\n\nWhen asked about fees: link the fee list\n\nAnswer from context."

    def test_language_rule_comes_last_and_follows_the_user(self):
        chat = self._chat()
        rule = chat._language_rule()
        assert "language of the user's most recent message" in rule
        assert rule.endswith("reply in the language of your documents.")

    def test_persona_and_rules_survive_an_edited_template(self):
        chat = self._chat()
        cfg = {"system_persona": "Be brief.", "rag_prompt_template": "Only use the documents."}
        text = chat._build_system_instruction(cfg, [{"trigger": "x", "instruction": "y"}])
        assert text.startswith("Be brief.") and "When x: y" in text and text.endswith("Only use the documents.")


class TestValidate:
    """learn._validate: which extracted dates become trusted events."""

    @staticmethod
    def _run(series, crosscheck):
        from app.knowledge.learn import _validate
        result = {"language": "de", "warnings": [], "schedules": series, "_crosscheck": crosscheck}
        _validate(result)
        return result

    @staticmethod
    def _zone2(n=10):
        # Fridays from 2026-01-02, plus Thursday 2026-04-02 (Good Friday shift, printed black)
        from datetime import date, timedelta
        dates = [{"date": (date(2026, 1, 2) + timedelta(weeks=i)).isoformat(), "is_exception": False} for i in range(n)]
        dates.append({"date": "2026-04-02", "is_exception": True})
        return {"name": "Hauskehricht", "zone": "Zone 2", "regular_weekday": "Freitag", "notes": "", "dates": dates}

    def test_grid_verified_series_kept_and_exception_from_weekday(self):
        series = self._zone2()
        series["dates"][0]["is_exception"] = True   # model wrongly flags a regular Friday
        result = self._run([series], {0: []})
        s = result["schedules"][0]
        assert "_problems" not in s and len(s["dates"]) == 11
        flags = {d["date"]: d["is_exception"] for d in s["dates"]}
        assert flags["2026-04-02"] is True and flags["2026-01-02"] is False
        assert result["warnings"] == []

    def test_few_missing_dates_are_dropped_with_readable_warning(self):
        result = self._run([self._zone2()], {0: ["2026-01-09"]})
        s = result["schedules"][0]
        assert "_problems" not in s and "2026-01-09" not in [d["date"] for d in s["dates"]]
        assert "09.01.2026" in result["warnings"][0] and "printed" not in result["warnings"][0]

    def test_many_missing_dates_reject_the_series(self):
        missing = [d["date"] for d in self._zone2()["dates"][:5]]
        result = self._run([self._zone2()], {0: missing})
        assert result["schedules"][0]["_problems"]
        assert "nicht zuverlässig gelesen" in result["warnings"][0]

    def test_series_outside_grid_uses_weekday_rule(self):
        bottenstein = {"name": "Hauskehricht", "zone": "Bottenstein", "regular_weekday": "", "notes": "",
                       "dates": [{"date": "2026-01-07", "is_exception": False}]}
        result = self._run([bottenstein], {})   # crosscheck ran, series not in grid
        assert "_problems" not in result["schedules"][0]
        assert result["warnings"] == []

    def test_without_text_layer_unflagged_off_weekday_rejects(self):
        series = self._zone2()
        series["dates"][-1]["is_exception"] = False
        result = self._run([series], None)
        assert result["schedules"][0]["_problems"]


class TestReviewFindings:
    """review._clean: which model findings become rows staff see."""

    LOGS = [
        {"id": 10, "user_message": "Hallo", "ai_message": "Hallo!"},
        {"id": 11, "user_message": "Wann ist Grünabfuhr?", "ai_message": "Dazu habe ich keine Informationen."},
        {"id": 12, "user_message": "Das stimmt nicht", "ai_message": "Entschuldigung."},
    ]

    def test_keeps_new_turns_and_attaches_log_id(self):
        from app.knowledge.review import _clean
        raw = [
            {"turn": 2, "kind": "unanswered", "question": "Wann ist Grünabfuhr?", "problem": "Keine Antwort", "suggestion": "Kalender ergänzen"},
            {"turn": 3, "kind": "pushback", "question": "", "problem": "Widerspruch", "suggestion": ""},
        ]
        out = _clean(raw, self.LOGS, first_new=1)
        assert [f["log_id"] for f in out] == [11, 12]
        assert out[1]["question"] == "Das stimmt nicht"  # falls back to the visitor's message

    def test_drops_old_turns_unknown_kinds_duplicates_and_empty(self):
        from app.knowledge.review import _clean
        raw = [
            {"turn": 1, "kind": "unanswered", "question": "Hallo", "problem": "x", "suggestion": ""},  # reviewed before
            {"turn": 2, "kind": "praise", "question": "q", "problem": "x", "suggestion": ""},
            {"turn": 2, "kind": "unanswered", "question": "q", "problem": "x", "suggestion": ""},
            {"turn": 2, "kind": "unanswered", "question": "q", "problem": "again", "suggestion": ""},
            {"turn": 3, "kind": "wrong", "question": "q", "problem": "", "suggestion": ""},
            {"turn": 9, "kind": "wrong", "question": "q", "problem": "x", "suggestion": ""},
            "garbage",
        ]
        out = _clean(raw, self.LOGS, first_new=1)
        assert len(out) == 1 and out[0]["kind"] == "unanswered" and out[0]["log_id"] == 11
