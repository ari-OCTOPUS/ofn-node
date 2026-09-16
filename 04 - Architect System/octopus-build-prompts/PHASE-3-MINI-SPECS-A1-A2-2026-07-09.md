---
type: proposal
subtype: PHASE_SPEC
status: draft-for-verdict
priority: P0
phase: 3
domain: architect / _ops / money-chain (Track-B)
created: 2026-07-09
created_by: agent
grounded_on: "HEAD a2215dd (post Phase-4)"
tags: [octopus, phase-3, money, reconcile, fitness, propose-only]
---

# PHASE 3 — mini-specs · A1 `reconcile_beat` + A2 `fitness outbox`

> **حساس‌ترین فاز (money-chain).** ناوردی‌های حاکم بر هر دو آیتم:
> propose-only · additive · هر مسیرِ نو پشتِ **flag پیش‌فرض خاموش** · **$0/offline** (هیچ bank/scrape/شبکه) ·
> ledger **append-only** (بدون schema-change، بدون spend) · `budgets.yaml`/HRV/genome **دست‌نخورده** ·
> `live_gate` قفل تا ۲۰۲۶-۰۷-۲۱ **دست‌نخورده**. **کد فقط بعد از verdict.**

## گاردریل‌ها (روی کد verify شد)
- `opslib.LIVE_GATE_DATE = date(2026,7,21)` · `live_gate_open()` دوقفله: `today ≥ gate` **AND** activation-flag — `[FACT opslib.py:85,278–282]`. هیچ‌کدام از A1/A2 این را لمس نمی‌کند.
- `budgets.yaml` فقط‌خواندنی است (`fitness.compute → opslib.load_budgets`، وزن‌ها I6) — agent **edit نمی‌کند** `[FACT fitness.py:134]`.
- `CONFIRMED` را فقط `reconcile`/`attribution.confirm` می‌نویسد؛ خودگزارشیِ ایجنت هرگز `[FACT reconcile.py:97–103 · test_attribution]`.
- fitness تا ۲۸ روزِ EXPERIENCE، `authoritative=False` (فقط سایه) `[FACT fitness.py:37,215]`.

---

## A1 — `reconcile_beat` (اجرای reconcile روی ضربان، پشت flag)

**فایل‌های درگیر:** `_ops/budget/reconcile.py` (منبعِ `run()`), `_ops/chrono.py` یا `_ops/live_loop.py` (حلقهٔ beat), `_ops/legs/lead_leg.py:139` (`run_reconcile` موجود).

**وضعیت فعلی `[FACT]`:** `reconcile.run(reconcile_dir=None, write=True)` فقط دستی (CLI) یا از `lead_leg.run_reconcile` صدا زده می‌شود — **هیچ cadence‌ای ندارد**. منطق: CSVهای انسانی‌دراپ‌شدهٔ `_ops/reconcile/*.csv` → CONFIRM فقط با هر ۴ شرط (lead_id · CLAIMED · مبلغِ exact · پنجرهٔ ۷ روز)، fail-closed، خروجی در `reconcile-latest.json`.

**تغییر پیشنهادی (low-level):**
- flag جدید `OCTOPUS_RECONCILE_BEAT` (پیش‌فرض **off**) + `CHRONO_RECONCILE_EVERY_N_BEATS` (پیش‌فرض `1440`=روزانه، مثلِ `CHRONO_AGE_PER_N_BEATS`).
- در حلقهٔ beat (همان‌جا که heartbeat/age_tick می‌زند): اگر flag on و `beat_seq % N == 0` → `reconcile.run(write=True)` صدا زده شود، در `try/except` fail-soft (خطا نباید ضربان را بکشد).
- **صفر تغییر در منطقِ `reconcile.run`.** فقط یک trigger افزوده می‌شود. هیچ مسیرِ خرج‌دار، هیچ شبکه، `live_gate` لمس نمی‌شود.

**تست‌ها:** flag off → صفر فراخوانی (رفتار عیناً فعلی) · flag on → هر N beat یک‌بار `run` · CSV خالی/نبودِ dir → graceful (`rows_read=0`) · CSVِ خراب → alert بدونِ confirm · double-claim → نادیده (موجود) · **اثبات: beat هرگز `live_gate` باز نمی‌کند و spend نمی‌زند** · idempotent (اجرای دوباره → CONFIRMEDِ قبلی دوباره اعتبار نمی‌گیرد، گاردِ `seen`/`CONFIRMED_STATES`).

