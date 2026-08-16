# Runbook — انحراف اسکیما (Schema Drift)

**وقتی:** بوت `SAFE MODE` می‌گوید با `schema:<name>(critical)`، یا preflight
ردیف drift نشان می‌دهد.

## معنی
- کد ستون/جدولی را انتظار دارد که فایل DB ندارد (یا برعکس).
- SAFE MODE عمدی است: نود باز می‌ماند ولی خروجی‌ها بسته می‌شوند.

## بررسی
```bash
cd /home/ari/ofn
python3 -m ofn.preflight 2>&1 | grep -i "schema\|critical"
```

## رفع
- اگر drift از یک migration جاافتاده است: migration تابعی اضافه کن
  (`apply_schema` با MIGRATIONS — مثل `_migrate_claimed_at`).
- اگر فایل قدیمی‌تر از کد است و migration ندارد: بنویس، بعد ری‌استارت.
- هرگز فایل `-wal`/`-shm` را دستی پاک نکن.

## تأیید
```bash
sudo systemctl restart ofn
python3 -m ofn.preflight          # بدون critical
journalctl -u ofn | grep "boot OK"
```

## هشدار
- `missing_columns` فقط جهت گم‌شده را گزارش می‌دهد — ستون اضافی بی‌اثر است.
- انحراف CRITICAL است چون هزینهٔ آن در دست شریک پرداخت می‌شود، نه در boot.
