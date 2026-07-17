@echo off
rem RUN-PANEL.bat - local onboarding panel, asks a few questions and remembers you.
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PANEL_AUTOOPEN=1
rem RC1: بارگذاریِ فلگ‌ها (مثلِ RUN-ORGANISM/CORTEX/LIVE) تا OCTOPUS_HTTP_AUTH به این سرور هم برسد
if exist "F:\backup\_ops\OCTOPUS-flags.cmd" call "F:\backup\_ops\OCTOPUS-flags.cmd"
cd /d F:\backup\_ops\panel
python -X utf8 server.py
pause
