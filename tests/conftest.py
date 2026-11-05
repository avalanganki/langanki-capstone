import config

# Never load the real .env in tests: every setting a test needs is patched or set explicitly.
config._loaded = True
