---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, migration, beat-lease, discovery]
created: 2026-08-16
updated: 2026-08-16
created_by: agent
sources:
  - "[[../06-EVIDENCE/BEAT-OWNERSHIP-LEASE-2026-08-16]]"
  - "[[../07 - Knowledge/شناخت-اختاپوس/57-LAPTOP-TO-ARM1-MIGRATION-2026-08-16]]"
---

# DISCOVERY — مهاجرت: مالکیت حقیقت، نه کپی پوشه

جملهٔ اصلی: **تو کد را منتقل نمی‌کنی، مالکیت حقیقت را منتقل می‌کنی.** پایان = لپ‌تاپ بسته، هیچ اتفاقی نمی‌افتد.

## YOU ARE HERE

فاز ۰ fencing lease روی دیسک است: `_ops/runtime/beat_lease.py` · ۱۷/۱۷ pytest · CLI `status` = VACANT. به chrono وصل نیست. بعدی = [[../agent-prompts/MEGAPROMPT-MIGRATE-CLOSE-GAPS-2026-08-16|مگاپرامپت بستن جاافتادگی]] (M0 + دیباگ dual-lease).

نوت: [[../07 - Knowledge/شناخت-اختاپوس/57-LAPTOP-TO-ARM1-MIGRATION-2026-08-16|۵۷]] · FPGA: [[../07 - Knowledge/شناخت-اختاپوس/58-FPGA-REFLEX-LAYER-2026-08-16|۵۸]] (خرید نه)

## کارت رأی

- [ ] **`lease.assert_valid()` قبل از هر beat** در `_tick_decision` (پیشنهاد: `pause`). تا رأی، CLI freeze بی‌اثر است.
- [ ] **`on_event` → لجر** (Arm 2 وقتی آمد؛ تا آن وقت jsonl سایه مجاز است نه genome زنده بدون رأی).
- [ ] **هر نوشتن state/لجر/بودجه با fencing token.**
- [ ] **اسکریپت M0** — hardcode / CRLF / case-fold.
- [ ] **قبل از M3:** rollback واقعی.
- [ ] FPGA: فقط ضبط داده (G1). خرید نه.

شواهد: [[../06-EVIDENCE/BEAT-OWNERSHIP-LEASE-2026-08-16|BEAT-LEASE]]