---

## A2 — `fitness outbox` (هندوفِ reconcile→fitness از یک outboxِ append-only)

**فایل‌های درگیر:** `_ops/budget/fitness.py` (`compute`), `_ops/budget/reconcile.py`, `_ops/budget/attribution.py`, `logs/…`.

**وضعیت فعلی `[FACT]`:** fitness از قبل یک «outbox» دارد — `logs/outbox.jsonl` ⟂ `core.db/outbox` (رویدادهای کلیک‌انسانیِ sent/rejected/failed) با tamper-check. سیگنالِ درآمدِ CONFIRMED از `attribution.confirmed_revenue()` **مستقیم** خوانده می‌شود و فقط پشتِ flag `OCTOPUS_WIRE_BARBELL` به value تزریق می‌شود `[FACT fitness.py:190–211]`.

**⚠️ ابهامِ scope (نیاز به verdict):**
- **تفسیر a (پیش‌فرضِ من):** یک outboxِ append-onlyِ اختصاصیِ reconcile→fitness (`logs/fitness-outbox.jsonl`): `reconcile` رویدادِ CONFIRMED-revenue را **append** می‌کند؛ `fitness` پشتِ flag `OCTOPUS_WIRE_FITNESS_OUTBOX` (off) از همان می‌خواند (decoupled + auditable)، و off = عیناً رفتارِ فعلی (خواندن مستقیم از attribution).
- **تفسیر b:** outboxِ موجود کافی است؛ A2 = فقط hardening/تستِ همان مسیر (⟂ check + barbell)، بدونِ outboxِ جدید.

**تغییر پیشنهادی (low-level، تفسیر a):**
- `reconcile.run` هنگام CONFIRM، یک خطِ append-only به `logs/fitness-outbox.jsonl` بزند: `{ts, lead_id, cell, amount_aud, source_hash}` — **append-only، بدونِ schema-change ژنوم، بدونِ spend**.
- `fitness.compute`: اگر `OCTOPUS_WIRE_FITNESS_OUTBOX=1` → درآمدِ CONFIRMED را از این outbox بخواند و با `attribution.confirmed_revenue()` ⟂ tamper-check کند (mismatch → alert + exclude، مثلِ `_tamper_check` موجود)؛ اگر off → عیناً مسیرِ فعلی.
- `authoritative`/۲۸-روز و وزن‌های `budgets.yaml` **دست‌نخورده**. فقط CONFIRMED وارد می‌شود (ناوردی: هرگز زیرِ CONFIRMED).

**تست‌ها:** flag off → fitness عیناً فعلی (zero-diff) · flag on → خواندن از outbox == اعداد attribution · outbox خالی → graceful · mismatch outbox↔attribution > tol → alert + exclude · authoritative همچنان False < ۲۸ روز · **اثبات: صفر spend، budgets فقط‌خواندنی، append-only**.

---

## ترتیب، وابستگی، ریسک
- ترتیب: **A1 اول** (کم‌ریسک‌تر: فقط trigger)، **A2 بعد** (چون به CONFIRMEDِ reconcile وابسته است).
- ریسکِ اصلی: هر دو money-adjacent‌اند → کاهش با off-flag + $0 + append-only + verify-tests. هیچ‌کدام `live_gate`/`budgets`/`money_gate` را تغییر نمی‌دهد.
- **بلاکرِ بهداشتی (فقط‌مالک):** `.git/index.lock` در sandbox دیده می‌شود؛ چون commit `a2215dd` نشست، Windows-side سالم است — ولی اگر git شکایت کرد: `del F:\backup\.git\index.lock`. همهٔ commitها Windows-side.

## Done-checklist فاز ۳
- [ ] A1: flag + beat-trigger؛ ۶ تست سبز؛ اثباتِ عدمِ باز شدنِ live_gate.
- [ ] A2: outbox append-only + خواندنِ flag-گیت؛ ⟂ tamper-test؛ zero-diff در flag off.
- [ ] Review + نحوهٔ on/off + rollback + آپدیت `PROJECT/HANDOFF/DecisionLog`.
