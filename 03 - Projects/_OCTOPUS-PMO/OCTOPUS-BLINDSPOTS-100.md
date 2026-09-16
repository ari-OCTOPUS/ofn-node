# Octopus — ۱۰۰ نقطهٔ کور (Blindspots-100)

> اسکن کامل سیستم توسط ۴ ایجنت اکتشافی، ۲۰۲۶-۰۷-۲۷.
> هدف: چیزهایی که در اختاپوس فراموش/نیمه‌ساخته/شکسته‌ست و جلوی «واقعی شدن به‌عنوان هوش مصنوعی» رو می‌گیره.
> هر آیتم با `file:line` قابل ردیابی‌ست. این فایل خوراکِ ایجنتای بعدیه.
>
> **تشخیص یک‌خطی:** داربست ایمنی (budget gate، hash-chain، atomic write، fail-closed) از خودِ لایهٔ یادگیری بالغ‌تره. سیستم زنده‌ست (beat 14455) ولی هوش فعالاً خوابیده: BCM صفر کلید، Hebbian یک جفت، governor LLM ۲۴h شکسته، debate روی stub، یک پا تیک‌می‌زنه، تولید مثل σ=۰.

---

## بخش ۰ — خلاصهٔ اجرایی

| محور | وضعیت | شواهد |
|---|---|---|
| Pacemaker / heartbeat | ✅ واقعی | `chrono.db` 14454 ردیف، HLC، WAL |
| budget_gate / organ_gate | ✅ واقعی | `organ-gate-log.jsonl` 1187 ردیف، reserve→settle واقعی |
| lead_scorer / thesis_queue | ✅ واقعی | deterministic، $0، closed-loop |
| C6 falsification | ✅ واقعی | ۵ فرضیه DONE/accepted با verifier |
| BCM (plasticity) | ⚠️ سیم‌کشی但没有غذ change | `bcm-weights.json`: step 65, keys `{}` |
| Hebbian | ⚠️ گرسنه | `hebbian.json`: ۱ جفت، strength 0.132 |
| Consolidation | ⚠️ تحلیل‌رفته | 290+ سیکل، ۳ insight تکراری |
| Governor LLM | ❌ شکسته 24h+ | `extract_json` روی truncated JSON، ۲۲ fail |
| Debate | ❌ بیشتر stub | qwen timeout → canned text |
| Legs | ❌ ۱ از ~۱۰ زنده | فقط lead-naghshi |
| Self-improvement metric | ❌ خودارجاعی | card-movement بشمار = improvement |
| Reproduction | ❌ طراحی‌شده، صفر اجرا | σ=0.0, pre-replication |

---

## بخش ۱ — یادگیری گرسنه‌ست (چرا «هوش مصنوعی واقعی» نیست) — آیتم ۱–۱۳

۱. **BCM خالیه.** `state/bcm-weights.json`: `{"step":65,"beta":0.02,"keys":{}}` — ۶۵ استپ، صفر کلید زنده مونده. ریاضیاتِ anti-saturation روی هیچی کار نمی‌کنه.
۲. **BCM هیچ activationای نمی‌گیره.** `consolidation.py` خروجی `y` رو به `bcm.update` پاس نمی‌ده؛ سیم فقط اسمش سیمه.
۳. **Hebbian پروداکشن ۱ جفت داره.** `hebbian.json`: `errors_high/rhythm_amber`، strength ۰.۱۳۲، ۵ هم‌وقت.
۴. **دایرهٔ واژگانِ Hebbian خیلی کوچیکه.** جمعاً ~۴ جوت کل aprendizaje — نمی‌تونه دنیای واقعی رو نمایش بده.
۵. **Consolidation insight ثابت تکرار میشه.** 290+ سیکل: «بهترین محتوا: asmr (score=50.00)» صدها بار — سنسور داره فایل استاتیک می‌خونه.
۶. **مقادیر awareness مکانیکی می‌چرخن.** 0.02/0.00/0.04/0.08/0.12 در یک الگوی ۳-مرحله‌ای ثابت — یادگیری نیست.
۷. **منابع یادگیری افتادن.** `acquisition` و `doctor_archive` از consolidation حذف شدن؛ الان فقط `school_awareness` باقی‌مونه.
۸. **Phase 2/3/4 خالی.** توی consolidation cycles: `latent_vector`، `bcm_pruned`، `bcm_theta` همگی `null` — سیم‌کشی بدون خوراک.
۹. **هیچ closed-loopی بین insight و action نیست.** consolidation append-only log؛ هیچ‌وقت چک نمیشه که insight به outcome изменила چیزی یا نه.
۱۰. **neural_driver فقط مشاوره‌ست.** `neural_driver.py:62` `advisory_only:true` — کل زیرسیستم عصبی یک سنسور فقط‌خواندنی‌ست که هیچ‌کس بهش عمل نمی‌کنه.
۱۱. **Hebbian هیچ‌وقت پیش‌بینی‌پذیریش تست نمیشه.** fire-together وصله ولی predictiveness هیچ‌وقت اعتبارسنجی نمیشه.
۱۲. **هیچ مسیر teacher/labeled-feedback وجود نداره.** curriculum نیست، reward shaping نیست، training data ingestion نیست.
۱۳. **یادگیری هیچ‌وقت در همون سیکل یک تصمیم واقعی رو تغییر نمیده.** megaprompt اخیر (commit `62f95b0`) دقیقاً همین رو خواسته؛ هنوز loop نشده. این «ریشه» بودنِ کل ادعای AI بودن اینجاست.

