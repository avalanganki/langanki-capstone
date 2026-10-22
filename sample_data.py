import json
from pathlib import Path

SAMPLE_PATH = Path(__file__).parent / "data" / "sample_nights.json"
FIELDS = ("date", "sleep_score", "readiness", "avg_hrv")


def load_nights(path=SAMPLE_PATH):
    nights = json.loads(Path(path).read_text())  # TODO(W10): real data
    for i, night in enumerate(nights):
        missing = [f for f in FIELDS if f not in night]
        if missing:
            raise ValueError(f"Night {i} is missing: {', '.join(missing)}")
    return nights
