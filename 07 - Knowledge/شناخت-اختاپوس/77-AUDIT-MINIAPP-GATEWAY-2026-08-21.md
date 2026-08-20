---
type: architecture-audit
status: conditional-pass
audit_verdict: CONDITIONAL_PASS
documentation_quality: PASS
external_code_verification: INCONCLUSIVE (local-only repository)
date: 2026-08-21
session_id: SESSION-20260820-21
scope: miniapp_gateway.py — code-level audit and requirements
baseline_head: 4faad7d
document_commit: 7ebbc2251af86d57ee137d11b184298f6580c42b
verified_head: pending-this-commit
hmac_design: PASS_WITH_AUTH_DATE_FIX
replay_protection: PARTIAL
webhook_migration: DESIGN_ONLY
rate_limit_retry: NEEDS_RETRY_AFTER_FIX
rate_limit_queue: REQUIRED
log_governance: NEEDS_GIT_POLICY_FIX
owner_visible_closure: DESIGN_ACCEPTED
wave1_unlock: false
paid_calls: 0
memory_production_writes: 0
---

# AUDIT — معماری درگاه AGI اختاپوس (miniapp_gateway.py)

> **حکم ممیزی: CONDITIONAL_PASS.** کد محلی `F:/backup` بررسی شد، اما این مخزن در GitHub عمومی
> قابل‌شناسایی نیست؛ بنابراین external verification = INCONCLUSIVE. SHA کامل سند اول:
> `7ebbc2251af86d57ee137d11b184298f6580c42b`. `baseline_head=4faad7d` مربوط به قبل
> از commit سند است؛ `document_commit=7ebbc22…` خود اسناد را ساخته؛ `verified_head` باید
> پس از commit این تصحیح به SHA کامل به‌روزرسانی شود.

## ۰) ماتریس حقیقت (کد محلی در برابر سند)

| مؤلفه | وضعیت | شواهد / ناسازگاری |
|---|---|---|
| HMAC-SHA-256 initData | PASS_WITH_AUTH_DATE_FIX | HMAC درست؛ freshness فعلی 3600s و skew -60s (نیاز: 300/-30 برای mutation) |
| Replay داخل TTL | PARTIAL | فقط freshness؛ nonce یک‌بارمصرف Decision Ledger وجود ندارد |
| درگاه تک‌مقصد / kill switch / redaction | PASS | `miniapp_gateway.py`، bind 127.0.0.1:8774، STOP-MINIAPP، proxy redaction |
| 429 retry | NEEDS_RETRY_AFTER_FIX | `_retry_after_from_429` به 30s cap می‌کند (خطر retry زودهنگام) |
| Rate-limit queue | REQUIRED | token bucket/durable scheduler/DLQ کامل وجود ندارد |
| Webhook | DESIGN_ONLY | مرکز polling؛ هیچ config webhook/secret فعالی نیست |
| Conversation Hub | PARTIAL | typed router موجود؛ اتصال یکپارچه read-only/ledger ناقص |
| Log governance | NEEDS_GIT_POLICY_FIX | inbound/miniapp-hits/tg-send-log اکنون tracked و not-ignored هستند |

## ۱) HMAC و freshness — یافتهٔ سطح کد

`telegram_center/miniapp_gateway.py:210-219` الگوریتم رسمی را درست پیاده می‌کند:

```python
check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
calc = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
hmac.compare_digest(calc, got_hash)
```

ولی `miniapp_gateway.py:52-53`:

```python
AUTH_MAX_AGE_S = float(os.environ.get("OCTOPUS_MINIAPP_AUTH_MAX_AGE_S", "3600"))
```

و `:220-223`:

```python
age = now - auth_date
reject if auth_date <= 0 or age > AUTH_MAX_AGE_S or age < -60.0
```

**تصحیح امنیتی اجباری**:

```python
INITDATA_TTL_S = 300
MAX_FUTURE_SKEW = 30
age_s = now_utc_s - auth_date
if age_s < -MAX_FUTURE_SKEW: reject("AUTH_DATE_IN_FUTURE")
if age_s > INITDATA_TTL_S:   reject("AUTH_DATE_EXPIRED")
```

نکته: شرط فعلی برخلاف سند اولیه «timestamp قدیمی را بی‌حد نمی‌پذیرد»، ولی پنجرهٔ آن ۳۶۰۰s
است نه ۳۰۰s؛ سند اولیه ادعای ۳۰۰s را بدون تطبیق کد نوشته بود.

## ۲) Replay داخل TTL — شکاف واقعی

کامنت خط ۲۲۳ می‌گوید «ضدِ replay»، ولی freshness فقط replay **پس از TTL** را رد می‌کند.
درخواست mutation/approval باید این قرارداد را داشته باشد:

```
proposal_id + card_id + one_time_nonce + expires_at
Decision Ledger: PENDING → CONSUMED (اولین استفاده)
دومین استفاده → 409 REPLAY_REJECTED
```

- read-only: HMAC + freshness + rate limit.
- mutation: HMAC + freshness + nonce یک‌بارمصرف.
- query_id/hash cache فقط کمک ضداسپم است، جای nonce تصمیم نیست.

## ۳) Rate limit — یافتهٔ سطح کد و اصلاح

`tg_api.py:_retry_after_from_429` در کد فعلی:

