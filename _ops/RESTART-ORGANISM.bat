@echo off
echo.
echo   Restarting the organism so Telegram turns on.
echo.
echo   Step 1 of 2 - stopping the old organism...
powershell -NoProfile -ExecutionPolicy Bypass -File "F:\backup\_ops\stop-organism.ps1"
echo.
echo   Step 2 of 2 - starting it fresh with your Telegram token...
timeout /t 2 /nobreak >nul
start "" "F:\backup\_ops\RUN-ORGANISM.bat"
timeout /t 6 /nobreak >nul
echo.
echo   Done. A NEW black window should now be open and staying open.
echo   That new window IS the organism - leave it open.
echo   You can close THIS window now.
echo.
pause
