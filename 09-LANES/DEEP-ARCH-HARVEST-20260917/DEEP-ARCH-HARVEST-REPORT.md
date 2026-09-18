---
mission: OCTOPUS-DEEP-ARCH-HARVEST-2026
role: CHIEF_SYSTEMS_ARCHAEOLOGIST_AND_HARVEST
mode: STRICT_READ_ONLY (Tier 1 / Class A)
date: 2026-09-17 (Australia/Sydney)
canonical_main: ae187e03ecb4c057bd63f424f45f519d9b239771 (verified = current main HEAD at 06:32Z)
receipt: OCTOPUS-DEEP-ARCH-HARVEST-2026-20260917T063244Z-f461f0f53b41 (sha256(INTENT)[:12])
gov: GOV_VERSION=V8, LADDER=L2
evidence_base: read-only tarballs of 4 repos + gh GET-only census + vault documents; zero git mutations; zero live-node contact; zero secret/PII values printed
---

# OCTOPUS-DEEP-ARCH-HARVEST-2026 — گزارش باستانی-فنی جامع

## 1. EXECUTIVE SYNTHESIS — اختاپوس هایبریدی چیست؟

موجودیت «اختاپوس» یک ارگانیسم نرم‌افزاریِ تک‌کانون-چندبدنی است: **یک مغز حاکمیتی (کد fail-closed در ofn-node) + یک قلب مالی (برد 138) + شش بازوی ادراکی/اجرایی (نودهای 180/182/100/160/193/114) + یک حافظهٔ بلندمدت (الت ابسیدین F:\backup) + یک لانهٔ تولد ایده‌ها (Armin/langar/vbaa-patches)**. هویت واقعی آن نه «یک ربات تلگرام» و نه «یک استور فروشگاهی»، بلکه یک **ماشین بقا با اقتصاد داخلی** است که در آن هر اثر بیرونی پشت ۵ لایهٔ پشت‌سرهم گیت شده و دکترین مرکزی آن یک جمله است که در سه فایل مختلف تکرار شده: *ready is not authorized* (`ofn/kernel/revenue_states.py:1-8`، `ofn/kernel/callbudget.py:55-58`، `ofn/kernel/spend_fence.py:1-10`).

سه یافتهٔ تعیین‌کنندهٔ این کاوش:

1. **اختاپوس امروز صبح (09-17) خودش را به‌روزرسانی کرد**: زنجیرهٔ PR#263→#264→#265 دقیقاً ساعت 04:32–05:02Z در main ادغام شد و HEAD فعلی همان رفر کانونیکال ae187e03 است؛ PR#265 فایل runtime برد ۱۳۸ (`self_model_producer.py`) را با طبقه‌بندی DECLARED≠WIRED به main برد. ارگانیسم همزمان با این کاوش، در حال خودپذیرایی بود.
2. **شکاف اعلام/سیم‌کشی نه باگ نیست، معماری است**: کل کد حول تمایز AST-present در برابر RUNTIME_WIRED ساخته شده (`self_model_producer.py:96-119`)؛ حتی قابلیت‌هایی که کامل نوشته‌اند (fake_executor، OnlyFans scaffold، vbaa guards، NATS mirror) عامدانه خاموش/قفل‌اند.
3. **گلوگاه موجود نه فناوری، نه گیت — تقاضاست**: منابع رسمی tender مرده‌اند (`demand_harvest.py:1-10`)، نودهای 100/160/114 زنده اما بیکارند (GAP-09)، و برد پول بدون swap و بدون backend تصویر لحظه‌ای است (GAP-06). ارزش بعدی در «وصل‌کردن عضوهای موجود» است، نه نوشتن عضو جدید.

## 2. ARCHITECTURAL PILLARS — ده لایه با ارجاع دقیق

### لایهٔ ۱ — توپولوژی ۴ مخزن

