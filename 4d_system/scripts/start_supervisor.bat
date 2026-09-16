@echo off
REM ============================================================
REM 4d_system self-heal supervisor (24/7 watchdog)
REM Keeps brain.daemon + brain.telegram_bot alive after crashes.
REM Never restarts after a protective HALT or an owner stop.
REM
REM Requires in .env:  CONTROL_PLANE_SELF_HEAL=1
REM Stop it with:      outputs\supervisor.stop  (or Ctrl+C)
REM ASCII-only messages on purpose (cmd OEM codepage).
REM ============================================================
cd /d "%~dp0.."
python -m control_plane.supervisor
