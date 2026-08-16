"""Bridge exposed to the web UI via pywebview's js_api. Each public method
here is callable from JavaScript as `window.pywebview.api.<method>(...)`."""
from __future__ import annotations
import threading
import time

import webview
from auth import TwitchAuth
from drops_tracker import DropsTracker
from notifications import notify
from queue_manager import QueueManager
from twitch_api import TwitchAPI


class Api:
    def __init__(self) -> None:
        self.auth = TwitchAuth()
        self.twitch = TwitchAPI(self.auth)
        self.drops = DropsTracker(self.auth)
        self.manager = QueueManager(self.twitch, lambda: None)
        self._manual_channel: str | None = None
        self._earned_ids: set[str] = set()
        self._earned_at: dict[str, float] = {}
        self._last_progress_poll = 0.0
        self._cached_progress: list[dict] = []
        self._auto_advanced_for_index = -1
        self._all_earned_notified_for_index = -1
        self._last_drops_error: str | None = None
        self._main_window = None
        self._cookie_window = None
        self._auto_relink_in_progress = False
        threading.Thread(target=self._auto_relink_loop, daemon=True).start()

    def set_window(self, window) -> None:
        self._main_window = window

    def set_cookie_window(self, window) -> None:
        self._cookie_window = window

    def _auto_relink_loop(self) -> None:
        """Implicit-grant tokens have no refresh_token, so they can't be
        silently refreshed the normal way -- instead, a few minutes before
        expiry, re-run the OAuth flow itself. Twitch skips the consent
        screen on a repeat authorization (as long as you're still logged
        into Twitch in your browser), so this just briefly opens/closes a
        browser tab on its own instead of waiting for you to notice
        "Not linked" and click Link Twitch again mid-session."""
        while True:
            time.sleep(60)
            token = self.auth.token
            if not token or self._auto_relink_in_progress:
                continue
            remaining = token.get("saved_at", 0) + token.get("expires_in", 0) - time.time()
            if remaining < 300:
                self._auto_relink_in_progress = True
                self.auth.begin_login(
                    lambda error: setattr(self, "_auto_relink_in_progress", False),
                    window=self._cookie_window,
                )

    def _get_player_session_token(self) -> str | None:
        """Reads the real 'auth-token' cookie from the shared WebView2
        profile (set by an actual twitch.tv login), which is what lets us
        call Twitch's internal GQL endpoint successfully -- see the note
        in drops_tracker.get_progress()."""
        if not self._cookie_window:
            return None
        try:
            cookies = self._cookie_window.get_cookies()
        except Exception:
            return None
        for cookie in cookies or []:
            for name, morsel in cookie.items():
                if name == "auth-token":
                    return morsel.value
        return None

    # --- auth -----------------------------------------------------------
    def link_twitch(self) -> None:
        done = {"finished": False}

        def callback(error):
            done["finished"] = True

        self.auth.begin_login(callback)
        # Give the browser-based login flow time to complete; get_status()
        # will reflect the real state as soon as the token is saved.
        for _ in range(180):
            if done["finished"]:
                break
            time.sleep(1)

    def unlink_twitch(self) -> None:
        self.auth.store.clear()
        self.auth.token = None

    def open_player_login(self) -> None:
        """Pops a real Twitch login page in a window sharing this app's
        WebView2 profile, so the resulting session cookie is visible to the
        embedded player iframe too (it's a separate profile from your normal
        browser, so drops won't count as watched until you log in here)."""
        webview.create_window("Sign in to Twitch", "https://www.twitch.tv/login", width=480, height=680)

    # --- queue ------------------------------------------------------------
    def add_stream(self, url: str, minutes: int) -> None:
        self.manager.add(url, int(minutes))

    def remove_stream(self, index: int) -> None:
        self.manager.remove(int(index))

    def play_stream(self, index: int) -> None:
        if 0 <= index < len(self.manager.items):
            self._manual_channel = self.twitch.channel_login(self.manager.items[index].link)

    def toggle_queue(self) -> None:
        if self.manager.running:
            self.manager.stop()
        else:
            if not self._get_player_session_token():
                return  # frontend keeps Start disabled until player sign-in; this is a safety net
            self._manual_channel = None
            self._auto_advanced_for_index = -1
            self._all_earned_notified_for_index = -1
            self.manager.start()

    def confirm_drops(self) -> None:
        self.manager.advance()

    def stop_stream(self) -> None:
        """Stop watching the current stream right now and unload the player,
        without waiting for its timer or drop completion. Advances the queue
        if there's a next item, otherwise the queue just stops."""
        self._manual_channel = None
        self.manager.advance()

    def open_inventory(self) -> None:
        self.drops.open_inventory()

    def get_drops_error(self) -> str | None:
        return self._last_drops_error

    def get_drops_progress(self) -> list[dict]:
        """Polled by the frontend periodically. Throttled server-side to
        avoid hammering Twitch's endpoint even if the UI asks more often."""
        now = time.time()
        if now - self._last_progress_poll >= 30 or not self._cached_progress:
            self._last_progress_poll = now
            session_token = self._get_player_session_token()
            campaigns = self.drops.get_progress(session_token=session_token)
            self._last_drops_error = self.drops.last_error
            if self._last_drops_error and not session_token:
                self._last_drops_error = "Sign in to Twitch player first, then wait a few seconds and try again."
            # Use "earned" (watch-minutes requirement met) as the trigger,
            # not Twitch's isClaimed -- some campaigns need a manual claim
            # click on the website even after the requirement is met, so
            # isClaimed can lag or never flip on its own.
            newly_earned_ids = set()
            for campaign in campaigns:
                for drop in campaign["drops"]:
                    if drop["earned"]:
                        newly_earned_ids.add(drop["id"])
            just_earned = newly_earned_ids - self._earned_ids
            for drop_id in just_earned:
                self._earned_at[drop_id] = now
            if self._earned_ids:  # skip notifying on the very first poll
                for campaign in campaigns:
                    for drop in campaign["drops"]:
                        if drop["id"] in just_earned:
                            extra = "" if drop["claimed"] else " (claim it on Twitch if not auto-claimed)"
                            notify("Drop earned!", f"{drop['name']} ({campaign['name']}) is complete.{extra}")
            self._earned_ids = newly_earned_ids

            current_game = None
            if self.manager.running and 0 <= self.manager.active_index < len(self.manager.items):
                try:
                    current_game = self.twitch.stream(self.manager.items[self.manager.active_index].link).get("game_name")
                except Exception:
                    current_game = None
            if current_game:
                campaigns = [c for c in campaigns if c["game"] == current_game]
            else:
                campaigns = []
            for campaign in campaigns:
                for drop in campaign["drops"]:
                    drop["earned_at"] = self._earned_at.get(drop["id"])
            self._cached_progress = campaigns

            # Fire a distinct "all drops earned" notification once per active
            # stream (works in both Fixed time and Until earned modes).
            if (self.manager.running and campaigns
                    and 0 <= self.manager.active_index < len(self.manager.items)
                    and self.manager.active_index != self._all_earned_notified_for_index):
                all_earned = all(d["earned"] for c in campaigns for d in c["drops"])
                if all_earned:
                    self._all_earned_notified_for_index = self.manager.active_index
                    notify("All drops earned", "Every drop for this stream is complete.")

            # Auto-advance a "watch until all drops earned" item (minutes<=0)
            # once every drop in its current-game campaign(s) is earned.
            if (self.manager.running and campaigns
                    and 0 <= self.manager.active_index < len(self.manager.items)
                    and self.manager.items[self.manager.active_index].minutes <= 0
                    and self.manager.active_index != self._auto_advanced_for_index):
                all_earned = all(d["earned"] for c in campaigns for d in c["drops"])
                if all_earned:
                    self._auto_advanced_for_index = self.manager.active_index
                    self.manager.advance()
        return self._cached_progress

    # --- status polled by the frontend every second ----------------------
    def get_status(self) -> dict:
        items = [
            {"login": self.twitch.channel_login(i.link), "minutes": i.minutes}
            for i in self.manager.items
        ]
        remaining = None
        now_channel = None
        queue_channel = None
        no_timer = False
        if self.manager.running and 0 <= self.manager.active_index < len(self.manager.items):
            remaining = max(0, self.manager.active_deadline - time.time())
            active_item = self.manager.items[self.manager.active_index]
            now_channel = self.twitch.channel_login(active_item.link)
            queue_channel = now_channel
            no_timer = active_item.minutes <= 0
        player_channel = self._manual_channel or queue_channel
        return {
            "linked": self.auth.linked,
            "player_signed_in": bool(self._get_player_session_token()),
            "items": items,
            "active_index": self.manager.active_index,
            "running": self.manager.running,
            "remaining": remaining,
            "no_timer": no_timer,
            "now_channel": now_channel,
            "player_channel": player_channel,
        }
