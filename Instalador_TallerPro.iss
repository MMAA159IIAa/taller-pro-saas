#define MyAppName "TallerPro SaaS Edition"
#define MyAppVersion "2.0.1"
#define MyAppPublisher "TallerPro"
#define MyAppExeName "TallerPro.exe"

[Setup]
AppId={{C6E26E80-887B-4321-99CC-90BAFD887B01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=Instalador_TallerPro_SaaS
SetupIconFile=icono.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startuponboot"; Description: "Garantizar que TallerPro inicie con Windows (Recomendado)"; GroupDescription: "Arranque Automático:"

[Files]
Source: "dist\TallerPro\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\TallerPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icono.ico"; DestDir: "{app}"

[Dirs]
Name: "C:\TallerPro_Contador"; Permissions: users-modify

[Icons]
Name: "{autodesktop}\TallerPro"; Filename: "{app}\TallerPro.exe"; Tasks: desktopicon; IconFilename: "{app}\favicon.ico"
Name: "{userstartup}\TallerPro"; Filename: "{app}\TallerPro.exe"; Tasks: startuponboot; IconFilename: "{app}\favicon.ico"

[Run]
Filename: "{app}\TallerPro.exe"; Description: "Iniciar TallerPro ahora"; Flags: nowait postinstall skipifsilent
