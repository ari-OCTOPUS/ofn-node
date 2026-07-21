---
type: architecture
status: active
tags: [architecture, wiring, debug, dispatch, flags, legs, heart, telegram, handoff]
created: 2026-07-21
updated: 2026-07-21
---

# MASTER WIRING-DEBUG + HANDOFF — 2026-07-21

> ممیزیِ عمیقِ **کلِ سیم‌کشیِ اختاپوس** روی درختِ کانونی `master = 4eb5543` (= هر دو germline).
> ۵ ممیزِ موازیِ read-only (W1 dispatch · W2 legs · W3 heart+brain · W4 telegram · W5 flags/safety)
> + راستی‌آزماییِ Coordinator. **صفر تغییرِ کد؛ صفر لمسِ درختِ زنده؛ STOP دست‌نخورده.** این سند
> «همه‌چیز» را برای ایجنتِ بعدی می‌گوید. هر ادعا file:line دارد.

## ۰. TL;DR برای ایجنتِ بعدی (اگر فقط این را بخوانی)
1. **۲۸ beat** در `wiring.py`، ~۲۶ از `organism.py` صدا زده می‌شوند؛ کیدنس **chrono-driven** است نه tick ‏۳۰۰ثانیه‌ای. پروفایلِ پیش‌فرض `paper-full` ‏۱۶ فلگ را روشن می‌کند؛ بقیه library-only.
2. **بزرگ‌ترین ریسکِ ایمنی (owner):** سپرِ تاریخ `LIVE_GATE_DATE=2026-07-21` **امروز رسید** → دیگر نمی‌بندد؛ و **۸ فایلِ `ACTIVATION-*.flag` فیزیکی روی دیسکِ درختِ کاری/زنده حاضرند** (`git rm --cached` فقط tracking را برد، فایل ماند). یعنی **هر دو نیمهٔ گیتِ پولی/زنده باز است** — تنها دفاعِ باقی = فلگ‌های env (پیش‌فرض خاموش) + کلید + بودجه. `paid_gate()` هم‌اکنون OPEN. قلبِ زنده **۶/۸ گیت روی دیسک سبز** (فقط ۳ فلگِ env تا سپردنِ pacemaker به قلبِ سایه).
3. **یک green-lie واقعی در suite:** از ۲۳۵ تستِ ثبت‌شده **۲۳۴ واقعاً اجرا می‌شوند؛ `test_mining_wiring.py` صفر assertion دارد** (pytest-style، بدون `__main__`، نه در PYTEST_TESTS → direct-run صفر اجرا) و توابعِ ناموجود را تست می‌کند.
4. **فقط ۳ از ۷ پا** خطِ ارزشِ dispatch‌شده‌اند (Lead/Ziman/Accounting)؛ Mining/Crypto فقط status-probe؛ TradeQuote/WLOS خارج از beat.
5. **تنها اثرِ بیرونیِ شبکه‌ایِ زنده = `ps_writeback`→PocketSmith PUT** — چهارگانه-گیت + fail-closed per-item verdict (D1، تأییدشده). Ziman از publish/send هاردکد-بلاک است.

---

## ۱. ستونِ فقراتِ beat (W1) — `organism.py` → `wiring.py`
- حلقهٔ اصلی `organism.py:325`؛ شمارندهٔ beat از `chrono.status()["beat"]` (`organism.py:349-354`) توسطِ thread پیس‌میکر (`organism.py:310-312`) — **نه** `TICK_SECONDS=300` (`organism.py:58`).
- **PAPER_FULL_FLAGS** (`wiring.py:82-102`، اعمال `organism.py:253`): DOCTOR, NEURAL, UNIFIED, LEAD, ZIMAN, SCHOOL, CONSOLIDATION, EVOLUTION, BOX, LEAD_TICK, IDEAS, SPECTRAL, BCM, SPARSE, FISHER, CARTOGRAPHER. بقیهٔ فلگ‌ها پیش‌فرض خاموش.
- **همیشه-روشن (فقط kill-switch):** `cortex_vitals_beat` (stress/innervation persist، `wiring.py:2240`)، `heartbeat_summary_beat` (`events.emit`، `wiring.py:2266`)، `enrich_state_with_germline` (`wiring.py:133`). این‌ها حتی در profileِ bare می‌نویسند.
- **beatهای دارای اثرِ بیرونی/durable وقتی فلگشان روشن است** (لیستِ ممیزیِ پیش از فعال‌سازی): `needs_nudge_beat`/`discovery_nudge_beat` (send TG، `wiring.py:2228/2460`) · `cockpit_requests_beat` (اجرای verbها، `wiring.py:1127/1265`، فلگ `OCTOPUS_TG_EXEC`) · `harvest_beat` (fetch شبکه→lead-inbox، `wiring.py:1685`) · `acct_beat`→`ps_writeback` (`accountant.py:337`) · `heart_beat`→`work_pump` (مسیرِ پولی، `wiring.py:1616`) · `reconcile_beat` (ledger، `wiring.py:767`) · `email_beat` (IMAP، `wiring.py:1649`).

