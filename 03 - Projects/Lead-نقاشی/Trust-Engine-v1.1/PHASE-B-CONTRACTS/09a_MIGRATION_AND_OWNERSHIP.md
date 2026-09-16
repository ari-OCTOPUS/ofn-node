---
type: reference
project: "[[03 - Projects/Lead-نقاشی/PROJECT]]"
status: idea
tags: [painting, lead, trust-engine, phase-b, migration, ownership, freeze]
created: 2026-07-21
updated: 2026-07-21
---

# 09a — MIGRATION + OWNERSHIP + FREEZE/DELETE (فاز B، مورد ۱۰/۱۱ مأموریتِ Opus)

> **جایگاه:** مکملِ `09_IMPLEMENTATION_SEQUENCE` در بستهٔ Trust-Engine-v1.1. سه بخش: (۱) طرحِ
> همگراییِ دو inboxِ متناقض + جذبِ producerهای موجود به مدلِ مرزِ امضاشده؛ (۲) نقشهٔ مالکیتِ
> جزء‌به‌جزء؛ (۳) فهرستِ freeze/delete (فقط توصیه — تصمیم با مالک؛ قاعدهٔ «هرگز حذف نکن» حاکم است).
> همهٔ ادعاها به file:line در درختِ کانونی `wave1/staging @ 3b77787` پین شده‌اند.
> **این سند طراحی است — صفر تغییرِ کد/فلگ/برنچ تا تأیید مالک (قاعدهٔ خودِ بسته).**

---

## بخش ۱ — MIGRATION: همگراییِ دو inbox + جذبِ producerها

### 1.1 صورت‌مسئله — دو «inbox» با schema ناسازگار روی یک دایرکتوری

هر دو ماژول `state/legs/lead-inbox/` را هدف می‌گیرند ولی زبانِ هم را نمی‌فهمند:

| | `legs/lead_leg_inbox.py` | `legs/lead_sense.py` |
|---|---|---|
| مسیر | `_STATE / "legs" / "lead-inbox"` (`lead_leg_inbox.py:29`) | `opslib.STATE_DIR / "legs" / "lead-inbox"` (`lead_sense.py:31-33`) |
| schema | `{lead_id, created_ts, source, raw_text, status:"new", contact:null, estimate:null, trace_id, _nkey}` (`lead_leg_inbox.py:132-141`) | dict آزاد با **حداقل `description` غیرخالی**؛ اختیاری address/cost_of_development/applicant/url/source/day/expected_aud (`lead_sense.py:4-7, 86-87`) |
| نام فایل | `LD-<uuid12>.json` (`:61, :144`) | هر `*.json` سطحِ اول (`:83`) |
| dedup | اسکنِ خطیِ `LD-*.json` با پنجرهٔ ۲۴h روی هشِ متن (`:110-128`) | ایندکسِ پایدارِ `processed/_seen.json` با هشِ description+address (`:48-52, 96-101`) |
| چرخهٔ عمر | فایل ثابت می‌ماند؛ status درجا mutate می‌شود | **هرگز-حذف**: پردازش‌شده → `processed/` + سایدکار؛ خراب → `rejected/` + دلیل (`:96-119`) |
| فلگ | `OCTOPUS_WIRE_LEAD_INBOX` (پیش‌فرض خاموش، `:35`) | بی‌فلگ؛ مصرف‌کننده‌اش پشتِ `OCTOPUS_WIRE_LEAD_DISCOVERY` (`wiring.py:1815`) |
| callerِ runtime | **صفر** (شواهد در 1.2) | `wiring.lead_discovery_beat` → `lead_sense.read_inbox(limit=max_n)` (`wiring.py:1828-1831`) |

**تداخلِ مخرب (کشفِ این ممیزی، فراتر از RUNTIME-TRUTH):** اگر روزی هر دو فلگ روشن شوند،
`lead_sense.read_inbox` با `box.glob("*.json")` فایل‌های `LD-*.json` را هم برمی‌دارد؛ چون `raw_text`
دارند نه `description`، اعتبارسنجیِ خط `lead_sense.py:86-87` رد می‌کند و خطِ `:90` آن‌ها را به
`rejected/` **منتقل می‌کند** — بعد از آن `lead_leg_inbox.get_lead` برای همان lead_id چیزی پیدا
نمی‌کند (`lead_leg_inbox.py:191-193`). یعنی هم‌زیستیِ دو schema روی یک دایرکتوری نه فقط زائد،
بلکه **یک‌طرفه ویرانگر** است. همگرایی اجباری است، نه سلیقه‌ای.

