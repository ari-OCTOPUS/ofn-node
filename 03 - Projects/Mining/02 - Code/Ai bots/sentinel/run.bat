@echo off
chcp 65001 > nul
echo.
echo ============================================================
echo   SENTINEL — اجرای روزانه
echo ============================================================
echo.

:: ── بررسی .env ──
if not exist ".env" (
    echo [ERROR] .env پیدا نشد! ابتدا setup.bat را اجرا کن.
    pause
    exit /b 1
)

:: ── اجرا ──
python run_daily.py
if errorlevel 1 (
    echo.
    echo [!] اجرا با خطا تمام شد — sentinel_daily.log را بررسی کن
) else (
    echo.
    echo [OK] اجرا موفق بود — پیام Telegram ارسال شد
)

echo.
pause
