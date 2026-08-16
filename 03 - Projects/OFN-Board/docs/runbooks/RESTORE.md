# Runbook — بازیابی از پشتیبان (RESTORE)

**قانون اول:** بازیابی از یک پشتیبان تأییدنشده ممنوع است. `verify_backup` اول.

## پیش از هر چیز — metadata
```bash
stat -c '%a %U:%G %n' <backup-dir>     # 0700 · مالک درست · symlink نباشد
```
بازبینی پشتیبان: اول metadata، بعد محتوا — هرگز برعکس.

## مرحله ۱ — verify
```bash
cd /home/ari/ofn
python3 -c "from ofn.adapters.backup import verify_backup; print(verify_backup('<backup-dir>'))"
```
باید `(True, ...)` برگردد.

## مرحله ۲ — توقف سرویس
```bash
sudo systemctl stop ofn
```

## مرحله ۳ — بازیابی دیتابیس‌ها
```bash
python3 -m ofn.restore_job <backup-dir>   # اگر CLI هست؛ وگرنه با اسکریپت restore
```
مطمئن شو sidecar های `-wal`/`-shm` حذف شده‌اند (کد این کار را می‌کند).

## مرحله ۴ — بازیابی رسانه‌ها (اختیاری، فقط sandbox)
```bash
python3 -c "from ofn.adapters.backup import restore_media; print(restore_media('<backup-dir>', '<target>'))"
```
**بازیابی زندهٔ رسانه = عمل عمدی اپراتور با تأیید آری.** این runbook مسیر را
ثبت می‌کند، نه اجازهٔ اجرا را.

## مرحله ۵ — health
```bash
sudo systemctl start ofn
python3 -m ofn.preflight          # بدون critical
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8794/
```

## Rollback
DB حذف نمی‌شود — با `keep_corrupt_as` کنار گذاشته می‌شود. اگر restore خراب بود،
فایل کنار‌گذاشته‌شده را برگردان.
