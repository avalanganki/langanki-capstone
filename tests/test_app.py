from streamlit.testing.v1 import AppTest


def test_app_shows_title_and_sample_nights():
    # Default 3s timeout is too short for the first cold import of pandas.
    at = AppTest.from_file("app.py").run(timeout=30)
    assert not at.exception
    assert at.title[0].value == "Patterns"
    table = at.dataframe[0].value
    assert len(table) == 4
    assert list(table.columns) == ["Date", "Sleep score", "Readiness", "HRV (ms)"]
    assert not table.isnull().values.any()
