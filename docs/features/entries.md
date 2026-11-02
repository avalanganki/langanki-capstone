# Nightly entries (US02, v0.2.0)

## Create (issue #3)

Evidence for the five checks. Runs on 2026-10-29, Python 3.9.6, Streamlit 1.50.0, pytest 8.4.2.

### Check 1 (AC1): save a synthetic entry

`0002_entries.sql` is applied: a count query against `entries` with the app's key returned 0 rows before any saves.

Pending: Ava saves a synthetic entry in the running app, screenshots "Saved your entry for <date>.", and shows the row in the Supabase table view.

### Check 2 (AC2, AC3): blank and duplicate saves refused

Covered by `test_blank_form_is_refused` and `test_second_save_for_same_date_is_refused` (in-memory fake client; row count stays 0 and 1).

Pending: screenshots of both messages in the running app with the row count unchanged.

### Check 3 (AC4): tags cleaned

`parse_tags(" Late Caffeine, stress,,stress ")` returns `["late caffeine", "stress"]` (`test_parse_tags`, `test_save_shows_confirmation_and_stores_row`).

Pending: the saved `tags` value from the Check 1 row.

### Check 4 (AC5): tests pass without real Supabase

```
$ pytest -v
tests/test_app.py::test_app_shows_title_and_sample_nights PASSED
tests/test_app.py::test_tonight_tab_has_three_questions_and_tags PASSED
tests/test_app.py::test_save_shows_confirmation_and_stores_row PASSED
tests/test_app.py::test_blank_form_is_refused PASSED
tests/test_app.py::test_second_save_for_same_date_is_refused PASSED
tests/test_entries.py::test_parse_tags[ Late Caffeine, stress,,stress -expected0] PASSED
tests/test_entries.py::test_parse_tags[-expected1] PASSED
tests/test_entries.py::test_parse_tags[ , ,-expected2] PASSED
tests/test_entries.py::test_parse_tags[Run, run, RUN, nap-expected3] PASSED
tests/test_entries.py::test_create_entry_inserts_row PASSED
tests/test_entries.py::test_create_entry_all_blank_raises PASSED
tests/test_entries.py::test_create_entry_duplicate_raises PASSED
tests/test_entries.py::test_create_entry_other_api_error_passes_through PASSED
tests/test_sample_data.py::test_loads_sample_file PASSED
tests/test_sample_data.py::test_missing_field_raises PASSED
15 passed in 2.00s
```

`db.get_client` is patched in every app test, and `create_entry` tests use a `MagicMock` client.

`streamlit run app.py --server.headless true` starts and `/_stcore/health` returns `ok`. Only the known `NotOpenSSLWarning` and Watchdog notices are printed.

### Check 5: privacy

`git grep -nE "sb_secret_|sb_publishable_|eyJ...|supabase\.co"` over tracked files returns nothing. `.env` is gitignored. The app prints no answers, tags, or keys; the server log above shows only startup lines.
