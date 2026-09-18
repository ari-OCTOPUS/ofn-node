# C2-ACTIVATION-20260908 — port spec (evidence-complete, ready to execute)

GOV_VERSION=V8 · LADDER=L2 · رأی مالک (OWNER-APPROVALS-2026-09-08، ۴گزینه‌ای):
«فعال‌سازی کامل C2 (پیشنهاد)» — مهاجرت board_cp به API جدید + رأی فلگ.

## یافته‌های قطعی (این نشست)
- bridge جدید: `CommandState`/`Command`/`TERMINAL_STATES`/`utcnow`/`canonical_json` در
  models.py؛ `ALLOWED_TRANSITIONS` در store.py:55؛ **`iso`/`now_utc`/`new_id`/
  `parse_iso`/`transition_allowed` هیچ‌کجا وجود ندارند** ⇒ باید در schema.py
  محلی بازنویسی شوند.
- `Command` جدید ابرمجموعهٔ فیلدهای build_command است (message_id…correlation_id ✓،
  +causation_id/traceparent اختیاری). **تنها بررسیِ مانده: آیا `parameters`
  هنوز فیلد است** (build_command متن را در parameters می‌گذارد؛ اگر نبود →
 迁移 به فیلد مجاز یا OperationSpec).
- سمت 138 از قبل مسلح: OCTOPUS_BOARD_CP_PULL=1 + CONTROL_URL=cp.master-painting.com.

## مراحل اجرا
1. schema.py: ایمپورت‌های محلی (iso=strftime, now_utc→utcnow, new_id=uuid4,
   parse_iso=fromisoformat, transition_allowed=wrap store.ALLOWED_TRANSITIONS)؛
   ALLOWED_TRANSITIONS از store. افزودنی؛ مصرف‌کننده‌های قدیمی همان نام‌ها.
2. تست: xfailِ test_drive_mirror.py برداشته شود → انتظار 3/3.
3. فلگ با رسید (الگوی round-6): OCTOPUS_BOARD_CP=1 در OCTOPUS-flags.cmd با
   pre-image sha + رسید در همین lane؛ بررسی .env برای OCTOPUS_BOARD_CP_BEARER
   (فقط نام) و TLS dir (_ops/state/board_cp/tls).
4. دیمن در ری‌استارتِ طبیعی بعدی فلگ را برمی‌دارد (پروسیجر 900s مالک)؛
   E2E واقعی: اولین lock-opened بعد از فعال‌سازی → ردیف در commands.sqlite →
   pull 138 (~2min) → رسید mirror-log.jsonl.
