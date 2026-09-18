# FINDINGS — دو نقص واقعی مسیر پول که حین رویدادسازی کشف و بسته شدند

لین: `09-LANES/EVENT-DRIVEN-OCTOPUS-20260918` · تاریخ کشف: 2026-09-18 ~09:05Z · همه با شاهد زنده روی board138.

هر دو نقص **پیش از این موج وجود داشتند** (نه ساختهٔ این مهاجرت) و هر دو در مسیر «موج تأییدشدهٔ مالک» قرار داشتند.

---

## F-1 — send_queue.py از 06:54Z هر اجرا کرش می‌کرد (کل ارسال قفل بود)

**شاهد:** `journalctl -u octopus-evt-send.service`:
```
File "/home/ari/ofn/state/revenue-drive/send_queue.py", line 124, in <module>
    for pk in (r.get("sent") or []):
TypeError: 'bool' object is not iterable
```
**ریشه:** رسیدِ `{"kind":"OWNER_BATCH_20260918B","sent":true}` (نوشته‌شده 06:54:05Z توسط لِین دیگر) — کد انتظار لیست داشت، بولی آمد. اسکنِ `already` روی **همهٔ** رسیدها اجرا می‌شود، پس از 06:54Z **هر** اجرای send_queue می‌مرد؛ یعنی تیک ۱۲:۰۰Z هم (که مالک برای موج تعیین کرده بود) بی‌صدا شکست می‌خورد.

**fix:** فقط وقتی فیلد واقعاً یک مجموعه است iterate شود (`isinstance(..., (list, dict, set, tuple))`).
پری‌ایمیج: `send_queue.py.pre-sentboolfix-20260918T090545Z`

---

## F-2 — موج مالک به اسپم تبدیل می‌شد: ۱۳۱ پکت برای ۵ گیرندهٔ تکراری

**شاهد (اندازه‌گیری زنده، 09:07Z):**
```
STAGED queue: packets=131 distinct_recipients=5
  info@absolutestrata.com.au      x33  Absolute Strata
  reception@alldiscox.com.au      x33  Alldis and Cox
  balmain@bcb.acebcm.com.au       x32  Ace Body Corporate Management
  info@acumenstrata.com.au        x19  Acumen Strata Management
  bcs_sydney@bcssm.com.au         x14  BCS Strata Sydney (PICA Group)
contacted(ever): 5   ← همان ۵
```
**ریشه (دو لایه):**
1. `money_executor.py` فقط با `quote-fingerprints.jsonl` فیلتر می‌کرد (۱ رکورد در کل تاریخ) ⇒ هر اجرا **همان ۵ لیدِ بالای رتبه** را برمی‌داشت، حتی اگر قبلاً ایمیل شده بودند.
2. شناسهٔ پکت از `abs(hash(name)) % 10000` ساخته می‌شد؛ `hash()` پایتون per-process تصادفی است ⇒ همان لید در هر اجرا پکت با **id تازه** می‌گرفت و دِداپِ id-محور هرگز آن را نمی‌دید.

**نتیجهٔ بالقوه:** ۲۵ ایمیلِ اولِ موج، ~۱۲ ایمیل به هر یک از ۵ کسب‌وکار بود (و ۶۰/روز کامل ⇒ ~۱۲×). دقیقاً همان تلهٔ «دِداپِ کلید خط‌محور = اسپم» ثبت‌شده در حافظهٔ پروژه.

**fix (سه لایه، همه افزودنی + رسید):**
1. **گارد گیرنده** در `send_queue.py`: ساخت مجموعهٔ «قبلاً ایمیل‌شده» از لجر ماندگار `lead-send-ledger.jsonl` + تاریخ `sent-log.jsonl`؛ هر پکت با گیرندهٔ تکراری بلاک و به `send-queue/terminal-dup/` پارک می‌شود (رسید `SEND_DEDUP_BLOCKED` + `SEND_DUP_PARKED`). ترتیب: گارد **قبل** از سقف بچ ۲۵ (وگرنه ۱۳۱ دِداپ جلوی پکت‌های تازه را می‌گرفت).
2. **فیلتر لید تازه** در `money_executor.py`: لیدهایی که گیرنده‌شان قبلاً ایمیل شده از `todo` حذف می‌شوند + رسید `EXECUTOR_NO_FRESH_LEAD` وقتی چیزی نماند.
3. **id قطعی**: `QP-<date>-<sha256(name)[:6]>` ⇒ تهیهٔ دوباره idempotent است و پکت تکراری نمی‌سازد.

**پاک‌سازی با رسید:** ۱۳۱ پکت تکراری از `send-queue/` و ۱۳۲ از `quote-packets/` به `terminal-dup-20260918/` منتقل شدند (رسیدهای `SEND_QUEUE_DUP_CLEANUP` + `PACKET_POOL_DUP_CLEANUP`؛ rollback = برگرداندن فایل‌ها).

**اثبات پس از fix (dry-run واقعی، بدون ارسال):**
```
{"DRY_RUN": true, "would_send": ["QP-20260918-292f10","QP-20260918-52c267","QP-20260918-ebe689"], ...}
```
یعنی ۳ پکتِ **تازه** (Bart Strata / Bright and Duggan / Bond Services) آمادهٔ ارسال شدند و دِداپ‌ها بلاک.

**تذکر باقی‌مانده (صادقانه):** صفِ قدیمی بر پایهٔ رتبهٔ ۵ لیدِ اول ساخته شده بود؛ پکت‌های زیمان/نقاشی برای ۶۳ لید تازهٔ بعدی باید به‌تدریج ساخته شوند (هر اجرا ۵ پکت، ۲ تا بدون ایمیل ⇒ نیازمند enrich). این در LANE-REPORT به‌عنوان کار باقی‌مانده ثبت شده است.
