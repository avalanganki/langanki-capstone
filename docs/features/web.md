# Web app (US06, v0.6.0)

The new Patterns UI in `web/`. See `docs/decisions/frontend_decision.md` and `docs/design/themes.md`. No secret values, emails, journal text, or Oura values are recorded here.

## Skeleton (issue #18)

Built on 2026-11-12, Node 26.13.0, Vite 8.3, React 19.3, TypeScript 7.0, Vitest 5.1, supabase-js 2.119.

What it does:
- `npm run dev` serves the app on http://localhost:5173 and forwards `/api` to the FastAPI server on port 8000, so the browser only ever calls its own origin.
- Signed out: the sign-in screen. An email field and "Send sign-in link" call `signInWithOtp` with `shouldCreateUser: false`, then show "Check your email for a sign-in link." A failure shows "Couldn't send the link. Try again." The email is cleared once the link is sent.
- Signed in: the app calls `/api/me`.
  - OK: the night-sky Tonight header with today's date, "Signed in.", and "Sign out".
  - 403: signs out and shows "This account can't use Patterns." on the sign-in screen.
  - Anything else: the API's own message (for example "Couldn't check sign-in. Try again.").
- `src/api.ts` `apiGet(path)` adds `Authorization: Bearer <access token>` from the Supabase session and throws `ApiError` with the API's `detail` on a non-2xx answer. If the API can't be reached, or answers with something that isn't JSON, the message is "Couldn't reach Patterns. Try again."
- `src/theme.css` holds the `themes.md` colours as CSS custom properties (`--night`, `--cocoa`, `--mauve`, `--rose`, `--amber`, `--cream`, `--blush`, `--dim`, `--placeholder`, `--cream-border`, `--bar2`), plus Fraunces and Nunito Sans from Google Fonts.

Decided while building:
- If `web/.env.local` is missing, the app shows "Sign-in isn't set up yet. Add the Supabase settings to web/.env.local." instead of a blank page, because `createClient` throws on an empty URL.
- The "not allowed" message is shown on the sign-in screen after sign-out, so it stays visible once the session is gone.
- Errors on dark use blush text with an amber bar on the left, so amber marks caution without being the text colour.
- The template's lint warnings are fixed: `formatToday` moved to `src/dates.ts`, and the `/api/me` result is stored per access token instead of being reset inside an effect.
- Added `@testing-library/user-event` as a dev dependency to type into and click the form in tests.

### Setup (Ava, once)

1. Supabase, Authentication, then Users: add Ava's user by email. Put its user ID in the root `.env` as `ALLOWED_USER_ID=`.
2. Authentication, then Sign In / Providers: turn off "Allow new users to sign up".
3. Authentication, then URL Configuration: add `http://localhost:5173` to Redirect URLs.
4. Copy `web/.env.example` to `web/.env.local` and fill in `VITE_SUPABASE_URL` and the **publishable** key. The secret key never goes in `web/`.

### Check 1 (AC1, AC2, AC4, AC5): sign in on a phone-sized window

Done by Ava on 2026-11-12: completed the Supabase setup (user added, `ALLOWED_USER_ID` set, `web/.env.local` with the publishable key), signed in on http://localhost:5173, and saw the Tonight header with "Signed in." Outlook was down, so she signed in with a password (issue #20) instead of the magic link. The account check through `/api/me` is the same for both. Ava approved merging on that basis; magic-link delivery is retested once Outlook is back.

Done by Claude on 2026-11-12, without real Supabase: with `npm run dev` and the API running, http://localhost:5173 loads, `/api/health` through the proxy returns `{"status":"ok"}`, and `/api/me` through the proxy returns 401 "Sign in required.". Rendered in a 360px-wide frame, the sign-in screen and the setup message fit with no sideways scroll, and the text on dark is blush. Screenshots reviewed in session, not committed.

### Check 2 (AC3): sign-ups off

