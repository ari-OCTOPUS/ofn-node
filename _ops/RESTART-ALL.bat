@echo off
REM RESTART-ALL.bat - the one button. Double-click to restart the whole organism.
REM
REM Delegates to RESTART-ALL.ps1, which restarts every limb through
REM RESTART-PROCESS.ps1 and then runs an acceptance gate (new pids, no stray
REM markers, flags loaded equally, fresh organism state, beat advancing).
REM
REM This file MUST keep CRLF line endings. cmd.exe reads a lone-LF batch file one
REM broken line at a time - that is how the centre once booted with 59 of 156 flags.
REM Written by hand with CRLF on 2026-08-03; do not re-save it with a LF editor.
REM ASCII only: a console pasting Persian back re-executes it as commands.

title OCTOPUS - restart all
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RESTART-ALL.ps1" %*
set RC=%ERRORLEVEL%
echo.
if "%RC%"=="0" (echo RESULT: OK) else (echo RESULT: FAILED - exit code %RC%)
echo.
pause
exit /b %RC%
