---
type: reference
project: "[[03 - Projects/Lead-نقاشی/PROJECT]]"
status: active
tags: [painting, lead, trust-engine, phase-b, api-boundary, security, design]
created: 2026-07-21
updated: 2026-07-21
---

# 07a — API BOUNDARY DESIGN: `POST /api/v1/lead-candidates`
**فاز B (معماری و قرارداد) · احراز هویتِ مرزِ ingestion + طراحیِ شکست/retry/dead-letter**
**ورودی‌ها:** `00_MASTER_BLUEPRINT.md` §3–§4 · `lead_inbox/LEAD_INBOX_SPEC.md` §0–§3,§8 · `RUNTIME-TRUTH-RECONCILE-2026-07-21.md` · `OPUS_MISSION_PROMPT.md` (invariants + REQUIRED API BOUNDARY)
**وضعیت:** طراحی — هیچ کدی نوشته/تغییری اعمال نشده. اجرا فقط بعد از تأیید مالک، در worktree ایزوله، پشتِ فلگ default-off.

---

## 0. تصمیمِ جای‌گیری: **listenerِ جدا روی loopback (پیشنهاد: 127.0.0.1:8774)** — نه توسعهٔ سرورِ موجود

### 0.1 نقشهٔ سرورهای HTTP موجود (بازرسی‌شده در سورسِ کانونی)

| سرور | فایل | bind/پورت | POST surface | ماهیت |
|---|---|---|---|---|
| dashboard | `_ops/dashboard/server.py:49,954` | 127.0.0.1:8770 (`DASHBOARD_PORT`) | — | نمایشِ read-only |
| organism status | داخل پروسهٔ organism | 127.0.0.1:8771 | — | وضعیت |
| cortex | `_ops/cortex/cortex.py:461-535` | 127.0.0.1:8772 | `POST /ask` → `model_router.ask` (خرجِ LLM) | مغز؛ حلقهٔ چرخه + HTTP |
| live cockpit | `_ops/live/server.py:794-898` | 127.0.0.1:8773 (`LIVE_PORT`) | `POST /api/action` (**restart-organism / start-stop-cortex**), `POST /api/ask` | اهرم‌های مالک |
| panel | `_ops/panel/server.py:30,614` | 127.0.0.1:8790 | فرم محلی | جانبی |

همه stdlib `http.server` + `ThreadingHTTPServer` + `SO_EXCLUSIVEADDRUSE` + `log_message` خاموش — این الگو عیناً بازاستفاده می‌شود.

### 0.2 چرا سرورِ موجود کافی/مجاز نیست

1. **`httpauth.py` احراز هویت نیست؛ فقط ضدِ CSRF مرورگر است.** `origin_ok` (`_ops/httpauth.py:39-54`) درخواستِ **بدونِ Origin/Referer را عمداً مجاز می‌کند** (curl/اسکریپت محلی مالک). یعنی POSTِ n8n (بدون Origin) از هر گاردِ فعلی رد می‌شود. مرز ingestion به **authentication مثبت (HMAC per-source)** نیاز دارد — مدلِ اعتمادِ متفاوت؛ مخلوط‌کردنِ دو مدل در یک handler دقیقاً جایی است که باگِ bypass می‌روید.
2. **جداییِ capability (الزامِ سلبیِ n8n).** `live/server.py::do_action` می‌تواند بدن را restart کند؛ `cortex /ask` بودجهٔ LLM می‌سوزاند. اگر ingestion به همان پروسه بچسبد، اثباتِ «producer به هیچ اهرمی نمی‌رسد» از «ساختاری» به «امیدواری به if/else» تنزل می‌کند. پروسهٔ ingestionِ جدا **صفر import** از gate/approval/outbound دارد و این با تستِ AST قابل اثبات است (الگوی موجود: `outcome_store.py` docstring «صفر import از settle/EffectorGate … تستِ ast»).
3. **blast radius.** باگ/DoS در parsing ورودیِ خارجی نباید کابینِ مالک (8773) یا مغز (8772) را بکشد. cockpit fail-soft است («رصد هرگز داشبورد را نمی‌کشد»)؛ مرزِ ingestion **fail-closed** است (شک = رد). دو دکترینِ متضاد = دو پروسه.
4. **چرخهٔ عمر متفاوت.** cortex حلقهٔ فکری دارد و با `STOP-CORTEX` می‌خوابد؛ listener باید مستقل از خواب/بیداریِ مغز، submissions را بپذیرد یا صادقانه 503 بدهد.

**ruling:** پروسهٔ جدید `_ops/lead_inbox/server.py`، bind **فقط `127.0.0.1`**، پورت `OCTOPUS_LEAD_INBOX_PORT` (پیش‌فرض **8774**؛ 8770–8773/8790/11434 اشغال‌اند)، launcher `RUN-LEAD-INBOX.bat` (الگوی `RUN-CORTEX.bat`)، توقفِ اختصاصی `_ops/STOP-LEAD-INBOX` (الگوی `STOP-CORTEX`) + احترامِ بی‌قیدوشرط به halt سراسری (§6.5). n8n self-hosted روی همین ماشین از loopback می‌رسد؛ **هرگز bind روی 0.0.0.0** — اگر روزی producer بیرونی لازم شد، تونل/ریورس‌پروکسیِ تصمیمِ مالک است، نه تغییرِ bind.

### 0.3 چیدمانِ ماژول (پیشنهادی)

