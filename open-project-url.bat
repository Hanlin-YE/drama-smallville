@echo off
setlocal
set "ROOT=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\open-project-url.ps1"
if errorlevel 1 (
  echo.
  echo Failed to open the project. See the message above.
  pause
)
