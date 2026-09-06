---
name: octopus-business-legs-wiring
description: "پروتکل ایجنتِ وصل‌کردن پاهای بیزنسی اختاپوس (painting/ziman/studio روی سه‌برد 138/180/182) به لپ‌تاپ و برقراری خودمختاری امن با دکترین «هارمونی بقا». Triggerها: پاهای بیزنسی، اختاپوس، سه‌برد، 138/180/182، وصل به لپ‌تاپ، هارمونی بقا، READ-ONLY FIRST، NO APPROVE_ONCE، خودمختاری واقعی، laptop hop، split-brain، wrong-body، cognitive_wake، dead-letter، WAL gate، HOLD_EXTERNAL. این skill قبل از اثبات runtime-truth و receipt اجازهٔ هیچ wiring اجرایی یا ادعای autonomy نمی‌دهد؛ کار آن اول اندازه‌گیری، طبقه‌بندی، طراحی fail-closed و ساخت dry-run است."
metadata:
  version: '1.0'
  author: armin
  perplexity:
    connectors:
      - id: github_mcp_direct
        reason: خواندن وضعیت PRها و drift مخزن ofn-node به‌صورت فقط‌خواندنی قبل از هر wiring.
---

# وصل‌کردن پاهای بیزنسی اختاپوس به لپ‌تاپ + خودمختاری امن

