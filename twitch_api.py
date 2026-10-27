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
    def find_game(self, name):
        """Returns {'id', 'name'} for the best-matching game/category, or None."""
        response = requests.get("https://api.twitch.tv/helix/search/categories", headers=self._headers(), params={"query": name, "first": 5}, timeout=15)
        response.raise_for_status()
        rows = response.json().get("data", [])
        if not rows: return None
        exact = next((r for r in rows if r["name"].lower() == name.lower()), None)
        best = exact or rows[0]
        return {"id": best["id"], "name": best["name"]}
    def streams_with_drops(self, game_id, limit=20):
        """Live streams for a game that are tagged as having drops enabled."""
        response = requests.get("https://api.twitch.tv/helix/streams", headers=self._headers(), params={"game_id": game_id, "first": limit}, timeout=15)
        response.raise_for_status()
        results = []
        for row in response.json().get("data", []):
            tags = [t.lower() for t in row.get("tags", [])]
            if any("dropsenabled" in t.replace(" ", "") for t in tags):
                results.append({
                    "login": row.get("user_login"),
                    "display_name": row.get("user_name"),
                    "title": row.get("title"),
                    "viewer_count": row.get("viewer_count", 0),
                })
        return results
