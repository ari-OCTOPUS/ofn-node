@echo off
rem RUN-ORGANISM.bat - always-on organism loop for the 30-day data run.
rem Clean kill: create file F:\backup\_ops\STOP-ORGANISM then wait one tick.
rem Restart (from dashboard): dashboard creates STOP-ORGANISM + RESTART-REQUESTED.
rem   We see STOP, notice RESTART-REQUESTED, clear both, and loop again with new env.
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d F:\backup\_ops
:loop
rem Load flag overrides from dashboard if present (set KEY=VALUE lines).
if exist "F:\backup\_ops\OCTOPUS.env" call "F:\backup\_ops\OCTOPUS.env"
python -X utf8 organism.py
echo organism exited - waiting 10 seconds ... press Ctrl+C twice to stop
timeout /t 10 /nobreak >nul
if exist "F:\backup\_ops\STOP-ORGANISM" (
    if exist "F:\backup\_ops\RESTART-REQUESTED" (
        del "F:\backup\_ops\STOP-ORGANISM" >nul 2>&1
        del "F:\backup\_ops\RESTART-REQUESTED" >nul 2>&1
        echo RESTART-REQUESTED found - restarting organism with new env ...
        goto loop
    )
    goto end
)
goto loop
:end
echo STOP-ORGANISM flag found - launcher ends here.
echo To run again: delete F:\backup\_ops\STOP-ORGANISM then double-click this .bat.
