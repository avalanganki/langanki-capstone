import datetime
from unittest.mock import MagicMock, patch

import pytest
from postgrest.exceptions import APIError
from streamlit.testing.v1 import AppTest


class FakeClient:
    """In-memory stand-in for the Supabase client.

    Tables: `entries` (one entry per date), `oura_connection` (upsert on id), and
    `nights` (upsert on night_date).
    """

    def __init__(self, rows=(), connection=None):
        self.tables = {"entries": [], "oura_connection": [], "nights": []}
        self._next_id = 1
        for row in rows:
            self._add(dict(row))
        if connection:
            self.tables["oura_connection"].append({"id": 1, **connection})

    @property
    def rows(self):
        return self.tables["entries"]

    @property
    def connection_rows(self):
        return self.tables["oura_connection"]

    @property
    def night_rows(self):
        return self.tables["nights"]

    def _add(self, row):
        row["id"] = self._next_id
        self._next_id += 1
        self.tables["entries"].append(row)

    def table(self, name):
        assert name in self.tables, name
        self._name = name
        self._query = {"op": None, "eq": None, "order": None, "desc": None, "limit": None}
        return self

    def insert(self, row):
        self._query.update(op="insert", row=row)
        return self

    def upsert(self, row, on_conflict="id"):
        self._query.update(op="upsert", row=row, key=on_conflict)
        return self

    def delete(self):
        self._query["op"] = "delete"
        return self

    def update(self, changes):
        self._query.update(op="update", changes=changes)
        return self

    def select(self, columns):
        self._query["op"] = "select"
        return self

    def order(self, column, desc=False):
        self._query.update(order=column, desc=desc)
        return self

    def eq(self, column, value):
        self._query["eq"] = (column, value)
        return self

    def limit(self, n):
        self._query["limit"] = n
        return self

    def execute(self):
        q = self._query
        table = self.tables[self._name]
        if q["op"] == "insert":
            row = dict(q["row"])
            if any(r["entry_date"] == row["entry_date"] for r in table):
                raise APIError({"code": "23505", "message": "duplicate key"})
            self._add(row)
            return MagicMock(data=[row])
        if q["op"] == "upsert":
            new = [dict(r) for r in (q["row"] if isinstance(q["row"], list) else [q["row"]])]
            keys = {r[q["key"]] for r in new}
            self.tables[self._name] = [r for r in table if r[q["key"]] not in keys] + new
            return MagicMock(data=new)
        rows = list(table)
        if q["eq"]:
            column, value = q["eq"]
            rows = [r for r in rows if r[column] == value]
        if q["op"] == "delete":
            self.tables[self._name] = [r for r in table if r not in rows]
            return MagicMock(data=rows)
        if q["op"] == "update":
            for r in rows:
                r.update(q["changes"])
            return MagicMock(data=rows)
        if q["order"] is not None:
            rows.sort(key=lambda r: r[q["order"]], reverse=q["desc"])
        if q["limit"] is not None:
            rows = rows[: q["limit"]]
        return MagicMock(data=rows)


BLANK_OURA = {"client_id": "", "client_secret": "", "redirect_uri": "http://localhost:8501/callback/"}
FAKE_OURA = {
    "client_id": "test-client-id",
    "client_secret": "test-client-secret",
    "redirect_uri": "http://localhost:8501/callback/",
}


@pytest.fixture(autouse=True)
def claude_off():
    # Never read the real Claude key in tests. Default: tag suggestions off.
    with patch("tagger.is_configured", return_value=False) as configured:
        yield configured


@pytest.fixture(autouse=True)
def oura_settings():
    # Never read the real .env in tests. Default: Oura not configured yet.
    with patch("oura.get_settings", return_value=dict(BLANK_OURA)) as settings:
        yield settings


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


# --- Delete an entry (issue #6) ---


@pytest.fixture
def three_entries():
    client = FakeClient(
        [
            entry("2000-01-03", ["synthetic middle", "", ""], ["stress"]),
            entry("2000-01-01", ["synthetic oldest", "", ""], []),
            entry("2000-01-05", ["synthetic newest", "", ""], ["nap"]),
        ]
    )
    with patch("db.get_client", return_value=client):
        yield client


