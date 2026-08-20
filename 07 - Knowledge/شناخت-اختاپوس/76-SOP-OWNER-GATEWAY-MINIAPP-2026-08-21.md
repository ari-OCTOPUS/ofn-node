---
type: sop
status: evidence-backed
date: 2026-08-21
session_id: SESSION-20260820-21
scope: owner-gateway — Telegram Mini App integration
baseline: 9bc506f
current_head: 4faad7d
paid_calls: forbidden
memory_production_writes: forbidden
---

# SOP — OCTOPUS Owner-Gateway (Telegram Mini App)

هدف: تبدیل رابط فعلی تلگرام به یک **فرماندهی fail-closed برای مالک** — یک درگاه واحد
(`miniapp_gateway`) که بات و Mini App هر دو façade روی همان Decision Ledger باشند، نه دو مغز موازی.
اصل حاکم: **بستن حلقه یک رخداد مالک‌محور است** — هر Loop Card بدون `telegram_surface`
و `miniapp_route` حق بسته‌شدن ندارد.

وضعیت هر آیتم: `[EXISTING]` = پیاده‌سازی‌شده با مسیر واقعی · `[REQUIRED]` = شکاف.

---

## ۱) اعتبارسنجی HMAC-SHA-256 InitData

الگوریتم اجباری (ترتیب معکوس‌شدنی نیست):

```
secret_key = HMAC_SHA256(key=b"WebAppData", msg=bot_token)
data_check_string = پارامترهای query به‌جز hash، مرتب‌شدهٔ الفبایی، joined با "\n"
signature = HMAC_SHA256(key=secret_key, msg=data_check_string)
قبول فقط اگر hmac.compare_digest(signature, hash) و auth_date ≤ 300s و user.id == owner_chat_id
```

Checklist:

- [x] `[EXISTING]` درگاه فقط روی `127.0.0.1:8774` بایند است — تونل هرگز مستقیم به 8773 نمی‌خورد (`telegram_center/miniapp_gateway.py`).
- [x] `[EXISTING]` HMAC دو-مرحله‌ای با `hmac.compare_digest` (مقایسهٔ زمان‌ثابت)؛ شکست = 403 با بدنهٔ خالی.
- [x] `[EXISTING]` `auth_date` با تلورانس ≤ ۳۰۰ ثانیه؛ `user.id` باید با `TELEGRAM_OWNER_CHAT_ID` برابر باشد.
- [x] `[EXISTING]` توکن فقط از env (`TG_CENTER_BOT_TOKEN`) — هرگز روی دیسک/لاگ/URL.
- [x] `[EXISTING]` کلید کشتار: فایل `STOP-MINIAPP` زیر `_ops` → 503 در هر درخواست.
- [x] `[EXISTING]` مسیرها بسته: فقط `GET /miniapp` و `GET /api/miniapp`؛ هر چیز دیگر 404، هر متد غیر-GET 405؛ redaction دولایه.
- [x] `[EXISTING]` شواهد زنده: `state/telegram/miniapp-hits.jsonl` با `{"authed": true}` (مسیر `/api/lifecycle`).
- [ ] `[REQUIRED]` تست‌های منفی اجباری: initData دستکاری‌شده رد شود (T-05)؛ auth_date منقضی؛ user غیرمالک؛ hash جعلی؛ replay.
- [ ] `[REQUIRED]` ثبت ردّ (403) بدون جزئیات اطلاعاتی در پاسخ، ولی با ردیف audit داخلی.

## ۲) Conversation Hub — ارکستراسیون موازی (Memory / Cortex / MCP)

ساختار فعلی `[EXISTING]`: `conversation_hub/` با `router.py`، `service.py`، `schemas.py`
(pydantic strict)، `shadow_rollout.py` — درگاه واحدِ تصمیم.

نظم لایه‌ها (هر لایه فقط یک وظیفه):

```
Mini App / Telegram
  → miniapp_gateway (auth HMAC، 8774)
  → conversation_hub.router (مسیریابیِ typed با schemas)
      ├─ memory lane:   MemoryStore خواندن فقط-خواندنی (state/memory/memory.db، uri mode=ro)
      ├─ cortex lane:   مغز/fallback محلی — propose-only، هرگز paid
      ├─ mcp lane:      ابزارهای خارجی فقط با allowlist و budget
      └─ provenance:    هر رویداد با event_id/correlation_id/task_id/run_id
  → decision ledger (immutable append-only)
  → durable outbox → Telegram delivery → receipt → readback
```

Checklist:

- [x] `[EXISTING]` schemas با `extra="forbid"` (ورودی ناشناخته رد می‌شود — fail-closed).
- [x] `[EXISTING]` shadow_rollout برای انتشار تدریجی.
- [ ] `[REQUIRED]` انعزال laneها: شکست memory lane نباید cortex lane را بمیراند (fail-soft per lane، fail-closed per auth).
- [ ] `[REQUIRED]` خواندن حافظه فقط با `mode=ro` (اثبات mutation صفر مثل WAVE1-PREFLIGHT).
- [ ] `[REQUIRED]` هر پاسخ حداقل provenance داشته باشد؛ بدون task_id هیچ effect بیرونی نرود.
- [ ] `[REQUIRED]` MCP فقط با allowlist صریح؛ بدون budget → propose-only.

