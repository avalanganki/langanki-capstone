import datetime
from unittest.mock import MagicMock

import pytest
from postgrest.exceptions import APIError

from entries import QUESTIONS, DuplicateEntryError, create_entry, parse_tags

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
