@echo off
REM owner-ping — پیامِ متنی به تلگرامِ مالک. هیچ مقداری echo نمی‌شود.
REM استفاده: owner-ping.cmd <utf8-text-file> [topic_id]
setlocal
call "%~dp0..\OCTOPUS-flags.cmd" >nul 2>&1
python -X utf8 "%~dp0owner_ping.py" %*
endlocal
