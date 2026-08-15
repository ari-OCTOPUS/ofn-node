---
type: truth-note
section: contradictions
created: 2026-08-15
status: open — هیچ تناقضی بدون رأی مالک «حل» نشده
rule: "هر دو مقدار ثبت می‌شوند؛ در صورت شواهد قوی فقط `likely` می‌نویسیم و status را open نگه می‌داریم"
---

# CONTRADICTIONS — ثبت تناقضات (STEP 7 مگاپرامپت)

```yaml
contradiction:
  id: C-001
  claim: "تعداد تست NBB-CP"
  value_a: 207
  source_a: "03 - Projects/NBB-Control-Plane/MANIFEST.yaml (2026-07-11) — «83 l0 + 102 l1 + 5 l2 + 17 import-lint»؛ README ریشه هم ۲۰۷ می‌گوید"
  value_b: 171
  source_b: "03 - Projects/NBB-Control-Plane/BACKUP-README.txt (2026-07-11) — «Head: 02561ea (171 tests green)»"
  live_check: "2026-08-15: py -m pytest -o addopts= -q → 171 passed in 2.50s"
  likely: value_b
  resolution: null
  status: open
```

```yaml
contradiction:
  id: C-002
  claim: "اعداد وضعیت ارگانیسم (coherence/beat)"
  value_a: "coherence=0.958, beat=36436"
  source_a: "مگاپرامپت مالک (2026-08-15)"
  value_b: "coherence=0.95, beat=36563"
  source_b: "OCTOPUS/CURRENT-TRUTH.md — بلوک auto 2026-08-15T04:10:09Z (runtime)"
  live_check: "خواندن مستقیم فایل در همین جلسه — مطابق value_b"
  likely: value_b
  resolution: null
  status: open
  note: "اختلاف likely ناشی از فاصلهٔ زمانی خواندن است (beat جلو می‌رود)؛ ولی طبق قاعده هر دو ثبت شد."
```

```yaml
contradiction:
  id: C-003
  claim: "سلامت سوئیت تست hypothesis_engine"
  value_a: "«۵ سوییت سبز» (فریم‌ورک deceptive-grid، ۹ سناریو + ablation + red-team)"
  source_a: "OCTOPUS/CURRENT-TRUTH.md — بخش 2026-08-13"
  value_b: "ImportError در collection: cannot import name 'falsified_assists_at' from 'deceptive_grid' (_ops/hypothesis_engine/experiments/deceptive_grid.py)"
  source_b: "اجرای زنده 2026-08-15: py -m pytest -q در _ops/hypothesis_engine"
  live_check: "بازتولیدپذیر در همین محیط (Python 3.13، بدون venv اختصاصی)"
  likely: "علت = ویرایشِ uncommitted درخت کاری، نه کد کامیت‌شده — git show HEAD شامل falsified_assists_at است (۲ بار) ولی درخت کاری (−۳۶۴ خط/+۶۷، uncommitted و pre-existing) صفر بار داشت"
  resolution: "owner_verdict NEW-4 (2026-08-15): بازگردانی با git stash قبلش — اجرا شد: git stash push مسیر-مشخص → stash@{0} (ویرایش آرشیو شد، حذف نشد) → اجرای مجدد تست‌ها: 23 passed in 1.53s ✅"
  status: resolved (رأی مالک + اجرای زندهٔ مجدد، 2026-08-15)
```

```yaml
contradiction:
  id: C-004
  claim: "محل NBB-CP حاکم"
  value_a: "app/NBB-CP — «۲۰۷ تست سبز»"
  source_a: "README.md ریشه (2026-08-10)"
  value_b: "app/ حذف شده در کامیت ea69126 (پاکسازی 2026-08-03)؛ نسخه‌های زنده در 03 - Projects/NBB-Control-Plane و 4d_system/*"
  source_b: "git log --diff-filter=D + بررسی درخت فایل‌سیستم 2026-08-15"
  live_check: "ls /f/backup/app → وجود ندارد"
  likely: value_b
  resolution: null
  status: open
  note: "رأی مالک 2026-08-15 دربارهٔ نسخه‌ها: «همش منم» — چهار نسخه یک پروژه‌اند. README ریشه همچنان ارجاع stale دارد."
```

