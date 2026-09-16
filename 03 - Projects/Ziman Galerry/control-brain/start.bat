@echo off
REM شروعِ یک‌کلیکیِ مغزِ کنترل روی ویندوز
cd /d %~dp0
if not exist .venv (
  python -m venv .venv
  call .venv\Scripts\activate
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate
)
python app.py
pause
