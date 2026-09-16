---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, migration, beat-lease, arm1]
created: 2026-08-16
updated: 2026-08-16
created_by: agent
sources:
  - "[[../../06-EVIDENCE/BEAT-OWNERSHIP-LEASE-2026-08-16]]"
  - "[[56-OCTOPUS-V3-FREEDOM-P0-2026-08-16]]"
  - "[[../../00 - Inbox/2026-08-16 DISCOVERY — Laptop to Arm1 Migration]]"
  - "[[58-FPGA-REFLEX-LAYER-2026-08-16]]"
  - "[[60-THREE-BOARD-AND-FPGA-CORRECTED-2026-08-16]]"
---

# ۵۷ — مهاجرت: مالکیت حقیقت، نه کپی پوشه

نوت ۵۶ = overlay آزادی/P0. این نوت = رودمپ مهاجرت. نوت ۰۵ تاریخی است. FPGA: [[58-FPGA-REFLEX-LAYER-2026-08-16|۵۸]] · سه برد فیزیکی: [[60-THREE-BOARD-AND-FPGA-CORRECTED-2026-08-16|۶۰]].

## جملهٔ اصلی

**تو کد را منتقل نمی‌کنی، مالکیت حقیقت را منتقل می‌کنی.**

الان لپ‌تاپ چهار نقش دارد: منبع حقیقت، اجراکننده، مغز، ابزار توسعه. مقصد:

```text
منبع حقیقت  → Arm 1 (state) + Arm 2 (شاهد لجر)   ← همیشه روشن
اجرا        → Arm 1 و Arm 3
مغز         → API بیرونی، فقط از Arm 1
توسعه       → لپ‌تاپ = کلاینت، نه قلب
legs بیزنسی → همان برد، از Arm 1 دستور می‌گیرد
```

تعریف پایان: لپ‌تاپ را ببندی و هیچ اتفاقی نیفتد.

## سه برد روی میز (۲۰۲۶-۰۸-۱۶ شب)

| فیزیکی | فاز | قانون |
|---|---|---|
| پاهای بیزنسی روشن | M4 | beat نزن؛ کلید مغز نگیر |
| خالی ۱ | M1 شاهد لجر | killswitch کپی نکن |
| خالی ۲ | M2→M3 Arm 1 | اول سایه، بعد lease |
| ۲× Artix-7 200T | M5 | PolarFire نیست؛ ترمز است |

جزئیات و رد پیست Deep Research: نوت ۶۰. تا M0 اسکن Windows، هیچ rsync.

## YOU ARE HERE

```text
[x] فاز ۰  fencing lease روی دیسک، unarmed     ← اینجا (کد + ۱۷ تست + CLI)
[ ] M0     بازرسی (hardcode/CRLF/case) + نقشهٔ اسرار + smoke + git tag
[ ] M1     Arm 2 شاهد لجر
[ ] M2     Arm 1 سایه (lease هنوز لپ‌تاپ)
[ ] M3     CUTOVER
[ ] M4     legs بیزنسی
[ ] M5     Arm 3 + فیزیک
[ ] M6     Arm 4 + بستن حلقه
```

قانون: هیچ‌وقت دو فاز را همزمان باز نکن. M0 تا M2 کم‌ریسک‌اند. تمام خطر در M3 است. مسیر برگشتی که یک‌بار واقعاً اجرا نشده وجود ندارد.

## چرا TTL به‌تنهایی کافی نیست

یک پروسه می‌تواند pause شود (GC، سوسپند لپ‌تاپ، وقفهٔ دیسک)، lease منقضی شود، برد دیگری مالک شود، و پروسهٔ اول بیدار شود و بنویسد. TTL این را نمی‌گیرد.

راه‌حل: **fencing token**. هر lease یک `revision` یکنواخت‌صعودی دارد. هر نوشتن به state / لجر / بودجه باید این token را همراه ببرد. `lease.token` اول `assert_valid()` را صدا می‌زند — بدون اعتبار، token نمی‌گیری.

دو باگ که تست‌ها قفل کردند:

1. **`release()` فایل را پاک نکند.** پاک‌کردن ⇒ مالک بعدی از revision=1 شروع می‌کند ⇒ نویسندهٔ کهنه با token=2 او را دور می‌زند. الان vacate می‌کند و شماره را نگه می‌دارد.
2. **ناحیهٔ مردهٔ عمدی.** مالک در `ttl - margin` بازنشسته می‌شود؛ بعدی تا `ttl + margin` صبر می‌کند. پیش‌فرض: TTL ۶۰ث، حاشیه ۱۰ث، مرده ۲۰ث (انحراف ساعت).