## ۳) Webhook با X-Telegram-Bot-Api-Secret-Token

وضعیت: `[REQUIRED]` — مرکز امروز polling است (`center.py` poll؛ در config هیچ کلید webhook نیست).
گذار با گارد دوجانبه:

1. تعیین endpoint عمومی (ترجیحاً زیر همین تونل معکوس، نه پورت 8774 که local است).
2. `setWebhook(url=..., secret_token=...)` — secret_token: ۱ تا ۲۵۶ کاراکتر، فقط `A-Z a-z 0-9 _ -`، از env خوانده شود.
3. در handler، هدر `X-Telegram-Bot-Api-Secret-Token` را **case-insensitive** بخوان و با `hmac.compare_digest` مقایسه کن؛ ناهمخوانی = 401 بدون پردازش.
4. **T-21 — گارد ingestion دوگانه**: polling باید هم‌زمان با webhook خاموش باشد (deleteWebhook هنگام بازگشت به polling؛ یک authority ingestion). هم‌زمانی = duplicate effect → stop condition.
5. offset/restart-safe: webhook بدون offset کار می‌کند؛ idempotency روی `update_id` حفظ شود (تست T-08: restart → resend صفر).
6. rollback: بازگشت به polling در ≤ ۶۰ ثانیه (اسکریپت‌شده)، بدون ازدست‌دادن offset.

## ۴) مدیریت Rate Limit (۳۰ msg/sec، 429)

واقعیت موجود `[EXISTING]` در `telegram_center/tg_api.py`:
`_429_MAX_RETRIES = 1` (هرگز retry-storm) · `_429_RETRY_CAP_S = 30` (سقف احترام به retry_after) ·
`_retry_after_from_429` (استخراج `parameters.retry_after`). بودجهٔ اعلان (critical exempt ولی counted) در `center.py:_budgeted_send`.

قاعدهٔ حیاتی (هم‌نظر هر سه مدل): **429 یعنی کل بات بلاک است، نه فقط یک چت** — `retry_after`
برای همهٔ کاربران و همهٔ متدها. پس coalescing و digest **پیش‌شرط** ارسال زنده‌اند، نه بهبود بعدی.

Checklist:

- [x] `[EXISTING]` retry کران‌دار (حداکثر ۱ تلاش، سقف ۳۰s).
- [x] `[EXISTING]` بودجهٔ روزانه/ساعتی event_bridge (MAX_PUSH_PER_DAY=6، MAX_PUSH_PER_HOUR=10).
- [ ] `[REQUIRED]` صف خروجی با token bucket: ~۱ پیام/ثانیه به هر چت، ≤ ۳۰/ثانیه کل؛ 429 → صف (نه drop)؛ backoff با jitter؛ پس از budget → DLQ.
- [ ] `[REQUIRED]` coalescing: ۴۲ درز اسکن = یک digest (شمارندهٔ تجمیعی با count/last_seen، نه ۴۲ فایل/پیام).
- [ ] `[REQUIRED]` دو شمارندهٔ مستقل: `business_attempts` و `delivery_attempts` — شکست ارسال هرگز نتیجهٔ محاسبه‌شده را دور نریزد.
- [ ] `[REQUIRED]` alert تجمیعی هنگام 429 پایدار (بدون اسپم؛ یک خط در beat).

## Fail-closed اجباری

- هر خطای auth → 403/401 خاموش؛ هر خطای مسیریابی → route پیش‌فرض fail-closed؛ هر خطای لایه → log + ادامهٔ لایه‌های مستقل.
- kill switch: `STOP-MINIAPP` (گیت‌وی) و kill-switch ماندگار مرکز.
- هرگز token/chat_id/raw payload در لاگ، artifact یا پاسخ.
- Wave 1 قفل؛ memory write صفر؛ paid call صفر.

## راستی‌آزمایی

1. تست‌های منفی HMAC (T-05)؛ 2. تست restart-no-resend (T-08)؛ 3. تست dual-ingestion (T-21)؛
4. تست 429-queue (بدون retry-storm، بدون drop)؛ 5. تست coalescing (N پیام = ۱ digest)؛
6. هر آیتم EXISTING با مسیر واقعی؛ هر REQUIRED با issue ثبت‌شده در Loop Registry.

## Rollback

- gateway: حذف `STOP-MINIAPP` برعکس؛ برگرداندن flag `OCTOPUS_TG_MINIAPP=0` → serve خاموش.
- webhook: `deleteWebhook` + polling؛ offset از config بازخوانی.
- rate queue: غیرفعال‌کردن صف = مسیر مستقیم قبلی با retry کران‌دار موجود.
