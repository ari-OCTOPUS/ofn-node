# VERDICT_QUEUE append payload — Lane LB (self-completing doctor), 2026-09-02

Target file (canonical): `F:\backup\06 - Architecture Maps\نقشه-اختاپوس\VERDICT_QUEUE.md`
Proposed action: APPEND the rows below to the existing table (after MAP-V2).
Not written directly — collision protocol per owner directive (Lane B, VERDICT_QUEUE section).

Source: doctor round 2026-09-02-final (read-only, proven), receipt
`09-LANES/LB/runs/2026-09-02-final/receipt.jsonl` (27 lines, all sha256-verified).

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| LB-V1 | mirror محتوادار `06-EVIDENCE/OCTOPUS-HANDOFF-MERGE-2026-08-22/merged/CURRENT-TRUTH.md` (6517 بایت، sha 7354caf8…) به pointer تبدیل شود؟ (نقض سیاست کانونیکال 2026-09-02) | convert-to-pointer / keep-merged-snapshot+label / open | open | بستن لغزندگی mirror؛ حقیقت یک‌پارچه |
| LB-V2 | ارجاع wildcard `06-EVIDENCE/C-NNN-*.md` در LEDGER-VS-CONTRADICTIONS.md به چه چیزی گره بخورد؟ (الان هیچ فایلی ماتچ نمی‌کند) | re-anchor-to-C-001..016 / mark-unmaterialized / open | open | درست‌بودن لجر تناقض‌ها |
| LB-V3 | ارجاع دوبارِ `scripts/verify_live_store.py` در 01-TRUTH (STATE + TEST-COUNT) — فایل در هیچ‌جای والت نیست | restore-file / strike-the-refs / open | open | اعتبار اسناد حقیقت |
| LB-V4 | ۷ فایل junk ریشهٔ والت (debug-*.log ×5 + دو فایل assertion-نام) به `99-ARCHIVE/root-junk-20260902/` منتقل شوند؟ | archive-move / keep / open | open | بهبود نه حذف (AGENTS.md §7) |
| LB-V5 | زمان‌بندی ۲۱ اندام گمشدهٔ self-backlog دکتر (خلاصه: novelty gate، budget allocation، lab sandbox، prescriptions) | schedule-via-lane-C-D / defer / open | open | نقشهٔ راه اندام‌سازی اختاپوس |
