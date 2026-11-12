# Link entries to the next night (US05, v0.5.0)

App code only. Nothing here is sent to Claude or any AI model (Oura API and MCP Agreement Sec. 4(d)). No real Oura values or journal text are recorded here; tests use synthetic 2000-dated rows.

## Link (issue #14)

Runs on 2026-11-05, Python 3.9.6.

How it works: Oura's `day` is the date the night's sleep ended, so the entry dated D goes with the night dated D + 1. `links.link_entries` works this out by date every time; nothing is stored, so edits, deletes, and refreshes can't leave a stale link.

Decided while building:
- Past entries uses `links.link_one(client, entry)`, which links only the entry on screen against every stored night. That is cheaper than linking all entries on each view, and the full set of stored nights keeps the "no ring data" range right.
- `links.load_linked(client)` links every entry; trends will use it with `linked_count`.
- HRV shows "ms" only when there is a value: "HRV No data", not "HRV No data ms".
- Not connected means no link at all (`None`), even when nights are stored, so sample nights are never matched to real entries.

### Check 1 (AC1 to AC7): tests

`tests/test_links.py`:
- `test_next_night_date`: Jan 4 to Jan 5, Jan 31 to Feb 1, Dec 31 to Jan 1, and Feb 28 to Feb 29 and Feb 29 to Mar 1 in the leap year 2000.
- `test_statuses_and_order`: linked, no ring data inside the fetched range, and not fetched before or after it, in input order (AC1, AC3, AC4).
- `test_partial_night_still_linked` (AC2), `test_no_nights_means_not_fetched`, `test_linked_count_skips_empty_nights`
- `test_load_linked_none_when_not_connected_and_never_reads_samples` (AC5), `test_load_linked_when_connected`, `test_link_one_uses_full_stored_range`

`tests/test_app.py`:
- `test_linked_entry_shows_next_night_with_no_data`: "Next night (Jan 2): Sleep score 81 · Readiness No data · HRV 52 ms" (AC1, AC2).
- `test_entry_in_range_without_night_shows_no_ring_data` (AC3), `test_entry_after_newest_night_shows_not_fetched` (AC4)
- `test_not_connected_shows_connect_message_and_no_scores` (AC5)
- `test_link_follows_edits_and_refresh`: a newly fetched night appears without re-saving the entry (AC6).
- Each app test also asserts `tagger.suggest_tags` is never called while viewing entries.

`pytest`: 144 passed (17 new). The running app's `/_stcore/health` returns `ok`. Ava's server on port 8501 was serving this branch's code; its log was not checked.

### Check 2: running app, connected, real data

Done by Ava on 2026-11-12: she reconnected to Oura (after an earlier failed attempt on Oura's sign-in page), refreshed, and opened a past entry. It shows "Next night" with the following day's date and that night's scores. Ava described it in words; no values or screenshots were recorded. The no-data, no-ring-data, and not-fetched states are covered by tests with synthetic data.

### Check 3: running app, disconnected

Done by Ava on 2026-11-12, disconnected after the #10 checks: an entry in Past entries shows "Connect Oura to see the next night's scores." Ava confirmed it in words; no screenshot.
