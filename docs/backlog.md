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

- Create: answer the night's questions and submit; the app saves a dated entry with the free text and its tags. Issue #3, see `docs/todo.md`.
- Read: see a list of past entries by date, and open one to see the answers and tags. Issue #4, see `docs/todo.md`.
- Update: fix a wrong tag or edit an answer on a saved entry. Issue #5, see `docs/todo.md`.
- Delete: remove one entry made by mistake. Issue #6, see `docs/todo.md`.

## Unscheduled

### Question generation: don't ask about screen use
Found in `docs/notes.md` (Oct 1, item 3). Ava answers on a screen, so a question like "what time did you stop looking at screens?" doesn't work. The Claude prompt for nightly questions should steer away from screen-time questions. Pick up with the question-generation story (FR-2).

### Drop the `test_entries` hello-world table
Found while planning US02. `supabase/migrations/0001_test_entries.sql` is left over from the Supabase hello-world and the app no longer uses it. Add a migration that drops it once `entries` is live.
