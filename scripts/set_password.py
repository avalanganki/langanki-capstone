"""Set the password on Ava's Supabase account without email (issue #20).

Run by hand only: .venv/bin/python scripts/set_password.py
Uses the secret key from .env, so it runs locally, never in the browser.
Prints only "Password set." or a plain error: never the password, email, user ID, or keys.
"""

import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
import db  # noqa: E402

MIN_LENGTH = 12

NO_USER = "ALLOWED_USER_ID is not set in .env."
MISMATCH = "The passwords don't match. Nothing changed."
TOO_SHORT = f"Use at least {MIN_LENGTH} characters. Nothing changed."
FAILED = "Couldn't set the password. Check the Supabase settings and try again."
DONE = "Password set."


def main(ask=getpass.getpass, out=print):
    user_id = config.get("ALLOWED_USER_ID")
    if not user_id:
        out(NO_USER)
        return 1
    first = ask("New password: ")
    second = ask("Same password again: ")
    if first != second:
        out(MISMATCH)
        return 1
    if len(first) < MIN_LENGTH:
        out(TOO_SHORT)
        return 1
    try:
        # email_confirm: an invited user who never opened the email can't sign in with a password.
        db.get_client().auth.admin.update_user_by_id(user_id, {"password": first, "email_confirm": True})
    except Exception:
        out(FAILED)  # the error text could echo settings, so it is never shown
        return 1
    out(DONE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
