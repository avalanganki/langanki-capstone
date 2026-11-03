# Nightly entries (US02, v0.2.0)

## Create (issue #3)

Evidence for the five checks. Runs on 2026-10-29, Python 3.9.6, Streamlit 1.50.0, pytest 8.4.2.

### Check 1 (AC1): save a synthetic entry

`0002_entries.sql` is applied: a count query against `entries` with the app's key returned 0 rows before any saves.

2026-11-03: Ava saved synthetic entries in the running app (for example `2000-01-01` with tags `synthetic, test`, and `2000-01-02`). The Supabase table view shows one row per date with `answers` as question/answer pairs and `tags` as `text[]`. Screenshot reviewed in session, not committed.

### Check 2 (AC2, AC3): blank and duplicate saves refused

Covered by `test_blank_form_is_refused` and `test_second_save_for_same_date_is_refused` (in-memory fake client; row count stays 0 and 1).

2026-11-03, in the running app: a blank save showed "Answer at least one question to save." and saved nothing. Filling in answers for the same date then saved normally, so the blank attempt didn't use up the date. The table has no duplicate `entry_date` values; skipped identity ids (3, 6, 7) match inserts that were refused.

### Check 3 (AC4): tags cleaned

`parse_tags(" Late Caffeine, stress,,stress ")` returns `["late caffeine", "stress"]` (`test_parse_tags`, `test_save_shows_confirmation_and_stores_row`).

Saved rows in Supabase show lowercased, trimmed tags (for example `["late caffeine"]`, `["synthetic","test"]`).

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

### Check 5 (AC6): Enter does not save

2026-11-03, in the running app: typing in the Tags box and pressing Enter saved nothing; clicking Save saved the entry. Also covered by an `AppTest` (16 tests pass).

### Check 6: privacy

`git grep -nE "sb_secret_|sb_publishable_|eyJ...|supabase\.co"` over tracked files returns nothing. `.env` is gitignored. The app prints no answers, tags, or keys; the server log above shows only startup lines.

## Read (issue #4)

Runs on 2026-11-03.

### Check 1 (AC1): empty state

Covered by `test_past_entries_empty_state` (fake client with no rows shows "No entries yet. Save one from Tonight.").

Decided: the real table already has rows, so the AppTest above is the evidence for the empty state rather than deleting data.

### Check 2 (AC2): newest first with count

Covered by `test_past_entries_listed_newest_first_with_count` (entries saved out of order list as "Wed, Jan 5, 2000", then "Sat, Jan 1, 2000"; caption "2 entries."). Against the real table, `list_entries` returned 6 rows in descending `entry_date` order (count and order only; no entry content printed).

Decided: one entry reads "1 entry." rather than "1 entries." (`test_single_entry_count_is_singular`).

2026-11-03: Ava checked in the running app that synthetic entries saved out of order list newest first with the right count.

### Check 3 (AC3): open an entry

Covered by `test_selecting_entry_shows_answers_and_tags`: every question shown, each answer in a bordered card, blank answers as "No answer", tags as "Tags: late caffeine, stress" or "Tags: No tags". `get_entry` against the real table found an existing id and returned `None` for a missing one.

2026-11-03: Ava opened an entry in the running app and it matched its row in Supabase.

### Check 4 (AC4): tests pass without real Supabase

`pytest`: 23 passed. App tests patch `db.get_client` with an in-memory fake; `list_entries`/`get_entry` tests use a `MagicMock` client.

`streamlit run app.py --server.headless true` starts, `/_stcore/health` returns `ok`, and the server log has no errors.
