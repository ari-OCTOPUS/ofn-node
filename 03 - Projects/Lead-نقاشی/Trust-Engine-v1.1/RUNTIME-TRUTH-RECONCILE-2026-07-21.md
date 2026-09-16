---
type: reference
project: "[[03 - Projects/Lead-نقاشی/PROJECT]]"
status: active
tags: [painting, lead, trust-engine, runtime-truth, phase-a, handoff, reconciliation]
created: 2026-07-21
updated: 2026-07-21
---

# RUNTIME-TRUTH — بلوپرینتِ Trust Engine ↔ سورسِ کانونی (فازِ A، از قبل انجام‌شده)

> بستهٔ `OPUS_MISSION_PROMPT` فازِ A را «تطبیقِ read-onlyِ runtime، قبل از هر طراحی» تعریف می‌کند و
> `00_RUNTIME_TRUTH.md` را می‌خواهد. **این سند همان است** — تا ایجنتِ Opus مستقیم به فاز B/C برود.
> درختِ کانونی: `wave1/staging` @ `3b77787`. **precedence #1 (runtime):** ارگانیسمِ زنده `F:\backup`
> روی `backup/before-cleanup-2026-07-19`@`a2183c3` است، **هارد عقب‌تر از staging و halt** (STOP-ORGANISM
> از ۱۹ژوئیه). پس امروز هیچ‌چیز به معنای واقعیِ runtime «LIVE» نیست؛ وضعیت‌ها = reachabilityِ کدِ
> کانونی اگر با profileِ پیش‌فرضِ `paper-full` + توکن بوت شود.

## 0. حقیقتِ ساختاریِ کلیدی
**firewallِ رضایتِ بلوپرینت ۱۰۰٪ در سورس غایب است.** `consented_inbound`/`public_b2b`/`market_signal`/
`outreach_allowed`/`consent_basis`/`retention_class`/`candidate_type` → **صفر occurrence** در کلِ `_ops/*.py`.
ستونِ فقراتِ کلِ بلوپرینت به‌عنوان کد وجود ندارد.

## 1. جدولِ RUNTIME-TRUTH — خطِ لولهٔ REQUIRED ARCHITECTURE