```
_ops/lead_inbox/
  server.py          # HTTP نازک: routing، size-limit، halt-check، فراخوانی boundary+intake
  boundary_auth.py   # allowlist/timestamp/nonce/HMAC — خالص، stdlib، بدون شبکه
  intake.py          # schema validation + consent firewall + persist + events + quarantine
  producer_watch.py  # چکِ غیبتِ producer (48h) — read-only روی receipts/heartbeats
_ops/tests/
  test_lead_boundary_auth.py
  test_lead_boundary_intake.py
  test_lead_boundary_negative_n8n.py   # AST + شمارش endpointها (§7)
```

همهٔ state زیر `state/legs/lead-inbox/` (مسیرِ موجودِ هر دو inbox قبلی — RUNTIME-TRUTH §4.3):

```
state/legs/lead-inbox/
  boundary.db          # SQLite WAL: leads + nonces (الگوی outcome_store.py)
  events.jsonl         # رسیدِ append-only هر submission (opslib.append_jsonl)
  quarantine/          # dead-letter داخلی + سایدکارِ دلیل (الگوی lead_sense._move_with_sidecar)
  heartbeats/<src>.json
  <ts>_<hash>.json     # فایلِ کاندیدِ سازگار با lead_sense.read_inbox (تغذیهٔ قوسِ موجود، §5)
```

---

## 1. قراردادِ endpoint

### 1.1 درخواست

```
POST /api/v1/lead-candidates
Content-Type: application/json; charset=utf-8
Content-Length: <= OCTOPUS_INGEST_MAX_BYTES (default 65536)

X-Octopus-Source:    <source_id>           # عضو allowlist، ^[a-z0-9_]{2,32}$
X-Octopus-Timestamp: <unix_seconds>        # صحیحِ اعشاری‌نشده، رشته
X-Octopus-Nonce:     <nonce>               # ^[A-Za-z0-9_-]{16,64}$ (پیشنهاد: uuid4().hex) — یک‌بارمصرفِ هر attempt
X-Octopus-Signature: <hex_hmac_sha256>     # lowercase hex، 64 کاراکتر
Idempotency-Key:     <source_id>:<external_id>   # پایدار بینِ retryها
```

**پیامِ امضا (عینِ spec §0):** `HMAC-SHA256(secret_source, utf8(timestamp) + "." + utf8(nonce) + "." + raw_body_bytes)` — body همان بایت‌های خام است، نه JSONِ نرمال‌شده (صفر ابهامِ canonicalization). مقایسه فقط `hmac.compare_digest` (الگوی `callback_token.py:74`).

**Body:** دقیقاً یک candidate با قراردادِ canonical v1.1 (`LEAD_INBOX_SPEC.md` §1). **بدونِ batch در v1** — idempotency و quarantine per-item ساده و اثبات‌پذیر می‌ماند.

### 1.2 پاسخ‌ها

| HTTP | body | معنا |
|---|---|---|
| 202 | `{"ok":true,"lead_id":"<uuid>","status":"accepted","receipt_event_id":"<uuid>"}` | پذیرفته شد؛ lead_id را inbox می‌سازد نه producer |
| 202 | `{"ok":true,"status":"heartbeat","receipt_event_id":"..."}` | heartbeat ثبت شد؛ صفر لید ساخته شد (§6.4) |
| 200 | `{"ok":true,"lead_id":"<uuid>","status":"duplicate"}` | Idempotency-Key تکراری → همان لیدِ قبلی؛ re-POST امن |
| 4xx/5xx | `{"ok":false,"error":{"code":"<CODE>","detail":"<ascii، بدون echo بدنه/secret>"},"receipt_event_id":"..."}` | جدول §1.3 |

### 1.3 کدهای خطای ساخت‌یافته (+ رفتار producer و مقصدِ داده)

| HTTP | code | شرط | retry producer؟ | receipt event | quarantine |
|---|---|---|---|---|---|
| 503 | `HALTED` | HALT-ALL / STOP(architect) / STOP-ORGANISM / FREEZE / STOP-LEAD-INBOX | آری (backoff) | آری | — |
| 401 | `AUTH_MISSING_HEADERS` | هر هدرِ الزامی غایب/بدفرمت | نه (باگِ پیکربندی) | آری (سبک) | نه |
| 403 | `SRC_UNKNOWN` | source خارج از allowlist | نه | آری (سبک) | نه |
| 503 | `SRC_UNCONFIGURED` | source در allowlist ولی secret env غایب → fail-closed (الگوی callback_token: بی‌secret هیچ امضایی معتبر نیست) | آری | آری + alert یک‌باره | نه |
| 401 | `TS_INVALID` | timestamp غیرصحیح | نه | آری (سبک) | نه |
| 401 | `TS_EXPIRED` | \|now−ts\| > 300s (هر دو جهت) | یک‌بار با ts تازه (clock skew) | آری (سبک) | نه |
| 401 | `SIG_INVALID` | عدم تطابق HMAC | نه — آلارمِ سمت producer | آری (سبک: فقط hash) | نه (§6.3) |
| 409 | `NONCE_REPLAY` | nonce قبلاً برای این source مصرف شده | یک‌بار با nonce تازه + همان Idempotency-Key | آری | نه |
| 413 | `BODY_TOO_LARGE` | Content-Length > سقف (قبل از خواندنِ بدنه) | نه | آری (سبک) | نه |
| 400 | `JSON_INVALID` | بدنهٔ احرازشده ولی JSON خراب | نه | آری | **آری** |
| 422 | `SCHEMA_INVALID` | نقضِ قرارداد v1.1 (§2 گام 9) | نه | آری | **آری** |
| 422 | `IDEM_MISMATCH` | هدرِ Idempotency-Key ≠ `source_id:external_id` بدنه | نه | آری | **آری** |
| 422 | `CONSENT_VIOLATION` | ادعای consent خارج از سقفِ per-source (§4) — مثلا market_signal با outreach_allowed=true | نه — red flag | آری + **alert فوری** | **آری** |
| 429 | `RATE_LIMITED` + `Retry-After: 60` | سقفِ نرخ per-source/سراسری | آری بعد از Retry-After | آری (سبک) | نه |
| 500 | `INTERNAL` | استثنای غیرمنتظره (هرگز بی‌صدا: alert) | آری | آری در حدِ ممکن | best-effort |

