# Todo

Items moved from `docs/backlog.md` that we are working on now.

## v0.3.0 US03 Connect Oura

- [ ] #10 Verify: real Oura checks. Paused 2026-11-05 by Ava; remaining: HRV with `daily` scope, expired sign-in renewal, empty `oura_connection` after Disconnect, Streamlit Cloud redirect URI. See `docs/features/oura.md`, Real API.

## v0.5.0 US05 Link entries to the next night

- [ ] #14 Link: each entry to the next night's Oura scores. Built on `dev/14-link-nights`; waiting on Ava's check (`git checkout dev/14-link-nights`, refresh http://localhost:8501).

## v0.6.0 US06 New UI

- [ ] #16 Settings: one config module, no Streamlit in backend modules
- [ ] #17 API skeleton: FastAPI with Supabase login check for Ava only
