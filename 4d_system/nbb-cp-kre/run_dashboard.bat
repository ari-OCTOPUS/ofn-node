@echo off
REM ============================================================
REM  nbb-cp-kre v0.2 — Knowledge Reality live dashboard
REM  double-click to launch the live Streamlit dashboard.
REM ============================================================
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

echo ^| Knowledge Reality v0.2 — live vault scanner + 18 visualisations
echo ^| Installing / updating nbb-cp-kre (incl. viz + live deps) ...
python -m pip install -e ".[ui,live]" --quiet
if errorlevel 1 goto :err

set KRE_VAULT=F:\backup
set KRE_OUT=F:\kre-out

echo.
echo ^| Vault  : %KRE_VAULT% ^(READ-ONLY^)
echo ^| Output : %KRE_OUT%
echo ^| Mode   : LIVE (file watcher + auto-refresh + cache)
echo.
echo ^| Open http://localhost:8501 in your browser when the server is up.
echo.
python -m streamlit run src\nbb_cp_kre\ui\streamlit_app.py --browser.gatherUsageStats false
goto :eof

:err
echo.
echo Install failed. Is Python 3.11+ on PATH? Are numpy/scipy/networkx/sklearn installed?
pause
