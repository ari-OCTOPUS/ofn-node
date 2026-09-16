---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, verifier, handshake, three-node]
created: 2026-08-18
updated: 2026-08-18
created_by: agent
sources:
  - "[[../../agent-prompts/MEGAPROMPT-VERIFIER-00-SHARED-CONTRACT-2026-08-18]]"
  - "[[../../00 - Inbox/2026-08-18 NOTE — verification doctrine activation order (laptop first)]]"
  - "[[../../06-EVIDENCE/EVIDENCE-ENVELOPE-CYCLE-01-2026-08-18]]"
---

# ۶۶ — Evidence Envelope سه‌گرهی (Verifier Pattern، 2026-08-18)

WAVE0. autonomy_delta=0. Structural Gate (`GITWRITE-FAILED` + OBSERVE_ONLY) سر جایش است.

## یک پاراگراف

مالک سه مگاپرامپت راستی‌آزمایی داد: لپ‌تاپ منبع حقیقت، Sensorium حس/گیت، پاها بدن/پول.
قرارداد مشترک = پاکت هندشیک تایپ‌شده با شاهد خام. بزرگ‌ترین علت خرابی چندعاملی
هندشیک ضمنی است نه کمبود هوش. پیاده‌سازی لپ‌تاپ **سایدکار** است
(`_ops/handshake/`) نه پچ دیمون TCB. Sensorium v2 فقط بعد از تأیید cycle-1.
پاها آخرین.

## کجا چیست

- قرارداد + سه پرامپت: `agent-prompts/MEGAPROMPT-VERIFIER-0{0,1,2,3}-*-2026-08-18.md`
- لانچر Inbox: [[../../00 - Inbox/2026-08-18 MEGAPROMPT — Verifier Pattern Three Nodes]]
- پاسخ به برد: [[../../00 - Inbox/2026-08-18 NOTE — Laptop Evidence Envelope cycle-1]]
- کد: `_ops/handshake/envelope.py` · صدور: `_ops/handshake/emit_cycle.py`
- تست (خارج از `run_all.py`): `_ops/tests/test_evidence_envelope_handshake.py`
- شواهد: [[../../06-EVIDENCE/EVIDENCE-ENVELOPE-CYCLE-01-2026-08-18]]
- پاکت مشاهدهٔ EQUIP G3 جدا است: `_ops/observatory/envelope.py`

## سقف تلاش / escalation

۳ دور. بعد مالک. unknown_outcome را فقط مالک می‌بندد. P-ACK-1 باطل است.