```yaml
contradiction:
  id: C-005
  claim: "وجود ADR-041 (رصدخانهٔ اینترنت)"
  value_a: "ADR-041 به‌عنوان سند رصدخانهٔ اینترنت (allowlist، gateway)"
  source_a: "مگاپرامپت مالک (2026-08-15)"
  value_b: "ADR-041 در هیچ‌جا نیست؛ دنبالهٔ پوشهٔ adr از ADR-040 به ADR-042 می‌پرد (024–032 هم غایب)"
  source_b: "جستجوی نام+محتوا+git history --all در F:\backup و ۱۰ Vault دیگر (2026-08-15)"
  live_check: "ls 03 - Projects/research-spec-compiler/adr/"
  likely: null
  resolution: "owner_verdict NEW-2 + اجرای --apply (2026-08-15 17:09): موتور octopus_sync سند را نوشت → 03 - Projects/research-spec-compiler/adr/ADR-041-internet-observatory.md — پرش ۰۴۰→۰۴۲ بسته شد ✅"
  status: resolved (applied)
  note: "گزارش نشست رصدخانه §10 نیز همین کار را به‌عنوان آیتم باز ۷ فهرست کرده بود."
```

```yaml
contradiction:
  id: C-006
  claim: "تعداد تست سبز کل (۴۱۴ یا ۴۰۸)"
  value_a: 414
  source_a: "CHECKPOINT (به ادعای مگاپرامپت؛ خود CHECKPOINT.md پیدا نشد)"
  value_b: 408
  source_b: "پیام کامیت (به ادعای مگاپرامپت؛ git log --all --grep ۴۰۸/۴۱۴ → خالی — تاریخچه در ea69126 اسکواش شده)"
  live_check: "collection از ریشه: 15 collected, 2 errors — قابل جمع نیست"
  likely: null
  resolution: null
  status: open
  note: "هیچ‌کدام تأییدشدنی نیست؛ هر دو unverified."
```

```yaml
contradiction:
  id: C-007
  claim: "تعداد تست سبز epistemics (ADR-039)"
  value_a: 133
  source_a: "سربرگ ADR-039 («C1-C4 پیاده و تست‌شده (۱۳۳ تست سبز)»)"
  value_b: "45/45 + 20/20 = 65"
  source_b: "OCTOPUS/CURRENT-TRUTH.md — بخش 2026-08-13"
  live_check: "سوئیت مربوطه در تلاش هدفمند اجرا نشد (test_planner.py collected 0) → قابل داوری نبود"
  likely: null
  resolution: null
  status: open
```

## روش نهایی

۱. هر دو مقدار ثبت شد. ۲. هیچ مقداری حذف/بازنویسی نشد. ۳. `likely` فقط نظر شواهدی است، نه رأی. ۴. resolution فقط با مالک یا runtime معتبر پر می‌شود.

```yaml
contradiction:
  id: C-009
  claim: "دکمه‌های تأیید/رد کارت‌های دکتر کار می‌کنند"
  value_a: "کارت با reply_markup ok/no ارسال می‌شود (ok:true) — به‌ظاهر کامل"
  source_a: "tg-outbox.jsonl — رسیدهای ارسال 2026-08-15 شب"
  value_b: "تپ مالک → پاسخ «نادیده»؛ رأی هرگز در tg-inbox.jsonl ثبت نمی‌شود"
  source_b: "گزارش مستقیم مالک 2026-08-15 شب + center.py:3308 («command ناشناس نادیده») + کانال دکتر mode=direct بدون OWNS_POLLING"
  live_check: "center فقط فعل‌های mo:/m:/توکن‌دار را route می‌کند؛ فرمت ok:intent: در واژگانش نیست"
  likely: "طراحی صدای اشتراکی ناقص است — دکمه به مقصد ندارد بدون ربات اختصاصی دکتر"
  resolution: "پیشنهاد دوگانه: (فوری) تایید چتی + (اصلی) ربات اختصاصی BotFather → OCTOPUS_DOCTOR_BOT_TOKEN جدید + OWNS_POLLING=1"
  status: open — owner_action
  note: "هم‌خانوادهٔ کشف 2026-07-28 (test_bridge_buttons.py: ۲۹ دکمهٔ در حال افتادن) — طبقهٔ باگ یکسان: مسیر رأی مالک بی‌صدا می‌میرد"
```

