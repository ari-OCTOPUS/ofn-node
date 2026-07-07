# ⚙️ همیشه‌روشن روی لپ‌تاپ (autostart)

مغزِ کنترل را طوری تنظیم می‌کند که **از هر بار روشن‌شدنِ ویندوز خودکار بالا بیاید**، حالتش را
**بیرونِ vault** نگه دارد (`%USERPROFILE%\.ziman-control`)، در `brain.log` لاگ کند، و اگر کرش کرد **خودش ری‌استارت** شود.

## راه‌اندازی (یک‌بار)
1. اول یک‌بار دستی تست کن که بالا می‌آید:
   `autostart\run-brain.bat`  → مرورگر: `http://127.0.0.1:8770`
2. برای خودکارشدن از logon:
   روی **`autostart\install-startup-shortcut.bat`** دابل‌کلیک کن.
   (یک میان‌بر در پوشهٔ Startup می‌سازد؛ بی‌پنجره در پس‌زمینه اجرا می‌شود.)
3. شروعِ همین‌حالا بدونِ ری‌استارت:  `wscript autostart\run-brain-hidden.vbs`

- **حذفِ خودکاراجرا:** `autostart\uninstall-startup-shortcut.bat`
- **لاگ:** `%USERPROFILE%\.ziman-control\brain.log`
- **دادهٔ حالت:** `%USERPROFILE%\.ziman-control\data\state.db` (بیرونِ vault ✅)

## محتوای روزانهٔ خودکار (اختیاری)
هر روز ۹ صبح یک بستهٔ DM و پست بساز:
- ثبت:  `autostart\install-daily-content.bat`  (تسکِ ویندوز «ZimanDailyContent»)
- حذف:  `schtasks /delete /tn "ZimanDailyContent" /f`
> نکته: تا کلیدِ Claude وصل نشده، خروجی offline (قالبی) است؛ با کلید، live.

## نکته‌ها
- برای «۲۴ساعته»: در تنظیماتِ Power ویندوز، Sleep را روی «Never» بگذار (وقتی به برق وصل است).
- روشِ جایگزینِ خودکاراجرا (به‌جای Startup): Task Scheduler → onlogon → `wscript.exe "…\run-brain-hidden.vbs"`.
- مرحلهٔ بعدِ واقعیِ «همیشه‌روشن» انتقال به یک **VPS** است؛ همین ساختار بدونِ تغییر آنجا هم کار می‌کند (`start.sh`).
