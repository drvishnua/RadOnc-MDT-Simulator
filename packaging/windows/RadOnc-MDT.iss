; Inno Setup 6 script for a per-user Windows x64 install.
#define MyAppName "RadOnc MDT Simulator"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "RadOnc MDT Simulator"

[Setup]
AppId={{8E9F7631-6DD9-4B96-8D6A-0EBE0E9BC7A2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\RadOncMDT
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist\installer
OutputBaseFilename=RadOnc-MDT-Simulator-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\RadOncMDT.exe
VersionInfoVersion=0.1.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoProductName={#MyAppName}

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Dirs]
Name: "{localappdata}\RadOncMDT\Data"; Flags: uninsneveruninstall
Name: "{localappdata}\RadOncMDT\Logs"; Flags: uninsneveruninstall

[Files]
Source: "..\..\dist\RadOncMDT\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "Start-RadOnc-MDT.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "Start-RadOnc-MDT.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "Stop-RadOnc-MDT.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "Stop-RadOnc-MDT.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\RadOnc MDT Simulator"; Filename: "{app}\Start-RadOnc-MDT.cmd"; WorkingDir: "{app}"
Name: "{group}\Stop RadOnc MDT Simulator"; Filename: "{app}\Stop-RadOnc-MDT.cmd"; WorkingDir: "{app}"
Name: "{autodesktop}\RadOnc MDT Simulator"; Filename: "{app}\Start-RadOnc-MDT.cmd"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\Start-RadOnc-MDT.cmd"; Description: "Launch RadOnc MDT Simulator"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "{app}\Stop-RadOnc-MDT.cmd"; Flags: runhidden waituntilterminated; RunOnceId: "StopInstalledRadOncMdt"
