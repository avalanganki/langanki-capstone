from unittest.mock import MagicMock, patch

import pytest
from postgrest.exceptions import APIError
from streamlit.testing.v1 import AppTest


class FakeClient:
    """In-memory stand-in for the Supabase client: enforces one entry per date."""

    def __init__(self, rows=()):
        self.rows = []
        self._next_id = 1
        for row in rows:
            self._add(dict(row))

    def _add(self, row):
        row["id"] = self._next_id
        self._next_id += 1
        self.rows.append(row)

    def table(self, name):
        assert name == "entries"
        self._query = {"op": None, "eq": None, "desc": False, "limit": None}
        return self

    def insert(self, row):
        self._query.update(op="insert", row=row)
        return self

    def update(self, changes):
        self._query.update(op="update", changes=changes)
        return self

    def select(self, columns):
        self._query["op"] = "select"
        return self

    def order(self, column, desc=False):
        assert column == "entry_date"
        self._query["desc"] = desc
        return self

    def eq(self, column, value):
        self._query["eq"] = (column, value)
        return self

    def limit(self, n):
        self._query["limit"] = n
        return self

    def execute(self):
        q = self._query
        if q["op"] == "insert":
            row = dict(q["row"])
            if any(r["entry_date"] == row["entry_date"] for r in self.rows):
                raise APIError({"code": "23505", "message": "duplicate key"})
            self._add(row)
            return MagicMock(data=[row])
        rows = list(self.rows)
        if q["eq"]:
            column, value = q["eq"]
            rows = [r for r in rows if r[column] == value]
        if q["op"] == "update":
            for r in rows:
                r.update(q["changes"])
            return MagicMock(data=rows)
        rows.sort(key=lambda r: r["entry_date"], reverse=q["desc"])
        if q["limit"] is not None:
            rows = rows[: q["limit"]]
        return MagicMock(data=rows)


@pytest.fixture
def fake():
    client = FakeClient()
    with patch("db.get_client", return_value=client):
        yield client


def run_app():
    # Default 3s timeout is too short for the first cold import of pandas.
    return AppTest.from_file("app.py").run(timeout=30)


def save(at, answer="Low energy", tags=""):
    at.text_area[0].input(answer)
    at.text_input[0].input(tags)
    return at.button[0].click().run(timeout=30)


def test_app_shows_title_and_sample_nights(fake):
    at = run_app()
    assert not at.exception
    assert at.title[0].value == "Patterns"
    table = at.dataframe[0].value
    assert len(table) == 4
    assert list(table.columns) == ["Date", "Sleep score", "Readiness", "HRV (ms)"]
    assert not table.isnull().values.any()
    assert "Based on 4 nights." in [c.value for c in at.caption]


def test_tonight_tab_has_three_questions_and_tags(fake):
    at = run_app()
    assert [t.label for t in at.tabs] == ["Tonight", "Past entries"]
    assert len(at.text_area) == 3
    assert at.text_input[0].label == "Tags (comma-separated)"


def find_forms(node):
    if getattr(node, "type", None) == "form":
        yield node
    for child in getattr(node, "children", {}).values():
        yield from find_forms(child)


def test_enter_key_does_not_save(fake):
    # AppTest can't press keys, so check the form is built with Enter-to-submit off.
    at = run_app()
    forms = list(find_forms(at._tree))
    assert len(forms) == 1
    assert forms[0].proto.form.enter_to_submit is False


def test_save_shows_confirmation_and_stores_row(fake):
    at = save(run_app(), tags=" Late Caffeine, stress,,stress ")
    assert not at.exception
    date = at.date_input[0].value.isoformat()
    assert at.success[0].value == f"Saved your entry for {date}."
    assert len(fake.rows) == 1
    assert fake.rows[0]["tags"] == ["late caffeine", "stress"]


def test_blank_form_is_refused(fake):
    at = save(run_app(), answer="")
    assert at.warning[0].value == "Answer at least one question to save."
    assert fake.rows == []


def test_second_save_for_same_date_is_refused(fake):
    at = save(run_app())
    at = save(at, answer="Different answer")
    assert at.warning[0].value == (
        "You already have an entry for this date. Edit it in Past entries."
    )
    assert len(fake.rows) == 1
    assert fake.rows[0]["answers"][0]["answer"] == "Low energy"


# --- Past entries (issue #4) ---

