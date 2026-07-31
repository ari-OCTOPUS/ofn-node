# 05 — MUTATION EVIDENCE · ۲۰۲۶-۰۷-۳۱

روش: mutate → اجرای سوییت → ثبتِ exit/قرمز → restore از **کپیِ فایل** (نه
`git checkout --`؛ درسِ ۰۷-۳۰) → پاکسازی `__pycache__` → سبزِ مجدد.
درایورها: `scratchpad/mutate_seams.py` و `mutate_manifest.py` (خروجی عیناً در لاگ چت).

## VQ-STATE-WRITE-001 (opslib.LockedJson + snapshot)

| # | جهش | سوییت | نتیجه |
|---|---|---|---|
| M1 | retry حذف (`range(5)`→`range(1)`) | test_lockedjson_write | exit 1 · ۲ قرمز ✅ |
| M2 | موفقیتِ ساکت (`raise last_err`→`return`) | test_lockedjson_write | exit 1 · ۳ قرمز ✅ |
| M3 | رسیدِ شکست حذف | test_lockedjson_write | exit 1 · ۳ قرمز ✅ |
| M4 | blocker ِ snapshot حذف | test_lockedjson_write | exit 1 · ۲ قرمز ✅ |

## VQ-MISSION-CARD-001 (درزِ کارت)

| # | جهش | نتیجه |
|---|---|---|
| MC1 | گیتِ فلگِ کارت حذف | exit 1 · ۳ قرمز ✅ |
| MC2 | dedup (چکِ همهٔ bucketها) حذف | exit 1 · ۲ قرمز ✅ |
| MC3 | فیلترِ needs_approval/requires_approval حذف | exit 1 · ۳ قرمز ✅ |
| MC4 | متنِ هدف (intent) واردِ title کارت | exit 1 · ۲ قرمز ✅ |
| MC5 | درزِ beat حذف (`card_enabled()`→`False`) | exit 1 · ۲ قرمز ✅ |

## §۱۰.۴ Memory read (درزِ بازیابی)

| # | جهش | نتیجه |
|---|---|---|
| MR1 | گیتِ فلگِ حافظه حذف | exit 1 · ۳ قرمز ✅ |
| MR2 | dump ِ متنِ خام به‌جای ساخت‌یافته | exit 1 · ۲ قرمز ✅ |
| MR3 | fail-soft حذف (raise) | exit 1 · ۲ قرمز ✅ |

## §۱۲ Manifest truth (capability_registry)

| # | جهش | نتیجه |
|---|---|---|
| MF1 | manifest ِ نامعتبر واردِ فهرستِ معتبر | exit 1 ✅ (جهشِ §۱۷.۲-۱۵) |
| MF2 | گزارشِ نامعتبر ساکت | exit 1 ✅ |

## نگاشت به جهش‌های اجباری §۱۷.۲ مگاپرامپت

| §۱۷.۲ | پوشش |
|---|---|
| 1 stale→AUTHORITATIVE · 2 حذفِ freshness blocker | از قبل در `test_snapshot_staleness` (۱۰/۱۰؛ سنجهٔ رفتاریِ ۰۷-۳۰) — این جلسه دوباره سبز تأیید شد |
| 3 unknown→A0 · 4 missing prereg · 5 external→safe · 7 receipt-fail→success · 8 illegal transition · 16 متن→مجوز | از قبل در `test_goal_action_bridge` M1..M18 ِ ۰۷-۳۰؛ این جلسه ۱۴/۱۴ سبز پس از رفعِ CONFLICT |
| 7 (write-receipt) | این جلسه: M2/M3 بالا |
| 10 memory→authorization · 11 untrusted→trusted | این جلسه: MR1/MR2 + سنجهٔ `t_memory_is_never_authority_over_the_plan` |
| 13 unknown callback · 14 core→group | سوییت‌های ثبت‌شدهٔ tg (callback/legs-only/access-model) |
| 15 manifest invalid→LIVE | این جلسه: MF1/MF2 |
| 17 shadow heart→authoritative | `test_snapshot_staleness` + `heart` shadow-only (لمس نشد) |
| 18 missing probe→LIVE | manifest ِ world_discovery صریحاً TESTED_NOT_WIRED اعلام می‌کند + MF1 |
| 6 expired authorization · 9 duplicate action_id · 12 missing evidence | پوشش این جلسه نه — در action_bridge ِ خودش تست دارد (idempotency/owner_gate ۰۷-۳۰)؛ دوباره جهش نزدم |
