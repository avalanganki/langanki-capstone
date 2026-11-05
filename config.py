"""Settings for Supabase, Oura, and Claude (issue #16).

Values come from environment variables, then `.env` (environment variables win).
Streamlit Community Cloud exposes root-level secrets as environment variables, and
Render sets them directly, so no module needs Streamlit to read settings.
Never print or log a value from here.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent / ".env"

_loaded = False  # tests set this to True so the real .env is never read


def _load():
    global _loaded
    if not _loaded:
        load_dotenv(ENV_PATH, override=False)
        _loaded = True


def get(name, default=""):
    _load()
    return (os.environ.get(name) or default).strip()
