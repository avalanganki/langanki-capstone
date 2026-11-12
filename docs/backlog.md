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

- Connect: OAuth sign-in (PKCE, state), callback at `/callback/`, tokens stored in Supabase, disconnect and revoke. Issue #7, done, see `docs/xchangelog.md`.
- Fetch: pull daily sleep score, readiness, and average HRV for a date range into a `nights` table, refreshing tokens as needed. Issue #8, done, see `docs/xchangelog.md`.
- Show: the Tonight tab shows stored Oura nights when connected and sample nights otherwise, labeled, with the night count. Issue #9, done, see `docs/xchangelog.md`.
- Verify: after Oura approves the app, run the real connect, fetch, show, refresh, and disconnect checks; confirm average HRV works with `daily`; add the Streamlit Cloud redirect URI. Issue #10, see `docs/todo.md`.

## v0.4.0

### US04 Claude tags: suggest tags from answers
As Ava, I want Patterns to suggest tags from my written answers, which I check before saving, so tagging is quick and consistent enough to compare against my Oura nights later. Source: PRD FR-4 (and FR-8 for editing).

Decisions (2026-11-05): Ava chose tags before score-aware questions (FR-2). Claude suggests and Ava saves, per the privacy policy ("may be sent to ... suggest tags"). Tags are open, not a fixed list. Ava's idea: Claude gets the known tags (a seed list plus every tag already saved) and must reuse one whenever the meaning matches ("drained" means `low energy`). It creates a new 1 to 3 word tag only when nothing fits, and new tags are flagged so Ava can swap in an existing one. Tags come from every prompt, including energy and wind-down. Claude gets each answer with its neutral question, because "around 3" means nothing without the question, plus the known-tag list. It never gets score-aware lead-ins, Oura data, name, email, or IDs. "Not mentioned" is never tagged as "none" (from the backlog item "Off-topic answers"). Model `claude-opus-5-5` at low effort, in one constant. A privacy line under the form covers PRD 10.2's disclosure.

- Suggest: "Suggest tags" button on Tonight. Claude reuses known tags, new tags are flagged, the output is structured, a privacy caption sits under the form, and errors fall back to typing. Issue #11, done, see `docs/xchangelog.md`.
- Source: store which tags Claude suggested vs. Ava typed, mark them in Past entries, and Suggest on edit. Issue #12, done, see `docs/xchangelog.md`.
- Verify: 12 synthetic nights against real Claude, including variant merging and a question-dependent answer (at least 10 match), cost under one cent a night, and the Streamlit Cloud secret. Issue #13, done, see `docs/xchangelog.md`.

## v0.5.0

### US05 Link entries to the next night
As Ava, I want each evening entry linked to the following night's Oura scores, and the tags from the evening before shown beside each night, so I can see how the night went after the day I described. Trends (FR-6/7) build on this. Source: PRD FR-5.

Decisions (2026-11-05): Oura's `day` is the date sleep ended, so the entry dated D links to the night dated D + 1. The link is worked out by date each time, never stored, so it stays right after a re-fetch, an edit, or a delete. Three honest states when there's no night: "No ring data for this night" (fetched, but Oura had nothing), "Not fetched from Oura yet", and "Connect Oura..." when not connected. Sample nights are never linked to real entries. App code only; nothing goes to Claude.

- Link: a "Next night" line on each past entry, with linked, no-ring-data, not-fetched, and not-connected states, and a linked-night count for trends. Issue #14, done, see `docs/xchangelog.md`.
- Evening before: an "Evening before" tags column beside each night, never on sample nights. Issue #15 closed 2026-11-05 as folded into US06: built in the new UI instead of Streamlit.

## v0.6.0

### US06 New UI: React frontend and FastAPI backend
As Ava, I want Patterns to look and feel like the Patterns design on my phone (night-sky Tonight screen, score rings, tag chips, cream Insights cards), so the nightly check-in is pleasant enough to do every night. Source: `docs/decisions/frontend_decision.md` (Nov 5, 2026), `docs/design/themes.md`, `docs/design/wireframes/prototype.html`.

