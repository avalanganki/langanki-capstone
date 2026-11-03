# Backlog

Grouped by user story. New issues and bugs start here. Items move to `docs/todo.md` when work begins.

## v0.1.0

### US00 Foundations: running skeleton
As the developer, I want a Streamlit app that starts cleanly and shows sample nights, so every later story has something working to build on.

Status: done, issue #1 (see `docs/xchangelog.md`)

### US01 Prototype: apply Oct 1 review notes
As Ava, I want the prototype to reflect my Oct 1 review notes (`docs/notes.md`), so later UI work builds on the right design.

Status: done, issue #2 (see `docs/xchangelog.md`)

## v0.2.0

### US02 Nightly entries: create, read, update, delete
As Ava, I want to save each night's answers as a dated entry with tags, look back at past entries, fix mistakes, and remove an entry I made by mistake, so my log is complete and accurate before it gets linked to Oura scores. Source: `D08.md`. Covers PRD FR-3, FR-8, and single-entry delete from FR-11.

Decisions: entries live in a Supabase `entries` table. Tags are typed by Ava (comma-separated) until Claude extraction (FR-4) is built. The night's questions are 3 fixed, neutral questions until Claude question generation (FR-2) is built. One entry per date.

- Create: answer the night's questions and submit; the app saves a dated entry with the free text and its tags. Issue #3, done, see `docs/xchangelog.md`.
- Read: see a list of past entries by date, and open one to see the answers and tags. Issue #4, done, see `docs/xchangelog.md`.
- Update: fix a wrong tag or edit an answer on a saved entry. Issue #5, done, see `docs/xchangelog.md`.
- Delete: remove one entry made by mistake. Issue #6, done, see `docs/xchangelog.md`.

## v0.3.0

### US03 Connect Oura: sign in and fetch daily summaries
As Ava, I want to connect my Oura account once and have Patterns pull my daily sleep score, readiness, and average HRV, so my entries can later be linked to real scores instead of sample data. Source: PRD FR-1. Registration values: `docs/oura-app-registration.md`.

Decisions (2026-11-03): Oura data is never sent to Claude or any AI model (Oura API and MCP Agreement Sec. 4(d)); PRD v1.2, architecture, and CLAUDE.md updated to match. Oura's MCP Server was ruled out (no public Oura server found, and MCP data can't be stored). Scope `daily` only. Until Oura approves the app, the Oura client ID and secret are blank placeholders: the app shows "Waiting for Oura app approval" and keeps using the synthetic sample nights, and all tests mock Oura. Checks that need the real API are marked "after approval".

- Connect: OAuth sign-in (PKCE, state), callback at `/callback/`, tokens stored in Supabase, disconnect and revoke. Issue #7, see `docs/todo.md`.
- Fetch: pull daily sleep score, readiness, and average HRV for a date range into a `nights` table, refreshing tokens as needed. Issue #8, see `docs/todo.md`.
- Show: the Tonight tab shows stored Oura nights when connected and sample nights otherwise, labeled, with the night count. Issue #9, see `docs/todo.md`.
- Verify: after Oura approves the app, run the real connect, fetch, show, refresh, and disconnect checks; confirm average HRV works with `daily`; add the Streamlit Cloud redirect URI. Issue #10, see `docs/todo.md`.

## Unscheduled

### Question generation: don't ask about screen use
Found in `docs/notes.md` (Oct 1, item 3). Ava answers on a screen, so a question like "what time did you stop looking at screens?" doesn't work. The Claude prompt for nightly questions should steer away from screen-time questions. Pick up with the question-generation story (FR-2).

### Drop the `test_entries` hello-world table
Found while planning US02. `supabase/migrations/0001_test_entries.sql` is left over from the Supabase hello-world and the app no longer uses it. Add a migration that drops it once `entries` is live.

### Off-topic answers: "not mentioned" is not "none"
Found testing US02 Create (answering the caffeine question with only food). The entry saves as-is, which is right, but a missing `caffeine` tag would later read as "no caffeine" in trends. When tag extraction (FR-4) and trends (FR-6/7) are built, treat a night with no caffeine tag as unknown, not zero, unless the answer says none. Possibly a short neutral follow-up when an answer doesn't address its question.

### Nights with no ring data
Found testing US02 Read. If the ring wasn't worn, Oura has no sleep score for that night. When Oura linking (FR-5) is built, the entry should still open and show "No ring data for this night" instead of blanks or zeros, and that night is left out of any correlation (and out of its night count).

### Tag source: typed vs found in answers
Found testing US02 Update. Ava can add tags that aren't in her answers, which is allowed (she knows things she didn't write). Once Claude extracts tags (FR-4), record whether each tag was typed by Ava or found by Claude, so an edit never gets silently overwritten by re-extraction.

### Delete a range of entries (e.g. a week)
Found testing US02 Delete. #6 deletes one entry at a time; there is no bulk delete. FR-11 asks for single-entry and delete-all only. If a range delete is wanted, it needs its own confirm step. Trends and correlations must be computed from whatever entries remain and the "based on N nights" count must drop to match; deleted nights show as gaps, never filled in.

### Journal answers that mention Oura scores
Found with the decision above. If Ava types her readiness or sleep score into an answer, that text would reach Claude. When tag extraction (FR-4) is built, decide whether to strip numbers that look like scores before sending, or just note it in the privacy policy.