| مخزن | اندازه | نقش واقعی در ارگانیسم |
|---|---|---|
| **ofn-node** @ ae187e03 | ۳۴۵۴ فایل؛ ۳۵۹ py در `ofn/` + ۵ زیرسیستم مستقل + ۴۸۱ فایل تست | DNA اجرایی ارگانیسم: `ofn/kernel/` (~۲۳۰ ماژول واژگان fail-closed)، `ofn/agents/` (۳۴ اندام)، `ofn/adapters/` (I/O)، `octopus_survival/`، `octopus_observation/`، `octopus_exec/`، `octopus_recovery/`، `shadow_homeostasis/`، `contracts/`، `budget/` |
| **Armin** | ۵ فایل | جعبهٔ ایده: `سیستم-همیشه-روشن-پرامپت-و-دستورالعمل.md` = طرح پیدایش langar؛ `heart-awareness-map-v3.html`. بیزینس واقعی نقاشی اینجا نیست — روی برد ۱۳۸ است (tenant `lead`، port 8792، `painting.sqlite`) — «جعبهٔ سیاه naming» (AUDIT-ARMIN.md). تصمیم مالک الف/ب باز است |
| **langar** | ۹۷ فایل | بات همراه تلگرامی HRV/RMSSD با قانون اساسی ۱۳/۱۴ اصل‌های (`core/constitution.py`)، self_improver، researcher. آمادگی اتصال به زنجیرهٔ درآمد: پایین (۹ قطعهٔ مرده، کپی‌های سایهٔ `_verify/` با schema v3 که تست سبزِ کاذب می‌دهد، امضای ناسازگار synthesizer — AUDIT-LANGAR.md §C3). دور از مسیر پول بماند |
| **vbaa-patches** | ۳۱ فایل | بستر بازبینی ۳ گارد امنیتی روی‌هم‌چیده: `artifact_admission.py` → `argument_provenance_guard.py` → `executor_handle_firewall.py` (`_ops/vbaa/`). ۹-way split در خود مخزن MERGE شده اما **صفر پذیرش در ofn-node** (بدون `_ops/`، بدون هیچ import — grep تأیید) |

