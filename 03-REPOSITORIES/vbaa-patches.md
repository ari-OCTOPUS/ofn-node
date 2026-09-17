---
id: moc-vbaa-patches
status: active
canonical_body: vbaa-patches
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
# MOC — vbaa-patches

بستر review/staging برای سه primitive امنیتی L7: ArtifactAdmission · ArgumentProvenanceGuard · ExecutorHandleFirewall.

- ۳۱ مسیر؛ تست قراردادی: ۲۳ passed + ۱ xfailed + ۲ xpassed (2026-09-17)
- **adoption در ofn-node اثبات نشده**: `_ops/vbaa` روی main صفر مسیر؛ فقط یک ذکر doc
- GAP ثبت‌شده: قرارداد انتقال vault → vbaa-patches → ofn-node وجود ندارد (ساخته نشد — مأموریت صریحاً گفت نساز)
