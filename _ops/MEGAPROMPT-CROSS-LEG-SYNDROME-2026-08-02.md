---
type: megaprompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, integrity, reconciliation, ldpc-analogy, parity, money-safety]
created: 2026-08-02
updated: 2026-08-02
inspiration: OMEGA-PARITY LDPC syndrome — zero syndrome = consistent; nonzero localizes the violated constraint
evidence_source: [[DEEP-SCAN-REPORT-2026-08-02]] § creative mapping
---

# مگاپرامپت — سندرمِ cross-leg (Organism Integrity Syndrome)

> الهامِ ریاضی: در یک کدِ LDPC، ماتریسِ تنکِ H روی داده‌ی ذخیره‌شده اعمال
> می‌شود؛ H·x = 0 یعنی داده با همه‌ی محدودیت‌ها سازگار است. هر بیتِ نقض،
> سندرم را ناصفر می‌کند و **دقیقاً نشان می‌دهد کدام رابطه شکسته**. اختاپوس
> چند invariantِ بحرانی دارد که **چک نمی‌شوند** — یعنی پول می‌تواند در فاصله‌ی
> بین دو منبع گم شود و هیچ‌کس نفهمد. این مگاپرامپت آن invariantها را صریح،
> چک‌شونده، و localize‌شده می‌کند.

---

## ۰ · قواعدِ §۰ (تکرار نشود)

از `_ops/` شروع کن، نه ریشه. `Grep`/`Glob`. ≤۶۰s. ≤۴ ایجنت.
هرگز فلگ/پروسه/commit بدونِ `OWNER_AUTH`.

---

## ۱ · نقش

تو یک ایجنتِ سازنده‌ای. خروجی: یک ماژولِ `organism_syndrome.py` که در هر beat،
مجموعه‌ای از **invariantهای cross-leg** را بررسی می‌کند، یک **بردارِ سندرم**
می‌سازد (هر invariant = یک بیت: 0=برقرار، 1=نقض)، نقض‌ها را localize می‌کند
(کدام رابطه، کدام ارگان، کدام فاصله)، و آن را قابل مشاهده می‌کند.

قراردادِ «observable»: سندرم باید در ORGANISM-STATE نوشته شود، و نقضِ هر
invariant باید به‌عنوان یک یافته قابل مشاهده باشد (کارت/دایجست/گزارش).

---

## ۲ · واقعیتِ روی دیسک (قبل از شروع، این را بخوان — دو invariant غایب)

این‌ها با grep راستی‌آزمایی شده‌اند (zero hits):

**(I-۱) یکپارچگیِ بودجه:** `sum(organ_spent) == global_spent`.
- `budget/organ_gate.py` per-organ spent را در `ORGAN_STATE` نگه می‌دارد.
- `budget/budget_gate.py` سقفِ جهانی را enforce می‌کند.
- **هیچ کد** مجموعِ organ_spent را با global_spent مقایسه نمی‌کند. اگر state
  یکی خراب شود، هیچ آلارمی نیست.
- یکپارچگیِ جهانی: `sum(organs[*].spent_month_musd) <= global_spent_cap`.

**(I-۲) تکمیلِ pipeی outbound:** «اگه outbound_worker ایمیل فرستاد، یک رخدادِ
`customer.sent` در funnel باید باشه.»
- `legs/outbound_worker.py` send می‌کند و به funnel record می‌زند.
- هیچ کد بررسی نمی‌کند که هر send واقعاً یک funnel event دارد. اگه record
  گم شود، پول/ایمیل بدون اثر ثبت می‌شود.

**همچنین (موجود، برای الگو):**
- `legs/recon.py:125-130` — خودش syndrome است (amount_mismatch). از این الگو
  پیروی کن.
- `budget/fitness.py:41-96` — integrity check (jsonl count vs db count). الگو.

---

## ۳ · فازها

### فاز ۱ — تعریفِ invariantها (صریح، نه مبهم)
هر invariant را به‌عنوان یک تابعِ pure بنویس:
`check_I1_budget_integrity(state) -> {name, ok: bool, gap, detail}`.
`check_I2_outbound_funnel(window_hours) -> {name, ok, missing: [...], detail}`.
سند کن تعریفِ هرکدام: چه چیزی باید برابر باشد، چه tolerate، چه localize.

### فاز ۲ — بردارِ سندرم
`organism_syndrome() -> {syndrome: {I1: 0/1, I2: 0/1, ...}, violations: [...],
summary: str}`. جمعِ همه‌ی invariantها. **هیچ fail-open نکن** — اگر منبعی
خوانده‌نشد، بیت = «unknown» (نه 0).

### فاز ۳ — اثرِ observable
- در یک beat (یا sidecar): `ORGANISM-STATE.organism_syndrome` را بنویس.
- هر نقض = یک یافته در دایجستِ doctor یا کارتِ هشدار (وقتی syndrome ناصفر است).
- localize: نقض باید بگوید «organ X: spent=$A vs global=$B، فاصله=$C».

### فاز ۴ — تست
- واحد: هر invariant روی stateِ fake (نقض‌دار و نقض‌ندار).
- mutation: state خراب → سندرم ناصفر، نه crash.
- observable: اجرا روی state واقعی (اگر ممکن) → عدد واقعی.

---

## ۴ · مرزهای سخت
- **read-only** در بررسی: ماژول فقط می‌خواند و عدد می‌سازد، هرگز state را
  تغییر نمی‌دهد.
- پشتِ فلگ (`OCTOPUS_WIRE_ORGANISM_SYNDROME`)، پیش‌فرض خاموش.
- هرگز «unknown» را به‌عنوان 0 گزارش نکن.
- هرگز invariant را طوری ننویس که flaky باشد (race روی فایلِ در حال نوشته‌شدن).
- additive: هیچ ماژولِ موجودی بازنویسی نشود.
- halt مقدم بر فلگ.

---

## ۵ · خروجیِ مورد انتظار
«فازِ N تمام/نیمه/باز» + اثباتِ observable. صادقانه بنویس اگر invariantی روی
داده‌ی زنده قابل اثبات نیست (مثلاً outbound مسلح نیست، پس I-۲ روی داده‌ی واقعی
خالی است).
