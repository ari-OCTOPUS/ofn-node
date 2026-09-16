@echo off
REM هر روز ساعت 09:00 یک بستهٔ DM و پست بساز.
schtasks /create /tn "ZimanDailyContent" /tr "\"%~dp0daily-content.bat\"" /sc daily /st 09:00 /f
echo [OK] تسکِ روزانه ثبت شد (09:00). حذف:  schtasks /delete /tn "ZimanDailyContent" /f
pause
