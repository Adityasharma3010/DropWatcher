"""Drops progress. Helix has no supported public Drops campaign/inventory
endpoint, so progress (minutes watched vs required, claimed state) is read
from Twitch's internal GQL API -- the same read-only query the Twitch
website itself runs when you open your Inventory page. This only reads
your own drop progress; it never simulates watch activity."""
import webbrowser
import requests

GQL_URL = "https://gql.twitch.tv/gql"
# Public web client id used by the Twitch website itself for GQL calls.
# Not a secret -- widely known/used by the open-source Twitch tooling
# ecosystem for this exact read-only inventory query.
GQL_CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"

INVENTORY_QUERY = """
query Inventory {
  currentUser {
    inventory {
      dropCampaignsInProgress {
        id
        name
        game { displayName }
        timeBasedDrops {
          id
          name
          requiredMinutesWatched
          self { currentMinutesWatched isClaimed }
        }
      }
    }
  }
}
"""


class DropsTracker:
    def __init__(self, auth=None):
        self.auth = auth
        self.last_error: str | None = None

    def open_inventory(self):
        webbrowser.open("https://www.twitch.tv/drops/inventory")

    def selected_complete(self, selected):
        return False

    def get_progress(self, session_token: str | None = None) -> list[dict]:
        """Returns in-progress drop campaigns with per-drop watch progress.
        Returns [] if not linked or the request fails.

        session_token, if provided, is the real Twitch website session
        cookie (auth-token) rather than our app's own OAuth token. Twitch's
        internal GQL endpoint validates that the token's issuing client_id
        matches the public web client_id used here -- an OAuth token from
        our own registered app fails that check (401 Unauthorized), but the
        real site session cookie passes, since it's the same credential
        the website itself uses for this exact call."""
        self.last_error = None
        token = session_token
        if not token:
            if not self.auth:
                self.last_error = "No auth object."
                return []
            token = self.auth.access_token()
        if not token:
            self.last_error = "Not linked to Twitch."
            return []
        headers = {"Client-Id": GQL_CLIENT_ID, "Authorization": f"OAuth {token}"}
        try:
            response = requests.post(GQL_URL, json={"query": INVENTORY_QUERY}, headers=headers, timeout=15)
            if not response.ok:
                self.last_error = f"GQL request failed ({response.status_code}): {response.text[:300]}"
                return []
            body = response.json()
            if "errors" in body:
                self.last_error = f"GQL errors: {body['errors']}"
                return []
            campaigns = body["data"]["currentUser"]["inventory"]["dropCampaignsInProgress"] or []
        except Exception as exc:
            self.last_error = f"Exception: {exc}"
            return []
        result = []
        for campaign in campaigns:
            drops = []
            for drop in campaign.get("timeBasedDrops", []):
                self_progress = drop.get("self") or {}
                current = self_progress.get("currentMinutesWatched", 0)
                required = drop.get("requiredMinutesWatched", 0)
                drops.append({
                    "id": drop["id"],
                    "name": drop["name"],
                    "required_minutes": required,
                    "current_minutes": current,
                    "earned": required > 0 and current >= required,
                    "claimed": bool(self_progress.get("isClaimed")),
                })
            result.append({
                "id": campaign["id"],
                "name": campaign["name"],
                "game": (campaign.get("game") or {}).get("displayName", ""),
                "drops": drops,
            })
        return result