### 1.2 انتخابِ آداپترِ canonical: خانوادهٔ `lead_sense` (با ارتقای پاکت به قراردادِ v1.1)

**رأی طراحی: storage-lifecycle و dedupِ `lead_sense.py` canonical می‌شود؛ `lead_leg_inbox.py` freeze و جذب.**

دلایل، همه از خواندنِ کد:

1. **مصرف‌کنندهٔ زندهٔ سیم‌کشی‌شده فقط یکی است.** کلِ قوسِ سنجشِ ~۸۰٪ سرهم
   (SENSE→SCORE→intake→quote→record→spine) از `lead_sense.read_inbox` تغذیه می‌شود:
   `wiring.py:1831` (خواندن) → `lead_scorer` (`:1832,1840`) → `lead_leg.intake` (`:1861`؛ خودِ intake در
   `lead_leg.py:64-86` است و `attribution.propose` را صدا می‌زند) → `lead_quote.create_quote` پشتِ
   `WIRE_LEAD_DRAFT` (`:1873-1878`) → صفِ ثبتِ outcome پشتِ `WIRE_LEAD_OUTCOME` (`:1888-1889, 1900-1901`)
   → `mark_processed` (`:1896`). RUNTIME-TRUTH §2.7 همین قوس را «بساز که تغذیه‌اش کنی، نه بازاختراع» می‌خواند.
2. **دو producerِ موجود از قبل schemaی آن را تولید می‌کنند:** `harvest_austender._write_candidate`
   (`harvest_austender.py:156-169`؛ قرارداد در docstringِ `:19-21`) و `email_inbound.bridge_leads_to_inbox`
   (`email_inbound.py:190-228`). تستِ قرارداد هم پین شده: `test_harvest_austender.py:86`
   («description غیرخالی، تنها فیلدِ لازمِ lead_sense»).
3. **الگویش در ارگانیسم تعمیم یافته:** `leg_cultivate.py:2-9` صریحاً «تعمیمِ الگوی lead_sense» برای همهٔ
   پاهاست — یعنی این lifecycle الگوی خانگیِ اثبات‌شده است.
4. **چرخهٔ عمرش با قانونِ اساسی و اسپک هم‌راستاست:** هرگز-حذف + انتقال + سایدکارِ دلیل (`lead_sense.py:104-119`)
   دقیقاً همان «quarantine store + never silent drop»ِ `LEAD_INBOX_SPEC.md §0` است — `rejected/` عملاً
   پیاده‌سازیِ موجودِ quarantine است؛ لازم نیست از نو ساخته شود.
5. **`lead_leg_inbox` چیزی ندارد که جذب‌شدنی نباشد:** `raw_text` ⊂ `description` (نگاشتِ بدیهی)؛
   dedupِ ۲۴h‌اش از `_seen.json` ضعیف‌تر است (O(n) اسکن در هر ثبت، فقط status=="new"، `:110-128`)؛
   atomic-writeاش (`:66-80`) همان الگوی tmp+os.replace است که بقیه هم دارند.

**تدقیقِ ادعای «صفر caller» (اصلاحِ ریز روی RUNTIME-TRUTH §1 ردیف 3a):** یک call-siteِ نهفته وجود دارد —
`telegram_center/owner_menu.py:117-120` به‌صورت lazy و hasattr-گارد `register_lead(intent)` را صدا می‌زند.
ولی این مسیر خودش در runtime **دست‌نیافتنی** است: `handle_new_mission` (`owner_menu.py:86`) هیچ callerِ
runtime ندارد — گزینهٔ «② مأموریت» در پنل فقط متنِ راهنما برمی‌گرداند و هرگز آن را صدا نمی‌زند
(`menu_integration.py:76-80`)؛ تنها فراخوانی، smoke-testِ `__main__` است (`owner_menu.py:138`). پس حکمِ
DEAD_CODE درست می‌ماند، اما freeze باید این سیمِ نهفته را هم تعیین‌تکلیف کند (M1b پایین).

