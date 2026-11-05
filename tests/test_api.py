"""API skeleton (issue #17). Supabase is always mocked; no real sign-in, Oura, or Claude."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from supabase_auth.errors import AuthApiError

from api.main import app

AVA = "00000000-0000-4000-8000-00000000a7a0"
OTHER = "00000000-0000-4000-8000-0000000000b0"
TOKEN = "test-access-token"
EMAIL = "someone@example.invalid"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def allowed(monkeypatch):
    monkeypatch.setenv("ALLOWED_USER_ID", AVA)


def supabase_returning(user_id=None, error=None):
    supa = MagicMock()
    if error is not None:
        supa.auth.get_user.side_effect = error
    elif user_id is None:
        supa.auth.get_user.return_value = MagicMock(user=None)
    else:
        supa.auth.get_user.return_value = MagicMock(user=MagicMock(id=user_id, email=EMAIL))
    return patch("db.get_client", return_value=supa)


def bearer(token=TOKEN):
    return {"Authorization": f"Bearer {token}"}


def assert_no_secrets(response):
    for secret in (TOKEN, AVA, OTHER, EMAIL):
        assert secret not in response.text


def test_health_needs_no_sign_in(client):
    with patch("db.get_client") as get_client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    get_client.assert_not_called()


@pytest.mark.parametrize("headers", [{}, {"Authorization": TOKEN}, {"Authorization": "Basic abc"}, {"Authorization": "Bearer "}])
def test_me_without_bearer_token_is_401(client, headers):
    with patch("db.get_client") as get_client:
        response = client.get("/api/me", headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "Sign in required."}
    get_client.assert_not_called()  # refused before asking Supabase


def test_rejected_token_is_401(client):
    with supabase_returning(error=AuthApiError("invalid JWT", 401, "bad_jwt")):
        response = client.get("/api/me", headers=bearer())
    assert response.status_code == 401
    assert response.json() == {"detail": "Sign in required."}
    assert_no_secrets(response)


def test_no_user_in_response_is_401(client):
    with supabase_returning(user_id=None):
        response = client.get("/api/me", headers=bearer())
    assert response.status_code == 401


def test_supabase_unreachable_is_503(client):
    with supabase_returning(error=ConnectionError("down")):
        response = client.get("/api/me", headers=bearer())
    assert response.status_code == 503
    assert response.json() == {"detail": "Couldn't check sign-in. Try again."}


def test_missing_supabase_settings_is_503(client):
    with patch("db.get_client", side_effect=RuntimeError("Supabase settings missing.")):
        response = client.get("/api/me", headers=bearer())
    assert response.status_code == 503


def test_other_account_is_403(client):
    with supabase_returning(user_id=OTHER):
        response = client.get("/api/me", headers=bearer())
    assert response.status_code == 403
    assert response.json() == {"detail": "This account can't use Patterns."}
    assert_no_secrets(response)


def test_blank_allowed_user_is_403(client, monkeypatch):
    monkeypatch.setenv("ALLOWED_USER_ID", "")
    with supabase_returning(user_id=AVA):
        response = client.get("/api/me", headers=bearer())
    assert response.status_code == 403


def test_ava_signed_in(client):
    with supabase_returning(user_id=AVA) as get_client:
        response = client.get("/api/me", headers=bearer())
    assert response.status_code == 200
    assert response.json() == {"signed_in": True}
    assert_no_secrets(response)
    get_client.return_value.auth.get_user.assert_called_once_with(TOKEN)


def test_api_does_not_log_token_or_ids(client, caplog):
    with caplog.at_level("DEBUG"), supabase_returning(user_id=AVA):
        client.get("/api/me", headers=bearer())
    for secret in (TOKEN, AVA, EMAIL):
        assert secret not in caplog.text


def preflight(client, origin):
    return client.options(
        "/api/me",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "authorization"},
    )


def test_cors_allows_vite_dev_server(client):
    response = preflight(client, "http://localhost:5173")
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_refuses_other_origins(client):
    response = preflight(client, "https://evil.example")
    assert "access-control-allow-origin" not in response.headers
