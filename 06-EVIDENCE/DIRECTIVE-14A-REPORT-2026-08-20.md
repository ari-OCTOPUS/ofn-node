---
type: evidence
task: directive-14A
tags: [telegram, canary, inventory, inbound, f1-f8, 2026-08-20]
created: 2026-08-20T18:45+10:00
created_by: agent B (ZCode) — الحاقیهٔ مالک #14A
paid_calls: 0 · full_loop: PAUSED · live_b: BLOCKED
---

# گزارش ۱۴A — یافته‌ها و اصلاح مسیر canary

```text
BOT INVENTORY (F1 — با bot ID عددی، نه نام):
  bot_id 8187434784 · @Robo2725_bot · «pi 4+1»  · token_fp 4cb748aa889f · TELEGRAM_BOT_TOKEN
  bot_id 7992324219 · @intergrade2725_Bot · «اختاپوس» · token_fp c33098cc078d · TG_CENTER_BOT_TOKEN
  bot_id 8861821707 · @zimangiftbot · «زیمان» · token_fp f0a1c6ccdf4a · TG_ZIMAN_STUDIO_BOT_TOKEN
CANONICAL BOT ID: 7992324219 (مرکز/Outer DM مالک) — مسیر: center.py (پoller tg_api،
  RUN-TG-CENTER.bat :loop) → input_surface_policy.classify → owner_console seam
ACTIVE HANDLERS: 1 (center.py PID 21176→25400، ریاستارت C-047-مطابق با baseline)
  + approval_channel روی TELEGRAM_BOT_TOKEN (پoller کانال تأیید — 409 من از همین بود)
/status event delta: 0→1 — منتظر canary (گیت پایین)
/status reply count: 0 تا canary
quota root cause (F4): ۱۲۲ رسید امروز · فقط 19.7٪ task_id دارند · ۹۸ بی‌انتساب
  (پروسه‌های کدقدیم pre-T50 + مسیرهای build بدون task_id) → ابهام bucket مانند «120/60»
tool-loop duplicates (F5): backlog — spec: normalized_request_key، max 2 تلاش،
  TOOL_REQUEST_QUARANTINED، cooldown 24h، aggregate_not_notify
negative metrics (F6): backlog — spec: raw=-1 → semantic=UNKNOWN → render=«نامعلوم»؛
  لنگر کد: _ops/c6_producer.py:125 UNKNOWN_PROBE="doctor_unknown_root_cause"
notification duplicate rate (F7): backlog — spec: dedupe key
  (subsystem+issue_type+root_cause+state_epoch)؛ هدف <5٪
cortex heard / business_brain heard: خیر (F8 — cognition inbox = مورد ۱۱؛ بعد از گیت ingest)
memory recall proof: — (بعد از canary /remember)
paid calls / AUD: 0 / 0
LIVE-B: BLOCKED · FULL LOOP: PAUSED · commit: همین گزارش
```

## تغییرات کد (هر دو additive؛ نه فایل داغ؛ زیر lease)

1. `_ops/telegram_center/input_surface_policy.py` — `classify` حالا برای مسیرهای DM
   متادیتای `update_id/message_date/chat_id` برمی‌گرداند (رفتار قبلی صفر تغییر).
2. `_ops/owner_console/telegram_adapter.py` — `handle_message` پس از احراز، رویداد
   spine دوزمانی emit می‌کند: occurred_at از `message.date` تلگرام (۱s)،
   `event_time_source=telegram_message_date`، idempotency از
   `tg-{chat}-{date}-{update_id}`، پشت flags (OCTOPUS_T48_EVENT_TIME + OCTOPUS_WIRE_SPINE)؛
   بدون date = بدون رویداد (نه تزریق ساعت). fail-soft مطلق.

ریاستارت مرکز: supervisor `RUN-TG-CENTER.bat :loop` احراز شد (STOP غایب)؛
baseline ثبت (`restart-baseline-center-14a.json`)؛ PID 21176→25400؛ پورت 8776 زنده.

## گیت بعدی (فقط یک /status از مالک)

```text
telegram_events: دقیقاً +1
spine row: موجود با message.date
owner auth: true
local model calls: 0
replies: دقیقاً 1
duplicate handler: 0
```
