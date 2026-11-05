"""Settings module (issue #16). Never reads the real .env: conftest.py marks it loaded."""

from pathlib import Path
from unittest.mock import patch

import pytest

import config
import db

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def fresh_env(tmp_path, monkeypatch):
    # A temp .env, loaded for real, then the "never load" flag restored.
    env = tmp_path / ".env"
    monkeypatch.setattr(config, "ENV_PATH", env)
    monkeypatch.setattr(config, "_loaded", False)
    for name in ("PATTERNS_TEST_A", "PATTERNS_TEST_B"):
        monkeypatch.delenv(name, raising=False)
    yield env
    for name in ("PATTERNS_TEST_A", "PATTERNS_TEST_B"):
        monkeypatch.delenv(name, raising=False)


def test_reads_environment_and_strips(monkeypatch):
    monkeypatch.setenv("PATTERNS_TEST_A", "  value  ")
    assert config.get("PATTERNS_TEST_A") == "value"


def test_default_when_missing(monkeypatch):
    monkeypatch.delenv("PATTERNS_TEST_A", raising=False)
    assert config.get("PATTERNS_TEST_A") == ""
    assert config.get("PATTERNS_TEST_A", "fallback") == "fallback"


def test_reads_dotenv_and_environment_wins(fresh_env, monkeypatch):
    fresh_env.write_text("PATTERNS_TEST_A=from-file\nPATTERNS_TEST_B=file-only\n")
    monkeypatch.setenv("PATTERNS_TEST_A", "from-environment")
    assert config.get("PATTERNS_TEST_A") == "from-environment"
    assert config.get("PATTERNS_TEST_B") == "file-only"


def test_dotenv_loaded_once(fresh_env):
    fresh_env.write_text("PATTERNS_TEST_A=one\n")
    with patch("config.load_dotenv", wraps=config.load_dotenv) as load:
        config.get("PATTERNS_TEST_A")
        config.get("PATTERNS_TEST_A")
    assert load.call_count == 1


def test_db_raises_plain_error_without_settings(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_KEY", "")
    with patch("db.create_client") as create:
        with pytest.raises(RuntimeError) as err:
            db.get_client()
    create.assert_not_called()
    assert str(err.value) == "Supabase settings missing."
    assert "example.invalid" not in str(err.value)


def test_db_uses_config_values(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    with patch("db.create_client") as create:
        db.get_client()
    create.assert_called_once_with("https://example.invalid", "test-key")


def test_only_app_imports_streamlit():
    modules = ["config.py", "db.py", "oura.py", "tagger.py", "entries.py", "nights.py", "sample_data.py"]
    for name in modules:
        assert "streamlit" not in (ROOT / name).read_text(), name