**نکتهٔ مهم:** canonical شدنِ `lead_sense` یعنی canonical شدنِ **مکانیکِ ذخیره/چرخهٔ عمر**؛ **قراردادِ
محتوا** همچنان Lead Candidate v1.1 است (`LEAD_INBOX_SPEC.md §1`) که امروز هیچ‌کدام پیاده نکرده‌اند
(RUNTIME-TRUTH §0: صفر occurrence از candidate_type/outreach_allowed/…). پلِ این دو، «آینهٔ سازگاری» است:

### 1.3 قراردادِ فایلِ همگرا (v1.1-in-lead_sense) — absorb بدونِ شکستنِ هیچ تستی

هر فایلِ جدید در `state/legs/lead-inbox/` این شکل را دارد (نوشته‌شده فقط توسط آداپترِ canonicalِ جدید):

```json
{
  "schema_version": "1.1",
  "lead_id": "<uuid — assigned by inbox>",
  "description": "<MIRROR of candidate.request.scope_text — legacy projection>",
  "address":     "<MIRROR of candidate.property.address — optional>",
  "source":      "<MIRROR of candidate.source.channel>",
  "applicant":   "<MIRROR of candidate.contact.organisation|name — optional>",
  "cost_of_development": null,
  "expected_aud": null,
  "day": "<MIRROR of candidate.source.received_at[:10]>",
  "candidate": { "...": "کلِ پاکتِ Lead Candidate v1.1 عیناً (candidate_type, consent, qualification, workflow)" }
}
```

- کلیدهای سطحِ بالا **آینهٔ writer-enforced** از پاکتِ v1.1‌اند؛ فقط writer آن‌ها را می‌سازد و هر ناسازگاری
  باگِ writer است (یک assert در تست). مصرف‌کننده‌های قدیمی دست‌نخورده کار می‌کنند:
  `lead_sense.read_inbox` (اعتبارسنجیِ description، `:86-87`)، `lead_scorer.score` (کلیدهای description/address/…)،
  `content_hash` (`:48-52`)، و تست‌های `test_lead_discovery_beat.py` / `test_harvest_austender.py` همگی سبز می‌مانند.
- فایروالِ رضایت و اجزای جدید فقط `candidate` را می‌خوانند. مسیرِ scorer ممنوع است چیزی از `candidate.consent`
  را تغییر دهد (تستِ ساختاری در فاز C).
- dedup دولایه: (الف) `_seen.json` موجود (هشِ محتوا) دست‌نخورده؛ (ب) کلیدِ جدید `idempotency_key = source:external_id`
  (اسپک §1) در یک ایندکسِ خواهرِ `_idem.json` با همان الگوی اتمیکِ `_save_seen` (`lead_sense.py:62-69`).

### 1.4 گام‌های migration (ترتیبِ اجرا در فاز C — همه پشتِ فلگِ خاموش، همه propose-only)

