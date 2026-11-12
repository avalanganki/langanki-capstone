"""Entry and tag routes (issue #19). Supabase and Claude are always faked; no real sign-in, Oura, or Claude."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import tagger
from api.auth import require_user
from api.main import app
from entries import QUESTIONS
from fakes import FakeClient

Q1, Q2, Q3 = QUESTIONS
SECRET_ANSWER = "Wiped out after the 4pm espresso"  # synthetic; must never appear in errors or logs


def pairs(a1="", a2="", a3=""):
    return [{"question": q, "answer": a} for q, a in zip(QUESTIONS, (a1, a2, a3))]


def new_entry(date="2026-01-05", answers=None, tags=(), suggested=()):
    return {
        "entry_date": date,
        "answers": answers if answers is not None else pairs(SECRET_ANSWER, "2pm", "Reading"),
        "tags": list(tags),
        "suggested_tags": list(suggested),
    }


def stored_row(date, tags=(), suggested=(), answers=None):
    return {
        "entry_date": date,
        "answers": answers if answers is not None else pairs("Fine", "Noon", "Stretching"),
        "tags": list(tags),
        "suggested_tags": list(suggested),
    }


@pytest.fixture
def fake():
    client = FakeClient()
    with patch("db.get_client", return_value=client):
        yield client


@pytest.fixture
def signed_in():
    app.dependency_overrides[require_user] = lambda: "test-user"
    yield
    app.dependency_overrides.pop(require_user, None)


@pytest.fixture
def api(signed_in, fake):
    return TestClient(app)


@pytest.fixture
def claude_on():
    with patch("tagger.is_configured", return_value=True):
        yield


# --- sign-in ---

ROUTES = [
    ("get", "/api/questions", None),
    ("get", "/api/entries", None),
    ("get", "/api/entries/1", None),
    ("post", "/api/entries", new_entry()),
    ("put", "/api/entries/1", {"answers": pairs("x"), "tags": []}),
    ("delete", "/api/entries/1", None),
    ("post", "/api/tags/suggest", {"pairs": pairs("x")}),
]


@pytest.mark.parametrize("method,path,body", ROUTES)
def test_every_route_needs_sign_in(fake, method, path, body):
    kwargs = {"json": body} if body is not None else {}
    with patch("tagger.suggest_tags") as suggest:
        response = getattr(TestClient(app), method)(path, **kwargs)
    assert response.status_code == 401
    assert response.json() == {"detail": "Sign in required."}
    assert fake.rows == []
    suggest.assert_not_called()


# --- questions ---


def test_questions(api):
    response = api.get("/api/questions")
    assert response.status_code == 200
    assert response.json() == {"questions": list(QUESTIONS)}


# --- create ---


def test_create_returns_201_with_saved_entry(api, fake):
    response = api.post("/api/entries", json=new_entry(tags=["low energy"], suggested=["low energy"]))
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["entry_date"] == "2026-01-05"
    assert body["answers"] == pairs(SECRET_ANSWER, "2pm", "Reading")
    assert body["tags"] == ["low energy"]
    assert body["suggested_tags"] == ["low energy"]
    assert body["tag_sources"] == [{"tag": "low energy", "source": "suggested"}]
    assert len(fake.rows) == 1


def test_create_same_date_is_409(api, fake):
    assert api.post("/api/entries", json=new_entry()).status_code == 201
    response = api.post("/api/entries", json=new_entry())
    assert response.status_code == 409
    assert response.json() == {"detail": "You already have an entry for this date. Edit it in Past entries."}
    assert len(fake.rows) == 1


@pytest.mark.parametrize("answers", [pairs(), pairs("   ", "\n", ""), []])
def test_create_blank_is_400(api, fake, answers):
    response = api.post("/api/entries", json=new_entry(answers=answers))
    assert response.status_code == 400
    assert response.json() == {"detail": "Answer at least one question to save."}
    assert fake.rows == []


def test_create_unknown_question_is_400(api, fake):
    answers = [{"question": "Your readiness was 62. How was your energy?", "answer": SECRET_ANSWER}]
    response = api.post("/api/entries", json=new_entry(answers=answers))
    assert response.status_code == 400
    assert response.json() == {"detail": "Unknown question."}
    assert SECRET_ANSWER not in response.text
    assert fake.rows == []


def test_create_normalizes_tags(api, fake):
    body = new_entry(tags=[" Late Caffeine", "stress", "", "STRESS "], suggested=["Late Caffeine "])
    response = api.post("/api/entries", json=body)
    assert response.json()["tags"] == ["late caffeine", "stress"]
    assert response.json()["suggested_tags"] == ["late caffeine"]
    assert fake.rows[0]["tags"] == ["late caffeine", "stress"]


def test_create_bad_date_is_422_without_answer_text(api, fake):
    response = api.post("/api/entries", json=new_entry(date="not-a-date"))
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request."}
    assert SECRET_ANSWER not in response.text
    assert fake.rows == []


def test_create_does_not_log_answer_text(api, caplog):
    with caplog.at_level("DEBUG"):
        api.post("/api/entries", json=new_entry())
        api.post("/api/entries", json=new_entry())  # 409
        api.post("/api/entries", json=new_entry(date="bad"))  # 422
    assert SECRET_ANSWER not in caplog.text


# --- list and get ---


def test_list_newest_first_with_tag_sources(signed_in):
    client = FakeClient(
        rows=[
            stored_row("2026-01-03", tags=["stress"]),
            stored_row("2026-01-05", tags=["low energy", "deadline"], suggested=["low energy", "nap"]),
            stored_row("2026-01-04"),
        ]
    )
    with patch("db.get_client", return_value=client):
        response = TestClient(app).get("/api/entries")
    assert response.status_code == 200
    items = response.json()["entries"]
    assert [e["entry_date"] for e in items] == ["2026-01-05", "2026-01-04", "2026-01-03"]
    assert set(items[0]) == {"id", "entry_date", "answers", "tags", "suggested_tags", "tag_sources"}
    assert items[0]["tag_sources"] == [
        {"tag": "low energy", "source": "suggested"},
        {"tag": "deadline", "source": "typed"},
    ]
    assert items[1]["tag_sources"] == []
    assert items[2]["tag_sources"] == [{"tag": "stress", "source": "typed"}]


def test_list_empty(api):
    assert api.get("/api/entries").json() == {"entries": []}


def test_get_found(api, fake):
    created = api.post("/api/entries", json=new_entry(tags=["nap"])).json()
    response = api.get(f"/api/entries/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_missing_is_404(api):
    response = api.get("/api/entries/99")
    assert response.status_code == 404
    assert response.json() == {"detail": "Entry not found."}


# --- update ---


def test_update_changes_answers_and_tags(api, fake):
    entry_id = api.post("/api/entries", json=new_entry(tags=["stress"], suggested=["stress"])).json()["id"]
    response = api.put(
        f"/api/entries/{entry_id}",
        json={"answers": pairs("Better", "", "Bath"), "tags": ["Stress", " Nap "], "suggested_tags": ["nap"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answers"] == pairs("Better", "", "Bath")
    assert body["tags"] == ["stress", "nap"]
    assert body["suggested_tags"] == ["nap"]
    assert body["tag_sources"] == [{"tag": "stress", "source": "typed"}, {"tag": "nap", "source": "suggested"}]
    assert body["entry_date"] == "2026-01-05"  # the date never changes on edit


def test_update_null_keeps_suggested_tags(api, fake):
    entry_id = api.post("/api/entries", json=new_entry(tags=["nap"], suggested=["nap", "stress"])).json()["id"]
    response = api.put(f"/api/entries/{entry_id}", json={"answers": pairs("x"), "tags": ["nap"], "suggested_tags": None})
    assert response.json()["suggested_tags"] == ["nap", "stress"]
    response = api.put(f"/api/entries/{entry_id}", json={"answers": pairs("x"), "tags": ["nap"]})
    assert response.json()["suggested_tags"] == ["nap", "stress"]


@pytest.mark.parametrize(
    "answers",
    [
        list(reversed(pairs("a", "b", "c"))),  # same questions, different order
        pairs("a", "b")[:2],  # one question missing
        [{"question": "Your HRV was low. Why?", "answer": "a"}] + pairs("b", "c")[1:],
    ],
)
def test_update_changed_question_is_400(api, fake, answers):
    entry_id = api.post("/api/entries", json=new_entry()).json()["id"]
    response = api.put(f"/api/entries/{entry_id}", json={"answers": answers, "tags": []})
    assert response.status_code == 400
    assert response.json() == {"detail": "Unknown question."}
    assert fake.rows[0]["answers"] == pairs(SECRET_ANSWER, "2pm", "Reading")


def test_update_blank_is_400(api, fake):
    entry_id = api.post("/api/entries", json=new_entry()).json()["id"]
    response = api.put(f"/api/entries/{entry_id}", json={"answers": pairs(" ", "", ""), "tags": []})
    assert response.status_code == 400
    assert response.json() == {"detail": "Answer at least one question to save."}
    assert fake.rows[0]["answers"] == pairs(SECRET_ANSWER, "2pm", "Reading")


def test_update_missing_is_404(api):
    response = api.put("/api/entries/99", json={"answers": pairs("x"), "tags": []})
    assert response.status_code == 404
    assert response.json() == {"detail": "Entry not found."}


# --- delete ---


def test_delete_then_404(api, fake):
    keep = api.post("/api/entries", json=new_entry(date="2026-01-04")).json()["id"]
    gone = api.post("/api/entries", json=new_entry(date="2026-01-05")).json()["id"]
    response = api.delete(f"/api/entries/{gone}")
    assert response.status_code == 204
    assert response.content == b""
    assert [r["id"] for r in fake.rows] == [keep]
    response = api.delete(f"/api/entries/{gone}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Entry not found."}


# --- database down ---


def test_database_error_is_503_without_details(signed_in, caplog):
    with patch("db.get_client", side_effect=RuntimeError(f"Failing row contains ({SECRET_ANSWER})")):
        with caplog.at_level("DEBUG"):
            response = TestClient(app).post("/api/entries", json=new_entry())
    assert response.status_code == 503
    assert response.json() == {"detail": "Couldn't reach the database. Try again."}
    assert SECRET_ANSWER not in response.text
    assert SECRET_ANSWER not in caplog.text


# --- suggest ---


def test_suggest_returns_tags_with_new_flag(api, fake, claude_on):
    fake.rows.append({"id": 50, **stored_row("2026-01-01", tags=["deadline"])})
    with patch("tagger.suggest_tags", return_value=[("low energy", False), ("espresso", True)]) as suggest:
        response = api.post("/api/tags/suggest", json={"pairs": pairs(SECRET_ANSWER, "4pm", "")})
    assert response.status_code == 200
    assert response.json() == {"tags": [{"tag": "low energy", "is_new": False}, {"tag": "espresso", "is_new": True}]}
    sent_pairs, known = suggest.call_args.args
    assert sent_pairs == [(Q1, SECRET_ANSWER), (Q2, "4pm"), (Q3, "")]
    assert known == tagger.known_tags(fake)
    assert "deadline" in known
    assert fake.rows[0]["id"] == 50 and len(fake.rows) == 1  # suggest saves nothing


def test_suggest_off_when_not_configured(api):
    with patch("tagger.is_configured", return_value=False), patch("tagger.suggest_tags") as suggest:
        response = api.post("/api/tags/suggest", json={"pairs": pairs(SECRET_ANSWER)})
    assert response.status_code == 503
    assert response.json() == {"detail": "Tag suggestions are off (no Claude API key)."}
    suggest.assert_not_called()


def test_suggest_tagger_error_is_503_without_answer_text(api, claude_on, caplog):
    with patch("tagger.suggest_tags", side_effect=tagger.TaggerError(tagger.FAILED)):
        with caplog.at_level("DEBUG"):
            response = api.post("/api/tags/suggest", json={"pairs": pairs(SECRET_ANSWER)})
    assert response.status_code == 503
    assert response.json() == {"detail": "Couldn't suggest tags right now. Type them instead."}
    assert SECRET_ANSWER not in response.text
    assert SECRET_ANSWER not in caplog.text


def test_suggest_unknown_question_sends_nothing(api, claude_on):
    body = {"pairs": [{"question": "Readiness was 58 today. How was your energy?", "answer": SECRET_ANSWER}]}
    with patch("tagger.suggest_tags") as suggest, patch("tagger.get_client") as claude:
        response = api.post("/api/tags/suggest", json=body)
    assert response.status_code == 400
    assert response.json() == {"detail": "Unknown question."}
    assert SECRET_ANSWER not in response.text
    suggest.assert_not_called()
    claude.assert_not_called()


def test_suggest_real_tagger_with_fake_claude(api, fake, claude_on):
    """End to end through tagger.suggest_tags with Claude's client mocked: only questions and answers are sent."""

    class Parsed:
        stop_reason = "end_turn"
        parsed_output = tagger.TagList(tags=["Low Energy", "espresso"])

    with patch("tagger.get_client") as get_client:
        get_client.return_value.beta.messages.parse.return_value = Parsed()
        response = api.post("/api/tags/suggest", json={"pairs": pairs(SECRET_ANSWER)})
    assert response.json() == {"tags": [{"tag": "low energy", "is_new": False}, {"tag": "espresso", "is_new": True}]}
    sent = get_client.return_value.beta.messages.parse.call_args.kwargs["messages"][0]["content"]
    assert sent == f"<question>{Q1}</question>\n<answer>{SECRET_ANSWER}</answer>"


def test_suggest_does_not_log_answer_text(api, claude_on, caplog):
    with patch("tagger.suggest_tags", return_value=[("stress", False)]):
        with caplog.at_level("DEBUG"):
            api.post("/api/tags/suggest", json={"pairs": pairs(SECRET_ANSWER)})
    assert SECRET_ANSWER not in caplog.text
