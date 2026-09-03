# [OWNER ORDER — THREE ACTIVE LANES ONLY / FOOD-FIRST ATTENTION BUDGET]
## 2026-09-03 (night AEST) · جایگزینِ فرمانِ ۱۱-لینه از دو مگاپرامپت ZCode

**مالک:** آری · **صادرکننده:** Perplexity Computer (اورکستراتور)
**پایه:** دو مگاپرامپت ZCode («اندام‌هایی که هیچ لینی نمی‌پرستارد» + «Attention-Debt/Blind-Spots») + مشاورهٔ معماری مفهومی (Food-First)
**اصل مادر:** شواهد نه ادعا · بهبود نه بازنویسی · حذف ممنوع · هر عدد = command + timestamp + exit code + SHA/path receipt

---

## حکم مالک

این دو مگاپرامپت ZCode **به‌عنوان backlog کورنقطه‌ها پذیرفته می‌شوند**، اما اجرای هم‌زمان ۱۱ لین **ممنوع** است. تا وقتی `verified_payment_count=1` نشده، فقط سه برش فعال است:

| کد | لین | چرا فعال است |
|---|---|---|
| **A** | R0 / Business-Identity | نزدیک‌ترین مسیر به `verified_payment_count: 0→1` |
| **B** | Pulse-IMAP / Board Diagnosis | کانال درآمد (imap ایمیل buy.nsw) ممکن است کور باشد؛ self-model هم unverifiable است |
| **C** | Queue-Hygiene / Attention Ledger | تنها لینی که باید صف تصمیم را **کم** کند، نه زیاد |

`#92` (PR امنیتی موجود، redaction) جداگانه از مسیر fast-lane عادی ادامه می‌یابد؛ لین تازه حساب نمی‌شود.

### همهٔ لین‌های زیر PARKED هستند (تا بعد از R0):

Durable Memory / Continuity-Proof (restore-drill قبلاً PASS شده؛ nightly verify بعداً) · Host Skeleton / Vault-Repo-Hygiene (attention-expensive، cleanup تصمیم‌ساز) · Frozen Legacy (romajan, Black Box — بعد از پول) · Mesh Health (۱۳۸/۱۸۰/۱۸۲ — مگر outage فعلی ثابت شود) · full Concept-Debt Census (فقط revenue-path slice الان مجاز است، نه کل) · Telegram/control-panel redesign (فقط inventory/design، کدنویسی بعد از R0)

### اصل فیلتر (برای هر کار آینده)

هر کار جدید باید یکی از این سه را کم کند:
- `revenue_distance`
- `risk`
- `owner_attention_cost`

اگر هیچ‌کدام را کم نمی‌کند: **BACKLOG, no execution.**

---

## قواعد مشترک سخت (نقض = توقف لین)

۱. شواهد نه ادعا — هر یافته با فرمان منبع‌دار.
۲. حذف ممنوع — فقط بایگانی با manifest، پس از رأی.
۳. هیچ ارسال بیرونی (ایمیل/پیام/پرداخت) توسط ایجنت.
۴. هیچ merge/self-merge — ادغام فقط با `mergeable_state=clean` + انسان.
۵. هیچ restart/kill/bind/systemd-edit بدون رأی جداگانهٔ مالک با شاهد (R4).
۶. هیچ re-arm/WAL/flag بدون فرمان کامل + رسید.
۷. هیچ حدسِ ABN، بیمه، supplier-status یا قیمت.
۸. راز فقط نام؛ محتوای بک‌اسلش‌دار فقط با ابزار Write/Edit.
۹. تناقض با سند/رأی قبلی → ثبت CONTRADICTIONS با شناسه، نه بحث یا حذف بی‌صدا.
۱۰. **هر خروجی رأی‌خواهِ لین A و B باید از مسیر لین C (Queue-Hygiene) عبور کند** — مستقیم به مالک نرود.
۱۱. **کل موج، نه هر لین، حداکثر یک بستهٔ رأی‌خواه در روز دارد؛ حداکثر ۵ آیتم.**
۱۲. هر لین پیش‌فرض خروجی‌اش **گزارش عددیِ بدون رأی** است؛ رأی‌خواهی فقط برای عمل برگشت‌ناپذیر.

---

## لین A — R0 / Business-Identity

**هدف:** نزدیک‌ترین مسیر به `verified_payment_count: 0 → 1`.

```text
وظیفه:
1. draft DET NSW را بخوان (docs/lanes/ECONOMIC-LEARNING/DRAFT-REPLY-det-nsw-2026-09-02.md).
2. missing fields را استخراج کن:
   - ABN
   - insurance
   - supplier registration / buy.nsw / SCM0256
   - references
   - price / quote amount (QT-20260902-001)
   - contact identity
3. هیچ مقدار را حدس نزن.
4. هیچ ایمیلی ارسال نکن؛ هیچ send_authorized تولید نکن.
5. quote بی‌قیمت QT-20260902-001 را به‌عنوان revenue blocker رسمی ثبت کن.
6. یک پاسخ‌نامهٔ ناقص اما آمادهٔ تکمیل بساز با:
   - fields_missing
   - fields_owner_must_supply
   - suggested price slots
   - risk notes
7. فقط owner-action list بده؛ اجرای ارسال فقط با دست مالک.
8. خروجی رأی‌خواه را مستقیم به مالک ندهی؛ به لین C (Queue-Hygiene) بده.

خروجی:
R0_BUSINESS_IDENTITY_REPORT.md
DET_DRAFT_PATH=
MISSING_FIELDS=
PRICE_REQUIRED=yes/no
OWNER_ONLY_ACTIONS=
VERIFIED_PAYMENT_COUNT=0
NEXT_OWNER_ACTION=
```

