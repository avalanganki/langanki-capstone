# Todo

Items moved from `docs/backlog.md` that we are working on now.

## v0.3.0 US03 Connect Oura

- [ ] #10 Verify: real Oura checks. Paused 2026-11-05 by Ava; remaining: HRV with `daily` scope, expired sign-in renewal, empty `oura_connection` after Disconnect. The Streamlit Cloud redirect URI is dropped (no live Streamlit, Ava 2026-11-05); the live redirect URI is set in the US06 deploy issue. See `docs/features/oura.md`, Real API.

## v0.5.0 US05 Link entries to the next night

- [ ] #14 Link: each entry to the next night's Oura scores. Built on `dev/14-link-nights`; waiting on Ava's check (`git checkout dev/14-link-nights`, refresh http://localhost:8501).

## v0.6.0 US06 New UI

- [ ] #19 Entry and tag routes: entries CRUD and Suggest tags in the API
- [ ] #20 Password sign-in: email and password beside the magic link
