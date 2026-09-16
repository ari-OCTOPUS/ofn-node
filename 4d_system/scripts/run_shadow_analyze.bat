@echo off
chcp 65001 >nul
REM B11 فاز ۲: خواندنِ outputs\llm_shadow.jsonl و صدورِ حکمِ تصمیم.
REM فقط-خواندنی: هیچ سوئیچِ زنده، هیچ ویرایشِ سورس، هیچ فلگی روشن نمی‌شود.
REM اول چند بار run_shadow_compare.bat را اجرا کن تا ≥۳۰ رکورد جمع شود.
cd /d "%~dp0.."
python -m llm.shadow_analyze
echo.
pause
