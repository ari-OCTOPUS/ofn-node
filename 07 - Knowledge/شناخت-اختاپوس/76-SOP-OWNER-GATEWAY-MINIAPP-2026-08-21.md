---
type: sop
status: conditional-pass
audit_verdict: CONDITIONAL_PASS
date: 2026-08-21
session_id: SESSION-20260820-21
scope: owner-gateway — Telegram Mini App integration
baseline_head: 4faad7d
document_commit: 7ebbc2251af86d57ee137d11b184298f6580c42b
verified_head: 2bfdefe8aede5ed18ca3e51e28827ca4b585d525
external_code_verification: local-only (F:/backup, not a public repo)
paid_calls: forbidden
memory_production_writes: forbidden
---

# SOP — OCTOPUS Owner-Gateway (Telegram Mini App)

> **Verdict: CONDITIONAL_PASS.** ساختار و کد پایه درست است، اما تا رفع اصلاحات امنیتی
> §C1–§C4 نباید به دستور اجرایی زنده تبدیل شود. این سند local-only است؛ مخزن عمومی
> نیست، پس تأیید بیرونی کد INCONCLUSIVE است و باید با `verified_head` (SHA کامل) و diff
> واقعی توسط یک verifier مستقل (نه نویسندهٔ سند) امضا شود.

هدف: تبدیل رابط فعلی تلگرام به یک **فرماندهی fail-closed برای مالک** — یک درگاه واحد
(`miniapp_gateway`) که بات و Mini App هر دو façade روی همان Decision Ledger باشند، نه دو مغز موازی.
اصل حاکم: **بستن حلقه یک رخداد مالک‌محور است** — هر Loop Card بدون `telegram_surface`
و `miniapp_route` حق بسته‌شدن ندارد.

وضعیت هر آیتم: `[EXISTING]` = پیاده‌سازی‌شده با مسیر واقعی · `[REQUIRED]` = شکاف · `[FIX]` = کد موجود اما نیازمند اصلاح امنیتی.

---

## اصلاحات بحرانی (پیش‌شرط ارتقا به EVIDENCE_BACKED_PASS)

### C1 — کنترل `auth_date` (دو-طرفه، نه یک‌طرفه)

قرارداد درست (رد آینده + انقضا):

```python
age_s = now_utc_s - auth_date
if age_s < -MAX_FUTURE_SKEW: reject("AUTH_DATE_IN_FUTURE")   # MAX_FUTURE_SKEW = 30
if age_s > INITDATA_TTL_S:   reject("AUTH_DATE_EXPIRED")     # INITDATA_TTL_S = 300
```

`[FIX]` کد فعلی `miniapp_gateway.py:222` شرط دو-طرفه دارد (`age > AUTH_MAX_AGE_S or age < -60.0`)
اما `AUTH_MAX_AGE_S` پیش‌فرض **۳۶۰۰ ثانیه** است (خط ۵۳)، نه ۳۰۰. skew منفی ۶۰s است، نه ۳۰.
اصلاح: `INITDATA_TTL_S=300`, `MAX_FUTURE_SKEW=30` برای مسیر mutation؛ read-only می‌تواند TTL بلندتر داشته باشد اما باید صریح باشد.

### C2 — Replay داخل TTL (nonce تصمیم، نه صرفاً freshness)

`[FIX]` کامنت `miniapp_gateway.py:223` می‌گوید «ضدِ replay» ولی فقط freshness است؛ همان initData تا
پایان TTL دوباره قابل‌استفاده است. تفکیک اجباری:

- درخواست‌های فقط‌خواندنی: HMAC + freshness + rate limit (کافی).
- درخواست‌های mutation/approval: `proposal_id + card_id + one_time_nonce + expires_at`.
- nonce پس از اولین مصرف در Decision Ledger → `CONSUMED`؛ تلاش دوم → `409 REPLAY_REJECTED`.
- `query_id`/hash در cache کوتاه‌عمر مجاز است ولی جای nonce تصمیم را نمی‌گیرد.

