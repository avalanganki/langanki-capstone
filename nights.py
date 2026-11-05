"""Nights shown on the Tonight tab: stored Oura nights when connected, sample nights otherwise.

Oura values are displayed to Ava only. Never send them to Claude or any AI model
(Oura API agreement Sec. 4(d)).
"""

import oura
import sample_data

SHOW_NIGHTS = 14
VALUE_FIELDS = ("sleep_score", "readiness", "avg_hrv")


def load_display_nights(client):
    """Return ("oura", nights) or ("sample", nights). Both use keys date, sleep_score, readiness, avg_hrv."""
    if oura.load_connection(client) is not None:
        rows = (
            client.table(oura.NIGHTS_TABLE)
            .select("night_date, sleep_score, readiness, avg_hrv")
            .order("night_date", desc=True)
            .limit(SHOW_NIGHTS)
            .execute()
            .data
        )
        if rows:
            return "oura", [
                {"date": r["night_date"], **{f: r.get(f) for f in VALUE_FIELDS}}
                for r in reversed(rows)
            ]
    return "sample", sample_data.load_nights()


def has_values(night):
    return any(night.get(f) is not None for f in VALUE_FIELDS)


def show_value(value):
    """A missing value reads "No data", never 0 or blank."""
    if value is None:
        return "No data"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(round(value, 1) if isinstance(value, float) else value)
