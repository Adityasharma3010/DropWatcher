import webview
from api import Api
from local_server import start_in_background

if __name__ == "__main__":
    url = start_in_background()
    api = Api()
    main_window = webview.create_window("Drop Watcher", url, js_api=api, width=1280, height=800, min_size=(980, 620))
    api.set_window(main_window)
    # Hidden, persistent window used only to read the real Twitch session
    # cookie once you've signed in via the visible login popup. It's never
    # shown -- same WebView2 profile, so it sees the same cookies.
    cookie_window = webview.create_window("", "https://www.twitch.tv/", hidden=True)
    api.set_cookie_window(cookie_window)
    # WebView2 (Edge) backend -> real DRM/Widevine support, unlike Qt's
    # bundled Chromium, and this now owns the app's one and only GUI thread.
    # private_mode=False keeps cookies persistent across runs -- required so
    # a one-time Twitch login inside the app carries over to the embedded
    # player iframe (which needs you logged in for drop progress to count).
    webview.start(gui="edgechromium", private_mode=False)

