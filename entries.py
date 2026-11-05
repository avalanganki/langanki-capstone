import datetime

from postgrest.exceptions import APIError

QUESTIONS = (
    "How was your energy this afternoon?",
    "When was your last caffeine today?",
    "How did you wind down tonight?",
)

UNIQUE_VIOLATION = "23505"


class DuplicateEntryError(Exception):
    pass


def parse_tags(text):
    tags = []
    for part in text.split(","):
        tag = part.strip().lower()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def create_entry(client, entry_date, answers, tags, suggested_tags=()):
    # answers is a list of {"question": ..., "answer": ...}
    # suggested_tags is what Claude returned on the last "Suggest tags" (#12).
    if all(not a["answer"].strip() for a in answers):
        raise ValueError("Answer at least one question to save.")
    row = {
        "entry_date": entry_date.isoformat(),
        "answers": answers,
        "tags": tags,
        "suggested_tags": list(suggested_tags),
    }
    try:
        return client.table("entries").insert(row).execute()
    except APIError as e:
        if e.code == UNIQUE_VIOLATION:
            raise DuplicateEntryError(entry_date) from None
        raise


def list_entries(client):
    # Newest entry_date first.
    return client.table("entries").select("*").order("entry_date", desc=True).execute().data


def get_entry(client, entry_id):
    rows = client.table("entries").select("*").eq("id", entry_id).limit(1).execute().data
    return rows[0] if rows else None


def update_entry(client, entry_id, answers, tags_text, suggested_tags=None):
    # Changes answers and tags only; entry_date stays as saved.
    # suggested_tags=None keeps the stored value (no new suggestion during this edit).
    if all(not a["answer"].strip() for a in answers):
        raise ValueError("Answer at least one question to save.")
    changes = {
        "answers": answers,
        "tags": parse_tags(tags_text),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    if suggested_tags is not None:
        changes["suggested_tags"] = list(suggested_tags)
    return client.table("entries").update(changes).eq("id", entry_id).execute()


def delete_entry(client, entry_id):
    # Deletes exactly one row, matched by id.
    return client.table("entries").delete().eq("id", entry_id).execute()


def tag_sources(entry):
    """[(tag, "suggested" | "typed")] in saved order. Entries from before #12 read as all typed."""
    suggested = set(entry.get("suggested_tags") or [])
    return [(t, "suggested" if t in suggested else "typed") for t in entry.get("tags") or []]
