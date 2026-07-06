@echo off
REM لانچرِ تولیدیِ مغزِ کنترل: حالت بیرونِ vault، لاگ، و ری‌استارتِ خودکار.
setlocal enabledelayedexpansion
set "ROOT=%~dp0.."
cd /d "%ROOT%"
if not defined CONTROL_STATE_DIR set "CONTROL_STATE_DIR=%USERPROFILE%\.ziman-control"
if not exist "%CONTROL_STATE_DIR%" mkdir "%CONTROL_STATE_DIR%"
if not exist .venv (
  python -m venv .venv
  call .venv\Scripts\activate.bat
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate.bat
)
:loop
echo [%date% %time%] brain starting >> "%CONTROL_STATE_DIR%\brain.log"
python app.py >> "%CONTROL_STATE_DIR%\brain.log" 2>&1
echo [%date% %time%] brain exited -- restarting in 10s >> "%CONTROL_STATE_DIR%\brain.log"
timeout /t 10 /nobreak >nul
goto loop
