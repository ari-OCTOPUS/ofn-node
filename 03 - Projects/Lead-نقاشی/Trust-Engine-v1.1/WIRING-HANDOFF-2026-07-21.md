---
type: reference
project: "[[03 - Projects/Lead-نقاشی/PROJECT]]"
status: active
tags: [painting, lead, trust-engine, phase-c, wiring, handoff]
created: 2026-07-21
updated: 2026-07-21
---

# WIRING HANDOFF — لِینِ لیدِ نقاشی: **COMPLETE-UNARMED** (برای ایجنتِ بعدی/مالک)

> **وضعیت (2026-07-21): COMPLETE-CONNECTED-UNARMED.** کلِ قوسِ لید ساخته، متصل، تست‌شده و
> adversarial-verify شده است — و **مسلح نیست** (هیچ ارسالِ واقعی ممکن نیست؛ transport = NOT_ARMED).
> راهنمای مالک: [[03 - Projects/Lead-نقاشی/Trust-Engine-v1.1/OWNER-RUNBOOK-LEAD|OWNER-RUNBOOK-LEAD]].
> دموِ زنده: [[03 - Projects/Lead-نقاشی/Trust-Engine-v1.1/DEMO-RUN-2026-07-21|DEMO-RUN]] (۹/۹).
> **Owner replay:** `powershell -File _ops/discovery/2026-07-21_LEAD-SAFETY-C1-DEMO/replay.ps1` →
> انتظار **۹/۹ PASS**، فلگ‌های زنده خاموش، صفر ارسال.
>
> **تنها نقطهٔ arm (عمداً باز):** وصلِ دکمهٔ رأیِ کارتِ زندهٔ تلگرام به `lead_effect_gate.on_lead_verdict`
> + مسلح‌کردنِ یک transportِ واقعی. هر دو رأیِ صریحِ مالک‌اند. `on_lead_verdict` ساخته/تست/verify شده.
>
> **رویدادهای gate-scopedِ نو (خارج از قراردادِ ratified، صادقانه):** `effect.settled` (گیت پاک کرد،
> نه ارسال) · `effect.refused` (گیت رد کرد). `communication.*` فقط از transportِ واقعیِ ارسال‌کننده
> می‌آید — که چون NOT_ARMED است، هرگز. (اگر قرارداد نهایی شد، این دو به EVENT_CONTRACT اضافه شوند.)

---

# WIRING HANDOFF — بخشِ نقاشی/لید مرتب و متصل شد (سابقه)

> **مخاطب:** ایجنتِ بعدی که کارِ لولهٔ لیدِ نقاشی را ادامه می‌دهد. این سند stand-alone است —
> بدونِ چتِ قبلی هم قابل‌عمل. **همه‌چیزِ این جلسه flag-off، propose-only، صفر ارسال، STOP دست‌نخورده.**
> master بعد از این کار: کامیت `e3ffb7e` روی برنچِ `claude/deploy-script-patch-verify-982ea5`
> (نوادهٔ خطیِ master؛ ff-safe). قوانینِ سختِ owner (R1–R5) رعایت شد: فایلِ STOP، ارسالِ واقعیِ
> غیر-synthetic، پول/LIVE سراسری، تضعیفِ consent-firewall، و green-دروغین همچنان ممنوع‌اند.

## ۱. وضعیتِ فعلیِ بخشِ نقاشی (یک صفحه)

**لولهٔ لید دو نسل کد است که یک دایرکتوری (`state/legs/lead-inbox/`) را share می‌کنند:**

- **نسلِ قدیم (flag-off):** `lead_sense → lead_scorer → lead_leg → lead_quote → lead_outcome_recorder`، تغذیه با `harvest_austender`/`email_inbound`. کاملاً سیم‌شده در beat loop ولی همهٔ beatهای ارزش‌ساز (lead_discovery/harvest/email/outcome/draft) **خارج از PAPER_FULL و خاموش‌اند** → پا فقط HLC می‌زند، صفر لید.
- **نسلِ نو (Trust-Engine فاز C، این جلسه‌ها ساخته + حالا سیم‌شده flag-off):** `consent_firewall → lead_candidate_inbox → lead_boundary_http` + `effector_gate_bridge`. **قبلاً orphan بود (صفر caller)؛ حالا reachable-اما-flag-off است.**

## ۲. چه چیزی این جلسه سیم شد (کامیت `e3ffb7e`)