**شکاف‌های پذیرش (Adoption Gaps):** ۳ گارد vbaa؛ `agi2027_control/` + ابزارهای ops در شاخهٔ رهاشدهٔ `release/p0` (PR#71 امروز بدون merge بسته شد؛ شاخه ۱۲ جلوتر/۱۸۶ عقبتر از main)؛ جزیره‌های بی‌ریشهٔ `codex/executor-safety-20260915` (failover پرووایدر + FIX-B) و `receipts/durability-snapshot-20260916` (فقط با tree-copy قابل مصرف چون اجدادشان کامیت secret مسدود را رد می‌کند)؛ یتیمِ ۱۱-کامیتی `rootfix/phase1-rca-20260916` بدون PR.

### لایهٔ ۲ — دکترین DECLARED vs WIRED

- هستهٔ دکترین: `ofn/adapters/self_model_producer.py` (۶۱۸ خط، schema `octopus.self-model.v3`): `classify_capability_status()` در خط ۱۰۱ فقط سه حالت برمی‌گرداند — `RUNTIME_WIRED` / `PRESENT_UNWIRED` / `UNKNOWN` — و `reading_status_for_capability()` خط ۱۱۶ تصریح می‌کند **AST هرگز healthy نیست** (اصلاح C7-3). جدول `CAPABILITIES` خطوط ۷۹–۹۴ (۱۳ قابلیت با نماد الزامی) و `MEMBER_UNITS` خطوط ۵۴–۶۲ (۷ یونیت برد: bridge، control_router، cycle_settler، router، revenue_timer=`capability-school-revenue.timer`، supervisor، verify_dispatcher).
- رتبه‌بندی قابلیت‌ها: قابلیت «سالم» فقط وقتی است که هم کد در checkout باشد (`check_capability` خط ۲۴۵ با `_symbol_present` AST-scan خط ۲۲۵) و هم سیم‌کشی runtime از بیرون تزریق شده باشد (`runtime_wired` پارامتر `_collect_capabilities` خط ۳۱۴).
- **نقاط کور خودمدل‌سازی نسبت به ۷ نود**: self-model فقط بردِ ۱۳۸ را می‌بیند؛ grep برای nats/fleet/180/182 در این فایل عملاً صفر است؛ قرارداد NATS داخل مخزن یک اسکلت خالی است (`contracts/nats_leaf_mirror_init.py:22-30`: `enabled: False`, «no network, no writer cutover»). سلامت فلیت در کد وجود دارد (`ofn/kernel/fleet.py`: «never measured → UNKNOWN»، `MIN_BASELINE_SAMPLES=20`) اما به self-model وصل نیست.
- نمونه‌های سنجش‌شدهٔ declared≠wired در main: `OFN_NO_AUTO_CUSTOMER_SEND` **به این نام وجود ندارد** (گارد واقعی: پنج‌لایه در `send_one` — لایهٔ ۳)؛ `gates.json` فقط یک مصرف‌کنندهٔ تستی دارد (`tests/test_release_gate_regression.py:208`)؛ `tools/leads_master.json` صفر مصرف‌کنندهٔ کدی دارد (قیف واقعی روی state برد زندگی می‌کند)؛ `OBSERVATORY`/`CORTEX_HYPOTHESIS` بازنشسته اما به‌صورت flag-frozen نگه داشته شده‌اند (`.cursor/hooks/guard_flags.py`، `tests/test_flag_freeze.py`، CI `observatory-fixture.yml`)؛ تستی که می‌گوید revenue_states «متعلق به PR#77 باز است» خودش کهنه است چون فایل در main هست (`tests/test_arch_token_otel_contracts.py:6` در برابر `ofn/kernel/revenue_states.py` موجود).

### لایهٔ ۳ — اوراکل‌های توقف و لچ‌های ایمنی

- **تک‌اوراکل HALT**: `ofn/budget/opslib.py:20` `HALT_FLAG = OFN_ROOT/"HALT-ALL"`؛ `master_halted()` خطوط ۲۸–۳۷ fail-closed — اول `HALT_SURVIVAL_LOOP=1` (خط ۳۱)، بعد فایل پرچم (خط ۳۳)، و هر استثنا ⇒ `halt-check-error` (خط ۳۶–۳۷). شیمِ `budget/opslib.py:1-5` صریحاً می‌گوید «اوراکل دوم نساز» (و `ofn/budget/opslib.py:5-8`: نه kill-فایل‌های ویندوزی خزانه — همان واگرایی HALT-ALL/HALT که از منبع تأیید شد).
- مصرف‌کنندگان master_halted (۷ نقطه): `ofn/agents/capability_token.py:87`، `outbound_worker.py:214` و `:451`، `quote_pipeline.py:79`، `release_pipeline.py:106` و `:184`، + تست. لایهٔ ۳ِ خالص: `ofn/kernel/halt.py:13-24` (غایب=RUNNING طبیعی، ناپارسا=HALTED).
- ترتیب کمربندها در `outbound_worker.send_one` (خط ۲۰۴): halt→flag(`OCTOPUS_WIRE_LEAD_OUTBOUND`)→conservation غیبت مالک (`owner_absence`)→گیت per-effect قبل از settle (اصلاح امنیتی W1). سقف‌ها: `cap_per_beat=2`، سقف روزانه (کامنت قدیمی ۱۰ / کانفیگ D27 = ۲۵ — هر دو ثبت).
- سایر کلیدها: `STOP-AUTONOMY` روی supervisor برد ۱۳۸ زندگی می‌کند (CURRENT-TRUTH خطوط ۲۳۷–۲۴۹؛ در main فقط `HALT_SURVIVAL_LOOP` هست)؛ `CHANNEL-REVOKED` در main یافت نشد — status: unverified. گیت ارسال مشتری به نام پرامپت وجود ندارد؛ معادل سازوکاری‌اش همان پنج‌لایهٔ send_one + `revenue_states` است.

### لایهٔ ۴ — قراردادهای مغز و شجره‌نامه

- `ofn/agents/brain_schema.py` (PR#181، GAP-066): `brain_input.v1`؛ ۶ نوع رویداد، ۳ بیزینس (painting/ziman/studio)، ۵ اکشن (rank/propose/verify/hold/escalate)؛ `BrainProposal.hold_external=False` خط ۷۶ با کامنت «owner vote 2026-09-07 UNLOCK-REGISTRY L23» و `may_authorize=False` ساختاری.
- `ofn/agents/brain_wake.py`: پل قلب→مغز؛ رویدادهای WAKE_WORTHY خطوط ۴۴–۴۸ (`payment.verified`, `payment.claimed`, `communication.quote_requested`, `lead.discovered`, `order.received`)؛ پاکت `cognitive_wake.v1` با `wake_sha256` و مهلت ۴ ساعته به outbox مش می‌رود تا مغزِ ۱۸۰ (لامای محلی) فکر کند و ۱۸۲ تأیید کند — حلقهٔ سه‌بردی با ۲۲/۲۲ ACK اثبات‌شده.
- `ofn/agents/release_pipeline.py`: `EffectGate.release()` خطوط ۹۱–۱۲۲ (halt/consent/payload را از state زنده بازاستنتاج می‌کند)؛ `pipeline()` خط ۲۲۰ و دو-گامیِ مالک در `ofn/kernel/release_switch.py` — «سوییچی که باید نگه داشته شود، نه پرچمی که فراموش می‌شود» (docstring خطوط ۱–۱۷)؛ `_config_gates_open()` خط ۱۲۵ گیت‌های بستهٔ واقعی (secret_rotation/partner_precondition) را از کانفیگ می‌خواند نه hardcoded-True.
- واگرایی عامدانه: پایٔ ziman هنوز نگه‌دار است — `ofn/ziman_cycle/gates.py:17` `hold_external=True` پیش‌فرض و `check()` fail-closed.
- تله‌های امنیتی: `ofn/agents/brain_schema.lock` = `c90c3697… brain_schema.py`؛ `contracts/FROZEN.lock` = `0701aeff… runtime_truth_v1.py`؛ و پین‌های CRLF دوگانه در `tests/test_brain_schema.py:52`، `tests/test_doctor_lane_contract_map.py:60`، `tests/test_runtime_truth_contract_frozen.py:31` (هشِ CRLF باید ≠ هشِ LF باشد — دستکاری EOL فوراً رد می‌شود).

### لایهٔ ۵ — زنجیرهٔ بقا و چرخهٔ مالی

- زنجیرهٔ واقعی در کد: هاروسترها (`h1_harvest/h1_buysw/h1_buysw_dom` با `MIN_VALUE_AUD=400` در `h1_buysw.py:22`؛ `h3_strata`؛ `nsw_ocp_harvest`؛ `seek_harvest`؛ `ziman_tender_harvest`؛ `demand_harvest` = منابع مرده) → `ofn/adapters/lead_store.py` (با باگ `MAX_PAGE=100` خط ۱۳ که PR#259 باز در حال ترمیم آن است) → `lead_email_writer` → `quote_engine.py:45` (`QUOTE_MAX_AUD` پیش‌فرض ۲۵٬۰۰۰) → `quote_pipeline` → `release_pipeline` (EffectGate + دو-گامی مالک) → `outbound_worker.send_one` → `lead_outbound_transport` + `mail_credentials` (SMTP خروجی) → `imap_listener.py` (ورودی: reply/bounce/optout، هر ۱۵ دقیقه، فقط ایمیل‌های خودِ ما) → `reply_queue_bridge` → صف مالک.
- `money_executor` هنوز متولد نشده: `ofn/adapters/fake_executor.py` دروازهٔ کامل (policy→witness→decision→payload-sha) را «صادقانه جعل» کرده تا وقتی اجراکنندهٔ واقعی بنشیند، قواعدش از قبل پین باشد.
- تایمر درایو روی برد: `octopus-revenue-drive.{service,timer}` هر ۶ ساعت، $0، هرگز ارسال بیرونی؛ رسیدها `state/revenue-drive/receipts.jsonl` + `owner-review.json` (CURRENT-TRUTH:392-403).
- خروجی‌ها و گیت‌ها: SMTP (wire flag + consent + halt)؛ تلگرام فقط از مسیر صف مالک (`octopus_survival/telegram_bridge.py:1-16`: «queue نه sendMessage»، `MAX_EVENTS_PER_DAY=20`)؛ Shopify (`shopify_connector/shopify_oauth/platforms/shopify`)؛ OnlyFans = اسکلت قفل‌دوطرفه (`platforms/onlyfans.py:1-15`، `OFN_ONLYFANS_HTTP_ARM` هرگز ست نشده).
- **تناقض سقف‌ها (resolution: open)**: پرامپت مأموریت $500/ماه + $20/24h + $2/task؛ برد ۱۳۸ state = $100/ماه + $10/24h (CURRENT-TRUTH:400)؛ کد = `D27_DAILY_SEND_CAP=25` + `D27_DAILY_SPEND_CAP_AUD=50` (`ofn/config.py:32-33`)؛ `callbudget.py:48-53` = REMOTE 100/روز، REMOTE_DEEP 5/روز؛ حافظهٔ rootfix = کانون 500AUD/ماه. پنج عدد، پنج منبع، هیچ‌کدام بر دیگری غلبه ندارد — رکورد کامل شد.

### لایهٔ ۶ — شبکهٔ عصبی ۷ بازو (از اسناد، بدون تماس زنده)

ماتریس نقش‌ها از `06-EVIDENCE/FLEET-HEARTBEAT-CANONICAL.md` + رجیستری `fleet_node_registry.v1` (LIVE-STATE-REPORT §2): **138=commander** (تنها enqueue/lease/writer؛ میزبان supervisor اتونومی v1.2)؛ **180=quality_restore_copy_RO** (هرگز commander)؛ **182=lab_witness + میزبان JetStream — DEGRADED** (GAP-02: حلقهٔ PathExists ≈۲ هسته می‌سوزاند)؛ **100=knowledge_retrieve** (coding worker، زنده اما بیکار GAP-09)؛ **160=knowledge_prep** (shadow verify، بیکار)؛ **193=model_infer** (پایلوت NPU)؛ **114=eval_batch**. هاب NATS روی لپ‌تاپ ۱۹۱؛ ۴ leaf زنده (138/180/193/114)؛ استریم `OCTOPUS_EVENTS` (subjects `octopus.>`، 2GB). اصطلاح «Audit Latch» برای ۱۸۲ فقط در خودِ heartbeat آمده — سازوکار مستقل: unverified. «دیده‌بان خودمختاری 160» هم فقط برچسب است — supervisor واقعی روی ۱۳۸ است: unverified. تفکیک امتیاز: pulse ۱۳۸ زیر `User=nobody/ProtectSystem=strict` اجرا می‌شود ولی systemd هشدار «nobody not safe» داده (توصیه: کاربر اختصاصی + credential 640)؛ `/etc/nats-leaf/` root-only 700. سِکِرت‌ها SoT روی لپ‌تاپ (MUST_STAY_ON_LAPTOP تا رسید Promotion).

### لایهٔ ۷ — باستان‌شناسی PRها

سرشماری کامل: **۲۵۳ PR** (۲۳۱ merged / ۱۰ open / ۱۲ closed-unmerged) روی ۱۶۷ شاخه. عمیق‌ها: **#71** امروز 05:13Z بدون merge بسته شد — شاخهٔ `release/p0` (12/186) با `agi2027_control/` و ابزار backup/restore/download قفل شد؛ **#181/#182** (brain_schema + reply-bridge) 09-04 ادغام؛ **#254** (octagonal/vertex kernel) 09-15؛ **#263** (همگرایی board138، option-a، ۵ فایل runtime با زنجیرهٔ sha256) + **#264** (ترمیم ۶ قرمز تست gates.json) + **#265** (= HEAD فعلی؛ طبقه‌بندی self-model + پذیرش فایل runtime برد) هر سه امروز. PRهای باز بزرگ: #259 (+۶۷۰۹، ترمیم سقف ۱۰۰تایی accounts)، #260 (+۴۶۵۶)، #251 (+۳۴۹۶)، #262، #261 — «PRهای Elahe» همه در خود ofn-nodeاند. چهار شاخهٔ جزیرهٔ بی‌ریشه (codex/executor-safety، receipts/durability-snapshot، ofn/wire، ofn/heartbeat) ساختاراً غیرقابل merge‌اند. `rescue/wo-align-20260906` نسخهٔ قدیم‌تر self_model_producer را دارد — کاندیدای تناقض با نسخهٔ merge شده.

### لایهٔ ۸ — گسل‌ها و بدهی پنهان

(۱) CRLF/محیط: پین‌های دوگانهٔ هش خوب کار می‌کنند اما runtime برد Whole-file-CRLF داشت (DC-03D)؛ CI ماتریس ubuntu+windows با `PYTHONUTF8=1` (full-suite.yml)؛ ریشهٔ مخزن پر از `*.bak-*` است. (۲) `budget/opslib.py:30-41` **بیکن دیباگ باقی‌مانده** که هنگام import به `F:\backup\debug-11f994.log` می‌نویسد. (۳) اشاره‌های زامبی به `OFN_WIRE_OUTBOUND` (۵ ref) با اینکه alias در `config.py:31` حذف شده. (۴) gates.json بدون مصرف‌کنندهٔ runtime. (۵) leads_master.json با PII داخل مخزن، بدون مصرف‌کننده؛ نسخهٔ واقعی air-gap شده روی state برد. (۶) منابع demand مرده (NSW eTendering از فوریه ۲۰۲۵ پایان). (۷) `deploy/systemd/` فقط ۱۴ یونیت `ofn-*` دارد در برابر ~۸۱ تایمر زندهٔ `octopus-*` روی برد — کانون توصیف استقرار کهنه است.

### لایهٔ ۹ — یکپارچگی با مغز ابسیدین

جریان مستند: pulse ۶۰ثانیه‌ای ۱۳۸ → NATS leaf → هاب :7422 → JetStream → مصرف‌کنندهٔ durable `vault-pulse` که `FLEET-HEARTBEAT-CANONICAL.md` را نگه می‌دارد (خود اسکریپت روی لپ‌تاپ است — unverified محلی). سایر سطوح: بلوک‌های auto در `OCTOPUS/CURRENT-TRUTH.md` با مارکرهای OCTOPUS-AUTO (نقص‌های ثبت‌شده: drop BOM)؛ صفوف append-only در 01-Dashboard؛ spool مالک با ACK_SEEN و W24 binder. نقشه‌ها: `00-INDEX.md`، `00-HOME/CURRENT-TRUTH-INDEX.md`، `00-HOME/SUPERSESSION-INDEX.md` → `SUPERSESSION-LEDGER.jsonl`، ۷ MOC در `4D-Vault/00-MOC/`. دفتر شکاف: نه «GAP-LEDGER» به این نام، بلکه جدول ۹ردیفی زنده در LIVE-STATE §9 + دفتر فصلی `GAPS-100-2026-09-01.md` (۱۰۰ آیتم، ۵ ستاره). اصل عدم حذف: الگوی ERRATUM/SUPERSEDED-BY (۳ نمونهٔ مستند در گزارش). 06-EVIDENCE = ۱۰۳۹ فایل md.

### لایهٔ ۱۰ — پتانسیل‌های کشف‌نشدهٔ خودمختاری

- **نردبان بقا A0–A7**: `octopus_survival/loop.py` (S6-D11) — آزمایش بدون hypothesis/kill/deadline/rollback رد می‌شود؛ A7+ نیاز به رأی مالک؛ preregistration تغییرناپذیر؛ PARSE_DRIFT هرگز حدس نمی‌زند؛ قطعی پرووایدر ⇒ park + rollback خودکار کاناری. کارنامهٔ اقتصادی: `economy.py` (مدرسهٔ اپیزود D-27، `KILL_METRIC="wrong_recipient"`).
- **خانه‌ستازی سایه‌ای (shadow homeostasis)**: `shadow_homeostasis/` ۱۰ ماژول — `homeostasis.py` SETPOINTS_V1 (شامل `hrv_min_for_green: 0.2`!)، `metacontrol.py` وزن‌های امتیازدهی ۶ حوزه با قید «Never sets executable True»، trust/world_model/canonical. یک خودتنظیم‌گر کامل که فقط منتظر سیم‌کشی است.
- **غیبت‌سنج مالک**: `ofn/agents/owner_absence.py` — dead-man معکوس (۳ تیک غایب دکتر ⇒ Conservation)، «سقف در غیبت = صفر مطلق».
- **شاهد سه‌سطحی**: `ofn/agents/external_witness.py` — WITNESS_A/B/C + تشخیص **SILENT_FLIP** (مقدار عوض شده بدون ruling_id = مهم‌ترین آلارم سیستم). WAL فعلاً WITNESS_A روی ۱۸۲.
- **کدینگ ورکر و ۱۹۳**: نود ۱00 به‌عنوان sandbox کدنویسی bound شده اما بیکار است (GAP-09: ~۱۱GB RAM آزاد)؛ ۱۹۳ پایلوت NPU برای استنتاج مدل — هر دو ظرفیت بلااستفاده.
- موتور فرضیه به مفهوم retired (CORTEX_HYPOTHESIS) از کد حذف شده؛ جایگزین واقعی‌اش نقش ۱۹۳ + `octopus_observation/scorer.py` است.

## 3. HIDDEN GEMS & UNWIRED TALENTS — ۵ قابلیت خاموش

1. **`ofn/adapters/fake_executor.py`** — دروازهٔ کامل owner-decision→provider با قواعد fail-closed پین‌شده؛ هر بار که «executor برای follow_up_at» (ستارهٔ GAPS-100) رأی بگیرد، بدنهٔ واقعی فقط باید transport عوض کند.
2. **`shadow_homeostasis/` (کل پکیج)** — هستهٔ خودتنظیم‌گری HRV-محور با متاکنترل ۶حوزه‌ای؛ `executable` ساختا false است تا رأی روشن‌کردن برسد. پل طبیعی به langar (RMSSD) وجود ندارد — ساخته نشده.
3. **`ofn/agents/external_witness.py` + SILENT_FLIP** — سیستم ضدخودفریبی از پیش ساخته شده و در main نشسته؛ مصرف‌کنندهٔ فعلی فقط WAL است؛ می‌تواند هر ادعای حیاتی فلیت را پوشش دهد.
4. **اسکلت مارکتینگ OnlyFans دولاکه** (`platforms/onlyfans.py`) + **سه گارد امنیتی vbaa** (artifact-admission/provenance/firewall) — دو پأ کامل و آماده که فقط منتظر owner-GO/پذیره‌اند.
5. **`agi2027_control/` در release/p0 گیر کرده** — ماژول runtime/rollback/integration برای کنترل نسل بعدی، به‌علاوهٔ ابزار backup/restore-drill که در main نیست؛ محتوای باارزشِ strand شده در PR#71 بسته‌شده.

(ششمی افتادنی: واژگان ~۲۳۰ ماژولی kernel با فلسفهٔ «witness تک‌عددی» — یک کتابخانهٔ ریاضی-امنیتی که مصرف‌کنندهٔ واقعی‌اش فقط تست‌ها هستند.)

## 4. CRITICAL VULNERABILITIES & DEBT — ۳ گلوگاه ساختاری

1. **تمرکز تک‌بردی بدون شبکهٔ ایمنی**: ۱۳۸ هم commander است هم برد پول هم میزبان supervisor؛ بدون swap (GAP-06)، بدون backend تصویر (DC-03E0: ext4 روی eMMC یگانه، لجر germline روی CIFS پر)، و self-modelش کور به ۶ بدن دیگر. از دست دادن ۱۳۸ = از دست دادن ارگانیسم اجرایی.
2. **واگرایی کانون/ران‌تایم و بهداشت شاخه**: برد worktree کثیف را اجرا می‌کند (نه commit را)؛ main امروز جلو رفت ولی ۱۶۷ شاخه/۲۵۳ PR با ۴ جزیرهٔ بی‌ریشه و ۱۰ PR باز بزرگ؛ deploy/systemd با واقعیت برد نمی‌خواند؛ ریسک اینکه «کد کانونیکال» و «کد زنده» دو چیز شوند دوباره بازتولید می‌شود (همان DC-03D).
3. **پارگی اعداد و PII**: پنج مجموعه سقف ناسازگار پول/ارسال (لایهٔ ۵)؛ کلیدهای اضطراری (STOP-AUTONOMY، CHANNEL-REVOKED) بیرون از مخزن؛ `tools/leads_master.json` با PII داخل git بدون مصرف‌کننده؛ بیکن دیباگ در شیم opslib؛ منابع رسمی demand مرده. هیچ‌کدام سخت نیست، همه با هم «بار شناختی مالک» را می‌سازند.

## 5. EVOLUTIONARY ROADMAP — به سوی خودگردانی حداکثری

1. **ریزش تک‌نقطه‌ای ۱۳۸ (هفتهٔ ۱)**: swap file، mirror روزانهٔ state پول به ۱۸۲ (که JetStream را هم دارد)، و export منظم overlay کثیف به شاخهٔ side (الگوی E1A که امروز با #263 اثبات شد).
2. **سیم‌کشی خودمدل فلیت (هفتهٔ ۱–۲)**: `fleet.py` + MEMBER_UNITS را به رجیستری NATS وصل کن؛ GAP-02 (فرسایش CPU نود ۱۸۲) را قبل از هر بار دیگری ببند چون شاهدِ سیستم همان است.
3. **پذیرش گاردها (هفتهٔ ۲)**: سه گارد vbaa را به‌صورت PR روی ofn-node بیاور (مصرف‌کنندهٔ طبیعی: fake_executor و مسیر lease)؛ `agi2027_control` را با tree-copy از release/p0 نجات بده.
4. **تولد money_executor واقعی (هفتهٔ ۲–۳)**: بدنهٔ transport روی fake_executor؛ رأی مالک برای follow_up_at executor (ستارهٔ GAPS-100) پیش‌شرط است.
5. **احیای تقاضا (مستمر)**: منابع مرده را با کانال‌های زنده عوض کن (Airtasker watch از قبل wired است)؛ نود ۱۹۳ را به رصد بازار/قیمت وصل کن؛ 100/160 را از «زنده اما بیکار» به دو شغل مشخص (sandbox کد + shadow verify سیکل مالی) ببر — بدون سخت‌افزار جدید.
6. **پل HRV↔homeostasis**: خروجی RMSSD langar را (پس از پاکسازی _verify) به SETPOINTS_V1 تزریق کن — ارگانیسم برای اولین بار «احساس بدن» می‌گیرد؛ تصمیم مالک دربارهٔ langar روی مسیر پول نگه داشته شود.
7. **یکنواخت‌سازی اعداد**: یک فایل کانونیک سقف‌ها با scope صریح (API-broker در برابر spend در برابر send-count)؛ پنج عدد امروز را با resolution: open ثبت کردم تا رأی مالک یکی را کانون کند.

---

### ثبت انطباق
- REMOTE_MUTATIONS=0 · EXISTING_FILE_MUTATIONS=0 · DELETE/OVERWRITE/MOVE=0 · git_commands_run=0 · live_node_contacts=0 · secret_values_printed=0 (فقط نام/مسیر/کلاس حساسیت).
- منابع: تاربال فقط-خواندنی ۴ مخزن (@ae187e03 برای ofn-node)؛ gh GET-only (pr list/view/diff، api branches/compare/commits)؛ اسناد vault (مسیرها در متن). اعداد بدون منبع در متن با status: unverified علامت خورده‌اند.
- پاکسازی: `C:\Users\Armin\harvest-20260917\` (تاربال‌ها) پس از تحویل قابل حذف است؛ rollback این لِین = حذف پوشهٔ `09-LANES/DEEP-ARCH-HARVEST-20260917/`.
