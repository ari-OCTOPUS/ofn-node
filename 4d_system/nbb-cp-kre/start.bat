@echo off
REM ============================================================
REM  start.bat — one-click launch of the Knowledge Reality live
REM  dashboard. Mirrors the control-brain/start.bat convention:
REM  UTF-8 console, optional venv, streamlit run.
REM ============================================================
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d %~dp0

REM --- optional local venv (matches control-brain pattern) ----------------
if exist .venv (
  call .venv\Scripts\activate
) else (
  REM fall back to the global interpreter; deps are already installed there
  echo (using global Python; create .venv if you want isolation)
)

REM --- defaults (override via env if you like) -----------------------------
if "%KRE_VAULT%"=="" set KRE_VAULT=F:\backup
if "%KRE_OUT%"==""   set KRE_OUT=F:\kre-out

echo ^| Knowledge Reality v0.2 — live
echo ^| Vault: %KRE_VAULT% ^(read-only^)   Output: %KRE_OUT%
echo.
python -m streamlit run src\nbb_cp_kre\ui\streamlit_app.py --browser.gatherUsageStats false
pause
