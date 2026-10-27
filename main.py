import os
import webview
from api import Api
from local_server import start_in_background
import settings
import tray
import window_state

if __name__ == "__main__":
    url = start_in_background()
    api = Api()
    state = window_state.load()
    main_window = webview.create_window(
        "Drop Watcher", url, js_api=api,
        width=state["width"], height=state["height"],
        min_size=(980, 620),
    )
    api.set_window(main_window)
    # Hidden, persistent window used only to read the real Twitch session
    # cookie once you've signed in via the visible login popup. It's never
    # shown -- same WebView2 profile, so it sees the same cookies.
    cookie_window = webview.create_window("", "https://www.twitch.tv/", hidden=True)
    api.set_cookie_window(cookie_window)

    def _remember_size(*_args):
        try:
            window_state.save(main_window.width, main_window.height)
        except Exception:
            pass

    main_window.events.resized += _remember_size

    def _on_minimized():
        # Opt-in (off by default) since redirecting the native minimize
        # button to the tray can occasionally leave the window stuck in a
        # minimized-but-hidden state depending on Windows/WebView2 timing.
        # Read the setting live so toggling it applies without a restart.
        if settings.load().get("minimize_to_tray"):
            main_window.hide()

    main_window.events.minimized += _on_minimized
    # Without this, closing the main window only destroys that one window --
    # the hidden cookie window keeps the whole process (and any playing
    # stream) running invisibly in the background. Force a full exit instead.
    main_window.events.closed += lambda: os._exit(0)

    def _on_loaded():
        tray.start(main_window)

    main_window.events.loaded += _on_loaded
    # WebView2 (Edge) backend -> real DRM/Widevine support, unlike Qt's
    # bundled Chromium, and this now owns the app's one and only GUI thread.
    # private_mode=False keeps cookies persistent across runs -- required so
    # a one-time Twitch login inside the app carries over to the embedded
    # player iframe (which needs you logged in for drop progress to count).
    webview.start(gui="edgechromium", private_mode=False)


