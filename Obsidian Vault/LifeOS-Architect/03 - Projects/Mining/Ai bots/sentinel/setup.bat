@echo off
chcp 65001 > nul
echo.
echo ============================================================
echo   SENTINEL — Setup (اولین بار)
echo ============================================================
echo.

:: ── بررسی Python ──
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python پیدا نشد!
    echo         از https://python.org دانلود کن
    pause
    exit /b 1
)
echo [OK] Python پیدا شد

:: ── بررسی .env ──
if not exist ".env" (
    echo.
    echo [!] فایل .env وجود ندارد — کپی می‌کنیم...
    copy ".env.template" ".env" > nul
    echo [OK] .env ساخته شد
    echo.
    echo  >>> حالا .env را باز کن و API keyها را وارد کن:
    echo      LUNARCRUSH_API_KEY=...
    echo      CRYPTOQUANT_API_KEY=...
    echo      TELEGRAM_BOT_TOKEN=...
    echo      TELEGRAM_CHAT_ID=...
    echo.
    notepad .env
) else (
    echo [OK] .env موجود است
)

:: ── نصب packages ──
echo.
echo [*] نصب Python packages...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] نصب package‌ها شکست خورد
    pause
    exit /b 1
)
echo [OK] همه‌ی packages نصب شدند

:: ── ساخت پوشه data ──
if not exist "data" mkdir data
echo [OK] پوشه‌ی data/ آماده است

echo.
echo ============================================================
echo   Setup کامل شد!
echo.
echo   مرحله‌ی بعد:
echo   1. اگر .env را تازه باز کردی، keyها را وارد کن و ذخیره کن
echo   2. run_first.bat را اجرا کن (تاریخچه‌ی ۳۶۵ روزه)
echo   3. بعد از آن هر روز run.bat را اجرا کن
echo ============================================================
echo.
pause
