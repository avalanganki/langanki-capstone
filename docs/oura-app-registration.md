# Oura app registration: values to paste

Where: https://developer.ouraring.com/applications (sign in, then create a new application). Researched 2026-11-03. The form itself is behind sign-in, so field names below come from Oura's docs and integration guides. Match each value to the closest field.

| Field | Value to paste |
|---|---|
| Application name | Patterns |
| Description | Patterns is a personal nightly reflection journal with one user (the developer), built as a university capstone project. Each evening it asks a few short questions about the day and saves the answers as a dated entry with tags. It shows the user's own Oura daily sleep score, readiness, and average HRV next to those entries so she can spot possible patterns, always with the number of nights each pattern is based on. Oura data is only displayed and compared inside the app with ordinary calculations; it is never sent to any AI model. Not medical advice. |
| Website | https://github.com/avalanganki/langanki-capstone |
| Privacy policy URL | https://github.com/avalanganki/langanki-capstone/blob/main/docs/legal/privacy-policy.md |
| Terms of service URL | https://github.com/avalanganki/langanki-capstone/blob/main/docs/legal/terms-of-service.md |
| Redirect URI | `http://localhost:8501/callback/` (trailing slash included; it must match exactly) |
| Scopes | Tick **Daily** only. The form ticks most boxes by default (seen 2026-11-03): untick Email, Personal, Heartrate, Tag, Workout, Session, SpO2, Stress, Heart Health, and Ring Configuration. |
| Logo (if asked) | Any original image. It must not use Oura's name or logo (API agreement Sec. 4(f)). |
| API agreement | Read and accept the Oura API and MCP Agreement (effective June 8, 2026): https://cloud.ouraring.com/legal/api-agreement |

Before submitting:
- Replace `[CONTACT EMAIL]` in both legal documents with a real contact address.
- Add the Streamlit Community Cloud redirect URI (`https://<app>.streamlit.app/callback/`) once the app's URL is final. Redirect URIs can be edited later.
- After approval, put `OURA_CLIENT_ID` and `OURA_CLIENT_SECRET` in `.env` (never in the repo or in chat).

## What we learned

- **AI restriction (affects our design).** Sec. 4(d): "You shall not use, and shall not permit any third party to use, the Oura API to develop, train, fine-tune, evaluate, prompt, or otherwise provide input or data to any AI Model or AI Platform." LLM use of Oura data is only allowed through Oura's MCP Server. Our architecture currently sends summary scores to Claude (FR-2), so that has to change. See the backlog item "Decision: keep Oura data away from Claude".
- **Least data.** Sec. 3(d) asks apps to request only the data they need. `daily` covers daily sleep, readiness, and activity summaries. Confirm on the first real call whether average HRV (from the `sleep` endpoint) is readable with `daily` alone. If it isn't, add the smallest extra scope and update the privacy policy.
- **Deletion.** Delete all of a user's data within 72 hours of a request (Sec. 5(f)). Stop processing at once on opt-out or revocation.
- **Incidents.** Report a data incident to Oura within 24 hours (Sec. 9).
- **Our terms** must disclaim warranties on behalf of third-party providers (Sec. 12(a)(x)). Done in the terms of service.
- **OAuth endpoints.** Authorize: `https://cloud.ouraring.com/oauth/authorize`. Token: `https://api.ouraring.com/oauth/token`. Revoke: `https://api.ouraring.com/oauth/revoke`. Refresh tokens are single-use. Use PKCE (S256) and a random `state`. Every API call needs a non-empty `User-Agent` header or it may get a 403.
- **Access limits.** Personal access tokens were retired in December 2025, so OAuth is the only way in. A third-party source says apps are limited to 10 users before Oura approval (fine for one user). Gen3 and newer rings need an active Oura membership for API access.

Sources: [Oura API and MCP Agreement](https://cloud.ouraring.com/legal/api-agreement), [Oura authentication docs](https://cloud.ouraring.com/docs/authentication), [Terra: Oura API for AI apps](https://tryterra.co/blog/oura-api-ai-apps-access-permissions-commercial-restrictions), [Oura support: The Oura API](https://support.ouraring.com/hc/en-us/articles/4415266939155-The-Oura-API)

## Option considered: Oura's MCP Server (researched 2026-11-03)

Sec. 4(d) of the agreement allows LLM use of Oura data only "solely through the MCP Server." We looked at whether Patterns could use that route. We decided against it for now:

- **No public Oura MCP server found.** The agreement defines the MCP Server as infrastructure "operated by the Company" (Oura), but no Oura docs or connection URL turned up. Every Oura MCP server found online is third-party. Those call the regular Oura API, so they don't count as Oura's MCP Server.
- **No storing.** Sec. 3(m): "you shall not store or cache any data accessed or obtained through the MCP Server" without separate written authorization from Oura. Patterns has to keep weeks of nightly scores to link entries to the next night and count nights per pattern, so MCP-only access can't support the core feature.
- **Supply-chain risk.** In February 2026 a trojanized copy of a community Oura MCP server carrying the StealC infostealer was planted in public MCP registries.

Decision: use the regular Oura API with the `daily` scope. Claude sees only journal answer text. App code links tags to Oura scores and writes any pattern sentences from templates, because a sentence like "sleep score averaged 6 lower on late-caffeine nights" is derived from Oura data. If an AI summary of the patterns is wanted later, ask Oura's developer support in writing for MCP access plus authorization to store data.

Sources: [Oura API and MCP Agreement](https://cloud.ouraring.com/legal/api-agreement), [Straiker: SmartLoader clones Oura Ring MCP](https://www.straiker.ai/blog/smartloader-clones-oura-ring-mcp-to-deploy-supply-chain-attack), [SC World: fake Oura server malware campaign](https://www.scworld.com/brief/hackers-use-fake-oura-server-for-stealc-malware-campaign), [athletedata.health Oura MCP guide (third-party, paid)](https://www.athletedata.health/guides/oura-mcp-server), [mitchhankins01/oura-ring-mcp (community)](https://github.com/mitchhankins01/oura-ring-mcp)