> **پروونانس (2026-09-03):** این مهارت را مالک ساخت و نشست موازی کامپایل کرد؛
> بازرسی مستقل (ایجنت مقیم): دقیقاً ۳ فایل مطابق ادعا، پاک از راز.
> بهداشتی‌سازی برای انتشار عمومی: ایمیل مالک → `owner-email (vault: ZIMAN-SEASON)`
> (دامنه می‌مانَد؛ در PR #140 عمومی است) · اصلاح گلیچ عنوان «##何时» → «## چه زمانی».
> مرحلهٔ قرنطینهٔ VBAA: `SAFETY_CASED`؛ پس از رأی معتبر GOV-V6 → `OWNER_ATTESTED`.


## چه زمانی از این skill استفاده کن

وقتی کاربر می‌خواهد یکی از این‌ها را:

- پاهای بیزنسی اختاپوس (painting / ziman gift / studio) را به لپ‌تاپ وصل کن
- خودمختاری واقعی در پاهای بیزنسی برقرار کن (نه نمایشی)
- حلقهٔ سه‌برد 138/180/182 را به لپ‌تاپ وصل کن («laptop hop» / «Windows hop»)
- «هارمونی بقا» را پیاده یا بررسی کن
- گیت‌های WAL / HOLD_EXTERNAL / APPROVE / dead-letter را بسنجد یا ببندد
- drift بین مخزن و مش runtime را پیدا کند
- قبل از اعلام autonomy، یک dry-run فقط‌خواندنی بسازد

اگر درخواست شامل هرگونه اقدام خارجی (send / publish / price / ads / restart / kill / secret) است، این skill **ممنوع** می‌کند مگر پشت گیت انسانی.

---

## دکترین: «هارمونی بقا»

```text
کم‌رویداد
یک مغز
دو شاهد
خواب وقتی کار کامل نیست
مشغول‌بودن زنده‌ماندن نیست
```

خودمختاری امن = حلقهٔ «حس → تشخیص → پیشنهاد → verify → کارت → رسید» خودش بچرخد؛ ولی money/price/ads/publish/send/contact/secrets/restart/kill/policy پشت گیت انسانی بماند. هدف «وصل‌کردن» یعنی: لپ‌تاپ می‌شود آینهٔ فقط‌خواندنیِ رسیدها + سطح APPROVE مالک + کتابخانهٔ کد — **نه** یک نود تصمیم‌گیر زنده در مش (وگرنه همان خطای split-brain / wrong-body).

---

## قوانین آهنین (تغییرناپذیر)

```text
- فقط READ-ONLY. هیچ APPROVE_ONCE.
- هیچ external action: send, contact, publish, price change, ads/budget, restart, kill, secret-read.
- هر چیزی UNKNOWN است تا رسید داشته باشد. بدون رسید = LIVE فرض نکن.
- بدون consumer، یک قابلیت «کار نمی‌کند».
- اگر دیتا ناقص است، سیستم باید بخوابد، نه حدس بزند.
- راز فقط دست مالک. ساخت/چرخش کلید فقط با اجازهٔ مالک.
- لپ‌تاپ نباید خودش را به‌جای برد ببیند (جلوگیری از split-brain / wrong-body).
```

**ضدلغزش:** این skill قبل از اثبات runtime-truth و receipt اجازهٔ هیچ wiring اجرایی یا ادعای autonomy نمی‌دهد؛ کار آن اول اندازه‌گیری، طبقه‌بندی، طراحی fail-closed و ساخت dry-run است.

---

## نقش نودها (با شاهد تأیید کن)

| نود | نقش |
|------|------|
| 138 | gateway / supervisor / telegram card / owner gate / متابولیسم (قلب همیشه‌بیدار) |
| 180 | brain / decision / rank / proposal (مغز — لاما محلی، کلود لازم نیست) |
| 182 | witness / verify / NATS / receipts (حس/شاهد) |
| لپ‌تاپ | آینهٔ فقط‌خواندنیِ رسیدها + سطح APPROVE + vault + کتابخانهٔ کد (نه نود تصمیم‌گیر زنده) |
| گیت‌هاب | حاکمیت (مستقل از هر میزبانی) |

> تعریف «خودمختاری واقعی» از نظر مالک: حلقه تا جایی بدون APPROVE بچرخد که فقط کارهای فقط‌خواندنی/طرح‌پیشنهاد/verify/رسید باشد؛ هر چیزی خارجی یا حساس = گیت مالک.

---

## قالب پاسخ اجباری برای هر ادعا

هر بند پاسخ باید دقیقاً این ساختار را داشته باشد؛ بدون شاهد = `UNKNOWN`:

```text
id:
claim:
node_id:
command / read_method:
output_excerpt:
evidence_path:
sha256_or_commit:
timestamp_utc:
status: LIVE | BLOCKED | PARKED | UNKNOWN | BROKEN | OWNER_DECISION
risk:
next_smallest_safe_step:
```

قانون: اگر receipt نیست → status باید `UNKNOWN` یا `BLOCKED` باشد، نه `LIVE`.

### دو محور متعامد وضعیت (اصلاح دکترین F1، 2026-09-03)

واژگان تک‌محوری کافی نیست — یک چیز می‌تواند هم‌زمان بی‌سیم و منتظر رأی باشد:

```text
f1_status  : LIVE | PRESENT_UNWIRED | STALE | NOT_FOUND | UNKNOWN   ← هستی و سیم‌کشی
gov_status : OPEN | BLOCKED | PARKED | OWNER_DECISION | BROKEN      ← حاکمیت
```

قواعد قفل‌شده:
- بدون رسید ⇒ `f1_status=UNKNOWN`، هرگز `LIVE`
- `readers` خالی ⇒ `f1_status=PRESENT_UNWIRED` (همان «بی‌خواننده»ها: گزارش دکتر، BrainPort، board_events، …)
- قرارداد ماشینی این دو محور: `contracts/runtime_truth_v1.py` (فریزشده با FROZEN.lock)

---

## ترتیب کار (ممنوع‌البرعکس)

```text
۱. حقیقت و رسید           → first
۲. بستن dead-letter و drift → second
۳. سیم‌کشی                 → third
۴. dry-run بدون اثر خارجی → fourth
۵. تازه بعد: خودمختاری     → last
```

برعکس کردن این ترتیب ممنوع است. تا ۷ خروجی با شاهد نیامده، هیچ سیم‌کشی اجرایی، approve، publish، send، ads، price change، restart یا secret action انجام نشود و «خودمختاری» اعلام نشود.

---

## مرز autonomous / owner-only

**autonomously مجاز:**
read-only scan · classify/rank gaps · generate proposal · prepare card · verify with witness · write local receipt · dry-run repair (با whitelist و dry_run=true پیش‌فرض)

**owner-only (fail-closed):**
money · approve_once · price change · ads budget/spend · publish to Google/Shopify/external · send/contact · secrets/keys · restart/kill/service control · policy change · SSH key creation/rotation

> این owner-onlyها باید در کد enforce شوند (file/function/flag). در گزارش بنویس کجا و آیا مسلح است یا خلع‌سلاح.

---

## ۷ خروجی اجباری قبل از هر wiring

1. `BUSINESS-LEGS-RUNTIME-TRUTH.md` (حقیقت runtime هر نود)
2. `THREE-BOARD-COMM-MAP.md` (نقشهٔ ارتباط سه‌برد)
3. `BUSINESS-LEGS-BLOCKERS.md` (وضعیت سه پا با فیلدهای BLOCKED)
4. `LAPTOP-CONNECTION-DESIGN-READONLY-FIRST.md` (طراحی اتصال فقط‌خواندنی)
5. `OWNER-DECISIONS-NEEDED.md` (حداکثر ۱۱ آیتم — چیز دیگری اختراع نکن)
6. `AUTONOMY-DRY-RUN-PLAN.md` (تست پذیرش بدون اثر خارجی)
7. `DO-NOT-TOUCH.md` (همهٔ forbiddenها)

---

## تست پذیرش (dry-run) قبل از اعلام خودمختاری

```text
synthetic business signal
→ 138 creates cognitive_wake.v1
→ 180 ranks/decides (proposal only)
→ 182 verifies PASS/FAIL
→ 138 owner card با HOLD_EXTERNAL
→ laptop read-only mirror دریافت می‌کند
→ owner decision path دیده می‌شود ولی اجرا نمی‌شود
→ receipt روی همهٔ نودهای درگیر نوشته می‌شود
```

شرط قبولی:
1. node_id در همهٔ receiptها هست
2. SHA/branch runtime معلوم است
3. هیچ external action انجام نشده
4. دیتای ناقص = خواب، نه حدس
5. owner-only actions fail-closed
6. laptop دچار wrong-body نمی‌شود
7. هیچ queue در dead-letter نمی‌ماند یا صادقانه BLOCKED گزارش می‌شود

---

## اگر ابزار SSH / برد / گیت‌هاب در دسترس نیست

این skill حدس نمی‌زند. وقتی دسترسی هست:
- status را `UNKNOWN` یا `BLOCKED` بزن.
- دقیقاً بنویس چه read-only measurement لازم است تا همان بند به `LIVE` برسد.
- `next_smallest_safe_step` را صریح بگو.
- هرگز مقدار راز یا کلید نخواه؛ فقط نقشهٔ «کدام توکن کجا زندگی می‌کند».

---

## فهرست کامل سؤال‌ها و چک‌لیست

دو فایل مرجع را دقیقاً وقتی که به آن بخش کار می‌رسد بخوان — کل را هم‌زمان در context نگیر:

- `references/full-question-set.md` — فهرست کامل بخش‌های A تا K: حقیقت runtime نودها، نقشهٔ مش، سه پای بیزنسی، طراحی اتصال لپ‌تاپ، گیت‌ها، هارمونی بقا، دیتابیس/رسید، GitHub/drift، تصمیم‌های مالک، و خروجی‌ها. این را قبل از شروع کار با کاربر و در شروع هر بند بخوان.
- `references/first-session-checklist.md` — هفت گام نخستین نشست: establish root، clean/dirty boundary، runtime inventory، doctor freshness، targeted tests، write receipts، ask owner only if blocked.

---

## قانون نهایی

تا این ۷ خروجی با شاهد نیامده: هیچ سیم‌کشی اجرایی، approve، publish، send، ads، price change، restart یا secret action انجام نشود؛ و «خودمختاری» اعلام نشود.
