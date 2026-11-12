from supabase import create_client

import config


def get_client():
    # Settings come from config (environment variables or .env). Never print them.
    url = config.get("SUPABASE_URL")
    key = config.get("SUPABASE_KEY")
    if not (url and key):
        raise RuntimeError("Supabase settings missing.")
    return create_client(url, key)
