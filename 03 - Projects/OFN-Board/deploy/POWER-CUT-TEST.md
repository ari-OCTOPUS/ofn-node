---
tags: [ofn, ops, test]
aliases: [تست قطع برق]
updated: 2026-08-04
---

# تست واقعی قطع برق — روی خود برد

**پیوندها:** [[INDEX]] · [[APPLY]] · [[CHECKPOINT]]

> بدون این، نگو «کار می‌کند». همهٔ تست‌های ما شبیه‌سازی‌اند؛ این یکی واقعی است.

## قبل از شروع

```bash
cd ~/ofn && python3 -m pytest -q          # باید سبز باشد
python3 -m ofn.preflight                  # گزارش بوت
```

## آزمایش ۱ — ریبوت نرم

```bash
sudo systemctl restart ofn
sleep 5
journalctl -u ofn -n 20 --no-pager
```

✅ قبول: صفر داده گم‌شده، زنجیرهٔ لجر سالم، صفر ارسال تکراری.

## آزمایش ۲ — کشیدن برق (مهم‌ترین)

۱. چند رویداد بساز تا چیزی برای از دست دادن باشد.
۲. **کابل برق را بکش.** نه `shutdown` — واقعاً بکش.
۳. صبر کن ۱۰ ثانیه، دوباره وصل کن.
۴. بعد از بالا آمدن:

```bash
python3 -m ofn.preflight
sqlite3 ~/.local/share/ofn/ledger.sqlite 'PRAGMA quick_check;'
```

✅ قبول:
- `quick_check` جواب `ok` بدهد
- زنجیرهٔ لجر تأیید شود
- هر پیامی که وسط ارسال بود در وضعیت `held` باشد، **نه** `pending`
- هیچ پیامی دوبار نرفته باشد

❌ اگر `quick_check` شکست خورد: `python3 -m ofn.restore_job` و بعد گزارش بده.

## آزمایش ۳ — کشتن پروسه

```bash
sudo systemctl kill -s SIGKILL ofn
sleep 10
systemctl is-active ofn        # باید active باشد
```

✅ قبول: زیر ۶۰ ثانیه خودش برگردد.

## آزمایش ۴ — بازیابی واقعی

```bash
python3 -m ofn.backup_job
mv ~/.local/share/ofn/ledger.sqlite ~/ledger.broken
python3 -m ofn.restore_job
sqlite3 ~/.local/share/ofn/ledger.sqlite 'PRAGMA integrity_check;'
```

✅ قبول: `ok` و زنجیره تأیید شود.

## آزمایش ۵ — رم زیر بار

```bash
free -h
systemctl show ofn -p MemoryCurrent
```

✅ قبول: سه leg هم‌زمان، پیک زیر ۳٫۲ گیگابایت.

---

## ⚠️ چیزی که هیچ تنظیم نرم‌افزاری حل نمی‌کند

حافظه‌های فلش ارزان دربارهٔ `fsync` دروغ می‌گویند. یک garbage-collect نیمه‌کاره
می‌تواند تا ۶۴ مگابایت دادهٔ **بی‌ربط** را از بین ببرد — حتی داده‌ای که در آن
لحظه اصلاً باز نبوده.

یک ماژول سوپرکپسیتور یا UPS کوچک (۱۵ تا ۳۰ دلار) که ۲۰ ثانیه برق نگه دارد و
shutdown تمیز بزند، از همهٔ pragmaهای این پروژه با هم بیشتر ارزش دارد.
