@echo off
rem run-live-headless.bat - start the live cockpit (8773) WITHOUT opening a browser.
rem Used by live-watchdog.ps1 so auto-revival never spams browser windows.
rem (RUN-LIVE.bat is the interactive launcher that DOES open the browser.)
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d F:\backup\_ops
rem don't double-start: if 8773 is already listening, do nothing.
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 8773 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 goto end
rem load non-secret flag overrides (same as RUN-LIVE.bat); secrets load in python via env_loader.
if exist "F:\backup\_ops\OCTOPUS-flags.cmd" call "F:\backup\_ops\OCTOPUS-flags.cmd"
python -X utf8 live\server.py
:end
