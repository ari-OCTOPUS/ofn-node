@echo off
rem RUN-DASHBOARD.bat - live Octopus dashboard on http://127.0.0.1:8770
rem Read-only to state; only writes OCTOPUS.env (flag overrides) + STOP-ORGANISM (clean kill).
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set DASHBOARD_AUTOOPEN=1
cd /d F:\backup\_ops\dashboard
python -X utf8 server.py
pause