Decisions (2026-11-05): Ava chose option B, a separate frontend. React + TypeScript (Vite) talks to a FastAPI backend that reuses the Python modules and holds every secret. Login is Supabase Auth, limited to Ava's account. Streamlit stays until the new UI matches it, then is removed. The prototype is corrected for the project rules: no causal follow-up, no screen-time question, the tag reuse rule, and a night count on every card. Fallback: if it isn't at parity by Nov 19, keep Streamlit for the demo. Decided 2026-11-05: Streamlit is no longer deployed live. It runs locally only until the new UI replaces it; the first live URL is the Render deploy.

Planned pieces (each becomes an issue when moved to `docs/todo.md`):
- Settings (issue #16, done, see `docs/xchangelog.md`): one `config.py` reads `.env` and environment variables for the Supabase, Oura, and Claude settings. It replaces the `st.secrets` fallbacks in `db.py`, `oura.py`, and `tagger.py`, so the modules no longer import Streamlit.
- API skeleton (issue #17, done, see `docs/xchangelog.md`): FastAPI app, Supabase access-token check that allows only Ava's account, health route, and pytest with FastAPI's test client.
- API routes: entries (create, list, get, update, delete) and Suggest tags are issue #19 (see `docs/todo.md`); then nights refresh (display is in #21), entry links, and Oura connect, callback, and disconnect.
- Frontend skeleton (issue #18, see `docs/todo.md`; magic-link sign-in chosen by Ava 2026-11-05, sign-ups off; also creates Ava's Supabase Auth user and sets `ALLOWED_USER_ID`): Vite + React + TypeScript, theme tokens from `themes.md` (night and cream palettes, Fraunces and Nunito Sans), Supabase sign-in, an API client, and Vitest.
- Password sign-in (issue #20, see `docs/todo.md`; added by Ava 2026-11-12 because Outlook was down and the magic link couldn't arrive): email and password beside the magic link, sign-ups still off, plus `scripts/set_password.py` to set the password without email.
- Tonight screen (issue #21, see `docs/todo.md`; includes the read-only `GET /api/nights` route, questions one at a time): night-sky header, score rings (sample nights labeled as sample), the three questions, Suggest tags with "New tags" and the privacy line, tag chips, and Save.
- Past entries screen: list, open, edit, delete, "(suggested)" marks, the "Next night" line, and the "Evening before" tags beside each night (absorbs #15 if not built in Streamlit).
- Oura settings: connect, refresh with "Last updated", and disconnect.
- Deploy: one Render web service (confirmed by Ava 2026-11-05) serving the API and the built frontend; secrets in its environment; the new Oura redirect URIs registered.
- Retire Streamlit: remove `app.py`, its AppTest tests, and the dependency once the new UI is at parity; update CLAUDE.md's run table.
- Insights screen: part of trends (FR-6/7), not this story.

## Unscheduled

### Retest magic-link sign-in
Found while closing US06 Frontend skeleton (#18), 2026-11-12. Outlook was down, so Ava signed in by password (#20) and the magic-link email was never received end to end. Its code is covered by tests. Once email works, send a link from http://localhost:5173, open it, and confirm the Tonight header with "Signed in." Record the result in `docs/features/web.md`. Labels: v0.6.0, US06.

### Question generation: don't ask about screen use
Found in `docs/notes.md` (Oct 1, item 3). Ava answers on a screen, so a question like "what time did you stop looking at screens?" doesn't work. The Claude prompt for nightly questions should steer away from screen-time questions. Pick up with the question-generation story (FR-2).

### Drop the `test_entries` hello-world table
Found while planning US02. `supabase/migrations/0001_test_entries.sql` is left over from the Supabase hello-world and the app no longer uses it. Add a migration that drops it once `entries` is live.

### Off-topic answers: "not mentioned" is not "none"
Found testing US02 Create (answering the caffeine question with only food). The entry saves as-is, which is right, but a missing `caffeine` tag would later read as "no caffeine" in trends. When tag extraction (FR-4) and trends (FR-6/7) are built, treat a night with no caffeine tag as unknown, not zero, unless the answer says none. Possibly a short neutral follow-up when an answer doesn't address its question.

### Nights with no ring data
Scheduled as US05 Link, issue #14 (the entry view); excluding these nights from correlations is part of FR-7. Found testing US02 Read. If the ring wasn't worn, Oura has no sleep score for that night. When Oura linking (FR-5) is built, the entry should still open and show "No ring data for this night" instead of blanks or zeros, and that night is left out of any correlation (and out of its night count).

### Tag source: typed vs found in answers
Done in US04 Source, issue #12 (see `docs/xchangelog.md`). Found testing US02 Update. Ava can add tags that aren't in her answers, which is allowed (she knows things she didn't write). Once Claude extracts tags (FR-4), record whether each tag was typed by Ava or found by Claude, so an edit never gets silently overwritten by re-extraction.

### Delete a range of entries (e.g. a week)
Found testing US02 Delete. #6 deletes one entry at a time; there is no bulk delete. FR-11 asks for single-entry and delete-all only. If a range delete is wanted, it needs its own confirm step. Trends and correlations must be computed from whatever entries remain and the "based on N nights" count must drop to match; deleted nights show as gaps, never filled in.

### Journal answers that mention Oura scores
Found with the decision above. If Ava types her readiness or sleep score into an answer, that text would reach Claude. When tag extraction (FR-4) is built, decide whether to strip numbers that look like scores before sending, or just note it in the privacy policy.

### Python 3.10+ for the Anthropic SDK 1.x
Found planning US04. The venv runs Python 3.9.6, so `pip` installs the last 0.x `anthropic` SDK; 1.x needs Python 3.10+. Upgrade the local venv and pin the Streamlit Cloud Python version, then move to `anthropic` 1.x.

### Claude follow-up questions
Found planning US04. PRD section 7 says Claude *may* add a follow-up based only on written answers; the architecture doc gives Claude only tag extraction. Ava to decide whether follow-ups are wanted before FR-2 work.

### Merge old tags saved under different names
Found planning US04. Tag reuse only applies to new suggestions. Entries saved before it (or with typed variants) can hold `tired` and `low energy` as separate tags, which splits trend counts. Add a "merge tag A into B" action that rewrites past entries after a confirm step. Pick up before trends (FR-6/7).

### Score-aware questions: keep the lead-in separate from the question
Found planning US04. When FR-2 adds lead-ins like "Your readiness was low this morning.", store the lead-in apart from the neutral question in each entry's answers. Claude tag suggestions send the neutral question only, and `tagger.build_prompt` refuses any question not in the fixed set.


### Fetch nights older than the 14-day window
Found planning US05. "Refresh Oura data" pulls the last 14 days, so entries from before the first refresh show "Not fetched from Oura yet." Add a one-time backfill (or a refresh range that reaches the oldest entry) so every entry can link. Watch the Oura rate limit.

### Draft a request to Oura about AI use of score data
Found 2026-11-05 (Ava asked whether Claude could see scores). Sec. 4(d) of the Oura API agreement forbids giving Oura API data to AI models, including typed-in copies within this app. If Claude wording of insights is ever wanted, email Oura's API team for written permission first. Also save the exact Sec. 4(d) text in `docs/research/` so the rule rests on its actual wording. No change to the rule until Oura answers in writing.

### API logs must not record query strings
Found building #17. uvicorn's access log writes each request's full path, including the query string. When the Oura callback moves to the API (`/callback/?code=...&state=...`), the authorization code would land in the log. Before that route ships, turn off uvicorn's access log or log only method, path without query, and status. CLAUDE.md: logs hold errors and timestamps only.
