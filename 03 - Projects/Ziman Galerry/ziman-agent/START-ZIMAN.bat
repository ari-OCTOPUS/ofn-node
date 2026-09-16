@echo off
:: START-ZIMAN.bat — راه‌اندازی ایمن و تست زیمان (بدون شبکه/API/تلگرام)
:: تمام دستورها local draft هستند. هیچ پیامی ارسال نمی‌شود.
:: ──────────────────────────────────────────────────────────────────────────
setlocal
cd /d "%~dp0"

echo.
echo ========================================================
echo   Ziman Phase 2 — local tests + CLI (no network)
echo ========================================================

:: ── ۱) تست‌های خالص product.py ─────────────────────────────────────────
echo.
echo [1/4] pytest tests\test_product.py ...
python -m pytest tests\test_product.py -q --tb=short
if errorlevel 1 (
    echo FAILED: product tests — لطفاً خطاها را رفع کن.
    goto :end
)

:: ── ۲) selftest داخلی CLI ────────────────────────────────────────────────
echo.
echo [2/4] phase2_cli.py --selftest ...
python phase2_cli.py --selftest
if errorlevel 1 (
    echo FAILED: selftest
    goto :end
)

:: ── ۳) dry-run Telegram (preview متن، ارسال نمی‌کند) ────────────────────
echo.
echo [3/4] /ziman_status dry-run ...
python phase2_cli.py --telegram-dry /ziman_status

:: ── ۴) worker selftest ───────────────────────────────────────────────────
echo.
echo [4/4] worker.py --selftest ...
python worker.py --selftest

echo.
echo ========================================================
echo   همه تست‌ها اجرا شدند.
echo   worker.py --once   ← یک draft بساز (offline)
echo   worker.py --dm 6   ← ۶ DM draft بساز
echo   worker.py --status ← وضعیت JSON
echo ========================================================

:end
endlocal
pause