| کار | فایل | فلگ/رفتار |
|---|---|---|
| **گاردِ همگراییِ دو inbox** — `read_inbox` فایل‌های `LD-*`/`_*` را skip می‌کند نه reject-move | `legs/lead_sense.py` | بی‌فلگ (ایمنیِ ساختاری) — cross-contamination بسته |
| **فیکسِ کرشِ نهفته** — `EffectorGate(db=None)` → ChronoDBِ واقعی | `wiring.py:187` | بی‌فلگ — settleِ تلگرام دیگر AttributeError نمی‌دهد |
| **launcherِ reachable مرزِ HTTP** — `maybe_start_lead_boundary()` + صدا در organism boot | `wiring.py` + `organism.py` | `OCTOPUS_WIRE_LEAD_BOUNDARY` (خاموش → no-op، loopback-only) |
| **همگراییِ producer** — owner_menu مسیرِ لید را از `submit_candidate` می‌برد | `telegram_center/owner_menu.py` | `OCTOPUS_WIRE_LEAD_CANDIDATES` (خاموش → fallback به قدیمی) |
| **freezeِ inboxِ قدیمی** — هدرِ FROZEN + منسوخ‌سازیِ فلگ | `legs/lead_leg_inbox.py` | فایل می‌ماند (قانونِ اساسی)؛ `OCTOPUS_WIRE_LEAD_INBOX` منسوخ |
| تست | `tests/test_lead_wiring.py` | ۷/۷ + صفر رگرسیونِ سوئیت |

**قوسِ کاملِ زنده‌ای که حالا وجود دارد (وقتی فلگ‌ها روشن شوند):**
`n8n → POST /api/v1/lead-candidates` (مرزِ HMAC) **یا** تلگرام `/lead` → `submit_candidate` → consent-firewall → dedup → فایلِ description-دار در lead-inbox → `lead_discovery_beat` (`lead_sense`) → `lead_scorer` → `lead_leg.intake` → `lead_quote` (draft) → Proposal Router → کارتِ تلگرام → رأیِ مالک → OutcomeStore. **این قوس سرتاسر reachable است ولی هر گِرهش پشتِ فلگِ خاموش.**

## ۳. چه چیزی هنوز مانده (کارِ ایجنتِ بعدی)

✅ **LEAD-SAFETY-C1 ساخته شد (2026-07-21، رأی مالک) — کامیت `5723f90`:** footgunِ batch-release بسته شد.
- `chrono._BATCH_RELEASE_KINDS` (allowlist): فقط kindهای پولِ شناخته‌شده (`send/publish/sync/pay`) با یک human-append batch-release می‌شوند؛ هر kindِ دیگر (ارسالِ به مشتری، ناشناخته، هجیِ نو) fail-safe فقط با `chrono.EffectorGate.release_one` (per-effect). تطبیق case/whitespace-insensitive.
- `legs/lead_effect_gate.py`: `authorize` (allowlistِ per-effect، پیش‌فرض خالی) + `may_release` (fail-closed: STOP/halt، consent-recheck که market_signal/synthetic هرگز، authorization صریح، idempotent) + `release_and_settle` (release_one + settle_fresh، هرگز batch، هرگز send).
- `legs/outbound_worker.py`: هر transport = **stubِ NOT_ARMED**، صفر importِ شبکه، flag `OCTOPUS_WIRE_LEAD_OUTBOUND` خاموش=بی‌اثر، حتی روشن = NOT_ARMED. راستی‌آزماییِ متخاصم تأیید کرد **نمی‌فرستد**.
- تست `test_lead_effect_gate` 13/13؛ ۲ باگِ متخاصم (denylist→allowlist، synthetic-normalize) قبل از merge فیکس شد.

🟡 **مانده برای مسلح‌سازیِ ارسال (owner-gated، فاز D):**
- **transport واقعی:** الان همه NOT_ARMED؛ مالک باید صریحاً یک adapter مسلح کند (رأیِ جدا).
- **جداسازیِ release از send برای staleness:** در `release_and_settle` فعلاً release و settle **اتمیک**اند (همان `now_ms`)، پس گاردِ stalenessِ `effector_gate_bridge` در این مسیر عملاً بی‌اثر است (چیزی کهنه نیست چون هم‌زمان‌اند) — این یک **ضعفِ صادقانه** است نه حفره. برای اینکه staleness واقعی شود، فاز D باید authorize/release را از send جدا کند (release در t0، send بعداً؛ آن‌وقت settle_fresh کهنه‌ها را رد می‌کند).
- `consent_gate`/`consent_store` (suppression) · `funnel_store` · نیمهٔ first-response draft (design-only، بخش‌های قبل).
- جذبِ producerهای قدیمی (`harvest_austender`/`email_inbound` → `submit_candidate`).