QS = (
    "How was your energy this afternoon?",
    "When was your last caffeine today?",
    "How did you wind down tonight?",
)


def entry(date, texts, tags):
    return {
        "entry_date": date,
        "answers": [{"question": q, "answer": t} for q, t in zip(QS, texts)],
        "tags": tags,
    }


@pytest.fixture
def two_entries():
    client = FakeClient(
        [
            entry("2000-01-01", ["synthetic older", "", "read"], []),
            entry("2000-01-05", ["synthetic newer", "2pm", "walk"], ["late caffeine", "stress"]),
        ]
    )
    with patch("db.get_client", return_value=client):
        yield client


def body_text(at):
    return [m.value for m in at.markdown]


def test_past_entries_empty_state(fake):
    at = run_app()
    assert not at.exception
    assert "No entries yet. Save one from Tonight." in [i.value for i in at.info]


def test_past_entries_listed_newest_first_with_count(two_entries):
    at = run_app()
    assert not at.exception
    box = at.selectbox[0]
    assert box.options == ["Wed, Jan 5, 2000", "Sat, Jan 1, 2000"]
    assert box.value == 2  # newest selected by default
    assert "2 entries." in [c.value for c in at.caption]


def test_selecting_entry_shows_answers_and_tags(two_entries):
    at = run_app()
    at.selectbox[0].set_value(1).run(timeout=30)
    text = body_text(at)
    for q in QS:
        assert q in text
    assert "synthetic older" in text
    assert "No answer" in text
    assert "Tags: No tags" in text

    at.selectbox[0].set_value(2).run(timeout=30)
    text = body_text(at)
    assert "synthetic newer" in text and "No answer" not in text
    assert "Tags: late caffeine, stress" in text


def test_single_entry_count_is_singular(fake):
    at = save(run_app())
    assert "1 entry." in [c.value for c in at.caption]


# --- Edit an entry (issue #5) ---


def open_edit(at):
    return at.button(key="edit").click().run(timeout=30)


def edit_areas(at):
    # Tonight's 3 text areas come first; the edit form's follow.
    return at.text_area[3:]


def test_edit_answer_and_tag_then_save(two_entries):
    at = open_edit(run_app())  # newest entry (2000-01-05) is selected by default
    assert not at.exception
    areas = edit_areas(at)
    assert [a.value for a in areas] == ["synthetic newer", "2pm", "walk"]
    tags_box = at.text_input[1]
    assert tags_box.value == "late caffeine, stress"

    areas[0].input("synthetic edited")
    tags_box.input("stress, Nap")
    at = at.button(key="save_changes").click().run(timeout=30)
    assert not at.exception
    assert "Updated your entry for 2000-01-05." in [s.value for s in at.success]

    row = next(r for r in two_entries.rows if r["id"] == 2)
    assert row["answers"][0]["answer"] == "synthetic edited"
    assert row["tags"] == ["stress", "nap"]
    assert row["entry_date"] == "2000-01-05"
    assert "updated_at" in row

    # Back in view mode with the new values.
    text = body_text(at)
    assert "synthetic edited" in text
    assert "Tags: stress, nap" in text
    assert len(at.text_area) == 3


def test_cancel_leaves_entry_unchanged(two_entries):
    at = open_edit(run_app())
    edit_areas(at)[0].input("should not save")
    at = at.button(key="cancel_edit").click().run(timeout=30)
    assert not at.exception
    row = next(r for r in two_entries.rows if r["id"] == 2)
    assert row["answers"][0]["answer"] == "synthetic newer"
    assert "updated_at" not in row
    assert "synthetic newer" in body_text(at)
    assert len(at.text_area) == 3


def test_edit_all_blank_is_refused(two_entries):
    at = open_edit(run_app())
    for a in edit_areas(at):
        a.input("")
    at = at.button(key="save_changes").click().run(timeout=30)
    assert "Answer at least one question to save." in [w.value for w in at.warning]
    row = next(r for r in two_entries.rows if r["id"] == 2)
    assert row["answers"][0]["answer"] == "synthetic newer"
    assert len(edit_areas(at)) == 3  # still editing


def test_edit_mode_date_is_not_an_input(two_entries):
    at = open_edit(run_app())
    assert "Date: Wed, Jan 5, 2000" in body_text(at)
    assert len(at.date_input) == 1  # only Tonight's date picker
