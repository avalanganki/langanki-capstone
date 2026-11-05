import time
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
import requests

import oura

SETTINGS = {
    "client_id": "test-client-id",
    "client_secret": "test-client-secret",
    "redirect_uri": "http://localhost:8501/callback/",
}
TOKEN_BODY = {
    "access_token": "test-access",
    "refresh_token": "test-refresh",
    "expires_in": 86400,
    "scope": "daily",
}


@pytest.fixture(autouse=True)
def clear_pending():
    oura._pending.clear()
    yield
    oura._pending.clear()


def response(status, body=None, text=""):
    resp = MagicMock(status_code=status, text=text)
    resp.json.return_value = body or {}
    return resp


def start():
    url = oura.start_sign_in(SETTINGS)
    return url, {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


def test_pkce_matches_rfc7636_example():
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    assert oura.pkce_challenge(verifier) == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"


def test_new_pkce_verifier_length_and_challenge():
    verifier, challenge = oura.new_pkce()
    assert 43 <= len(verifier) <= 128
    assert challenge == oura.pkce_challenge(verifier)
    assert "=" not in challenge


def test_authorize_url_asks_for_daily_only_with_s256():
    url, q = start()
    assert url.startswith(oura.AUTHORIZE_URL + "?")
    assert q["scope"] == "daily"
    assert q["response_type"] == "code"
    assert q["code_challenge_method"] == "S256"
    assert q["client_id"] == "test-client-id"
    assert q["redirect_uri"] == "http://localhost:8501/callback/"
    verifier, _ = oura._pending[q["state"]]
    assert q["code_challenge"] == oura.pkce_challenge(verifier)
    assert "test-client-secret" not in url


def test_each_sign_in_gets_a_new_state():
    _, a = start()
    _, b = start()
    assert a["state"] != b["state"]


def test_finish_sign_in_exchanges_code():
    _, q = start()
    verifier, _ = oura._pending[q["state"]]
    with patch("oura.requests.post", return_value=response(200, TOKEN_BODY)) as post:
        tokens = oura.finish_sign_in(q["state"], "the-code", SETTINGS)
    url = post.call_args.args[0]
    kwargs = post.call_args.kwargs
    assert url == oura.TOKEN_URL
    assert kwargs["data"] == {
        "grant_type": "authorization_code",
        "code": "the-code",
        "redirect_uri": "http://localhost:8501/callback/",
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "code_verifier": verifier,
    }
    assert kwargs["headers"]["User-Agent"] == oura.USER_AGENT
    assert tokens["access_token"] == "test-access"
    assert tokens["refresh_token"] == "test-refresh"
    assert tokens["scope"] == "daily"
    assert tokens["expires_at"] > "2026"


def test_unknown_state_refused_before_any_network_call():
    with patch("oura.requests.post") as post:
        with pytest.raises(oura.OuraAuthError):
            oura.finish_sign_in("not-a-state", "code", SETTINGS)
    post.assert_not_called()


def test_expired_state_refused():
    _, q = start()
    verifier, _ = oura._pending[q["state"]]
    oura._pending[q["state"]] = (verifier, time.time() - oura.STATE_MAX_AGE - 1)
    with patch("oura.requests.post") as post:
        with pytest.raises(oura.OuraAuthError):
            oura.finish_sign_in(q["state"], "code", SETTINGS)
    post.assert_not_called()


def test_state_works_only_once():
    _, q = start()
    with patch("oura.requests.post", return_value=response(200, TOKEN_BODY)):
        oura.finish_sign_in(q["state"], "code", SETTINGS)
        with pytest.raises(oura.OuraAuthError):
            oura.finish_sign_in(q["state"], "code", SETTINGS)


def test_token_error_never_includes_code_or_body():
    _, q = start()
    leaky = response(400, text="invalid_grant code=secret-code token=test-access")
    with patch("oura.requests.post", return_value=leaky):
        with pytest.raises(oura.OuraAuthError) as err:
            oura.finish_sign_in(q["state"], "secret-code", SETTINGS)
    message = str(err.value)
    assert "400" in message
    for secret in ("secret-code", "test-access", "test-client-secret", "invalid_grant"):
        assert secret not in message


def test_save_and_load_connection():
    client = MagicMock()
    oura.save_connection(client, {"access_token": "a", "refresh_token": "r", "expires_at": "x", "scope": "daily"})
    client.table.assert_called_with("oura_connection")
    row = client.table.return_value.upsert.call_args.args[0]
    assert row["id"] == 1 and row["access_token"] == "a"


def test_load_connection_none_when_empty():
    client = MagicMock()
    client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
    assert oura.load_connection(client) is None


def test_disconnect_deletes_tokens_even_if_revoke_fails():
    client = MagicMock()
    with patch("oura.load_connection", return_value={"id": 1, "access_token": "test-access"}), patch(
        "oura.requests.get", side_effect=requests.ConnectionError("down")
    ) as get:
        oura.disconnect(client)
    assert get.call_args.kwargs["params"] == {"access_token": "test-access"}
    client.table.return_value.delete.return_value.eq.assert_called_once_with("id", 1)


def test_is_configured_needs_id_and_secret():
    assert oura.is_configured(SETTINGS)
    assert not oura.is_configured({**SETTINGS, "client_id": ""})
    assert not oura.is_configured({**SETTINGS, "client_secret": " ".strip()})


def test_get_settings_reads_environment(monkeypatch):
    monkeypatch.setattr(oura, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("OURA_CLIENT_ID", " id ")
    monkeypatch.setenv("OURA_CLIENT_SECRET", "secret")
    monkeypatch.delenv("OURA_REDIRECT_URI", raising=False)
    settings = oura.get_settings()
    assert settings == {
        "client_id": "id",
        "client_secret": "secret",
        "redirect_uri": "http://localhost:8501/callback/",
    }
