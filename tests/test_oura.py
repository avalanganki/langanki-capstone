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
    monkeypatch.setenv("OURA_CLIENT_ID", " id ")
    monkeypatch.setenv("OURA_CLIENT_SECRET", "secret")
    monkeypatch.delenv("OURA_REDIRECT_URI", raising=False)
    settings = oura.get_settings()
    assert settings == {
        "client_id": "id",
        "client_secret": "secret",
        "redirect_uri": "http://localhost:8501/callback/",
    }


# --- Fetch (issue #8). Synthetic fixtures only; no real Oura or Supabase. ---

import datetime
import json
from pathlib import Path
from unittest.mock import Mock

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / f"oura_{name}.json").read_text())["data"]


def merged():
    return {n["night_date"]: n for n in oura.merge_days(fixture("daily_sleep"), fixture("daily_readiness"), fixture("sleep"))}


def test_merge_all_three_values():
    assert merged()["2000-01-01"] == {
        "night_date": "2000-01-01", "sleep_score": 81, "readiness": 79, "avg_hrv": 52,
    }


def test_merge_missing_readiness_stays_none():
    night = merged()["2000-01-02"]
    assert night["readiness"] is None
    assert night["sleep_score"] == 74


def test_merge_nap_ignored_for_hrv():
    assert merged()["2000-01-02"]["avg_hrv"] == 47  # main sleep, not the nap's 70


def test_merge_no_long_sleep_means_no_hrv():
    night = merged()["2000-01-03"]
    assert night["avg_hrv"] is None
    assert (night["sleep_score"], night["readiness"]) == (68, 62)


def test_merge_two_long_sleeps_longer_wins():
    assert merged()["2000-01-04"]["avg_hrv"] == 58


def test_merge_empty_day_left_out_and_sorted_oldest_first():
    days = [n["night_date"] for n in oura.merge_days(fixture("daily_sleep"), fixture("daily_readiness"), fixture("sleep"))]
    assert days == ["2000-01-01", "2000-01-02", "2000-01-03", "2000-01-04"]


def test_merge_never_fills_zero():
    for night in merged().values():
        assert 0 not in (night["sleep_score"], night["readiness"], night["avg_hrv"])


def test_fetch_collection_follows_next_token():
    pages = [
        response(200, {"data": [{"day": "2000-01-01"}], "next_token": "page-2"}),
        response(200, {"data": [{"day": "2000-01-02"}], "next_token": None}),
    ]
    with patch("oura.requests.get", side_effect=pages) as get:
        items = oura.fetch_collection("tok", "daily_sleep", datetime.date(2000, 1, 1), datetime.date(2000, 1, 3))
    assert [i["day"] for i in items] == ["2000-01-01", "2000-01-02"]
    first, second = get.call_args_list
    assert first.args[0] == "https://api.ouraring.com/v2/usercollection/daily_sleep"
    assert first.kwargs["params"] == {"start_date": "2000-01-01", "end_date": "2000-01-03"}
    assert "next_token" not in first.kwargs["params"]
    assert second.kwargs["params"]["next_token"] == "page-2"
    assert first.kwargs["headers"] == {"Authorization": "Bearer tok", "User-Agent": oura.USER_AGENT}


@pytest.mark.parametrize(
    "status, error, message",
    [
        (401, oura.OuraAuthError, "Oura connection expired. Connect again."),
        (403, oura.OuraAccessError, "Oura denied access. An active Oura membership may be needed."),
        (429, oura.OuraRateLimitError, "Oura is busy. Try again in a few minutes."),
        (500, oura.OuraError, "Couldn't reach Oura. Try again later."),
    ],
)
def test_fetch_error_status_maps_to_message(status, error, message):
    with patch("oura.requests.get", return_value=response(status, text="body with tok")):
        with pytest.raises(error) as err:
            oura.fetch_collection("tok", "sleep", datetime.date(2000, 1, 1), datetime.date(2000, 1, 2))
    assert str(err.value) == message


def test_fetch_network_failure_is_plain_message():
    with patch("oura.requests.get", side_effect=requests.ConnectionError("tok leaked?")):
        with pytest.raises(oura.OuraError) as err:
            oura.fetch_collection("tok", "sleep", datetime.date(2000, 1, 1), datetime.date(2000, 1, 2))
    assert str(err.value) == "Couldn't reach Oura. Try again later."


NOW = datetime.datetime(2000, 1, 5, 12, 0, tzinfo=datetime.timezone.utc)


def connection(expires_in):
    return {
        "id": 1, "access_token": "old-access", "refresh_token": "old-refresh", "scope": "daily",
        "expires_at": (NOW + expires_in).isoformat(),
    }


