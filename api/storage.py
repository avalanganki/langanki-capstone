"""Database access for the API routes (issue #19).

Database errors can carry row values (Postgres "Failing row contains ..."), so they are
replaced with a plain message and only the error type is logged, never its text.
"""

import logging
from contextlib import contextmanager

from fastapi import HTTPException

import db

logger = logging.getLogger("patterns.api")

DB_FAILED = "Couldn't reach the database. Try again."


@contextmanager
def database():
    """Yield a Supabase client. Any unexpected error becomes a 503 with no details."""
    try:
        yield db.get_client()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Database call failed: %s", type(e).__name__)
        raise HTTPException(status_code=503, detail=DB_FAILED) from None
