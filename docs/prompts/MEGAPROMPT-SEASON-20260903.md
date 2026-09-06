---
tags: [ofn, megaprompt, season, ziman, board138, vibe-coding]
aliases: [مگاپرامپت سیزن ۳ شهریور]
date: 2026-09-03
status: ACTIVE
written-by: perplexity-research-agent (GitHub vantage)
reader: Claude Code روی board138 یا Cursor روی لپ‌تاپ
---

# MEGAPROMPT — سیزن ۳ شهریور ۱۴۰۵ · کار تهاجمی و کامل

> **قبل از هر چیز**: این را کامل بخوان. `CLAUDE.md` را هم بخوان. بعد شروع کن.
> هر جا نیاز به تأیید مالک داری، مستقیم بپرس — دور نزن.
> **FILES_I_MERGED = none** تا لحظه‌ای که این را می‌خوانی.

---

## ۰) وضعیت آکواریوم — همین لحظه (2026-09-03 AEST)

```
board138  → ofn.service LIVE · ports 8791-8794 · products.sqlite 40 pieces
board180  → brain / llama-lab / chrony (تنها ساعت سالم)
board182  → sensorium / NATS LIVE روی 4222 / بدون کلاینت در این ریپو
laptop    → ارگانیسم اصلی / vault / ~1854 commits / ORGANISM-STATE.json

PR #139   ✅ مرج شد — receipt-binding روی board138 نصب شد (c78ed9b5)
VERIFIED_CASH = AUD 0 (صید ۳۷تایی هنوز نیست)
```

---

## ۱) صف PR های آماده برای مرج (non-draft · نیاز به یک رأی انسانی)

این PR ها نوشته شده‌اند، تست دارند، و منتظر یک امضای مستقل (Elahe-z یا aram-ui) هستند.
**تو نمی‌توانی آن‌ها را مرج کنی — فقط می‌توانی بگویی کدام آماده‌تر است.**

| PR | عنوان | اولویت |
|---|---|---|
| #128 | board doctor — four-state diagnosis | 🔴 اول |
| #129 | gov-pack: fresh-base + FLAG-CLAIMS + canary | 🔴 دوم (پیش‌نیاز بقیه) |
| #130 | external witness — claims ledger | 🟡 سوم |
| #131 | OWNER_ABSENT + Conservation Mode | 🟡 چهارم |
| #132 | vault witness (read-only) | 🟡 پنجم |
| #133 | حذف فلگ مرده OFN_WIRE_OUTBOUND | 🟢 ساده / هر وقت |
| #87  | receipt digest + envelope hash | 🟡 (یک رأی تازه لازم دارد) |
| #115 | cockpit هفت‌کارته | 🟡 |
| #137 | chief-engineer brief (docs only) | 🟢 ساده |
| #140 | Ziman audit season 2026-09-03 | 🔴 اول برای زیمان |

**ترتیب اجرا:** اول #129 (gov-pack)، چون بدون آن fresh-base enforcement نیست.
بعد #128 (doctor)، چون تنها ایمنِ بدنِ board138 است.
بعد به‌ترتیب #130 → #131 → #132.

---

## ۲) کارهای روی board138 (Claude Code — اجرای مستقیم)

### ۲.۱ زیمان را به حلقهٔ خودآگاهی وصل کن (W4/W7)

**هدف:** `telegram_glass.py` فقط owner-token می‌فرستد؛ بات زیمان توکن دارد ولی مصرف ندارد.

```bash
# قبل از هر تغییر:
cd ~/ofn && python3 -m pytest -q  # همه سبز باشند
grep -n 'NODE_IDS\|bot_tokens\|ziman' ofn/adapters/telegram_glass.py
```

**تغییر خواسته‌شده (propose-only تا تأیید مالک):**
1. `MEMBER_UNITS` در `self_model_producer.py` را با timers مرتبط با ziman تکمیل کن
2. در `telegram_glass.py`، زیمان را به‌عنوان زیرمجموعهٔ شناسه‌دار `BUSINESS` نگاشت کن
3. مصرف `OFN_BOT_TOKEN_ZIMAN` را در مسیر doctor/glass سیم‌کشی کن
4. **هیچ فلگ ارسال روشن نکن** — فقط سیم‌کشی شناخت