### دیباگِ dispatch (W1)
- **DEAD-FLAG `OCTOPUS_WIRE_FITNESS`:** `append_outbox` (`wiring.py:791`) فلگ را می‌خواند و کارِ durable می‌کند ولی **صفر callerِ production** (فقط `test_phase3_trackb.py`)؛ در عینِ حال `wire_summary` آن را «wire_fitness» تبلیغ می‌کند (`wiring.py:584`). → یا caller وصل کن یا از summary حذف کن.
- **ORPHAN `SprintRunner`:** `organism.py:284` ساخته می‌شود، هرگز tick نمی‌شود (هیچ `sprint_beat`). ساختِ مرده.
- **chrono = تک‌نقطهٔ خرابیِ بی‌آلارم:** اگر `chrono.status()` throw کند (`organism.py:351-353`→`_cstat=None`) همهٔ beatها `beat=0` می‌گیرند و کلِ گیت‌های کیدنس early-return می‌کنند → spine بی‌صدا inert، حلقه سالم به‌نظر می‌رسد. **آلارم لازم دارد.**
- **کوپلینگِ پنهان:** `OCTOPUS_WIRE_INGEST` بدونِ `OCTOPUS_WIRE_SCHOOL` بی‌اثر است (`ingest_beat` فقط داخلِ `afferent_beat`، `wiring.py:1438`؛ sensory_bus فقط با SCHOOL). مستند/decouple کن.
- **at-most-once در `cockpit_requests_beat`:** cursor قبل از اجرای verbها persist می‌شود (`wiring.py:1235`)؛ کرشِ میان‌اجرا = گم‌شدنِ بی‌صدای دستور. اولین فعال‌سازی کلِ backlog را skip می‌کند (`wiring.py:1209-1214`).
- **epoch state درون-حافظه‌ای:** `_EPOCH_STATE`/`_*_STATE` روی restart ریست می‌شوند → beatهای دارای اثرِ بیرونی (`harvest`/`acct`/`reconcile`) ممکن است یک‌بار در همان پنجره دوباره fire کنند (idempotencyِ harvest/acct تأییدنشده).
- **carve-out پروتکشن:** `doctor_selfknowledge_beat` حتی زیرِ protective-halt یک thread ‏LLM می‌سازد (`organism.py:491-494`) — «یادگیری≠تغییر»، ولی بدان که halt آن را نمی‌بندد.

---

## ۲. هفت پا (W2) — بلوغِ خطِ ارزش
جدول: IN=intake · SC=score · PR=proposal · TG=visibility · OV=owner-verdict · DO=durable-outcome · LF=learning. (FOR=flag-off-reachable · LIB=library-only · OG=owner-gated · SH=shadow/status · MISS=missing)

