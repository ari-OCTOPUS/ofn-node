@echo off
rem One-click runner for pf-test-fossil-cleanup-2026-07-11.ps1 (ASCII only)
rem Runs the session-47 delegated cleanup: merge + quarantine + gitignore + live suite.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0pf-test-fossil-cleanup-2026-07-11.ps1"
echo.
pause