## بخش ۲ — مغز / حاکم / مناظره شکسته — آیتم ۱۴–۲۵

۱۴. **Governor LLM router 24h+ شکسته.** `debate/client.py:42-48` `extract_json` روی JSON ناقص/` ``` `-fenced fail می‌کنه؛ ۲۲ fail در `governor-alerts.md`، تقریباً ساعتی.
۱۵. **`extract_json` با `s.rfind("}")`== −1** روی بریس بسته‌نشده raise می‌کنه → fallback "dry".
۱۶. **Governor روی "dry" می‌افته.** تخصیص‌دهندهٔ متابولیک کور شده، بودجهٔ ارگان‌ها بر اساس فشار allocate نمیشه.
۱۷. **Debate local-brain timeout.** qwen2.5:1.5b در 90s (`OCTOPUS_DEBATE_LOCAL_BUDGET_S`) timeout → `_stub_transport` → متن canned فارسی مستقل از موضوع.
۱۸. **۷ رویداد «مغزِ محلی نشد → stub»** — اکثر راند مناظره stub (صادقانه tag شده).
۱۹. **survivors-queue پر از `undecided-after-3-rounds`** stub، بعضی به JP/CN/TH (هذیان چندزبانه).
۲۰. **stub متن مستقل از موضوع برمی‌گردونه** — مناظره تئاتره، انتخاب adversarial نیست.
۲۱. **مغز گرون (Claude/Fugu)** ۱۰ call یکسان/day، 12242 token ورودی، ۳۹–۱۱۶ خروجی — عملاً بیکار.
۲۲. **`c6_producer`/`c6_trigger` صفر LLM call** — موتور falsification از مغزی که به اسمشه استفاده نمی‌کنه.
۲۳. **`deep_think` تازه وصله** (۴ slot/day) — هنوز propose-only card، عمل نمی‌کنه.
۲۴. **`CORTEX_LOCAL_FIRST`** همهٔ secondary رو به یک مدل 1.5B می‌فرسته که نمی‌تونه استدلال کنه.
۲۵. **policy انتخاب مدل نیست.** مغز ارزان/گرون استاتیک انتخاب میشه، نه بر اساس سختی سوال (commit `970601b` فقط شروعِ اصلاح).

## بخش ۳ — پاها / محرک‌ها مرده — آیتم ۲۶–۳۴

۲۶. **فقط lead-naghshi تیک‌می‌زنه.** ۴۵ از ۵۰ beat اخیر `["lead-naghshi"]`، ۵ تاش `[]`.
۲۷. **business_legs** (mining/crypto/accounting/knowledge) همگی `live:false`، >۳۵ روز stale.
۲۸. **ziman-gallery، vault-cartographer** entry وضعیت دارن ولی در `chrono.db` `leg_clock` ثبت نیستن.
۲۹. **«۱۰ ارگان innervated» فقط freshness فایله**، نه پروسهٔ مستقل — cortex فایل می‌بینه، agent نه.
۳۰. **`arm_gate_enforcing:false`، `wire_actuator:false`** — EffectorGate امروز pass-throughه.
۳۱. **کانال‌های whatsapp/email `NotWiredStub`، human-gated** — فقط dashboard (read-only) و telegram (poll) زنده‌ان.
۳۲. **legs `propose_only:true`** — هیچ پایی واقعاً یک عمل business اجرا نمی‌کنه.
۳۳. **reconcile organ stale 93h**، awareness 0.347، note «کهنه (93h)» — watchdog ای خودش stale شده.
۳۴. **`wire_reconcile:false`** در ORGANISM-STATE — حلقهٔ reconcile خاموشه ولی هنوز توی freshness monitorه.

## بخش ۴ — حلقهٔ خودبهبودی ناصادق — آیتم ۳۵–۴۴

۳۵. **`improvement_rate` حرکتِ card رو improvement می‌شماره.** `improve.py:261-292` (خودارجاعی).
۳۶. **`outcomes.jsonl`: 230 ردیف، صفر ردیف با after/result/delta/measured/verdict.**
۳۷. **۸۳ closure روی ۴ کلید؛ ۲۰ جفت (ts,key) هم true هم false** — دادهٔ آموزشی متناقض.
۳۸. **`_close_intents`** (`goal_directed.py:263-275`) روی intent غیر یکتا loop می‌زنه → closure متناقض.
۳۹. **تنها metric متحرک `total_discoveries` بود** — شمارشِ خودکاوی به‌عنوان پیشرفت.
۴۰. **flag `OCTOPUS_HONEST_OUTCOMES` هست ولی خاموشه.** وقتی روشن بشه rate → ~۰ = «موفقیت، نه regression».
۴۱. **Doctor ۲۰۲۶-۰۷-۲۶ ۴ نقص واقعی پیدا کرد** ولی «همه روی card-to-owner تموم شد، هیچ‌کدوم به code change نرسید».
۴۲. **`self_patch` هیچ‌وقت auto-apply نمی‌کنه** — کلیک مالک لازم؛ cap روزانه ۳، allowlist فقط `telegram_center/`+`cortex/`.
۴۳. **Doctor `apply_merge` فقط interactive پس از Telegram** — مسیر auto باریک (knob whitelist) default-offه.
۴۴. **هیچ اندازه‌گیری از اینکه یک lesson رفتار آینده رو تغییر داد یا نه** — حافظه بدون پیامد.

## بخش ۵ — تولید مثل طراحی‌شده ولی بی‌استفاده — آیتم ۴۵–۵۲

۴۵. **`replication-latest.json`: σ_effective 0.0، zone `pre-replication`، `proposals_written:[]`** — هیچ‌وقت spawn نشده.
۴۶. **شرط‌های spawn انباشته:** acceptance≥40%، ≥۵ قضاوت، fitness authoritative، بدون alert، gate زنده، halt/freeze نبودن.
۴۷. **`fitness-latest.json`: `authoritative:false`**، «قفل verdict جلسه ۱۶: ~۴ هفته سایه» — fitness هنوز authoritative نیست.
۴۸. **هیچ سیگنال «چه چیزی clone کنم؟»** — gradient فیtness برای انتخاب رفتار قابل تکثیر نیست.
۴۹. **Germline backupه (3-2-1)، نه تولید مثل** — بقا، نه تکثیر.
۵۰. **هدف σ~1.0 ولی مسیر از 0.0 به 1.0 نیست** — bootstrapping وجود نداره.
۵۱. **`MAX_CELLS=6`، `spawn_depth=1`** — حد خوب، ولی اولین spawn هیچ‌وقت اتفاق نیفتاد.
۵۲. **تولید مثل human-gated طراحی شده** ولی fast-path برای اینکه مالک بگه «آره X رو clone کن» نیست.

## بخش ۶ — حافظه / فساد / شکنندگی — آیتم ۵۳–۶۳

۵۳. **latent_space در صورت فساد بی‌صدا wipe میشه.** `latent_space.py:176` `except: pass → start fresh` — از دست رفتن نامرئی.
۵۴. **فراموشی BCM برگشت‌ناپذیره.** کلید زیر `w_floor=0.05` برای همیشه حذف میشه، restore از consolidation log نیست.
۵۵. **`consolidation.json` append-only، بدون dedup، بدون retract اگر falsified شد** — 290+ سیکل برای همیشه رشد می‌کنه.
۵۶. **JSONL append بدون lock.** `events.py:173`، `rules_store.py:143`، `opslib.append_jsonl` — ریسک interleave همزمان روی Windows.
۵۷. **`rules-ledger.jsonl` hash-chain به ترتیب append وابسته‌ست**؛ نویسنده‌های همزمان می‌تونن `prev_sha256` رو بشکنند.
۵۸. **`organ-gate-log.jsonl` بدون lock append میشه** — lock فقط روی `organ-state.json`ه.
۵۹. **محافظ memory-poisoning دستیه.** (قانون اساسی s7: ۲+ source، ولی monitor خودکار نیست).
۶۰. **بکاپ از bcm-weights/hebbian قبل از هر step نیست** — اگر update بد بیفته، rollback نیست.
۶۱. **`chrono.db` WAL 4.1MB بدون checkpoint** — ریسک اگر پروسه با WAL داغ بمیره.
۶۲. **`self-model.json` 157KB هر beat بازنویسی میشه** — churn؛ اگر وسط write قطع شه، self-model خراب میشه.
۶۳. **brain_core parity `compared:0`** — shadow mode داره هیچی مقایسه نمی‌کنه.

## بخش ۷ — متریک‌ها دروغ می‌گویند — آیتم ۶۴–۷۰

۶۴. **cortex coherence 0.961 / coverage 100% / dead_spots [] «سبز»** در حالی که stress 2461 alert و doctor زرد.
۶۵. **coherence freshnessِ فایل رو می‌سنجنه، نه سلامت عملکردی** — گمراه‌کننده اگر به‌عنوان «ارگانیسم سالم» خونده بشه.
۶۶. **`audit-matrix` `static_by_construction:true`** — ۱۷/۴۳ آیتم هرگز Done نمیشن؛ ceiling 75.6%، نه signal.
۶۷. **«owner autonomy preference» status Missing** — panel OWNER-PROFILE می‌خونه ولی export/cockpit نه، رفتار hard-code.
۶۸. **شمارنده step BCM بدون کلید بالا میره** — فعالیت ≠ یادگیری.
۶۹. **`beat_seq` بالا میره (14455) در حالی که ارگان‌ها خوابن** — uptime ≠ agency.
۷۰. **هیچ metric برون‌زایی (exogenous) وجود نداره** — هیچی اثر روی دنیای واقعی (lead بسته، پول، bug fix) نمی‌سنجد.

## بخش ۸ — همزمانی / اتمیسیتی — آیتم ۷۱–۷۵

۷۱. **`observe()` در hebbian thread-safe نیست** — beat همزمان می‌تونه increment هم‌وقت رو drop کنه.
۷۲. **lock سراسری برای نوشتن در سراسر ارگانیسم نیست** — هر ماژول lock خودش.
۷۳. **`organ_gate` reserve/settle روی دو فایل تراکنشی نیست** — crash بینش = reserve درزکرده.
۷۴. **stale-lock break در 30s** (`opslib.py:241-255`) — نویسندهٔ کند می‌تونه lockش وسط write دزدیده بشه.
۷۵. **fsync روی JSONL نیست** — داده در OS buffer هنگام قطع برق از بین میره.

## بخش ۹ — آموزش‌پذیری مفقود — آیتم ۷۶–۸۲

۷۶. **مسیر ingestion دانش خارجی به لایهٔ عصبی نیست** — genome/second-brين ارجاع داده شدن ولی به learning خوراک داده نشدن.
۷۷. **curriculum / صعود از ساده به سخت نیست** — deep_think ۴ slot flat.
۷۸. **UI labeling human-in-the-loop نیست** — verdict از طریق Telegram ad-hoc میاد، نه آموزش ساختاریافته.
۷۹. **replay buffer نیست** — نمی‌شه beat گذشته رو تمرین/دوباره-consolidate کرد.
۸۰. **distillation از مغز گرون به مغز محلی نیست** — جواب‌های Claude به qwen آموزش نمیده.
۸۱. **hook fine-tuning نیست** — وزن‌ها rule-based، هیچ‌وقت gradient آپدیت نمیشن.
۸۲. **حالت «student/teacher» با وجود infra تولید مثل نیست** — clone curriculum برای آموزش داده شدن نداره.

## بخش ۱۰ — سوار کردن روی هوش مصنوعی دیگر — آیتم ۸۳–۸۹

۸۳. **API surface / SDK تمیز نیست** — ارگانیسم یک درهم‌تنیدگی filesystem+script، نه service قابل فراخوانی.
۸۴. **`event_bus` in-processه** (`octopus_core/event_bus.py`) — پروتکل شبکه‌ای برای host کردن جای دیگه نیست.
۸۵. **`bridge.py` به transport تلگرام coupling داره** — model-agnostic نیست.
۸۶. **abstraction «host brain» نیست** — LLM به clientهای خاص hard-code، نه swappable-per-call.
۸۷. **`brain_core_db` mode HARNESS، parity 0** — پل به مغز خارجی وصله ولی هیچی مقایسه نمی‌کنه.
۸۸. **contract نسخه‌دار بین ارگانیسم و مدل host نیست** — نمی‌شه با امنیت به GPT/Gemini/local وصله.
۸۹. **`saba_link` به vendor خاص coupling داره** — seam عمومی «هر LLM رو بپرس» نیست.

## بخش ۱۱ — رصد / کوری — آیتم ۹۰–۱۰۰

۹۰. **flags.cmd armed-but-not-loaded** (فرضیهٔ C6 قبلاً پیدا کرد) — flagهای mid-run تا restart اعمال نمیشن.
۹۱. **`STOP-FUGU.cleared` + فایل صفر‌بایتی `state$db` سرگردان** — markerهای بدون مالک.
۹۲. **`governor-alerts` 2461 خط، rollup نه** — signal زیر نویز مدفونه.
۹۳. **تفاضل بین «wired» و «fed» نیست** — `wire_bcm:true` ولی `keys:{}`؛ flag دربارهٔ live بودن دروغ میگن.
۹۴. **PROJECT_F deadline -7d، اولویت صفر، unresolved** — هدف گیرکرده بدون اقدام مالک.
۹۵. **circuit-breaker thrash:** ۳ restart/300s throttled (lead-naghshi) — self-heal restart-looping.
۹۶. **قلب 19h/day خوابید تا cap 288→2000 شد** — bug کانفیگ که به‌جای «انرژی پایین» جا زده.
۹۷. **alert روی «نرخ fallback به stub» نیست** — سیستم می‌تونه کاملاً روی stub کار کنه و سبز بمونه.
۹۸. **alert وقتی source دادهٔ ارگان به صفر میفته نیست** (acquisition/doctor_archive بی‌صدا افتادن).
۹۹. **`HEARTBEAT.md` 415 خط/81KB dump تکراری** — نویز، نه signal.
۱۰۰. **consolidation «I1 — never touched» by design** — حافظهٔ مرکزی write-only و هیچ‌وقت reconcile نمیشه.

---

## بخش ۱۲ — ایده‌های اجرایی (چطور امروز ازش استفاده کنیم)

### ۱۲.الف — تولید مثل را همین امروز استفاده کن (اولین spawn واقعی)

σ=0 و pre-replication. برای اولین spawn واقعی، **نه کل ارگانیسم رو clone کن، یک رفتار/پا رو.** سریع‌ترین مسیر امن:

1. **`lead_scorer` رو به‌عنوان «ژنوم» انتخاب کن** — تنها پای واقعی، deterministic، $0. thresholdهای tunedش «genome» هستن.
2. **مالک `fitness` رو authoritative کن** (قفل ۴-هفته‌ای verdict جلسه ۱۶ رو با یک verdict بردار).
3. **۵ قضاوت انسانی روی یک رفتار قابل تکثیر جمع کن** با acceptance≥40%.
4. **alertها رو پاک کن، live gate رو باز کن.**
5. **بذار `replication.py` proposal emit کنه برای spawn یک نمونهٔ دوم از lead_scorer با market/params متفاوت.**

این اولین reproduction واقعیه و داخل هرم امنیتی باقی می‌مونه.

### ۱۲.ب — آموزشش کن (build a teacher path)

1. **هر verdict تلگرام مالک → یک ردیف structured `(input, decision, label)` در `outcomes.jsonl`.** همین، training data ساخته شد.
2. **`OCTOPUS_HONEST_OUTCOMES` رو روشن کن** تا improvement_rate صادقانه بشه (حتی اگه →۰).
3. **sourceهای `acquisition`/`doctor_archive` رو با outcome واقعی به consolidation برگردون** تا BCM activation بگیره (`y>0`، `theta` آداپت کنه).
4. **replay buffer از beat گذشته اضافه کن**؛ deep_think تمرین/دوباره-consolidate کنه.
5. **distillation:** هر جواب Claude در deep_think → `(question, answer)` در یک set distillation که مغز محلی imitate کنه.

### ۱۲.ج — باهوشترش کن (پنج فیکس پر-بازده)

1. ** Governor router (تقریباً یک‌خطی):** قبل از `extract_json`، ` ``` ` fenceها رو strip کن یا با `max_tokens` بالاتر retry کن. → metabolic allocator زنده میشه. (آیتم ۱۴)
2. **Debate stub:** `OCTOPUS_DEBATE_LOCAL_BUDGET_S` رو ببر بالا، یا Muse/Architect رو برای موضوعات سخت به مغز گرون بفرست. (آیتم ۱۷)
3. **loop رو ببند:** یک insight consolidation در هر سیکل یک تصمیم واقعی رو تغییر بده (خواستهٔ واقعی megaprompt). `neural_driver` رو از `advisory_only` به یک gated effect روی اولویت‌بندی پا ببر. (آیتم ۱۰، ۱۳)
4. **BCM رو غذا بده:** هم‌وقت‌های signal رو با `y>0` به `bcm.update` pipe کن. (آیتم ۱، ۲)
5. **model-selection policy:** `ask_brain(difficulty, prompt)` که بر اساس سختی به ارزان/گرون/محلی route کنه. (آیتم ۲۵، ۲۱)

