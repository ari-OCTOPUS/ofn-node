---
type: "reference"
status: "🟢"
scan: "2026-07-29"
tags:
  - state
  - قرارداد
---

# قراردادِ فایل‌های state دکتر — `90-_meta/state/`

منبع: خودِ سورس (نه حدس). هر بخش با فایل:خط. **این‌ها دادهٔ دکترند؛ فایل‌های
هم‌نامِ `_ops/state/` مالِ ارگانیسم‌اند و قالبِ متفاوتی دارند — هرگز قاطی نشوند.**

## missions.json — `daemon.py:36-65`

لیستی از دیکت‌ها با `"schema": "doctor-mission.v1"`. فیلدها از دیتاکلاسِ `Mission`:
`mission_id` · `title` · `state` · `risk` · و بقیهٔ فیلدهای dataclass.
`state` فقط یکی از: `proposed | running | awaiting-merge | merged | rejected | failed`.
«باز» یعنی state در (`proposed`, `running`, `awaiting-merge`) — `daemon.py:51`.
اگر فایل نباشد یعنی هنوز هیچ ماموریتی ساخته نشده.

## tg-outbox.jsonl — `channel.py:173-188`

هر خط یک JSON:

```json
{"ts": 1753.0, "mission_id": "m-x", "gate": "intent",
 "payload": {"chat_id": "", "text": "...", "parse_mode": "Markdown",
   "disable_web_page_preview": true,
   "reply_markup": {"inline_keyboard": [[
     {"text": "✅ تأیید", "callback_data": "ok:intent:m-x"},
     {"text": "❌ رد", "callback_data": "no:intent:m-x"}]]}}}
```

`gate` ∈ (`intent`, `diff`, `test`). کارتِ بی‌دکمه `reply_markup` ندارد.
در حالتِ direct فیلدِ `result_ok` هم اضافه می‌شود.

## tg-inbox.jsonl — `channel.py:245-277`

هر خط یک رأی:

```json
{"mission_id": "m-x", "gate": "intent", "approved": true,
 "voter_id": 123, "callback_id": "890", "ts": 1753.1}
```

خطِ ردشدهٔ غیرمالک فیلدِ `"ignored"` دارد و در شمارش نمی‌آید.
**کارتِ بی‌رأی** (`pending` — `channel.py:190-194`): مجموعهٔ کلیدهای
`mission_id:gate` در outbox **منهای** همان کلیدها در رأی‌های معتبرِ inbox.

## fugu-quota.json — `fugu.py` (کلاسِ Quota)

```json
{"day": "2026-07-29", "used_total": 3, "spent_usd": 0.44, "unpriced_calls": 1}
```

روزِ نو ⇒ ری‌ست. ⛔ فایلِ هم‌نامِ `_ops/state/fugu-quota.json` مالِ ارگانیسم است
با قالبِ متفاوت (`used{}`, `consecutive_failures`, `denied{}`) — R-09: دکتر به آن
دست نمی‌زند و از آن نمی‌خواند.

## paid-calls.jsonl — `fugu.py::_receipt`

رسیدِ هر فراخوانِ پولی: `ts، actor، provider، model، effort، shape، ok،
tokens_in، tokens_out، cost_usd (null=تعرفهٔ نامعلوم)، ms، quota_used،
spent_usd_today`.
