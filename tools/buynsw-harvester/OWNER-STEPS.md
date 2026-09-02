# بستهٔ خر-پروف — راه‌اندازی پل buy.nsw (نسخهٔ 0.2 — از ۲ سپتامبر ۲۰۲۶)

هر خط = یک دستور کامل. کپی → Paste → Enter. **خروجی هر مرحله را برای ایجنت بفرست (انگار خرم).**
هیچ خطی را جمع نکن، اگر جا افتاد همان شماره را بگو تا دقیق همان را بدهم.

وضعیت فعلی (کارهای ایجنت — انجام شده):
- نسخهٔ 0.2 = ادغام پکیج «buysw-harvester-for-ari» (بازیابی از Temp) با پل فایلی؛
  تست ۲۶/۲۶ سبز (روی board138 هم سبز)
- PR #84 باز است: https://github.com/ari-OCTOPUS/ofn-node/pull/84
- روی board138 پوشهٔ `/home/ari/wt-buynsw-ingest` آمادهٔ اجراست (به نودِ در حال اجرا دست نزدهایم)

---

## بخش A — روی کامپیوتر سیدنی که Chrome دارد (فقط بار اول)

### A1. دانلود پوشهٔ اکستنشن (PowerShell روی همان کامپیوتر)

```powershell
Invoke-WebRequest -Uri https://github.com/ari-OCTOPUS/ofn-node/archive/refs/heads/fix/demand-harvest.zip -OutFile $env:USERPROFILE\Desktop\buynsw.zip
```

⚠️ اگر ۴۰۴ داد، آدرس درست از PR #84 کپی کن (دکمهٔ Code → Download zip).

```powershell
Expand-Archive -Path $env:USERPROFILE\Desktop\buynsw.zip -DestinationPath $env:USERPROFILE\Desktop\buynsw -Force
```

✅ بررسی: باید پوشهٔ `Desktop\buynsw\ofn-node-fix-demand-harvest\tools\buynsw-harvester` وجود داشته باشد که داخلش `manifest.json` است.

### A2. نصب در Chrome (با موس، دستور ندارد)

1. Chrome را باز کن → در نوار آدرس بنویس: `chrome://extensions` → Enter
2. کلید **Developer mode** (بالا-راست) را روشن کن
3. دکمهٔ **Load unpacked** → پوشهٔ `buynsw-harvester` را از مسیر A1 انتخاب کن
4. آیکون اکستنشن (پازل-شکل، کنار نوار آدرس) را با سنجاق 📌 پین کن

✅ بررسی: آیکون «OFN buy.nsw Harvester» در نوار ابزار دیده می‌شود.

---

## بخش B — اولین برداشت + دامپ دیباگ (روی کامپیوتر سیدنی)

### B1. صفحهٔ نتایج buy.nsw را باز کن

در همان Chrome برو به صفحهٔ جستجوی مناقصه‌ها (مثلاً `buy.nsw.gov.au` → مناقصه‌ها/Opportunities → نتایج).

### B2. دامپ دیباگ (فقط بار اول — برای قفل‌کردن سلکتورها)

روی آیکون اکستنشن بزن → دکمهٔ **«دامپ دیباگ DOM»**.
فایل `buynsw-debug-….json` در Downloads ذخیره می‌شود.

✅ بررسی: در پنجرهٔ اکستنشن عدد `linkCount` را ببین و یادداشت کن.

### B3. برداشت

دکمهٔ **«برداشت از این صفحه»** را بزن. اگر چند صفحه نتیجه است: عدد کادر کنار
«خودکار» را بگذار (پیش‌فرض ۱۵) و **«شروع خودکار»** را بزن؛ هر وقت خواستی **«توقف»**.
نکتهٔ طلایی: روی صفحهٔ جزئیات هر مناقصه/جوایز (CAN) هم «برداشت» بزن — تماس‌ها و
تأمین‌کننده و ABN همان‌جا استخراج و با رکورد قبلی ادغام می‌شود.

### B4. خروجی نهایی

دکمهٔ **«خروجی JSON»** → فایل `buysw-leads-….json` در Downloads ذخیره می‌شود.

✅ بررسی: شمارش «کل بافر» باید بزرگ‌تر از صفر باشد.

### B5. این دو فایل را برای ایجنت بفرست

هم `buysw-debug-….json` و هم `buysw-leads-….json` (از Downloads).

---

## بخش C — ریختن بچ داخل نود (از هر کامپیوتری که به board138 دسترسی SSH دارد)

فقط به جای نام دقیق فایل دقت کن (تاریخ/ساعت داخل اسمش است).

### C1. فایل بچ را روی board138 بگذار

```powershell
scp $env:USERPROFILE\Downloads\buysw-leads-PUT-EXACT-NAME-HERE.json ari@192.168.0.138:/home/ari/
```

### C2. اجرای ingest (یک خط)

```powershell
ssh ari@192.168.0.138 "cd /home/ari/wt-buynsw-ingest && python3 tools/ingest_buynsw_batch.py /home/ari/buysw-leads-PUT-EXACT-NAME-HERE.json"
```

✅ بررسی: خروجی JSON باید `"status": "DONE"` داشته باشد با شمارش `"accepted"`, `"rejected_filter"`, `"rejected_dup"`, `"rejected_invalid"`.
کد خروج: `0` = موفق | `2` = بچ رد شد (هیچی نوشته نشده) | `1` = خطا.

❌ اگر پیام `database is locked` آمد: فقط یک بار دیگر C2 را اجرا کن.

---

## ❌ ممنوع‌ها

- ❌ روی board138 دست به branch اصلی (`release/p0`) یا ری‌استارت سرویس نزن — ingest از `wt-buynsw-ingest` اجرا می‌شود و کافی است.
- ❌ فایل بچ JSON را دستی ویرایش نکن.
- ❌ PR #84 را خودت merge یا close نکن — دروازهٔ بازبینی مستقل (Elahe-z) باید خودش کار کند.
- ❌ اسم فایل‌ها را دستی تایپ نکن — از اسم واقعی فایل ذخیره‌شده کپی کن.
- ❌ اگر EXIT=2 شد نگران نشو — یعنی بچ معتبر نبود و هیچ چیزی در DB نوشته نشده؛ فقط فایل و خروجی را بفرست.
