@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
echo Refreshing OCTOPUS live data...
python extract_live_data.py
python extract_ops_data.py
python extract_graph.py
echo Done.
