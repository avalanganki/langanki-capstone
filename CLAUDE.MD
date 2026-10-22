# CLAUDE.md

## What this is
Patterns: a nightly reflection app for Oura ring users. Claude asks short, contextual questions about the day, turns the answers into tags, and links them to the next night's Oura scores. The goal is to point to specific lifestyle factors (caffeine, late workouts, stress) that may be affecting sleep, HRV, and readiness, in plain language instead of the Oura app's medical jargon.

## Who uses it
- Ava, a self-described biohacker, is the only user this semester (single user, Oura API v2 via OAuth2).
- Multi-user and other wearables are out of scope.

## Stack
Python, Streamlit, Supabase (database and login), Oura API v2, Claude API. Deployed on Streamlit Community Cloud. This replaces local SQLite from PRD v1.1.

## Conventions
- Requirements live in /docs (concept brief, PRD, architecture). If a request contradicts them, say so. Don't guess.
- Commit messages must say what was decided, not vague.
- Not medical advice or diagnosis. Never claim a factor causes a score change.
- Any correlation shown must include the number of nights it is based on.
- Question tone is brief and neutral, never judgmental.

## Privacy rules (never break)
- Send Claude only daily summary values (sleep score, readiness, average HRV). No raw heart rate series, name, email, or account IDs.
- Never log journal text or health values. Logs hold errors and timestamps only.
- Secrets live in `.env` (gitignored). Oura tokens are never logged or committed.
- No real Oura data or journal entries in the repo, demos, or screenshots. Use the synthetic dataset.
- Oura scopes: `daily`, `heartrate`, and possibly `tag`. Never `email` or `personal`.

## Instructions for Claude

1. Project planning goes on the backlog in `docs/backlog.md`, grouped by user story or feature. New issues and bugs start here.
2. `docs/todo.md` holds items moved from the backlog that we are working on NOW. Finish the todos before starting the next backlog item.
3. We don't write code unless there is a GitHub issue for it.
4. Each todo becomes a GitHub issue, with the issue number tracing back to the item.
5. Every issue is well defined so a programmer of moderate ability can complete it trivially.
6. Every issue has Acceptance Criteria and Definition of Done sections, written for a product manager.
7. Label each issue with its backlog version and story, e.g. v1.10.0, US01.
8. Do not wander off task. If you find a bug, feature, or enhancement idea while working, add it to the backlog and label it.
9. Code each issue on a `dev/<issue-number>-<short-name>` branch. When done, merge to `main`.
10. Test what we write, with unit and integration tests. Mock the Oura and Claude APIs in tests.
11. An issue is not done until tests pass, the server runs, and the app runs without error.
12. When closing a GitHub issue, review `docs/todo.md` and move completed items into `docs/xchangelog.md`.
13. Start the next issue from `main` with a clean working directory.

## Running the stubs

| Folder | Install (once) | Start | Test | Port |
|---|---|---|---|---|
| `/` (app root) | `pip install -r requirements.txt` | `streamlit run app.py` | `pytest` | 8501 |

Gotchas on this machine:
- The Oura redirect URI must match the registered one exactly, including the trailing slash (`http://localhost:8501/callback/`).
- Oura API calls can be denied without an active Oura membership.
- Streamlit Community Cloud apps sleep when idle, so the first load is slow.
- Check `git status` for `.env` and any exports before every push.