| گام | کار | ریسک/گارد |
|---|---|---|
| **M0** | تصویبِ همین سند توسط مالک (انتخابِ canonical + نام‌ها + فلگ‌ها) | — |
| **M1** | **Freeze** `lead_leg_inbox.py`: هدرِ کامنتِ `FROZEN — superseded by lead_candidate_inbox (2026-07-21)`؛ فلگِ `OCTOPUS_WIRE_LEAD_INBOX` منسوخ اعلام و **هرگز روشن نشود** (در ACTIVATION runbook هم نیست — RUNTIME-TRUTH §4.8). فایل و تستش (`tests/run_all.py:127` → `test_lead_leg_inbox.py`) سرِجایشان می‌مانند: تست مستقیم import می‌کند و `_LEAD_INBOX_DIR` را monkeypatch (`test_lead_leg_inbox.py:33-37`)، پس freeze-با-کامنت صفر اثرِ رفتاری دارد و ۱۳/۱۳ سبز می‌ماند. | هیچ تغییرِ رفتاری؛ تست‌ها دست‌نخورده |
| **M1b** | سیمِ نهفتهٔ `owner_menu.py:117-131`: در فاز C به آداپترِ canonical re-point شود با **همان پاکتِ خروجی** `{ok, status, lead_id, reason}` (قراردادِ ثبت‌شده در `owner_menu.py:12-13`) تا contractِ owner_menu نشکند؛ تا آن روز، مسیرِ فعلی دست‌نیافتنی + graceful است (`gate_off → status="queued"`, `:124-125`) و دست نمی‌خورد. | backward-compatible by contract |
| **M2** | ساختِ آداپترِ canonical: `_ops/legs/lead_candidate_inbox.py` (نامِ ASCII، بدونِ تصادم با ماژولِ frozen) با تنها نقطهٔ ورودِ `submit_candidate(candidate: dict, source_id: str) -> {ok, lead_id, status, reason}`: validate → normalize به قراردادِ 1.3 → classify (candidate_type) → **consent firewall** (fail-closed: نبودِ consent ⇒ `outreach_allowed=false`؛ `market_signal` ساختاراً هرگز true نمی‌شود) → dedup دولایه → نوشتنِ اتمیک به `lead-inbox/` → رویدادِ receipt (append-only). نامعتبر → `rejected/` + سایدکارِ دلیل (سازوکارِ موجودِ `lead_sense._move_with_sidecar`). پشتِ `OCTOPUS_WIRE_LEAD_CANDIDATES=0`. | ماژولِ نو، فلگ‌آف، stdlib |
| **M3** | **جذبِ producerها** (نوشتنِ مستقیمِ فایل → فراخوانیِ کتابخانه‌ای): بدنهٔ `harvest_austender._write_candidate` (`:156-169`) و `email_inbound.bridge_leads_to_inbox` (`:190-228`) به `submit_candidate()` سوییچ می‌کنند — امضای توابع و فلگ‌هایشان (`OCTOPUS_WIRE_HARVEST`, `OCTOPUS_WIRE_EMAIL`) دست نمی‌خورد. producerِ in-process به HMAC/HTTP نیاز ندارد؛ «مرزِ امضاشده» برای **اتوماسیونِ بیرونی** است — producerِ داخلی از همان گلوگاهِ validate/classify/firewall رد می‌شود با `source_id` از allowlist. نگاشت: austender → `candidate_type=market_signal`, `consent.basis=none`, `outreach_allowed=false`, `retention_class=signal_30d` (fail-closed؛ اسکیلیشن فقط با کارتِ مالک)؛ email → `consented_inbound` با `evidence=inbound_email_to_business`, `compliance_reason=SpamAct_inbound_request` **فقط وقتی** پارس، درخواستِ مستقیمِ سرویس را نشان دهد؛ در تردید → `basis=unknown` ⇒ `outreach_allowed=false` + کارتِ clarify. | فقط با فلگِ M2 روشن فعال می‌شود؛ مسیرِ قدیمی تا سبز شدنِ probeها به‌عنوان fallbackِ frozen می‌ماند |
| **M4** | مرزِ HTTPِ امضاشده برای بیرونی‌ها: `_ops/legs/lead_boundary_http.py` — `POST /api/v1/lead-candidates` با HMAC-SHA256 روی `${timestamp}.${nonce}.${body}` + انقضای ±300s + nonce-replay + `Idempotency-Key` + allowlistِ `X-Octopus-Source` + سقفِ اندازه + خطاهای ساختارمند (اسپک §0) → همان `submit_candidate()`. پشتِ `OCTOPUS_WIRE_LEAD_BOUNDARY=0`. n8n هیچ credentialِ gate ندارد (تستِ منفیِ الزامی). ۳۵ رفرنسِ HMACِ موجود مالِ callbackِ تلگرام/LANGAR است نه ingestion (RUNTIME-TRUTH §2.2) — کدِ نو، الگوی موجود. | stdlib `http.server`؛ فقط localhost تا رأی مالک |
| **M5** | دادهٔ موجود: چون `OCTOPUS_WIRE_LEAD_INBOX` هرگز در runbook روشن نبوده و ماژول dead است، انتظارِ صفر فایلِ `LD-*.json` داریم؛ گاردِ migration: شمارشِ `LD-*.json` قبل/بعد؛ اگر >۰ بود، تبدیلِ `{raw_text}→{description}` از مسیرِ `submit_candidate` + انتقالِ نسخهٔ اصلی به `lead-inbox/legacy-ld/` (انتقال، نه حذف) — **فقط با رأی مالک**. | drift-proof، برگشت‌پذیر |
| **M6** | راستی‌آزمایی: کلِ suite سبز (۲۳۴/۲۳۵ خطِ پایه) + تست‌های نوی اسپک (امضای نامعتبر/timestamp منقضی/nonce تکراری/idempotency/consent-fail-closed/market_signal-هرگز-outbound) + دو probeِ read-onlyِ موجودِ بسته. | معیارِ خروج |

