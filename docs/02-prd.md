# Product Requirements Document: Patterns

**Author:** Ava Langanki
**Course:** IST 300, Building Software with Agentic AI
**Date:** September 27, 2026
**Status:** Draft v1

## 1. Overview
Patterns is a nightly reflection app. It uses Claude to ask contextual questions about the user's day, then builds a log that can be compared against Oura ring data (sleep, HRV, resting heart rate, readiness) to find which lifestyle factors affect those scores.

## 2. Problem Statement
Oura has a tagging feature, but it is hard to find and easy to forget. Because logging takes effort, there are gaps in the record, and without a consistent record it is difficult to connect daily behaviors to changes in scores. A short, journal-style conversation at bedtime would make logging easier and more complete.

## 3. Target User
**Primary:** Ava, a self-described biohacker who checks Oura statistics daily to learn which lifestyle factors help or hurt her scores.
**Scope note:** The app is designed for a single user this semester.

## 4. Job to Be Done
When I'm winding down for bed, I want to quickly capture what happened in the context of my sleep and readiness scores, so I can identify correlations between my lifestyle and how I feel the next day.

## 5. Goals
- Make nightly logging fast enough to do every night.
- Use Oura data to guide Claude's questions so they are relevant to that day.
- Build a structured log that can be analyzed alongside Oura metrics.
- Show trends and possible correlations after enough nights have been logged.

## 6. Non-Goals
- Medical advice or diagnosis.
- Replacing the Oura app.
- Supporting multiple users or other wearables.
- Proving that one factor causes another.

## 7. Core User Flow
1. **Evening:** The user opens Patterns. The app pulls the day's Oura data (activity, previous night's sleep, readiness).
2. **Reflection:** Claude asks 3 to 5 contextual questions (e.g., "Your readiness was low this morning. How did your energy feel this afternoon?").
3. **Capture:** The user answers in free text. Claude pulls structured tags from the answers (caffeine, alcohol, workout time, stress, screen time, meal timing).
4. **Next morning:** The app links that night's sleep data to the previous evening's entry.
5. **Over time:** A trends view shows possible relationships between tags and scores.

## 8. Functional Requirements
| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Connect to the Oura API and fetch daily sleep, readiness, HRV, and heart rate data | Must |
| FR-2 | Generate 3 to 5 contextual questions each night using that day's data | Must |
| FR-3 | Accept free-text answers and save each entry with a date | Must |
| FR-4 | Extract structured tags from answers | Must |
| FR-5 | Link each evening entry to the following night's sleep data | Must |
| FR-6 | Show trend charts of scores alongside tags | Should |
| FR-7 | Point out possible correlations once enough data exists | Should |
| FR-8 | Let the user edit or correct extracted tags | Should |
| FR-9 | Nightly reminder | Could |
| FR-10 | Export log to CSV | Could |
| FR-11 | Delete a single entry or all stored data | Should |

## 9. Non-Functional Requirements
- **Speed:** A nightly session takes under 3 minutes.
- **Privacy:** See Section 10.2.
- **Transparency:** Any correlation shown includes the number of nights it is based on.
- **Tone:** Questions are brief and neutral, not judgmental.

## 10. Technical Approach

### 10.1 Stack and Integration
- **Language:** Python
- **Oura data:** Oura API v2 using OAuth2 (authorization code flow with refresh tokens).  
- **App registration:** Self-serve at cloud.ouraring.com. Unapproved apps can connect up to 10 Oura users, so a single-user course project does not need Oura's review.
- **Redirect URI:** A localhost callback (e.g., `http://localhost:8501/callback/`). Must match the registered URI exactly, including the trailing slash.
- **Scopes:** Request only `daily`, `heartrate`, and possibly `tag`. Do not request `email` or `personal`.
- **Requirement:** Active Oura membership, or API calls may be denied.
- **AI:** Claude API for question generation and tag extraction
- **Storage:** SQLite, local only
- **Interface:** Streamlit or a simple web app
- **Build tools:** [TBD]

