"""Remembers the app window's size between launches.

Deliberately does NOT persist X/Y position: a stale or invalid saved
position (e.g. from a monitor that's since been disconnected, or a bad
save mid-resize) can put the window fully off-screen with no way to get
it back, since even the taskbar/tray "show" just re-shows it at that same
unreachable spot. Size alone is safe -- the OS still picks a sane,
on-screen position each launch."""
import json
from pathlib import Path
from auth import APP_DIR

STATE_FILE = APP_DIR / "window_state.json"
DEFAULTS = {"width": 1280, "height": 800}


def load() -> dict:
    try:
        data = json.loads(STATE_FILE.read_text())
        return {**DEFAULTS, "width": data.get("width", DEFAULTS["width"]), "height": data.get("height", DEFAULTS["height"])}
    except Exception:
        return dict(DEFAULTS)


def save(width, height) -> None:
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({"width": width, "height": height}))
    except Exception:
        pass

