import datetime

import streamlit as st

import db
from entries import (
    QUESTIONS,
    DuplicateEntryError,
    create_entry,
    get_entry,
    list_entries,
    parse_tags,
)
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

def format_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d:%a, %b} {d.day}, {d.year}"


with past:
    client = db.get_client()
    saved = list_entries(client)
    if not saved:
        st.info("No entries yet. Save one from Tonight.")
    else:
        dates = {e["id"]: e["entry_date"] for e in saved}
        chosen = st.selectbox("Entry", list(dates), format_func=lambda i: format_date(dates[i]))
        st.caption(f"{len(saved)} {'entry' if len(saved) == 1 else 'entries'}.")
        entry = get_entry(client, chosen)
        if entry is None:
            st.warning("That entry no longer exists.")
        else:
            for item in entry["answers"]:
                st.write(item["question"])
                with st.container(border=True):
                    st.write(item["answer"].strip() or "No answer")
            st.write("Tags: " + (", ".join(entry["tags"]) or "No tags"))
