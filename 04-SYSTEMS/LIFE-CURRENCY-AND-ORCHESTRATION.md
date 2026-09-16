# LIFE CURRENCY & ORCHESTRATION
## واحد زندگی و ارکستراسیون مستقل از Provider

> **وضعیت:** نهایی — 2026-08-16
> **مالک:** Armin
> **اصل:** ضربان قلب = مقدار زندگی هر ایجنت — نوع و مقدار API و توکن

---

## ۱. واحد زندگی (Life Currency) — سه‌بعدی

| بعد | نام | واحد | توضیح |
|-----|-----|------|-------|
| ۱ | Token | tok | مقدار توکن مجاز |
| ۲ | Call | call | تعداد فراخوانی API |
| ۳ | Risk | risk | وزن ریسک اقدام |

### تبدیل به API

cost = token_used × risk_weight + call_overhead

risk_weight:
- A0 (مشاهده) = 0.1
- A1 (sandbox) = 0.5
- A2 (reversible) = 2.0 ← خودکار
- A3 (owner gate) = 5.0
- A4 (external) = 10.0 ← فقط مالک
- A5 (money) = 50.0
- A6 (forbidden) = ∞

### مبادله بودجه: آزاد با لاگ

ایجنت‌ها آزادانه بودجه را مبادله یا قرض می‌کنند. فقط لاگ اجباری است.
DEBT_FORBIDDEN = false.

---

## ۲. ارکستراسیون مستقل از Provider

> ارکستراسیون داخل قراردادها و رویدادهای OCTOPUS است، نه داخل Provider.
> Fugu / DeepSeek / GLM / Ollama فقط آداپتور محاسباتی هستند.

### ترتیب Fallback: Fugu → DeepSeek → GLM → Ollama

### کاهش پله‌ای خودمختاری

| Provider | A0-A1 | A2 | A3+ |
|----------|-------|-----|-----|
| Fugu | auto | auto | owner |
| DeepSeek | auto | auto | owner |
| GLM | auto | propose | owner |
| Ollama | auto | propose | owner |

### نرخ تبدیل

| Provider | نرخ | کیفیت |
|----------|-----|--------|
| Fugu | 1.0× | tier 1 |
| DeepSeek | 0.8× | tier 2 |
| GLM | 0.9× | tier 2 |
| Ollama | 0.1× | tier 3 |

### قواعد fallback
1. Health check هر beat
2. Switch بدون restart
3. ثبت در events.jsonl
4. اطلاع‌رسانی تلگرام
5. Budget re-rate خودکار
6. Downgrade خودکار: GLM/Ollama → A2 auto→propose

---

## ۳. نردبان اقدامات نهایی

| کلاس | تعریف | خودکار | مالک | fallback |
|------|-------|--------|------|----------|
| A0 | مشاهده | ✅ | — | auto |
| A1 | sandbox reversible | ✅ | — | auto |
| A2 | reversible change | ✅ | — | propose |
| A3 | owner gate | — | ✅ | owner |
| A4 | external effect | — | ✅ | owner |
| A5 | money/commitment | — | ✅ | owner |
| A6 | forbidden | ❌ | ❌ | ❌ |

---

## ۴. self_improve_auto

- مجاز: هر تغییری به جز TCB و safety gates
- ممنوع: تغییر فایل‌های TCB، killswitch، safety gates
- تغییرات TCB = halt فوری (enforce=1)

---

## ۵. قوانین اساسی هوشمندی

| قانون | توضیح |
|--------|-------|
| QUALITY_GATE | A3+ فقط با provider tier ≤ 2 |
| BUDGET_HARD_CAP | > ۲× daily_budget در یک beat ممنوع |
| NO_SILENT_DOWNGRADE | هر کاهش کیفیت → اطلاع مالک |
| PROPOSE_ON_FALLBACK | GLM/Ollama: A2 → propose |
| RESERVE_FLOOR | ۲۰٪ بودجه ذخیره اضطراری |
| FREE_TRADE_LOGGED | مبادله آزاد با لاگ |
| CONSENSUS_HALT | halt فقط با consensus دو مغز |

---

## ۶. چرخه heartbeat

هر beat (~43s):
1. pulse_arbiter: ۳ رای قلب
2. GREEN → budget به ۱۱ عضو
3. مصرف/ذخیره/مبادله بودجه
4. doctor_setpoint سلامت
5. cortex-state.json به‌روز
6. ماژول خاموش: هر ۱۰ beat heartbeat OFF
7. YELLOW → budget نصف
8. RED → survival فقط
