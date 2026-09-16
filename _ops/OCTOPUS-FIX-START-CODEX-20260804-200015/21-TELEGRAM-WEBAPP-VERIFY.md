# 21 — Telegram/WebApp adapter verification

Read `_ops/intel_spine/telegram_adapter.py` (97 lines) and `webapp_adapter.py` in full.

## telegram_adapter.py

- `log_incoming(update, owner_id)`: extracts text/chat_id/from_id from a Telegram Bot-API
  shaped dict, detects `/stop`/`/halt`/`/kill` prefixes (marked `d_level="D0"`,
  `safety_verdict="allow"` for those specifically), then calls
  `intel_spine.log_interaction(...)` — a local append only.
- `log_outgoing(chat_id, text, stream)`: docstring is explicit — **"این تابع پیام ارسال
  نمی‌کند. فقط log می‌کند."** (this function does not send a message, only logs). Confirmed
  by reading the body: it calls only `intel_spine.log_interaction`.
- `log_callback(...)`: same pattern for button-press callbacks.
- All three wrap their body in try/except returning `None` on failure — a logging failure
  can never raise up into the caller (center.py), so it cannot block `/stop` or any other
  real command.
- No `send_text`, no bot-API call, no `requests`/`socket` import anywhere in the file.

## webapp_adapter.py (37 lines, read in full)

Request metadata only (method/path/read-vs-mutating classification) passed into
`intel_spine.log_interaction`; no request body is captured (per the file's own naming —
"no-body request logging" per the commit message, confirmed structurally: the function
signature does not accept or forward a body/payload argument).

## Test confirmation

`test_adapters_obsidian.py` — 15/15 pass, including: `telegram log_incoming`,
`telegram no raw chat_id in events` (asserts the literal test chat_id value does NOT appear
in the logged JSONL — a real leak-detection test, not just a type check), `telegram
log_outgoing`, `telegram log_callback`, `telegram /stop logged`, `webapp log_request
read-only`, `webapp log_request mutating`.

## Status: PASS — genuinely no-outbound, genuinely no raw chat_id, genuinely
logger-failure-independent of `/stop` handling.