| پا | IN | SC | PR | TG | OV | DO | LF | dispatch از beat؟ | گیتِ اثرِ بیرونی |
|---|---|---|---|---|---|---|---|---|---|
| **Lead** (مرجع) | FOR | FOR | FOR | FOR | FOR | FOR | FOR | **بله** `leg_beat`(organism:551)+`lead_discovery_beat`(:650) | هیچ send؛ quote/invoice=فایلِ محلی |
| **Ziman** | SH | LIB(biology orphan) | FOR | FOR | FOR | FOR | MISS | **بله** `ziman_beat`(:560) | **هاردکد-بلاک** publish/send (`ziman_leg.py:487`) |
| **Accounting** | FOR | FOR | FOR | FOR | OG(manual `/review`) | FOR(local) | FOR($0) | **بله** `acct_beat`(:624) | **PocketSmith PUT** — quad-gate+fail-closed |
| **Mining** | SH | MISS | MISS | SH | MISS | MISS | MISS | **فقط status** `business_legs_beat`(:604) | ندارد (live=False همیشه) |
| **Crypto** | SH | MISS | MISS | SH | MISS | MISS | MISS | **فقط status** (:604) | ندارد (صفر trade) |
| **TradeQuote** | FOR | — | FOR | MISS | MISS | FOR(local) | MISS | **نه** (nested در `lead_quote.py:200`) | فقط فایلِ آفلاین، صفر شبکه |
| **WLOS** | FOR(RO) | — | — | — | — | — | inward | **نه** (`self_knowledge.py:108`) | RO؛ OCTOPUS هرگز نمی‌نویسد |

### دیباگِ پاها (W2)
- **Lead کاملاً wired ولی کاملاً تاریک:** هر ۷ مرحله وجود دارد و reachability-tested، ولی پشتِ ~۶ فلگِ مستقلِ خاموش که paper-full روشنشان نمی‌کند: برای روشنیِ سرتاسر لازم است `LEAD_DISCOVERY`+`LEAD_DRAFT`+`LEAD_OUTCOME`+`SPINE`+`PROPOSAL_BUTTONS`+`VERDICT_OUTCOME` (+`EMAIL`/`HARVEST` برای intakeِ خودکار).
- **پینچ‌پوینتِ رأیِ مالک برای همهٔ پاهای proposal:** بدونِ `OCTOPUS_WIRE_PROPOSAL_BUTTONS` (`wiring.py:557`) هیچ verdict گرفته نمی‌شود؛ بدونِ `OCTOPUS_WIRE_VERDICT_OUTCOME` (`live_loop.py:455`) هیچ verdict پایدار نمی‌شود.
- **Mining خشک‌ترین پا:** صفر منبعِ داده (`live=False` همیشه، `mining_leg.py:58`)، صفر scorer/proposal — نیازمندِ specِ بیزنسِ مالک.
- **Crypto نیم‌اندام:** دادهٔ تازهٔ واقعی می‌آید ولی صفر scorer/proposal (afferent هست، efferent نیست).
- **Accounting کامل‌ترین حلقهٔ واقعی** ولی OVش دستی (`accountant.py:388`) نه کارتِ خودکار.

---

## ۳. قلب + مغز (W3) — و بزرگ‌ترین یافتهٔ ایمنی
### 🔴 یافتهٔ حیاتی (تأییدِ Coordinator)
- **فایل‌های `ACTIVATION-*.flag` فیزیکی روی دیسک حاضرند** (درختِ کاری wave1-staging + درختِ زنده). `git rm --cached` (D2) tracking را برد ولی کپیِ working-tree را نگه داشت → runtime `.exists()` = True → نیمهٔ «فلگ» هر double-lock **این‌جا** برآورده است. **کلونِ تازه پاک است** (نیتِ D2)، ولی خودِ درخت‌ها اهرم دارند.
- **سپرِ تاریخ رفت:** `LIVE_GATE_DATE=2026-07-21` (`opslib.py:167`) = امروز → `live_gate_open` (`opslib.py:405`) دیگر با تاریخ نمی‌بندد. با فلگ‌های حاضر، **هر دو نیمهٔ هر گیتِ زنده باز است**.
- **`paid_gate()` هم‌اکنون OPEN** (`model_router.py:100-108`) via RESEARCH-EARLY+CORTEX-PAID حاضر → خرجِ واقعیِ cortex فقط به `keys_present()` (`:226`) + بودجهٔ organ_gate گیت‌خورده.
- **override قلبِ زنده ۶/۸ گیت روی دیسک GREEN:** `production_wire_open()` (`shadow.py:84`) — SIM_PASS، equations-locked، Gate-0، hash-match، `live_gate_open(ACT_PULSE)` همه سبز؛ فقط `OCTOPUS_WIRE_BIO`+`OCTOPUS_WIRE_PULSE` (env، `shadow.py:110-113`) بسته. تنها مصرف‌کننده = `organism.py:769-778` که `_sleep_s`ِ واقعی را با دورهٔ قلبِ سایه جایگزین می‌کند → با ۳ فلگِ env، pacemakerِ واقعی به قلبِ سایه سپرده می‌شود. **(این همان ریسکِ «heart wire_open → live-sleep-override» حافظه است — الان maximally armed.)**

