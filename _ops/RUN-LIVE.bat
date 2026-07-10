@echo off
rem RUN-LIVE.bat - live control room on http://127.0.0.1:8773 (read + owner actions).
rem Optional autostart: schtasks /Create /TN "OCTOPUS-Live" /SC ONLOGON /TR "F:\backup\_ops\RUN-LIVE.bat"
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d F:\backup\_ops
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 8773 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 goto already
if exist "F:\backup\_ops\OCTOPUS-flags.cmd" call "F:\backup\_ops\OCTOPUS-flags.cmd"
start "octopus-live" http://127.0.0.1:8773
python -X utf8 live\server.py
goto end
:already
echo live cockpit already on 8773.
start "octopus-live" http://127.0.0.1:8773
:end
