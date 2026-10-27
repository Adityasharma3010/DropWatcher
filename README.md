# 📺 Drop Watcher — Twitch Drops Queue Companion for Windows

A Windows desktop app that manages a queue of Twitch streams while you farm Drops. It plays streams in Twitch's official embedded player, checks whether each channel is live, runs per-stream timers, shows your Drop progress, and sends Windows notifications when something needs your attention.

[![Python](https://img.shields.io/badge/Language-Python%203.11%2B-blue)](#)
[![pywebview](https://img.shields.io/badge/UI-pywebview-green)](#)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)](#)
[![Twitch](https://img.shields.io/badge/API-Twitch%20Helix-9146ff)](#)
[![Status](https://img.shields.io/badge/Status-Active-success)](#)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](#)

---

## ✨ Features

- 🔗 Link your Twitch account with OAuth
- 🔒 Tokens stored encrypted on your machine (Fernet)
- 📋 Stream queue — add channel URLs with a per-stream mode:
  - ⏱️ **Fixed time** — watch for N minutes
  - 🎯 **Until drops earned** — watch until every Drop for that game is earned
- 🟢 Live / offline check for each channel via Twitch Helix (every 20 seconds, without freezing the UI)
- 🎥 Native embedded Twitch player (WebView2)
- 📊 Drop progress panel — minutes watched vs required, earned and claimed state
- 🔔 Windows notifications — stream ended, timer finished, drop earned, all drops earned, queue advanced
- ⏭️ Queue advance on timer end, stream offline, or when you confirm you've claimed Drops
- 📦 Build a standalone `.exe`, plus an Inno Setup installer script

---

## 🛡️ Safety and Scope

- Drop Watcher plays streams through Twitch's **official embedded player**. You watch normally.
- It does **not** create synthetic viewing/watch-minute events and does **not** automate claiming Drops.
- Claiming happens on Twitch's official [Drops Inventory](https://www.twitch.tv/drops/inventory) page. The **I claimed Drops — next stream** button is a manual confirmation.
- Twitch has no supported public API for Drop campaign progress, so the progress panel runs the **same read-only inventory query the Twitch website runs** against Twitch's internal GQL endpoint, using your own Twitch web session cookie from the in-app login. This only reads your own progress. Because that endpoint is undocumented, it can change or stop working at any time.

Use at your own risk and follow Twitch's Terms of Service.

---

## 🏗️ Tech Stack

- Python 3.11+
- [pywebview](https://pywebview.flowrl.com/) with the Edge WebView2 backend
- Bottle — serves the UI from `http://localhost:5010`
- Twitch Helix API — stream status
- `cryptography` (Fernet) — encrypted token storage
- `winotify` — Windows toast notifications
- HTML / CSS / vanilla JavaScript front end
- PyInstaller + Inno Setup — packaging

---

## 📂 Folder Structure

```
📦 DropWatcher
┣ 📂 web/                  # UI (index.html, app.js, style.css)
┣ 📜 main.py               # App entry — creates the windows
┣ 📜 api.py                # Python API exposed to the UI (queue, status, drops)
┣ 📜 auth.py               # OAuth login + encrypted token store
┣ 📜 twitch_api.py         # Helix stream-status calls
┣ 📜 drops_tracker.py      # Drop progress reader
┣ 📜 queue_manager.py      # Queue + timer logic
┣ 📜 local_server.py       # Serves web/ over localhost
┣ 📜 notifications.py      # Windows notifications
┣ 📜 config.py             # Client ID, redirect URI, scopes
┣ 📜 build.ps1             # PyInstaller build script
┣ 📜 setup.iss             # Inno Setup installer script
┗ 📜 requirements.txt
```

---

## ⚙️ Configuration

`config.py` reads these environment variables:

| Variable               | Required | Description                                              |
| ---------------------- | -------- | -------------------------------------------------------- |
| `TWITCH_CLIENT_ID`     | No       | Overrides the built-in client ID                         |
| `TWITCH_CLIENT_SECRET` | No       | Only needed if you switch to a confidential-client setup |

The default login uses Twitch's implicit grant, so no client secret is required.

Redirect URL: set this in your [Twitch Developer Console](https://dev.twitch.tv/console) application to exactly:

```
http://localhost:3000
```

Encrypted token location:

```
%LOCALAPPDATA%\DropWatcher\token.enc
```

⚠️ Never embed a client secret inside the built executable.

---

## 🛠️ Installation & Setup

Requirements: Windows 10/11 with the Edge WebView2 runtime, and Python 3.11 or newer.

Clone repository:

```powershell
git clone https://github.com/Adityasharma3010/DropWatcher.git
cd DropWatcher
```

Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

Run:

```powershell
py main.py
```

---

## 🕹️ Usage

1. Click **Link Twitch** and approve access
2. Click **Sign in to Twitch player** so the embedded player and Drop progress use your Twitch session
3. Add channel URLs, choose **Fixed time** or **Until drops earned**, and set minutes
4. Click **Start queue**
5. Watch the **Drop progress** panel; claim finished Drops from **Drops Inventory**
6. Click **I claimed Drops — next stream** to move on (or let the timer / auto-advance do it)

---

## 📦 Build a Windows App

In a PowerShell terminal:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build.ps1
```

Output:

```
dist\Drop Watcher\Drop Watcher.exe
```

Move the whole `Drop Watcher` folder wherever you like and create a shortcut to the `.exe`.

Optional installer: install [Inno Setup](https://jrsoftware.org/isdl.php), build the app first, then compile `setup.iss`. The installer is written to `installer_output/`.

---

## 🧠 Future Improvements

- Per-channel Drop-campaign selection
- Saved / reusable queues
- Persist the queue between sessions
- Light theme
- Automated tests

---

## 🤝 Contributing

Fork → Create branch → Commit → Pull Request

---

## 📄 License

MIT License

---

## 👨‍💻 Author

Aditya Sharma  
Website: [https://adityasharma.site](https://adityasharma.site)

---

⭐ If you like this project, please give it a star!
