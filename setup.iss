[Setup]
AppName=KSO SnapTube Turbo V2
AppVersion=2.0
AppPublisher=KSO
AppPublisherURL=https://github.com/kso
DefaultDirName={autopf}\KSO_SnapTube_Turbo_V2
DefaultGroupName=KSO SnapTube Turbo V2
OutputDir=installer_output
OutputBaseFilename=KSO_SnapTube_Turbo_V2_Setup
SetupIconFile=
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayName=KSO SnapTube Turbo V2
UninstallDisplayIcon={app}\KSO_SnapTube_Turbo_V2.exe

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\KSO_SnapTube_Turbo_V2.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\KSO SnapTube Turbo V2"; Filename: "{app}\KSO_SnapTube_Turbo_V2.exe"
Name: "{group}\{cm:UninstallProgram,KSO SnapTube Turbo V2}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\KSO SnapTube Turbo V2"; Filename: "{app}\KSO_SnapTube_Turbo_V2.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\KSO_SnapTube_Turbo_V2.exe"; Description: "{cm:LaunchProgram,KSO SnapTube Turbo V2}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // تشغيل التطبيق بعد التثبيت
  end;
end;
