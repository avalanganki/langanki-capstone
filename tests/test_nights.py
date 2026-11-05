"""Tonight tab data source (issue #9). Synthetic rows only; Supabase is the in-memory fake."""

from test_app import FAR_FUTURE, FakeClient

import nights
import sample_data


def synthetic_rows(count):
    # Dates in 2000, made-up values. Inserted out of order on purpose.
    days = [f"2000-01-{d:02d}" for d in range(1, count + 1)]
    return [
        {"night_date": d, "sleep_score": 70 + i % 10, "readiness": 60 + i % 20, "avg_hrv": 40 + i, "fetched_at": "2000-02-01T00:00:00+00:00"}
        for i, d in reversed(list(enumerate(days)))
    ]


def client_with(rows=(), connected=True):
    client = FakeClient(connection=dict(FAR_FUTURE) if connected else None)
    client.tables["nights"] = [dict(r) for r in rows]
    return client


def test_not_connected_gives_sample():
    source, shown = nights.load_display_nights(client_with(synthetic_rows(3), connected=False))
    assert source == "sample"
    assert shown == sample_data.load_nights()


def test_connected_without_rows_gives_sample():
    source, shown = nights.load_display_nights(client_with([]))
    assert source == "sample"
    assert shown == sample_data.load_nights()


def test_connected_with_rows_gives_newest_14_oldest_first():
    source, shown = nights.load_display_nights(client_with(synthetic_rows(20)))
    assert source == "oura"
    assert [n["date"] for n in shown] == [f"2000-01-{d:02d}" for d in range(7, 21)]
    assert set(shown[0]) == {"date", "sleep_score", "readiness", "avg_hrv"}


def test_show_value_never_zero_for_missing():
    assert nights.show_value(None) == "No data"
    assert nights.show_value(0) == "0"  # a real zero stays zero
    assert nights.show_value(52.0) == "52"
    assert nights.show_value(48.25) == "48.2"
    assert nights.show_value(81) == "81"


def test_has_values():
    assert not nights.has_values({"date": "2000-01-01", "sleep_score": None, "readiness": None, "avg_hrv": None})
    assert nights.has_values({"date": "2000-01-01", "sleep_score": None, "readiness": 60, "avg_hrv": None})
