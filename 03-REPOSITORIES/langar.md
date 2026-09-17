---
id: moc-langar
status: active
canonical_body: langar
source_repo: none
source_path: 09-LANES/UNIFIED-RECON-20260917
created_at: 2026-09-17
verified_at: 2026-09-17
supersedes: []
superseded_by: []
mirrors: []
evidence_grade: E2
sensitivity: internal
---
# MOC — langar

زیرسیستم Telegram/HRV/پژوهش — خفته، deployable، **ایزوله از money path**.

- ۹۷ مسیر؛ دو خانوادهٔ `langar/` و `langar-pro/`
- هیچ import از ofn (دو طرف)؛ هیچ سرویس روی board-138 (زنده بررسی 2026-09-16T23:47Z؛ ممیزی 08-27 برای 180/182 هم همین را می‌گوید)
- تست: harness مستقیم 13+22 سبز؛ `pytest` عمومی collection می‌شکند (SystemExit در module scope)
- بدهی‌ها: `_verify/` کپی سایه (drift v3/v8 در ممیزی) · `.fuse_hidden…` در git track شده · P1 امضای synthesizer (ممیزی؛ دوباره اندازه‌گیری نشده)
