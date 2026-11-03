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

## Update (issue #5)

Runs on 2026-11-03.

### Check 1 (AC1, AC2): edit an answer and a tag

Covered by `test_edit_answer_and_tag_then_save`: the edit form opens pre-filled with the saved answers and tags ("late caffeine, stress"). After changing an answer and the tags to "stress, Nap", it shows "Updated your entry for 2000-01-05.", stores tags `["stress", "nap"]` with `updated_at` set and `entry_date` unchanged, and returns to view mode with the new values. `test_update_entry_sends_answers_and_tags_not_date` checks that the update never includes `entry_date`.

2026-11-03: Ava changed one answer and one tag on a synthetic entry in the running app; the view and the Supabase row showed the new values and a new `updated_at`.

### Check 2 (AC3): Cancel

Covered by `test_cancel_leaves_entry_unchanged`: after typing a change and pressing Cancel, the stored row and the view are unchanged and `updated_at` is not touched.

2026-11-03: Ava made a change and pressed Cancel in the running app; the original values remained.

### Check 3 (AC4): date can't change

Covered by `test_edit_mode_date_is_not_an_input`: edit mode shows "Date: Wed, Jan 5, 2000" as text, and the only date input on the page is Tonight's.

2026-11-03: Ava confirmed in the running app that edit mode shows the date as text, not an input.

### Also: all-blank edit refused

`test_edit_all_blank_is_refused` and `test_update_entry_all_blank_raises`: clearing every answer shows "Answer at least one question to save.", nothing is saved, and the form stays open.

Decided: Edit, Save changes, and Cancel use button callbacks instead of `st.rerun()`, so the page never shows a stale edit form after leaving edit mode.

### Check 4 (AC5): tests pass without real Supabase

`pytest`: 29 passed. `streamlit run app.py --server.headless true` starts, `/_stcore/health` returns `ok`, and the server log has no errors.

## Delete (issue #6)

Runs on 2026-11-03.

### Check 1 (AC1, AC3): delete the middle of 3 entries

Covered by `test_delete_confirm_removes_only_selected_entry`: with synthetic entries on 2000-01-01, 01-03, and 01-05, selecting 01-03 and pressing Delete shows "Delete your entry for 2000-01-03? This can't be undone." and deletes nothing yet. "Yes, delete" then shows "Deleted your entry for 2000-01-03.", leaves 2 rows, lists the other two newest first with "2 entries.", and leaves their answers and tags unchanged. `test_delete_entry_deletes_by_id_only` checks the query matches on `id` alone.

`test_deleting_last_entry_shows_empty_state`: deleting the only entry shows the "Deleted..." message and the empty state.

2026-11-03: Ava deleted the middle of 3 synthetic entries in the running app; the list dropped it, the others were unchanged, and the Supabase row count went from 3 to 2.

### Check 2 (AC2): Cancel

Covered by `test_delete_cancel_keeps_entry`: Delete then Cancel keeps all 3 rows and returns to the normal view.

2026-11-03: Ava pressed Delete then Cancel in the running app; the entry stayed listed.

### Check 3 (AC4): tests pass without real Supabase

`pytest`: 33 passed. `streamlit run app.py --server.headless true` starts, `/_stcore/health` returns `ok`, and the server log has no errors.

### Check 4: full create, read, update, delete pass

2026-11-03: Ava created, opened, edited, and deleted one synthetic entry end to end in the running app with no errors.