| # | مرحلهٔ بلوپرینت | artifactِ فعلی (file:line) | وضعیت | شکاف |
|---|---|---|---|---|
| 1 | External Adapter (n8n) | فقط طراحی؛ producerهای کد `harvest_austender.py`/`email_inbound.py` | **MISSING** (به‌عنوان adapterِ امضاشده) | producerها مستقیم فایل می‌نویسند، نه از مرزِ امضاشده |
| 2 | Signed `/api/v1/lead-candidates` | — (صفر) | **MISSING** | هیچ HTTP endpoint، صفر HMAC-over-ts.nonce.body، صفر nonce/allowlist |
| 3 | Inbox | (a) `lead_leg_inbox.py:86 register_lead` · (b) `lead_sense.py:76 read_inbox` | (a) **DEAD_CODE** · (b) **BLOCKED_BY_FLAG** | (a) صفر caller · (b) دایرکتوریِ inbox اصلاً وجود ندارد (producer فعال نیست) |
| 4 | Normalisation | `lead_sense.py:48`، `lead_leg_inbox.py:42` | **SHADOW** (کمینه) | فقط lowercase/hash، نه نرمال‌سازی به قراردادِ canonical |
| 5 | Deduplication | `lead_sense.py:72`، `lead_leg_inbox.py:110` (24h) | **BLOCKED_BY_FLAG** | کار می‌کند ولی روی text-hash، نه `Idempotency-Key: source:external_id` |
| 6 | Candidate Classification | — (taxonomیِ رضایت صفر) | **MISSING** | scorer نوعِ **معامله** را دسته می‌کند نه نوعِ **رضایت** |
| 7 | Consent Firewall | — | **MISSING** | هیچ firewall؛ هیچ‌چیز `outreach_allowed=false` را fail-closed enforce نمی‌کند |
| 8 | Qualification | `lead_scorer.py:236` (via `wiring.py:1840`) | **BLOCKED_BY_FLAG** (`WIRE_LEAD_DISCOVERY`) | scorerِ deterministicِ خوب، ولی بدونِ intent/urgency schema + missing-question + licensing risk |
| 9 | Response/Quote Draft | `lead_quote.py:129` + `lead_leg.py:89` | **BLOCKED_BY_FLAG** (`WIRE_LEAD_DRAFT`) | نیمهٔ quote موجود؛ **نیمهٔ first-response + inspection-options نیست** |
| 10 | Proposal Router | `live_loop.py:327`، `organism.py:575` | **SHADOW** | reachable ولی advisory/delivery-only (`live_loop.py:332`)؛ لید فقط اگر `WIRE_LEAD_DRAFT` تولید کند |
| 11 | Telegram Card | `live_loop.py:279` deliver `:383`، buttons `:366` | **SHADOW** + **BLOCKED_BY_FLAG** | کارت اگر channel/token؛ دکمه پشتِ `WIRE_PROPOSAL_BUTTONS` |
| 12 | Human Verdict | `live_loop.py:411`، `verdict_recorder.py:44` | **BLOCKED_BY_FLAG** (`WIRE_VERDICT_OUTCOME`) | measurement-only؛ وگرنه in-memory (restart گم) |
| 13 | LANGAR Append | `legs/langar_bridge.py` | **DISCONNECTED** (از لید) | LANGAR موجود ولی مسیرِ verdictِ لید هرگز به آن append نمی‌کند |
| 14 | EffectorGate | `chrono.py:344`، `wiring.py:187` | **DISCONNECTED** (از لید) | گیت موجود + به settleِ تلگرام wired؛ هیچ مسیرِ لید به آن نمی‌رسد |
| 15 | Outbound Worker | — | **MISSING** | صفر workerِ SMS/email؛ هر legِ doc می‌گوید «انسان دستی می‌فرستد» |
| 16 | Provider Result | — | **MISSING** | صفر ingestionِ callbackِ provider |
| 17 | Outcome Attribution | `budget/attribution.py:23`، `lead_outcome_recorder.py:90`، `verdict_recorder.py` | **BLOCKED_BY_FLAG** + partial | funnelِ بازار (sent→…→won/lost→paid) غایب |
| 18 | Cortex Measurement | `goal_directed.py:229` (reads `proposal_metrics` `:196`) | **SHADOW** (reachable) | قوسِ `record_proposal_outcome → measure` واقعاً **بسته** است |

## 2. شکاف‌ها — چه چیزی باید ساخته شود vs چه چیزی فقط سیم‌کشی

**باید از صفر ساخته شود (صفر کد):**
1. **firewallِ رضایت + taxonomyِ candidate** (`candidate_type`/`consent_basis`/`outreach_allowed` fail-closed) — دیوارِ باربرِ بلوپرینت، کاملاً غایب. **بالاترین ریسک.**
2. **مرزِ امضاشدهٔ `/api/v1/lead-candidates`** (HMAC/ts/nonce/idempotency/allowlist/quarantine). (۳۵ رفرنسِ hmacِ موجود = توکنِ callbackِ تلگرام + append-guardِ LANGAR، نه ingestion.)
3. **workerِ outboundِ Octopus + ingestionِ نتیجهٔ provider** — کلِ نیمهٔ راستِ حلقه (send→delivered→replied). امروز ارسال دستی است.
4. **funnelِ نتیجهٔ بازار** (`sent→replied→inspection→quote_sent→won/lost→paid→gross_profit`). فقط money-attribution (CSV) + owner-verdict-measurement موجود است.

**موجود پشتِ فلگ — نیازمندِ سیم‌کشی نه ساخت:**
5. **scorerِ صلاحیتِ deterministic** (`lead_scorer.py`) — محکم، ولی taxonomyِ غلط + گیت‌شده.
6. **quote-draftِ ساختارمند** (`lead_quote.py`) — واقعاً خوب، پشتِ `WIRE_LEAD_DRAFT`.
7. **قوسِ داخلیِ Proposal Router → کارت → verdictِ durable → Cortex measure** ~۸۰٪ سرهم است و measurement-only/idempotent؛ جداییِ owner-verdict از market-outcome **از قبل در کد رعایت شده**. P0 را بساز که این را **تغذیه** کند، نه بازاختراع.
8. **first-response draft** (نیمهٔ speed-to-leadِ P0-3) — تنها نیمهٔ غایب.

