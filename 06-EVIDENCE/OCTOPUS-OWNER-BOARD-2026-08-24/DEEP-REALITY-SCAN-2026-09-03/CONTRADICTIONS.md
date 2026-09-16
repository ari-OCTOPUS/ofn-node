# CONTRADICTIONS — 2026-09-03 (هیچ‌کدام با حدس حل نشدند)

- contradiction_id: RC-1
  claim_a: «first send = Sep 1 13:16:59Z fact; OWNER RULED AUTHORIZED»
  source_a: حافظهٔ ایجنت + رأی Q-05 (2026-09-02)
  claim_b: «first send + first payment receipt (PAINT-L5-001) still PENDING»
  source_b: CURRENT-TRUTH بخش Day-7 close-out (قبل از update عصر)
  runtime_priority_source: رأی مالک + sqlite outbox (۵ sent واقعی)
  status: OPEN (روایت کهنه در دو سند قدیمی زنده است)
  risk: متوسط — سردرگمی ایجنت تازه
  required_verification: برچسب superseded روی سندهای قدیمی (با نقل‌قول)

- contradiction_id: RC-2
  claim_a: «NTP 138 خاموش، +0.5s drift»
  source_a: MISSING-WIRING-50 #47 (2026-09-02)
  claim_b: «NTPSynchronized=yes»
  source_b: timedatectl (2026-09-03T07:23Z)
  runtime_priority_source: runtime
  status: RESOLVED_BY_RUNTIME (ترمیم بین دو اسکن) — سند census نیازمند یادداشت History
  risk: کم
  required_verification: –

- contradiction_id: RC-3
  claim_a: «outbox 182: 2330 verdict بی‌ارسال»
  source_a: MISSING-WIRING-50 #37 (09-02)
  claim_b: «wrapper ارسال 21/21 انجام شد» + «138 outbox=0»
  source_b: رسید healing-wave (09-03) + ssh امروز
  runtime_priority_source: runtime
  status: OPEN (سه اسنپ‌شات در ۲۴ ساعت؛ منبع واحد وضعیت صف وجود ندارد)
  risk: متوسط
  required_verification: شمارندهٔ ماندگار per-queue با ts

- contradiction_id: RC-4
  claim_a: telegram_bridge «live» در IGNITION
  source_a: docs survival
  claim_b: «inactive»
  source_b: CURRENT-TRUTH (census#27)
  status: OPEN · risk: متوسط · required_verification: وضعیت واقعی سرویس

- contradiction_id: RC-5
  claim_a: «fullest tree = fix/demand-harvest لپ‌تاپ»
  source_a: CURRENT-TRUTH warning
  claim_b: «deployed = main@60dce961»
  source_b: ssh 138 (2026-09-03)
  status: OPEN · risk: بالا برای deploy · required_verification: رأی مالک روی منبع deploy

- contradiction_id: RC-6
  claim_a: «journal 138: صفر firing»
  source_a: journalctl -u (امروز)
  claim_b: «۱۰ تایمر تازه fire»
  source_b: list-timers (همان لحظه)
  runtime_priority_source: list-timers
  status: RESOLVED_AS_VISIBILITY (کاربر خارج از گروه journal) — برای ثبت ماند
  risk: کم

- contradiction_id: RC-7
  claim_a: سیاست append-only/نظم والت
  source_a: canonical policy 09-02
  claim_b: والتن گیت dirty=400 روی برنچ rescue
  source_b: git status (امروز)
  status: OPEN · risk: بالا (از دست رفتن رسیدها) · required_verification: کامیت انتخابی هدفمند

- contradiction_id: RC-8
  claim_a: «۱۵۷/۱۵۷ تست دکتر»
  source_a: OCTOPUS-DOCTOR/README
  claim_b: «168/168 (دوبار اندازه‌گیری)»
  source_b: اجرای مستقیم 09-02
  runtime_priority_source: runtime
  status: OPEN (سند کهنه) · risk: کم · required_verification: به‌روزرسانی README با نقل‌قول