def test_delete_confirm_removes_only_selected_entry(three_entries):
    at = run_app()
    at.selectbox[0].set_value(1).run(timeout=30)  # 2000-01-03, the middle date
    at = at.button(key="delete").click().run(timeout=30)
    assert "Delete your entry for 2000-01-03? This can't be undone." in [
        w.value for w in at.warning
    ]
    assert len(three_entries.rows) == 3  # nothing deleted until confirmed

    at = at.button(key="confirm_delete").click().run(timeout=30)
    assert not at.exception
    assert "Deleted your entry for 2000-01-03." in [s.value for s in at.success]
    assert sorted(r["entry_date"] for r in three_entries.rows) == ["2000-01-01", "2000-01-05"]
    assert at.selectbox[0].options == ["Wed, Jan 5, 2000", "Sat, Jan 1, 2000"]
    assert "2 entries." in [c.value for c in at.caption]
    # The other entries are untouched.
    others = {r["entry_date"]: r for r in three_entries.rows}
    assert others["2000-01-05"]["answers"][0]["answer"] == "synthetic newest"
    assert others["2000-01-05"]["tags"] == ["nap"]


def test_delete_cancel_keeps_entry(three_entries):
    at = run_app()
    at = at.button(key="delete").click().run(timeout=30)
    at = at.button(key="cancel_delete").click().run(timeout=30)
    assert not at.exception
    assert len(three_entries.rows) == 3
    assert len(at.selectbox[0].options) == 3
    assert "synthetic newest" in body_text(at)
    assert at.button(key="delete")  # back to normal view


def test_deleting_last_entry_shows_empty_state(fake):
    at = save(run_app())
    at = at.button(key="delete").click().run(timeout=30)
    at = at.button(key="confirm_delete").click().run(timeout=30)
    assert not at.exception
    assert fake.rows == []
    assert any(s.value.startswith("Deleted your entry for ") for s in at.success)
    assert "No entries yet. Save one from Tonight." in [i.value for i in at.info]


# --- Connect Oura (issue #7) ---

TOKENS = {
    "access_token": "test-access",
    "refresh_token": "test-refresh",
    "expires_at": "2000-01-02T00:00:00+00:00",
    "scope": "daily",
}


def all_text(at):
    texts = [m.value for m in at.markdown]
    for kind in (at.success, at.info, at.warning, at.caption):
        texts += [e.value for e in kind]
    return " ".join(str(t) for t in texts)


def run_callback(params):
    at = AppTest.from_file("app.py")
    for k, v in params.items():
        at.query_params[k] = v
    return at.run(timeout=30)


def test_oura_not_configured_shows_waiting_message(fake):
    at = run_app()
    assert not at.exception
    assert "Waiting for Oura app approval. Showing sample data." in [i.value for i in at.sidebar.info]


def test_oura_configured_shows_connect_button(fake, oura_settings):
    oura_settings.return_value = dict(FAKE_OURA)
    at = run_app()
    assert not at.exception
    buttons = at.get("link_button")
    assert len(buttons) == 1
    assert buttons[0].proto.label == "Connect Oura"
    assert "scope=daily" in buttons[0].proto.url


def test_callback_saves_connection(fake, oura_settings):
    oura_settings.return_value = dict(FAKE_OURA)
    with patch("oura.finish_sign_in", return_value=dict(TOKENS)) as finish:
        at = run_callback({"code": "the-code", "state": "the-state"})
    assert not at.exception
    finish.assert_called_once_with("the-state", "the-code")
    assert "Connected to Oura." in [s.value for s in at.success]
    assert len(fake.connection_rows) == 1
    assert fake.connection_rows[0]["access_token"] == "test-access"
    assert "test-access" not in all_text(at)
    assert at.button(key="oura_disconnect")  # sidebar now offers Disconnect


def test_callback_with_bad_state_saves_nothing(fake, oura_settings):
    oura_settings.return_value = dict(FAKE_OURA)
    with patch("oura.requests.post") as post:
        at = run_callback({"code": "the-code", "state": "unknown"})
    assert not at.exception
    post.assert_not_called()
    assert "Sign-in expired or didn't match. Try Connect again." in [w.value for w in at.warning]
    assert fake.connection_rows == []


