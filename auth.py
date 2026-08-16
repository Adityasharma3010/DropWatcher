"""OAuth authorization-code login and encrypted local token store."""
from __future__ import annotations
import base64, hashlib, json, os, secrets, threading, time, webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
import requests
from cryptography.fernet import Fernet
from config import SCOPES, TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_REDIRECT_URI

APP_DIR = Path(os.getenv("LOCALAPPDATA", Path.home())) / "DropWatcher"
TOKEN_FILE, KEY_FILE = APP_DIR / "token.enc", APP_DIR / "key.bin"
class AuthError(RuntimeError): pass

class TokenStore:
    def __init__(self):
        APP_DIR.mkdir(parents=True, exist_ok=True)
        if not KEY_FILE.exists(): KEY_FILE.write_bytes(Fernet.generate_key())
        self.fernet = Fernet(KEY_FILE.read_bytes())
    def load(self):
        try: return json.loads(self.fernet.decrypt(TOKEN_FILE.read_bytes())) if TOKEN_FILE.exists() else None
        except Exception: return None
    def save(self, token):
        token["saved_at"] = time.time()
        TOKEN_FILE.write_bytes(self.fernet.encrypt(json.dumps(token).encode()))
    def clear(self): TOKEN_FILE.unlink(missing_ok=True)

class TwitchAuth:
    def __init__(self): self.store = TokenStore(); self.token = self.store.load()
    @property
    def linked(self): return bool(self.token and self.token.get("access_token"))
    def access_token(self):
        if not self.token: return None
        if time.time() >= self.token.get("saved_at", 0) + self.token.get("expires_in", 0) - 60:
            try:
                self.refresh()
            except AuthError:
                # Implicit-grant tokens have no refresh_token, so expiry
                # always lands here -- fail gracefully (require re-linking)
                # instead of raising and crashing every caller.
                self.store.clear(); self.token = None; return None
        return self.token["access_token"] if self.token else None
    def refresh(self):
        if not self.token or not self.token.get("refresh_token"): raise AuthError("Link Twitch again.")
        body = {"client_id": TWITCH_CLIENT_ID, "grant_type": "refresh_token", "refresh_token": self.token["refresh_token"]}
        if TWITCH_CLIENT_SECRET: body["client_secret"] = TWITCH_CLIENT_SECRET
        response = requests.post("https://id.twitch.tv/oauth2/token", data=body, timeout=15)
        if not response.ok:
            self.store.clear(); self.token = None; raise AuthError("Token refresh failed; link Twitch again.")
        self.token = response.json(); self.store.save(self.token)
    def begin_login(self, callback, window=None):
        state = secrets.token_urlsafe(24)
        # Implicit grant: Twitch returns the access token directly in the redirect
        # URL's fragment (#access_token=...). Fragments are never sent to a server
        # by the browser, so this tiny landing page reads it with JS and re-sends
        # it as a normal query string in a second request our local server can see.
        FRAGMENT_FORWARDER = b"""<!doctype html><html><body>
<script>
var h = window.location.hash.substring(1);
if (h) { window.location.replace("/token?" + h); }
else { document.body.innerText = "No token received."; }
</script></body></html>"""
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                path = urlparse(self.path).path
                if path == "/token":
                    result = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
                    self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
                    self.wfile.write(b"<h2>Drop Watcher linked.</h2><p>You may close this tab.</p>")
                    self.server.result = result
                else:
                    self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
                    self.wfile.write(FRAGMENT_FORWARDER)
            def log_message(self, *_): pass
        def login():
            try:
                server = HTTPServer(("localhost", 3000), Handler)
                params = {"client_id": TWITCH_CLIENT_ID, "redirect_uri": TWITCH_REDIRECT_URI, "response_type": "token", "scope": " ".join(SCOPES), "state": state}
                authorize_url = "https://id.twitch.tv/oauth2/authorize?" + urlencode(params)
                if window is not None:
                    # Silent path: navigate the app's own hidden, already
                    # signed-in window. Twitch skips the consent screen for
                    # a repeat authorization, so nothing is ever shown to
                    # the person -- no system browser tab, no popup.
                    window.load_url(authorize_url)
                else:
                    webbrowser.open(authorize_url)
                server.timeout = 180
                while not hasattr(server, "result"): server.handle_request()
                result = server.result
                if window is not None:
                    # Return the hidden window to its resting page so cookie
                    # reads for drop tracking keep working normally.
                    window.load_url("https://www.twitch.tv/")
                if result.get("state") != state or "access_token" not in result:
                    raise AuthError(f"Twitch sign-in was cancelled or returned an error: {result}")
                # Implicit grant tokens don't come with a refresh_token or a real
                # expires_in from a token endpoint response shape; normalize it.
                self.token = {
                    "access_token": result["access_token"],
                    "refresh_token": None,
                    "expires_in": int(result.get("expires_in", 3600)),
                }
                self.store.save(self.token); callback(None)
            except Exception as exc: callback(str(exc))
        threading.Thread(target=login, daemon=True).start()
