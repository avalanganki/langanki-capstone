# Claude tag suggestions (US04, v0.4.0)

Claude sees only each answer, the fixed neutral question it answers, and the list of known tags. It never gets Oura data, scores, score-aware lead-ins, name, email, or IDs (Oura API and MCP Agreement Sec. 4(d)). No real journal text is recorded here; every example is synthetic.

## Suggest (issue #11)

Runs on 2026-11-05, Python 3.9.6, `anthropic` 0.125.0 (the last 0.x; 1.x needs Python 3.10, see backlog), pydantic 2.13.5.

Decided while building:
- The request uses `client.beta.messages.parse`, not `client.messages.parse`, because the server-side refusal fallback (`fallbacks="default"`, beta `server-side-fallback-2026-07-01`) is only on the beta path. The installed SDK accepts it, so it is on.
- `build_prompt` refuses any question not in `entries.QUESTIONS`. Score-aware lead-ins (FR-2) can never reach Claude by accident.
- Answers are sent inside `<question>` and `<answer>` tags, and the system prompt says the journal text is data, not instructions.
- The "New tags" caption stays until the next Suggest, so it is still visible after typing edits.
- Tests patch `tagger.is_configured` to False by default, so they never read the real `ANTHROPIC_API_KEY`.

### Check 1 (AC1 to AC8): tests with a mocked client

`tests/test_tagger.py`:
- `test_request_has_answers_with_questions_and_known_tags`: also checks the model, low effort, structured output, and the fallback.
- `test_request_has_no_oura_data`: no Oura field names and no values from the Oura fixtures (AC7).
- `test_question_not_in_fixed_set_refused_before_call`: a score lead-in is refused before any call.
- `test_blank_answers_make_no_call`, `test_blank_answers_are_left_out_of_request`
- `test_known_tags_seed_first_then_saved_a_to_z`
- `test_normalize` (7 cases), `test_invalid_tags_dropped`
- `test_results_known_first_in_known_order_then_new_deduped` (AC2, AC3)
- `test_api_errors_raise_plain_message_without_answers` (connection, 429, 500, 401), `test_refusal_raises_plain_message`, `test_unparsed_output_raises_plain_message` (AC6)
- `test_tagger_does_not_log` (AC9)

`tests/test_app.py`:
- `test_suggest_fills_tags_and_does_not_save` (AC1)
- `test_suggest_merges_after_typed_tags` (AC4)
- `test_new_tags_caption_only_for_new` (AC3)
- `test_suggest_error_shows_message_and_keeps_typed_tags` (AC6)
- `test_suggest_disabled_when_not_configured` (AC8)
- `test_save_after_suggest_stores_tags`

`pytest`: 113 passed (29 new). Claude is never called.

### Smoke call (real API, synthetic answers)

One real call on 2026-11-05 to confirm the request shape:
- Synthetic answers: "Felt pretty drained after lunch" / "around 3, an iced latte" / "Read for a bit, then twenty minutes in the sauna".
- Result: `low energy`, `caffeine`, `late caffeine`, `reading` (all known), then `sauna` (new).
- "Drained" was merged into `low energy`, and "around 3" became `late caffeine` because the question was sent with it (AC2, AC5's intent).
- `stop_reason` was `end_turn` on `claude-opus-5-5`, with 784 input and 32 output tokens: about $0.004 a night at $4 / $20 per million tokens.

The full accuracy and cost check is #13.

### Check 2: running app with no key

Pending: Ava removes or blanks `ANTHROPIC_API_KEY` in `.env`, restarts the app, and screenshots the disabled "Suggest tags" button and "Tag suggestions are off (no Claude API key)." Then she restores the key.

### Check 3: running app with a key

Pending: Ava types synthetic answers (not real journal text), clicks "Suggest tags", and screenshots the filled Tags box and any "New tags" caption. Then she clicks Save and confirms the entry saved with those tags.
