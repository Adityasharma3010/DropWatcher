; Drop Watcher installer script (Inno Setup)
; Requires Inno Setup (free): https://jrsoftware.org/isdl.php
;
; Build the app first with build.ps1 (or `pyinstaller ...`) so
; dist\Drop Watcher\ exists, THEN compile this script.

#define MyAppName "Drop Watcher"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Aditya Sharma"
#define MyAppExeName "Drop Watcher.exe"

[Setup]
AppId={{B6C1E6C0-6E7A-4E1E-9E8C-9D6E6F1C1A11}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=DropWatcher-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Per-user install avoids requiring admin rights; switch to
; "admin" + remove the line below if you want a system-wide install instead.
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
; Pulls in everything build.ps1 produced -- the exe plus its _internal
; folder and the bundled web/ assets.
Source: "dist\Drop Watcher\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