---

## لین B — Pulse-IMAP / Board Diagnosis

**هدف:** تشخیص فقط‌خواندنی اینکه چرا کانال درآمد/ایمیل و پنج پروسهٔ self-model دیده نمی‌شوند.

```text
وظیفه:
1. فقط‌خواندنی بررسی کن:
   - octopus-imap.service (اولویت اول — کانال ایمیل buy.nsw)
   - octopus-heartbeat.service
   - پورت‌های 8771, 8772, 8773, 8774, 8776
2. برای هر unit فقط این دستورها مجاز است:
   - systemctl status <unit>
   - systemctl cat <unit>
   - journalctl -u <unit> --no-pager | tail -50
   - ss -tlnp
   - ps فقط خواندنی
3. هیچ restart/kill/bind/systemd-edit انجام نده.
4. جدول آشتی بساز: «نسل mesh پنج‌عضوی» در برابر «runtime فعلی بورد» — کدام سرویس جایگزین کدام شده.
5. علت‌های محتمل را رتبه‌بندی کن:
   - never-started
   - crashed
   - wrong bind/interface
   - replaced by newer service
   - missing unit
   - expected-port obsolete
6. برای هر remediation فقط پیشنهاد بده (بدون اجرا):
   - enable/start
   - replace mapping
   - retire/document
   - keep-unverifiable
7. هر ریشه‌یابی یک رسید jsonl با sha256.
8. خروجی رأی‌خواه را مستقیم به مالک ندهی؛ به لین C بده.

خروجی:
PULSE_IMAP_DIAGNOSIS.md
MISSING_PROCESSES=
IMAP_STATUS=
HEARTBEAT_STATUS=
PORT_LISTENERS=
ROOT_CAUSE_RANKED=
REMEDIATION_OPTIONS_AWAITING_OWNER=
NOTHING_RESTARTED=yes
```

---

## لین C — Queue-Hygiene / Attention Ledger

**هدف:** صف تصمیم مالک را **کم** کند، نه زیاد. این لین reducer است، نه producer.

```text
وظیفه:
1. تمام ورودی‌ها را یکی کن:
   - PRهای باز (#70,#71,#72,#73,#76,#77,#82,#83,#84,#85,#87,#88,#92 ...)
   - OWNER-DECISION-QUEUE
   - VERDICT_QUEUE
   - GAPS-100
   - D-34 open decisions
   - backlogهای doctor(21)/economic
   - خروجی لین‌های A و B همین موج
2. برای هر آیتم این ستون‌ها را بساز:
   - id
   - source
   - age_days
   - owner_only (yes/no)
   - risk_tier (fast/slow/irreversible)
   - revenue_distance (R0/R1/R2/R3)
   - stale (yes/no، با measured_at + ttl)
   - recommended_default_if_silent
   - evidence_path
3. آیتم‌ها را با سن × اثر × ریسک مرتب کن.
4. بستهٔ نهایی مالک بساز: **حداکثر ۵ آیتم کل** (نه ۵ از هر لین).
5. هیچ تصمیمی نگیر؛ فقط بستهٔ رأی بساز.
6. هر آیتم = یک فرمان PowerShell تک‌خطی بدون گیومهٔ داخلی + خط راستی‌آزمایی + ❌ ممنوعه‌ها.

خروجی:
ATTENTION_LEDGER.jsonl
OWNER_DAILY_PACKET.md
PARKED_LANES.md
QUEUE_COUNTS=
OWNER_PACKET_ITEMS_MAX_5=yes
```

---

## تعریف پایان موج

```text
DONE وقتی:
- هیچ لین بیشتر از یک گزارش نداده.
- فقط Queue-Hygiene (لین C) بستهٔ رأی مالک ساخته.
- بستهٔ مالک ≤۵ آیتم است، نه سه بسته از سه لین.
- R0 blocker (قیمت QT-20260902-001 + missing fields DET) دقیقاً مشخص است.
- IMAP/heartbeat/ports فقط تشخیص داده شده‌اند، نه درمان.
- هیچ‌کدام از هشت لین پارک‌شده (Durable Memory, Continuity-Proof, Host Skeleton,
  Vault/Repo Hygiene, Frozen Legacy, Mesh Health, full Concept Census,
  Telegram/panel redesign) اجرا نشده‌اند.
```

---

## استعارهٔ نهایی

دو مگاپرامپت ZCode درست دیدند که نیمی از اختاپوس در تاریکی مانده — میزبان ویندوزی، دوقلوهای منجمد، هویت حقوقی، صف‌های پیر. اما درمانِ «کورنقطهٔ توجه»، ساختن ۱۱ بیمارستان تازه نیست؛ **یک قیف** است که همه‌چیز را به یک بستهٔ کوچک تبدیل می‌کند. تا اختاپوس اولین لقمهٔ پول واقعی را هضم نکند، هیچ اندام تازه — حتی اندام‌های «پرستاری» — حق ساختن ندارد.
