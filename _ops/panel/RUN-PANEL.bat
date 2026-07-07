@echo off
rem RUN-PANEL.bat - local onboarding panel, asks a few questions and remembers you.
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PANEL_AUTOOPEN=1
cd /d F:\backup\_ops\panel
python -X utf8 server.py
pause