---

## 2. خطِ لولهٔ احراز — ترتیبِ قطعیِ چک‌ها (همه fail-closed)

```
(0) روش/مسیر: فقط POST /api/v1/lead-candidates (+ GET /health read-only) → وگرنه 404
(1) halt سراسری: opslib.master_halted() یا STOP-ORGANISM یا frozen() یا STOP-LEAD-INBOX → 503 HALTED
    (ارزان‌ترین چک اول؛ هیچ nonce/state قبل از آن مصرف نمی‌شود)
(2) Content-Length حاضر و <= سقف → وگرنه 413 (بدنه هرگز خوانده نمی‌شود؛ ضدِ mem-DoS)
(3) هدرها حاضر/خوش‌فرم (regexهای §1.1) → وگرنه 401 AUTH_MISSING_HEADERS
(4) source ∈ allowlist (OCTOPUS_INGEST_SOURCES) → وگرنه 403 SRC_UNKNOWN
(5) secret این source از env resolve شود → وگرنه 503 SRC_UNCONFIGURED
(6) timestamp صحیح و |now−ts|<=300 → وگرنه 401 TS_INVALID/TS_EXPIRED
(7) خواندنِ بدنه با سقفِ سخت + timeout سوکت (BaseHTTPRequestHandler.timeout=15s؛ ضدِ slowloris)
(8) HMAC با compare_digest (secret فعلی، بعد secret _PREV اگر هست — چرخش §2.2) → وگرنه 401 SIG_INVALID
(9) nonce: INSERT OR IGNORE در nonces(source_id,nonce) → rowcount==0 → 409 NONCE_REPLAY
    (nonce فقط بعد از امضای معتبر مصرف/ثبت می‌شود — مهاجمِ بی‌secret نمی‌تواند جدول را مسموم کند)
(10) rate limit: شمارش nonceهای این source در ۶۰ ثانیهٔ اخیر > سقف → 429 (nonce ثبت شده = شمارندهٔ طبیعی)
(11) JSON parse → خطا → quarantine + 400
(12) Idempotency-Key: فرمت + تطابق با بدنه → خطا → quarantine + 422؛ سپس UNIQUE(idempotency_key)
     در leads → موجود → 200 duplicate (بدونِ ردیف/رویدادِ لیدِ نو؛ receipt «duplicate.detected» ثبت می‌شود)
(13) schema validation قرارداد v1.1 (stdlib، validator دستی — §2.3) → خطا → quarantine + 422
(14) consent firewall مرزی (§4) → تخطی → quarantine + 422 CONSENT_VIOLATION + alert
(15) persist اتمیک (§3) + receipt event lead.candidate.received + فایلِ handoff (§5) → 202
```

هر گام که رد کند، گام‌های بعدی هرگز اجرا نمی‌شوند؛ **هر مسیر — موفق یا رد — دقیقاً یک receipt event می‌نویسد** (spec §0: «append-only receipt event for EVERY submission»).

### 2.1 secretهای per-source — provisioning فقط سمتِ مالک

- نام env: `OCTOPUS_INGEST_SECRET_<SOURCE_ID_UPPERCASE>` (مثلاً `OCTOPUS_INGEST_SECRET_N8N_DA`).
- بارگذاری از `.env` ریشه با `env_loader.load_env()` موجود (`_ops/budget/env_loader.py` — «هرگز log/commit/echo؛ فقط set/skip گزارش می‌شود»). **هیچ secretی در repo/نوت/HANDOFF/لاگ نمی‌آید** (قانون اساسی §۱۰).
- ماژول secret **نمی‌سازد**؛ غیبت = fail-closed (`SRC_UNCONFIGURED`) — عینِ دکترین `callback_token.py` («روشن ولی secret غایب = fail-closed؛ ساختِ مقدار = کارِ مالک»).
- allowlist: `OCTOPUS_INGEST_SOURCES="n8n_da,n8n_domain,n8n_fbgroups,n8n_module1"` (default: خالی = هیچ producerی پذیرفته نمی‌شود).

### 2.2 چرخشِ secret

هر source اختیاری `OCTOPUS_INGEST_SECRET_<SRC>_PREV` دارد؛ verify اول با فعلی، بعد با PREV (هر دو compare_digest). پنجرهٔ چرخش = تا حذفِ دستی `_PREV` توسط مالک. افزودن به `04 - Architect System/architect/01-Project/SECRETS-ROTATION-CHECKLIST.md` (ارجاع، بدون مقدار).

### 2.3 schema validation — stdlib، بدون وابستگی

