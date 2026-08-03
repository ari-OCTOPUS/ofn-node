@echo off
title QuantumAlpha v3  --  Single Run
color 0B
cd /d "%~dp0"
echo.
echo  [Single Run Mode]
echo.
python -X utf8 main.py --once
echo.
echo  Done. Press any key to close.
pause > nul