**اثرِ خالص:** یک دایرکتوری، یک schema (v1.1 + آینهٔ legacy)، یک نقطهٔ ورود (submit_candidate)، دو درگاه
(کتابخانه‌ای برای legهای داخلی؛ HTTPِ امضاشده برای بیرونی)، صفر تستِ شکسته، صفر حذف.

---

## بخش ۲ — OWNERSHIP MAP (جزء‌به‌جزء، موجود vs نو)

| # | جزء | ماژولِ مالک | وضعیت | شاهد |
|---|---|---|---|---|
| 1 | مرزِ امضاشدهٔ ingestion (HTTP) | `legs/lead_boundary_http.py` | **NEW** (M4) | RUNTIME-TRUTH §1.2: صفر endpoint |
| 2 | Inbox (ذخیره + چرخهٔ عمر + quarantine) | `legs/lead_sense.py` (canonical) + `legs/lead_candidate_inbox.py` (writer/validator نو) | **EXISTING** + **NEW** | `lead_sense.py:76-119`؛ `rejected/` = quarantine |
| 3 | Normalisation به قراردادِ v1.1 | `legs/lead_candidate_inbox.py` | **NEW** | RUNTIME-TRUTH §1.4: فقط lowercase/hash موجود |
| 4 | Deduplication / idempotency | `lead_sense._seen.json` (موجود) + `_idem.json` source:external_id (نو) | **EXISTING** + extend | `lead_sense.py:48-73`؛ اسپک §1 |
| 5 | Candidate classification + **Consent Firewall** | `legs/consent_firewall.py` (تابعِ خالص، fail-closed) | **NEW — greenfield، بالاترین ریسک** | RUNTIME-TRUTH §0: صفر occurrence |
| 6 | Qualification (scoring) | `legs/lead_scorer.py` via `wiring.lead_discovery_beat` | **EXISTING** (پشتِ `WIRE_LEAD_DISCOVERY`) | `lead_scorer.py` (تابعِ خالص، `:11-13`)؛ `wiring.py:1804-1915` |
| 7 | Quote draft | `legs/lead_quote.py` (+ `pricing.py`) | **EXISTING** (پشتِ `WIRE_LEAD_DRAFT`) | `wiring.py:1873-1878`؛ `lead_quote.py:1-17` |
| 8 | First-response draft + inspection options | ماژولِ نو در P0-3 | **NEW** (تنها نیمهٔ غایبِ درafting) | RUNTIME-TRUTH §1.9, §2.8 |
| 9 | Proposal Router + کارتِ تلگرام | `live_loop.route_leg_proposals` | **EXISTING** (SHADOW؛ دکمه پشتِ `WIRE_PROPOSAL_BUTTONS`) | `live_loop.py:327-409, :366` |
| 10 | Verdictِ مالک (پایدار، idempotent) | `live_loop.record_proposal_outcome_by_token` → `outcomes/verdict_recorder.py` | **EXISTING** (پشتِ `WIRE_VERDICT_OUTCOME`) | `live_loop.py:429-470`؛ `verdict_recorder.py:44-96` (تفکیکِ measurement/market در `:10-13, :26-33` **از قبل رعایت شده**) |
| 11 | LANGAR append (مسیرِ لید) | `legs/langar_bridge.py` موجود؛ سیمِ لید→LANGAR | **EXISTING ولی DISCONNECTED** → wiring نو | RUNTIME-TRUTH §1.13؛ `langar_bridge.py:16-20` |
| 12 | EffectorGate + بلاکِ سختِ `synthetic_test` | `chrono.EffectorGate` | **EXISTING** + یک چکِ type-level نو (`source.channel=="synthetic_test"` ⇒ همیشه closed) | `chrono.py:339-378` (تک‌گلوگاهِ TINV-7؛ STOP/FREEZE ارشد `:358-367`)؛ تزریق: `wiring.py:187` |
| 13 | Outbound worker (تنها مسیرِ ارسال) | `effectors/outbound_worker.py` | **NEW** (کاملاً غایب) — آخرین milestone، بعد از سنتتیک | RUNTIME-TRUTH §1.15 |
| 14 | Outcome attribution (پول) | `budget/attribution.py` (+ `reconcile`، تنها نویسندهٔ CONFIRMED) | **EXISTING** | `attribution.py:1-27` |
| 15 | Outcome events (سنجش + funnel) | `outcomes/outcome_store.py` + `outcomes/lead_outcome_recorder.py`؛ funnelِ بازار = extendِ EVENT_TYPES | **EXISTING** + extend | `outcome_store.py:27` (پنج type فعلی)؛ `lead_outcome_recorder.py:89-103` |
| 16 | Cortex measurement | `cortex/goal_directed.measure` | **EXISTING** (قوس بسته است) | `goal_directed.py:196, :229` |
| 17 | Budget enforcement | خانوادهٔ `_ops/budget/` (`money_gate.py`, `budgets.yaml`) — **تنها enforcer** (ناوردی) | **EXISTING** — لید چیزی اضافه نمی‌کند | invariant #4 مأموریت |
| 18 | سطحِ تأییدِ پولی/تلگرام (`app:` scheme) | `telegram_center/approval_store.py` + `center.py` | **EXISTING — مسیرِ لید حقِ استفاده ندارد** (تفکیکِ عمدیِ `prop:` از `app:`) | `live_loop.py:308-315` |

