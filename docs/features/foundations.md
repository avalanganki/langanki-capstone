# Foundations: running skeleton (US00, v0.1.0, issue #1)

Evidence for the five checks. All runs on 2026-10-22, Python 3.9.6, Streamlit 1.50.0, pytest 8.4.2.

## Check 1 (AC1): fresh clone starts with no errors

Cloned `dev/1-foundations` into a new folder, created a new virtual environment, then:

```
$ python3 -m venv .venv
$ .venv/bin/pip install -r requirements.txt
install exit: 0          (only a "newer pip available" notice)
$ .venv/bin/streamlit run app.py --server.headless true
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
  For better performance, install the Watchdog module: ...
$ curl localhost:8501/_stcore/health
ok
```

No errors. Two notices, neither an error:
- `NotOpenSSLWarning` from urllib3, because the macOS system Python uses LibreSSL. It comes from the machine's Python, not the app.
- Streamlit suggests installing Watchdog for faster file reloads. It's optional and not added.

## Check 2 (AC2): title and sample nights on screen

Rendered with Streamlit's `AppTest`. Exceptions: none. Title: `Patterns`.

| Date | Sleep score | Readiness | HRV (ms) |
|---|---|---|---|
| 2026-01-05 | 82 | 78 | 54 |
| 2026-01-06 | 71 | 66 | 41 |
| 2026-01-07 | 88 | 85 | 62 |
| 2026-01-08 | 75 | 72 | 48 |

4 rows, all four fields present on every row, none missing. Caption under the table: "Based on 4 nights."

Browser click-through by Ava: [ ] pending

## Check 3 (AC3): one file, marked TODO

Sample file: `data/sample_nights.json`

```
sample_data.py:4:SAMPLE_PATH = Path(__file__).parent / "data" / "sample_nights.json"
sample_data.py:9:    nights = json.loads(Path(path).read_text())  # TODO(W10): real data
```

## Check 4 (AC4): .env ignored, no keys committed

```
$ git check-ignore -v .env
.gitignore:2:.env	.env
$ git grep -n "sk-"
(no output, exit 1)
$ git grep -n "OURA"
(no output, exit 1)
$ git grep -nE "sk-ant-|(OURA|SUPABASE|ANTHROPIC)_[A-Z_]*=[^[:space:]]|eyJ[A-Za-z0-9_-]{10,}"
(no output, exit 1)
```

The same patterns were also searched across every commit in history (`git rev-list --all`): no matches. `.env` has never been committed. The sample data is synthetic (dates in January 2026, invented values).

## Check 5 (AC5): pytest passes

```
$ pytest -v
configfile: pytest.ini
testpaths: tests
collected 3 items
tests/test_app.py::test_app_shows_title_and_sample_nights PASSED         [ 33%]
tests/test_sample_data.py::test_loads_sample_file PASSED                 [ 66%]
tests/test_sample_data.py::test_missing_field_raises PASSED              [100%]
============================== 3 passed in 1.07s ===============================
```

`test_loads_sample_file` is the sample-file test.

Note: the first run failed with `AppTest script run timed out after 3(s)`, because the cold first import of pandas is slower than Streamlit's 3-second default. The test timeout was raised to 30s, and the suite above is the rerun.
