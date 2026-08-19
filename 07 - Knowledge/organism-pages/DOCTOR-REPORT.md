# DOCTOR-REPORT (ماشینی)

> machine-generated · grade=MEASURED · منبع: `_ops/doctor_contract/prescription_gate.py` + `_ops/ablation/harness.py` + phase-gates.jsonl

## قرارداد تجویز (گیت فاز ۴)

- هر تجویز: observed_symptom + causal_hypothesis + proposed_mutation + falsification_condition + expected_cost + rollback + evidence_refs.
- B0 → صف مالک (هرگز اینجا تجویز نمیشود)؛ zone ناشناخته → رد.
- هزینه بالای سقف → رد؛ هیچ VERIFIED، حداکثر MEASURED.

## فالسایفر (فاز ۴)

- سه تجویز اجرا شد؛ دو تا ابطال شدند (latency 8>5 و void_rate 0.08<0.10)؛ یکی رد نشد (hit_rate 0.9).
- بدون snapshot = not-evaluable (نه پاس).

## ابلیشن (فاز ۵)

- گیت قابلیتاطمینان علّی است: با گیت K=5 → UNRESOLVED؛ بدون گیت → SECOND_POSITION_BIAS.
- prediction ledger: DELETE → ABORT (تریگر) — append-only علّی.
- حافظه: حذف رکوردِ برتر → انتخاب عوض میشود (شرط لازمِ PROMOTE).

## هشدار θ (منبع: `_ops/state/doctor/self-knowledge-latest.json`)

self_accuracy=1.0 فقط ۳ فیلدِ آسان؛ confidence=null → کالیبراسیون ادعا نمیشود.
