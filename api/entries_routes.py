"""Entry routes for the new UI (issue #19), reusing `entries.py`.

Never log request bodies, answers, or tags. Error messages never include them.
"""

import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

import entries
from api.auth import require_user
from api.storage import database

UNKNOWN_QUESTION = "Unknown question."
NOT_FOUND = "Entry not found."
BLANK = "Answer at least one question to save."
DUPLICATE = "You already have an entry for this date. Edit it in Past entries."

router = APIRouter(prefix="/api", dependencies=[Depends(require_user)])


class Pair(BaseModel):
    question: str
    answer: str


class NewEntry(BaseModel):
    entry_date: datetime.date
    answers: List[Pair]
    tags: List[str] = []
    suggested_tags: List[str] = []


class EntryChanges(BaseModel):
    answers: List[Pair]
    tags: List[str] = []
    suggested_tags: Optional[List[str]] = None  # None keeps the stored suggestion


def normalize_tags(tags):
    """Same cleaning as the Streamlit tags box: lowercase, trimmed, no blanks or repeats."""
    return entries.parse_tags(",".join(tags))


def check_questions(pairs):
    if any(p.question not in entries.QUESTIONS for p in pairs):
        raise HTTPException(status_code=400, detail=UNKNOWN_QUESTION)


def check_not_blank(pairs):
    if all(not p.answer.strip() for p in pairs):
        raise HTTPException(status_code=400, detail=BLANK)


def as_dicts(pairs):
    return [{"question": p.question, "answer": p.answer} for p in pairs]


def to_json(row):
    return {
        "id": row["id"],
        "entry_date": str(row["entry_date"]),
        "answers": row.get("answers") or [],
        "tags": row.get("tags") or [],
        "suggested_tags": row.get("suggested_tags") or [],
        "tag_sources": [{"tag": t, "source": s} for t, s in entries.tag_sources(row)],
    }


def find(client, entry_id):
    row = entries.get_entry(client, entry_id)
    if row is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    return row


@router.get("/questions")
def list_questions():
    return {"questions": list(entries.QUESTIONS)}


@router.get("/entries")
def list_all():
    with database() as client:
        rows = entries.list_entries(client)
    return {"entries": [to_json(r) for r in rows]}


@router.get("/entries/{entry_id}")
def get_one(entry_id: int):
    with database() as client:
        row = find(client, entry_id)
    return to_json(row)


@router.post("/entries", status_code=201)
def create(body: NewEntry):
    check_questions(body.answers)
    check_not_blank(body.answers)
    with database() as client:
        try:
            result = entries.create_entry(
                client,
                body.entry_date,
                as_dicts(body.answers),
                normalize_tags(body.tags),
                normalize_tags(body.suggested_tags),
            )
        except entries.DuplicateEntryError:
            raise HTTPException(status_code=409, detail=DUPLICATE) from None
    return to_json(result.data[0])


@router.put("/entries/{entry_id}")
def update(entry_id: int, body: EntryChanges):
    with database() as client:
        stored = find(client, entry_id)
        stored_questions = [a["question"] for a in stored.get("answers") or []]
        if [p.question for p in body.answers] != stored_questions:
            raise HTTPException(status_code=400, detail=UNKNOWN_QUESTION)
        check_not_blank(body.answers)
        suggested = None if body.suggested_tags is None else normalize_tags(body.suggested_tags)
        entries.update_entry(client, entry_id, as_dicts(body.answers), ",".join(body.tags), suggested)
        row = find(client, entry_id)
    return to_json(row)


@router.delete("/entries/{entry_id}", status_code=204)
def delete(entry_id: int):
    with database() as client:
        find(client, entry_id)
        entries.delete_entry(client, entry_id)
    return Response(status_code=204)