validator دستیِ `validate_candidate(d) -> list[str]` (الگوی کد موجود: صفر کتابخانهٔ بیرونی). چک‌های الزامی:
- `schema_version == "1.1"`؛ `candidate_type ∈ {consented_inbound, public_b2b, market_signal}`.
- `source.channel` ∈ enum قرارداد؛ `source.source_id == X-Octopus-Source`؛ `source.external_id` ناخالی.
- `consent.basis ∈ {explicit, inferred_business, none, unknown}`؛ `consent.retention_class` ∈ enum.
- `request.scope_text` ناخالی (قرارداد: «required — whatever was actually observed»).
- **attachment isolation:** `request.photos` فقط آرایهٔ رشته‌های مرجع (URL/مسیر)، هر آیتم ≤2048 کاراکتر، ≤10 آیتم، ردِ `^data:` و هر blob باینری/base64. inbox هرگز عکس fetch نمی‌کند — fetch یک effectorِ گیت‌شدهٔ بعدی است («photos by reference, scanned before touch»).
- فیلدهای producer در `qualification`/`workflow` **نادیده گرفته و overwrite می‌شوند** (§4) — producer فقط مشاهده تحویل می‌دهد، نه قضاوت.

---

## 3. storeها — بازاستفادهٔ الگوهای موجود، نه بازاختراع

| قطعه | الگوی کپی‌شده (file:line) |
|---|---|
| SQLite WAL + `_LOCK` + `INSERT OR IGNORE` + UNIQUE idempotency | `_ops/outcomes/outcome_store.py:65-107` |
| append-only JSONL | `opslib.append_jsonl` (`_ops/budget/opslib.py:277`) |
| quarantine = move + سایدکارِ دلیل، تصادمِ نام → suffix، **هرگز حذف** | `_ops/legs/lead_sense.py:104-119` (`rejected/` + `.result.json`) |
| نوشتنِ اتمیک tmp+os.replace | `_ops/legs/lead_leg_inbox.py:66-80` |
| HMAC/compare_digest/fail-closed-بی‌secret | `_ops/telegram_center/callback_token.py` |
| alert مشهود | `opslib.alert` → `governor-alerts.md` (`opslib.py:341-344`؛ همان که cockpit «alerts_today» می‌شمارد) |
| سرور انحصاری loopback | `_Srv(SO_EXCLUSIVEADDRUSE)` در `live/server.py:794-800` |

### 3.1 `boundary.db`

```sql
CREATE TABLE IF NOT EXISTS leads(
  lead_id          TEXT PRIMARY KEY,          -- uuid4، inbox-assigned
  idempotency_key  TEXT UNIQUE NOT NULL,      -- "<source_id>:<external_id>"
  candidate_type   TEXT NOT NULL,
  source_id        TEXT NOT NULL,
  channel          TEXT NOT NULL,
  external_id      TEXT NOT NULL,
  consent_basis    TEXT NOT NULL,
  outreach_allowed INTEGER NOT NULL DEFAULT 0,  -- server-forced (§4)
  retention_class  TEXT NOT NULL,
  compliance_reason TEXT,
  suburb TEXT, service TEXT, urgency TEXT,
  status           TEXT NOT NULL DEFAULT 'received',
  received_at      TEXT NOT NULL,             -- ISO-8601 UTC-aware
  recorded_at      TEXT NOT NULL,
  schema_version   TEXT NOT NULL,
  payload_json     TEXT NOT NULL              -- کاندیدِ canonical کامل بعد از نرمال‌سازی مرزی
);
CREATE TABLE IF NOT EXISTS nonces(
  source_id TEXT NOT NULL, nonce TEXT NOT NULL, ts INTEGER NOT NULL,
  PRIMARY KEY(source_id, nonce)
);
CREATE INDEX IF NOT EXISTS idx_nonces_src_ts ON nonces(source_id, ts);
```

GC نانس‌ها: حذفِ ردیف‌های `ts < now-3600` در هر N-امین درخواست (نگه‌داشتِ ≥12× پنجرهٔ replay؛ nonce تنها دادهٔ حذف‌شونده است — رسیدِ append-onlyاش در events.jsonl می‌ماند، پس «هرگز حذف نکن» نقض نمی‌شود).

### 3.2 `events.jsonl` — envelope عینِ spec §3

```json
{"event_id":"uuid","event_type":"lead.candidate.received","occurred_at":"ISO-8601",
 "correlation_id":"<lead_id|->","causation_id":null,"source_component":"lead_boundary",
 "schema_version":"1.0",
 "payload":{"source_id":"n8n_da","outcome":"accepted|rejected|duplicate|heartbeat",
            "error_code":null,"http_status":202,"body_sha256":"...","body_bytes":1834,
            "idempotency_key":"n8n_da:DA-2026-1234","quarantine_ref":null,"sig_valid":true}}
```

انواع رویداد مصرفی این مرز: `lead.candidate.received`، `lead.candidate.rejected`، `lead.duplicate.detected`. رسیدِ ردهای **احرازنشده** «سبک» است: هرگز بدنهٔ خام/PII/secret — فقط hash+اندازه+کد (ضدِ log-poisoning و ضدِ نشتِ PII؛ سیاستِ redaction موجود).

### 3.3 quarantine (dead-letter داخلی)

`quarantine/<utc_ts>_<error_code>_<body_sha256_12>.json` (بدنهٔ خام bytes) + سایدکار `.reason.json` `{error_code, detail, source_id, received_at, receipt_event_id}`. **فقط برای بدنه‌های احرازشده** (گام‌های 11-14) — بدنهٔ بی‌امضا هرگز persist نمی‌شود (§6.3). هرگز حذف؛ خروج فقط انتقال به `_Archive` با تصمیم مالک.

