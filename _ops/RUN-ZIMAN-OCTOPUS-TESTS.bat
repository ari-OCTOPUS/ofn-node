@echo off
:: RUN-ZIMAN-OCTOPUS-TESTS.bat — تست‌های اتصال زیمان به اختاپوس (offline)
:: اجرا: cd /d F:\backup\_ops && RUN-ZIMAN-OCTOPUS-TESTS.bat
:: ──────────────────────────────────────────────────────────────────────────
setlocal
cd /d "%~dp0"

echo.
echo ========================================================
echo   Ziman ↔ Octopus wiring + biology tests (no network, no spend)
echo ========================================================

:: ── ۱) تست پای زیمان ───────────────────────────────────────────────────
echo.
echo [1/4] tests\test_ziman_leg.py ...
python -m pytest tests\test_ziman_leg.py -q --tb=short

:: ── ۲) تست wiring (make_ziman_leg + ziman_beat) ─────────────────────────
echo.
echo [2/4] tests\test_ziman_wiring.py ...
python -m pytest tests\test_ziman_wiring.py -q --tb=short

:: ── ۳) تست زیست‌شناسی: قلب + اعصاب + دکتر تکاملی ────────────────────────
echo.
echo [3/4] tests\test_ziman_biology.py ...
python -m pytest tests\test_ziman_biology.py -q --tb=short

:: ── ۴) smoke اتصال wiring ────────────────────────────────────────────────
echo.
echo [4/4] smoke_ziman_wire.py ...
set OCTOPUS_WIRE_ZIMAN=1
python smoke_ziman_wire.py

echo.
echo ========================================================
echo   پایان. برای تست‌های Phase 2 product:
echo   cd /d "F:\backup\03 - Projects\Ziman Galerry\ziman-agent"
echo   python -m pytest tests\test_product.py -q
echo ========================================================

endlocal
pause
