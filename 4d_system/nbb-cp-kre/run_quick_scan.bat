@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m nbb_cp_kre.cli run --vault "F:\backup" --out "F:\kre-out" --quick --top-k 40
pause
