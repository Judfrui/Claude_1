; Installateur Windows de Corbu (Inno Setup 6).
; Compilé par .github/workflows/windows.yml après le build PyInstaller :
;   iscc /DVersion=0.1.0 packaging\corbu.iss

#ifndef Version
  #define Version "0.0.0"
#endif

[Setup]
AppId={{0A814240-AED9-43E0-93FB-35D9790E08AB}
AppName=Corbu
AppVersion={#Version}
AppPublisher=Les contributeurs de Corbu
DefaultDirName={autopf}\Corbu
DefaultGroupName=Corbu
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=Corbu-{#Version}-installation
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LicenseFile=..\LICENSE
UninstallDisplayIcon={app}\Corbu.exe
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "bureau"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"

[Files]
Source: "..\dist\Corbu\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Corbu"; Filename: "{app}\Corbu.exe"
Name: "{group}\Corbu (serveur pour le réseau du bureau)"; Filename: "{app}\Corbu.exe"; Parameters: "--hote 0.0.0.0"
Name: "{group}\Désinstaller Corbu"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Corbu"; Filename: "{app}\Corbu.exe"; Tasks: bureau

[Run]
Filename: "{app}\Corbu.exe"; Description: "Lancer Corbu"; Flags: nowait postinstall skipifsilent
