import datetime

import streamlit as st

import db
from entries import QUESTIONS, DuplicateEntryError, create_entry, parse_tags
from sample_data import load_nights

st.title("Patterns")

tonight, past = st.tabs(["Tonight", "Past entries"])

with tonight:
    # Enter in the Tags box would otherwise save a half-finished entry, and a date can't be saved twice.
    with st.form("entry", clear_on_submit=False, enter_to_submit=False):
        entry_date = st.date_input("Date", value=datetime.date.today())
        answers = [{"question": q, "answer": st.text_area(q)} for q in QUESTIONS]
        tags_text = st.text_input("Tags (comma-separated)")
        submitted = st.form_submit_button("Save")

    if submitted:
        try:
            create_entry(db.get_client(), entry_date, answers, parse_tags(tags_text))
            st.success(f"Saved your entry for {entry_date.isoformat()}.")
        except ValueError:
            st.warning("Answer at least one question to save.")
        except DuplicateEntryError:
            st.warning("You already have an entry for this date. Edit it in Past entries.")

    st.caption("Sample data. Not real Oura data.")
    nights = load_nights()
    st.dataframe(
        [
            {
                "Date": n["date"],
                "Sleep score": n["sleep_score"],
                "Readiness": n["readiness"],
                "HRV (ms)": n["avg_hrv"],
            }
            for n in nights
        ],
        hide_index=True,
    )
    st.caption(f"Based on {len(nights)} nights.")

with past:
    st.info("Coming soon")
