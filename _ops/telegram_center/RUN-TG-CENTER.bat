@echo off
rem RUN-TG-CENTER.bat - Telegram command-center loop (hub with 9 leg topics).
rem Clean kill: create file F:\backup\_ops\STOP-TG-CENTER then wait one cycle.
rem Flag-off by design: without TELEGRAM_BOT_TOKEN (or chat id) center.py exits
rem as a safe no-op immediately - zero network, zero writes.
rem Secrets (TELEGRAM_BOT_TOKEN, TELEGRAM_OWNER_CHAT_ID, TG_CENTER_CHAT_ID) come
rem from the environment / canonical secrets flow - NEVER hardcoded here.
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d F:\backup\_ops
:loop
if exist "F:\backup\_ops\STOP-TG-CENTER" goto stopped
rem Optional non-secret flag overrides (batch-safe .cmd only; never a .env).
if exist "F:\backup\_ops\OCTOPUS-flags.cmd" call "F:\backup\_ops\OCTOPUS-flags.cmd"
python -X utf8 telegram_center\center.py
echo tg-center exited - waiting 10 seconds ... press Ctrl+C twice to stop
timeout /t 10 /nobreak >nul
goto loop
:stopped
echo STOP-TG-CENTER flag found - launcher ends here.
echo To run again: delete F:\backup\_ops\STOP-TG-CENTER then double-click this .bat.
