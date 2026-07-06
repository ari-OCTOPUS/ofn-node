@echo off
REM میان‌بر در پوشهٔ Startup تا مغز از logon بعدی خودکار بالا بیاید.
set "VBS=%~dp0run-brain-hidden.vbs"
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Startup')+'\ZimanControlBrain.lnk'); $s.TargetPath='wscript.exe'; $s.Arguments='\"%VBS%\"'; $s.WorkingDirectory='%~dp0'; $s.Save()"
echo.
echo [OK] میان‌بر ساخته شد. از logon بعدی خودکار بالا می‌آید.
echo برای شروعِ همین حالا:  wscript "%VBS%"
pause
