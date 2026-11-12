# Changelog

Completed items moved from `docs/todo.md`.

## v0.1.0

- [x] #1 US00 Foundations: running skeleton. Merged 2026-10-22. Evidence: `docs/features/foundations.md`
- [x] #2 US01 Prototype: apply Oct 1 review notes. Reviewed by Ava and merged 2026-10-22.

## v0.2.0

- [x] #3 US02 Create: save tonight's entry. Merged 2026-11-03. Evidence: `docs/features/entries.md`
- [x] #4 US02 Read: list and open past entries. Merged 2026-11-03. Evidence: `docs/features/entries.md`
- [x] #5 US02 Update: edit answers and tags. Merged 2026-11-03. Evidence: `docs/features/entries.md`
- [x] #6 US02 Delete: remove one entry. Merged 2026-11-03. Evidence: `docs/features/entries.md`. Closes out US02 nightly entries (create, read, update, delete).

## v0.3.0

- [x] #7 US03 Connect: sign in with Oura, store tokens, disconnect. Real sign-in checked by Ava and merged 2026-11-05. Evidence: `docs/features/oura.md`
- [x] #8 US03 Fetch: pull daily sleep score, readiness, and average HRV into `nights`. Merged 2026-11-05. Evidence: `docs/features/oura.md`
- [x] #9 US03 Show: Tonight tab uses stored Oura nights when connected, sample nights otherwise. Merged 2026-11-05. Evidence: `docs/features/oura.md`

## v0.4.0

- [x] #11 US04 Suggest: Claude suggests tags from all answers, reusing known tags. Merged 2026-11-05. Evidence: `docs/features/tags.md`
- [x] #12 US04 Source: remember suggested vs typed tags; suggest on edit. Merged 2026-11-05. Evidence: `docs/features/tags.md`
- [x] #13 US04 Verify: real Claude tag accuracy and cost. 12 of 12 synthetic nights matched, about $0.004 a night, and it works on Streamlit Cloud. Merged 2026-11-05. Evidence: `docs/features/tags.md`. Closes out US04 Claude tags.

## v0.6.0

- [x] #16 US06 Settings: one config module; backend modules no longer import Streamlit. Merged 2026-11-05. Checked locally; the live Streamlit check was dropped (no live Streamlit, Ava decision). Evidence: `docs/features/backend.md`
- [x] #17 US06 API skeleton: FastAPI with Supabase login check for Ava only. Merged 2026-11-05. Evidence: `docs/features/backend.md`
- [x] #18 US06 Frontend skeleton: Vite React app, Patterns theme, Supabase sign-in gated by `/api/me`. Merged 2026-11-12. Ava signed in (by password via #20, Outlook down). Still to do: sign-ups-off screenshot and a magic-link retest. Evidence: `docs/features/web.md`
- [x] #19 US06 Entry and tag routes: entries CRUD and Suggest tags in the API, with Streamlit's messages; no journal text in errors or logs. Merged 2026-11-12. Evidence: `docs/features/backend.md`
