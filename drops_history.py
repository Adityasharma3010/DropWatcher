"""Local history log of drops you've earned over time."""
import json
from pathlib import Path
from auth import APP_DIR

HISTORY_FILE = APP_DIR / "drops_history.json"
MAX_ENTRIES = 500


def load() -> list[dict]:
    try:
        return json.loads(HISTORY_FILE.read_text())
    except Exception:
        return []


def append(entries: list[dict]) -> None:
    if not entries:
        return
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        history = load()
        history.extend(entries)
        history = history[-MAX_ENTRIES:]
        HISTORY_FILE.write_text(json.dumps(history))
    except Exception:
        pass
