"""Link each evening entry to the following night's Oura scores (issue #14, PRD FR-5).

Oura's `day` is the date the night's sleep ended, so the entry dated D goes with the
night dated D + 1. The link is worked out by date each time and never stored.
App code only: nothing here is sent to Claude or any AI model (Oura API agreement Sec. 4(d)).
"""

import datetime

import oura
from entries import list_entries
from nights import VALUE_FIELDS, has_values

LINKED = "linked"
NO_RING_DATA = "no_ring_data"
NOT_FETCHED = "not_fetched"


def next_night_date(entry_date):
    day = datetime.date.fromisoformat(str(entry_date))
    return (day + datetime.timedelta(days=1)).isoformat()


def link_entries(entries, nights):
    """For each entry, in order: {"entry", "night_date", "night", "status"}."""
    by_date = {n["night_date"]: n for n in nights}
    oldest = min(by_date) if by_date else None
    newest = max(by_date) if by_date else None
    links = []
    for entry in entries:
        night_date = next_night_date(entry["entry_date"])
        night = by_date.get(night_date)
        if night is not None:
            status = LINKED
        elif oldest is not None and oldest <= night_date <= newest:
            status = NO_RING_DATA  # a fetch covered this date and Oura had nothing
        else:
            status = NOT_FETCHED
        links.append({"entry": entry, "night_date": night_date, "night": night, "status": status})
    return links


def load_stored_nights(client):
    return (
        client.table(oura.NIGHTS_TABLE)
        .select("night_date, " + ", ".join(VALUE_FIELDS))
        .execute()
        .data
    )


def load_linked(client):
    """Links for every entry, or None when Oura isn't connected. Never uses sample nights."""
    if oura.load_connection(client) is None:
        return None
    return link_entries(list_entries(client), load_stored_nights(client))


def link_one(client, entry):
    """The link for one entry, or None when Oura isn't connected."""
    if oura.load_connection(client) is None:
        return None
    return link_entries([entry], load_stored_nights(client))[0]


def linked_count(links):
    """Linked nights with at least one value: the N in "based on N nights"."""
    return sum(1 for link in links if link["status"] == LINKED and has_values(link["night"]))
