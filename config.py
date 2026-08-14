import os

# The client ID supplied for this project. Override with TWITCH_CLIENT_ID if needed.
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "ufwi7ainb28ne0u1azxlvjcs38i138")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "")
TWITCH_REDIRECT_URI = "http://localhost:3000"
SCOPES = ["user:read:email"]
