# ✅ VaultScanner VERDICT_QUEUE

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| MAP-V1 | scan همین workspace انجام شود؟ | yes/no | open | fresh inventory |
| MAP-V2 | report قبلی F:\backup آرشیو/برچسب شود؟ | yes/no | open | جلوگیری از drift |
| LB-V1 | mirror محتوادار `06-EVIDENCE/OCTOPUS-HANDOFF-MERGE-2026-08-22/merged/CURRENT-TRUTH.md` به pointer تبدیل شود؟ | convert-to-pointer / keep+label / open | **رأی مالک ۲۰۲۶-۰۹-۰۲: convert-to-pointer — اجرا شد** (محتوا بایت‌به‌بایت در 99-ARCHIVE\mirror-cleanup-20260902) | بستن لغزندگی mirror |
| LB-V2 | ارجاع `06-EVIDENCE/C-NNN-*.md` در LEDGER-VS-CONTRADICTIONS.md (NNN literal بود) | re-anchor / mark-placeholder / open | **رأی مالک ۲۰۲۶-۰۹-۰۲: re-anchor به C-0\* — اجرا شد** | درست‌بودن لجر تناقض‌ها |
| LB-V3 | ارجاع `scripts/verify_live_store.py` ×۲ در 01-TRUTH (فایل در والت نیست) | strike / restore / open | **رأی مالک ۲۰۲۶-۰۹-۰۲: strike — اجرا شد** (متن تاریخچه حفظ، backtickها برداشته شد) | اعتبار اسناد حقیقت |
| LB-V4 | ۷ فایل junk ریشهٔ والت | archive-move / keep / open | **رأی مالک ۲۰۲۶-۰۹-۰۲: archive-move — اجرا شد** (99-ARCHIVE\root-junk-20260902 با پیشوند archive_) | بهبود نه حذف (AGENTS.md §7) |
| LB-V5 | زمان‌بندی ۲۱ اندام گمشدهٔ self-backlog دکتر | lane-C-D / سه‌فوری / defer | **رأی مالک ۲۰۲۶-۰۹-۰۲ شب: سپردن به لین C/D** (ثبت: ECONOMIC-LEARNING-RULINGS-2026-09-02 رأی ۵) | نقشهٔ راه اندام‌سازی |