---

## 4. consent firewall در مرز — ساختاری، نه توصیه‌ای

علاوه بر schema، دو لایهٔ سختِ سمتِ سرور:

1. **سقفِ per-source (default-deny):** هر source فقط جفت‌های مجازِ (channel, candidate_type) را می‌تواند submit کند — config env:
   `OCTOPUS_INGEST_TYPES_N8N_DA="market_signal"` · `OCTOPUS_INGEST_CHANNELS_N8N_DA="nsw_da"` (به‌همین‌ترتیب n8n_domain→domain_listing، n8n_fbgroups→facebook_group؛ فقط `n8n_module1` مجاز به `market_signal,public_b2b`). غیبتِ config = فقط `market_signal`. **نتیجهٔ ساختاری: هیچ producerِ n8n نمی‌تواند `consented_inbound` بسازد** — مسیرِ A (`/lead` تلگرام) داخلی/in-process است و اصلاً از HTTP نمی‌آید.
2. **overwrite مرزی (بی‌اعتنا به ادعای producer):**
   - `market_signal` → `consent.basis` حداکثر `none`، `outreach_allowed=false` (اگر producer ادعای true کرده بود → quarantine + `CONSENT_VIOLATION` + alert؛ ادعا خودش سیگنالِ compromise/باگ است).
   - `basis ∈ {none, unknown}` یا بلوکِ consent غایب → `outreach_allowed=false` (fail-closed عینِ spec §2).
   - `qualification.*` producer → صفر می‌شود (قضاوت کارِ LeadQualificationLeg است).
   - `workflow` → همیشه `{status:"received", owner_action_required:true, external_send_allowed:false, next_action:"qualify"}` — **`external_send_allowed` فقط از مسیر verdict مالک → LANGAR → EffectorGate عوض می‌شود، هرگز از مرز.**
   - `source.channel=="synthetic_test"` فقط از sourceهای صریحاً مجاز (تست/مالک، نه n8n)؛ برچسب در `payload_json` حفظ می‌شود تا بلاکِ سختِ EffectorGate-به-type پایین‌دست enforce شود (invariant بلوپرینت §4 Path A).

---

## 5. handoff به قوسِ موجود (~۸۰٪ سرهم) — تغذیه، نه بازاختراع

RUNTIME-TRUTH §1/#3 دو inbox ناسازگار را ثبت کرده. ruling این طراحی:

- **canonical جدید = `boundary.db`** (قرارداد v1.1 کامل).
- **پل به قوسِ موجود — گیت‌شده بر `candidate_type` (تصحیحِ راستی‌آزماییِ 2026-07-21):** فقط برای لیدهای `consented_inbound` و `public_b2b`ی که از firewall رد شده‌اند، مرز یک فایلِ کاندیدِ سازگار با `lead_sense.read_inbox` (`_ops/legs/lead_sense.py:76-93`؛ dict با `description` ناخالی + address/source/url) اتمیک در `state/legs/lead-inbox/` می‌نویسد، با `lead_id` و کلِ پاکتِ v1.1 (شاملِ `candidate_type`/`consent`) داخلِ dict. از آنجا زنجیرهٔ موجودِ گیت‌شده — `lead_scorer.py:236` (via `wiring.py:1840`، پشتِ `WIRE_LEAD_DISCOVERY`) → `lead_quote.py:129`/`lead_leg.py:89` (پشتِ `WIRE_LEAD_DRAFT`) → Proposal Router `live_loop.py:327` → کارت/دکمه‌ها → رأیِ durable → `goal_directed.measure` — مصرف می‌کند.
  - **چرا گیت لازم است:** RUNTIME-TRUTH §0 تأیید می‌کند این قوس ۱۰۰٪ consent-نابیناست (صفر occurrence از `candidate_type`/`outreach_allowed` در `_ops`). پس اگر مرز برای `market_signal` هم فایل بنویسد، سیگنال وارد قوسِ draft می‌شود و یک quote/response draft + کارت می‌سازد — نقضِ صریحِ `LEAD_INBOX_SPEC §2` («market_signal → outbound draft: NEVER») و بلوپرینت §4. `outreach_allowed=false` جلوی *ارسال* را می‌گیرد ولی جلوی *ساختِ draft/کارت* را نه (گیتِ پایین‌دستی که آن را بگیرد امروز وجود ندارد — RUNTIME-TRUTH §4.5). پس بلوک باید در همین نقطهٔ ورود، ساختاری باشد.
  - **`market_signal` کجا می‌رود:** در `boundary.db` می‌ماند و یک سطحِ جداگانهٔ signals/digest (بلوپرینت §5 Path B، گامِ ۴: «۱۴ رینوی تأییدشده در زونت») تغذیه می‌کند — نه کارتِ per-candidate. ارتقا به `public_b2b` فقط با کارتِ هفتگیِ مالک (سقفِ ۱۰/هفته). **تستِ ساختاریِ فاز C:** «market_signal هرگز فایلِ lead-inbox و هرگز quote/response-draft proposal نمی‌سازد» — علاوه بر تستِ موجودِ outbound-path.
  - dedupe متنیِ `lead_sense` (hash content) به‌عنوان defense-in-depth پشتِ idempotency-key می‌ماند.
