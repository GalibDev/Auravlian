#define AppVersion "0.8.0"
[Setup]
AppId={{7C160C8E-0EC3-4F53-AB24-605BAF10BBA2}
AppName=Auravlian
AppVersion={#AppVersion}
AppPublisher=GalibDev
AppPublisherURL=https://github.com/GalibDev/Auravlian
DefaultDirName={localappdata}\Programs\Auravlian
DefaultGroupName=Auravlian
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist
OutputBaseFilename=Auravlian-Setup-{#AppVersion}
SetupIconFile=..\assets\logo\auravlian.ico
UninstallDisplayIcon={app}\Auravlian.exe
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
[Files]
Source: "..\dist\Auravlian\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Auravlian"; Filename: "{app}\Auravlian.exe"
Name: "{autodesktop}\Auravlian"; Filename: "{app}\Auravlian.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\Auravlian.exe"; Description: "Launch Auravlian"; Flags: nowait postinstall skipifsilent

