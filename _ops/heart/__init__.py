"""_ops/heart — قلبِ تکاملیِ ترکیبی (hybrid heart).

ضربان = velocity (توان‌عبورِ واقعیِ شناخت) · SOG = باندِ هدف (setpoint، نه نرخ) ·
Governor = autoregulation بین ضربان و spend · Internal-CPI = نویزِ واسط (تورم).

قانون: ADR-001 (coupled-not-merged؛ Doctor فقط HeartParams می‌نویسد، نرخ از dynamics
ظاهر می‌شود) + HYBRID-HEART-MASTER-PLAN + پرامپت‌های HH-P0..P7 در
`04 - Architect System/octopus-build-prompts/`.

ماژول‌ها:
  sog_math         — HH-P0: قفلِ ریاضیِ SOG (MC مستقلِ E_shadow/I_pred) → lock-file
  producers        — HH-P1: velocity_meter · internal_cpi · delta_self_estimator (Gate-0)
  interface        — HH-P2: HeartParams/HeartSignal (typed، ratify ADR-001)
  autoregulation   — HH-P3: کوپلِ velocity→Governor→spend (additive، پشتِ flag)
  control_law      — HH-P4: قانونِ Living-Beat (velocity-first؛ σ فقط ترمز)
  sim_heart        — HH-P4: اثباتِ closed-loop (Gate-B، loop-gain G<1) → SIM-REPORT
  shadow           — HH-P5: shadow_step + production_wire_open (predicate ۸شرطی)
  doctor_setpoint  — HH-P6: مدولاتورِ w-slow (باندِ target-velocity، هرگز نرخ)

خطوطِ قرمزِ پکیج: stdlib-only · $0 تا live-gate · read-only نسبت به منابعِ پول/chrono ·
هیچ self-grading (provenance خارجی) · shadow هرگز period ارگانیسم را نمی‌نویسد.
"""
