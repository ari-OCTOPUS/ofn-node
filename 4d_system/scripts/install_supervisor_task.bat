@echo off
REM ============================================================
REM Registers a Windows logon task so the self-heal supervisor
REM starts automatically every time you log in (24/7 operation).
REM
REM RUN THIS YOURSELF (double-click) - it changes a system setting
REM (Task Scheduler), so it is an owner action by design.
REM
REM Before running, make sure .env contains:
REM   CONTROL_PLANE_SELF_HEAL=1
REM
REM To remove later:
REM   schtasks /Delete /TN "4d_system_supervisor" /F
REM ============================================================
cd /d "%~dp0.."
schtasks /Create /TN "4d_system_supervisor" /TR "\"%CD%\scripts\start_supervisor.bat\"" /SC ONLOGON /F
if errorlevel 1 (
    echo [X] Failed to register the task.
    exit /b 1
)
echo [OK] Task "4d_system_supervisor" registered - starts at next logon.
echo      To start it right now without relogin:
echo      schtasks /Run /TN "4d_system_supervisor"
