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

Done by Ava on 2026-11-05: with no key, "Suggest tags" is disabled and the page shows "Tag suggestions are off (no Claude API key)." The key was restored afterwards.

### Check 3: running app with a key

Done by Ava on 2026-11-05 with synthetic answers: "Suggest tags" filled the Tags box (with the "New tags" caption when a tag was new), and Save stored the entry with those tags. Screenshots kept out of the repo.

## Source (issue #12)

Runs on 2026-11-05, Python 3.9.6. All entries in tests are synthetic.

Decided while building:
- `suggested_tags` holds what Claude returned on the last Suggest for that entry. A tag Ava both typed and got suggested shows as suggested.
- The edit form now loads the saved answers and tags into the boxes when Edit is clicked, instead of using widget defaults. That lets Suggest write into the Tags box without a Streamlit warning.
- Cancel after Suggest in edit mode discards the suggestion. Nothing is stored.
- If an older entry's question isn't one of today's fixed questions, Suggest sends nothing and shows "Couldn't suggest tags right now. Type them instead."
- The Tonight Tags box key is now `tonight_tags`; Tonight and edit share one suggest helper (`run_suggest`).

### Check 1: `0005_entry_suggested_tags.sql` applied

Done by Ava on 2026-11-05: `0005_entry_suggested_tags.sql` applied in Supabase, and `entries` now has the `suggested_tags` column.

### Check 2 (AC1 to AC5): tests

`tests/test_entries.py`:
- `test_create_entry_stores_suggested_tags`, `test_update_entry_stores_new_suggestion`
- `test_update_entry_without_suggestion_keeps_stored`
- `test_tag_sources_marks_suggested_and_typed`, `test_tag_sources_old_entry_all_typed` (AC4)

`tests/test_app.py`:
- `test_save_after_suggest_stores_suggested_tags`: Suggest, remove one tag, type one, and save (AC1, AC2).
- `test_save_without_suggest_stores_no_suggestions`
- `test_past_entries_marks_only_suggested_tags` (AC1), `test_old_entry_shows_tags_as_before` (AC4)
- `test_suggest_in_edit_saves_only_on_save_changes` (AC3)
- `test_cancel_after_suggest_in_edit_changes_nothing`
- `test_removed_tag_stays_removed_on_later_edit`: no automatic re-suggest, and the stored suggestion is kept (AC2).
- `test_edit_suggest_disabled_when_not_configured`

`pytest`: 126 passed (13 new). Claude is never called. The running app's `/_stcore/health` returns `ok` and the server log has no errors.

### Check 3: running app

Done by Ava on 2026-11-05 with synthetic answers: Suggest, remove one tag, type one, and save. Past entries shows "(suggested)" only on Claude's tags. Screenshot kept out of the repo.
