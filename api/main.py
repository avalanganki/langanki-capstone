"""Patterns API (issue #17). Holds every secret; the browser only ever sends its Supabase access token.

Never log tokens, user IDs, emails, journal text, or health values.
Oura data never goes to Claude or any AI model (Oura API agreement Sec. 4(d)).
"""

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase_auth.errors import AuthError

import config
import db

DEV_ORIGINS = ["http://localhost:5173"]  # Vite dev server; the deploy issue adds the live origin

SIGN_IN_REQUIRED = "Sign in required."
NOT_ALLOWED = "This account can't use Patterns."
CHECK_FAILED = "Couldn't check sign-in. Try again."

app = FastAPI(title="Patterns API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


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


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/me")
def me(user_id: str = Depends(require_user)):
    # Never return email or IDs: the frontend only needs to know the sign-in works.
    return {"signed_in": True}
