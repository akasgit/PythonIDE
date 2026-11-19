@echo off
rem Starts PythonIDE. Double-click this file.
cd /d "%~dp0"
where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw -3 start.pyw %*
    exit /b
)
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw start.pyw %*
    exit /b
)
echo Python is not installed on this computer.
echo Please install Python 3.8 or newer from https://www.python.org/downloads/
echo and tick "Add Python to PATH" during installation.
pause