### 10.2 Data Privacy and Security
Patterns handles two sensitive data types: biometric data from Oura and personal journal text. The approach follows common privacy principles: collect only what is needed, keep it secure, be transparent about where it goes, and let the user delete it.

**Regulatory context:** HIPAA does not apply, since neither Oura nor this app is a healthcare provider or insurer. The FTC Health Breach Notification Rule covers health apps that sync with fitness trackers and counts unauthorized sharing as a breach. A single-user personal project likely falls outside it, but the design follows its intent in case the app is ever shared.

| Area | Practice |
|---|---|
| Data minimization | Send Claude only daily summary values (e.g., sleep score, readiness, average HRV), not raw heart rate time series. No name, email, or account IDs in prompts. |
| Third-party disclosure | Journal text must go to Claude to generate questions and tags. Anthropic does not train on API data without permission and deletes API inputs and outputs within 30 days, unless flagged for a usage policy violation. The app states this on first launch. |
| Storage | SQLite database stored locally, protected by device encryption (FileVault). Optional: database-level encryption. |
| Secrets | Oura client secret and Claude API key stored in a `.env` file listed in `.gitignore`. Oura access and refresh tokens stored locally, never logged or committed. |
| Logging | Application logs record errors and timestamps only, never journal text or health values. |
| Repository hygiene | The database, `.env`, and any exports are excluded from Git. No real personal data in the repo. |
| Demos and screenshots | Class demos use a synthetic dataset, not real Oura data or journal entries. |
| Retention and deletion | The user can delete individual entries or all data (FR-11). Revoking the Oura connection removes stored tokens. |
| Policies | A short `PRIVACY.md` and `TERMS.md` in the repo, linked in the Oura app registration, describing the above. |

## 11. Success Metrics
- **Consistency:** Entries logged on at least 80% of nights over a 30-day test.
- **Speed:** Median session under 3 minutes.
- **Question quality:** User rates questions as relevant at least 70% of the time (simple thumbs up/down).
- **Insight:** At least one correlation surfaces that the user did not already suspect.

## 12. Biggest Unknowns
1. **Filtering:** How much Oura data and past journal history should be sent to Claude each night? Too little and the questions are generic; too much and they lose focus, cost more, and expose more personal data.
2. **Question value:** Do Claude's questions actually help identify correlations, or do they just add friction compared to fixed tags?

**Proposed test:** Run two weeks with fixed questions and two weeks with contextual questions, then compare completion rate, session length, and how useful the tags are.

## 13. Risks
- **Small sample:** One user with 30 to 60 nights can show patterns, but not reliable conclusions.
- **Confounding factors:** Many factors change at once (e.g., a stressful exam day often also means caffeine and late screen time).
- **API changes:** Oura authentication or rate limits could block progress.
- **Timing mismatch:** Entries are logged before the sleep data exists, so linking the two must be handled carefully.
- **Data exposure:** An accidental commit of the database or `.env` would expose health data or keys. Mitigated by `.gitignore` and a check before each push.

## 14. Milestones
| Milestone | Deliverable | Target Date |
|---|---|---|
| M1 | PRD finalized, Oura app registered, privacy docs written | [TBD] |
| M2 | Data pipeline and storage working | [TBD] |
| M3 | Nightly reflection flow with Claude | [TBD] |
| M4 | Tag extraction and entry linking | [TBD] |
| M5 | Trends view and final demo | Dec. 11 |


## Sources
- Oura API authentication: https://cloud.ouraring.com/docs/authentication
- Oura PAT deprecation and 10-user limit: https://www.aifitnessapi.com/integrate/oura-api
- Anthropic API data retention: https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data
- Anthropic training policy: https://platform.claude.com/docs/en/manage-claude/api-and-data-retention
- FTC Health Breach Notification Rule: https://www.ftc.gov/business-guidance/resources/complying-ftcs-health-breach-notification-rule-0