- **freeze:** `lead_leg_inbox.py` (dead-code، صفر caller، schema `{raw_text}`) منجمد اعلام می‌شود — Phase B مورد ۱۱؛ حذف نه (قانون: انتقال/انجماد، نه حذف).

دیاگرام متنی:

```
n8n (فقط secret ingestion)
   │  POST /api/v1/lead-candidates  (HMAC ts.nonce.body · idem-key · allowlist)
   ▼
lead_inbox/server.py (127.0.0.1:8774، پروسهٔ جدا، صفر import از gate/approval/outbound)
   ├─ رد → events.jsonl (receipt) [+ quarantine اگر احرازشده] [+ alert]
   └─ پذیرش → boundary.db + events.jsonl + فایلِ سازگار با lead_sense
                 ▼
   قوسِ داخلیِ موجود (فلگ‌گیت‌شده): scorer → quote/draft → ProposalRouter → کارتِ تلگرام
                 ▼
   رأیِ مالک (single-use) → verdict_recorder (durable) → LANGAR append → EffectorGate
                 ▼
   (آینده) outbound worker مالِ Octopus — تنها مسیرِ ارسال؛ n8n هیچ‌جای این ستون نیست
```

---

## 6. طراحیِ شکست / retry / dead-letter

### 6.1 قراردادِ retry producer (at-least-once + idempotent-re-POST)

- **دو هویتِ جدا — قلبِ پروتکل:** `nonce` per-attempt (هر تلاش تازه)؛ `Idempotency-Key` per-candidate (بینِ همهٔ تلاش‌ها ثابت). retransmit بعد از timeoutِ مبهم = nonce و timestamp تازه، همان کلید → بدترین حالت `200 duplicate`، **هرگز لیدِ دوم/کارتِ دوم/اثرِ دوم**.
- backoff پیشنهادی n8n: 1m→5m→15m→1h→6h (سقف ۵ تلاش)، فقط برای خطاهای retryable جدول §1.3؛ بعد از آن آیتم در صفِ خطای خودِ workflow می‌ماند (dead-letter سمتِ producer) و توریِ ایمنی، هشدارِ غیبتِ §6.4 است — دادهٔ Path B/C ذاتاً re-pollable است، چیزی گم نمی‌شود.
- 4xxهای پیکربندی (SIG_INVALID/SRC_UNKNOWN/SCHEMA_INVALID/…) **هرگز retry نمی‌شوند** — retryِ کور روی باگ = alert-storm.

### 6.2 dead-letter سمتِ inbox = quarantine (§3.3) + کارتِ هشدار

هر quarantine بلافاصله: (۱) receipt event با `quarantine_ref`؛ (۲) `opslib.alert(["lead-boundary quarantine: <code> from <src> (<ref>)"])` → همان سطحِ مشهودِ موجود (governor-alerts.md → شمارندهٔ cockpit → مسیرِ کارتِ governor وقتی زنده است). **ضدِ طوفان:** dedupe با فایلِ marker `alert-markers/<date>_<src>_<code>` (الگوی `conflict_to_human` marker) — اولین رخداد فوری، تکرارِ همان کلاس در همان روز فقط شمارش؛ جمعِ روزانه در digest. قاعدهٔ kill بلوپرینت (junk>50%/هفته → fix-or-pause) از روی همین رویدادها محاسبه می‌شود. **هیچ ردِ silent drop در هیچ مسیری وجود ندارد.**

### 6.3 استثنای سنجیده: بدنهٔ **احرازنشده** quarantine نمی‌شود

ذخیرهٔ بدنهٔ دلخواهِ بی‌امضا = primitive پرکردنِ دیسک برای هر پروسهٔ محلی. بنابراین ردهای مراحل 0-10 فقط receiptِ سبک (hash/size/code) می‌گیرند؛ بدنهٔ کامل فقط بعد از امضای معتبر persist می‌شود. این تنها انحرافِ آگاهانه از قرائتِ لفظیِ «invalid → quarantine store» است و دلیلش DoS-hardening است — نیازمند تأیید مالک (§10-Q3).

### 6.4 heartbeat و هشدارِ غیبتِ 48h

- producer در هر runِ بی‌نتیجه، **همان endpoint** را با کاندیدِ heartbeat صدا می‌زند (الزامِ «n8n فقط به /lead-candidates POST می‌کند» لفظاً حفظ می‌شود): `candidate_type=market_signal`، `consent.basis=none`، `external_id="hb-<UTC-date>"`، `request.scope_text="producer heartbeat - no candidates this run"`. مرز الگوی `external_id^hb-` را تشخیص می‌دهد → `heartbeats/<src>.json` را refresh می‌کند، receipt می‌نویسد (`payload.outcome="heartbeat"`)، **صفر ردیفِ لید** → `202 {"status":"heartbeat"}`. idempotency روزانه طبیعی است (`src:hb-<date>`). market_signal بودن یعنی حتی با باگ هم هرگز outreach-پذیر نیست.
- **watcher:** `producer_watch.check()` — read-only روی `heartbeats/` + آخرین receiptِ accepted هر source؛ آستانه `OCTOPUS_INGEST_HB_HOURS_<SRC>` (default 48 طبق spec §7). فراخوانی از سه‌جا، عمداً redundant و مستقل از پروسهٔ خودِ listener: (a) هر POST موفق (ارزان)، (b) beat ارگانیسم وقتی زنده شد، (c) surface داشبورد (read-only). تخطی → alert با dedupe روزانه: «producer <src> silent for <N>h».