### C3 — `retry_after` بدون cap زمان ممنوعیت

`[FIX]` `tg_api.py:_retry_after_from_429` مقدار Telegram را `min(ra, 30)` می‌کند — اگر Telegram
۷۵s بگوید، ارسال زودهنگام = 429 مجدد. اصلاح:

```
next_attempt_at = now + retry_after + jitter    # به retry_after کاملِ Telegram احترام بگذار
```

- سقف فقط روی `sleep`ِ همگام، نه روی زمان ممنوعیت اعلام‌شده.
- اگر retry_after > latency budget → پیام durable بماند، sender بعداً بردارد؛ پایان budget → DLQ (نه drop).
- business result جدا commit شود؛ شکست delivery آن را از بین نبرد.

### C4 — برچسب سیاست نرخ (نه ادعای تضمین Telegram)

- «۳۰ msg/sec برای کل بات» = `[LOCAL CONSERVATIVE POLICY]`، نه `[TELEGRAM GUARANTEE]`.
  سند رسمی: ~۱ پیام/ثانیه به یک چت، ~۲۰/دقیقه در گروه، ~۳۰/ثانیه برای bulk notifications.
- «429 کل بات را بلاک می‌کند» تأییدنشده است → به‌جایش: `[LOCAL FAIL-SAFE POLICY] global sender cooldown تا retry_after`.

---

## ۱) اعتبارسنجی HMAC-SHA-256 InitData

الگوریتم (مطابق قرارداد رسمی Telegram):

```
secret_key = HMAC_SHA256(key=b"WebAppData", msg=bot_token)
data_check_string = پارامترهای query به‌جز hash، مرتب‌شدهٔ الفبایی، joined با "\n"
signature = HMAC_SHA256(key=secret_key, msg=data_check_string)
قبول فقط اگر hmac.compare_digest(signature, hash) و کنترل auth_date طبق C1 و user.id == owner
```

Checklist:

- [x] `[EXISTING]` بایند فقط `127.0.0.1:8774`؛ تونل هرگز مستقیم به 8773 (`miniapp_gateway.py`).
- [x] `[EXISTING]` HMAC دو-مرحله‌ای با `hmac.compare_digest`؛ شکست = 403 بدنهٔ خالی (خط ۲۱۲–۲۱۹).
- [x] `[EXISTING]` توکن فقط از env (`TG_CENTER_BOT_TOKEN`).
- [x] `[EXISTING]` kill switch `STOP-MINIAPP` → 503؛ redaction دولایه؛ مسیرها بسته (404/405).
- [ ] `[FIX-C1]` TTL را برای mutation به ۳۰۰s و skew به ۳۰s برسان (فعلاً 3600/-60).
- [ ] `[FIX-C2]` nonce تصمیم برای mutation/approval + 409 REPLAY_REJECTED.
- [ ] `[REQUIRED]` تست‌های منفی T-05 (بایت دستکاری‌شده، hash جعلی، auth_date منقضی/آینده، user غیرمالک، replay).

## ۲) Conversation Hub — ارکستراسیون موازی (Memory / Cortex / MCP)

ساختار فعلی `[EXISTING]`: `conversation_hub/{router,service,schemas,shadow_rollout}.py` (pydantic strict، `extra="forbid"`).

```
Mini App / Telegram
  → miniapp_gateway (auth HMAC + C1/C2)
  → conversation_hub.router (typed)
      ├─ memory lane:  sqlite3 uri mode=ro (state/memory/memory.db)
      ├─ cortex lane:  fallback محلی، propose-only، DEGRADED_LOCAL_ONLY صریح
      └─ mcp lane:     allowlist + budget؛ بدون budget → propose
  → decision ledger (append-only) → durable outbox → delivery → receipt → readback
```

