"""Run tag suggestions against the real Claude API on synthetic cases (issue #13).

Run by hand only: .venv/bin/python scripts/check_tags.py
Uses tests/fixtures/tag_cases.json (synthetic answers) and the seed tags only.
It never reads Supabase, entries, or Oura data. It costs real money (a few cents).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import tagger  # noqa: E402
from entries import QUESTIONS  # noqa: E402

CASES = ROOT / "tests" / "fixtures" / "tag_cases.json"
PRICE_IN, PRICE_OUT = 4.00, 20.00  # claude-opus-5-5, $ per million tokens


class CountingClient:
    """Wraps the real client to add up token usage. Does not record answers or responses."""

    def __init__(self, client):
        self._client = client
        self.calls = self.tokens_in = self.tokens_out = 0
        self.beta = self
        self.messages = self

    def parse(self, **kwargs):
        response = self._client.beta.messages.parse(**kwargs)
        self.calls += 1
        self.tokens_in += response.usage.input_tokens
        self.tokens_out += response.usage.output_tokens
        return response


def matches(case, result):
    known = {t for t, is_new in result if not is_new}
    new = [t for t, is_new in result if is_new]
    return known == set(case["expect"]) and len(new) == (1 if case.get("new") else 0)


def main():
    if not tagger.is_configured():
        sys.exit("No ANTHROPIC_API_KEY in .env.")
    cases = json.loads(CASES.read_text())["cases"]
    client = CountingClient(tagger.get_client())
    known = list(tagger.SEED_TAGS)
    passed = 0
    for case in cases:
        pairs = list(zip(QUESTIONS, case["answers"]))
        try:
            result = tagger.suggest_tags(pairs, known, client=client)
        except tagger.TaggerError as err:
            result, note = [], f" ({err})"
        else:
            note = ""
        ok = matches(case, result)
        passed += ok
        shown = [t + (" (new)" if is_new else "") for t, is_new in result]
        expected = case["expect"] + (["<one new tag>"] if case.get("new") else [])
        print(f"{'PASS' if ok else 'FAIL'}  {case['name']}{note}")
        print(f"      expected: {', '.join(expected) or '(none)'}")
        print(f"      got:      {', '.join(shown) or '(none)'}")
    cost = client.tokens_in * PRICE_IN / 1e6 + client.tokens_out * PRICE_OUT / 1e6
    per_call = cost / client.calls if client.calls else 0
    print(f"\n{passed} of {len(cases)} match. {client.calls} Claude calls, "
          f"{client.tokens_in} input and {client.tokens_out} output tokens, "
          f"about ${cost:.4f} total (${per_call:.4f} per night), model {tagger.MODEL}.")


if __name__ == "__main__":
    main()
