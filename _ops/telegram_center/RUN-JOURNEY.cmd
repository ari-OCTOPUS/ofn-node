@echo off
rem RUN-JOURNEY.cmd - one tick of the unattended acceptance journey.
rem This is what the Windows Scheduled Task runs (every ~15 minutes).
rem ASCII-only: cmd.exe parses this file in the OEM codepage.
rem
rem The journey decides for itself what to do from its own state file; two
rem ticks inside the same window do nothing twice. It NEVER polls Telegram -
rem the live center owns that token's poller. Only sends.
rem
rem Secrets (TELEGRAM_BOT_TOKEN / TG_CENTER_BOT_TOKEN / chat ids) are loaded by
rem env_loader from the vault-root .env - NEVER hardcoded here.
rem Kill switch: delete the scheduled task, or set OCTOPUS_JOURNEY_TASK and let
rem the final phase delete it itself.
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
pushd "%~dp0"
if exist "%~dp0..\OCTOPUS-flags.cmd" call "%~dp0..\OCTOPUS-flags.cmd"
python -X utf8 "%~dp0acceptance_journey.py" --tick
set RC=%ERRORLEVEL%
popd
exit /b %RC%
