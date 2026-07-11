@echo off
rem RUN-CODE-AUTONOMY.bat - درایورِ خودمختاریِ کد سطح A (زیرِ قانونِ قلب).
rem flag-off by design: بدونِ ACTIVATION-CODE-AUTONOMY.flag همه‌چیز no-opِ امن است.
rem kill switch: فایلِ F:\backup\_ops\STOP-CODE-AUTONOMY را بساز (توقفِ آنی).
rem این حلقه فقط approvalهای تأییدشدهٔ مالک را (بعد از تپِ ✅ در تلگرام) مصرف می‌کند؛
rem هر اعمال زیرِ ۷ گیت: فعال‌سازی + قلب≠freeze + تأیید + deny-list + سایهٔ سبز + refractory + canary.
rem اعمال فقط روی شاخهٔ کاری است؛ merge به masterِ زنده = گامِ جداگانهٔ مالک.
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d F:\backup\_ops
:loop
if exist "F:\backup\_ops\STOP-CODE-AUTONOMY" goto stopped
python -X utf8 cortex\code_autonomy.py run
echo code-autonomy exited - waiting 10 seconds ... press Ctrl+C twice to stop
timeout /t 10 /nobreak >nul
goto loop
:stopped
echo STOP-CODE-AUTONOMY flag found - driver ends here.
echo To run again: delete F:\backup\_ops\STOP-CODE-AUTONOMY then run this .bat.
