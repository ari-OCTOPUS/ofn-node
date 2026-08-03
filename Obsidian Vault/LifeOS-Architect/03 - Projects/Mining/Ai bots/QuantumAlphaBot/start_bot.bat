@echo off
title QuantumAlpha v3
color 0A
cd /d "%~dp0"
echo.
echo  ============================================================
echo    QuantumAlpha v3  --  Starting...
echo    Runs every 6 hours  ^|  Ctrl+C to stop
echo  ============================================================
echo.
python -X utf8 main.py
pause
