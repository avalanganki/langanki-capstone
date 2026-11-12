"""Suggest tags for the new UI (issue #19), reusing `tagger.py`.

Claude sees only the fixed questions, the answers, and the known tags: never Oura data or
anything derived from it (Oura API agreement Sec. 4(d)), and never names, emails, or IDs.
Never log answers, tags, or Claude's response.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import entries
import tagger
from api.auth import require_user
from api.entries_routes import UNKNOWN_QUESTION, Pair
from api.storage import database

TAGS_OFF = "Tag suggestions are off (no Claude API key)."

router = APIRouter(prefix="/api/tags", dependencies=[Depends(require_user)])


class SuggestRequest(BaseModel):
    pairs: List[Pair]


@router.post("/suggest")
def suggest(body: SuggestRequest):
    # Checked before anything else, so an unknown question never reaches Claude.
    if any(p.question not in entries.QUESTIONS for p in body.pairs):
        raise HTTPException(status_code=400, detail=UNKNOWN_QUESTION)
    if not tagger.is_configured():
        raise HTTPException(status_code=503, detail=TAGS_OFF)
    with database() as client:
        known = tagger.known_tags(client)
    pairs = [(p.question, p.answer) for p in body.pairs]
    try:
        found = tagger.suggest_tags(pairs, known)
    except tagger.TaggerError as e:
        raise HTTPException(status_code=503, detail=str(e)) from None
    except ValueError:
        raise HTTPException(status_code=400, detail=UNKNOWN_QUESTION) from None
    return {"tags": [{"tag": t, "is_new": is_new} for t, is_new in found]}