### مغز (همه پشتِ فلگِ پیش‌فرض‌خاموش، fail-soft)
- **context fence** = فقط observe (`model_router.py:191-196`، `opslib.alert` روی hit، هرگز block/mutate). +آداپتورِ ۴ callerِ غیر-router (debate_loop/doctor_setpoint/governor_epoch/chord، D4). «wired»≠«enforcing».
- **event spine ۴ producerِ زنده** (نه فقط lead): lead (`wiring.py:1766`)، doctor (`self_knowledge.py:360`)، ziman (`ziman_leg.py:574`)، proposal/mission (`owner_menu.py:105`) — همه پشتِ `OCTOPUS_WIRE_SPINE`؛ `dual_write` payload را sanitize می‌کند (D4، `event_spine.py:191`).
- **memory gate** episodic پشتِ **دو** فلگ (`MEMORY_GATE`+`LEAD_OUTCOME`، `wiring.py:1780`)؛ فقط IDهای PII-scrubbed.
- **outcome_store** durable/WAL/idempotent/replay (`outcome_store.py`).
- **drawdown_guard (D3)** SHADOW/advisory؛ `HH_DRAWDOWN_ENFORCE` هرگز پول را نمی‌بندد (enforcement = placeholderِ no-op).

---

## ۴. دروازهٔ تلگرام (W4)
- **گیتِ مالک همیشه اول؛ توکن additive:** `handle_update` برای non-owner قبل از هر dispatch `None` برمی‌گرداند (`center.py:517`)؛ `is_owner` = دقیقِ `from.id==owner` fail-closed (`tg_api.py:212`). `OCTOPUS_WIRE_CB_TOKEN` روی `ap:ok/no`، `ms:approve/reject`، `ok/no/later` توکنِ HMAC+expiry+destination-binding اضافه می‌کند (D4)؛ flag-off = byte-identical.
- **دکمه‌ها measurement-only (تأییدشده):** تنها مسیرِ settle = `app:approve`→`gate.settle` در `approval_channel.py:497-505,772` (اسکیمِ جدا، توکنِ یک‌بارمصرفِ خودش، TINV-7). `prop:`/`ap:`/`ms:`/legacy فقط state/measurement؛ `verdict_recorder` به‌طورِ ساختاری `delivered/settled/failed/verified` را ممنوع می‌کند (`verdict_recorder.py:33`).
- **verdict→outcome idempotent:** هر دو مسیر (center `_durable_verdict_outcome` و live_loop `_record_durable_verdict`) به یک `outcomes.db` با کلیدِ `correlation|proposal|event_type` می‌رسند → double-tap یا رأی از دو مسیر = صفر رویدادِ تکراری.

### دیباگِ تلگرام (W4)
- **شکافِ 409/singleton (ریسکِ اصلی، فقط با config مهار):** دو poller (approval_channel داخلِ organism با `TELEGRAM_BOT_TOKEN` + center.py جدا با `TG_CENTER_BOT_TOKEN`)، **بدونِ lockfile**. اگر `TG_CENTER_BOT_TOKEN` ست نباشد fallback به `TELEGRAM_BOT_TOKEN` (`tg_api.py:171`) → هر دو یک بات را poll → **409**. دفاع فقط advisory (هشدارِ ۱/ساعت + process-scanِ watchdog).
- **asymmetry `ms:test`:** owner-gated ولی **token-gated نیست** حتی با CB_TOKEN روشن (`center.py:1034-1059`)؛ با `OCTOPUS_WIRE_MISSION_RUNNER=1` یک subprocessِ worktreeِ ایزوله اجرا می‌کند (هرگز apply/patch/net/live-tree، ALLOWLIST `mission_runner.py:55`). برای parity، tokenize کن.
- در این لِین **صفر dead-flag**.

---

