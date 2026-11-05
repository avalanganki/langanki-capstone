**Frontend Decision: React frontend + FastAPI backend (replaces Streamlit)**

Date: 2026-11-05. Decided by Ava. Supersedes the interface part of `stack_decision.md`; Supabase stays.

**Context:** The UI lab and the Patterns design (`docs/design/themes.md`, `docs/design/wireframes/prototype.html`) need layouts Streamlit can't do well on a phone: the night-sky header, score rings, tag chips, and the cream Insights cards. `stack_decision.md` named this as what would change the decision: "If Streamlit is too hard to use on my phone after the UI lab."

**Options considered:**
- A) Keep Streamlit and restyle it with custom CSS. Cheapest, but the design's layouts stay limited and fragile.
- B) A separate frontend with a small Python API. Full design control; costs a rebuild before new features. **Chosen.**

**Decision:**
- **Frontend:** React with TypeScript, built with Vite. A phone-first single-page app styled from `themes.md`.
- **Backend:** FastAPI (Python). It reuses the existing modules (`entries.py`, `oura.py`, `tagger.py`, `links.py`, `nights.py`) and holds every secret: the Supabase secret key, the Oura client secret and tokens, and the Claude API key. The browser never sees them.
- **Login:** Supabase Auth. The browser signs in with Supabase and sends the user's access token to the API. The API checks it and allows only Ava's account (single user this semester).
- **Hosting:** one web service that runs FastAPI and also serves the built frontend, so there is one URL. Render's free tier, confirmed by Ava on 2026-11-05. It sleeps when idle, like Streamlit Community Cloud.
- **Oura redirect URI:** the callback moves to the API, at `http://localhost:8000/callback/` locally and `https://<app>/callback/` live. Both must be added to the Oura app registration, exactly, with the trailing slash.
- **Transition:** Streamlit keeps running locally only (no live Streamlit deploy, Ava 2026-11-05) until the new UI matches it (Tonight, Past entries, Oura connect and refresh, Suggest tags). Then `app.py` and the Streamlit dependency are removed in their own issue.

**Rules that don't change:** Oura data, and anything derived from it, never goes to Claude. Claude sees only answers, the neutral questions, and the tag list. Nothing logs journal text or health values. Correlations are computed by app code and always show their night count. Never claim a cause.

**Corrections to the prototype, to carry into the build:**
- **No causal follow-up:** "Sounds like that coffee carried into the evening" implies a cause and is a Claude follow-up, which isn't decided yet (backlog). Leave it out.
- **No screen-time question:** "What time did you stop looking at screens?" was ruled out in `docs/notes.md`.
- **Tag reuse:** tags follow the reuse rule (`low energy`, not `low afternoon energy`).
- **Night counts:** every Insights card states its own night count. Don't share one "9 nights of 23" line across cards.

**Costs and risks:**
- About 1 to 2 weeks of rebuilding before trends (M5, due Dec 11).
- Streamlit AppTest UI tests are replaced by API tests (pytest with FastAPI's test client) and a smaller set of frontend tests.
- A second language (TypeScript) enters the repo.

**What would change my mind:** if the rebuild isn't at Streamlit parity by Nov 19, keep Streamlit for the final demo and restyle it (option A) so trends still ship on time.
