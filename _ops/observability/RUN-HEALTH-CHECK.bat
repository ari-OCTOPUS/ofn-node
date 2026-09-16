@echo off
REM RUN-HEALTH-CHECK.bat — Run all observability checks in sequence.
REM Exit code = highest severity (0=ok, 1=warn, 2=err).
REM All outputs go to stdout/stderr; no file writes.

setlocal enabledelayedexpansion
set MAX_EXIT=0

cd /d "%~dp0"

set PYTHON=py -3
where py >nul 2>&1 || set PYTHON=python

echo ===== Octopus Health Check Suite =====
echo.

echo --- health_check.py ---
%PYTHON% health_check.py
if !errorlevel! gtr !MAX_EXIT! set MAX_EXIT=!errorlevel!

echo.
echo --- budget_monitor.py ---
%PYTHON% budget_monitor.py
if !errorlevel! gtr !MAX_EXIT! set MAX_EXIT=!errorlevel!

echo.
echo --- flag_monitor.py ---
%PYTHON% flag_monitor.py
if !errorlevel! gtr !MAX_EXIT! set MAX_EXIT=!errorlevel!

echo.
echo --- leg_monitor.py ---
%PYTHON% leg_monitor.py
if !errorlevel! gtr !MAX_EXIT! set MAX_EXIT=!errorlevel!

echo.
echo ===== Suite exit: !MAX_EXIT! =====
endlocal & exit /b %MAX_EXIT%
