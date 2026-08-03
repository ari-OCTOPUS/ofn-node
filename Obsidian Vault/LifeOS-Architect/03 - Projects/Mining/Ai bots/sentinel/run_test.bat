@echo off
chcp 65001 > nul
echo.
echo ============================================================
echo   SENTINEL — تست Mock (بدون API واقعی)
echo ============================================================
echo.
echo این فقط تست است — هیچ API واقعی صدا زده نمی‌شود.
echo پیام Telegram واقعی ارسال می‌شود (Telegram Bot token لازم است).
echo.

python run_daily.py --mock
if errorlevel 1 (
    echo [!] خطا رخ داد
) else (
    echo [OK] تست موفق
)

echo.
pause
