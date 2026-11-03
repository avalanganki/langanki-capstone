# Patterns: Privacy Policy

Effective: November 3, 2026

Patterns is a personal nightly reflection journal built as a university capstone project. It has one user: the developer. It is not a commercial product and is not offered to the public.

## What Patterns collects

- **Oura daily summaries**, with your permission through Oura's OAuth sign-in: daily sleep score, readiness score, and average HRV. Patterns requests only the Oura scopes it needs for these values. It never requests the `email` or `personal` scopes.
- **Your journal entries**: the date, your answers to a few short evening questions, and the tags on each entry.
- **Oura access and refresh tokens**, so Patterns can fetch your daily summaries without asking you to sign in every night.

Patterns does not collect your name, email address, age, gender, height, weight, location, or raw heart-rate series.

## How it is used

- To show your own Oura daily summaries next to your journal entries, and to point out possible patterns between tags and the following night's scores. Every pattern shown includes the number of nights it is based on.
- Patterns does not give medical advice or diagnoses, and it never claims that a factor causes a change in your scores.

## AI processing

- **Oura data is never sent to any AI model or AI platform.** Patterns compares your Oura values with your tags using ordinary calculations inside the app.
- Your typed journal answers may be sent to Anthropic's Claude API to suggest tags. These requests contain only the answer text, with no Oura data, name, email, or account IDs.
- No data from Patterns is used to train, fine-tune, or evaluate any AI model.

## Where it is stored

- Entries, stored Oura daily summaries, and Oura tokens are kept in a Supabase database with row-level security turned on. The app runs on Streamlit Community Cloud.
- Application logs contain only errors and timestamps. They never contain journal text, health values, or tokens.
- Patterns does not sell, rent, or share your data with anyone, and it shows no advertising.

## Your choices and rights

- **Delete entries**: delete any single entry in the app at any time.
- **Delete everything**: ask for all of your data to be deleted, and it will be deleted within 72 hours. This includes entries, stored Oura summaries, and tokens.
- **Disconnect Oura**: revoke Patterns' access at any time from your Oura account settings (or ask for it to be revoked). Patterns then stops fetching data immediately and deletes its stored tokens.
- When you revoke access or ask for deletion, Patterns stops all processing of your Oura data.

## Retention

Data is kept only while the project is active. When the project ends, all Oura data, tokens, and entries are deleted.

## Security

Secrets and tokens are never committed to source control or written to logs. Access to the database requires the project's private keys. If a data incident ever occurs, it will be reported to Oura within 24 hours as Oura's API agreement requires.

## Changes

Any change to this policy will be posted on this page with a new effective date.

## Contact

Questions or deletion requests: [CONTACT EMAIL]

Source code: https://github.com/avalanganki/langanki-capstone
