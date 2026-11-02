import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ENV_PATH = Path(__file__).parent / ".env"


def get_client():
    # Locally the values come from .env; on Streamlit Cloud from st.secrets. Never print them.
    load_dotenv(ENV_PATH)
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not (url and key):
        import streamlit as st

        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)
