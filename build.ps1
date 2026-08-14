# Builds a standalone Windows application in .\dist\Drop Watcher\Drop Watcher.exe
$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found. Install Python from python.org and select it in VS Code."
}

python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --clean --windowed --name "Drop Watcher" --add-data "web;web" main.py

Write-Host "Built: $PWD\dist\Drop Watcher\Drop Watcher.exe"
