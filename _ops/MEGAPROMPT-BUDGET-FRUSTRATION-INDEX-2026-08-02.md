---
type: megaprompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, budget, observability, frustration, parity-analogy]
created: 2026-08-02
updated: 2026-08-02
inspiration: OMEGA-PARITY frustration (Ising/parity) — measure of unsatisfiable demand
evidence_source: [[DEEP-SCAN-REPORT-2026-08-02]] § creative mapping
---

# مگاپرامپت — شاخصِ ناامیدیِ بودجه (Budget Frustration Index)

> الهامِ ریاضی: در مدل‌های parity/Ising، «frustration» = میزانِ نقضِ اجتناب‌ناپذیرِ
> مجموعه‌ای از محدودیت‌ها که نمی‌توان همه‌شان را هم‌زمان برآورده کرد. اختاپوس
> ۶+ ارگان روی ~AU$12 headroom رقابت می‌کنند؛ وقتی `organ_gate.reserve()` deny
> می‌زند، فقط یک خط به `ORGAN_LOG` می‌نویسد و ساکت می‌شود. هیچ تجمیعی از
> «گرسنگیِ ارگان» نیست — ارگانی که دائماً گرسنه از ارگانی که سیر شده قابل
> تشخیص نیست. این مگاپرامپت آن نقاط کوری را قابل مشاهده می‌کند.

---

## ۰ · این ماشین هنگ می‌کند (قواعدِ §۰ — تکرار نشود)

از `_ops/` شروع کن، نه از ریشه. `Grep`/`Glob`. هر فرمان زیر ۶۰s. ≤۴ ایجنت.
هرگز فلگ/پروسه/commit بدونِ `OWNER_AUTH`.

---

## ۱ · نقش

تو یک ایجنتِ سازنده‌ای. خروجی: یک ماژولِ additive که `ORGAN_LOG` (لگِ deny/allow
هر reserve/settle) را تجمیع می‌کند و یک **frustration index** می‌سازد که نشان
می‌دهد هر ارگان چقدر تقاضا کرده، چقدر گرفته، و چقدر **نبرده** (denied). این عدد
باید برای مالک قابل‌مشاهده باشد: در ORGANISM-STATE، در یک metric، و در یک کارتِ
تلگرام (وقتی یک ارگان از آستانه‌ای فراتر رفت).

قراردادِ «observable»: اگر این کار فقط تست سبز دهد ولی چیزی در ORGANISM-STATE
یا کارت ظاهر نشود، نیمه‌تحویل است.

---

## ۲ · واقعیتِ روی دیسک (قبل از شروع، این را بخوان)

- `budget/organ_gate.py:34` — `_log(op, organ, est, verdict, task)` هر reserve را
  به `opslib.ORGAN_LOG` می‌نویسد (append-only JSONL). هر ردیف: `{ts, op, organ,
  est_usd, task, allow, reason}`.
- `budget/organ_gate.py:60-124` — `reserve()` در ۴ حالت deny می‌زند: `halted`،
  `frozen`، `unknown-organ`، `organ-monthly>cap`، و `budget_gate:...`.
- هیچ تجمیعی از این denies وجود ندارد. grep در doctor/, telegram_center/render.py,
  governor/ = صفر.
- `budget/governor_epoch.py:260-278` — governor فشار را با `pressure_state()`
  می‌سنجد ولی آن سرعتِ مصرف است، نه تقاضای برآورده‌نشده.

---

## ۳ · فازها

### فاز ۱ — تجمیعِ لگ (read-only + pure)
یک تابع بساز: `frustration_snapshot(window_hours=24) -> dict`. ورودی: مسیرِ
ORGAN_LOG. خروجی: per-organ `{requested_count, allowed_count, denied_count,
requested_usd, allowed_usd, denied_usd, denial_rate, top_reasons}`. pure، صفر
mutate، صفر side-effect. خطای parse → fail-soft (ردیفِ خراب را رد کن، نه crash).

### فاز ۲ — شاخصِ ناامیدی (pure)
`frustration_index(snapshot) -> float`. تعریفِ صریح: میزانِ تقاضای برآورده‌نشده،
وزن‌دار با اولویتِ ارگان (از `budgets.yaml` weights). عدد در [0,1]. سند کن که
چرا این تعریف، نه چیزی غلط‌تر (مثلاً «تعدادِ deny» به‌تنهایی گمراه‌کننده‌ست چون
یک ارگانِ پرکار با ۱۰ deny و ۱۰۰ allow سیرتر از ارگانی با ۱ deny و ۰ allow است).

### فاز ۳ — اثرِ observable
- در `business_legs_beat` یا یک beatِ جدا: `ORGANISM-STATE.budget_frustration`
  را بنویس (sidecar، مثلِ business_legs).
- در render.py یا یک کارتِ تلگرام: وقتی `denial_rate` ارگانی از آستانه‌ای
  (مثلاً ۰.۵) گذشت، یک خطِ هشدار در دایجست بیاور.

### فاز ۴ — تست
- واحد: snapshot روی لگِ fake (داده‌شده).
- mutation: لگِ خراب → fail-soft نه crash.
- observable: اجرا روی ORGAN_LOG واقعی (اگر وجود دارد) → عدد واقعی.

---

## ۴ · مرزهای سخت
- **propose-only** در فازِ گزارش: ماژول فقط می‌خواند و عدد می‌سازد، هرگز
  reserve/settle را تغییر نمی‌دهد.
- پشتِ فلگ (`OCTOPUS_WIRE_BUDGET_FRUSTRATION`)، پیش‌فرض خاموش.
- هرگز عددِ زنده را جعل نکن: اگر ORGAN_LOG خالی است، بنویس «no signal»، نه ۰.
- additive: هیچ ماژولِ موجودی بازنویسی نشود.
- halt مقدم بر فلگ.

---

## ۵ · خروجیِ مورد انتظار
«فازِ N تمام/نیمه/باز» + اثباتِ observable (ORGANISM-STATE diff، یا کارت، یا CLI).
صادقانه بنویس اگر مسیر end-to-end اثبات‌نشده.
