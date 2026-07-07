@echo off
rem RUN-ORGANISM.bat - always-on organism loop for the 30-day data run.
rem Clean kill: create file F:\backup\_ops\STOP-ORGANISM then wait one tick.
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d F:\backup\_ops
:loop
python -X utf8 organism.py
echo organism exited - restart in 10 seconds ... press Ctrl+C twice to stop
timeout /t 10 /nobreak >nul
if exist "F:\backup\_ops\STOP-ORGANISM" goto end
goto loop
:end
echo STOP-ORGANISM flag found - launcher ends here.