## ۵. سرشماریِ فلگ + ایمنی (W5) — census نقص‌ها
### فلگ‌های مرده/تزئینی (پاکسازی)
- **COSMETIC `OCTOPUS_WIRE_MINING`:** فقط در `wire_summary` (`wiring.py:601`) + ردیفِ UIِ `approval_channel.py:2192` خوانده می‌شود؛ نه `make_mining_leg` نه `mining_beat` وجود دارد → هیچ رفتاری گیت نمی‌کند.
- **DEAD `OCTOPUS_WIRE_TELEGRAM`** (فقط docstring، `wiring.py:10`؛ گیتِ واقعی = `TELEGRAM_BOT_TOKEN`).
- **DEAD `OCTOPUS_WIRE_INGEST_EXAMPLE`** (فقط echo در `ingest_adapter.py:271`).
- **DEAD-effect `HH_DRAWDOWN_ENFORCE`** (فقط یک فیلدِ status؛ `enforced=False` هاردکد).

### orphanها (تعریف‌شده، صفر importerِ production)
- **drawdown_guard** (`scripts/drawdown_guard.py`) — **صفر importerِ `_ops`**؛ گاردِ P0-money از هیچ مسیرِ خرجِ زنده reachable نیست. (owner-gated re-impl)
- **ziman_biology.py** کلِ ماژول orphan (`ziman_beat` `biology=None` پین، `wiring.py:2374`).
- **context_fence.build_context/fence_block** (`context_fence.py:46,61`) بی‌caller (prod فقط `screen`).
- **paper_mvo.run_paper_mvo** (test-only؛ جانشین = lead_outcome_recorder).
- توابعِ orphanِ داخلِ ماژولِ wiredِ lead_quote: `revise_quote/render_quote_html/quote_history/mark_sent`.
- **ماژول‌های مرده (صفر importer):** approval_channel_merge، approval_queue_unified، approval_state_machine، spine_reconcile، metrics/metric_separation، claims_backfill، deposits_export، ingest_adapter، sync_health، cortex/depth_guard، heart/replay_s، observability/tracer.

### تست‌های phantom/green-lie
- **۴ phantomِ عمداً مستثنا** (درست): test_effector_idempotency، test_drawdown_enforcer، test_mining_leg، test_tg_approval_store (این آخری در واقع سبز و prod-imported است — باید ثبت/مستند شود، نه گروهِ phantom).
- **🔴 یک green-lieِ واقعی (تأییدِ Coordinator):** از ۲۳۵ تستِ ثبت‌شده **۲۳۴ واقعاً اجرا می‌شوند؛ `test_mining_wiring.py` صفر assertion دارد** — pytest-style (۱۰ تابعِ `def test_`، fixtureِ monkeypatch)، بدونِ `__main__`، **نه در `PYTEST_TESTS`** (`run_all.py:251-259`) → `run_all` مستقیم `python file.py` می‌زند (`:270`) → هیچ تستی اجرا نمی‌شود، exit 0. بدتر: `wiring.make_mining_leg`/`mining_beat` که تست می‌کند اصلاً وجود ندارند. کامنتِ `run_all.py:253-257` **دقیقاً همین باگ را برای ziman توضیح داده و فیکس کرده** ولی mining جا مانده. → به PYTEST_TESTS ببر یا de-register کن + کامنتِ کهنهٔ `:178-179` را اصلاح کن.

### ایمنی (تأییدشده سالم)
- **STOP-ORGANISM:** در **۴۹ سایتِ `.exists()` در ۲۳ فایل** honor می‌شود؛ **هیچ مسیرِ پایتونی STOP را حذف نمی‌کند**. تنها حذفِ مجاز = `ACTIVATION-RUNBOOK-2026-07-21.ps1:88` (پشتِ `$DoIt`). `deploy-to-live.ps1:140-142` = گاردِ defense-in-depth که اگر artifactی del-STOP داشته باشد deploy را می‌شکند.
- **HALT-ALL:** `opslib.master_halted()` (`opslib.py:284`) ≻ STOP(architect)؛ honorers: `watchdog.py:31-36` (فیکسِ D-G)، twinِ D5 (`organism-watchdog.ps1:19-29`)، tg-center/live watchdogها. بدونِ گپ.
- **ps_writeback fail-closed (D1، تأییدشده):** choke-pointِ واحد (`ps_writeback.py:142`)؛ PUT فقط به `^/transactions/[0-9]+` با فیلدِ `{"labels"}`؛ قبل از PUT گیتِ per-item `_owner_verdict_ok` (bind به content_sha256، **single-use** consumed + **TTL-expire**)؛ verdict فقط owner-invoked. هیچ PUT بدونِ رأیِ durableِ هش‌خوردهٔ منقضی‌نشده.

