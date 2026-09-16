# MASTER PLAN — Mining Pre-Execution → First Safe Experiment

> وضعیت فعلی: pre-execution / INFORM-only. این برنامه execution permission نیست.

## هدف نهایی

ساخت مسیر امن از وضعیت فعلی پروژه Mining تا اولین آزمایش کوچک mine-and-hold، بدون نقض D-10/D-11/D-20.

---

## Phase 0 — Lock & Truth Base

### خروجی‌های لازم
- همه secrets rotate/redact شوند.
- VERDICT_QUEUE با پاسخ انسانی تکمیل شود.
- Hardware Registry واقعی پر شود.
- برق واقعی یا solar/free بودن تأیید شود.
- تأیید شود هیچ mining فعال نیست.

### معیار Done
```yaml
wallet_seed_rotation: done
hardware_registry: filled
verdict_queue_open: 0
electricity_verified: true
zero_mining_active_confirmed: true
```

### مسئول
- مالک انسانی برای verdict/secrets/inventory.
- ایجنت فقط report/checklist.

---

## Phase 1 — One-Node Benchmark

### هدف
اندازه‌گیری واقعی H/s/W/temp روی یک OPi5، نه تصمیم سود.

### الگوریتم‌های پیشنهادی benchmark
1. yespower / yespowerr16
2. VerusHash
3. RandomX با huge pages
4. RandomWOW یا GhostRider در صورت زمان

### خروجی
- `benchmark_result.yaml` برای هر تست.
- `Benchmark Report.md`
- بروزرسانی OpenQuestions: H/s واقعی.

### گیت‌ها
- برق امن.
- دما زیر ۷۵°C، ترجیحاً زیر ۶۵–۷۰°C.
- rejected shares کمتر از ۲٪.
- حداقل ۲۴h برای تست اولیه، ۴۸h برای burn-in.

---

## Phase 2 — Read-only Scouting v1

### هدف
ساخت pipeline واقعی کشف کوین بدون execution.

### منابع
- Bitcointalk ANN
- MiningPoolStats newcoins
- GitHub/CryptoMiso dev activity
- GeckoTerminal/Rug checker برای exit risk
- minerstat فقط اگر دسترسی مجاز/بودجه باشد

### خروجی
- `coin_candidates.yaml`
- `Coin Scout Draft Report.md`
- no pool connection
- no wallet

---

## Phase 3 — Experiment Proposal

### هدف
برای فقط یک کوین، proposal بسازیم.

### محتوای proposal
- چرا ARM viable است؟
- چرا survival دارد؟
- بنچمارک مبنا چیست؟
- node group چیست؟
- death-watch plan چیست؟
- مدت آزمایش چند روز است؟
- برق چطور پاس شده؟

### خروجی
- `experiment_proposal.yaml`
- human verdict request

---

## Phase 4 — First Experiment, only after approval

این فاز در MVP اجرا نمی‌شود. فقط بعد از approval:

- deploy از مسیر repo+deploy gate.
- zero wallet access حفظ شود.
- یک node-group.
- یک کوین.
- یک death-watch log در هفته.
- no buy/sell/withdraw.

---

## Phase 5 — Steady Report Loop

- weekly death-watch
- hardware health
- mined coin info-only
- electricity report
- abandon proposal فقط با D2

---

## Anti-Drift Rules

- FPGA production mining فعلاً park/R&D، نه critical path.
- ESP32 = nervous system/sensors/watchdog، نه production mining.
- payback/liquidity فقط info، نه kill criteria.
- Tentacle v3.0 فقط future spec، نه runtime.
- Fleet Manager موجود است اما تا verdict خاموش/report-only.