Pending: screenshot of the Supabase "Allow new users to sign up" setting turned off (Ava hasn't confirmed this yet). The API already refuses any account but `ALLOWED_USER_ID` (403, issue #17).

### Check 3 (AC6): no secrets committed

`.gitignore` now covers `node_modules/`, `web/dist/`, `.env.local`, and `.env.*.local`. `web/` reads only `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`. `git grep -n "sb_secret_" -- web` returns nothing (exit 1).

### Check 4 (AC7): tests

`npm test` (Vitest, `src/supabase.ts` and `fetch` mocked through `src/test/supabaseMock.ts`):

```
 ✓ src/api.test.ts (7 tests)
 ✓ src/screens/SignIn.test.tsx (5 tests)
 ✓ src/App.test.tsx (5 tests)

 Test Files  3 passed (3)
      Tests  17 passed (17)
```

- `api.test.ts`: sends the Bearer token and returns the JSON; throws `ApiError` with `detail` on 401 and on 403; plain message when the body isn't JSON or the API is unreachable; no `Authorization` header when signed out; never logs the token.
- `SignIn.test.tsx`: sends the OTP with `shouldCreateUser: false` and shows the check-email message (and the email is gone from the page); an error, or a thrown request, shows the retry message; a blank email can't be sent; never logs the email.
- `App.test.tsx`: signed out shows SignIn and calls no API; `/api/me` OK shows "Tonight" and "Signed in."; 403 shows the not-allowed message and signs out; any other error shows the API's message; Sign out returns to the sign-in screen.

`npm run build` and `npm run lint` pass with no errors or warnings. `pytest -q`: 149 passed.

## Password sign-in (issue #20)

Added on 2026-11-12 by Ava's decision: Outlook was down, so the magic-link email couldn't arrive. The magic link stays; a password is added beside it. Sign-ups stay off.

What it does:
- The sign-in screen has a "Use a password instead" button. It swaps to Email, Password, and "Sign in"; "Use a sign-in link instead" swaps back.
- "Sign in" calls `signInWithPassword`, which never creates an account. Once signed in, `App` checks `/api/me` exactly as with the link, so any other account is refused and signed out.
- A wrong email or password shows "Couldn't sign in. Check your email and password." It never says which was wrong and never shows Supabase's own message. The password field is cleared after every attempt.
- `scripts/set_password.py` sets the password on the `ALLOWED_USER_ID` account with the secret key, with no email. It asks twice with hidden input, needs 12 or more characters, and prints only "Password set." or a plain error.

Decided while building:
- The script also marks the account's email as confirmed. Otherwise an invited user who never opened the email can't sign in with a password, which is the exact situation this issue is for.
- The Email field uses `autocomplete="username"` on the password form, so password managers pair it with the password.

### Setup (Ava, once)

In a terminal at the repo root: `.venv/bin/python scripts/set_password.py`. Skip this if the user was created in the dashboard with a password already.

### Check 1 (AC1, AC2): sign in with a password

AC1 done by Ava on 2026-11-12: ran `scripts/set_password.py`, then signed in with her password on http://localhost:5173 and saw the Tonight header with "Signed in."

Pending (AC2): one wrong password, with a screenshot of "Couldn't sign in. Check your email and password." and of the signed-in header, with no email visible.

Done by Claude on 2026-11-12: the running dev server shows "Use a password instead" under the sign-in link form at 360px wide.

### Check 2 (AC3, AC6): tests

`npm test`: 25 passed (8 new).
- `SignIn.test.tsx`: `switches to the password form and back`; `is disabled until both fields are filled`; `signs in with the email and password and never sends a link`; `shows the generic message on error, without Supabase text, and clears the password`; `shows the generic message when the request throws`; `never logs the email or password`. The five magic-link tests from #18 still pass (AC4).
- `App.test.tsx`: `a password sign-in for an account that is not allowed is signed out` (AC3); `a password sign-in for my account shows the Tonight header`.

`pytest -q`: 155 passed on this branch (6 new, in `tests/test_set_password.py`): sets the password on `ALLOWED_USER_ID`; refuses a mismatch, a short password, or a blank `ALLOWED_USER_ID` without calling Supabase; and a Supabase error or missing settings shows the plain message with no password or ID. `npm run build` and `npm run lint` are clean.

### Check 3 (AC5): no secrets

Tests use only synthetic passwords. The script never prints the password, email, ID, or keys.
