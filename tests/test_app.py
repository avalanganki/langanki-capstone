from streamlit.testing.v1 import AppTest


def test_app_shows_title_and_sample_nights():
    at = AppTest.from_file("app.py").run()
    assert not at.exception
    assert at.title[0].value == "Patterns"
    table = at.dataframe[0].value
    assert len(table) == 4
    assert list(table.columns) == ["Date", "Sleep score", "Readiness", "HRV (ms)"]
    assert not table.isnull().values.any()
