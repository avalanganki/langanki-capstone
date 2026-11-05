"""Oura OAuth2 sign-in (authorization code flow with PKCE).

Never log, print, or show tokens, codes, or Oura response bodies.
Oura data must never be sent to Claude or any AI model (Oura API agreement Sec. 4(d)).
"""

import base64
import datetime
import hashlib
import os
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
USER_AGENT = "Patterns/0.3 (capstone project)"
STATE_MAX_AGE = 10 * 60  # seconds
TIMEOUT = 15  # seconds per Oura request

ENV_PATH = Path(__file__).parent / ".env"
TABLE = "oura_connection"

# state -> (verifier, created_at). Module-level so it survives Streamlit reruns and the
# browser coming back from Oura in a new session (same server process).
_pending = {}


class OuraAuthError(Exception):
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
