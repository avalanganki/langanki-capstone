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

Done by Ava on 2026-11-05 in the running app: the message "Sign-in expired or didn't match. Try Connect again." appeared and `oura_connection` stayed empty.

### Check 3 (AC5): cancelled

Covered by `test_callback_cancelled`.

Done by Ava on 2026-11-05: `http://localhost:8501/callback/?error=access_denied` showed "Oura connection was cancelled."

### Check 4 (AC2, AC3, AC6): real sign-in and disconnect

Covered by `test_authorize_url_asks_for_daily_only_with_s256`, `test_finish_sign_in_exchanges_code`, `test_callback_saves_connection`, `test_disconnect_removes_tokens`, and `test_disconnect_deletes_tokens_even_if_revoke_fails`.

Done by Ava on 2026-11-05 with the real Oura sign-in (screenshots kept out of the repo, token columns hidden):
- Oura's consent page asked for daily summaries only.
- After approving, Patterns showed "Connected to Oura." and one row appeared in `oura_connection`.
- Disconnect showed "Disconnected from Oura." and the table was empty again.

Migration `0003_oura_connection.sql` applied in Supabase.

Decided: revoke uses GET with the token as a query parameter, because that is the form Oura's docs give (`/oauth/revoke?access_token=...`). The issue said POST. Revoke failures are ignored, so our copy of the tokens is always deleted.

### Check 5 (AC7, AC8): tests and privacy

`pytest`: 53 passed (20 new). `requests` is mocked in every Oura test; Supabase is the in-memory fake or a `MagicMock`. Token errors carry only the HTTP status, never the code, tokens, or response body (`test_token_error_never_includes_code_or_body`). `test_callback_saves_connection` checks the token never appears on the page.

`streamlit run app.py --server.headless true` starts, `/_stcore/health` returns `ok`, and the server log has no errors. Rerun 2026-11-05: 53 passed. Correction 2026-11-05: the log checked was from a second, idle server Claude started on port 8502. Ava's click-through ran on her own server on port 8501, whose log wasn't checked. The `ok` health check did reach 8501.

## Fetch (issue #8)

Runs on 2026-11-05, Python 3.9.6. All fixtures are synthetic (`tests/fixtures/oura_*.json`, dates in 2000, made-up values).

Decided while building:
- `fetched_at` is set on every save, not left to the column default, which only fills new rows. Otherwise "Last updated" would show the first fetch forever.
- `sync_nights` fetches all three collections before saving anything, so an Oura error never overwrites stored nights (AC6).
- Requests run to one day past today, then results are trimmed to the 14-day window. That way tonight's row is included whether Oura treats `end_date` as inclusive or exclusive.
- `parse_timestamp` reads Supabase timestamps safely: Python 3.9 can't parse `Z` or fractions shorter than 6 digits.
- A network failure (no response at all) shows "Couldn't reach Oura. Try again later."

### Check 1 (AC1 to AC4): merge, save, refresh twice

- `test_merge_all_three_values`, `test_merge_missing_readiness_stays_none`, `test_merge_never_fills_zero` (AC2)
- `test_merge_nap_ignored_for_hrv`, `test_merge_no_long_sleep_means_no_hrv`, `test_merge_two_long_sleeps_longer_wins` (AC3)
- `test_merge_empty_day_left_out_and_sorted_oldest_first`
- `test_fetch_collection_follows_next_token`
- `test_sync_nights_saves_merged_window_and_returns_count`, `test_save_nights_upserts_on_night_date_with_fresh_fetched_at`
- `test_refresh_saves_nights_and_shows_count` (app): shows "Updated 4 nights from Oura." and "Last updated ...". A second refresh leaves exactly 4 rows (AC4), and missing readiness is stored as empty.

### Check 2 (AC5, AC6): token refresh and errors

- `test_valid_token_used_without_refresh`
- `test_expiring_token_refreshed_and_saved_before_fetch`: the call order is refresh, save new tokens, then the three fetches.
- `test_failed_refresh_raises_expired_message`, `test_not_connected_raises`
- `test_fetch_error_status_maps_to_message` for 401, 403, 429, and 500; `test_fetch_network_failure_is_plain_message`
- `test_sync_nights_saves_nothing_if_a_fetch_fails`
- `test_refresh_on_403_shows_membership_message_and_saves_nothing` (app)

`pytest`: 77 passed (24 new). Nothing in `oura.py` logs or prints. Error messages are fixed strings with no tokens, bodies, or health values.

