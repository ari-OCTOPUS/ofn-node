@echo off
rem RUN-CORTEX.bat - central controller brain (separate process, owner vote 2026-07-10).
rem Clean kill: create file F:\backup\_ops\STOP-CORTEX then wait one cycle.
rem Autostart (owner, once):
rem   schtasks /Create /TN "OCTOPUS-Cortex" /SC ONLOGON /TR "F:\backup\_ops\RUN-CORTEX.bat"
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d F:\backup\_ops
rem D4 (2026-07-23): boot-time global-halt guard (HALT-ALL / architect STOP) - never boot under it.
if exist "F:\backup\_ops\HALT-ALL" goto globalhalt
if exist "F:\backup\04 - Architect System\STOP" goto globalhalt
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 8772 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 goto already
if exist "F:\backup\_ops\OCTOPUS-flags.cmd" call "F:\backup\_ops\OCTOPUS-flags.cmd"
python -X utf8 cortex\cortex.py
echo cortex exited.
goto end
:already
echo cortex already alive on 8772 - not starting a duplicate.
goto end
:globalhalt
echo GLOBAL HALT active (HALT-ALL or architect STOP) - refusing to boot the cortex.
:end
