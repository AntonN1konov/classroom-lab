; Установщик Classroom Lab для Windows (Inno Setup 6)
; Собирается в GitHub Actions: iscc /DAppVersion=x.y.z desktop\installer.iss
; Перед сборкой нужен результат PyInstaller в dist\ClassroomLab

#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

#define AppName "Classroom Lab"
#define AppExe "ClassroomLab.exe"

[Setup]
AppId={{6F1C2A8E-3B7D-4E59-9C41-2D8A5F0B7C13}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Anton Nikonov
AppPublisherURL=https://github.com/AntonN1konov/classroom-lab
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=ClassroomLab-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Права администратора нужны, чтобы открыть порт в брандмауэре для студентов
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#AppExe}

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\ClassroomLab\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
; Разрешаем входящие подключения студентов из локальной сети
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""{#AppName}"" dir=in action=allow program=""{app}\{#AppExe}"" enable=yes profile=any"; Flags: runhidden waituntilterminated
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""{#AppName}"""; Flags: runhidden; RunOnceId: "RemoveFirewallRule"
