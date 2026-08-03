@echo off
:: QuantumAlpha — ثبت Task Scheduler برای اجرای خودکار هر 6 ساعت
:: Run as Administrator

echo Setting up Windows Task Scheduler...
echo.

set BOT_DIR=%~dp0
set PYTHON_CMD=python -X utf8 "%BOT_DIR%main.py"

:: حذف task قبلی اگه بود
schtasks /delete /tn "QuantumAlphaBot" /f >nul 2>&1

:: ایجاد task جدید — هر 6 ساعت، از موقع بوت
schtasks /create ^
  /tn "QuantumAlphaBot" ^
  /tr "cmd /c cd /d \"%BOT_DIR%\" && python -X utf8 main.py --once >> \"%BOT_DIR%logs\quantum_log.txt\" 2>&1" ^
  /sc hourly ^
  /mo 6 ^
  /st 08:00 ^
  /ru "%USERNAME%" ^
  /f

if %errorlevel% == 0 (
    echo.
    echo  [OK] Task registered: runs every 6 hours starting 08:00
    echo  [OK] Logs saved to: %BOT_DIR%logs\quantum_log.txt
    echo.
    echo  To view: Task Scheduler ^> Task Scheduler Library ^> QuantumAlphaBot
    echo  To stop: schtasks /delete /tn "QuantumAlphaBot" /f
) else (
    echo  [!] Failed. Right-click this file and choose "Run as administrator"
)

:: ایجاد پوشه logs
if not exist "%BOT_DIR%logs" mkdir "%BOT_DIR%logs"

pause