def test_valid_token_used_without_refresh():
    with patch("oura.load_connection", return_value=connection(datetime.timedelta(hours=1))), patch(
        "oura.requests.post"
    ) as post:
        assert oura.get_access_token(MagicMock(), SETTINGS, now=NOW) == "old-access"
    post.assert_not_called()


def test_expiring_token_refreshed_and_saved_before_fetch():
    calls = Mock()
    calls.post.return_value = response(200, {**TOKEN_BODY, "access_token": "new-access", "refresh_token": "new-refresh"})
    calls.get.return_value = response(200, {"data": [], "next_token": None})
    client = MagicMock()
    real_now = datetime.datetime.now(datetime.timezone.utc)
    expiring = {**connection(datetime.timedelta(0)), "expires_at": (real_now + datetime.timedelta(minutes=4)).isoformat()}
    with patch("oura.load_connection", return_value=expiring), patch("oura.get_settings", return_value=SETTINGS), patch(
        "oura.requests.post", calls.post
    ), patch("oura.requests.get", calls.get), patch("oura.save_connection", calls.save):
        oura.sync_nights(client, today=datetime.date(2000, 1, 5))
    names = [c[0] for c in calls.mock_calls if c[0] in ("post", "save", "get")]
    assert names[:2] == ["post", "save"]  # new tokens saved before any fetch
    assert names[2:] == ["get", "get", "get"]
    assert calls.post.call_args.kwargs["data"] == {
        "grant_type": "refresh_token", "refresh_token": "old-refresh",
        "client_id": "test-client-id", "client_secret": "test-client-secret",
    }
    saved = calls.save.call_args.args[1]
    assert saved["refresh_token"] == "new-refresh"
    assert calls.get.call_args.kwargs["headers"]["Authorization"] == "Bearer new-access"


def test_failed_refresh_raises_expired_message():
    with patch("oura.load_connection", return_value=connection(datetime.timedelta(minutes=-1))), patch(
        "oura.requests.post", return_value=response(400, text="invalid_grant old-refresh")
    ), patch("oura.save_connection") as save:
        with pytest.raises(oura.OuraAuthError) as err:
            oura.get_access_token(MagicMock(), SETTINGS, now=NOW)
    assert str(err.value) == "Oura connection expired. Connect again."
    save.assert_not_called()


def test_not_connected_raises():
    with patch("oura.load_connection", return_value=None):
        with pytest.raises(oura.OuraNotConnected):
            oura.get_access_token(MagicMock(), SETTINGS, now=NOW)


def test_parse_timestamp_handles_supabase_formats():
    for text in ("2000-01-05T12:00:00+00:00", "2000-01-05T12:00:00.12+00:00", "2000-01-05T12:00:00Z"):
        parsed = oura.parse_timestamp(text)
        assert parsed.tzinfo is not None
        assert (parsed.year, parsed.hour) == (2000, 12)


def test_sync_nights_saves_merged_window_and_returns_count():
    client = MagicMock()
    with patch("oura.get_access_token", return_value="tok"), patch(
        "oura.fetch_collection", side_effect=lambda token, name, start, end: fixture(name)
    ) as fetch, patch("oura.save_nights") as save:
        count = oura.sync_nights(client, days=14, today=datetime.date(2000, 1, 5))
    assert count == 4
    names = [c.args[1] for c in fetch.call_args_list]
    assert names == ["daily_sleep", "daily_readiness", "sleep"]
    assert fetch.call_args.args[2] == datetime.date(1999, 12, 23)  # 14 days ending today
    assert [n["night_date"] for n in save.call_args.args[1]] == ["2000-01-01", "2000-01-02", "2000-01-03", "2000-01-04"]


def test_sync_nights_saves_nothing_if_a_fetch_fails():
    def fetch(token, name, start, end):
        if name == "sleep":
            raise oura.OuraRateLimitError(oura.BUSY)
        return fixture(name)

    with patch("oura.get_access_token", return_value="tok"), patch("oura.fetch_collection", side_effect=fetch), patch(
        "oura.save_nights"
    ) as save:
        with pytest.raises(oura.OuraRateLimitError):
            oura.sync_nights(MagicMock(), today=datetime.date(2000, 1, 5))
    save.assert_not_called()


def test_save_nights_upserts_on_night_date_with_fresh_fetched_at():
    client = MagicMock()
    oura.save_nights(client, [{"night_date": "2000-01-01", "sleep_score": 81, "readiness": None, "avg_hrv": 52}], now=NOW)
    client.table.assert_called_with("nights")
    upsert = client.table.return_value.upsert
    rows = upsert.call_args.args[0]
    assert upsert.call_args.kwargs == {"on_conflict": "night_date"}
    assert rows[0]["fetched_at"] == NOW.isoformat()
    assert rows[0]["readiness"] is None
