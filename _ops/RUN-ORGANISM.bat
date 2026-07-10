@echo off
rem RUN-ORGANISM.bat - always-on organism loop for the 30-day data run.
rem Clean kill: create file F:\backup\_ops\STOP-ORGANISM then wait one tick.
rem Restart (from dashboard): dashboard creates STOP-ORGANISM + RESTART-REQUESTED.
rem   We see STOP, notice RESTART-REQUESTED, clear both, and loop again with new env.
rem
rem Secrets (TELEGRAM_BOT_TOKEN, TELEGRAM_OWNER_CHAT_ID, API keys) load from the
rem canonical secrets file F:\backup\.env via env_loader.py inside python - NOT here.
rem Optional NON-secret flag overrides: put `set KEY=VALUE` lines in OCTOPUS-flags.cmd
rem (a .cmd is batch-safe; a .env is NOT callable - it pops a Windows "open with" dialog).
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d F:\backup\_ops
:loop
rem Guard: if the organism is already alive on 8771, this launcher is a duplicate. Don't
rem spawn a second loop that just bounces off the port (that was the 2026-07-10 restart-loop).
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 8771 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 goto already
rem Optional non-secret flag overrides (batch-safe .cmd only; never a .env).
if exist "F:\backup\_ops\OCTOPUS-flags.cmd" call "F:\backup\_ops\OCTOPUS-flags.cmd"
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
    goto stopped
)
goto loop
:already
echo(
echo [redundant] organism is already running on 127.0.0.1:8771 - nothing to do.
echo You can close this window. Live status page: http://127.0.0.1:8771
echo Clean kill (from anywhere): create the file  F:\backup\_ops\STOP-ORGANISM
timeout /t 10 /nobreak >nul
goto :eof
:stopped
echo STOP-ORGANISM flag found - launcher ends here.
echo To run again: delete F:\backup\_ops\STOP-ORGANISM then double-click this .bat.