- [x] `[EXISTING]` schemas با `extra="forbid"` (fail-closed).
- [ ] `[REQUIRED]` انعزال laneها (fail-soft per lane، fail-closed per auth).
- [ ] `[REQUIRED]` memory فقط `mode=ro`؛ هر effect بیرونی فقط با task_id.

## ۳) Webhook با X-Telegram-Bot-Api-Secret-Token

وضعیت: `[REQUIRED / DESIGN_ONLY]` — مرکز امروز polling است (بدون کلید webhook در config).
`getUpdates` و webhook متقابلاً انحصاری‌اند؛ گذار دقیق:

1. ورودی polling را **pause** کن (نه stop).
2. آخرین `update_id` را durable ثبت کن.
3. `setWebhook(url, secret_token)` — secret_token: ۱–۲۵۶ نویسه، فقط `A-Z a-z 0-9 _ -`، از env.
4. `getWebhookInfo` + تست هدر secret را پاس کن.
5. **فقط سپس** worker polling را متوقف کن (T-21: هرگز هم‌زمان = dual-ingestion).
6. rollback: `deleteWebhook(drop_pending_updates=false)`.
7. polling از `highest_durable_update_id + 1` ادامه یابد.

قرارداد ثابت status code (رفع ناسازگاری 401/403):

```
invalid/missing webhook secret → 403 empty body
valid duplicate update         → 200 پس از durable dedupe
valid newly accepted update    → 200 فقط پس از intent commit
```

هدر `X-Telegram-Bot-Api-Secret-Token` را case-insensitive با `hmac.compare_digest` مقایسه کن.

## ۴) مدیریت Rate Limit (`[LOCAL CONSERVATIVE POLICY]`)

- [x] `[EXISTING]` retry کران‌دار (`_429_MAX_RETRIES=1`)؛ استخراج `parameters.retry_after`.
- [ ] `[FIX-C3]` cap زمان ممنوعیت را بردار؛ فقط sleep همگام سقف بگیرد؛ durable + DLQ.
- [ ] `[REQUIRED]` صف token bucket: ~۱/s per chat، ~۳۰/s کل (سیاست محافظه‌کارانهٔ محلی)؛ backoff+jitter.
- [ ] `[REQUIRED]` coalescing: ۴۲ درز = یک digest (count + last_seen).
- [ ] `[REQUIRED]` دو شمارندهٔ مستقل business_attempts / delivery_attempts.

## Fail-closed اجباری

- خطای auth → 403/401 خاموش؛ خطای مسیریابی → route پیش‌فرض fail-closed؛ خطای لایه → log + ادامهٔ لایه‌های مستقل.
- kill switch (رفتار بدون ابهام):

```
STOP-MINIAPP exists  → 503
STOP-MINIAPP removed → may serve again فقط پس از health gate (نه resume خودکار)
OCTOPUS_TG_MINIAPP=0 → process disabled
```

`resume` باید health-gated و owner-authenticated باشد؛ حذف فایل به‌تنهایی resume کامل نمی‌سازد.

## راستی‌آزمایی (شرط EVIDENCE_BACKED_PASS)

`verified_head` با SHA کامل · diff واقعی commit · C1 اصلاح · replay داخل TTL تست (C2) ·
retry_after بدون cap زمانی (C3) · T-05/T-08/T-21/T-22 با receipt غیرتهی · امضای verifier مستقل.

## Rollback

- gateway: `OCTOPUS_TG_MINIAPP=0` → serve خاموش؛ kill switch مستقل.
- webhook: `deleteWebhook(drop_pending_updates=false)` + polling از highest_durable+1.
- rate queue: غیرفعال = مسیر مستقیم قبلی با retry کران‌دار موجود.

> DOC-RECONCILE-2026-08-23: gateway still LIVE on 127.0.0.1:8774 (PID 12220); public OCTOPUS_MINIAPP_URL unset — process-up ≠ Telegram menu URL.