### 6.5 رفتار با STOP/HALT — ruling: **مرز در halt می‌بندد (fail-closed)**

تصمیم: با وجودِ هرکدام از `HALT-ALL` / `STOP(architect)` / `STOP-ORGANISM` / `FREEZE` / `STOP-LEAD-INBOX` → هر POST (حتی heartbeat) = `503 HALTED`، **صفر جهشِ state** (نه nonce، نه ردیفِ لید، نه فایلِ handoff، نه quarantine). **تصحیحِ راستی‌آزمایی (2026-07-21):** «صفر نوشتن» اولیه با §1.3 (ردیفِ HALTED: receipt=آری)، §2 گام‌آخر («هر مسیر دقیقاً یک receipt») و بندِ آلارمِ همین بخش (که به «receiptهای HALTED» متکی است) و الزامِ spec §0 («append-only receipt event for EVERY submission») در تناقض بود. قاعدهٔ نهاییِ سازگار: **در halt، تنها نوشته = رویدادِ receiptِ append-only در `events.jsonl` (`payload.outcome="halted_refused"`) + alertِ dedupe‌شده؛ هیچ جهشِ دیگری به state رخ نمی‌دهد** (این‌ها همان ردِ حسابرسیِ اجباری‌اند، نه صفِ کار). دلایلِ بستنِ مرز در halt: 
1. **سابقهٔ دکترین:** `EffectorGate.force_closed` (`chrono.py:358-367`) دقیقاً همین سه شرط را بی‌قیدوشرط refuse می‌کند؛ مرز ورودی نباید نرم‌تر از مرز خروجی باشد. STOP مالک یعنی «ارگانیسم دست نگه دارد» — نه «فقط دهانش را ببندد ولی معده‌اش کار کند».
2. **انباشتِ بی‌ناظر:** در halt هیچ حلقه‌ای quarantine/alert/qualify را رصد نمی‌کند؛ پذیرشِ نوشتن = صفِ نامرئیِ در حالِ رشد + سطحِ حملهٔ باز در دقیقاً لحظه‌ای که مالک «ایست» گفته.
3. **بدونِ گم‌شدنِ داده:** producerها retry+ backoff دارند، Path B/C ذاتاً re-poll می‌شوند، و غیبتِ طولانی، هشدارِ 48h را می‌اندازد. 503 صادقانه + retry امن‌تر از پذیرشِ خاموش است.
4. Path A («هرگز نباید بلاک شود») از این endpoint عبور نمی‌کند — در halt کلِ ارگانیسم خوابیده و این قید ناظر به روزهای عادی است.

503 شدنِ حین halt خودش heartbeat-miss تولید نمی‌کند؟ چرا — و درست است: مالک باید بداند producerها پشتِ در جمع شده‌اند؛ alertِ dedupe-شده «boundary halted, N submissions refused since <ts>» (شمارنده در حافظه + receiptهای HALTED) این را گزارش می‌کند.

---

## 7. الزامِ سلبی: n8n فقط secret ingestion دارد — اثباتِ ساختاری

