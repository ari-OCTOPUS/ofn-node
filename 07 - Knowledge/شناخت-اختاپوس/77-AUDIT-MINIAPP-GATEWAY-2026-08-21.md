---
type: architecture-audit
status: evidence-backed
date: 2026-08-21
session_id: SESSION-20260820-21
scope: miniapp_gateway.py — code-level audit and requirements
current_head: 4faad7d
paid_calls: forbidden
memory_production_writes: forbidden
---

# AUDIT — معماری درگاه AGI اختاپوس (miniapp_gateway.py)

این سند، ممیزی سطح-کد درگاه مالک است: چه چیزی پیاده‌سازی‌شده (با مسیر واقعی)، چه چیزی
شکاف است (با مشخصات پیاده‌سازی)، و هر دو با اصل fail-closed. عددها و مسیرها از کد
فعلی استخراج شده‌اند، نه حدس.

## ۰) خلاصهٔ ممیزی

| مؤلفه | وضعیت | شواهد |
|---|---|---|
| HMAC-SHA-256 initData | ✅ پیاده‌سازی‌شده | `telegram_center/miniapp_gateway.py` (بایند 127.0.0.1:8774) |
| درگاه تک‌مقصد تونل | ✅ پیاده‌سازی‌شده | docstring PLAN-T4 §۱–۳ |
| Kill switch | ✅ پیاده‌سازی‌شده | فایل `STOP-MINIAPP` → 503 |
| Redaction دولایه | ✅ پیاده‌سازی‌شده | مسیر proxy + redaction دوباره |
| مدیریت 429 (کران‌دار) | ✅ پایه موجود | `tg_api.py: _429_MAX_RETRIES=1, _429_RETRY_CAP_S=30` |
| صف rate-limit با backoff/jitter | ❌ شکاف | نیازمند RateLimitQueue |
| Webhook + secret_token | ❌ شکاف | مرکز polling است؛ بدون کلید webhook در config |
| حلقهٔ رویداد یکپارچه (memory+agentic) | 🟡 ناقص | hub موجود؛ اتصال read-only + ledger لازم است |
| لاگ‌های پایدار از طریق رابط تلگرام | 🟡 ناقص | لاگ‌ها موجودند؛ مسیرهای cockpit/miniapp باید کامل شوند |

## ۱) منطق اعتبارسنجی امضا (HMAC-SHA-256)

الگوریتم دقیق (پیاده‌سازی‌شده در `miniapp_gateway.py` — دیوار §۲):

```
1. پارس query string (parse_qsl)
2. حذف پارامتر hash
3. مرتب‌سازی الفبایی پارامترهای باقی‌مانده
4. اتصال با "\n" به‌صورت key=value → data_check_string
5. secret_key = HMAC_SHA256(key=b"WebAppData", msg=bot_token)
6. signature = HMAC_SHA256(key=secret_key, msg=data_check_string)
7. hmac.compare_digest(signature, hash) — مقایسهٔ زمان‌ثابت
8. auth_date ≤ now + 300s ؛ user.id == TELEGRAM_OWNER_CHAT_ID
```

الزامات تکمیل:

- **آزمون منفی** (T-05): تغییر یک بایت از initData → رد؛ hash جعلی → رد؛ auth_date منقضی →
  رد؛ user غیرمالک → رد؛ replay همان initData پس از ۳۰۰s → رد.
- **ثبت ردّ**: پاسخ 403 با بدنهٔ خالی (بدون اطلاعات)، اما ردیف audit با دلیل طبقه‌بندی‌شده
  (بدون token/chat id خام).
- **مقاومت زمان‌ثابت**: `hmac.compare_digest` در همهٔ مقایسه‌ها، از جمله secret_token وب‌هوک.

## ۲) مکانیزم صف برای Rate Limit (HTTP 429)

واقعیت: `tg_api._call_post` روی 429 تا سقف `_429_RETRY_CAP_S=30` احترام می‌گذارد و فقط
`_429_MAX_RETRIES=1` تلاش مجدد دارد؛ `_retry_after_from_429` مقدار `parameters.retry_after`
را استخراج می‌کند. این fail-safe است، ولی **صف نیست**: پیام‌ها drop می‌شوند.

مشخصات `RateLimitQueue` (پیشنهادی):

```
class RateLimitQueue:
  - token bucket: 1 msg/s per chat، 30 msg/s global (سقف تلگرام)
  - enqueue(message) → bucket؛ ظرفیت خالی → صف FIFO با اولویت critical
  - on 429: خواندن retry_after (تا سقف 30s)، backoff = retry_after + jitter(0..1s)
  - تلاش مجدد = ۱ بار؛ شکست دوم → DLQ (هرگز حلقهٔ بی‌نهایت)
  - دو شمارندهٔ مستقل: business_attempts / delivery_attempts
  - coalescing: پیام‌های هم‌نوع در پنجرهٔ ۵s → یک digest (count + last_seen)
  - خروجی از صف فقط از طریق sender تک‌مالک (single-owner sender)
```

نکتهٔ حیاتی (مستند در SOP §۴): 429 بات را **کاملاً** بلاک می‌کند، نه فقط یک چت؛ پس صف
و coalescing پیش‌شرط ارسال زنده‌اند، نه بهبود.

