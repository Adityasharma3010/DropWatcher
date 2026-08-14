# Drop Watcher

A Windows Twitch stream-queue companion with a native embedded Twitch player. It uses OAuth account linking, encrypted local token storage, Twitch Helix stream status checks, local queue timers, and Windows notifications.

## Safety and scope

This app does not create synthetic viewing/watch-minute events, automate Drops claims, or use undocumented Twitch GQL APIs. It plays streams through Twitch's embedded player and opens the official [Drops Inventory](https://www.twitch.tv/drops/inventory) page for claiming. Twitch does not offer a supported viewer API for checking a user's Drops campaign progress, so the **I claimed Drops — next stream** button remains a manual confirmation.

## Setup

1. Install Python 3.11 or newer, then run `py -m pip install -r requirements.txt`.
2. Set the Twitch Developer Console OAuth redirect URL to exactly `http://localhost:3000`.
3. Set your app secret in PowerShell and launch:

   ```powershell
   $env:TWITCH_CLIENT_SECRET = "your-client-secret"
   py main.py
   ```

The provided Twitch client ID is configured in `config.py`; use `TWITCH_CLIENT_ID` to override it. Tokens are encrypted at `%LOCALAPPDATA%\DropWatcher\token.enc`.

## Use

Choose **Link Twitch**, add channel URLs and watch-time limits, then start the queue. Open a channel to watch normally in Twitch. The app checks live/offline state asynchronously and shows queue/timer status without freezing the interface. Once you have confirmed and claimed Drops on Twitch's official Inventory page, choose **I claimed Drops — next stream** to advance the queue.

## Build a Windows app

After Python is correctly installed, run this in the VS Code PowerShell terminal:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build.ps1
```

The standalone app will be created at `dist\Drop Watcher\Drop Watcher.exe`. You can move that entire `Drop Watcher` folder to a permanent place (for example, `C:\Apps\Drop Watcher`) and create a desktop shortcut to the `.exe`. VS Code is not needed to run it.

Do not embed a Twitch client secret in the executable. For the authorization-code exchange, start the app from a shortcut that supplies `TWITCH_CLIENT_SECRET`, or use a backend you control to keep the secret server-side. A PKCE-only Twitch app may not need a client secret, depending on its Twitch configuration.
