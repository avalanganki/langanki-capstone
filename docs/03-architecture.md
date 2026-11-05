**Technical Architecture**

**Scope**
MVP Slice. Items in the Won't column are not shown


**Stack** (updated Nov 5, 2026; see `docs/decisions/frontend_decision.md`)

Choice | Serves | Downsides
React + TypeScript (Vite) | Fr-2 Fr-3 Fr-6 Fr-8 | A second language; more code than Streamlit
FastAPI (Python) | All: holds secrets, reuses the Python modules | One more piece to deploy
Render web service (to confirm) | Live URL for API and frontend | Free tier sleeps when idle, first load is slow
Supabase (database and Auth) | Fr-3 Fr-4 Fr-5, login | Health data and journal text live on third-party server
Oura API | Fr-1 | Requires an active membership
Claude API | Fr-4 | Costs money per call. Sees journal answers, neutral questions, and the tag list only, never Oura data (Oura agreement Sec. 4(d))

**Trace:**

1. Browser: I open the app on my phone and sign in with Supabase Auth. The browser holds only my Supabase session, no secrets
2. Browser -> API: Each request carries my Supabase access token. The API checks it and allows only my account
3. API -> Oura: On Refresh, the API fetches recent sleep score, readiness, and HRV and saves them in Supabase. Oura tokens stay in the API and Supabase
4. API: App code picks tonight's questions from a fixed set, using today's scores. Nothing is sent to Claude in this step
5. Browser -> API: I answer, and optionally tap Suggest tags
6. API -> Claude: Only my answers, the neutral questions, and my tag list (no Oura data, no score lead-ins) go to Claude, which returns tags
7. API -> Supabase: The entry and tags are saved. Each entry links to the next night's scores by date when it's read
8. API -> Browser: I see a confirmation, my past entries, and the next night's scores
9. API: Trends and correlations are computed and worded by app code from templates, each with its number of nights. Claude is not involved
