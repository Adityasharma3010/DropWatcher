"""Serves the web/ static assets over plain HTTP on localhost.

Twitch's embedded player requires the page embedding it to be loaded
from a real http(s) origin matching its `parent=` param -- a pywebview
window pointed at a bare file:// path won't satisfy that, so we serve
the UI from http://localhost instead.
"""
from __future__ import annotations
import threading
from pathlib import Path
from bottle import Bottle, static_file

WEB_DIR = Path(__file__).parent / "web"
PORT = 5010

app = Bottle()


@app.route("/")
def index():
    return static_file("index.html", root=str(WEB_DIR))


@app.route("/<filename:path>")
def assets(filename):
    return static_file(filename, root=str(WEB_DIR))


def start_in_background() -> str:
    thread = threading.Thread(
        target=lambda: app.run(host="localhost", port=PORT, quiet=True),
        daemon=True,
    )
    thread.start()
    return f"http://localhost:{PORT}/"