```python
return min(ra, _429_RETRY_CAP_S)   # cap=30s
```

این یعنی `retry_after=75` → تلاش بعد از 30s (زودهنگام). قرارداد درست:

```
next_attempt_at = now + full_retry_after + jitter
```

- سقف روی `sleep` همگام، نه زمان ممنوعیت؛ اگر بزرگ است، پیام durable بماند و sender scheduler بردارد.
- پایان attempt budget → DLQ، نه drop.
- business result جدا از delivery result.
- نرخ‌ها را فقط سیاست محافظه‌کارانهٔ محلی بنامید:
  - `[LOCAL CONSERVATIVE POLICY]` ~۱/s per chat، ~۲۰/min group، ~۳۰/s bulk.
  - `[LOCAL FAIL-SAFE POLICY]` global sender cooldown تا retry_after.
- ادعای «Telegram guarantee: whole bot blocked» حذف شد (سند رسمی تضمین نمی‌کند).

## ۴) Webhook migration — دستور دقیق و status code ثابت

`getUpdates` و webhook متقابلاً انحصاری‌اند:

1. polling input را pause کن؛ 2. highest durable update_id را ثبت کن؛ 3. `setWebhook` با
`secret_token` (۱–۲۵۶ نویسه، حروف/عدد/_/-)؛ 4. `getWebhookInfo` + secret-header test؛
5. سپس worker polling را stop کن؛ 6. rollback = `deleteWebhook(drop_pending_updates=false)`؛
7. polling از highest_durable+1.

Status code contract:

```
missing/invalid secret → 403 empty body
valid duplicate update → 200 after durable dedupe
valid new update       → 200 only after intent commit
```

## ۵) Log governance — اصلاح سیاست Git

یافتهٔ مستقیم:

| مسیر | tracked | ignored |
|---|---:|---:|
| `_ops/state/telegram/inbound-log.jsonl` | yes | no |
| `_ops/state/telegram/miniapp-hits.jsonl` | yes | no |
| `_ops/state/tg-send-log.jsonl` | yes | no |

پس عبارت قبلی «همهٔ لاگ‌ها در git قابل‌بازبینی» **حذف شد** — این رفتار مطلوب نیست.
طرح صحیح:

- `state/telegram/*.jsonl` در `.gitignore` (پس از migration امن؛ historical artifacts را حذف نکن).
- segment فعال append-only؛ rotation بر اساس size/time؛ segment sealed تغییرناپذیر + hash.
- archive فشرده با retention مشخص؛ evidence manifest فقط:
  `path_ref, sha256, first_event_at, last_event_at, record_count`.
- فقط fixture غیرحساس و verifier report وارد Git؛ secret scan روی diff هر commit.

## ۶) API لاگ Mini App — allowlist ثابت، نه path آزاد

مسیر `/api/logs/<kind>` فقط اگر `<kind>` به دیکشنری ثابت نگاشت شود:

```python
LOG_VIEWS = {
    "inbound": inbound_read_model,
    "delivery": delivery_read_model,
    "receipts": receipt_read_model,
    "dlq": dlq_read_model,
}
```

قیود: `limit<=100` · cursor امضاشده (نه offset دلخواه) · بدون path parameter آزاد · فیلتر
زمان + task scope · redaction بعد از read و قبل serialization · max response bytes · raw فقط
backend evidence store · snapshot کهنه با `freshness_status=STALE`.

## ۷) Kill switch — قرارداد بدون ابهام

```
STOP-MINIAPP exists  → gateway 503
STOP-MINIAPP removed → may serve فقط پس از health gate
OCTOPUS_TG_MINIAPP=0 → process disabled
```

حذف فایل kill switch به‌تنهایی resume کامل نیست؛ resume باید health-gated و owner-authenticated.

## ۸) Conversation Hub — نیازهای کد

```
Gateway (HMAC+nonce)
 → conversation_hub.router (typed, extra=forbid)
   ├ memory: sqlite uri mode=ro
   ├ cortex: propose-only, DEGRADED_LOCAL_ONLY
   └ MCP: allowlist + budget
 → provenance (event/correlation/task/run)
 → Decision Ledger append-only
 → durable outbox → receipt → readback
```

## ۹) شروط EVIDENCE_BACKED_PASS

- `verified_head` SHA کامل ۴۰کاراکتری + diff واقعی commit؛
- auth_date = 300s/-30s (mutation) + تست آینده/انقضا؛
- nonce replay داخل TTL (409) + تست؛
- retry_after کامل در scheduler durable (بدون cap زمان ممنوعیت)؛
- T-05/T-08/T-21/T-22 با receipt غیرتهی؛
- log policy migration + allowlisted Mini App log API؛
- verifier مستقل (نه نویسندهٔ سند) confirmed=true.

تا آن زمان:

```yaml
audit_verdict: CONDITIONAL_PASS
documentation_quality: PASS
external_code_verification: INCONCLUSIVE
hmac_design: PASS_WITH_AUTH_DATE_FIX
replay_protection: PARTIAL
webhook_migration: DESIGN_ONLY
rate_limit_retry: NEEDS_RETRY_AFTER_FIX
rate_limit_queue: REQUIRED
log_governance: NEEDS_GIT_POLICY_FIX
owner_visible_closure: DESIGN_ACCEPTED
wave1_unlock: false
paid_calls: 0
memory_production_writes: 0
```