**مالکیتِ شناسه‌ها (زنجیرهٔ correlation):** `lead_id` (uuid) را فقط inbox می‌سازد (اسپک §1)؛
`attribution_id` (`LEAD-YYYYMMDD-NNN`) را فقط `attribution.propose` از مسیرِ `lead_leg.intake`
(`lead_leg.py:82`)؛ `proposal_id` را recorder/router؛ `effect_id` را فقط `EffectorGate.request`
(`chrono.py:369-378`). کارتِ فعلی linkage را حفظ می‌کند (`live_loop.py:377`) — قاعده: شناسه «اگر موجود،
حمل می‌شود؛ هرگز اختراع نمی‌شود» (`verdict_recorder.py:54-56`).

---

## بخش ۳ — FREEZE/DELETE (فقط توصیه — رأی با مالک؛ حذف ممنوع، فقط freeze/انتقال)

| # | مورد | شاهد | توصیه |
|---|---|---|---|
| F1 | `legs/lead_leg_inbox.py` | callerِ runtime = صفر (تنها سیمِ نهفته `owner_menu.py:117-120` که خودش dead است — `menu_integration.py:76-80` هرگز `handle_new_mission` را صدا نمی‌زند)؛ schema با مصرف‌کنندهٔ زنده ناسازگار؛ هم‌فعال‌سازی = تخریبِ یک‌طرفه (بخش 1.1) | **FREEZE** با کامنتِ هدر؛ فایل + تستش می‌مانند (۱۳/۱۳ سبز)؛ انتقال به `_Archive` فقط بعد از re-pointِ M1b و رأی مالک |
| F2 | فلگِ `OCTOPUS_WIRE_LEAD_INBOX` | dead-flagِ عملی؛ در ACTIVATION runbook نیست (RUNTIME-TRUTH §4.8) | **DEPRECATE** — مستندسازی «هرگز روشن نشود»؛ تستِ منفی: روشن‌بودنش نباید مسیرِ canonical را تغییر دهد |
| F3 | نوشتنِ مستقیمِ فایل در `harvest_austender._write_candidate` (`:156-169`) و `email_inbound.bridge_leads_to_inbox` (`:190-228`) | دورزدنِ مرزِ واحدِ validate/firewall — «producerها مستقیم فایل می‌نویسند» (RUNTIME-TRUTH §1.1) | **ABSORB** (M3)؛ بدنهٔ قدیمی تا اثباتِ مسیرِ نو، fallbackِ frozen؛ سپس کاندیدِ آرشیو با رأی مالک |
| F4 | ردیفِ GLM-A در `OCTOPUS-COMPONENT-REGISTRY.md:62` («روی برنچ، merge نشده») | STALE — فایل در درختِ کانونی هست (RUNTIME-TRUTH §3.2) | **DOC-FIX** در همان PRِ freeze |
| F5 | `telegram_center/actions.py` | خودِ ارگانیسم یتیم اعلامش کرده: `owner_debug.py:93` («جایگزین: owner_menu → MERGE/DELETE») | echo توصیهٔ موجود: **FREEZE→ARCHIVE** با رأی مالک |
| F6 | فلگِ `RUNNER_APPLY` | صفر خواننده — REFUTED/STALE (RUNTIME-TRUTH §3.4) | **DOC-FREEZE**؛ runner واقعی = `OCTOPUS_WIRE_MISSION_RUNNER` |
| F7 | dedupِ ۲۴hِ داخلیِ `lead_leg_inbox` (`:110-128`) | جذب‌شده در dedupِ دولایهٔ canonical (1.3) | با F1 یک‌جا frozen می‌شود — جداگانه کاری لازم نیست |

