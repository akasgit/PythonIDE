; Inno Setup script for PythonIDE.
;
; Builds PythonIDE-Setup-<version>.exe. When run, the installer:
;   1. looks for Python 3.8 or newer (with Tkinter) on the computer;
;   2. if none is found, installs the bundled Python 3.8.10 (32-bit, which
;      runs on both 32-bit and 64-bit Windows 7/8/10/11);
;   3. installs PythonIDE and creates Start menu / desktop shortcuts.
;
; Build (on Windows):  ISCC.exe /DAppVersion=1.0.0 installer\PythonIDE.iss
; The Python installer must be at installer\python-3.8.10.exe. The GitHub
; workflow in .github/workflows/build-installer.yml downloads it.

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define PythonInstaller "python-3.8.10.exe"

[Setup]
AppId={{8F3C2A51-6B7D-4E2A-9C1F-5D4B3A2E1F00}
AppName=PythonIDE
AppVersion={#AppVersion}
AppVerName=PythonIDE {#AppVersion}
AppPublisher=PythonIDE
DefaultDirName={autopf}\PythonIDE
DefaultGroupName=PythonIDE
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=PythonIDE-Setup-{#AppVersion}
SetupIconFile=..\pythonide\icon.ico
UninstallDisplayIcon={app}\pythonide\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
; Windows 7 SP1 or newer (Python 3.8 needs SP1).
MinVersion=6.1sp1

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
; Python is installed right after this file is copied (AfterInstall), so it
; is ready before the shortcuts below are created.
Source: "{#PythonInstaller}"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: NeedPython; AfterInstall: InstallPython
Source: "..\pythonide\*.py"; DestDir: "{app}\pythonide"; Flags: ignoreversion
Source: "..\pythonide\icon.ico"; DestDir: "{app}\pythonide"; Flags: ignoreversion
Source: "..\start.pyw"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Start PythonIDE.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Teachers drop their own example programs here.
Name: "{app}\examples"; Permissions: users-modify

[Icons]
Name: "{group}\PythonIDE"; Filename: "{code:PythonW}"; Parameters: """{app}\start.pyw"""; WorkingDir: "{app}"; IconFilename: "{app}\pythonide\icon.ico"; Comment: "Python editor for students"
Name: "{group}\Teacher examples folder"; Filename: "{app}\examples"
Name: "{group}\Uninstall PythonIDE"; Filename: "{uninstallexe}"
Name: "{autodesktop}\PythonIDE"; Filename: "{code:PythonW}"; Parameters: """{app}\start.pyw"""; WorkingDir: "{app}"; IconFilename: "{app}\pythonide\icon.ico"; Comment: "Python editor for students"; Tasks: desktopicon

[Run]
Filename: "{code:PythonW}"; Parameters: """{app}\start.pyw"""; WorkingDir: "{app}"; Description: "Start PythonIDE now"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\pythonide\__pycache__"

[Code]
var
  PythonWPath: String;

{ True for registry tags like "3.8", "3.8-32", "3.11" (Python 3.8 or newer). }
function ParseVersion(Tag: String; var Minor: Integer): Boolean;
var
  Dash, Dot, Major: Integer;
  V: String;
begin
  Result := False;
  V := Tag;
  Dash := Pos('-', V);
  if Dash > 0 then
    V := Copy(V, 1, Dash - 1);
  Dot := Pos('.', V);
  if Dot = 0 then
    Exit;
  Major := StrToIntDef(Copy(V, 1, Dot - 1), 0);
  Minor := StrToIntDef(Copy(V, Dot + 1, Length(V)), 0);
  Result := (Major = 3) and (Minor >= 8);
end;

{ Look through one registry view for the newest suitable Python. }
procedure ScanRegistry(Root: Integer; var Best: String; var BestMinor: Integer);
var
  Names: TArrayOfString;
  I, Minor: Integer;
  Dir: String;
begin
  if not RegGetSubkeyNames(Root, 'SOFTWARE\Python\PythonCore', Names) then
    Exit;
  for I := 0 to GetArrayLength(Names) - 1 do
  begin
    if ParseVersion(Names[I], Minor) and (Minor > BestMinor) then
    begin
      if RegQueryStringValue(Root, 'SOFTWARE\Python\PythonCore\' + Names[I] + '\InstallPath', '', Dir) then
      begin
        Dir := AddBackslash(Dir);
        { PythonIDE needs Tkinter, which is an optional part of Python. }
        if FileExists(Dir + 'pythonw.exe') and FileExists(Dir + 'Lib\tkinter\__init__.py') then
        begin
          Best := Dir + 'pythonw.exe';
          BestMinor := Minor;
        end;
      end;
    end;
  end;
end;

function FindPython(): String;
var
  Minor: Integer;
begin
  Result := '';
  Minor := 7;
  if IsWin64 then
    ScanRegistry(HKLM64, Result, Minor);
  ScanRegistry(HKLM32, Result, Minor);
  ScanRegistry(HKCU, Result, Minor);
end;

function InitializeSetup(): Boolean;
begin
  PythonWPath := FindPython();
  Result := True;
end;

function NeedPython(): Boolean;
begin
  Result := PythonWPath = '';
end;

function PythonDir(): String;
begin
  Result := ExpandConstant('{commonpf32}\Python38-32');
end;

procedure InstallPython();
var
  Code: Integer;
  Params: String;
begin
  WizardForm.StatusLabel.Caption := 'Installing Python 3.8.10. This can take a few minutes...';
  Params := '/passive InstallAllUsers=1 PrependPath=1 Include_tcltk=1 Include_pip=1 ' +
            'Include_launcher=1 InstallLauncherAllUsers=1 Include_test=0 Include_doc=0 ' +
            'AssociateFiles=1 Shortcuts=1 TargetDir="' + PythonDir() + '"';
  if not Exec(ExpandConstant('{tmp}\{#PythonInstaller}'), Params, '', SW_SHOW,
              ewWaitUntilTerminated, Code) then
    Code := -1;
  if (Code <> 0) and (Code <> 3010) then
    MsgBox('Python could not be installed (error code ' + IntToStr(Code) + ').' + #13#10 + #13#10 +
           'PythonIDE will be installed, but it needs Python to work. Please install ' +
           'Python 3.8 from python.org (tick "Add Python to PATH"), then start PythonIDE ' +
           'with "Start PythonIDE.bat" in ' + ExpandConstant('{app}') + '.',
           mbError, MB_OK);
  PythonWPath := FindPython();
end;

{ Used by the shortcuts: the pythonw.exe that will start PythonIDE. }
function PythonW(Param: String): String;
begin
  if PythonWPath = '' then
    PythonWPath := FindPython();
  if PythonWPath = '' then
    PythonWPath := PythonDir() + '\pythonw.exe';
  Result := PythonWPath;
end;

function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo,
  MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
begin
  Result := MemoDirInfo + NewLine + NewLine;
  if MemoTasksInfo <> '' then
    Result := Result + MemoTasksInfo + NewLine + NewLine;
  Result := Result + 'Python:' + NewLine;
  if PythonWPath = '' then
    Result := Result + Space + 'Python 3.8.10 will be installed (no suitable Python was found).'
  else
    Result := Result + Space + 'Already installed, will be used: ' + PythonWPath;
end;
