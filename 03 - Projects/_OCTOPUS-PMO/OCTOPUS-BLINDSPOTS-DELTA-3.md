# Octopus — نقاط کورِ جدید (DELTA-3: ۱۹۷–۳۲۷)

> اسکنِ تمام‌عیارِ نهایی، ۲۰۲۶-۰۷-۲۷. مکملِ ۱۰۰ + DELTA + DELTA-2.
> هفت ایجنت از رویِ کد خواندند: organism.py، neural، cortex/doctor/governor، telegram hub، wiring/chrono/cardiac، pf_os/langar، data/config/genome، tests/scripts/model_router، cross-cutting.
> هیچ فایلِ اصلیِ زیراسکن‌نرفته نماند. این دور، یافته‌های **بنیادی** داشت.

---

## بخش ۰ — سه یافتهٔ بازنویسی‌کنندهٔ نقشهٔ ذهنی (خلاصهٔ کل اسکن)

### یافتهٔ ۱ — پاسخِ قطعی به «آیا هوش مصنوعیِ واقعیه؟»: **نه.**

مسیرِ efferentِ یگانه از لایهٔ neural به یک تصمیم، `protective_override` است که فقط `pain` و `reflexes` را می‌خواند — و این دو از **thresholdهای ثابت** (نه از وزن‌های آموخته‌شده) محاسبه می‌شوند. `neural_driver.evaluate` هیچ‌گاه `bcm` یا `hebbian` را import نمی‌کند.BCM/Hebbian/consolidation یک **پایانِ فقط‌نوشتنی** هستند. (آیتم ۳۱۰)

### یافتهٔ ۲ — علتِ قطعیِ خالی‌بودن BCM

`bcm.py:153` — حلقهٔ sync-delete وقتی `known_keys` (از `latent_space.keys()` که خالیه) خالی باشه، **همهٔ وزن‌ها را پاک می‌کنه**. علتِ بالادست: `organism.py:749` هیچ‌گاه `acquisition_data`/`doctor_archive` را پاس نمی‌دهد. BCM در هر سیکل پاک و دوباره پاک می‌شه. (آیتم neural ۱۹۷ / ۱۹۸)

### یافتهٔ ۳ — لایهٔ امنیت روی فرض‌هایی ساخته شده که بقیهٔ کد نقضش می‌کنن

- **TINV-5** («هیچ ماژولی wall clock نخواند») به‌عنوان قانون مستنده، ولی ۴ ماژول از ~۵۰ رعایتش می‌کنن. ۲۱۴ `time.time()` در مسیرهای امنیتی. (آیتم ۳۲۰)
- **۵۹۵ نقطهٔ `except: pass` بی‌صدا**، ۵۶ تاش در budget/neural، چندتاش در persist کردنِ verdict پول. (آیتم ۳۱۴)
- **«مالک» سه مفهومِ متفاوت** در سه سطح (bot center / approval channel / center chat). سطحِ پول بیشترین اجازه را دارد. (آیتم ۳۱۲)
- **گرامرِ flag چهار idiom رقیب** دارد: یک flag می‌تونه `on` و `off` همزمان باشه بسته به اینکه کی بخواندش. (آیتم ۳۱۶)

---

## بخش ۱ — ارکستراسیون (organism.py) — ۱۹۷–۲۱۳