ساعت **monotonic** برای «آیا هنوز مالکم؟». ساعت دیواری اگر NTP عقب بپرد دروغ می‌گوید.

بک‌اند: `FileLeaseStore` فقط دیسک محلی (UNC/SMB رد می‌شود). `NatsKvLeaseStore` برای M2+ از revision خود NATS KV. `BEAT-FREEZE.flag` همه را، حتی مالک فعلی را، متوقف می‌کند — برای شب cutover.

ساعت ۲ صبح:

```text
python -m _ops.runtime.beat_lease_cli status
python -m _ops.runtime.beat_lease_cli freeze "cutover rehearsal"
```

خروجی: `HELD — do NOT start a second organism` یا `VACANT — free to take`.

SoT کد: `_ops/runtime/beat_lease.py`. پروتوتایپ HMAC در `_ops/octopus_v3/beat_lease.py` fencing نیست؛ سیم نشود.

## پنج تله

1. Split-brain / دو بودجه — lease همین است.
2. SQLite+WAL روی شبکه — تک‌نویسنده روی Arm 1، نه share، نه Postgres در مهاجرت (۴ گیگ).
3. Windows→Linux: CRLF، بک‌اسلش، case-fold. یک عصر **قبل از کپی**.
4. `.env` یکپارچه می‌میرد. Arm 1 تنها کلید مغز و تنها egress. rotate در cutover، نه در ریپو.
5. ۷۲۹ تست روی برد ۴ گیگ نه. smoke <۹۰ث هر بوت؛ full فقط لپ‌تاپ قبل از cutover.

## فازها (شرط عبور)

| فاز | هدف | شرط عبور | برگشت |
|---|---|---|---|
| M0 | بدانی چه را منتقل می‌کنی | `MIGRATION-INVENTORY.md` پنج بخش + full سبز | هیچ چیز عوض نشده |
| M1 | شاهد مستقل | یک بایت دستی ⇒ verify بشکند + alarm؛ سه روز head-hash | Arm 2 خاموش |
| M2 | Arm 1 می‌بیند، اجرا نمی‌کند | ۷۲ساعت اختلاف <۱٪، صفر crash، **صفر beat از Arm 1** | Arm 1 خاموش |
| M3 | cutover | لپ‌تاپ ۲۴ساعت بسته؛ beat و بودجه درست؛ صفر یتیم در لجر | lease+snapshot — **قبل از M3 یک‌بار تمرین** |
| M4 | legs کلاینت `octopus.command.legs` | Arm 1 خاموش ⇒ اکشن نو نه | فلگ مستقل قبلی |
| M5 | taint فیزیکی | سیم رله را بکش ⇒ بار <۳ث خاموش؛ taint=false رد شود | Arm 3 جدا |
| M6 | لپ‌تاپ رسماً کلاینت | Arm 4 به `octopus.command.arm1` بنویسد ⇒ رد + ثبت لجر | ندارد |

چه چیزی منتقل **نمی‌شود:** `_Archive/` `_Duplicates/` `node_modules/` ۷۲۹ تست کامل · `.env` یکپارچه · vault ابسیدین (پروژهٔ جدا).

## رأی‌های باز

ایجنت بعد این‌ها را می‌بندد (نه cutover): [[../../agent-prompts/MEGAPROMPT-MIGRATE-CLOSE-GAPS-2026-08-16|MIGRATE-CLOSE-GAPS]]

- [ ] `on_event` به لجر Arm 2 (هنوز Arm 2 نیست — تا M1 روی jsonl محلی هم می‌تواند سایه باشد)
- [ ] `lease.assert_valid()` قبل از هر ضربان در chrono — پیشنهاد: no-lease → `pause` نه `stop`
- [ ] هر نوشتن state/لجر/بودجه باید `fencing_token` را حمل کند
- [ ] اسکریپت M0
- [ ] قبل از M3: rollback واقعی
- [ ] چرخش کلیدها در cutover (خارج از ریپو)

شواهد: [[../../06-EVIDENCE/BEAT-OWNERSHIP-LEASE-2026-08-16|BEAT-LEASE]] · کارت: [[../../00 - Inbox/2026-08-16 DISCOVERY — Laptop to Arm1 Migration|Inbox]]
