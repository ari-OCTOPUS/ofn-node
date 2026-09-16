# REPORT-P2

## خط حقیقت

```text
power-motor-documented + chaos-matrix-verified + evidence-ladder-established + discovery-candidates-identified
!= public-beta != money-live != AGI != golden-traces-complete
```

## Done

### P2.a — ROUTE-POLICY.md

- سه لایهٔ مدل (local/secondary/primary) با مدل‌ها و نقش‌ها
- مسیر تصمیم کامل با ارجاعِ خط (`model_router.py:376-526`)
- سقف‌ها (daily cap, fail ceiling, breaker, ask budget, timeout, monthly)
- فلگ‌های مسیریابی (LOCAL_FIRST, ROUTE_SCORER, ROUTE_SHADOW)
- `daily-cost.py` برای خواندن هزینه

### P2.b — Chaos fault×outcome matrix

- ۱۲ سناریو: timeout, rate_limit, breaker recovery, half_open probe, quota, STOP, kill_seam, corrupt JSON, retry bound, IO failure, closed gate, fallback order
- همه pass (۱۰۰٪ consistency, robustness, fault-tolerance)
- شواهد: `test_ti_breaker_chaos.py` + `test_ti_router_snapshot.py`
- فایل: `test_intelligence/fixtures/chaos-matrix.json`

### P2.c — Evidence & trust ladder

- چهار سطح: STRUCTURAL → TESTED → SHADOW → ARMED
- جدولِ ۱۵ قابلیت با سطح و شاهد فعلی
- همه در سطح TESTED (به‌جز dark_capabilities که STRUCTURAL است — اسکنر است نه قابلیت اجرا)
- قواعد ارتقا + ممنوعیت ادعای بدون شاهد

### P2.d — Golden traces

- **BLOCKED**: به sessionهای واقعیِ shadow نیاز دارد (پس از P1 arm)
- زیرساخت آماده: `golden_traces/README.md` با قالب و روش
- پس از ۷ روز shadow: ۵ بهترین + ۵ بدترین

### P2.e — Discovery loop

- ۵ candidate از held-out tasks با FIXED_TRIALS
- همه Novel ∧ Repeatable(5/5) ∧ Useful ∧ Policy-Compliant
- ۵ قابلیت شناسایی‌شده: local-first gate, circuit breaker, action_sha256, content-free memory, schema enforcement
- فایل: `test_intelligence/fixtures/discovery-held-out.json`
- **هیچ arm خودکار** — candidates advisory هستند

## Evidence (paths + commands)

```text
Route policy:       _ops/ROUTE-POLICY.md
Chaos matrix:       _ops/test_intelligence/fixtures/chaos-matrix.json
Evidence ladder:    _ops/EVIDENCE-LADDER.md
Golden traces:      _ops/test_intelligence/fixtures/golden_traces/README.md (blocked)
Discovery:          _ops/test_intelligence/fixtures/discovery-held-out.json
Daily cost:         python _ops/scripts/daily-cost.py

TI red-team:        python _ops/tests/test_ti_redteam_injection.py → 3/3 (25/25 cases)
TI chaos:           python _ops/tests/test_ti_breaker_chaos.py → 10/10
TI router:          python _ops/tests/test_ti_router_snapshot.py → 8/8
```

## Flags touched (before → after)

```text
NO flags armed. All documentation and evidence only.
```

## Gates

- [x] صفر regression در TI red-team (۲۵/۲۵)
- [x] ROUTE-POLICY + هزینهٔ روزانه قابل‌خواندن
- [ ] ≥۱۰ golden traces redacted — **BLOCKED (P1 arm لازم)**
- [x] matrix chaos کامل (۱۲ سناریو)
- [x] هیچ فلگ پول/outbound جدید بدون رأی

## NOT done / blocked

1. **Golden traces** — نیاز به sessionهای واقعی پس از arm
2. **Live chaos day** — P5، staging
3. **Dashboard هزینه/کیفیت** — P5

## Owner decisions needed

1. **Arm P1** — بدون آن golden traces و sessionهای واقعی ممکن نیست
2. **CORTEX_LOCAL_FIRST arm?** — صرفه‌جویی پول، اما کیفیت محلی باید کافی باشد

## Next phase entry criteria

- P3 blocked تا P1 gate سبز
- P2 می‌تواند ادامه پیدا کند (golden traces) پس از P1