| # | Severity | نقطهٔ کور | فیکس |
|---|---|---|---|
| ۱۹۷ | 🔴 CRIT | هیچ signal handler؛ SIGTERM = hard kill، stateِ در‌دست‌رفته | `signal.signal(SIGTERM, _graceful)` + checkpoint |
| ۱۹۸ | 🔴 HIGH | HTTP handler `ORGANISM-STATE.json` را بدون lock می‌خواند، race با نویسنده | LockedJson در handler یا symlink `.latest` |
| ۱۹۹ | 🔴 HIGH | `initiative.speak()` LLM همزمان، tick را block می‌کند | thread daemon مثل self_patch |
| ۲۰۰ | 🔴 HIGH | `deep_think.run()` مغزِ گران، tick را block می‌کند | thread daemon با callback |
| ۲۰۱ | 🔴 HIGH | `heart_wires.beat()` درون daily-block، با وجود designِ «هر N beat» | dedent به سطحِ خواهرِ daily |
| ۲۰۲ | 🟠 MED | `telemetry.snapshot/reconcile` بدون try/except منفرد | wrap در try/except |
| ۲۰۳ | 🟠 MED | `enrich_state_with_germline` بدون try/except | wrap |
| ۲۰۴ | 🟠 MED | ۴ استفاده از `time.time()` برای scheduling، بدون monotonic | `time.monotonic()` برای فاصله‌ها |
| ۲۰۵ | 🟠 MED | `RESTART-REQUESTED` بدون TTL/اعتبارسنجی مالک → restart-loop بی‌نهایت | atomic delete + TTL |
| ۲۰۶ | 🟠 MED | `merge_prev=True` کلیدهای stale را نگه می‌دارد | exclude list گسترش یابد |
| ۲۰۷ | 🟡 LOW | heartbeat اولین tick همیشه (init 0.0) | init `time.time()` |
| ۲۰۸ | 🟡 LOW | code sidecar chrono.py را capture نمی‌کند | اضافه به `_KEY_MODULES` |
| ۲۰۹–۲۱۳ | 🟡 LOW | daily string-compare، cardiac floor، last_daily validation، wiring monolithic | جزئیات |

## بخش ۲ — neural/حافظه — ۲۱۴–۲۳۱ (یافتهٔ بحرانی)

| # | Severity | نقطهٔ کور | فیکس |
|---|---|---|---|
| ۲۱۴ | 🔴 CRIT | **BCM sync-delete همهٔ وزن‌ها وقتی latent_space خالیه** (`bcm.py:153`) — علتِ قطعیِ خالی‌بودن | `if known:` guard قبل از sync-delete |
| ۲۱۵ | 🔴 HIGH | `organism.py:749` هیچ‌گاه acquisition_data/doctor_archive پاس نمی‌دهد | پاس داده‌های واقعی |
| ۲۱۶ | 🔴 HIGH | neural_beat consolidation path همیشه acquisition خالی | حذف dead path یا inject |
| ۲۱۷ | 🔴 HIGH | `OCTOPUS_WIRE_BCM_FEED` در PAPER_FULL_FLAGS نیست → فیکسِ BCM default-off | اضافه به flags |
| ۲۱۸ | 🟠 MED | Hebbian rich-mode ≥۲ انحراف همزمان لازم، ولی انحراف‌ها mutually-exclusive | threshold ≥۱ یا baseline_normal |
| ۲۱۹ | 🟠 MED | latent_space encoder = SHA-256 hash projection، نه embedding معنایی | مدل real یا مستندسازی stub |
| ۲۲۰ | 🟠 MED | دو مسیر consolidation (هر ۱۰ beat / هر ۷۲۰ beat) با sourceهای متفاوت، counter مشترک | حذف مسیر مرده |
| ۲۲۱ | 🟠 MED | sensory_bus PII = substring ساده، encoded/obfuscated را از دست می‌دهد | regex + word boundary |
| ۲۲۲ | 🟡 LOW | SprintRunner بدون timeout wall-clock | `max_wall_seconds` |
| ۲۲۳ | 🟡 LOW | HookBus خطاها برای همیشه در RAM انباشته | cap deque |
| ۲۲۴ | 🟡 LOW | nociceptor وزن‌های ثابت بدون calibration | env-vars یا adaptive |
| ۲۲۵ | 🟡 LOW | ReflexArc `is_effect: False` hardcode روی همه | type-based |
| ۲۲۶–۲۳۱ | 🟡 LOW | جزئیاتِ neural | — |

## بخش ۳ — cortex/doctor/governor — ۲۳۲–۲۴۶

| # | Severity | نقطهٔ کور | فیکس |
|---|---|---|---|
| ۲۳۲ | 🔴 HIGH | **حلقهٔ خودبهبودی OPEN** در ۳ نقطه: apply انسانی، outcomes صفر، feedback صفر | روشن‌کردن OCTOPUS_HONEST_OUTCOMES |
| ۲۳۳ | 🔴 HIGH | **اولین spawn: fitness.authoritative سخت‌ترین blocker (~۴ هفته قفل)** | verdict مالک برای رفع قفل |
| ۲۳۴ | 🟠 MED | governor fiks شده caller-specific ولی `extract_json` هنوز fence-stripping ندارد | فیکس سیستمیک |
| ۲۳۵ | 🟠 MED | debate stub متن canned مستقل از موضوع | budget بالاتر یا مغز گران |
| ۲۳۶ | 🟠 MED | doctor ۲۰۲۶-۰۷-۲۶: ۴ نقص واقعی، هیچ‌کدوم code change (agent mislabeling) | — |
| ۲۳۷–۲۴۶ | 🟠/🟡 | rules_store closed-loop، self_patch allowlist، deep_think propose-only | جزئیات |

