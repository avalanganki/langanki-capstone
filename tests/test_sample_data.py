import json

import pytest

from sample_data import FIELDS, load_nights


def test_loads_sample_file():
    nights = load_nights()
    assert 3 <= len(nights) <= 4
    for night in nights:
        for field in FIELDS:
            assert field in night


def test_missing_field_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps([{"date": "2026-01-01", "sleep_score": 80}]))
    with pytest.raises(ValueError, match="readiness, avg_hrv"):
        load_nights(bad)
