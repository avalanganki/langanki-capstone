"""Nights for the Tonight screen (issue #21), reusing `nights.py`. Read-only.

Oura values go to the browser only, never to Claude or any AI model (Oura API agreement Sec. 4(d)).
Never log health values.
"""

from fastapi import APIRouter, Depends

import nights
import tagger
from api.auth import require_user
from api.storage import database

router = APIRouter(prefix="/api", dependencies=[Depends(require_user)])


@router.get("/nights")
def list_nights():
    with database() as client:
        source, rows = nights.load_display_nights(client)
    shown = [{"date": str(n["date"]), **{f: n.get(f) for f in nights.VALUE_FIELDS}} for n in rows]
    return {"source": source, "nights": shown, "counted": sum(1 for n in shown if nights.has_values(n))}


@router.get("/tags/status")
def tags_status():
    return {"on": tagger.is_configured()}
