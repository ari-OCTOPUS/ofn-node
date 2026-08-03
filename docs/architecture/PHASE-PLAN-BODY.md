# PHASE PLAN — بدنِ اختاپوس (BODY organ)

> 2026-07-29 · propose-only · هیچ فازی بدونِ تست/شاهد رد نمی‌شود · فعال‌سازیِ فلگ فقط با
> جمله‌ی `OWNER_AUTH: ARM FLAG OCTOPUS_WIRE_BODY` از مالک (پروتکلِ ARMING-ORDER-2026-07-29).

## قوانینِ هر فاز
1. baseline: خروجیِ صریحِ `python -X utf8 F:\backup\_ops\tests\run_all.py` قبل و بعد (07-29: 389 فایلِ تست [OBS]). افتِ سوئیت = توقفِ خودکار.
2. اعمالِ کد سریالی، additive، flag-gated (پیش‌فرض ۰)، fail-soft. بکاپ → assert count==1 → compile → دو sha.
3. هیچ ACTIVATION-*.flagی ساخته نمی‌شود (دستِ مالک). هیچ رازی نوشته نمی‌شود.
4. ثبتِ canonicalهای نو در ARCHITECTURE-SOT.md با verdict (پیشنهاد در TRUTH_MAP §9).

---

## Phase A — Discovery (انجام شد ✅)
خروجی: `docs/architecture/OCTOPUS_TRUTH_MAP.md` · `docs/math/EQUATION-REGISTRY.md` ·
`docs/architecture/BODY-MATH-SELF-INTEGRATION.md` · این فایل.
شواهد: ORGANISM-STATE (beat 16528) · synapse-trail degraded · PULSE-EQUATIONS-LOCKED ·
ARMING-ORDER · BOTS-REGISTRY · ledger tail · approval_fatigue · self-model.json.

## Phase B — Schemas + SQL + stubs (بدونِ اثرِ runtime)
- `schemas/body_state.v1.schema.json` · `sensor_event.v1` · `math_observation.v1` · `telegram_body_card.v1` (پیشنهادِ مسیر: `_ops/body/schemas/`)
- `db DDL`: body_ticks · math_observations · audit_labels(+seed) · approval_audits · audit_evidence → `_ops/state/body/body.db` (SQLite، WAL مثل بقیه‌ی dbها)
- stubs پکیج `_ops/body/` (خالیِ اجرا، پر از docstring+قرارداد) + `tests/test_body_schemas.py` (validation + fail-closed enum)
- **گیتِ خروج**: تست‌های اسکیما سبز؛ سوئیت ≥ baseline؛ هیچ importی از runtime.

## Phase C — body_state + math_filter MVP (shadow)
- sensor_hub: خواندنِ read-only از state/* (events→cpm · chrono→phi/phase · coherence→r · budget/fatigue · quota · germline_lag)
- math_filter: EQ-BODY-01/02/03 (SNR gate + bandpass + Hilbert روی سریِ cpm)
- خروجی: `_ops/state/body/body-ticks.jsonl` + `body-state-latest.json` (LOW_CONFIDENCE-aware)
- تست‌ها: سینوسیِ مصنوعی، SNR threshold، LOW_CONFIDENCE روی پنجره‌ی کوچک (بازتولیدِ درسِ phi-bootstrap)
- wiring: فقط یک observerِ per-cycle در wiring.py **اگر** مالک بگوید؛ وگرنه standalone beat (`RUN-BODY.bat`) — تصمیمِ مالک.

## Phase D — Telegram `/body` (read-only)
- live_commands += headهای body/بدن → telegram_body.card() (الگوی /id؛ ≤700 char quiet)
- منبع: فقط body-state-latest.json؛ کهنگی>2×cadence ⇒ کارتِ «داده‌ی کهنه»
- تست: قالب‌بندی + fail-closed روی فایلِ غایب.

## Phase E — self-model + ledger
- merge در self-model: body:{BCS, PĒ, r, coverage_pct, last_tick_ts}
- anchorِ هفتگی در genome ledger: NOTE با sha256ِ tick-rollup (الگوی hash-chain)

## Phase F — Kuramoto-lite (اختیاری)
- θ_i از beat timestamps؛ r و ψ در shadow؛ هشدارِ desync فقط advisory (تلگرام، بدونِ اقدام)

## Phase G — reward/trust bridge
- EQ-BODY-06 روی verdict_recorder outcomes؛ تستِ guard: هیچ مسیرِ به‌روزرسانی از confidence

## Phase H — سخت‌افزار (فقط با verdictِ مالک)
- HardwareSensorAdapter interface؛ اولین کاندید: system metrics (CPU/RAM) یا mic RMS — نه آنتن‌ی ELF.

---

## Vertical Slice (هدفِ کدنویسِ بعدی — Phase B+C+D)

```
events.jsonl ──read──▶ sensor_hub.tick()
                         │ sensor_event.v1
                         ▼
                     math_filter (SNR gate → Hilbert A,φ)
                         │ math_observation.v1 (LOW_CONFIDENCE-aware)
                         ▼
                     body-state-latest.json + body-ticks.jsonl
                         │
                         ├──▶ /body در تلگرام (read-only)
                         └──▶ (Phase E) anchor در ledger
```

## این هفته چه ساخته می‌شود / چه چیزی سخت‌افزار می‌خواهد / چه چیزی propose-only می‌ماند
- **این هفته:** Phase B+C+D کامل (بدونِ فلگِ روشن — shadow). تلگرام فردا می‌تواند `/body` را از فایلِ state بخواند (داده‌ی واقعیِ shadow).
- **سخت‌افزار:** mic/system/IMU/ELF — Phase H، فقط با verdict.
- **propose-only برای همیشه (تا ابلاغِ جدا):** هر اقدامِ اجرایی از روی body_state؛ reward_bridge نوشتن روی trust؛ Kuramoto روی scheduling.
- **تصمیم‌های لازم از مالک (فقط دو تا):**
  1. `CONTINUE PHASE B`؟ (ساختِ اسکیما+stub+تست — هنوز بدونِ اثرِ runtime)
  2. مسیرِ wiring در Phase C: observer داخلِ wiring.py یا standalone beat؟ (پیش‌فرضِ امن: standalone)
