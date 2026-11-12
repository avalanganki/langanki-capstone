"""Patterns API (issues #17, #19). Holds every secret; the browser only ever sends its Supabase access token.

Never log tokens, user IDs, emails, journal text, or health values.
Oura data never goes to Claude or any AI model (Oura API agreement Sec. 4(d)).
"""

from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api import entries_routes, tags_routes
from api.auth import CHECK_FAILED, NOT_ALLOWED, SIGN_IN_REQUIRED, require_user  # noqa: F401

DEV_ORIGINS = ["http://localhost:5173"]  # Vite dev server; the deploy issue adds the live origin

INVALID_REQUEST = "Invalid request."

app = FastAPI(title="Patterns API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(RequestValidationError)
def invalid_request(request, exc):
    # FastAPI's default 422 echoes the request body back, which could include journal text.
    return JSONResponse(status_code=422, content={"detail": INVALID_REQUEST})


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/me")
def me(user_id: str = Depends(require_user)):
    # Never return email or IDs: the frontend only needs to know the sign-in works.
    return {"signed_in": True}


app.include_router(entries_routes.router)
app.include_router(tags_routes.router)
