@echo off
REM ============================================================
REM run-studio.bat — اجرای استودیوی Creator در پس‌زمینه (Windows) [C1 rename 2026-07-20]
REM Project-F · 2026-07-17
REM
REM این فایل توسط Scheduled Task در startup صدا زده می‌شود.
REM auto-restart: اگه استودیو crash کنه، ۱۰ ثانیه بعد دوباره بالا می‌آید.
REM ============================================================

setlocal
set "PROJECT_DIR=F:\backup\03 - Projects\اونلی فنز"
set "STUDIO_DIR=%PROJECT_DIR%\studio"
set "PYTHON=python"

REM 2026-07-25 (فاز ۱ یکپارچه‌سازی): فعال‌سازیِ ستونِ فقرات (studio هم emit می‌کند).
REM CORTEX برای studio لازم نیست (studio مغزِ creator مخصوصِ خودش را دارد)؛
REM فقط SPINE روشن می‌شود تا draft_submitted به bus/bridge برود.
set "OCTOPUS_WIRE_PROJECTF_SPINE=1"

cd /d "%STUDIO_DIR%"

:LOOP
echo [%date% %time%] starting creator_studio...
%PYTHON% creator_studio.py
echo [%date% %time%] creator_studio exited (code %errorlevel%). restart in 10s.
timeout /t 10 /nobreak >nul
goto LOOP