## ۳) حلقهٔ رویداد یکپارچه: memory محلی + فراخوانی‌های agentic

معماری هدف (façade واحد — هر دو مسیر Telegram و Mini App به همین حلقه):

```
miniapp_gateway / telegram center
  → orchestrator (conversation_hub.router — typed، extra="forbid")
      → memory lane:   sqlite3.connect(f"file:state/memory/memory.db?mode=ro", uri=True)
                       فقط خواندن؛ VETO از owner_fact؛ retrieval با goal_key
      → cortex lane:   fallback محلی/propose-only؛ DEGRADED_LOCAL_ONLY صریح
      → mcp lane:      allowlist + budget؛ بدون budget → propose
  → provenance: event_id / correlation_id / task_id / run_id (از durable context)
  → decision ledger: append-only immutable (decision-record.jsonl)
  → durable outbox → Telegram delivery → receipt → readback
```

الزامات:

- **Memory read-only**: اتصال با `mode=ro` (مثل WAVE1-PREFLIGHT: hash قبل/بعد یکسان)؛
  هیچ مسیری از gateway نتواند write کند (write guard: F3 + two-phase admission + quarantine).
- **Agentic calls**: propose-only؛ هر effect بیرونی فقط پس از تصمیم ledger و با task_id.
- **Unified loop**: یک حلقهٔ poll/event برای هر دو سطح (Telegram و Mini App)؛ دو مسیر
  موازی approval ممنوع — هر دو façade روی همان ledger.
- **Budget هر حلقه**: max_retries، timeout، kill_switch، rollback — هیچ حلقه‌ای بی‌سقف نباشد.

## ۴) لاگ‌های پایدار، قابل‌دسترس از طریق رابط تلگرام

فهرست واقعی لاگ‌های ماندگار (state/telegram/):

| لاگ | محتوا | دسترسی کنونی |
|---|---|---|
| `inbound-log.jsonl` | هر update ورودی (بدون متن خام) | cockpit /loops، /receipts |
| `miniapp-hits.jsonl` | هر درخواست gateway + authed | — |
| `brain-receipts.jsonl` | رسید مغزها | — |
| `tg-send-log.jsonl` | هر ارسال + message_id/ok | /receipts |
| `event-bridge-outbox.jsonl` | صف push رویدادها | /dlq |
| `reconciliation-queue.jsonl` | صف reconciliation تحویل | /dlq |
| `digest-buffer.jsonl` | بافر digest | — |
| `legacy-coerce.jsonl` | coerceهای legacy | — |

الزامات:

- **persistence**: append-only + rotation با سقف اندازه (بدون حذف تاریخچه)؛ همهٔ لاگ‌ها
  در git قابل‌بازبینی (درخت state).
- **دسترسی از طریق رابط تلگرام**:
  - Cockpit: `/loops`، `/receipts <task_id>`، `/dlq`، `/memory_status`، `/brain_status` (موجود در
    `owner_console/local_commands.py`) — خلاصه + evidence reference، نه dump.
  - Mini App: مسیرهای فقط-خواندنی `/api/logs/<kind>?since=` و `/api/status` روی 8774 با
    همان auth HMAC؛ خروجی JSON محدود (آخرین N ردیف، redactشده).
- **بدون secret**: token/chat_id خام/raw payload در هیچ لاگ؛ redaction در لایهٔ نوشتن
  (parity با `center.py:_scrub`).
- **freshness**: داشبورد بدون event تازه، stale است؛ `last_round_ts` نمایش داده شود.

## ۵) ماتریس تست اجباری

| تست | هدف | وضعیت |
|---|---|---|
| T-05 initData دستکاری‌شده رد شود | auth | REQUIRED |
| T-08 restart → resend صفر | outbox | ✅ موجود (durable_loop 15/15) |
| T-21 webhook+polling dual-ingestion صفر | ingestion | REQUIRED (پس از webhook) |
| T-22 ۴۲ درز = یک digest | rate/coalescing | REQUIRED |
| 429-queue بدون retry-storm و بدون drop | rate | REQUIRED |
| F3/staging/write-guard | memory | ✅ موجود (12/12 + 49/49) |

## ۶) نتیجه‌گیری

درگاه مالک پایهٔ امنِ درستی دارد (HMAC + kill switch + redaction + retry کران‌دار).
شکاف‌های ساختاری: صف rate-limit کامل، webhook با secret_token (با گارد dual-ingestion)،
اتصال read-only حلقهٔ رویداد به memory/ledger، و سطح دسترسی لاگ‌ها در Mini App.
هر شکاف با NEED در Needs Ledger و loop در Loop Registry ثبت می‌شود؛ هیچ‌کدام
closure تلقی نمی‌شوند مگر با verifier مستقل و مشاهدهٔ مالک (OWNER_VISIBLE).

## Evidence

- `telegram_center/miniapp_gateway.py` (بایند 8774، HMAC §۲، STOP-MINIAPP)
- `telegram_center/tg_api.py:38-39,173-181` (429 کران‌دار)
- `conversation_hub/{router,service,schemas,shadow_rollout}.py`
- `state/telegram/miniapp-hits.jsonl` (شواهد authed)
- `state/waves/WAVE1-PREFLIGHT-2026-08-21.json` (memory read-only اثبات)
