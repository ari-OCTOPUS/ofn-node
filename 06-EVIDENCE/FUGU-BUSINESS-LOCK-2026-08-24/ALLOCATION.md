# ALLOCATION 14 days (2026-08-24 .. 2026-09-07)

## Hard rules
1. Allowlist only: Ziman | Studio (dry captions/planning) | Master Painting
2. Deny: ARCHITECT_SYS, Mining, WLOS, eToro, random research, cyber unless owner GO
3. Prefer model=fugu; fugu-ultra only for hard money tasks
4. Never silent PAYG: stop at subscription quota; alert owner
5. Log every call: business + task_id + model + usage totals (incl orchestration)

## Split of weekly Max window
- Ziman 50%
- Studio 30%
- Painting 20%

## Soft daily
- ~7% of weekly Max window then stop Fugu that day (leave buffer for spikes)

## Capacity math (ESTIMATE from public + DevelopersIO Standard trial; NOT Sakana official token count)
Official: Max = 20x Standard. Exact tokens unpublished. Quota = rolling 5h% + weekly%.

DevelopersIO Standard sample after 3xfugu + 3xultra + 1xcodex:
- ~89k total tokens (≈35k surface + ≈54k orchestration ≈ 60% orch)
- 18% of 5-hour quota, 6% of weekly quota

Scaled to Max (x20):
- Same session ≈ 0.9% of Max 5h, ≈ 0.3% of Max weekly
- Rough Max weekly capacity ≈ 100 / 0.3 ≈ 330 of those mixed sessions
- Or: one heavy Ultra codegen alone was >10% Standard 5h → ≈ 0.5% Max 5h → ~200 heavy Ultra calls per Max 5h window (theoretical upper; do NOT plan at the ceiling)

Practical 14-day plan (conservative, Ultra-sparing):
- Daily soft: ~15–25 light fugu calls OR ~2–4 medium Ultra calls (not both at max)
- Weekly soft: keep Ultra under ~40% of weekly window; fill rest with fugu
- Two-week target: empty almost all remaining Max allowance into the 3 businesses, WITHOUT crossing into PAYG

## Pay-as-you-go danger (if overshoot)
Ultra: $5/$30 per 1M in/out (<=272K). Orchestration billed same. One Ultra codegen ~29k tokens in sample ≈ order $0.5–$1+ depending mix — stacks fast.