def test_callback_cancelled(fake, oura_settings):
    oura_settings.return_value = dict(FAKE_OURA)
    at = run_callback({"error": "access_denied"})
    assert not at.exception
    assert "Oura connection was cancelled." in [w.value for w in at.warning]
    assert fake.connection_rows == []


def test_disconnect_removes_tokens(oura_settings):
    oura_settings.return_value = dict(FAKE_OURA)
    client = FakeClient(connection=dict(TOKENS))
    with patch("db.get_client", return_value=client), patch("oura.requests.get") as revoke:
        at = run_app()
        at = at.button(key="oura_disconnect").click().run(timeout=30)
    assert not at.exception
    assert revoke.called
    assert client.connection_rows == []
    assert "Disconnected from Oura." in [s.value for s in at.success]
    assert at.get("link_button")  # back to Connect


# --- Fetch Oura nights (issue #8). Synthetic fixtures; requests is mocked. ---

import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
FAR_FUTURE = {**TOKENS, "expires_at": "2999-01-01T00:00:00+00:00"}


def oura_get(url, params=None, headers=None, timeout=None):
    name = url.rsplit("/", 1)[1]
    body = json.loads((FIXTURES / f"oura_{name}.json").read_text())
    return MagicMock(status_code=200, json=MagicMock(return_value=body))


def connected(oura_settings):
    oura_settings.return_value = dict(FAKE_OURA)
    return FakeClient(connection=dict(FAR_FUTURE))


def test_refresh_saves_nights_and_shows_count(oura_settings):
    client = connected(oura_settings)
    today = datetime.date(2000, 1, 5)
    with patch("db.get_client", return_value=client), patch("oura.requests.get", side_effect=oura_get), patch(
        "oura.datetime.date"
    ) as date:
        date.today.return_value = today
        date.side_effect = datetime.date
        at = run_app()
        assert not any(c.value.startswith("Last updated") for c in at.sidebar.caption)
        at = at.button(key="oura_refresh").click().run(timeout=30)
        assert not at.exception
        assert "Updated 4 nights from Oura." in [s.value for s in at.sidebar.success]
        assert [n["night_date"] for n in sorted(client.night_rows, key=lambda n: n["night_date"])] == [
            "2000-01-01", "2000-01-02", "2000-01-03", "2000-01-04",
        ]
        assert any(c.value.startswith("Last updated ") for c in at.sidebar.caption)
        # Refreshing again updates in place: each night appears once.
        at = at.button(key="oura_refresh").click().run(timeout=30)
    assert len(client.night_rows) == 4
    readiness = {n["night_date"]: n["readiness"] for n in client.night_rows}
    assert readiness["2000-01-02"] is None  # missing stays empty, never zero


def test_refresh_on_403_shows_membership_message_and_saves_nothing(oura_settings):
    client = connected(oura_settings)
    denied = MagicMock(status_code=403)
    with patch("db.get_client", return_value=client), patch("oura.requests.get", return_value=denied):
        at = run_app()
        at = at.button(key="oura_refresh").click().run(timeout=30)
    assert not at.exception
    assert "Oura denied access. An active Oura membership may be needed." in [w.value for w in at.sidebar.warning]
    assert client.night_rows == []


def test_not_configured_has_no_refresh_button(fake):
    at = run_app()
    assert not [b for b in at.button if b.key == "oura_refresh"]


# --- Show Oura nights on Tonight (issue #9). Synthetic rows only. ---

SYNTHETIC_NIGHTS = [
    {"night_date": "2000-01-02", "sleep_score": 74, "readiness": None, "avg_hrv": 47.0, "fetched_at": "2000-01-06T08:00:00+00:00"},
    {"night_date": "2000-01-01", "sleep_score": 81, "readiness": 79, "avg_hrv": 52.5, "fetched_at": "2000-01-06T08:00:00+00:00"},
    {"night_date": "2000-01-03", "sleep_score": 68, "readiness": 62, "avg_hrv": None, "fetched_at": "2000-01-06T08:00:00+00:00"},
]


def test_tonight_sample_label_when_not_connected(fake):
    at = run_app()
    captions = [c.value for c in at.caption]
    assert "Sample data. Not real Oura data." in captions
    assert "From your Oura ring." not in captions


