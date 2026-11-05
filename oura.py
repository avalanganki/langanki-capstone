"""Oura OAuth2 sign-in (authorization code flow with PKCE) and daily summary fetch.

Never log, print, or show tokens, codes, or Oura response bodies.
Oura data must never be sent to Claude or any AI model (Oura API agreement Sec. 4(d)).
"""

import base64
import datetime
import hashlib
import os
import re
import secrets
import time
from pathlib import Path
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

AUTHORIZE_URL = "https://cloud.ouraring.com/oauth/authorize"
TOKEN_URL = "https://api.ouraring.com/oauth/token"
REVOKE_URL = "https://api.ouraring.com/oauth/revoke"
SCOPE = "daily"
API_BASE = "https://api.ouraring.com/v2/usercollection"
USER_AGENT = "Patterns/0.3 (capstone project)"
STATE_MAX_AGE = 10 * 60  # seconds
TIMEOUT = 15  # seconds per Oura request

ENV_PATH = Path(__file__).parent / ".env"
TABLE = "oura_connection"
NIGHTS_TABLE = "nights"
REFRESH_MARGIN = datetime.timedelta(minutes=5)

EXPIRED = "Oura connection expired. Connect again."
DENIED = "Oura denied access. An active Oura membership may be needed."
BUSY = "Oura is busy. Try again in a few minutes."
UNREACHABLE = "Couldn't reach Oura. Try again later."
NOT_CONNECTED = "Oura isn't connected. Connect Oura first."

# state -> (verifier, created_at). Module-level so it survives Streamlit reruns and the
# browser coming back from Oura in a new session (same server process).
_pending = {}


class OuraError(Exception):
    """Base Oura error. The message is plain language, safe to show, and never holds tokens or data."""


class OuraAuthError(OuraError):
    pass


class OuraAccessError(OuraError):
    pass


class OuraRateLimitError(OuraError):
    pass


class OuraNotConnected(OuraError):
    pass


def get_settings():
    load_dotenv(ENV_PATH)
    names = ("OURA_CLIENT_ID", "OURA_CLIENT_SECRET", "OURA_REDIRECT_URI")
    values = {n: (os.environ.get(n) or "").strip() for n in names}
    if not (values["OURA_CLIENT_ID"] and values["OURA_CLIENT_SECRET"]):
        try:
            import streamlit as st

            values = {n: str(st.secrets.get(n, values[n])).strip() for n in names}
        except Exception:
            pass  # no secrets file: stay unconfigured
    return {
        "client_id": values["OURA_CLIENT_ID"],
        "client_secret": values["OURA_CLIENT_SECRET"],
        "redirect_uri": values["OURA_REDIRECT_URI"] or "http://localhost:8501/callback/",
    }


def is_configured(settings=None):
    settings = settings or get_settings()
    return bool(settings["client_id"] and settings["client_secret"])


def pkce_challenge(verifier):
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def new_pkce():
    verifier = secrets.token_urlsafe(64)  # 86 characters, within PKCE's 43-128
    return verifier, pkce_challenge(verifier)


def _drop_expired(now):
    for state in [s for s, (_, made) in _pending.items() if now - made > STATE_MAX_AGE]:
        del _pending[state]


def start_sign_in(settings=None):
    settings = settings or get_settings()
    now = time.time()
    _drop_expired(now)
    state = secrets.token_urlsafe(32)
    verifier, challenge = new_pkce()
    _pending[state] = (verifier, now)
    query = {
        "response_type": "code",
        "client_id": settings["client_id"],
        "redirect_uri": settings["redirect_uri"],
        "scope": SCOPE,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    return f"{AUTHORIZE_URL}?{urlencode(query)}"


def _token_request(data):
    resp = requests.post(
        TOKEN_URL, data=data, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT
    )
    if resp.status_code != 200:
        # Status only: the body may echo the code or tokens.
        raise OuraAuthError(f"Oura token request failed (HTTP {resp.status_code}).")
    body = resp.json()
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        seconds=int(body["expires_in"])
    )
    return {
        "access_token": body["access_token"],
        "refresh_token": body["refresh_token"],
        "expires_at": expires_at.isoformat(),
        "scope": body.get("scope") or SCOPE,
    }


def finish_sign_in(state, code, settings=None):
    pending = _pending.pop(state, None)
    if pending is None or time.time() - pending[1] > STATE_MAX_AGE:
        raise OuraAuthError("Sign-in state unknown or expired.")
    settings = settings or get_settings()
    return _token_request(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings["redirect_uri"],
            "client_id": settings["client_id"],
            "client_secret": settings["client_secret"],
            "code_verifier": pending[0],
        }
    )


def save_connection(client, tokens):
    row = {"id": 1, **tokens}
    return client.table(TABLE).upsert(row).execute()


def load_connection(client):
    rows = client.table(TABLE).select("*").eq("id", 1).limit(1).execute().data
    return rows[0] if rows else None


