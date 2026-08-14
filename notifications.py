def notify(title, message):
    try:
        from winotify import Notification
        Notification(app_id="Drop Watcher", title=title, msg=message).show()
    except Exception: pass
