"""Nights and tag-status routes (issue #21). Supabase is faked; no real Oura or Claude. Synthetic values only."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import sample_data
from api.auth import require_user
from api.main import app
from fakes import FakeClient

CONNECTION = {"access_token": "test-access", "refresh_token": "test-refresh", "expires_at": "2999-01-01T00:00:00+00:00", "scope": "daily"}
MARKER_HRV = 47.25  # synthetic, distinctive, must never appear in logs


def night(date, sleep=None, readiness=None, hrv=None):
    return {"night_date": date, "sleep_score": sleep, "readiness": readiness, "avg_hrv": hrv}


@pytest.fixture
def signed_in():
    app.dependency_overrides[require_user] = lambda: "test-user"
    yield
    app.dependency_overrides.pop(require_user, None)


def get(client, path):
    with patch("db.get_client", return_value=client):
        return TestClient(app).get(path)


@pytest.mark.parametrize("path", ["/api/nights", "/api/tags/status"])
def test_needs_sign_in(path):
    with patch("db.get_client") as get_client:
        response = TestClient(app).get(path)
    assert response.status_code == 401
    assert response.json() == {"detail": "Sign in required."}
    get_client.assert_not_called()


def test_sample_when_not_connected(signed_in):
    client = FakeClient()
    client.night_rows.append(night("2000-01-02", 80, 70, 50))  # stored nights are never shown without a connection
    response = get(client, "/api/nights")
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "sample"
    assert body["nights"] == sample_data.load_nights()
    assert body["counted"] == len(sample_data.load_nights())


def test_oura_nights_oldest_first_when_connected(signed_in):
    client = FakeClient(connection=dict(CONNECTION))
    client.night_rows.extend([night("2000-01-03", 81, 72, 55.5), night("2000-01-01", 70, 60, 40), night("2000-01-02", 75, 65, 45)])
    body = get(client, "/api/nights").json()
    assert body["source"] == "oura"
    assert [n["date"] for n in body["nights"]] == ["2000-01-01", "2000-01-02", "2000-01-03"]
    assert body["nights"][-1] == {"date": "2000-01-03", "sleep_score": 81, "readiness": 72, "avg_hrv": 55.5}


def test_missing_values_stay_null_and_empty_nights_are_not_counted(signed_in):
    client = FakeClient(connection=dict(CONNECTION))
    client.night_rows.extend([night("2000-01-01", 80, None, None), night("2000-01-02"), night("2000-01-03", None, None, 50)])
    body = get(client, "/api/nights").json()
    assert body["nights"][0] == {"date": "2000-01-01", "sleep_score": 80, "readiness": None, "avg_hrv": None}
    assert body["nights"][1]["sleep_score"] is None  # never 0
    assert body["counted"] == 2


def test_connected_with_no_nights_falls_back_to_sample(signed_in):
    body = get(FakeClient(connection=dict(CONNECTION)), "/api/nights").json()
    assert body["source"] == "sample"


def test_database_error_is_503_without_values(signed_in, caplog):
    with patch("db.get_client", side_effect=RuntimeError(f"row has avg_hrv {MARKER_HRV}")):
        with caplog.at_level("DEBUG"):
            response = TestClient(app).get("/api/nights")
    assert response.status_code == 503
    assert response.json() == {"detail": "Couldn't reach the database. Try again."}
    assert str(MARKER_HRV) not in response.text
    assert str(MARKER_HRV) not in caplog.text


def test_nights_never_logs_values_or_calls_claude(signed_in, caplog):
    client = FakeClient(connection=dict(CONNECTION))
    client.night_rows.append(night("2000-01-01", 80, 70, MARKER_HRV))
    with patch("tagger.suggest_tags") as suggest, patch("tagger.get_client") as claude, caplog.at_level("DEBUG"):
        body = get(client, "/api/nights").json()
    assert body["nights"][0]["avg_hrv"] == MARKER_HRV
    assert str(MARKER_HRV) not in caplog.text
    suggest.assert_not_called()
    claude.assert_not_called()


@pytest.mark.parametrize("on", [True, False])
def test_tags_status(signed_in, on):
    with patch("tagger.is_configured", return_value=on):
        response = TestClient(app).get("/api/tags/status")
    assert response.status_code == 200
    assert response.json() == {"on": on}