---

## ۶. لیستِ نقص‌های اولویت‌بندی‌شده برای ایجنتِ بعدی
**P0 — ایمنی/پول/یکپارچگی (رأیِ مالک لازم):**
1. **[امنیت، فوری] فایل‌های `ACTIVATION-*.flag` فیزیکی + rollover تاریخ** → هر دو نیمهٔ گیتِ پولی/زنده روی دیسکِ درختِ زنده باز است؛ تنها دفاع = env-flags خاموش. اسکریپتِ deploy این فلگ‌ها را از درختِ زنده حذف می‌کند (گامِ owner-gated)؛ تا آن، آگاه باش که `paid_gate` و قلبِ ۶/۸ armed‌اند. `.env` مالِ ۱۸ژوئیه (توکن نچرخیده).
2. **[یکپارچگیِ تست] `test_mining_wiring.py` green-lie** → «۲۳۵ سبز» در واقع ۲۳۴ اجرا + ۱ no-op. فیکس: PYTEST_TESTS یا de-register + اصلاحِ کامنت.
3. **[P0-money] `drawdown_guard` orphan + no-op** → گاردِ drawdown از هیچ مسیرِ خرج reachable نیست؛ enforcement ساخته نشده. re-impl + wire + آستانه = رأیِ مالک.
4. **[money] زنجیرهٔ reconcile orphan** (claims_backfill/deposits_export/sync_health) — Track-B هرگز live نشد.

**P1 — بهداشتِ سیم‌کشی (اکثراً غیر-owner، ولی mining/biology owner-gated):**
5. dead-flag `OCTOPUS_WIRE_FITNESS` (`append_outbox` صفر caller) — wire یا drop از summary.
6. cosmetic `OCTOPUS_WIRE_MINING` + dead `OCTOPUS_WIRE_TELEGRAM`/`OCTOPUS_WIRE_INGEST_EXAMPLE` — prune.
7. orphan `SprintRunner` (`organism.py:284`) — یا `sprint_beat` بساز یا ساختش را بردار.
8. ماژول‌های مرده (approval_*_merge/unified/state_machine، spine_reconcile، tracer، …) — wire-or-remove.
9. توابعِ orphanِ داخلِ ماژول‌های wired (context_fence.build_context/fence_block، lead_quote.*).
10. `ziman_biology` کلِ ماژول (owner-gated: اقتدارِ biology).
11. `test_tg_approval_store.py` را ثبت/مستند کن (سبز، prod-imported، اشتباهاً phantom گروه‌بندی شده).

**P2 — تاب‌آوری:**
12. **آلارمِ chrono:** اگر chrono down شود کلِ spine بی‌صدا inert می‌شود — health-alarm اضافه کن (`organism.py:349`).
13. کوپلینگِ INGEST↔SCHOOL را مستند/decouple کن.
14. `ms:test` را tokenize کن (parity با vote verbs).
15. لاکِ singletonِ token-keyed برای دو poller (به‌جای فقط هشدارِ 409).
16. helperِ `_epoch_fire` را در ۸ سایتِ hand-rolled یکسان کن (`every_n<=0` معنای متفاوت دارد).

---

## ۷. ناوردی‌ها و مسیرِ این ممیزی
- درختِ کانونی: `master = 4eb5543` (= germline×2). live tree `F:\backup` روی `a2183c3` (۳۱+ کامیت عقب) — سیم‌کشیِ **قدیمی** را می‌رانَد (بدونِ کارِ موجِ اخیر). این ممیزی درختِ کانونی را دید.
- **صفر تغییرِ کد در این ممیزی؛ صفر لمسِ درختِ زنده؛ STOP-ORGANISM `C8FE7176…5CD099` دست‌نخورده.**
- منبعِ کاملِ لِین‌ها: خروجیِ ۵ ممیزِ read-only در transcript؛ این سند سنتزِ آن‌هاست. مرجع‌های مرتبط: [[WAVE-INTEGRATION-2026-07-21]] · `_ops/deploy/DEPLOY-2026-07-21.md`.