**به‌روزرسانی C-009 (2026-08-15 ~18:17):** پل ساخته و مستقر شد — هوک سه‌بخشی قبل از جدولِ verb در center.py + `_doctor_ingest` (importlib فایل‌لود به‌خاطر سایهٔ پکیج `_ops/doctor`) + ۵ تست سبز + کامیت «feat(center): doctor vote bridge». منتظر تپِ مالک روی همان دکمه‌ها برای تأیید حل کامل.

**✅ C-009 RESOLVED (2026-08-15 ~18:22):** پل رأی دکتر (کامیت feat(center)) مستقر شد و **۷ رأی واقعی مالک همان شب از همان دکمه‌ها ثبت شد** (هر سه کارت تایید؛ رأی‌دهنده با چت مالک تطبیق شد). یافتم جانبی: کارت‌ها دو مسیر داشتند (ارسال مستقیم ربات اصلی + پخش relay ربات center) — فقط دکمه‌های نسخهٔ center به poller می‌رسند؛ پیشنهاد آینده: حالت دکتر به outbox برگردد تا relay تنها صدای واحد باشد (نویز دو-copy برود).


---

## 📛 قانون تخصیص شناسهٔ تناقض (مستقر به حکم مالک — 2026-08-15 شب، پس از برخورد C-008)

1. شناسه‌ها فقط از **یک شمارندهٔ واحد** — آزاد بعدی: **C-010**
2. قبل از تخصیص، `C-0NN` روی **هر دو مخزن** grep شود: `F:ackup` و working repo
3. دو ایجنتِ هم‌زمان بدون شمارندهٔ مشترک = برخوردِ حتمی (این‌طور C-008 دوبار ثبت شد)

```yaml
contradiction:
  id: C-008
  claim: "فرمول hash انبار شاهد نامعلوم بود (none of 15 candidates matched)"
  source_a: "موتور sync (verifier تعبیه‌شده با کاندیدهای قدیمی) — ثبت ~18:06 در پک"
  source_b: "scripts/verify_live_store.py اصلاح‌شده با src-formula — PASS 27/27 (17:1x)"
  resolution: "resolved — فرمول عین سورس بازتولید شد (evidence_store.py:125-130 + prediction_registry.py:91)؛ نسخهٔ تعبیه‌شدهٔ موتور همچنان کاندیدهای قدیمی دارد تا به‌روزرسانی صاحبش"
  status: resolved (روش حل: افزودن کاندید صحیح، نه تغییر کد انبار)
  cross_ref: "C-009 (پل رأی دکتر) — برخورد نام‌گذاری همین دو رکورد بود"
```

> **یادداشت تاریخی:** کامیت‌های `3156316` و `0823ce5` (پیش از این حکم) با «C-008» منظورشان پل رأی دکتر بود — پس از حکم، همان موضوع **C-009** است. تاریخ git تغییرناک است؛ این یادداشت مترجم آن است.

```yaml
contradiction:
  id: C-010
  claim: "مسیر پولیِ مغز (هر provider) سالم است"
  value_a: "deepseek secondary در 13:36 کار می‌کرد (paid-calls.jsonl)"
  source_a: "_ops/state/paid-calls.jsonl — رکورد 2026-08-15T13:36:39"
  value_b: "JSONDecodeError: Unexpected UTF-8 BOM در circuit_breaker._load_state → کل _ask_paid قبل از تماس می‌شکست"
  source_b: "اجرای زندهٔ probe در 19:2x + فایل _ops/state/circuit-state.json دارای BOM"
  resolution: "BOM از فایل strip شد (19:2x) → probe فوری ok:True؛ سخت‌سازی opslib.read با utf-8-sig = پیشنهاد (core مشترک، نیازمند تست در همان commit)"
  status: resolved (data-fix) — hardening proposed
  root_cause_fa: "BOM اثرِ نوشتن با PowerShell (Set-Content/Out-File پیش‌فرض BOM می‌نویسند) — درس: فایل‌های state هرگز با PowerShell نوشته نشوند یا خواننده BOM-تابلنت شود"
  registered_by: "laptop-agent (grep دو-مخزن انجام شد — قانون شناسه C-009 رعایت شد)"
```