### Check 3: `0004_nights.sql` applied

Done by Ava on 2026-11-05: `0004_nights.sql` applied in Supabase; the empty `nights` table shows `night_date`, `sleep_score`, `readiness`, `avg_hrv`, and `fetched_at`.

### Check 4: not connected

Covered by `test_not_configured_has_no_refresh_button` and `test_oura_not_conDone by Ava on 2026-11-05: the connected sidebar shows "Refresh Oura data" and "Disconnect" (screenshot kept out of the repo, no real values shown). The not-configured state is covered by the tests above.ted state with no Refresh button.

## Show (issue #9)

Runs on 2026-11-05, Python 3.9.6. All rows in tests are synthetic (dates in 2000, made-up values). No real Oura values are recorded here.

Decided while building:
- Table values are shown as text so a missing value reads "No data". A numeric column would show it blank. A real 0 still shows as 0.
- HRV shows whole numbers without ".0" and anything else to one decimal.
- If you're connected but nothing has been fetched yet, Tonight shows the sample nights with the sample label.

### Check 1 (AC1): sample nights when not connected

Covered by `test_not_connected_gives_sample`, `test_connected_without_rows_gives_sample`, and `test_tonight_sample_label_when_not_connected`.

Done by Ava on 2026-11-05: Tonight while not connected shows the sample nights labeled "Sample data. Not real Oura data." (screenshot kept out of the repo).

### Check 2 (AC2 to AC4): Oura nights, "No data", night count

- `test_connected_with_rows_gives_newest_14_oldest_first`: 20 synthetic nights stored, the newest 14 shown oldest first.
- `test_tonight_shows_oura_nights_when_connected` (app): "From your Oura ring." label, dates oldest first, missing readiness and HRV shown as "No data", "Based on 3 nights."
- `test_show_value_never_zero_for_missing`, `test_has_values`: the count includes only nights with at least one value.

The real-data view is checked in #10, described in words only.

### Check 3 (AC5): tests

`pytest`: 84 passed (7 new). Oura and Supabase are never touched: tests use the in-memory fake client.

`streamlit run app.py` is running and `/_stcore/health` returns `ok`. Correction 2026-11-05: the log checked was from a second, idle server Claude started on port 8502. Ava's click-through ran on her own server on port 8501, whose log wasn't checked. The `ok` health check did reach 8501.

## Real API (issue #10)

Run by Ava on 2026-11-05 against her real Oura account. Results are described in words only; no real values are recorded.

### Check 1 (AC1): consent page and connect

Done under #7 (see Connect, Check 4): Oura's consent page asked for daily summaries only, and Patterns showed "Connected to Oura."

### Check 2 (AC2): refresh

Done: "Refresh Oura data" saved 14 nights, and the `nights` table holds 14 rows.

Done by Ava on 2026-11-12: average HRV is present with the `daily` scope, so no extra Oura scope is needed. The scope stays `daily` only; the privacy policy, app registration, and CLAUDE.md need no change.

### Check 3 (AC3): Tonight

Done: Tonight shows the nights labeled "From your Oura ring." with the "Based on N nights." caption.

### Check 4 (AC4): expired sign-in renews itself

Done by Ava on 2026-11-12: after reconnecting, she set `expires_at` to an hour in the past (`update oura_connection set expires_at = now() - interval '1 hour';`) and clicked "Refresh Oura data". It refreshed without asking her to connect again, and `select expires_at > now() as renewed from oura_connection;` returned `true`. That query returns only a true/false value, never the token.

### Check 5 (AC5): disconnect

Done: after Disconnect, Patterns no longer appears in Ava's Oura connected apps.

Done by Ava on 2026-11-12: after Disconnect, `select count(*) from oura_connection;` returned 0.

### Check 6 (AC6): Streamlit Cloud

Dropped on 2026-11-05 by Ava's decision: Streamlit is not deployed live. The live redirect URI is registered in the US06 deploy issue instead.

### Check 7: privacy

Done by Claude on 2026-11-12. During these checks, the Streamlit log (14 lines) had zero matches for `access_token`, `refresh_token`, `Bearer`, `code=`, `state=`, `sleep_score`, `readiness`, `hrv`, or `Traceback`. Only the match counts were printed, never the log lines. `git status` shows no `.env` or exports. Claude never read the `nights` or `oura_connection` tables: Ava ran every query and reported the results in words.

`pytest -q` on `main`: 191 passed. No code fixes were needed, so there is no `dev/10-oura-verify` branch.