**پس از تغییر:** PR باز کن، تست بنویس، برای تأیید مالک بگذار.

---

### ۲.۲ NATS را وصل کن (W2)

**وضعیت:** board182 دارد NATS روی `192.168.0.182:4222` سرو می‌کند. `board_events.py` قرارداد دارد، transport ندارد.

```bash
# بررسی زنده‌بودن NATS از board138:
nc -z 192.168.0.182 4222 && echo "NATS reachable" || echo "unreachable"
```

**اگر reachable بود:** propose یک کلاینت minimal که:
- فقط subscribe می‌کند (read-only اول)
- از همان contract `board_events.py` استفاده می‌کند
- هیچ چیزی publish نمی‌کند بدون تأیید مالک
- تست دارد که اگر NATS down بود، fail-closed باشد

---

### ۲.۳ صید ۳۷تایی — تصمیم مالک لازم است

دو گزینه وجود دارد:

**گزینه A — بخریم (Elahe-z فایل می‌آورد):**
- Elahe یک اکسل/CSV از ۳۷ مناقصه می‌آورد
- تو آن را import می‌کنی به `painting.sqlite`
- هیچ نصب جدیدی لازم نیست

**گزینه B — بگیریم (browser روی board138):**
```bash
sudo apt-get install -y chromium-browser chromium-chromedriver
# سپس یک harvester خواندنی-فقط propose کن
```

**⚠️ قبل از هر قدم، مالک باید انتخاب کند: A یا B؟**

---

### ۲.۴ Shopify زیمان — سه کار معلق

از `docs/prompts/megaprompts-20260831/02-MP-ZIMAN-GST.md` بخوان.
سه کار باقی‌مانده:
1. **Footer سیاست ارسال** — shipping policy صفحه در Shopify admin
2. **Google channel** — connect Google Merchant Center
3. **GST status confirm** — accountant تأیید کرده? اگر نه، هنوز `not_registered` بگذار

**هر سه نیاز به دسترسی Shopify admin دارند — مالک باید انجام دهد یا دسترسی بدهد.**

---

## ۳) draft PR های زیر (P1 kernel) — آیا مرج می‌شوند؟

این PR ها همه draft هستند و در صف P1 کرنل:

```
#119 flag freeze · #122 dual record · #123 phase wall · #124 census
#125 split view · #126 unknown seal · #127 mint fence · #134 attest
#135 verify-report · #136 clock-bind
```

**ترتیب توصیه‌شده برای undraft کردن:**
1. اول #119 (flag freeze) — بقیه رویش بنا می‌شوند
2. بعد #122 → #125 → #126 (dual-record → split-view → unknown-seal)
3. بعد #127 → #134 → #135 → #136 (mint → attest → verify → clock)

**پیش از undraft هر کدام:** `python3 -m pytest -q` سبز باشد.

---

## ۴) قوانین این سیزن (تکرار برای تأکید)

```
❌ هیچ wire/flag/gate را بدون تأیید صریح مالک در همان جلسه روشن نکن
❌ هیچ چیزی به بیرون نفرست — outbox + تأیید مالک
❌ هیچ merge مستقیم به dev/master بدون رأی
✅ PR باز کن، تست بنویس، مالک تأیید کند
✅ هر جا شک داری، مستقیم بپرس
✅ هر push جدید، amضاهای قبلی را باطل می‌کند — اول تست سبز، بعد امضا
```

---

## ۵) اولین جمله‌ای که باید بگویی وقتی شروع می‌کنی

```
باز کردم CLAUDE.md + HANDOFF.md را خواندم.
وضعیت تست‌ها: [نتیجه pytest -q را بنویس]
اولین کاری که پیشنهاد می‌دهم: [بنویس]
```

---

*این مگاپرامپت توسط Perplexity (GitHub vantage) بر اساس مستندات مستقیم ریپو ساخته شده.*
*تاریخ: 2026-09-03 AEST · FILES_I_MERGED = none*