## بخش ۴ — telegram hub/امنیت — ۲۴۷–۲۶۶

| # | Severity | نقطهٔ کور | فیکس |
|---|---|---|---|
| ۲۴۷ | 🔴 HIGH | `ap:detail` عنوان job را بدون HTML escape رندر می‌کند (XSS-like) | `_html.escape` |
| ۲۴۸ | 🔴 HIGH | expiry callback-token روی wall-clock (parity با #۳۱۳) | `time.monotonic()` |
| ۲۴۹ | 🔴 HIGH | mission_runner test subprocess کل env شامل secretها را به ارث می‌برد | env whitelist scrub |
| ۲۵۰ | 🔴 HIGH | `action_hash` fail-soft به `""` → bind محتوا بی‌صدا drop | fail-closed در mint |
| ۲۵۱ | 🟠 MED | single-writer approval_store بدون automated enforcement | file-lock یا grep CI |
| ۲۵۲ | 🟠 MED | سه‌لایه scrub semantic ناسازگار (line/string/char) | یک تابع مشترک |
| ۲۵۳ | 🟠 MED | mission_runner artifacts به live vault root نوشته می‌شود | under worktree |
| ۲۵۴ | 🟠 MED | flag grammar ناسازگار (`== "1"` vs set) | `opslib.flag_on()` یکپارچه |
| ۲۵۵ | 🟠 MED | event_bridge dedup قبل از send success ثبت می‌شود | بعد از send |
| ۲۵۶ | 🟠 MED | autonomy_matrix فیلدهای nested را نمی‌بیند ( گسترش #۱۳۸) | flatten بازگشتی |
| ۲۵۷–۲۶۶ | 🟡 LOW | tg_api fallback 409، _mint_ha_token no-op، mirror topic drift، audit JSONL بدون lock، heartbeat jitter، _scrub false-positive | جزئیات |

## بخش ۵ — wiring/chrono/cardiac — ۲۶۷–۲۸۰

| # | Severity | نقطهٔ کور | فیکس |
|---|---|---|---|
| ۲۶۷ | 🟠 MED | **HLC بدون max-drift bound؛ `c` بعد از backward clock jump بی‌نهایت رشد می‌کند** | `max_drift_ms` + alert |
| ۲۶۸ | 🟠 MED | `restart_from_known_good` HLC leg را به GENESIS `(0,0)` reset می‌کند | `hlc_tick(GENESIS, now)` |
| ۲۶۹ | 🟠 MED | `organism.py:627` هر epoch یک ChronoDB جدید باز می‌کند، هرگز نمی‌بندد (FD leak) | reuse یا `.close()` |
| ۲۷۰ | 🟠 MED | chrono.db WAL بدون checkpoint policy، رشد بی‌نهایت | `wal_checkpoint(TRUNCATE)` دوره‌ای |
| ۲۷۱ | 🔴 HIGH | **`beat_seq` اگر chrono.db خالی/خراب باشه بی‌صدا از ۱ ری‌استارت** | fail-closed یا restore |
| ۲۷۲ | 🟠 LOW-MED | LiveLoop collectionها بدون lock، فقط GIL | `threading.RLock` |
| ۲۷۳ | 🟡 LOW | **`saba-bridge.jsonl` dead letterbox — pf_os می‌نویسد، octopus هیچ‌وقت نمی‌خواند** | یک خط در organism.py |
| ۲۷۴ | 🟡 LOW | cartographer_beat روی bus ثبت نیست (no HLC/ack/leg_clock) | register LegHandle |
| ۲۷۵ | 🟠 MED | **هیچ cross-verify بین chrono.db checkpoint و genome ledger در boot** | مقایسه ledger_hash |
| ۲۷۶ | 🟠 MED | **arm_gate enforcement default-OFF** (`OCTOPUS_REQUIRE_ARM`) | flip default یا مستندسازی |
| ۲۷۷ | 🟡 LOW | production_wire_open Gate-0 بدون freshness check روی signals file | assert ts |
| ۲۷۸–۲۸۰ | 🟡 LOW | _ZIMAN_STATE/_HEART_STATE restart، effective_period magic 0.6 | جزئیات |

## بخش ۶ — pf_os/langar — ۲۸۱–۲۹۶

| # | Severity | نقطهٔ کور | فیکس |
|---|---|---|---|
| ۲۸۱ | 🔴 HIGH | **bridge write-only** (تأیید #۲۷۳) | یک خط در wiring.py |
| ۲۸۲ | 🟡 LOW | phantom `F:backup/` directories از path-escape bug باقی‌مانده | rm -rf |
| ۲۸۳ | 🟠 MED | EventBus یک-ارگانی (فقط orchestrator publish می‌کند) | spine.emit در ماژول‌های دیگر |
| ۲۸۴ | 🟠 MED | VaultBank seeded ولی `used_count: 0` همه — هرگز مصرف نشده | audit pipeline |
| ۲۸۵ | 🟠 MED | ۴ از ۵ DataSpine store هرگز ساخته نشده‌اند | adoption gap، مستندسازی |
| ۲۸۶ | 🟠 MED | `/api/store` endpoint `snapshot()` صدا می‌زند که وجود ندارد | متد درست |
| ۲۸۷–۲۹۶ | 🟠/🟡 | PII reject list ناسازگار، cortex warmup no-op، _content_free بدون scrub، capabilities persist نشده، saba_link بدون lock، brain.py "arch" over-reject، vault_admin static banned، cortex_client health path، event_bus JSONL بدون lock، bridge_beat unicode، langar bare import، bridge atomic_append، loop draft delta، learning_bus verify | جزئیات |

## بخش ۷ — data/config/genome + tests/scripts/model_router — ۲۹۷–۳۲۶

| # | Severity | نقطهٔ کور | فیکس |
|---|---|---|---|
| ۲۹۷ | 🟠 MED | OCTOPUS-flags.cmd بدون checksum، flag drift بی‌صدا | boot-time check |
| ۲۹۸ | 🟡 LOW | flags.cmd duplicate set statements | lint |
| ۲۹۹ | 🟡 LOW | money_pulse flag اصلاً در flags.cmd نیست | اضافه با کامنت |
| ۳۰۰ | 🟠 MED | sensory_bus فقط ۵ observation type → hardcoded topic IDs | گسترش mapping |
| ۳۰۱ | 🟡 LOW | idea_graph source dirs hardcoded | env config |
| ۳۰۲ | 🟠 MED | **context_fence فقط alert، هیچ‌وقت block نمی‌کند** | `CONTEXT_FENCE_BLOCK=1` flag |
| ۳۰۳ | 🟡 LOW | decision_receipt CoT check فقط top-level | recursive scan |
| ۳۰۴ | 🟡 LOW | flags.cmd mojibake فارسی | بازنویسی انگلیسی |
| ۳۰۵ | 🟠 MED | **watchdog split-brain: دو نسخهٔ divergent organism-watchdog.ps1** | collapse یا assertion |
| ۳۰۶ | 🟡 LOW | sog_math وابسته به `C:\Users\Armin\Desktop\4D\4.py` | env var |
| ۳۰۷ | 🟠 MED | **`run_all.py` فقط ۲۷ تست می‌زند، نه ۳۴۷** — ~۳۲۰ تست هرگز CI | expand یا tier |
| ۳۰۸ | 🟠 MED | held_out_evaluator خودش در canary suite‌اش نیست | meta-recursive |
| ۳۰۹ | 🔴 HIGH | **۳ بات token-sharing 409 risk، بدون runtime guard**؛ START-HERE.bat second-brain همچنان زنده | delete/neuter + boot check |
| ۳۱۰ | (در cross-cutting) | — | — |
| ۳۱۱–۳۲۶ | (در cross-cutting) | — | — |

## بخش ۸ — cross-cutting (نیازمند نگاهِ بین‌ماژولی) — ۳۱۰–۳۲۷

| # | Severity | نقطهٔ کور | فیکس |
|---|---|---|---|
| ۳۱۰ | 🔴 **CRITICAL** | **`protective_override` یگانه efferent neural است و از یادگیری hard-immunized** — ریشهٔ قطعیِ نه‌بودنِ AI واقعی | در `neural_driver.evaluate` وزن‌های BCM/Hebbian را در pain/reflex fold کن |
| ۳۱۱ | 🔴 HIGH | **circuit_breaker cooldown wall-clock → NTP step breaker داغ را re-close می‌کند** | `time.monotonic()` |
| ۳۱۲ | 🔴 HIGH | **مالک سه مفهوم متفاوت؛ سطحِ پول بیشترین اجازه** | `identity.py` یکپارچه |
| ۳۱۳ | 🔴 HIGH | **تمام expiryها wall-clock → backward jump توکن‌های پولِ منقضی را معتبر می‌کند** | monotonic + re-issue در restart |
| ۳۱۴ | 🔴 HIGH | **۵۹۵ `except: pass` بی‌صدا، ۵۶ در budget/neural، چندتا در persist verdict پول** | lint: `except` در `_ops/budget/` باید alert کند |
| ۳۱۵ | 🔴 HIGH | **Hebbian/BCM in-memory state از چند thread بدون lock** | یک Lock در هر ماژول |
| ۳۱۶ | 🔴 HIGH | **flag grammar ۴ idiom رقیب؛ یک flag همزمان on و off** | یک `opslib.flag()` |
| ۳۱۷ | 🟠 MED | approval_state_machine/approval_queue_unified orphan ولی test-referenced → false safety | delete یا wire |
| ۳۱۸ | 🟠 MED | agent_gateway_http/lead_boundary_http `_RATE` module-global بدون lock از HTTP multithreaded | Lock per `_RATE` |
| ۳۱۹ | 🟠 MED | `opslib.append_jsonl` بدون fsync ولی hash-chain و reserve→settle به durability وابسته‌اند | flush+fsync |
| ۳۲۰ | 🟠 MED | TINV-5 قانون مستنده، ۴ ماژول رعایتش می‌کنن | lint grep CI |
| ۳۲۱ | 🟠 MED | chord/repair_policy هر beat اجرا می‌شه ولی هیچ repair واقعی تغذیه نمی‌کنه | wire به self_patch یا shadow-only |
| ۳۲۲ | 🟠 MED | هر subprocess/.bat کل env با secretها را به ارث می‌برد، هیچ `env=` scrub نیست | `opslib.scrubbed_env()` |
| ۳۲۳ | 🟠 MED | signal_hub._HUB module-global بین leg و neural_driver بدون lock | thread-safe SignalHub |
| ۳۲۴ | 🟠 MED | local_llm available() با ۴s timeout flap می‌کند → theatre-while-success | retry + fail-closed |
| ۳۲۵ | 🟠 MED | `git worktree add --detach HEAD` فرض می‌کنه HEAD سبزه، هیچ‌وقت نیست | baseline.json |
| ۳۲۶ | 🟡 LOW | blackbox_map/ingest_raw مسیرهای `F:\` hardcoded | `opslib.ORG_ROOT` |
| ۳۲۷ | 🟡 LOW | event_bus/unified_bus در-process؛ host دوم غیرممکن | transport seam |

---

## بخش ۹ — پاسخِ نهایی به سوالِ مالک

### چه مانعِ اصلیِ «هوشِ مصنوعیِ واقعی» بودن است؟

**آیتم ۳۱۰.** لایهٔ neural ساختاراً از تصمیم‌ها **unplugged** است. یگانه مسیرِ خروجی (`protective_override`) فقط `pain`/`reflexes` را از thresholdهای ثابت می‌خواند — نه از وزن‌های آموخته‌شدهٔ BCM/Hebbian. یعنی حتی اگر BCM را غذا بدهی و Hebbian را پر کنی، **هیچ تصمیمی عوض نمی‌شود.** این ریشه‌ست، نه BCM خالی (آن فقط نشسته). **یک import + یک read در `neural_driver.evaluate`** حلقه را می‌بندد.

### چگونه از تولیدِ مثل امروز استفاده کنیم؟

**آیتم ۲۳۳.** اولین spawn واقعی امروز ممکن نیست چون `fitness.authoritative` ~۴ هفته‌ست قفل. مسیر:
1. مالک verdict بدهد تا قفلِ verdict جلسهٔ ۱۶ برداشته شه.
2. ۵ قضاوتِ انسانی روی یک رفتار قابل‌تکثیر جمع شه (acceptance≥۴۰%).
3. alertها پاک شه، live gate باز شه.
4. `replication.py` proposal برای spawnِ دومین lead_scorer با params متفاوت emit کنه.

### چگونه آموزشش دهیم؟

1. هر verdict تلگرام → ردیف `(input, decision, label)` در `outcomes.jsonl`. (امروز: ۲۳۰ ردیف، صفر outcome.)
2. `OCTOPUS_HONEST_OUTCOMES` روشن → improvement_rate صادقانه (حتی اگه →۰).
3. **بستنِ آیتم ۳۱۰**: وزن‌های BCM در تصمیم واقعی اثر بگذارند.
4. ThompsonBandit سمتِ PF (یادگیرندهٔ واقعی) را با outcome واقعی تغذیه کن (امروز صفر observation).
5. distillation: جواب‌های Claude → qwen.

### چگونه باهوش‌ترش کنیم (۵ فیکسِ پر-بازده)?

1. **آیتم ۳۱۰** — plug neural به تصمیم (یک import). ریشه.
2. **آیتم ۲۱۴** — guard BCM sync-delete (یک خط). BCM شروع به یادگیری می‌کنه.
3. **آیتم ۲۱۵** — پاسِ acquisition_data واقعی به consolidation (یک خط).
4. **آیتم ۳۱۶** — یک `opslib.flag()` یکپارچه (flag drift متوقف).
5. **آیتم ۲۳۲** — روشن‌کردن `OCTOPUS_HONEST_OUTCOMES` (یک flag).

### چگونه روی هوشِ مصنوعیِ دیگر سوارش کنیم؟

**آیتم ۳۲۷.** event_bus در-process است. برای host کردن روی ماشین/مدل دیگر:
1. `transport` seam به `unified_bus` اضافه کن (network جای in-process).
2. host-brain seam واحد `ask_brain(difficulty, prompt)` (آیتم ۸۳–۸۹ از ۱۰۰).
3. parity shadow را از ۰ به >۰ ببر (`brain_core`).

---

## بخش ۱۰ — ۵ کارِ امروز + ۵ کارِ هفته (نهایی)

### امروز (P0 — کم‌ریسک، پر-بازده)
1. **فیکس BCM sync-delete** (آیتم ۲۱۴) — یک خط `if known:`. CRIT، ریشهٔ خالی‌بودن.
2. **فیکس redact() fail-open** (آیتم ۱۳۱ از DELTA-2) — یک خط. CRIT امنیتی.
3. **روشن‌کردن `OCTOPUS_HONEST_OUTCOMES`** — یک flag.
4. **فیکس governor router** (آیتم ۱۴ از ۱۰۰) — strip fences.
5. **unify flag grammar** (آیتم ۳۱۶) — یک helper.

### هفته (P1 — پر-بازده)
1. **plug neural به تصمیم** (آیتم ۳۱۰) — یک import. **ریشهٔ AI بودن.**
2. **پاسِ acquisition_data به consolidation** (آیتم ۲۱۵) — یک خط.
3. **اولین observation واقعی به ThompsonBandit** (آیتم ۱۵۶ از DELTA-2).
4. **state-machine whitelist برای money transitions** (آیتم ۱۳۶ از DELTA-2).
5. **wire `ledger_core.py`** (آیتم ۱۸۱ از DELTA-2) — ۴۹۵ خطِ زنده.

---

## بخش ۱۱ — جمعِ نقاط کور تا کنون

| سند | محدوده | تعداد |
|---|---|---|
| `OCTOPUS-BLINDSPOTS-100.md` | ۱–۱۰۰ | ۱۰۰ |
| `OCTOPUS-BLINDSPOTS-DELTA.md` | ۱۰۱–۱۳۰ | ۳۰ |
| `OCTOPUS-BLINDSPOTS-DELTA-2.md` | ۱۳۱–۱۹۶ | ۶۶ |
| `OCTOPUS-BLINDSPOTS-DELTA-3.md` (این) | ۱۹۷–۳۲۷ | ۱۳۱ |
| **جمع** | | **۳۲۷ نقطهٔ کور** |

**پوشش اسکن:** organism.py، neural/، cortex/، doctor/، governor، debate، replication، telegram_center/، approval_channel.py، wiring.py، chrono.py، cardiac.py، heart/، pf_os/، langar/، brain/ (PF)، genome-system/، outcomes/، afferent/، tests/، scripts/بات‌ها، model_router، event_bus، cross-cutting. **هیچ فایلِ اصلیِ زیراسکن‌نرفته نماند.**
