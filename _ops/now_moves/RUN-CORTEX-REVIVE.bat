@echo off
REM RUN-CORTEX-REVIVE.bat — M3: revive cortex (port 8772) after an unplanned death.
REM Default = dry-run verdict (NO launch, NO writes). Add --revive to actually
REM relaunch a dead 8772 (also needs OCTOPUS_WIRE_CORTEX_REVIVE=1). Crash-safe:
REM backoff + restart-cap; honors STOP-CORTEX / STOP-ORGANISM / parent STOP.
REM
REM Owner activation (once): set OCTOPUS_WIRE_CORTEX_REVIVE=1 in OCTOPUS-flags.cmd,
REM then register a periodic Scheduled Task, e.g.:
REM   schtasks /Create /TN "OCTOPUS-Cortex-Revive" /SC MINUTE /MO 5 ^
REM     /TR "F:\backup\_ops\now_moves\RUN-CORTEX-REVIVE.bat --revive"
setlocal
cd /d "%~dp0"
if exist "F:\backup\_ops\OCTOPUS-flags.cmd" call "F:\backup\_ops\OCTOPUS-flags.cmd"
python -X utf8 cortex_symmetric_revive.py %*
endlocal