**صریحاً KEEP (دست نزنید):** `lead_scorer.py`، `lead_quote.py`، `lead_sense.py`، `lead_leg.py`،
`verdict_recorder.py`، `outcome_store.py`، `lead_outcome_recorder.py`، `budget/attribution.py`،
`live_loop.py` (router/verdict)، `langar_bridge.py`، `chrono.EffectorGate` — این‌ها قوسِ ~۸۰٪ سرهمِ
قابل‌اتکایند؛ P0 آن‌ها را تغذیه می‌کند، بازنویسی نمی‌کند (RUNTIME-TRUTH §2.5-2.8, §4.6).

**قواعدِ حاکم بر هر اقدامِ این بخش:** هرگز حذف — فقط کامنتِ freeze/فلگِ خاموش؛ انتقال به `_Archive`
فقط با رأی صریحِ مالک؛ همهٔ رفتارهای نو پشتِ فلگِ پیش‌فرض-خاموش؛ همه‌چیز propose-only تا تأییدِ مالک؛
STOP-ORGANISM ارشدِ همه است و لمس نمی‌شود.

---

## پیوست — فلگ‌های نو (همه default-off) و سوالاتِ بازِ مالک

| فلگ | می‌گشاید |
|---|---|
| `OCTOPUS_WIRE_LEAD_CANDIDATES` | آداپترِ canonical (`submit_candidate` + firewall + normalize) |
| `OCTOPUS_WIRE_LEAD_BOUNDARY` | listenerِ HTTPِ امضاشده (فقط بعد از سبزیِ سنتتیک) |
| `OCTOPUS_WIRE_LEAD_OUTBOUND` | workerِ outbound (آخرین گام؛ گیتِ کامل Verdict→LANGAR→EffectorGate) |

**سوالاتِ باز برای مالک:**
1. تأییدِ انتخابِ canonical (بخش 1.2) و نامِ ماژولِ نو `lead_candidate_inbox.py`؟
2. تأییدِ F1/F2 (freezeِ lead_leg_inbox + منسوخ‌شدنِ فلگش)؟
3. طبقهٔ AusTender: پیش‌فرضِ fail-closed = `market_signal`؛ اگر مالک تندر را «دعوتِ به پاسخ» بداند، ارتقا به `public_b2b` تصمیمِ آگاهانهٔ اوست.
4. زمانِ رأیِ آرشیو برای F1/F3/F5 (پیشنهاد: بعد از ۲۰ outcomeِ واقعی، نه قبل).
