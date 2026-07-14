@echo off
powershell -NoProfile -Command "Remove-Item ([Environment]::GetFolderPath('Startup')+'\ZimanControlBrain.lnk') -ErrorAction SilentlyContinue"
echo [OK] خودکاراجرا حذف شد.
pause
