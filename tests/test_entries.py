import datetime
from unittest.mock import MagicMock

import pytest
from postgrest.exceptions import APIError

from entries import (
    QUESTIONS,
    DuplicateEntryError,
    create_entry,
    delete_entry,
    get_entry,
    list_entries,
    parse_tags,
    update_entry,
)

DATE = datetime.date(2026, 1, 5)


def answers(*texts):
    return [{"question": q, "answer": t} for q, t in zip(QUESTIONS, texts)]


@pytest.mark.parametrize(
    "text, expected",
    [
        (" Late Caffeine, stress,,stress ", ["late caffeine", "stress"]),
        ("", []),
        (" , ,", []),
        ("Run, run, RUN, nap", ["run", "nap"]),
    ],
)
def test_parse_tags(text, expected):
    assert parse_tags(text) == expected


def test_create_entry_inserts_row():
    client = MagicMock()
    create_entry(client, DATE, answers("Low", "2pm", ""), ["stress"])
    client.table.assert_called_once_with("entries")
    client.table.return_value.insert.assert_called_once_with(
        {"entry_date": "2026-01-05", "answers": answers("Low", "2pm", ""), "tags": ["stress"]}
    )


def test_create_entry_all_blank_raises():
    client = MagicMock()
    with pytest.raises(ValueError):
        create_entry(client, DATE, answers("", "  ", "\n"), ["stress"])
    client.table.assert_not_called()


def test_create_entry_duplicate_raises():
    client = MagicMock()
    client.table.return_value.insert.return_value.execute.side_effect = APIError(
        {"code": "23505", "message": "duplicate key"}
    )
    with pytest.raises(DuplicateEntryError):
        create_entry(client, DATE, answers("Low", "", ""), [])


def test_create_entry_other_api_error_passes_through():
    client = MagicMock()
    client.table.return_value.insert.return_value.execute.side_effect = APIError(
        {"code": "42P01", "message": "missing table"}
    )
    with pytest.raises(APIError):
        create_entry(client, DATE, answers("Low", "", ""), [])


def test_list_entries_orders_newest_first():
    client = MagicMock()
    rows = [{"id": 2, "entry_date": "2000-01-05"}, {"id": 1, "entry_date": "2000-01-01"}]
    client.table.return_value.select.return_value.order.return_value.execute.return_value.data = rows
    assert list_entries(client) == rows
    client.table.assert_called_once_with("entries")
    client.table.return_value.select.return_value.order.assert_called_once_with(
        "entry_date", desc=True
    )


def _get_chain(client):
    return client.table.return_value.select.return_value.eq.return_value.limit.return_value


def test_get_entry_found():
    client = MagicMock()
    row = {"id": 7, "entry_date": "2000-01-05"}
    _get_chain(client).execute.return_value.data = [row]
    assert get_entry(client, 7) == row
    client.table.return_value.select.return_value.eq.assert_called_once_with("id", 7)


def test_get_entry_not_found():
    client = MagicMock()
    _get_chain(client).execute.return_value.data = []
    assert get_entry(client, 99) is None


def test_update_entry_sends_answers_and_tags_not_date():
    client = MagicMock()
    update_entry(client, 7, answers("Edited", "", ""), " Stress, nap,stress")
    client.table.assert_called_once_with("entries")
    changes = client.table.return_value.update.call_args.args[0]
    assert changes["answers"] == answers("Edited", "", "")
    assert changes["tags"] == ["stress", "nap"]
    assert "updated_at" in changes
    assert "entry_date" not in changes
    client.table.return_value.update.return_value.eq.assert_called_once_with("id", 7)


def test_update_entry_all_blank_raises():
    client = MagicMock()
    with pytest.raises(ValueError):
        update_entry(client, 7, answers("", " ", ""), "stress")
    client.table.assert_not_called()


def test_delete_entry_deletes_by_id_only():
    client = MagicMock()
    delete_entry(client, 7)
    client.table.assert_called_once_with("entries")
    client.table.return_value.delete.assert_called_once_with()
    client.table.return_value.delete.return_value.eq.assert_called_once_with("id", 7)
