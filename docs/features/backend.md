# Backend for the new UI (US06, v0.6.0)

See `docs/decisions/frontend_decision.md`. No secret values, journal text, or Oura values are recorded here.

## Settings (issue #16)

Runs on 2026-11-05, Python 3.9.6.

What changed:
- `config.get(name, default="")` reads a setting from the environment, loading `.env` once on first use. Environment variables win over `.env`.
- `db.get_client()`, `oura.get_settings()`, and `tagger.get_api_key()` read only through `config.get`. Their `st.secrets` fallbacks are gone.
- `db.get_client()` raises `RuntimeError("Supabase settings missing.")` when the URL or key is blank, instead of falling through to Streamlit.

Decided while building:
- `.env` loads lazily, on the first `config.get`, not at import. `tests/conftest.py` marks it as already loaded, so **tests never read the real `.env`**. Before this, any test run loaded the real keys into the test process, even though tests patched around them.
- Streamlit Community Cloud exposes root-level secrets as environment variables, so the live app needs no change. AC2 confirms this.
- The default Oura redirect stays `http://localhost:8501/callback/` until the API takes over the callback.

### Check 1 (AC3): only `app.py` imports Streamlit

`git grep -n "streamlit" -- db.py oura.py tagger.py entries.py nights.py sample_data.py config.py` returns nothing (exit 1). `links.py` is on `dev/14-link-nights` and has no Streamlit import either. `test_only_app_imports_streamlit` keeps it that way.

### Check 2 (AC4, AC5): tests

`tests/test_config.py`:
- `test_reads_environment_and_strips`, `test_default_when_missing`
- `test_reads_dotenv_and_environment_wins` (a temp `.env`), `test_dotenv_loaded_once`
- `test_db_raises_plain_error_without_settings` (AC4: plain message, no values, no client built), `test_db_uses_config_values`
- `test_only_app_imports_streamlit` (AC3)

Updated: `test_get_settings_reads_environment` (Oura) and `test_is_configured_reads_environment` (Claude) no longer stub `load_dotenv`.

`pytest`: 134 passed (7 new).

With the real `.env`, a one-off check printed only presence: all six settings present, Oura and Claude configured, and the Supabase client built. No values were printed.

### Check 3 (AC1, AC2): click-through

Pending:
- Locally: done by Ava on 2026-11-05. On http://localhost:8501 (`dev/16-config`), past entries, Oura Refresh, and Suggest tags all work as before.
- Live: Streamlit Community Cloud deploys `main`, so the live check runs right after merging. If it breaks, the merge is reverted.
