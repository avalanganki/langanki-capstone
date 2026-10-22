import streamlit as st

from sample_data import load_nights

st.title("Patterns")
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
