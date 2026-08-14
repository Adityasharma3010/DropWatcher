from dataclasses import dataclass
import threading, time
from notifications import notify
@dataclass
class QueueItem:
    link: str
    minutes: int = 60
class QueueManager:
    def __init__(self, api, on_update):
        self.api, self.on_update, self.items = api, on_update, []
        self.active_index, self.active_deadline, self.running, self.auto_advance = -1, 0, False, True
        self._stop, self._advance = threading.Event(), threading.Event()
    def add(self, link, minutes): self.items.append(QueueItem(link, minutes)); self.on_update()
    def remove(self, index):
        if 0 <= index < len(self.items): self.items.pop(index); self.on_update()
    def start(self):
        if self.items and not self.running:
            self.running = True; self._stop.clear(); self._advance.clear(); threading.Thread(target=self._run, daemon=True).start()
    def stop(self): self.running = False; self._stop.set(); self.on_update()
    def advance(self):
        """Advance only after the user has verified/claimed Drops in Twitch."""
        if self.running: self._advance.set()
    def _run(self):
        self.active_index = 0
        while self.running and self.active_index < len(self.items):
            item = self.items[self.active_index]
            # minutes <= 0 means "no fixed timer" -- watch until something
            # else ends it (drops complete via advance(), or stream offline).
            no_timer = item.minutes <= 0
            deadline = time.time() + (10**9 if no_timer else item.minutes * 60)
            self.active_deadline = deadline
            reason = "timer"
            while self.running and time.time() < deadline:
                if self._advance.is_set(): reason = "claimed"; break
                try:
                    if not self.api.stream(item.link).get("id"):
                        reason = "offline"; notify("Stream ended", f"{item.link} is offline."); break
                except Exception: pass
                self.on_update(); self._stop.wait(20)
                if self._stop.is_set(): break
            if not self.running: break
            self._advance.clear()
            if reason == "timer" and not no_timer: notify("Time's up", f"Finished your watch timer for {item.link}.")
            self.active_index += 1; self.on_update()
            if self.active_index < len(self.items):
                message = "Drops confirmed — starting the next stream timer." if reason == "claimed" else "Starting the next stream timer."
                notify("Queue advanced", message)
        if self.running: notify("Queue empty", "There are no more streams in your queue.")
        self.running = False; self.active_index = -1; self.active_deadline = 0; self.on_update()
