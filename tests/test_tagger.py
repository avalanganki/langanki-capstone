"""Claude tag suggestions (issue #11). The Anthropic client is always mocked; Claude is never called."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import anthropic
import httpx
import pytest

import tagger
from entries import QUESTIONS

FIXTURES = Path(__file__).parent / "fixtures"
Q_ENERGY, Q_CAFFEINE, Q_WINDDOWN = QUESTIONS
PAIRS = [
    (Q_ENERGY, "Felt drained after lunch"),
    (Q_CAFFEINE, "around 3"),
    (Q_WINDDOWN, "Read a book, then sauna"),
]
KNOWN = list(tagger.SEED_TAGS) + ["sauna"]


def fake_client(tags=(), stop_reason="end_turn", parsed=True):
    client = MagicMock()
    response = MagicMock(stop_reason=stop_reason)
    response.parsed_output = tagger.TagList(tags=list(tags)) if parsed else None
    client.beta.messages.parse.return_value = response
    return client


def sent(client):
    kwargs = client.beta.messages.parse.call_args.kwargs
    return kwargs, kwargs["system"] + "\n" + kwargs["messages"][0]["content"]


def test_request_has_answers_with_questions_and_known_tags():
    client = fake_client(["low energy"])
    tagger.suggest_tags(PAIRS, KNOWN, client=client)
    kwargs, text = sent(client)
    for question, answer in PAIRS:
        assert f"<question>{question}</question>\n<answer>{answer}</answer>" in text
    for tag in KNOWN:
        assert f"- {tag}" in text
    assert kwargs["model"] == "claude-opus-5-5"
    assert kwargs["output_config"] == {"effort": "low"}
    assert kwargs["output_format"] is tagger.TagList
    assert kwargs["fallbacks"] == "default"
    assert kwargs["betas"] == ["server-side-fallback-2026-07-01"]
    assert len(kwargs["messages"]) == 1


def oura_fixture_values():
    values = set()
    for name in ("daily_sleep", "daily_readiness", "sleep"):
        for item in json.loads((FIXTURES / f"oura_{name}.json").read_text())["data"]:
            for key in ("score", "average_hrv"):
                if item.get(key) is not None:
                    values.add(str(item[key]))
    return values


def test_request_has_no_oura_data():
    client = fake_client(["low energy"])
    tagger.suggest_tags(PAIRS, KNOWN, client=client)
    _, text = sent(client)
    for field in ("sleep_score", "readiness", "avg_hrv", "hrv", "oura"):
        assert field not in text.lower()
    for value in oura_fixture_values():
        assert value not in text


def test_question_not_in_fixed_set_refused_before_call():
    client = fake_client()
    lead_in = "Your readiness was low this morning. " + Q_ENERGY
    with pytest.raises(ValueError):
        tagger.suggest_tags([(lead_in, "tired")], KNOWN, client=client)
    client.beta.messages.parse.assert_not_called()


def test_blank_answers_make_no_call():
    client = fake_client()
    assert tagger.suggest_tags([(q, "  ") for q in QUESTIONS], KNOWN, client=client) == []
    client.beta.messages.parse.assert_not_called()


def test_blank_answers_are_left_out_of_request():
    client = fake_client(["low energy"])
    tagger.suggest_tags([(Q_ENERGY, "tired"), (Q_CAFFEINE, "")], KNOWN, client=client)
    _, text = sent(client)
    assert Q_CAFFEINE not in text


def test_known_tags_seed_first_then_saved_a_to_z():
    client = MagicMock()
    client.table.return_value.select.return_value.execute.return_value.data = [
        {"tags": ["Sauna", "stress"]},
        {"tags": ["  cold   shower ", "alcohol"]},
        {"tags": []},
    ]
    assert tagger.known_tags(client) == list(tagger.SEED_TAGS) + ["cold shower", "sauna"]
    client.table.assert_called_with("entries")


@pytest.mark.parametrize(
    "raw, clean",
    [
        ("Low Energy", "low energy"),
        ("  late   caffeine ", "late caffeine"),
        ("", None),
        ("   ", None),
        ("a" * 31, None),
        ("one two three four", None),
        ("one two three", "one two three"),
    ],
)
def test_normalize(raw, clean):
    assert tagger.normalize(raw) == clean


def test_results_known_first_in_known_order_then_new_deduped():
    client = fake_client(["Sauna", "cold plunge", "late caffeine", "low energy", "LOW ENERGY", "cold plunge"])
    result = tagger.suggest_tags(PAIRS, KNOWN, client=client)
    assert result == [("low energy", False), ("late caffeine", False), ("sauna", False), ("cold plunge", True)]


def test_invalid_tags_dropped():
    client = fake_client(["", "far too many words in this tag", "nap"])
    assert tagger.suggest_tags(PAIRS, KNOWN, client=client) == [("nap", False)]


REQUEST = httpx.Request("POST", "https://api.anthropic.com/v1/messages")


@pytest.mark.parametrize(
    "error",
    [
        anthropic.APIConnectionError(message="down", request=REQUEST),
        anthropic.RateLimitError("busy", response=httpx.Response(429, request=REQUEST), body=None),
        anthropic.InternalServerError("oops", response=httpx.Response(500, request=REQUEST), body=None),
        anthropic.AuthenticationError("bad key", response=httpx.Response(401, request=REQUEST), body=None),
    ],
)
def test_api_errors_raise_plain_message_without_answers(error):
    client = MagicMock()
    client.beta.messages.parse.side_effect = error
    with pytest.raises(tagger.TaggerError) as err:
        tagger.suggest_tags(PAIRS, KNOWN, client=client)
    assert str(err.value) == "Couldn't suggest tags right now. Type them instead."
    assert err.value.__cause__ is None
    for _, answer in PAIRS:
        assert answer not in str(err.value)


def test_refusal_raises_plain_message():
    with pytest.raises(tagger.TaggerError):
        tagger.suggest_tags(PAIRS, KNOWN, client=fake_client(stop_reason="refusal"))


def test_unparsed_output_raises_plain_message():
    with pytest.raises(tagger.TaggerError):
        tagger.suggest_tags(PAIRS, KNOWN, client=fake_client(parsed=False))


def test_is_configured_reads_environment(monkeypatch):
    monkeypatch.setattr(tagger, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    assert tagger.is_configured()
    monkeypatch.setenv("ANTHROPIC_API_KEY", " ")
    monkeypatch.setattr(tagger, "get_api_key", lambda: "")
    assert not tagger.is_configured()


def test_tagger_does_not_log(caplog):
    client = fake_client(["low energy"])
    with caplog.at_level("DEBUG"):
        tagger.suggest_tags(PAIRS, KNOWN, client=client)
    for _, answer in PAIRS:
        assert answer not in caplog.text


# --- Verify cases (issue #13). Checks the synthetic case file only; no Claude call. ---


def test_tag_cases_fixture_is_valid():
    cases = json.loads((FIXTURES / "tag_cases.json").read_text())["cases"]
    assert len(cases) == 12
    used = set()
    for case in cases:
        assert len(case["answers"]) == len(QUESTIONS)
        assert set(case["expect"]) <= set(tagger.SEED_TAGS), case["name"]
        used |= set(case["expect"])
    assert used == set(tagger.SEED_TAGS)  # every seed tag is checked at least once
