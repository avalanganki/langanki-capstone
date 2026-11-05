# Backend for the new UI (US06, v0.6.0)

See `docs/decisions/frontend_decision.md`. No secret values, journal text, or Oura values are recorded here.

## Settings (issue #16)

Runs on 2026-11-05, Python 3.9.6.

What changed:
- `config.get(name, default="")` reads a setting from the environment, loading `.env` once on first use. Environment variables win over `.env`.
- `db.get_client()`, `oura.get_settings()`, and `tagger.get_api_key()` read only through `config.get`. Their `st.secrets` fallbacks are gone.
- `db.get_client()` raises `RuntimeError("Supabase settings missing.")` when the URL or key is blank, instead of falling through to Streamlit.

Decided while building:
- `.env` loads lazily, on the first `config.get`, not at import. `tests/conftest.py` marks it as already loaded, so **tests never read the real `.env`**. Before this, any test run loaded the real keys into the test process, even though tests patched around them.
- Streamlit Community Cloud exposes root-level secrets as environment variables, so the live app needs no change. AC2 confirms this.
- The default Oura redirect stays `http://localhost:8501/callback/` until the API takes over the callback.

### Check 1 (AC3): only `app.py` imports Streamlit

`git grep -n "streamlit" -- db.py oura.py tagger.py entries.py nights.py sample_data.py config.py` returns nothing (exit 1). `links.py` is on `dev/14-link-nights` and has no Streamlit import either. `test_only_app_imports_streamlit` keeps it that way.

### Check 2 (AC4, AC5): tests

`tests/test_config.py`:
- `test_reads_environment_and_strips`, `test_default_when_missing`
- `test_reads_dotenv_and_environment_wins` (a temp `.env`), `test_dotenv_loaded_once`
- `test_db_raises_plain_error_without_settings` (AC4: plain message, no values, no client built), `test_db_uses_config_values`
- `test_only_app_imports_streamlit` (AC3)

Updated: `test_get_settings_reads_environment` (Oura) and `test_is_configured_reads_environment` (Claude) no longer stub `load_dotenv`.

`pytest`: 134 passed (7 new).

With the real `.env`, a one-off check printed only presence: all six settings present, Oura and Claude configured, and the Supabase client built. No values were printed.

### Check 3 (AC1, AC2): click-through

Pending:
- Locally: done by Ava on 2026-11-05. On http://localhost:8501 (`dev/16-config`), past entries, Oura Refresh, and Suggest tags all work as before.
- Live: dropped on 2026-11-05 by Ava's decision. The Streamlit app won't be the live version of Patterns; the live URL will be the Render deploy of the new UI (US06). AC2 no longer applies.

## API skeleton (issue #17)

Runs on 2026-11-05, Python 3.9.6, FastAPI 0.128.8, uvicorn 0.39.0, supabase 2.32.0.

What it does:
- `GET /api/health` returns `{"status": "ok"}` with no sign-in, for the host's health check.
- `require_user` checks every protected route:
  - It reads `Authorization: Bearer <token>`.
  - It asks Supabase whether the token is valid (`auth.get_user(token)`), which works with both current and legacy signing keys.
  - It allows only the user whose ID matches `ALLOWED_USER_ID`.
- `GET /api/me` returns `{"signed_in": true}` and nothing else: no email, no IDs.
- CORS allows only the Vite dev server, `http://localhost:5173`.

Decided while building:
- A missing or non-Bearer header is refused before Supabase is called.
- If Supabase can't be reached or isn't configured, the answer is 503 "Couldn't check sign-in. Try again.", not 401. A 401 would wrongly tell Ava to sign in again. A token Supabase rejects is still 401.
- A blank `ALLOWED_USER_ID` refuses everyone (403), so a missing setting never opens the API.

### Check 1 (AC1): the API starts

`uvicorn api.main:app --port 8000` started. Against the real `.env`:

```
GET /api/health                                  {"status":"ok"}
GET /api/me (no header)                          {"detail":"Sign in required."} HTTP 401
GET /api/me (Bearer not-a-real-token)            {"detail":"Sign in required."} HTTP 401
```

The made-up token was checked by the real Supabase project and rejected. The server log shows only method, path, and status; the token does not appear in it.

### Check 2 (AC2 to AC5): tests

`tests/test_api.py`:
- `test_health_needs_no_sign_in`
- `test_me_without_bearer_token_is_401`: four header cases, and Supabase isn't called (AC2).
- `test_rejected_token_is_401`, `test_no_user_in_response_is_401`
- `test_supabase_unreachable_is_503`, `test_missing_supabase_settings_is_503`
- `test_other_account_is_403` (AC3), `test_blank_allowed_user_is_403`
- `test_ava_signed_in` (AC4)
- `test_api_does_not_log_token_or_ids`, and every refusal test checks that the response has no token, ID, or email.
- `test_cors_allows_vite_dev_server`, `test_cors_refuses_other_origins`

`pytest`: 149 passed (15 new). Supabase is always mocked.

### Check 3: real sign-in

Waits for the frontend skeleton issue, which adds a sign-in screen. Until then, AC4 is covered by tests.

Pending: Ava opens http://localhost:8000/api/health and sees `{"status":"ok"}`. She also adds her Supabase user ID to `.env` as `ALLOWED_USER_ID` (Supabase, Authentication, then Users). That's needed before the frontend sign-in works.
