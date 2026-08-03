@echo off
chcp 65001 > nul
echo.
echo ============================================================
echo   SENTINEL — اولین اجرا (Harvest 365 روز)
echo   فقط یک بار اجرا کن!
echo ============================================================
echo.
echo این اسکریپت تاریخچه‌ی کامل ۳۶۵ روزه را می‌کشد.
echo زمان: ~10-15 دقیقه (rate limited).
echo.
pause

python run_daily.py --harvest
if errorlevel 1 (
    echo.
    echo [ERROR] خطا رخ داد — sentinel_daily.log را بررسی کن
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Harvest کامل شد!
echo   از این به بعد هر روز فقط run.bat را اجرا کن.
echo ============================================================
echo.
pause