| اهرم | سازوکارِ دسترسی | چرا n8n ساختاراً نمی‌رسد |
|---|---|---|
| تأیید/رأی (approve) | فقط دکمه‌های تلگرام از طریق getUpdates-پولینگِ خودِ Octopus؛ گیتِ owner-user-id (allowlist در approval_channel) + توکنِ HMACِ callback (`OCTOPUS_CB_SECRET`) + single-use اتمیک (`approval_store` pop) | **هیچ endpoint HTTPِ تأییدی در هیچ پروسه‌ای وجود ندارد** (رأی از api.telegram.org کشیده می‌شود، push نمی‌شود)؛ n8n نه `TELEGRAM_BOT_TOKEN` دارد نه `OCTOPUS_CB_SECRET` نه user-id مالک |
| LANGAR append | in-process؛ `human_append_guard` HMAC (mint فقط در approval_channel) | n8n secret گارد را ندارد؛ سطحِ HTTPی اصلاً وجود ندارد |
| EffectorGate release/settle | آبجکتِ in-process روی ChronoDB (`chrono.py:344-414`)؛ settle بدونِ release_refِ همان appendِ انسانی False | صفر سطحِ شبکه؛ پروسهٔ listener حتی importش نمی‌کند |
| outbound (SMS/email) | امروز MISSING (RUNTIME-TRUTH #15)؛ آینده: workerِ Octopus که فقط effectهای settled را مصرف می‌کند | کلیدهای provider (Twilio/SendGrid) هرگز به n8n داده نمی‌شوند؛ در env با namespace جدا |
| budget/flags | `budget_gate` تنها enforcer؛ فلگ‌ها env مالک | secret ingestion هیچ‌کدام را باز نمی‌کند |
| خودِ ingestion | تنها چیزی که secretش را دارد | سقفِ قدرتِ کاملِ یک producerِ compromised: تولیدِ کاندیدِ propose-only با `outreach_allowed=false` سرور-forced، rate-limited، فقط در typeهای مجازِ همان source (§4) |

**enforcement در CI:** `test_lead_boundary_negative_n8n.py` — (۱) AST: importهای `_ops/lead_inbox/*` باید بیرونِ مجموعهٔ ممنوعه باشند `{approval_channel, chrono, langar*, unified_bus, telegram*, model_router, twilio, smtplib}` (الگوی تستِ AST موجودِ outcome_store)؛ (۲) شمارشِ routeها: پروسهٔ listener دقیقاً `{POST /api/v1/lead-candidates, GET /health}` را سرو می‌کند — هیچ `/gate/*`ی وجود ندارد که محافظت بخواهد؛ (۳) گرِپِ کانفیگ: هیچ `OCTOPUS_CB_SECRET`/`TELEGRAM_BOT_TOKEN` در envِ نمونهٔ n8n. این پاسخِ مستقیم به تستِ الزامی #10 مأموریت است.

**دو شکافِ صادقانه (نه overclaim):**
- **R-1:** `live/server.py` `POST /api/action` (restart-organism) با httpauth فعلی از **هر پروسهٔ محلیِ بدونِ Origin** قابل فراخوانی است — از جمله n8nِ هم‌ماشین. این اهرمِ availability است نه approval/outbound، ولی باید بسته شود: یا توکنِ محلیِ مشترک برای `/api/action`، یا اجرای n8n در containerی بدونِ دسترسی به loopback میزبان. (تصمیم مالک؛ خارج از scope این artifact.)
- **R-2:** «n8n has no gate credentials» فقط تا وقتی صادق است که تفکیکِ env رعایت شود؛ چک‌لیستِ deploy n8n باید صریحاً فقط `OCTOPUS_INGEST_SECRET_<SRC>` را تزریق کند و CI گرِپِ R-2 را داشته باشد.

---

## 8. فلگ‌ها و پیکربندی (همه default-off / fail-closed)

| env | default | نقش |
|---|---|---|
| `OCTOPUS_WIRE_LEAD_BOUNDARY` | `0` | روشن‌شدنِ listener؛ خاموش = پروسه بالا نمی‌آید (صفر اثر) |
| `OCTOPUS_LEAD_INBOX_PORT` | `8774` | پورت loopback |
| `OCTOPUS_INGEST_SOURCES` | خالی (=هیچ‌کس) | allowlist |
| `OCTOPUS_INGEST_SECRET_<SRC>` / `_PREV` | غایب (=fail-closed) | secret per-source، فقط .env مالک |
| `OCTOPUS_INGEST_TYPES_<SRC>` / `OCTOPUS_INGEST_CHANNELS_<SRC>` | `market_signal` / خالی | سقفِ ساختاری consent (§4) |
| `OCTOPUS_INGEST_MAX_BYTES` | `65536` | سقف بدنه |
| `OCTOPUS_INGEST_RATE_PER_MIN` | `60` (سراسری `300`) | rate limit |
| `OCTOPUS_INGEST_HB_HOURS_<SRC>` | `48` | آستانهٔ غیبت |

---

## 9. نگاشت به تست‌های الزامی مأموریت

| تست مأموریت | پوشش در این طراحی |
|---|---|
| 1 امضای معتبر پذیرفته | §2 گام 8-15؛ 202 |
| 2 امضای نامعتبر رد | `SIG_INVALID`، receipt سبک |
| 3 timestamp منقضی رد | `TS_EXPIRED` (±300s دوطرفه) |
| 4 nonce تکراری رد | `NONCE_REPLAY` (INSERT OR IGNORE) |
| 5 idempotency-key تکراری = بدونِ لیدِ دوم | `200 duplicate` + UNIQUE |
| 6 consent غایب → outreach_allowed=false | §4 overwrite مرزی |
| 7 market_signal به outbound نمی‌رسد | §4 + سقف per-source + گیت پایین‌دست |
| 10 n8n بدون credential/endpoint گیت | §7 (AST + شمارش route + گرِپ env) |
| 13 شکستِ producer → alert + حالتِ retry-safe | §6.1/6.2/6.4 |
| 16 صفر secret/PII در لاگ | receiptهای سبک، redaction، `log_message` خاموش، env_loader بدونِ echo |

(تست‌های 8, 9, 11, 12, 14, 15, 17 مالِ artifactهای همسایهٔ فاز B/C هستند؛ 9 این‌جا نیمه‌پوشش دارد: §6.5.)

---

## 10. تصمیم‌های بازِ مالک

1. **Q1 — پورت 8774 و نامِ فلگ‌ها** را تأیید می‌کنی؟
2. **Q2 — R-1:** بستنِ `/api/action` کابین برای پروسه‌های محلیِ غیرمرورگری (توکن محلی یا ایزولاسیون n8n) — الان یا قبل از فعال‌سازی Path B؟
3. **Q3 — §6.3:** پذیرشِ استثنای «بدنهٔ احرازنشده quarantine نمی‌شود» (receipt سبک به‌جای ذخیرهٔ بدنه)؟
4. **Q4 — §6.5:** تأییدِ ruling «مرز در halt کاملاً می‌بندد (503)» به‌جای «پذیرش-ولی-پردازش‌نکردن»؟
5. **Q5 —** retention پوشهٔ quarantine (پیشنهاد: انتقال به `_Archive` بعد از ۹۰ روز، دستی/کارت‌گیت‌شده)؟
6. **Q6 —** heartbeat به‌شکل کاندیدِ `hb-` روی همان endpoint (§6.4) یا sub-endpoint جدا (`/api/v1/producer-heartbeat`) با همان HMAC؟ (پیش‌فرضِ طراحی: همان endpoint، برای حفظِ لفظِ «فقط lead-candidates».)

---
*این مرز یک دهانهٔ باریک است: هرچه از آن می‌گذرد propose-only متولد می‌شود، هرچه ردش می‌کند ردِ ثبت‌شده دارد، و هیچ‌چیز آن‌سویش دستِ producer نیست.*