def disconnect(client):
    connection = load_connection(client)
    if connection:
        try:
            # Oura's docs give the revoke URL with the token as a query parameter.
            requests.get(
                REVOKE_URL,
                params={"access_token": connection["access_token"]},
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT,
            )
        except requests.RequestException:
            pass  # still remove our copy of the tokens
    client.table(TABLE).delete().eq("id", 1).execute()


# --- Fetch (issue #8) ---


def parse_timestamp(value):
    """Parse a Supabase/ISO timestamp. Python 3.9's fromisoformat can't read 'Z' or short fractions."""
    if isinstance(value, datetime.datetime):
        return value
    text = value.replace("Z", "+00:00")
    text = re.sub(r"\.(\d+)", lambda m: "." + (m.group(1) + "000000")[:6], text)
    parsed = datetime.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed


def refresh_tokens(client, connection, settings=None):
    settings = settings or get_settings()
    try:
        tokens = _token_request(
            {
                "grant_type": "refresh_token",
                "refresh_token": connection["refresh_token"],
                "client_id": settings["client_id"],
                "client_secret": settings["client_secret"],
            }
        )
    except OuraAuthError:
        raise OuraAuthError(EXPIRED) from None
    except requests.RequestException:
        raise OuraError(UNREACHABLE) from None
    # Oura refresh tokens work only once: save the new pair before anything else can fail.
    save_connection(client, tokens)
    return tokens


def get_access_token(client, settings=None, now=None):
    connection = load_connection(client)
    if not connection:
        raise OuraNotConnected(NOT_CONNECTED)
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if parse_timestamp(connection["expires_at"]) - now < REFRESH_MARGIN:
        connection = refresh_tokens(client, connection, settings)
    return connection["access_token"]


def fetch_collection(token, name, start, end):
    """All `data` items from one Oura collection, following `next_token` pages."""
    url = f"{API_BASE}/{name}"
    headers = {"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT}
    params = {"start_date": start.isoformat(), "end_date": end.isoformat()}
    items = []
    while True:
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        except requests.RequestException:
            raise OuraError(UNREACHABLE) from None
        if resp.status_code == 401:
            raise OuraAuthError(EXPIRED)
        if resp.status_code == 403:
            raise OuraAccessError(DENIED)
        if resp.status_code == 429:
            raise OuraRateLimitError(BUSY)
        if resp.status_code != 200:
            raise OuraError(UNREACHABLE)
        body = resp.json()
        items.extend(body.get("data") or [])
        next_token = body.get("next_token")
        if not next_token:
            return items
        params = {**params, "next_token": next_token}


def merge_days(daily_sleep, daily_readiness, sleep):
    """One dict per day from the three collections. Missing values stay None; empty days are dropped."""
    days = {}

    def day(d):
        return days.setdefault(
            d, {"night_date": d, "sleep_score": None, "readiness": None, "avg_hrv": None}
        )

    for item in daily_sleep:
        if item.get("score") is not None:
            day(item["day"])["sleep_score"] = item["score"]
    for item in daily_readiness:
        if item.get("score") is not None:
            day(item["day"])["readiness"] = item["score"]

    main_sleep = {}  # day -> the longest long_sleep record
    for item in sleep:
        if item.get("type") != "long_sleep":
            continue  # naps, rests, and deleted periods don't count
        best = main_sleep.get(item["day"])
        if best is None or (item.get("total_sleep_duration") or 0) > (
            best.get("total_sleep_duration") or 0
        ):
            main_sleep[item["day"]] = item
    for d, item in main_sleep.items():
        if item.get("average_hrv") is not None:
            day(d)["avg_hrv"] = item["average_hrv"]

    return [days[d] for d in sorted(days)]


def save_nights(client, nights, now=None):
    if not nights:
        return
    # Set fetched_at on every save: the column default only applies to new rows.
    fetched_at = (now or datetime.datetime.now(datetime.timezone.utc)).isoformat()
    rows = [{**n, "fetched_at": fetched_at} for n in nights]
    client.table(NIGHTS_TABLE).upsert(rows, on_conflict="night_date").execute()


def last_fetched(client):
    rows = (
        client.table(NIGHTS_TABLE)
        .select("fetched_at")
        .order("fetched_at", desc=True)
        .limit(1)
        .execute()
        .data
    )
    return parse_timestamp(rows[0]["fetched_at"]) if rows else None


def sync_nights(client, days=14, today=None):
    """Fetch the last `days` days from Oura, save them, and return how many nights were saved.

    All three collections are fetched before anything is saved, so an Oura error overwrites nothing.
    """
    token = get_access_token(client)
    today = today or datetime.date.today()
    start = today - datetime.timedelta(days=days - 1)
    # Ask for one day past today so tonight's row is included whether Oura's end_date is
    # inclusive or exclusive, then keep only the requested window.
    end = today + datetime.timedelta(days=1)
    collections = [
        fetch_collection(token, name, start, end)
        for name in ("daily_sleep", "daily_readiness", "sleep")
    ]
    nights = [n for n in merge_days(*collections) if start.isoformat() <= n["night_date"] <= today.isoformat()]
    save_nights(client, nights)
    return len(nights)
