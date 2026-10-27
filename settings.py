"""Small persistent app settings (not account data -- just local preferences)."""
import json
from auth import APP_DIR

SETTINGS_FILE = APP_DIR / "settings.json"
DEFAULTS = {"minimize_to_tray": False}


def load() -> dict:
    try:
        data = json.loads(SETTINGS_FILE.read_text())
        return {**DEFAULTS, **data}
    except Exception:
        return dict(DEFAULTS)


def save(settings: dict) -> None:
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps({**DEFAULTS, **settings}))
    except Exception:
        pass
