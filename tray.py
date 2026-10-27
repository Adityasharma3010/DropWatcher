"""System tray icon: lets the app be minimized out of the taskbar while
still running, with a right-click menu to restore or quit."""
import os
import threading


def _make_icon_image():
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 4, 60, 60), fill=(145, 71, 255, 255))  # Twitch-purple circle
    draw.text((22, 18), "D", fill=(255, 255, 255, 255))
    return img


def start(main_window):
    import pystray

    def on_show(icon, item):
        main_window.restore()
        main_window.show()

    def on_quit(icon, item):
        icon.stop()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("Show Drop Watcher", on_show, default=True),
        pystray.MenuItem("Quit", on_quit),
    )
    icon = pystray.Icon("DropWatcher", _make_icon_image(), "Drop Watcher", menu)
    threading.Thread(target=icon.run, daemon=True).start()
    return icon
