@echo off
chcp 65001 >nul
REM B11: جمع‌آوری داده‌ی تصمیم برای یکی‌سازی پشته‌های LLM.
REM هر اجرا ۶ پرامپت روی هر دو پشته + ثبت در outputs\llm_shadow.jsonl
REM چند بار در روزهای مختلف اجرا کن تا ≥۳۰ رکورد جمع شود.
cd /d "%~dp0.."
python -m llm.shadow_compare --n 6
echo.
echo رکوردها در: outputs\llm_shadow.jsonl
pause
