@echo off
REM یک‌بار DM و پست بساز (برای تسکِ روزانه).
set "ROOT=%~dp0.."
cd /d "%ROOT%"
if not exist .venv (
  python -m venv .venv
  call .venv\Scripts\activate.bat
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate.bat
)
cd /d "%ROOT%\..\ziman-agent"
python worker.py --dm 6
python worker.py --posts 3
