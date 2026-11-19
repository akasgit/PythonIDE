# Used by GitHub Actions: installs PythonIDE on a machine that looks like it
# has no Python, then checks the right Python was installed and the app starts.
param(
    [Parameter(Mandatory = $true)][string]$ExpectedPython,  # e.g. Python38-32
    [string]$ExtraArgs = '',
    # GitHub's machines come with Python 3.12.10 (32-bit) partly installed, and it
    # cannot be fully removed. Python's installer then only "repairs" that copy, so
    # a fresh install cannot be checked there. With this switch the test checks
    # that the right Python installer was chosen and finished successfully, and
    # skips the checks that need a fresh install.
    [switch]$PythonPreinstalledOnRunner
)
$ErrorActionPreference = 'Stop'

# Hide every registered Python so the installer must install its own.
foreach ($key in 'HKLM:\SOFTWARE\Python\PythonCore', 'HKLM:\SOFTWARE\WOW6432Node\Python\PythonCore', 'HKCU:\SOFTWARE\Python\PythonCore') {
    if (Test-Path $key) { Remove-Item $key -Recurse -Force; Write-Host "Hid existing Python: $key" }
}

$setup = (Get-ChildItem "$PSScriptRoot\Output\*.exe" | Select-Object -First 1).FullName
$log = Join-Path $env:RUNNER_TEMP "install-$ExpectedPython.log"
$arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/TASKS=desktopicon', "/LOG=$log")
if ($ExtraArgs) { $arguments += $ExtraArgs }
$p = Start-Process $setup -ArgumentList $arguments -Wait -PassThru
if ($p.ExitCode -ne 0) { Get-Content $log; throw "Installer failed with code $($p.ExitCode)" }

$app = "${env:ProgramFiles(x86)}\PythonIDE"

if ($PythonPreinstalledOnRunner) {
    if (-not (Test-Path "$app\start.pyw")) { throw "PythonIDE files were not installed" }
    $installer = "python-" + ($ExpectedPython -replace 'Python3(\d+)-32', '3.$1') + ".10.exe"
    if (-not (Select-String -Path $log -Pattern ([regex]::Escape($installer)) -Quiet)) {
        throw "The installer did not choose $installer"
    }
    $pyLog = Get-ChildItem $env:TEMP -Filter 'Python *.log' | Where-Object { $_.Name -notmatch '_\d+_' } |
        Sort-Object LastWriteTime | Select-Object -Last 1
    if (-not (Select-String -Path $pyLog.FullName -Pattern 'Exit code: 0x0' -Quiet)) {
        throw "Python's installer did not finish successfully ($($pyLog.Name))"
    }
    Write-Host "OK: $installer was chosen and Python's installer finished successfully."
    exit 0
}
if (-not (Test-Path "$app\start.pyw")) { throw "PythonIDE files were not installed" }

$lnk = (New-Object -ComObject WScript.Shell).CreateShortcut("$env:PUBLIC\Desktop\PythonIDE.lnk")
Write-Host "Desktop shortcut runs: $($lnk.TargetPath) $($lnk.Arguments)"
if (-not (Test-Path $lnk.TargetPath)) { throw "The shortcut points to a Python that does not exist" }
if ($lnk.TargetPath -notlike "*\$ExpectedPython\pythonw.exe") { throw "Expected the bundled $ExpectedPython to be used" }

$python = Join-Path (Split-Path $lnk.TargetPath) 'python.exe'
& $python -c "import sys, tkinter; print('Using Python', sys.version, '- Tk', tkinter.TkVersion)"
if ($LASTEXITCODE -ne 0) { throw "Python or Tkinter is missing" }

# Run the test suite with the Python the installer put on the machine.
& $python -m unittest discover -s (Join-Path $PSScriptRoot '..\tests')
if ($LASTEXITCODE -ne 0) { throw "Tests failed with the installed Python" }

$ide = Start-Process $lnk.TargetPath -ArgumentList "`"$app\start.pyw`"" -WorkingDirectory $app -PassThru
Start-Sleep -Seconds 10
if ($ide.HasExited) { throw "PythonIDE closed by itself (exit code $($ide.ExitCode))" }
Write-Host "PythonIDE is running with $ExpectedPython."
Stop-Process -Id $ide.Id
