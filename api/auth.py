"""Sign-in check shared by every protected route (issue #17).

Never log tokens, user IDs, or emails.
"""

from fastapi import Header, HTTPException
from supabase_auth.errors import AuthError

import config
import db

SIGN_IN_REQUIRED = "Sign in required."
NOT_ALLOWED = "This account can't use Patterns."
CHECK_FAILED = "Couldn't check sign-in. Try again."


def require_user(authorization: str = Header(default="")):
    """Return the signed-in user's ID if it's Ava's account; otherwise refuse."""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail=SIGN_IN_REQUIRED)
    try:
        response = db.get_client().auth.get_user(token.strip())
    except AuthError:
        raise HTTPException(status_code=401, detail=SIGN_IN_REQUIRED) from None
    except Exception:
        # Supabase unreachable or misconfigured: not the user's fault, so not a 401.
        raise HTTPException(status_code=503, detail=CHECK_FAILED) from None
    user = getattr(response, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail=SIGN_IN_REQUIRED)
    allowed = config.get("ALLOWED_USER_ID")
    if not allowed or str(user.id) != allowed:
        raise HTTPException(status_code=403, detail=NOT_ALLOWED)
    return str(user.id)
