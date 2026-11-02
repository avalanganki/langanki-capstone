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


def create_entry(client, entry_date, answers, tags):
    # answers is a list of {"question": ..., "answer": ...}
    if all(not a["answer"].strip() for a in answers):
        raise ValueError("Answer at least one question to save.")
    row = {"entry_date": entry_date.isoformat(), "answers": answers, "tags": tags}
    try:
        return client.table("entries").insert(row).execute()
    except APIError as e:
        if e.code == UNIQUE_VIOLATION:
            raise DuplicateEntryError(entry_date) from None
        raise
