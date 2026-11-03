# Connect Oura (US03, v0.3.0)

Oura data is never sent to Claude or any AI model (Oura API and MCP Agreement Sec. 4(d)). No real Oura values or tokens are recorded here.

## Connect (issue #7)

Runs on 2026-11-03, Python 3.9.6, Streamlit 1.50.0, pytest 8.4.2. The Oura app was approved during this issue, so the real sign-in checks can run here instead of waiting for #10.

### Check 1 (AC1): waiting message with blank settings

Covered by `test_oura_not_configured_shows_waiting_message`: with blank Oura settings the sidebar shows "Waiting for Oura app approval. Showing sample data." and every earlier test still passes. Tests never read the real `.env`: an autouse fixture patches `oura.get_settings` to blanks.

The real `.env` now has all three Oura settings (names checked, values not printed), so the running app shows "Connect Oura" instead.

### Check 2 (AC4): stale or foreign sign-in refused

Covered by `test_callback_with_bad_state_saves_nothing`, `test_unknown_state_refused_before_any_network_call`, `test_expired_state_refused`, and `test_state_works_only_once`.

Callback path: `curl localhost:8501/callback/?code=fake&state=fake` returns `301 Location: /callback?code=fake&state=fake`, which then loads the app (200). Streamlit drops the trailing slash but keeps the query, so the app still reads `code` and `state`. The token exchange sends the registered `http://localhost:8501/callback/` exactly.

Pending: Ava opens that URL in the running app, screenshots "Sign-in expired or didn't match. Try Connect again.", and shows `oura_connection` still empty.

### Check 3 (AC5): cancelled

Covered by `test_callback_cancelled`.

Pending: Ava opens `http://localhost:8501/callback/?error=access_denied` and screenshots "Oura connection was cancelled."

### Check 4 (AC2, AC3, AC6): real sign-in and disconnect

Covered by `test_authorize_url_asks_for_daily_only_with_s256`, `test_finish_sign_in_exchanges_code`, `test_callback_saves_connection`, `test_disconnect_removes_tokens`, and `test_disconnect_deletes_tokens_even_if_revoke_fails`.

Pending (now possible, since the app is approved):
- Click "Connect Oura". Screenshot Oura's consent page, which should list daily summaries only.
- Approve. Screenshot "Connected to Oura."
- Show one row in `oura_connection`, with only `id`, `scope`, `expires_at`, and `connected_at` visible. Hide the token columns.
- Click Disconnect. Screenshot "Disconnected from Oura." and the empty table.

Decided: revoke uses GET with the token as a query parameter, because that is the form Oura's docs give (`/oauth/revoke?access_token=...`). The issue said POST. Revoke failures are ignored, so our copy of the tokens is always deleted.

### Check 5 (AC7, AC8): tests and privacy

`pytest`: 53 passed (20 new). `requests` is mocked in every Oura test; Supabase is the in-memory fake or a `MagicMock`. Token errors carry only the HTTP status, never the code, tokens, or response body (`test_token_error_never_includes_code_or_body`). `test_callback_saves_connection` checks the token never appears on the page.

`streamlit run app.py --server.headless true` starts, `/_stcore/health` returns `ok`, and the server log has no errors.
