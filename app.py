import logging
import os

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
log = logging.getLogger(__name__)


@st.cache_resource
def get_client():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


st.title("Patterns: Supabase hello world")

client = get_client()

note = st.text_input("Test note", value="hello world")
if st.button("Save test entry"):
    try:
        client.table("test_entries").insert({"note": note}).execute()
        st.success("Saved.")
    except Exception:
        log.error("Insert into test_entries failed")
        st.error("Could not save the entry.")

st.subheader("Latest entries")
try:
    rows = (
        client.table("test_entries")
        .select("*")
        .order("created_at", desc=True)
        .limit(5)
        .execute()
        .data
    )
    st.dataframe(rows)
except Exception:
    log.error("Select from test_entries failed")
    st.error("Could not load entries.")
