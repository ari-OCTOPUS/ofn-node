@echo off
rem RUN-DASHBOARD.bat - live Octopus dashboard on http://127.0.0.1:8770
rem Read-only to state; only writes OCTOPUS.env (flag overrides) + STOP-ORGANISM (clean kill).
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set DASHBOARD_AUTOOPEN=1
rem RC1: بارگذاریِ فلگ‌ها (مثلِ RUN-ORGANISM/CORTEX/LIVE) تا OCTOPUS_HTTP_AUTH به این سرور هم برسد
if exist "F:\backup\_ops\OCTOPUS-flags.cmd" call "F:\backup\_ops\OCTOPUS-flags.cmd"
cd /d F:\backup\_ops\dashboard
python -X utf8 server.py
pause
