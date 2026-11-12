"""scripts/set_password.py (issue #20). Supabase and getpass are always mocked."""

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "set_password.py"
spec = importlib.util.spec_from_file_location("set_password", SCRIPT)
set_password = importlib.util.module_from_spec(spec)
spec.loader.exec_module(set_password)

AVA = "00000000-0000-4000-8000-00000000a7a0"
PASSWORD = "synthetic-pass-123"


@pytest.fixture(autouse=True)
def allowed(monkeypatch):
    monkeypatch.setenv("ALLOWED_USER_ID", AVA)


@pytest.fixture
def supa():
    client = MagicMock()
    with patch("db.get_client", return_value=client):
        yield client


def run(answers):
    printed = []
    answers = iter(answers)
    code = set_password.main(ask=lambda prompt: next(answers), out=printed.append)
    return code, printed


def assert_nothing_secret(printed):
    text = "\n".join(printed)
    assert PASSWORD not in text
    assert AVA not in text


def test_sets_password_on_allowed_user(supa):
    code, printed = run([PASSWORD, PASSWORD])
    assert code == 0
    assert printed == ["Password set."]
    supa.auth.admin.update_user_by_id.assert_called_once_with(AVA, {"password": PASSWORD, "email_confirm": True})
    assert_nothing_secret(printed)


def test_mismatch_is_refused(supa):
    code, printed = run([PASSWORD, PASSWORD + "x"])
    assert code == 1
    assert printed == ["The passwords don't match. Nothing changed."]
    supa.auth.admin.update_user_by_id.assert_not_called()
    assert_nothing_secret(printed)


def test_short_password_is_refused(supa):
    code, printed = run(["short", "short"])
    assert code == 1
    assert printed == ["Use at least 12 characters. Nothing changed."]
    supa.auth.admin.update_user_by_id.assert_not_called()


def test_blank_allowed_user_is_refused(supa, monkeypatch):
    monkeypatch.setenv("ALLOWED_USER_ID", "")
    code, printed = run([PASSWORD, PASSWORD])
    assert code == 1
    assert printed == ["ALLOWED_USER_ID is not set in .env."]
    supa.auth.admin.update_user_by_id.assert_not_called()


def test_supabase_error_shows_plain_message(supa):
    supa.auth.admin.update_user_by_id.side_effect = RuntimeError(f"bad request for {AVA} with {PASSWORD}")
    code, printed = run([PASSWORD, PASSWORD])
    assert code == 1
    assert printed == ["Couldn't set the password. Check the Supabase settings and try again."]
    assert_nothing_secret(printed)


def test_missing_supabase_settings_shows_plain_message():
    with patch("db.get_client", side_effect=RuntimeError("Supabase settings missing.")):
        code, printed = run([PASSWORD, PASSWORD])
    assert code == 1
    assert printed == ["Couldn't set the password. Check the Supabase settings and try again."]
