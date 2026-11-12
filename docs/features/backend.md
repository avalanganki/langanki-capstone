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

Done by Ava on 2026-11-05: http://localhost:8000/api/health shows `{"status":"ok"}`. `ALLOWED_USER_ID` is not in `.env` yet (checked for presence only); setting it, and creating a Supabase Auth user if needed, moves to the frontend skeleton issue.

## Entry and tag routes (issue #19)

Built on 2026-11-12, Python 3.9.6, FastAPI 0.128.8. Every route below needs sign-in (`require_user`, set once on each router).

What it does:
- `GET /api/questions` returns `{"questions": [...]}`, the three fixed questions from `entries.QUESTIONS`.
- `GET /api/entries` returns `{"entries": [...]}`, newest first. Each entry has `id`, `entry_date`, `answers`, `tags`, `suggested_tags`, and `tag_sources` as `[{"tag", "source"}]`, where source is `suggested` or `typed`.
- `GET /api/entries/{id}` returns one entry, or 404 "Entry not found."
- `POST /api/entries` saves a new entry and returns it with 201. It refuses an unknown question (400 "Unknown question."), all-blank answers (400 "Answer at least one question to save."), and a date already used (409 "You already have an entry for this date. Edit it in Past entries."). Tags and suggested tags are cleaned like the Streamlit tags box: lowercase, trimmed, no blanks or repeats.
- `PUT /api/entries/{id}` changes answers and tags. The questions must be the stored ones, in the same order (otherwise 400 "Unknown question."). `suggested_tags: null`, or leaving it out, keeps the stored suggestion. The date never changes.
- `DELETE /api/entries/{id}` returns 204, or 404 if the entry is missing.
- `POST /api/tags/suggest` takes `{"pairs": [{"question", "answer"}]}` and returns `{"tags": [{"tag", "is_new"}]}` from `tagger.suggest_tags`, with the known tags from saved entries. It saves nothing. Without a Claude key it's 503 "Tag suggestions are off (no Claude API key)."; a Claude failure is 503 "Couldn't suggest tags right now. Type them instead."

Decided while building:
- `require_user` moved to `api/auth.py` so the routers can use it without a circular import. `api.main` still re-exports it.
- An unknown question is refused before anything else on Suggest tags, so it never reaches Claude, even if the key is set.
- FastAPI's default 422 response echoes the request body back, which could include journal text. The API now answers any malformed request with 422 "Invalid request." and nothing else.
- Database errors can carry row values (Postgres "Failing row contains ..."). `api/storage.py` turns any unexpected database error into 503 "Couldn't reach the database. Try again." and logs only the error type.
- A blank `answers` list counts as all blank (400), the same as three empty answers.
- `FakeClient` moved from `tests/test_app.py` to `tests/fakes.py`, so the Streamlit and API tests share it.

### Check 1 (AC1 to AC6): tests

`tests/test_api_entries.py` (Supabase faked with `FakeClient`, `require_user` overridden with `app.dependency_overrides`, `tagger.suggest_tags` or Claude's client mocked):
- Sign-in (AC3): `test_every_route_needs_sign_in`, for all seven routes; nothing is saved and nothing goes to Claude.
- Questions: `test_questions`
- Create (AC1): `test_create_returns_201_with_saved_entry`, `test_create_same_date_is_409`, `test_create_blank_is_400` (three cases), `test_create_unknown_question_is_400` (AC4), `test_create_normalizes_tags`, `test_create_bad_date_is_422_without_answer_text` (AC5)
- List and get (AC1): `test_list_newest_first_with_tag_sources`, `test_list_empty`, `test_get_found`, `test_get_missing_is_404`
- Update (AC1): `test_update_changes_answers_and_tags`, `test_update_null_keeps_suggested_tags`, `test_update_changed_question_is_400` (reordered, missing, and replaced question), `test_update_blank_is_400`, `test_update_missing_is_404`
- Delete (AC1): `test_delete_then_404`
- Database down (AC5): `test_database_error_is_503_without_details`
- Suggest (AC2): `test_suggest_returns_tags_with_new_flag`, `test_suggest_off_when_not_configured`, `test_suggest_tagger_error_is_503_without_answer_text` (AC5), `test_suggest_unknown_question_sends_nothing` (AC4), `test_suggest_real_tagger_with_fake_claude` (only the question and answer are sent), `test_suggest_does_not_log_answer_text` (AC5)
- Logs (AC5): `test_create_does_not_log_answer_text`, plus `caplog` checks in the database and Suggest tests.

`pytest -q`: 185 passed (36 new), with no real Supabase, Oura, or Claude (AC6).

### Check 2: route list

Done by Claude on 2026-11-12: `uvicorn api.main:app --port 8000` started without error. The OpenAPI route list shows `GET /api/health`, `GET /api/me`, `GET /api/questions`, `GET /api/entries`, `POST /api/entries`, `GET`, `PUT`, and `DELETE /api/entries/{entry_id}`, and `POST /api/tags/suggest`. Without sign-in, all seven new routes return 401 "Sign in required." The server log shows only method, path, and status.

Pending: Ava opens http://localhost:8000/docs and screenshots the route list, with no data shown.
