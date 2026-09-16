@echo off
REM ============================================================
REM run-langar.bat — اجرای بات لنگر در پس‌زمینه (Windows)
REM Project-F · 2026-07-16
REM
REM این فایل توسط Scheduled Task در startup صدا زده می‌شود.
REM auto-restart: اگه بات crash کنه، ۱۰ ثانیه بعد دوباره بالا می‌آید.
REM ============================================================

setlocal
set "PROJECT_DIR=F:\backup\03 - Projects\اونلی فنز"
set "LANGAR_DIR=%PROJECT_DIR%\langar"
set "PYTHON=python"

REM 2026-07-25 (فاز ۱ یکپارچه‌سازی): فعال‌سازیِ ستونِ فقرات + مغزِ غنی‌شده.
REM هر دو پیش‌فرض خاموش بودند. با این خطوط، langar_bot هنگامِ اجرا این‌ها را
REM می‌بیند. اگر خواستی برگردانی: این دو خط را به =0 تغییر بده یا پاک کن.
set "OCTOPUS_WIRE_PROJECTF_SPINE=1"
set "OCTOPUS_WIRE_PROJECTF_CORTEX=1"

cd /d "%LANGAR_DIR%"

:LOOP
echo [%date% %time%] starting langar_bot...
%PYTHON% langar_bot.py
echo [%date% %time%] langar_bot exited (code %errorlevel%). restart in 10s.
timeout /t 10 /nobreak >nul
goto LOOP