def test_tonight_shows_oura_nights_when_connected(oura_settings):
    client = connected(oura_settings)
    client.tables["nights"] = [dict(r) for r in SYNTHETIC_NIGHTS]
    with patch("db.get_client", return_value=client):
        at = run_app()
    assert not at.exception
    captions = [c.value for c in at.caption]
    assert "From your Oura ring." in captions
    assert "Sample data. Not real Oura data." not in captions
    table = at.dataframe[0].value
    assert list(table["Date"]) == ["2000-01-01", "2000-01-02", "2000-01-03"]
    assert list(table["Readiness"]) == ["79", "No data", "62"]  # missing is "No data", not 0
    assert list(table["HRV (ms)"]) == ["52.5", "47", "No data"]
    assert "Based on 3 nights." in captions


# --- Suggest tags (issue #11). Claude is always mocked. ---

OFF_CAPTION = "Tag suggestions are off (no Claude API key)."
PRIVACY = "Suggest tags sends only your answers, the questions, and your tag list"


def suggest_button(at):
    return at.button(key="suggest_tags")


def test_suggest_disabled_when_not_configured(fake):
    at = run_app()
    assert not at.exception
    assert suggest_button(at).disabled
    assert OFF_CAPTION in [c.value for c in at.caption]


def tags_on(claude_off):
    claude_off.return_value = True


def test_suggest_fills_tags_and_does_not_save(fake, claude_off):
    tags_on(claude_off)
    with patch("tagger.suggest_tags", return_value=[("low energy", False), ("late caffeine", False)]) as suggest:
        at = run_app()
        assert not suggest_button(at).disabled
        assert any(c.value.startswith(PRIVACY) for c in at.caption)
        at.text_area[0].input("Felt drained")
        at.text_area[1].input("around 3")
        at = suggest_button(at).click().run(timeout=30)
    assert not at.exception
    assert at.text_input(key="tags_text").value == "low energy, late caffeine"
    assert fake.rows == []  # nothing saved
    pairs, known = suggest.call_args.args
    assert pairs[0] == (QS[0], "Felt drained") and pairs[1] == (QS[1], "around 3")
    assert known[:2] == ["low energy", "high energy"]


def test_suggest_merges_after_typed_tags(fake, claude_off):
    tags_on(claude_off)
    with patch("tagger.suggest_tags", return_value=[("stress", False), ("low energy", False)]):
        at = run_app()
        at.text_area[0].input("Rough day")
        at.text_input(key="tags_text").input("Stress, deadline")
        at = suggest_button(at).click().run(timeout=30)
    assert at.text_input(key="tags_text").value == "stress, deadline, low energy"


def test_new_tags_caption_only_for_new(fake, claude_off):
    tags_on(claude_off)
    with patch("tagger.suggest_tags", return_value=[("reading", False), ("sauna", True)]):
        at = run_app()
        at.text_area[2].input("Sauna then a book")
        at = suggest_button(at).click().run(timeout=30)
    captions = [c.value for c in at.caption]
    assert "New tags: sauna. Swap in an existing tag if one fits." in captions
    with patch("tagger.suggest_tags", return_value=[("reading", False)]):
        at = suggest_button(at).click().run(timeout=30)
    assert not any(c.value.startswith("New tags") for c in at.caption)


def test_suggest_error_shows_message_and_keeps_typed_tags(fake, claude_off):
    import tagger

    tags_on(claude_off)
    with patch("tagger.suggest_tags", side_effect=tagger.TaggerError(tagger.FAILED)):
        at = run_app()
        at.text_area[0].input("Tired")
        at.text_input(key="tags_text").input("stress")
        at = suggest_button(at).click().run(timeout=30)
    assert not at.exception
    assert "Couldn't suggest tags right now. Type them instead." in [w.value for w in at.warning]
    assert at.text_input(key="tags_text").value == "stress"


def test_save_after_suggest_stores_tags(fake, claude_off):
    tags_on(claude_off)
    with patch("tagger.suggest_tags", return_value=[("low energy", False)]):
        at = run_app()
        at.text_area[0].input("Drained")
        at = suggest_button(at).click().run(timeout=30)
        at = at.button[0].click().run(timeout=30)
    assert len(fake.rows) == 1
    assert fake.rows[0]["tags"] == ["low energy"]
