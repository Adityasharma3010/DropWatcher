import re, requests
from config import TWITCH_CLIENT_ID
class TwitchAPI:
    def __init__(self, auth): self.auth = auth
    @staticmethod
    def channel_login(link): return re.sub(r"[^a-zA-Z0-9_]", "", link.rstrip("/").split("/")[-1]).lower()
    def _headers(self):
        token = self.auth.access_token()
        if not token: raise RuntimeError("Link Twitch first.")
        return {"Client-Id": TWITCH_CLIENT_ID, "Authorization": f"Bearer {token}"}
    def stream(self, link):
        login = self.channel_login(link)
        response = requests.get("https://api.twitch.tv/helix/streams", headers=self._headers(), params={"user_login":login}, timeout=15)
        response.raise_for_status(); rows = response.json().get("data", [])
        return rows[0] if rows else {"user_login":login, "live":False}