### ۱۲.د — روی هوش مصنوعی دیگر سوارش کن

1. **host-brain seam:** یک تابع واحد `ask_brain(difficulty, prompt) -> text` که جای clientهای hard-code، route کنه. ارگانیسم model-agnostic میشه.
2. **API نازک شبکه‌ای:** `event_bus` رو wrap کن تا یک مدل/پروسهٔ خارجی بتونه hostش کنه.
3. **parity shadow (هم‌اکنون وجود داره):** تصمیم‌های ارگانیسم رو با مدل host A/B کن قبل از cutover (`brain_core` parity از ۰ به >۰).

---

## بخش ۱۳ — ترتیب‌بندی پیشنهادی برای ایجنتای بعدی

| فاز | کار | آیتم‌ها | بازده |
|---|---|---|---|
| **P0 (امروز)** | فیکس governor router، روشن‌کردن `OCTOPUS_HONEST_OUTCOMES` | 14، 40 | بالا، کم‌ریسک |
| **P1 (هفته)** | feeding BCM، distillation setup، بستن loop روی یک تصمیم | 1، 2، 13، 80 | بالا |
| **P2** | host-brain seam، API نازک، parity>0 | 83–89 | متوسط |
| **P3** | اولین spawn واقعی (lead_scorer clone) | 45–52 | متوسط، نمادین |
| **P4** | metric برون‌زا، alert روی stub-rate | 70، 97 | متوسط |

---

## منابع کلیدی (برای خواندن توسط ایجنت بعدی)

- `ARCHITECTURE-SOT.md`، `OCTOPUS-STRUCTURE.md`، `ARCHITECT-ORGANISM-CONTEXT.md`
- `MEGAPROMPT--octopus-repair-2026-07-25.md` (تشخیص خودارجاعی بودنِ حلقهٔ یادگیری)
- `OCTOPUS-DATAFLOW-WIRING-PROMPT.md`
- `_ops/neural/{bcm,hebbian,consolidation,neural_driver,latent_space}.py`
- `_ops/budget/{governor_epoch,replication,organ_gate,opslib}.py`
- `_ops/debate/{debate_loop,client}.py`
- `_ops/cortex/{improve,audit-matrix}.py`، `_ops/deep_think.py`، `_ops/self_patch.py`
- `_ops/state/{ORGANISM-STATE,bcm-weights,cardiac-budget}.json`
- `_ops/neural/{consolidation,hebbian}.json`، `_ops/governor/governor-alerts.md`
- `03 - Projects/اونلی فنز/{pf_os/*,orchestrator.py,DecisionLog.md}`
