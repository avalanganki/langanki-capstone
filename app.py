import datetime

import requests
import streamlit as st

import db
import oura
from entries import (
    QUESTIONS,
    DuplicateEntryError,
    create_entry,
    get_entry,
    list_entries,
    delete_entry,
    parse_tags,
    update_entry,
)
from nights import has_values, load_display_nights, show_value

st.title("Patterns")


def handle_oura_callback():
    # Oura sends the browser back to /callback/?code=...&state=... (or ?error=...).
    params = st.query_params
    if "error" in params:
        st.query_params.clear()
        st.warning("Oura connection was cancelled.")
    elif "code" in params and "state" in params:
        code, state = params["code"], params["state"]
        st.query_params.clear()  # don't leave the code in the address bar
        try:
            tokens = oura.finish_sign_in(state, code)
        except oura.OuraAuthError:
            st.warning("Sign-in expired or didn't match. Try Connect again.")
        except requests.RequestException:
            st.warning("Couldn't reach Oura. Try Connect again.")
        else:
            oura.save_connection(db.get_client(), tokens)
            st.success("Connected to Oura.")


def disconnect_oura():
    oura.disconnect(db.get_client())
    st.session_state.oura_flash = "Disconnected from Oura."


def refresh_oura():
    try:
        count = oura.sync_nights(db.get_client())
    except oura.OuraError as err:
        st.session_state.oura_error = str(err)  # plain-language message, no tokens or values
    else:
        st.session_state.oura_flash = f"Updated {count} {'night' if count == 1 else 'nights'} from Oura."


handle_oura_callback()

with st.sidebar:
    st.subheader("Oura")
    if "oura_flash" in st.session_state:
        st.success(st.session_state.pop("oura_flash"))
    if "oura_error" in st.session_state:
        st.warning(st.session_state.pop("oura_error"))
    oura_settings = oura.get_settings()
    if not oura.is_configured(oura_settings):
        st.info("Waiting for Oura app approval. Showing sample data.")
    elif oura.load_connection(db.get_client()):
        st.write("Connected to Oura.")
        st.button("Refresh Oura data", key="oura_refresh", on_click=refresh_oura)
        updated = oura.last_fetched(db.get_client())
        if updated:
            st.caption(f"Last updated {updated:%b} {updated.day}, {updated:%Y %H:%M} UTC")
        st.button("Disconnect", key="oura_disconnect", on_click=disconnect_oura)
    else:
        st.link_button("Connect Oura", oura.start_sign_in(oura_settings))

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

    source, nights = load_display_nights(db.get_client())
    st.caption("From your Oura ring." if source == "oura" else "Sample data. Not real Oura data.")
    # Values are shown as text so a missing one reads "No data", never 0 or blank.
    st.dataframe(
        [
            {
                "Date": n["date"],
                "Sleep score": show_value(n["sleep_score"]),
                "Readiness": show_value(n["readiness"]),
                "HRV (ms)": show_value(n["avg_hrv"]),
            }
            for n in nights
        ],
        hide_index=True,
    )
    counted = sum(1 for n in nights if has_values(n))
    st.caption(f"Based on {counted} {'night' if counted == 1 else 'nights'}.")

def format_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d:%a, %b} {d.day}, {d.year}"


def start_edit(entry_id):
    st.session_state.editing = entry_id


def cancel_edit():
    st.session_state.editing = None


def save_edit(entry):
    answers = [
        {"question": item["question"], "answer": st.session_state[f"edit_answer_{i}"]}
        for i, item in enumerate(entry["answers"])
    ]
    try:
        update_entry(db.get_client(), entry["id"], answers, st.session_state.edit_tags)
    except ValueError:
        st.session_state.edit_error = "Answer at least one question to save."
        return
    st.session_state.editing = None
    st.session_state.flash = f"Updated your entry for {entry['entry_date']}."


def start_delete(entry_id):
    st.session_state.deleting = entry_id


def cancel_delete():
    st.session_state.deleting = None


def confirm_delete(entry):
    delete_entry(db.get_client(), entry["id"])
    st.session_state.deleting = None
    st.session_state.flash = f"Deleted your entry for {entry['entry_date']}."


with past:
    client = db.get_client()
    saved = list_entries(client)
    # Shown before the empty state so "Deleted..." still appears after deleting the last entry.
    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))
    if not saved:
        st.info("No entries yet. Save one from Tonight.")
    else:
        dates = {e["id"]: e["entry_date"] for e in saved}
        chosen = st.selectbox("Entry", list(dates), format_func=lambda i: format_date(dates[i]))
        st.caption(f"{len(saved)} {'entry' if len(saved) == 1 else 'entries'}.")
        entry = get_entry(client, chosen)
        if entry is None:
            st.warning("That entry no longer exists.")
        elif st.session_state.get("editing") == entry["id"]:
            # The date is shown as text, not an input: an entry's date can't change.
            st.write(f"Date: {format_date(entry['entry_date'])}")
            with st.form(f"edit_{entry['id']}", enter_to_submit=False):
                for i, item in enumerate(entry["answers"]):
                    st.text_area(item["question"], value=item["answer"], key=f"edit_answer_{i}")
                st.text_input(
                    "Tags (comma-separated)", value=", ".join(entry["tags"]), key="edit_tags"
                )
                st.form_submit_button(
                    "Save changes", key="save_changes", on_click=save_edit, args=(entry,)
                )
                st.form_submit_button("Cancel", key="cancel_edit", on_click=cancel_edit)
            if "edit_error" in st.session_state:
                st.warning(st.session_state.pop("edit_error"))
        else:
            for item in entry["answers"]:
                st.write(item["question"])
                with st.container(border=True):
                    st.write(item["answer"].strip() or "No answer")
            st.write("Tags: " + (", ".join(entry["tags"]) or "No tags"))
            if st.session_state.get("deleting") == entry["id"]:
                st.warning(f"Delete your entry for {entry['entry_date']}? This can't be undone.")
                st.button("Yes, delete", key="confirm_delete", on_click=confirm_delete, args=(entry,))
                st.button("Cancel", key="cancel_delete", on_click=cancel_delete)
            else:
                st.button("Edit", key="edit", on_click=start_edit, args=(entry["id"],))
                st.button("Delete", key="delete", on_click=start_delete, args=(entry["id"],))
