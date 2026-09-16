# Octopus — نقاط کورِ جدید (DELTA-2: ۱۳۱–۱۹۶)

> اسکنِ عمیقِ دوم، ۲۰۲۶-۰۷-۲۷. مکملِ ۱۰۰ + DELTA.
> سه ایجنت از رویِ کد خواندند: صفحهٔ پول/امنیت، مغزِ سمتِ PF، پاها+ژنوم.
> **یک ایجنت (ارکستراسیون مرکزی) دوباره سقوط کرد** → آیتم ۱۹۶.
>
> **دو یافتهٔ بنیادیِ بازنویسی‌کنندهٔ نقشهٔ ذهنی:**
> 1. مغزِ سمتِ PF **سرگردان نیست** — به orchestrator/langar/pf_os وصله. ولی **صفر دادهٔ واقعی** دریافت کرده (bandit_state.json وجود ندارد).
> 2. حلقهٔ genome→behavior **در ۴ نقطه قطع است** — پاسخِ قطعی به سوالِ بازِ DELTA آیتم ۱۱۷.

---

## بخش ۰ — تصحیح‌های حیاتیِ این دور

| # | آنچه قبلاً گفته شد | واقعیت | منبع |
|---|---|---|---|
| C8 | مغزِ سمتِ PF «سرگردان/وصل‌نشده» است | ❌ به ۷ فایلِ production وصله (orchestrator، langar_bot، pf_admin، pf_os/*). ولی همهٔ فایل‌های state خالی‌اند. | grep قطعی |
| C9 | ThompsonBandit «ممکن است BCM را بیدار کند» | ⚠️ واقعاً یک یادگیرندهٔ Beta-Bernoulliِ خوب‌پیاده‌شده‌ست (recency decay، exploration floor، min-pull، approval gating، atomic persist) — ولی **صفر observation**. | `brain/learning.py` |
| C10 | genome loop «بسته‌نشده» (مبهم) | ✅ **قطعاً در ۴ نقطه قطع**: NOTEها ۹۹.۴٪، doctor فقط METRIC/PROPOSAL می‌خواند، _ops هیچ‌وقت values.yaml نمی‌خواند، human_two_key فقط مستنده. | §۳ زیر |
| C11 | second-brain deprecated ولی parity بهش ارجاع می‌دهد | ✅ تأیید. brain_core parity `compared:0` — سیم به جسد. | DELTA آیتم ۱۱۶ |

---

## بخش ۱ — صفحهٔ پول/امنیت (۱۳۱–۱۵۵) — حساس‌ترین

### ۱۳۱. 🔴 CRIT — `redact()` fail-open است
`approval_channel.py:2859` — وقتی لایهٔ redaction استثنا بندازد، **متنِ کاملِ بدون-redact** به `send_text` برمی‌گردد → PII/secret به تلگرام نشت می‌کند. فیکس: در صورت استثنا `REDACTED_BODY` برگردان.

### ۱۳۲. 🔴 HIGH — `_redact_pii()` لایهٔ دوم خاموش است
`approval_channel.py:2874` — هر خطای import/attribute را بی‌صدا می‌بلعد. وقتی `sensory_bus` نباشد، دومین خطِ دفاعِ PII no-op می‌شود.

### ۱۳۳. 🔴 HIGH — TOCTOU بین on_human_judgment و status read
`approval_channel.py:1088-1091` — پس از `on_human_judgment()`، یک `status_of()` جداگانه خوانده می‌شود. تردِ دیگری می‌تواند status را بین write و read تغییر دهد → double-settle یا miss.

### ۱۳۴. 🔴 HIGH — وضعیت APPROVING گیر می‌کند
`approval_channel.py:1069-1076` — `APPROVING` durably نوشته می‌شود ولی به gate atomic بسته نیست. اگر crash بین `persist("APPROVING")` و `settle()` رخ دهد، کارت برای همیشه در APPROVING گیر می‌کند. **هیچ timeout-reconciliation نیست.**

### ۱۳۵. 🔴 HIGH — wall clock برای expiry (نقض TINV-5)
`pending_card_recovery.py:72` — `_now()` از `time.time()` استفاده می‌کند. پرشِ به‌عقبِ clock → کارت‌های منقضی دوباره معتبر. پرشِ به‌جلو → کارت‌های معتبر بی‌صدا منقضی. باید HLC یا monotonic.

### ۱۳۶. 🔴 HIGH — ماشینِ وضعیت بدون whitelistِ transition
`pending_card_recovery.py:542` — `persist_money_decision()` هر transition را می‌پذیرد: `APPROVED→APPROVING`، `DENIED→APPROVED` هر دو مجازند.

### ۱۳۷. 🔴 HIGH — ۴۰۹ ادامه می‌دهد به consume کردن
`approval_channel.py:419-423` — تشخیصِ ۴۰۹ فقط alert با throttle ۱ساعته‌ست. poller به consume کردن ادامه می‌دهد → callbackها بی‌صدا توسط consumerِ رقیب بلعیده می‌شوند. باید cooldown یا self-terminate.

### ۱۳۸. 🔴 HIGH — `autonomy_matrix.is_important()` فقط فیلدهای top-level
`autonomy_matrix.py:47-59` — فقط `title`/`action`/`suggested_action` را regex می‌کند. یک proposal با `{"title":"update config","params":{"amount_aud":5000}}` به‌عنوان "free" طبقه‌بندی می‌شود → autonomous.

### ۱۳۹. 🔴 HIGH — الگوی secret ناقص
`cockpit_readmodel.py:509` — `contains_secret()` فقط token/sk-/PEM/HEX64 را می‌شناسد. AWS `AKIA...`، JWT `eyJ...`، connection stringها را نمی‌گیرد.

### ۱۴۰. 🟠 MED — `_new_token()` race روی counter
`approval_channel.py:640-648` — counter خارج از lock خوانده/استفاده می‌شود. دو فراخوانیِ سریع برای effect_id یکسان → token یکسان.

### ۱۴۱. 🟠 MED — `prop` scheme از owner-gate مستثنی
`approval_channel.py:768-781` — `_MUTATING_CALLBACK_SCHEMES` شامل `prop` نیست. ولی `prop` state-mutating است (رأی‌گیری).

### ۱۴۲. 🟠 MED — quarantine بدون redact ذخیره می‌شود
`approval_channel.py:482-487` — متنِ خام (تا ۱۰۰۰ کاراکتر) بدون redact در `_quarantine` ذخیره می‌شود. اگر نمایش داده شود → نشت.

### ۱۴۳. 🟠 MED — quarantine بدون bound (OOM)
`approval_channel.py:300` — `_quarantine` یک `list[dict]` بدون bound. هر پیام یک ورودی. حجمِ پایدار → OOM.

### ۱۴۴. 🟠 MED — `_new_act_token` فقط RAM
`approval_channel.py:2886` — act tokenها فقط در `_pending_act`. restart → همهٔ دکمه‌های act مرده. (برخلاف money cardها که durable‌اند.)

### ۱۴۵. 🟠 MED — lock غیراتمیک روی ویندوز
`pending_card_recovery.py:180-220` — `O_CREAT|O_EXCL` روی ویندوز واقعاً atomic نیست. پنجرهٔ stale-reclaim ۳۰s → دو پروسه می‌توانند همزمان lock را داشته باشند.

### ۱۴۶. 🟡 LOW — `_save_offset` بدون fsync
`approval_channel.py:4309-4321` — `OSError` بی‌صدا بلعیده، fsync نیست. قطع برق → offset خراب یا duplicate processing.

### ۱۴۷. 🟡 LOW — token money فقط ۶۴ بیت
`pending_card_recovery.py:106` — HMAC به ۱۶ hex (۶۴ بیت) trunc. کافی ولی ضعیف‌تر از callback token ۹۶ بیتی.

### ۱۴۸. 🟡 LOW — `_load_store` corrupted → {} بی‌صدا
`pending_card_recovery.py:139-147` — اگر `pending-cards.json` خراب باشد، {} برمی‌گردد → **همهٔ کارت‌های pending پول ناپدید می‌شوند** بدون alert.

### ۱۴۹. 🟡 LOW — redact برای HEX64 partial
`cockpit_readmodel.py:515-520` — فقط خود hex را replace می‌کند، context اطراف (`password=...`) باقی می‌ماند.

### ۱۵۰. 🟡 LOW — `tg_send_log` در bare except
`approval_channel.py:1443-1448` — خطای record کردنِ log بی‌صدا بلعیده → "measurement is on" غیرقابلِ ممیزی.

### ۱۵۱–۱۵۵. (جزئیاتِ تخصصیِ امنیتی — `langar_bridge` owner-ID leak، TOCTOU و غیره — در فایل مرجع.)

---

## بخش ۲ — مغزِ سمتِ PF (۱۵۶–۱۸۰) — یافتهٔ بازنویسی‌کننده

### یافتهٔ کلیدی: مغز وصل است ولی گرسنه‌ست

| سوال | پاسخِ قطعی از رویِ کد |
|---|---|
| آیا مغزِ PF سرگردان است؟ | ❌ نه. به orchestrator + langar_bot + pf_admin + pf_os وصله. |
| آیا ThompsonBandit واقعیه؟ | ✅ بله. Beta-Bernoulli با recency decay، exploration governance، min-pull، approval gating، atomic persist. |
| آیا reward loop بسته‌ست؟ | ⚠️ **معماری بسته، ولی صفر observation.** مسیر: select→post→feedback_loop→observe→posterior تماماً وصله. |
| آیا BCM می‌تونه ازش یاد بگیره؟ | ❌ هیچ پلی بین `brain/learning.py` و `_ops/neural/bcm.py` نیست. |
| وضعیت state files؟ | **همه خالی/مفقود**: bandit_state.json، acquisition_memory.json، fan_db.json، kpi.json، link_state.json، ab_tests.json. |

### ۱۵۶. 🔴 HIGH — ThompsonBandit صفر observation
`brain/learning.py:70` — `bandit_state.json` وجود ندارد. یادگیرندهٔ واقعی، بدون داده.

### ۱۵۷. 🔴 HIGH — پلِ PF-brain ↔ octopus-BCM وجود ندارد
`brain/learning.py:104` ↔ `_ops/neural/bcm.py` — هیچ مسیر کد. خروجیِ `posterior()` می‌توانست BCM را بیدار کند، ولی وصله نیست.

### ۱۵۸. 🟠 MED — `hebb_orch.json` نویسنده ندارد
`brain/hebb_orch.json` — orchestrator آن را **می‌خواند** ولی هیچ کد در کلِ repo به آن **نمی‌نویسد**. ۴ جفت saturated手动اً یک‌بار نوشته شده، اکنون یتیم.

### ۱۵۹. 🟠 MED — A/B tracker آماری نامعتبر
`brain/ab_tracker.py:63-81` — «significance» = تفاوتِ نسبی ≥۱۵٪. بدون t-test، بدون sample size، بدون peeking protection.

### ۱۶۰. 🟠 MED — A/B از bandit جدا
`brain/ab_tracker.py` — import نمی‌کند `learning.py`. outcomeهای A/B در انزوا می‌میرند.

### ۱۶۱. 🟠 MED — نرمال‌سازیِ ناسازگار
`acquisition.py:128` (linear cap) vs `learning.py:49` (tanh). heuristic و bandit روی scaleهای ناسازگار.

### ۱۶۲. 🟠 MED — `process_all` به sub-agentها arg نمی‌دهد
`dual_brain_v3.py:252,258` — `pricer()` بدون arg صدا زده، `content_optimizer(None)`. منطقِ تطبیقی هرگز فعال نمی‌شود.

### ۱۶۳. 🟠 MED — ۱۰ sub-agent: ۰ واقعی، ۴ نیمه‌واقعی، ۶ stub
`dual_brain_v3.py` — Strategist/Pricer/Scheduler/RiskAnalyzer/Segmenter/TrendForecaster/RetentionStrategist/ContentOptimizer/FunnelAnalyst/CompetitorIntel. اکثراً hardcoded.

### ۱۶۴. 🟠 MED — `archive.json` ادعاهای یادگیریِ جعلی
`project_f_brain.py:219` — `learned=(outcome in ("approved","published"))` فارغ از metric. ۲ ورودی با metric_before=after=0 ولی `learned=true`.

### ۱۶۵. 🟠 MED — storeها بدون threading lock
`brain/store.py:52-60` — فقط `acquisition_pipeline.py` RLock دارد. بقیه (bandit، tracker، lifecycle، archive) بدون lock.

### ۱۶۶. 🟡 LOW — Pricer از خریدهای واقعی feedback نمی‌گیرد
`dual_brain_v3.py:100-114` — `_pricing_history` فقط قیمت‌های تأییدشده، نه فروش واقعی.

### ۱۶۷. 🟡 LOW — `ContentEngine` seed ثابت `random.Random(42)`
`content_engine.py:47` — همان ۱۰ ایده هر بار.

### ۱۶۸–۱۸۰. (جزئیاتِ مغز — duplicate brain، KPI dedup، lifecycle trivial، و غیره.)

---

## بخش ۳ — پاها + ژنوم (۱۸۱–۱۹۶) — حلقهٔ ژنوم قطع است

### پاسخِ قطعی: genome→behavior loop در ۴ نقطه قطع

```
lesson → [genome entry] → [READ by decision] → behavior change
            ↑ قطع ۱           ↑ قطع ۲و۳          ↑ قطع ۴
```

| نقطهٔ قطع | جایی که می‌شکند |
|---|---|
| ۱ — formalize شدن | ۹۹.۴٪ NOTE، صفر APPLY، صفر GENOME_CHANGE، فقط ۶ PROPOSAL |
| ۲ — خوانده شدن | doctor فقط METRIC/PROPOSAL می‌خواند (۱۰ از ۲۱۷۴)؛ NOTEها را نادیده |
| ۳ — ارگانیسم می‌خواند | `_ops/` **هرگز** `values.yaml`/`Genome.load()` را import نمی‌کند |
| ۴ — رفتار تغییر | `human_two_key_for_genome` فقط مستنده، کد ندارد |

### ۱۸۱. 🔴 HIGH — `ledger_core.py` ۴۹۵ خطِ production با صفر caller
`_ops/legs/ledger_core.py:350` — double-entry کامل (GST guard، period lock، idempotency، trial balance، reversal). **هیچ‌کس صدا نمی‌زند.** داراییِ پنهان.

### ۱۸۲. 🔴 HIGH — `ps_writeback.py` می‌تواند POST کند پشتِ flagِ read-only
`OCTOPUS_WIRE_POCKETSMITH` هم GET و هم POST را gate می‌کند. قرارداد «read-only» نقض می‌شود. فیکس: flag را split کن.

### ۱۸۳. 🔴 HIGH — verify failureِ ledger non-blocking
`brain_worker.py:251-256` — اگر hash chain بشکند، فقط alert. ارگانیسم به tick ادامه می‌دهد. audit trail فاسد نادیده گرفته می‌شود.

### ۱۸۴. 🔴 HIGH — Doctor ژنوم ۹۹.۴٪ داده را نادیده می‌گیرد
`genome-system/agents/doctor.py:31-33` — فقط METRIC+PROPOSAL (۱۰ از ۲۱۷۴). NOTEها (ORGANISM_DAILY، EXPERIENCE) هرگز ارزیابی نمی‌شوند.

### ۱۸۵. 🔴 HIGH — `_ops/` هرگز `values.yaml` را نمی‌خواند
۱۰ اصلِ invariant (approve_first، propose_only_agents، evaluator_in_genome، genome_not_self_modifiable) **تزئینی‌اند**. ارگانیسم invariants خودش را hardcoded دارد.

### ۱۸۶. 🔴 HIGH — `human_two_key_for_genome` فقط مستند
`genome_change_protocol.md` ۷۲h cooldown + two-key را توصیف می‌کند. **کد ندارد.** guardian.py timer/تأیید را پیاده نمی‌کند.

### ۱۸۷. 🟠 MED — scheduler dispatch spam در ledger
tailِ ledger: ۱۰ ورودیِ تکراریِ `SCHEDULER_DISPATCH/rfc-followup` برای `RFC-886f7fac` هر ~۶۰s. ~۱۴۴۰ ورودی/روز نویز. verify را کند و signal را رقیق.

### ۱۸۸. 🟠 MED — ziman_leg `incubating` بی‌صدا
`leg.py:148` — اگر `ZIMAN` در budgets.yaml نباشد، money_link=incubating، هرگز reserve. **بدون alert.** degrade خاموش.

### ۱۸۹. 🟠 MED — grammarِ flag ناسازگار
`outbound_worker.py:31` (`=="1"`) vs `pocketsmith_api.py:57` (`in {"1","true","yes","on"}`). `OCTOPUS_WIRE_LEAD_OUTBOUND=true` arm نمی‌کند ولی PocketSmith را arm می‌کند. footgun.

### ۱۹۰. 🟠 MED — ziman proposals از spine غایب
`ziman_leg.py:569-579` — `spine_adapters` lazy import، fail-soft. اگر import fail → proposals در audit spine ناپدید.

### ۱۹۱. 🟠 MED — `_effectively_reversed` بدون cycle detection
`ledger_core.py:291-300` — عمق ۳۲، اگر J1↔J2 همدیگر را reverse کنند، هر دو "effectively reversed" → هر دو settle، نه قابلِ reversal. خطای منطق.

### ۱۹۲. 🟡 LOW — `brain_worker.py` پشتِ flagِ default-off
`brain_worker.py:50-54` — `OCTOPUS_WIRE_TICK_WORKERS` خاموش. ۶۲۱ خطِ isolation layer (per-organ try/except، circuit-breaker) تولید نمی‌کند.

### ۱۹۳. 🟡 LOW — `langar_bridge` cmd truncate
`langar_bridge.py:89` — `cmd_prefix` به ۲۰ کاراکتر. `/pf_pause_for_review` → `/pf_pause_for_re` مبهم.

### ۱۹۴–۱۹۵. (جزئیات — circular import fragile، redundant I/O در lead gate.)

### ۱۹۶. 🔴 HIGH (متا) — ارکستراسیون مرکزی برای یک ایجنت بیش از حد بزرگ
`organism.py` + `wiring.py` + `live_loop.py` + `chrono.py` + `cardiac.py` با هم از پنجرهٔ context یک ایجنت بزرگ‌ترند. **دو بار سقوط.** این یعنی نقشهٔ کاملِ beat-loop / call-graph هنوز ناکاملِ کشیده‌نشده — خودش یک نقطهٔ کور.

---

## بخش ۴ — ۵ کارِ امروز + ۵ کارِ هفته (به‌روزرسانی‌شده)

### امروز (کم‌ریسک، پر-بازده)
1. **فیکسِ redact() fail-open** (آیتم ۱۳۱) — یک خط. CRIT.
2. **روشن‌کردن `OCTOPUS_HONEST_OUTCOMES`** (از ۱۰۰).
3. **فیکسِ governor router** (از ۱۰۰، آیتم ۱۴).
4. **split flag PocketSmith read/write** (آیتم ۱۸۲) — یک متغیر.
5. **unify flag grammar** (آیتم ۱۸۹) — regex.

### هفته (پر-بازده)
1. **اولین observation واقعی به ThompsonBandit** (آیتم ۱۵۶) — حلقه را می‌بندد.
2. **پلِ bandit→BCM** (آیتم ۱۵۷) — BCM خوابیده را بیدار می‌کند.
3. **state-machine whitelist برای money transitions** (آیتم ۱۳۶).
4. **timeout-reconciliation برای APPROVING** (آیتم ۱۳۴).
5. **wire `ledger_core.py`** (آیتم ۱۸۱) — ۴۹۵ خطِ کتاب‌داریِ از کارافتاده را زنده می‌کند.

---

## بخش ۵ — جمعِ نقاط کور تا کنون

| سند | محدوده | تعداد |
|---|---|---|
| `OCTOPUS-BLINDSPOTS-100.md` | ۱–۱۰۰ | ۱۰۰ |
| `OCTOPUS-BLINDSPOTS-DELTA.md` | ۱۰۱–۱۳۰ (+۷ تصحیح) | ۳۰ |
| `OCTOPUS-BLINDSPOTS-DELTA-2.md` (این) | ۱۳۱–۱۹۶ (+۴ تصحیح) | ۶۶ |
| **جمع** | | **۱۹۶ نقطهٔ کور + ۱۱ تصحیح** |
