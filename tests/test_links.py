"""Linking entries to the next night (issue #14). Synthetic 2000-dated rows; no real Oura, Supabase, or Claude."""

from unittest.mock import patch

import pytest

import links
from test_app import FAR_FUTURE, FakeClient


@pytest.mark.parametrize(
    "entry_date, night_date",
    [
        ("2000-01-04", "2000-01-05"),
        ("2000-01-31", "2000-02-01"),
        ("1999-12-31", "2000-01-01"),
        ("2000-02-28", "2000-02-29"),  # 2000 is a leap year
        ("2000-02-29", "2000-03-01"),
    ],
)
def test_next_night_date(entry_date, night_date):
    assert links.next_night_date(entry_date) == night_date


def night(day, sleep=80, readiness=70, hrv=50.0):
    return {"night_date": day, "sleep_score": sleep, "readiness": readiness, "avg_hrv": hrv}


def entry(day, entry_id=None):
    return {"id": entry_id or day, "entry_date": day, "answers": [], "tags": []}


NIGHTS = [night("2000-01-02"), night("2000-01-03", readiness=None), night("2000-01-05")]


def test_statuses_and_order():
    entries = [entry("2000-01-04"), entry("2000-01-01"), entry("2000-01-03"), entry("2000-01-05"), entry("1999-12-30")]
    result = links.link_entries(entries, NIGHTS)
    assert [r["entry"]["entry_date"] for r in result] == [e["entry_date"] for e in entries]  # input order
    assert [(r["night_date"], r["status"]) for r in result] == [
        ("2000-01-05", "linked"),
        ("2000-01-02", "linked"),
        ("2000-01-04", "no_ring_data"),  # inside the fetched range, Oura had nothing
        ("2000-01-06", "not_fetched"),  # after the newest stored night
        ("1999-12-31", "not_fetched"),  # before the oldest stored night
    ]
    assert result[0]["night"] == NIGHTS[2]
    assert result[2]["night"] is None


def test_partial_night_still_linked():
    [result] = links.link_entries([entry("2000-01-02")], NIGHTS)
    assert result["status"] == "linked"
    assert result["night"]["readiness"] is None


def test_no_nights_means_not_fetched():
    result = links.link_entries([entry("2000-01-01"), entry("2000-01-02")], [])
    assert {r["status"] for r in result} == {"not_fetched"}


def test_linked_count_skips_empty_nights():
    empty = {"night_date": "2000-01-03", "sleep_score": None, "readiness": None, "avg_hrv": None}
    result = links.link_entries(
        [entry("2000-01-01"), entry("2000-01-02"), entry("2000-01-04"), entry("2000-01-09")],
        [night("2000-01-02"), empty, night("2000-01-05")],
    )
    assert links.linked_count(result) == 2


def client_with(entries=(), nights=(), connected=True):
    client = FakeClient(rows=[{k: v for k, v in e.items() if k != "id"} for e in entries],
                        connection=dict(FAR_FUTURE) if connected else None)
    client.tables["nights"] = [dict(n) for n in nights]
    return client


def test_load_linked_none_when_not_connected_and_never_reads_samples():
    client = client_with([entry("2000-01-01")], NIGHTS, connected=False)
    with patch("sample_data.load_nights") as samples:
        assert links.load_linked(client) is None
        assert links.link_one(client, client.rows[0]) is None
    samples.assert_not_called()


def test_load_linked_when_connected():
    client = client_with([entry("2000-01-01"), entry("2000-01-04")], NIGHTS)
    with patch("sample_data.load_nights") as samples:
        result = links.load_linked(client)
    samples.assert_not_called()
    assert [(r["entry"]["entry_date"], r["status"]) for r in result] == [
        ("2000-01-04", "linked"),  # list_entries returns newest first
        ("2000-01-01", "linked"),
    ]


def test_link_one_uses_full_stored_range():
    client = client_with([entry("2000-01-03")], NIGHTS)
    assert links.link_one(client, client.rows[0])["status"] == "no_ring_data"