🟡 **۴ ماژولِ غایب (طبق فورنسیکِ Agent-A/C):** `consent_gate`، `consent_store` (suppression table — طراحی‌شده، سیم‌نشده)، `lead_effect_gate` (بالا)، `funnel_store` (قیفِ بازار sent→…→paid — قراردادش در `06_FUNNEL_STATE_MACHINE` هست، store نه).

🟡 **نیمهٔ first-response draft:** فقط quote-draft هست؛ نیمهٔ «پاسخِ اولِ سریع + گزینه‌های بازدید» (P0-3) design-only.

🟡 **جذبِ producerهای قدیمی:** `harvest_austender._write_candidate` و `email_inbound.bridge_leads_to_inbox` هنوز مستقیم فایل می‌نویسند؛ باید به `submit_candidate` سوییچ کنند (طرح در `PHASE-B-CONTRACTS/09a_MIGRATION`، گام M3).

## ۴. توالیِ فعال‌سازی (owner-gated — هیچ‌کدام را ایجنت خودسر روشن نکند)

۱. **رأیِ مالک روی قراردادهای فاز B** (`PHASE-B-CONTRACTS/00_VERIFICATION_AND_FIXES.md`).
۲. **synthetic-first:** `set OCTOPUS_WIRE_LEAD_CANDIDATES=1` → یک لیدِ synthetic کلِ لولهٔ داخلی را طی کند، صفر ارسال (ساختاراً بلاک). تست: `test_lead_candidate_inbox.py` این را اثبات می‌کند.
۳. **ingressِ بیرونی:** `set OCTOPUS_WIRE_LEAD_BOUNDARY=1` + secretهای `OCTOPUS_INGEST_SECRET_<SRC>` (فقط `.env` مالک، هرگز در repo) → مرزِ HMAC روی 127.0.0.1:8774.
۴. **مصرفِ داخلی:** `OCTOPUS_WIRE_LEAD_DISCOVERY` + `OCTOPUS_WIRE_LEAD_DRAFT` (لیدِ نوشته‌شده → scorer → quote → کارت).
۵. **فقط پس از ساختِ per-effect gate:** هیچ مسیرِ ارسالِ واقعی فعال نشود.

## ۵. تله‌ها و ارجاع‌ها

- **گوچای REAL_VAULT:** تست‌های source-grep/import، `REAL_VAULT`=درختِ زنده (`F:\backup`) را می‌خوانند نه worktree. برای تستِ ویرایشِ worktree، از `Path(__file__).parent.parent` self-relative import کن (الگو در `test_lead_wiring.py`).
- **ادغامِ ماژولِ staged → ff abort روی untrackedِ هم‌نام:** اگر فایلی روی درختِ زنده untracked است و نسخهٔ tracked داری، قبل از ff به `E:/deploy-snapshots/.../collisions` منتقلش کن.
- **فورنسیکِ موازی (خواندنی، نه دوباره‌کاری):** `_ops/discovery/2026-07-21_LEAD-PAINT-SCAN/AGENT-A-CARTOGRAPHER/` و `AGENT-C-COMMERCIAL-MVO/` (اسکنِ read-only همین پوشه — تأیید می‌کنند «بیشتر ساخته‌شده از آن‌چه docs می‌گوید»).
- **گزارشِ Agent-06 (۲۵ توصیهٔ معماریِ کلِ ارگانیسم):** scopeش کلِ سیستم است نه فقط نقاشی (CloudEvents/Outbox/W3C-trace/FSM legality-matrix/…). چند موردش با کارِ ما هم‌پوشان: **#13 content-based idempotency key را من در inbox پیاده کردم**؛ #7 FSM legality-matrix و #11 transactional-outbox کاندیدهای خوبِ فاز بعدند. بقیه = تصمیمِ جدا.
- نقشهٔ کاملِ ارگانیسم: کارتوگرافیِ ۱۰-زیرسیستمِ 2026-07-21 (در حافظه؛ رجیستری: بخشِ TRUST ENGINE در `_ops/OCTOPUS-COMPONENT-REGISTRY.md`).

## ۶. اثباتِ صداقت
- تستِ نو: `test_lead_wiring.py` 7/7؛ کلِ سوئیت صفر رگرسیون (فقط ۵ قرمزِ محیطیِ capability-revoked، مستقل از این کار).
- همه flag-off = رفتارِ امروز بایت‌به‌بایت. `maybe_start_lead_boundary` با فلگِ خاموش `None` (هیچ threadی، هیچ portی).
- outboundِ واقعی عمداً ساخته‌نشد (R2). consent-firewall تقویت شد نه تضعیف (این جلسه‌ها ۴ باگِ متخاصم فیکس شد، از جمله R4).