## 3. ادعاهای «CURRENT EVIDENCE»ِ بلوپرینت
1. **Proposal Router در live_loop ~07-17** → **CONFIRMED** (`live_loop.py:327`). نکته: advisory/measurement-only، نه گیتِ اثر.
2. **lead-inbox غایب / صفر لید / وضعیتِ فلگ‌ها** → **CONFIRMED با تصحیح:** `WIRE_LEAD` «unset» نیست — ‏paper-full آن را ۱ می‌کند؛ بقیه (HARVEST/EMAIL/LEAD_DRAFT/INBOX/DISCOVERY) پیش‌فرض ۰. **«backendِ inbox فقط روی برنچ» → STALE/REFUTED:** `lead_leg_inbox.py` در کانونی هست — ولی dead-code (صفر caller).
3. **pulse بعد از STOP** → **CONFIRMED (روی درختِ زنده):** نویسنده = persistence قلبِ **سایه/heartstate** (`state/pulse/heart-*`)، جدا از beat loop (beatها STOP را honor می‌کنند). انتسابِ دقیقِ پروسه بدونِ trace زنده UNKNOWN.
4. **`RUNNER_APPLY=1`** → **REFUTED/STALE:** صفر خواننده = dead flag. فعال‌سازیِ زنده از `OCTOPUS_WIRE_MISSION_RUNNER` استفاده می‌کند.
5. **برنچ = backup/before-cleanup نه master** → **CONFIRMED برای درختِ زنده.** کارِ کانونی روی `wave1/staging`. **هیچ‌کدام master نیست** — مدلِ ذهنیِ «master=حقیقت»ِ بلوپرینت هم کهنه است.

## 4. برای ایجنتِ Opus — قبل از فاز B/C
1. **firewallِ رضایت در هیچ شکلی وجود ندارد** (صفر رفرنس) — greenfield؛ بالاترین ریسکِ ناوردیِ غایب.
2. **هیچ مرزِ HTTP و HMACِ per-source نیست** — HMACِ موجود برای callbackِ تلگرام + LANGAR است، نه ingestion.
3. **دو «inbox»ِ متناقض** هر دو به `state/legs/lead-inbox/` هدف دارند: `lead_leg_inbox.py` (schema `{raw_text}`، dead) و `lead_sense.py` (خواندنِ dictهای discovery). **schema ناسازگار** — یکی را انتخاب/همگرا کن (فاز B مورد ۱۰/۱۱).
4. **قوسِ measurementِ داخلی ~۸۰٪ سرهم و درست است** — بساز که تغذیه‌اش کنی، نه بازاختراع. جداییِ owner-verdict/market-outcome در کد رعایت شده (`verdict_recorder.py:33/64`).
5. **مسیرِ لید هرگز EffectorGate/LANGAR را لمس نمی‌کند** — هر دو موجود ولی فقط به settleِ تلگرام wired. زنجیرهٔ Verdict→LANGAR→EffectorGate→Outbound برای لید کاملاً unbuilt؛ outbound worker اصلاً نیست.
6. **`lead_scorer.py` + `lead_quote.py` دو داراییِ واقعیِ قابل‌استفاده** — deterministic/$0/propose-only. repurpose، نساز.
7. **P0-4 فقط money + CSVِ دستی** — funnelِ بازار و provider-callback نیست؛ `delivered`ِ recorder یعنی «رسیدِ تصمیم در sandbox»، نه «پیام تحویل شد».
8. **runbookِ فعال‌سازیِ روزِ اول هیچ فلگِ لید را روشن نمی‌کند** (فقط measurement flags)؛ `LEAD_OUTCOME` در آن هست ولی inert (تنها caller = `lead_discovery_beat` که خاموش می‌ماند).
9. **runtime halt و روی کدِ کهنه** — کدِ کانونی فقط روی `wave1/staging`؛ درختِ زنده برنچِ دیگر/قدیمی؛ STOP-ORGANISM ‏owner-pinned، لمسش نکن.
10. **`RUNNER_APPLY` dead-flag** — نادیده بگیر؛ اگر runner لازم شد از `OCTOPUS_WIRE_MISSION_RUNNER`.
