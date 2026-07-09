---
type: build-prompts
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
created_by: agent
sources:
  - "[[2026-07-09 CHRONO-GROUNDING-PLAN — design↔reality + roadmap + decision-gates]]"
  - "recon workflow wthvcewz9 (HEAD=fb90fab)"
tags: [octopus, chrono, glm-prompt, build-ready, propose-only]
created: 2026-07-09
updated: 2026-07-09
---

# 🐙 CHRONO BUILD PROMPTS — مجموعهٔ کامل (هیچ گپی جا نمانده)

> پرامپت‌های copy-paste برای کارگرِ کدنویس (GLM/Codex). **هر گپِ recon → یک پرامپت.** گیت‌های تصمیم با پیش‌فرضِ توصیه‌شده بسته شدند (§دربارهٔ تصمیم‌ها). مبنا: [[2026-07-09 CHRONO-GROUNDING-PLAN — design↔reality + roadmap + decision-gates|GROUNDING-PLAN]]. **کدِ اختاپوس کاملاً در `_ops/` است — نه «Brushline/60_code» (آن پروژهٔ نقاشی است).**

## تصمیم‌های بسته‌شده (پیش‌فرضِ توصیه‌شده — قابلِ وتوی Ari، در AGENT_QUESTIONS ثبت شد)
- **D-A** = HLC فقط علّی + نرخِ ذهنی در experience_meter (نه merge به max). → P-A2
- **D-B** = بله، صفِ world-deadline کنارِ beat-deadline. → P-A3
- **D-C** = امضای entry + wire کردنِ کانالِ تلگرامِ موجود به‌عنوان تنها نویسندهٔ is_human. → P-H1
- **D-D** = تثبیتِ heart-driven age (v0.4.6) + آپدیتِ متنِ spec. → P-D2
- **D-E** = wire کردنِ Doctor Evolution + Box B3 پشتِ flagِ **خاموش** (قابلِ آزمایش، بی‌ریسک). → P-N1/N2
- **D-F** = فعلاً فقط اتصالِ HLC + حلقهٔ خودمختار به همان LeadLeg (ناوگانِ ۶-پا ساخته نشود). → P-L1
- **D-G** = فقط effect-lease پذیرفته (=P-L2)؛ sleep-leg/quarantine-reader/lineage-archive بعداً.
- **D-H** = genome-system فعلاً فایلِ ساده بماند؛ لایهٔ نامیِ V2/alias حداقلی در repo authored شود. → P-D4/D5

## قواعدِ مشترک (در هر پرامپت مستتر است)
```
محیط: کدِ واقعی روی F:\backup (master، ۱۰۲ فایلِ _ops). Glob/Grep به‌خاطرِ .gitignore فایل‌ها را پنهان می‌کنند → Bash(find/grep) + Read مسیرِ مطلق.
walls (نقض=ردِ کار): additive-only · propose-only · fail-closed · human-gate برای پول/spawn · secret فقط env · money قفل (capability∧LIVE_ENABLED∧approval) · هیچ auto-merge · بدونِ ledger/جدولِ موازی (LANGAR=همان genome ledger JSONL) · کانونِ فارسی+inline-English + تگ‌های 【E】/【P】/【S】.
اثبات: self-report ≠ proof — هر تغییر یک تستِ رفتاریِ مستقل؛ اجرا: python -X utf8 _ops/tests/run_all.py و خروجیِ خام paste شود.
تصادم: GLM هم‌زمان commit می‌کند. قبل از edit: git -C /f/backup log -1 --format="%h %cr" -- <file>؛ path-scoped؛ فایلِ hot → هماهنگی نه parallel-build.
اول PLAN (فایل/flag/کجا)، هر ابهام → «⚑ برای معمار»، بعد کد.
```

## ماتریسِ پوشش — هر گپِ recon → پرامپت (اثباتِ کامل‌بودن)
| گپ (شدت) | زیرسیستم | پرامپت | وضعیت |
|---|---|---|---|
| HLC روی رکوردِ ledger غایب (HIGH) | chrono | P-A1 | ready |
| E19 subjective-time flatten (HIGH) | chrono | P-A2 | ready (D-A) |
| E20 world-deadline غایب (HIGH) | chrono | P-A3 | ready (D-B) |
| E15 shared-fate درون‌process (MED، mitigated) | chrono | P-A4 | ready (اختیاری) |
| TINV-5 نشتی sprint.py (MED) | neural | P-A5 | ready |
| E16 is_human جعل‌پذیر (HIGH 🔴) | ledger | P-H1 | ready (D-C، heart-touch) |
| E17 content-addressing (MED) | ledger | P-H2 | ready |
| E21 durability off-site (HIGH) | ledger | P-H3 | ready |
| ledger-fallback خارج از زنجیره (LOW) | ledger | P-H4 | ready |
| فقط ۱ پا/بدونِ حلقه/HLC جدا (HIGH) | legs | P-L1 | ready (D-F) |
| E18 idempotency گیتِ اثر (HIGH) | legs | P-L2 | ready (D-G effect-lease) |
| C5 packet (step/token/stop/verifier) (MED) | legs | P-L3 | ready |
| C7 role-contract فرمال (LOW) | legs | P-L4 | ready |
| TINV-2/R13 cross-process lock best-effort (MED) | legs | P-L5 | ready |
| ApprovalQueue واگرا: cockpit-shadow ≠ approval_channel (MED) | legs | P-L6 | ready |
| Doctor Evolution unwired (HIGH) | doctor | P-N1 | ready (D-E، flag خاموش) |
| Box B3 unwired (MED) | doctor | P-N2 | ready (D-E، flag خاموش) |
| B1 «neural≫null» stub/flaky (LOW، گمراه) | box | P-N3 | **در حالِ اجرا** task_aed6ebad |
| باگِ canonical_consolidation (HIGH 🔴) | memory | P-M1 | ready |
| consolidation سیم‌کشی‌نشده (HIGH) | memory | P-M2 | ready (وابسته P-M1) |
| verification-gate روی school learn (MED) | memory | P-M3 | ready |
| E23/C6 taint (HIGH) | memory | P-M4 | ready |
| seed_curriculum ۴۸ vs ۲۰۰ (LOW) | memory | P-M5 | ready (verdictِ مالک) |
| settings.json hooks غایب (MED) | safety | P-S1 | ready |
| money-lock date نادقیق (MED) | safety | P-S2 | ready |
| Project-F↛Fugu guard غایب (MED) | safety | P-S3 | ready |
| R16 third-party skill unenforced (LOW) | safety | P-S4 | ready |
| هم‌نامیِ LANGAR ≥۶ (CRITICAL 🔴) | docs | P-D1 | doc (no-code) |
| TINV-3 spec کهنه (MED) | docs | P-D2 | doc |
| name-map phantom Brushline≠Octopus | docs | P-D3 | doc |
| لایهٔ V2/E-codes/atlas غایب (D-H) | docs | P-D4 | doc |
| genome submodule vs plain (open #110) | docs | P-D5 | doc |
| ۱۲-سندِ زنده aspirational: live/draft/absent (HIGH) | docs | P-D6 | doc |

**ترتیبِ اجرا (وابستگی):** اول P-D1 (بهداشتِ نام، پیش از هر لمسِ کدِ langar) → T0 باگ‌ها (P-M1) → wiring (P-M2, P-N1, P-N2) → chrono deltas (P-A2..A5؛ **P-A1 ببینِ هشدارِ سریال ↓**) → legs (P-L1..L6) → امنیت (P-H1..H4, P-S1..S4) → docs بقیه (P-D1..D6).
- **⚠️ hot-file سریال:** `P-A1` (افزودنِ HLC به رکورد) و `P-H1` (افزودنِ امضا به رکورد) **هر دو** بدنهٔ hashِ `ledger.py` + `verify()` را نسخه‌بندی می‌کنند → **سریال، هرگز parallel** (یکی merge و سبز شود، بعد دیگری روی همان بستر). ترتیبِ توصیه‌شده: P-A1 اول (HLC)، بعد P-H1 (امضا).
- **P-H1 (قلب):** germline-backup + reviewِ Ari **قبل از merge**. چون `germline-backup.ps1` هنوز untracked است، **P-H3 (که آن را track می‌کند) پیش‌نیازِ ترتیبیِ P-H1 است**.

---

# GROUP W — اتصالِ عصب‌کشی (اولویتِ اول؛ «مغز روشن = کلِ بدن وصل») · مرجع: [[../2026-07-09 OCTOPUS-WIRING-MAP — nervous system + boot connection|WIRING-MAP]]

## P-W1 · [بحرانی] نخاع: organism ↔ LiveLoop/UnifiedBus
```
تسک (P-W1، بحرانی‌ترین) · اتصالِ مغز به بدن:
بخوان: _ops/organism.py (main() init خط ~143-162: make_unified_bus/make_lead_leg صدا زده می‌شود ولی return دور ریخته می‌شود؛ + tick loop) · _ops/live_loop.py (LiveLoop + _InMemoryBus + publish_*_advisory + process_lead/apply_ari_verdict) · _ops/unified_bus.py (UnifiedBus.publish) · _ops/wiring.py (make_unified_bus/make_lead_leg/wire_summary).
گپ (recon 🔴): organism حلقهٔ لخت می‌زند؛ LiveLoop (bus+legs+doctor+advisory) هیچ‌جا instantiate/run نمی‌شود = shelfware. make_unified_bus()/make_lead_leg() return نگه‌داشته نمی‌شود.
بساز (additive، پشتِ profile/flag): (۱) در boot، bus=make_unified_bus() و leg=make_lead_leg() را **نگه دار**؛ یک LiveLoop با bus/leg/doctor/channel بساز و نگه دار. (۲) در tick، سیگنال‌های موجود (neural result، rhythm/spectral، doctor، afferent) را به bus **publish** کن. (۳) propose-only مطلق؛ settle فقط از approval_channel/EffectorGate (دست‌نخورده). (۴) fail-soft هر جزء (§۴: alert نه crash).
DoD: boot یک bus+LiveLoopِ واقعی می‌سازد و نگه می‌دارد؛ tick publish می‌کند؛ تستِ رفتاری: بعد از چند tick، bus event دارد و LiveLoop.advisory_signals پُر است؛ profile=bare → رفتارِ فعلی؛ run_all سبز. path-scoped: organism.py + wiring.py(اگر لازم) + test.
بعدش run_all خام + hash.
```

## P-W2 · آورانِ واقعی: sensory_bus → school_bridge در حلقه
```
تسک (P-W2) · sensory → school در حلقهٔ زنده:
بخوان: _ops/afferent/sensory_bus.py (SensoryBus/AfferentEvent/classify/PII) · _ops/afferent/school_bridge.py (learn_from) · _ops/organism.py (tick) · _ops/live_loop.py (publish_afferent_advisory).
گپ: sensory_bus و school_bridge فقط در اسکریپتِ ingest_raw صدا می‌شوند نه در حلقهٔ زنده → «کلاس درس» از جریانِ زنده یاد نمی‌گیرد.
بساز (پشتِ profile/flag، propose-only): در حلقه (هر N beat) observationهای afferent (فقط لیبلِ انتزاعی، صفر PII) → school_bridge.learn_from → insightهای propose-only به bus؛ awareness persist. verification-gate (فقط CONFIRMED به یادگیریِ تثبیت‌شده — با P-M3 هماهنگ). صفر رکوردِ خام/PII.
DoD: تستِ رفتاری: afferent در حلقه → mean_awareness تغییر → insight روی bus؛ PII هرگز وارد نمی‌شود (تست)؛ خاموش=no-op؛ run_all سبز. path-scoped.
```

## P-W3 · profileِ بوت: OCTOPUS_PROFILE (paper-full پیش‌فرض)
```
تسک (P-W3) · سوئیچِ profile به‌جای ۶ flagِ پراکنده:
بخوان: _ops/wiring.py (flag() + همهٔ OCTOPUS_WIRE_*) · _ops/organism.py (boot) · WIRING-MAP §۲.
گپ: ۶ flag پیش‌فرض خاموش → بوتِ عادی = حلقهٔ لخت؛ مغز از بدن استفاده نمی‌کند.
بساز: تابعِ profile در wiring: OCTOPUS_PROFILE ∈ {bare, paper-full, live}. `paper-full` (پیش‌فرضِ نو) همهٔ wiringِ امنِ propose-only را ON کند (neural/consolidation/school/sensory/doctor+evolution+box/unified/lead-incubating). `bare`=رفتارِ فعلی. flagهای مجزا override بمانند (سازگاری). **money/live مطلقاً جدا:** profile هیچ‌کدام از capability_gate/LIVE_ENABLED/effectorِ پول را باز نمی‌کند.
DoD: paper-full → wire_summary همهٔ امن‌ها True؛ bare → همه False؛ **تستِ سخت: هیچ profile مسیرِ پول را باز نمی‌کند** (capability_gate بسته می‌ماند)؛ run_all سبز. path-scoped: wiring.py + organism.py + test.
```

## P-W4 · [اثباتِ نهایی] connection self-test — «همه‌چیز وصل است»
```
تسک (P-W4، اثبات) · connection self-test:
هدف: تستِ رفتاری که organism را در profile=paper-full برای چند beatِ **تزریقی** (بدونِ sleep واقعی) اجرا/شبیه‌سازی کند و assert کند **هر ماژول ≥۱ بار fire کرد**: sensory→school (mean_awareness تغییر/insight) · neural (snapshot) · canonical_consolidation (خروجی) · doctor.run_cycle (advisory) · evolution (اگر flag) · box (اگر flag) · leg (proposal) · rhythm/spectral advisory روی bus · unified bus (events>0).
بخوان: organism.py (boot+tick پس از W1/W2/W3) · live_loop.py · ماژول‌های wired.
بساز: تستی که instanceِ سبکِ organism/LiveLoop با busِ واقعی می‌سازد، N beat می‌زند، و برای هر ماژول assert «fire شد» دارد؛ اگر یکی fire نکرد → fail با نامِ همان ماژول (تشخیصِ اتصالِ گمشده). در bare → assert فقط متابولیک fire می‌کند.
DoD: paper-full سبز = اثباتِ اینکه بوتِ مغز کلِ بدن را فعال می‌کند؛ در run_all ثبت شود. path-scoped: test + run_all.
```

## P-W5 · فعال‌سازیِ germline.py (CRIT-tier alarm + retry) — از ممیزیِ اتصال
```
تسک (P-W5) · germline.py shelfware است:
بخوان: _ops/germline.py (lag_alarm/lag_severity/run_with_retry — warn2h/ERR26h/CRIT72h) · _ops/wiring.py (enrich_state_with_germline — تعریف شده ولی هیچ‌جا صدا زده نمی‌شود) · _ops/organism.py (tick ~۱۸۸-۱۹۵: از opslib.germline_lag_hours inline استفاده می‌کند، نه germline.py).
گپ: tick نسخهٔ فقیرترِ inline را دارد (بدونِ CRIT tier)؛ germline.py غنی‌تر بی‌مصرف مانده.
بساز: بلوکِ inlineِ germline در tick را با wiring.enrich_state_with_germline(state) جایگزین کن (که germline.lag_alarm را استفاده می‌کند)؛ قرارداد یکی شود. fail-soft (نبودِ دیسک هرگز tick را نکشد).
DoD: tick از germline.py استفاده می‌کند (CRIT tier فعال)؛ تستِ رفتاری: lag>72h → CRIT؛ run_all سبز. path-scoped.
```

## P-W6 · فعال‌سازیِ checkpoint.py (per-beat replay) — پس از P-W1
```
تسک (P-W6) · checkpoint.py shelfware است:
بخوان: _ops/checkpoint.py (checkpoint(beat,hlc,ledger_hash) + replay) · _ops/unified_bus.py (_checkpoint داخلیِ تکراری، خط ~۹۹-۱۱۵) · _ops/chrono.py.
گپ: checkpoint.py بی‌مصرف؛ unified_bus نسخهٔ DDLِ تکراریِ خودش را دارد.
بساز: unified_bus._checkpoint به checkpoint.checkpoint() delegate کند (حذفِ DDLِ تکراری) — پس از P-W1 که unified_bus را واقعاً به حلقه وصل می‌کند. یک قالبِ checkpointِ واحد. صفر spend.
DoD: یک مسیرِ checkpointِ واحد (بدونِ تکرار)؛ تستِ رفتاریِ replay؛ run_all سبز. path-scoped. (وابسته به P-W1.)
```

## P-W7 · اتصالِ spectral.py به Doctor — از ممیزیِ اتصال
```
تسک (P-W7) · spectral.py shelfware است:
بخوان: _ops/doctor/spectral.py (spectral_mine(trace) → spectral-criticality) · _ops/doctor/doctor.py (run_cycle / _gather_trace / mine).
گپ: spectral_mine در run_cycle صدا زده نمی‌شود.
بساز: spectral.spectral_mine(trace) را داخلِ Doctor.run_cycle/_gather_trace صدا بزن تا advisoryِ spectral-criticality کنارِ mine() اضافه شود (trace از قبل organs+errors دارد). advisory/propose-only؛ دکتر معیارِ سنجشِ خودش را ویرایش نکند.
DoD: run_cycle خروجیِ spectral را به‌عنوان advisory دارد؛ تستِ رفتاری؛ run_all سبز. path-scoped.
```

---

# GROUP A — Chrono deltas

## P-A1 · HLC-stamp روی رکوردِ LANGAR (versioned، additive)
```
بخوان: 07 - Knowledge/genome-system/ledger/ledger.py (append/_canonical/verify/age_rule versioning) · _ops/chrono.py (hlc_tick/hlc_max، ChronoBus) · _ops/unified_bus.py (publish).
گپ (HIGH): رکوردهای ledger هیچ hlc_phys/hlc_logical ندارند؛ ترتیبِ کلیِ قلب از HLC جداست (اسناد §0.3/§10 می‌گویند هر رویداد HLC-stamped در LANGAR).
بساز (با احتیاطِ hash-body، دقیقاً مثلِ الگوی age_rule): فیلدهای hlc_phys/hlc_logical اختیاری به بدنهٔ رکوردهای **نو** اضافه شوند و از ChronoBus/unified_bus.publish تزریق شوند. verify() نسخه‌بندی شود: رکوردهای legacy بدونِ hlc معتبر بمانند (chain نشکند)، رکوردهای نو hlc داشته باشند. هیچ backfillِ رکوردِ قدیمی (ترتیبِ جعلی ممنوع).
DoD: رکوردِ نو hlc دارد و در بدنهٔ hash است؛ verify() هم legacy هم نو را می‌پذیرد؛ تستِ رفتاری + تستِ سازگاریِ chain با رکوردِ مخلوط؛ run_all سبز. commit path-scoped: ledger.py + unified_bus.py + test. **قلب — germline-backup قبلش.**
```

## P-A2 · [D-A] زمانِ ذهنی: HLC فقط علّی، نرخ در meter (E19)
```
بخوان: _ops/chrono.py (beat_once step2/3: now=hlc_tick(hlc_max(...))→broadcast؛ LegHandle._on_broadcast→_merge_for) · experience_meter.
گپ (E19): broadcastِ max(HLC) ساعتِ هر پا را به max می‌کشد → زمانِ ذهنیِ متفاوت له می‌شود؛ با canonِ «پاها در نرخ‌های متفاوت» تنش دارد.
بساز (تصمیمِ D-A): HLC فقط ضامنِ ترتیبِ علّی بماند (merge فقط برای رابطهٔ علّیِ واقعی، نه هم‌ترازیِ اجباریِ همهٔ پاها هر ضربان). «زمانِ ذهنی/نرخ» صرفاً در experience_meter زندگی کند و merge نشود. تصریح در docstring + کد.
DoD: تستِ رفتاری: پای کند پس از ضربان نرخِ ذهنیِ متفاوتش را حفظ می‌کند (به max کشیده نمی‌شود) در حالی که ترتیبِ علّی سالم است؛ run_all سبز. commit path-scoped.
```

## P-A3 · [D-B] صفِ world-deadline کنارِ beat-deadline (E20/C4)
```
بخوان: _ops/chrono.py (anticipation_queue: فقط due_beat؛ scheduler WHERE due_beat<=beat).
گپ (E20): هیچ راهی برای کدگذاریِ deadlineِ دنیای واقعی (مثل followupِ مشتریِ نقاشی «۹ صبح») نیست؛ downtime همه‌چیز را slip می‌کند.
بساز (تصمیمِ D-B): دو کلید/دو صف — world-deadline (زمانِ جهان) + beat-deadline (کارِ درونی). **فقط pacemaker مجاز به ترجمهٔ wall→beat** (TINV-5 حفظ؛ پاها ساعت نخوانند). catch-up policy برای downtime.
DoD: تستِ رفتاری: تعهدِ world-deadline پس از downtime هم fire می‌شود؛ کارِ beat-based بی‌تغییر؛ run_all سبز. commit path-scoped.
```

## P-A4 · [اختیاری] کاهشِ shared-fate درون‌process (E15)
```
بخوان: _ops/chrono.py (Pacemaker daemon-thread) · _ops/organism.py (doctor_beat در main loop؛ legs in-memory) · _ops/watchdog.py + 04/scripts/organism-watchdog.ps1 (نگهبانِ بیرونی).
گپ (MED، از قبل mitigated): pacemaker daemon-thread + doctor_beat + legs همه در یک process؛ یک crash هر سه را می‌کشد. C2 (watchdogِ بیرونیِ PS1) revive-after-death می‌کند، ولی supervisionِ مستقلِ زنده نیست.
بساز (کم‌ریسک، اختیاری): fail-soft هر جزء را سخت‌تر کن (استثنا در یکی، بقیه زنده)؛ اطمینان از ثبتِ Scheduled-Task برای PS1 (اسکریپتِ ثبت + verify). اگر جداسازیِ process بزرگ است → فقط «⚑ برای معمار» با هزینه/فایده، کد نزن.
DoD: crashِ شبیه‌سازی‌شدهٔ یک جزء → pacemaker/heartbeat زنده می‌ماند یا PS1 revive می‌کند (تست/داکیومنت)؛ run_all سبز.
```

## P-A5 · نشتیِ TINV-5 در sprint.py (wall-clock → beat)
```
بخوان: _ops/neural/sprint.py (~۲۵/۷۶/۹۱: deadline_ts=time.time()+budget_beats*60) · _ops/chrono.py (beat_seq).
گپ: SprintContract بودجهٔ beat را با ساعتِ دیواری می‌سنجد — خلافِ TINV-5.
بساز: بودجه بر حسبِ beat_seq (تزریقی از broadcast/param)، نه time.time().
DoD: sprint دیگر time.time() برای deadline نمی‌خواند؛ تستِ رفتاری با beatِ تزریقی؛ run_all سبز. commit path-scoped.
```

---

# GROUP H — Heart / ledger security

## P-H1 · [D-C] قلبِ احرازشده — is_human فقط از کانالِ امضاشده (E16 🔴 شدیدترین حفره)
```
پیش‌نیاز: germline-backup + reviewِ Ari قبل از merge (تغییرِ قلب).
بخوان: 07 - Knowledge/genome-system/ledger/ledger.py (append: is_human بولیِ آزاد) · _ops/budget/approval_channel.py (TelegramApprovalChannel: allowlist+token+hmac؛ NotWired؛ گیتِ افکت نه نوشتن) · _ops/chrono.py (on_human_judgment).
گپ (E16): هر مسیرِ کد می‌تواند append(is_human=True) بزند؛ گیتِ فعلی جلوِ افکت است نه نوشتنِ رکورد.
بساز (تصمیمِ D-C): امضا روی entry (کلید فقط env/نزدِ Ari) + verifyِ امضا جزوِ verify() زنجیره؛ کانالِ تلگرامِ موجود را wire کن به‌عنوان تنها تولیدکنندهٔ is_human. مسیرِ کدِ عادی نتواند is_human=True بنویسد (بدونِ امضا → رد). رکوردهای legacy معتبر بمانند (versioned).
DoD: append(is_human=True) از مسیرِ غیراحرازشده رد/بی‌امضا؛ verify() امضای human را چک می‌کند؛ تستِ رفتاریِ جعل؛ chain با رکوردِ مخلوط سالم؛ run_all سبز. commit path-scoped.
```

## P-H2 · content-addressing payload (E17)
```
بخوان: ledger.py (payload درون‌خطی، immutable-by-hash ولی نه CAS) · _ops/chrono.py (gated_effect.payload_ref).
گپ (E17): payload با hash تغییرناپذیر است ولی content-addressed نیست (ref به CAS ندارد).
بساز (additive): برای payloadهای بزرگ/بیرونی، ذخیرهٔ content-addressed (hash→محتوا) + payload_ref در رکورد؛ payloadهای کوچک می‌توانند inline بمانند (سازگاریِ عقب‌رو). hash روی بایتِ canonical حفظ.
DoD: payloadِ بزرگ به CAS می‌رود و ref در رکورد؛ verify() سالم؛ تستِ رفتاری؛ run_all سبز. commit path-scoped.
```

## P-H3 · durability off-site + شاهدِ بیرونی (E21)
```
بخوان: _ops/germline.py (lag monitor) · 07/genome-system/scripts/backup.py (git+tar محلی) · 04/scripts/germline-backup.ps1 (untracked).
گپ (E21): off-site copy#3 خودکار نیست؛ شاهدِ بیرونیِ head-hash نیست؛ ps1 untracked.
بساز: (۱) germline-backup.ps1 را track کن؛ (۲) copy#3 off-site خودکار (restic/rclone به مقصدِ رمزشده — credential فقط env، هرگز commit)؛ (۳) انتشارِ دوره‌ایِ head-hashِ ledger نزدِ شاهدِ بیرونی (commitِ امضاشده/فایلِ جدا). سایه فقط‌خواندنی.
DoD: بکاپِ off-site خودکار + head-hash منتشر + restore-drill سبز؛ secret فقط env. (بخشی ops/runbook — هماهنگی با Ari.)
```

## P-H4 · جذبِ ledger-fallback به زنجیره (out-of-chain sink)
```
بخوان: _ops/budget/opslib.py (ledger_note: هنگام شکست به STATE_DIR/ledger-fallback.jsonl می‌نویسد) · ledger.py.
گپ (LOW): fallback یک سینکِ ثانویهٔ خارج از زنجیره است → ریسکِ خفیفِ گم‌شدنِ رویداد از chain.
بساز: مکانیزمِ reconcile که رویدادهای fallback را پس از رفعِ اختلال به زنجیرهٔ اصلی append/ادغام کند (idempotent، بدونِ دوباره‌شماری)؛ آلارم اگر fallback غیرخالی ماند.
DoD: رویدادِ fallback پس از recovery به chain می‌رود؛ تستِ رفتاری؛ run_all سبز. commit path-scoped.
```

---

# GROUP L — Legs / effect-gating

## P-L1 · [D-F] اتصالِ HLC + حلقهٔ خودمختار به LeadLeg (فقط همان یک پا)
```
بخوان: _ops/legs/leg.py + lead_leg.py · _ops/chrono.py (ChronoBus.LegHandle، HLC) · _ops/organism.py (make_lead_leg که return ذخیره نمی‌شود).
گپ (HIGH): پا حلقهٔ خودمختار ندارد؛ آبجکتِ Leg به LegHandle/HLC وصل نیست؛ make_lead_leg دور ریخته می‌شود. تصمیمِ D-F: فقط همان LeadLeg، ناوگانِ ۶-پا نساز.
بساز (پشتِ flag، مرحله‌ای): آبجکتِ LeadLeg را به یک LegHandle/HLC ببند؛ از حلقهٔ ضربان بران (نه دور ریختن)؛ HLC بزند و ack بدهد؛ propose-only، هیچ effector؛ single-writer حفظ. خاموش = رفتارِ فعلی.
DoD: LeadLeg در حلقه HLC می‌زند و ack می‌دهد؛ تستِ رفتاری؛ خاموش=no-op؛ run_all سبز. commit path-scoped.
```

## P-L2 · [D-G] idempotency + Effect Lease گیتِ اثر (E18)
```
بخوان: _ops/chrono.py (EffectorGate: request/release_gated_effects/settle + gated_effect DDL) · _ops/budget/approval_channel.py (_settle_effect).
گپ (E18): release همهٔ pendingها را با یک human-append آزاد می‌کند (بدونِ بندِ اثرِ خاص)؛ effect_id تصادفی (بدونِ dedupِ محتوایی)؛ حالتِ 'failed' نیست.
بساز (تصمیمِ D-G = Effect Lease): (۱) release فقط اثرِ متناظرِ همان human-append (release_ref) را releasable کند؛ (۲) کلیدِ dedupِ محتوایی (organ,action,payload-hash) → exactly-once؛ (۳) حالتِ 'failed' + گذارها. paper (هیچ اثرِ liveِ نو). fail-closed.
DoD: تستِ رفتاری: (الف) دو request یکسان→یک اثر؛ (ب) human-append برای X فقط X را release؛ (ج) settleِ دوبار idempotent؛ (د) crash بینِ append/settle دوباره fire نمی‌کند؛ run_all سبز. commit path-scoped.
```

## P-L3 · پاکتِ بودجهٔ کامل per-task (C5)
```
بخوان: _ops/legs/leg.py (TaskPacket: فقط budget_aud/spawn=0) · _ops/budget/reconcile.py (verifier مستقلِ Lead) · _ops/doctor/box/warden.py (سقفِ token، برای box نه پاها).
گپ (C5): TaskPacket فقط cost-cap دارد؛ step/token-cap و stop-condition فرمال نیست؛ verifier مستقل فقط برای Lead.
بساز (additive روی TaskPacket): سقفِ step + سقفِ token + stop-condition صریح + قلابِ verifierِ مستقل از doer (به‌صورتِ عمومی، نه فقط Lead). کارِ بی‌پاکت dispatch نشود.
DoD: task با سقفِ step/token فراتر → رد/توقف؛ verifier مستقل قبل از ApprovalQueue؛ تستِ رفتاری؛ run_all سبز. commit path-scoped.
```

## P-L4 · قراردادِ نقشِ فرمال (C7)
```
بخوان: _ops/legs/leg.py (TaskPacket) + lead_leg.py.
گپ (C7): ممنوعات+budget هست ولی goal/escalation فرمالیزه نشده؛ فقط ۱ نقش نمونهٔ عینی.
بساز: بلوکِ قراردادِ نقش به‌صورتِ داده (هدف/ورودی/خروجیِ استاندارد/ممنوعات/قاعدهٔ escalation/budget) روی Leg؛ sub-legِ آینده از والد ارث ببرد. برای LeadLeg نمونهٔ کامل پر شود.
DoD: قرارداد به‌صورتِ داده قابلِ‌بازرسی؛ تستِ ساختاری+رفتاری؛ run_all سبز. commit path-scoped.
```

## P-L5 · سخت‌سازیِ single-writerِ cross-process (TINV-2/R13)
```
بخوان: 07/genome-system/ledger/ledger.py (_AppendLock: روی timeout «بدونِ قفل ادامه می‌دهد» → امکانِ fork زنجیره) · _ops/unified_bus.py (مسیرهای مستقیمِ قدیمیِ ledger.append deprecated-not-deleted).
گپ (MED): تک‌نویسندهٔ سختِ سراسری نیست؛ cross-process best-effort.
بساز: قفلِ cross-process fail-closed کن (روی timeout → رد/صبر، نه ادامهٔ بی‌قفل)؛ مسیرهای مستقیمِ قدیمی را پشتِ UnifiedBus کانالیزه کن (deprecate با adapter، نه delete). هیچ fork.
DoD: دو نویسندهٔ هم‌زمان → یکی رد/صبر، chain forkنمی‌شود؛ تستِ رفتاری؛ run_all سبز. commit path-scoped.
```

## P-L6 · یکپارچه‌سازیِ ApprovalQueue (صفِ shadow ≠ صفِ واقعی)
```
بخوان: _ops/brain/cockpit.py (ApprovalItem/_approval_queue/add_approval — صفِ advisory/shadow، docstring: «هیچ import از *_gate/chrono/money production»؛ به EffectorGate وصل نیست) · _ops/budget/approval_channel.py (_do_approve/_settle_effect — مسیرِ واقعیِ settle) · _ops/chrono.py (EffectorGate).
گپ (MED): دو صفِ تأییدِ ناهمگام وجود دارد: صفِ cockpit (shadow، به گیت وصل نیست) و approval_channel (مسیرِ واقعی). «ConstitutionGate» یک نامِ phantomِ V2 است (نساز)، ولی واگراییِ این دو صف واقعی است — کاربر ممکن است در UIِ cockpit «تأیید» ببیند که هیچ اثری settle نمی‌کند، یا برعکس.
بساز (بدونِ ساختِ موجودِ سوم): یک منبعِ حقیقتِ واحد برای وضعیتِ تأیید — صفِ cockpit باید **نمای فقط‌خواندنیِ** همان حالتِ approval_channel/EffectorGate باشد (نه یک صفِ مستقل)، یا صریحاً به‌عنوان shadow برچسب بخورد و هرگز ادعای «تأییدشده» نکند مگر از مسیرِ واقعی. propose-only؛ فقط approval_channel→on_human_judgment مجاز به settle بماند.
DoD: تستِ رفتاری: آیتمِ «تأییدشده» در cockpit ⟺ اثرِ متناظر واقعاً releasable/settled در EffectorGate است (بدونِ واگرایی)؛ صفِ shadow هرگز به‌تنهایی settle نمی‌کند؛ run_all سبز. commit path-scoped: cockpit.py + test (+ approval_channel اگر لازم).
```

---

# GROUP N — Neural / Doctor wiring

## P-N1 · [D-E] سیم‌کشیِ Doctor Evolution (flag خاموش)
```
بخوان: _ops/doctor/evolution.py (RFCArchive/measured_lift/tournament_rank/survivor — dead) · _ops/doctor/doctor.py (run_cycle) · calibration.py.
گپ (HIGH): evolution.py هرگز از run_cycle صدا نمی‌شود.
بساز پشتِ flagِ نو (پیش‌فرض خاموش، تصمیمِ D-E): mine از RFCArchive نمونه، tournament_rank قبل از submit، measured_lift به‌جای liftِ موردِانتظار. propose-only + human-merge + verifier-independence دست‌نخورده (دکتر معیارِ خودش را ویرایش نکند). خاموش=رفتارِ فعلی.
DoD: flag روشن→archive/tournament/measured_lift در چرخه fire (تستِ رفتاری)؛ خاموش→no-op؛ verifier-independence حفظ؛ run_all سبز. commit path-scoped.
```

## P-N2 · [D-E] سیم‌کشیِ Box B3 bridge (flag خاموش)
```
بخوان: _ops/doctor/box/ (box.py/b3_bridge/falsif_harness/b4_fusion/warden) · doctor.py (submit_for_approval).
گپ (MED): box/* هیچ مسیرِ runtime ندارد.
بساز پشتِ flag (خاموش، D-E) — **کلِ خوشهٔ box (۱۲ فایل)، نه فقط seam** (ممیزیِ اتصال: همه shelfware): box.py را در run_cycle instantiate کن و روی trace step بزن → box.step() metrics → b3_bridge.box_to_doctor_pipeline(metrics, doctor) → doctor.submit_for_approval (propose-only، human-gate)؛ b4_fusion.compute_phi_t = سیگنالِ novelty به Box؛ falsif_suite = کنترلِ دوره‌ای. با wire‌شدنِ box.py، support-libهایش (agent_state/dynamics/archivist/topology/warden/sensors/null_dreamer) خودکار reachable می‌شوند. Wardenِ ۲٪ + STOP-obey حفظ. خاموش=on-shelf.
DoD: flag روشن → Box در چرخه step می‌کند و از b3_bridge به doctor propose می‌رسد (نه merge)؛ b4/falsif فعال؛ خاموش→no-op؛ run_all سبز. commit path-scoped.
```

## P-N3 · [در حالِ اجرا: task_aed6ebad] رفعِ گمراهیِ B1 stub/flaky
```
(این پرامپت الان به‌عنوان تسکِ جدا در حالِ اجراست — این‌جا برای کاملیِ ماتریس.)
بخوان: _ops/doctor/box/falsif_harness.py (neural_dreamer_action=stub) + test_box_b134.py ([B1] suite flaky ~۱/۳).
بساز: یا [B1] را قطعی/معنادار کن (seed ثابت + نمونهٔ بزرگ‌تر/آستانهٔ منطبق) + docstring «تستِ plumbing نه هوش»؛ یا تا وقتی Dreamerِ واقعی نیست → xfail/skipِ صریح (نه سبزِ دروغین).
DoD: ۱۰ اجرای پیاپی→۱۰/۱۰ قطعی؛ run_all سبز؛ هیچ سبزِ گمراه‌کننده. commit path-scoped.
```

---

# GROUP M — Memory / context

## P-M1 · فیکسِ باگِ canonical_consolidation (HIGH 🔴)
```
بخوان: _ops/wiring.py (canonical_consolidation، ~۲۵۵-۲۹۳: mean_awareness() ناموجود) · _ops/afferent/school_bridge.py · 07/school-memory/curriculum.py (AwarenessField.mean_awareness) · test_frontier.py.
گپ (HIGH): mean_awareness() روی SchoolBridge وجود ندارد → AttributeError بی‌صدا بلعیده → School هرگز به consolidation نمی‌رسد؛ تست‌های fake آن را نمی‌گیرند.
بساز: یا mean_awareness() به SchoolBridge اضافه (که self.field.mean_awareness برگرداند) یا فراخوانی اصلاح شود؛ except دیگر خطا را بی‌صدا نبلعد (منشور §۴ → opslib.alert)؛ تستِ نو با SchoolBridgeِ **واقعی**.
DoD: باگ رفع؛ تست با SchoolBridgeِ واقعی سبز؛ except خطا را نمی‌بلعد؛ run_all سبز. commit path-scoped.
```

## P-M2 · سیم‌کشیِ canonical_consolidation در حلقهٔ زنده (وابسته P-M1)
```
بخوان: _ops/organism.py + live_loop.py + wiring.py (canonical_consolidation + الگوی OCTOPUS_WIRE_*) + neural/consolidation.py.
گپ (HIGH): فقط تست‌ها صدایش می‌زنند → دو مسیرِ موازیِ حافظه مانده (M-unification محقق نشده).
بساز: پشتِ flagِ نو (OCTOPUS_WIRE_CONSOLIDATION، خاموش) هر N ضربان fire شود (نه هر tick)؛ verification-gate حفظ؛ صفر spend. خاموش=no-op.
DoD: flag روشن→consolidation منبعِ School را می‌گنجاند (اثباتِ رفتاری با SchoolBridgeِ واقعی)؛ خاموش→no-op؛ run_all سبز. commit path-scoped.
```

## P-M3 · verification-gate روی school_bridge.learn_from
```
بخوان: _ops/afferent/school_bridge.py (learn_from: از هر afferent=True یاد می‌گیرد) · _ops/neural/consolidation.py (_verify_source الگو).
گپ (MED): learn_from گیتِ CONFIRMED ندارد؛ از دادهٔ بیرونی‌تبار (crypto) مستقیم یاد می‌گیرد.
بساز: همان verification-gateِ ConsolidationCycle را روی learn_from اعمال کن (فقط منبعِ verified/CONFIRMED به یادگیریِ ماندگار برسد؛ afferentِ خام می‌تواند observe شود ولی نه به یادگیریِ تثبیت‌شده تبدیل). سازگار با taint (P-M4).
DoD: تستِ رفتاری: دادهٔ unverified → observe ولی نه یادگیریِ تثبیت‌شده؛ CONFIRMED → یادگیری؛ run_all سبز. commit path-scoped.
```

## P-M4 · برچسبِ taint + وراثت (E23/C6)
```
بخوان: _ops/afferent/sensory_bus.py (Observation/classify) · school_bridge.py (AfferentEvent) · curriculum.py (InsightEvent).
گپ (E23/C6): هیچ فیلدِ taint/origin؛ وراثت نیست (فعلاً propose-only مهارش می‌کند).
بساز (additive): فیلدِ trust (external|internal|confirmed) روی Observation→AfferentEvent→InsightEvent با وراثت (مشتقِ external، external است)؛ قاعدهٔ سخت (assert/alert): دادهٔ tainted در جایگاهِ فرمان ننشیند؛ تطهیر فقط human-append. رکوردهای قدیمی پیش‌فرضِ عاقلانه.
DoD: تستِ رفتاری: insightِ مشتقِ external → trust=external؛ CONFIRMED→internal؛ run_all سبز. commit path-scoped.
```

## P-M5 · گسترشِ curriculum به ۲۰۰ نود (verdictِ مالک)
```
پیش‌نیاز: verdictِ Ari (خودِ کد این را deferred اعلام کرده).
بخوان: 07/school-memory/curriculum.py (seed_curriculum: ۶ لایه×۸=۴۸).
بساز: گسترش به ~۲۰۰ نود در ۶ لایه طبقِ طرحِ School (با تأییدِ ساختارِ لایه‌ها از Ari). laplacian/spectral_gap مقیاس‌پذیر بماند.
DoD: seed ۲۰۰ نود؛ spectral_gap محاسبه می‌شود؛ تست؛ run_all سبز. commit path-scoped. (⚑ ساختارِ ۲۰۰-نودی نیازِ تأییدِ Ari.)
```

---

# GROUP S — Safety / ops

## P-S1 · لایهٔ hooks در settings.json (منشور §۱۰)
```
بخوان: .claude/settings.json (فقط deny، بدونِ hooks) · _PROJECT_INSTRUCTIONS.md §۱۰ · .agentignore.
گپ (MED): منشور «deny + hooks» می‌گوید ولی hooks نیست.
بساز: لایهٔ hookِ حداقلی که مسیرهای ممنوعِ .agentignore (secret/.git/_code) را در سطحِ tool-call مسدود/لاگ کند (backstopِ واقعی) — همسو با §۱۰.
DoD: hookِ کارکننده + تستِ «مسیرِ ممنوع مسدود شد»؛ چیزِ موجود نشکند.
```

## P-S2 · آشتیِ معناشناسیِ money-lock date
```
بخوان: _ops/budget/opslib.py (live_gate_open، LIVE_GATE_DATE=2026-07-21) · capability_gate.py («calendar≠capability») · money_gate.py.
گپ (MED): تاریخ فقط debate/replication را گیت می‌کند نه پولِ واقعی؛ ادعای ۴-جزئیِ money-lock دربارهٔ تاریخ نادقیق است.
بساز: معناشناسی را صریح و یکدست کن — یا تاریخ را به‌عنوان یک شرطِ لازمِ صریح در مستنداتِ money-lock درست توصیف کن (کد سالم است، فقط ادعا نادقیق)، یا اگر تاریخ باید در گیتِ پول هم باشد، با تأییدِ Ari اضافه کن. پیش‌فرض: اصلاحِ توصیف (کد fail-closed درست است).
DoD: توصیفِ money-lock با کد می‌خواند؛ اگر کدی، تستِ رفتاری؛ run_all سبز.
```

## P-S3 · enforceِ containmentِ Project-F (نه فقط UI)
```
بخوان: _ops/afferent/sensory_bus.py (PII blacklistِ عمومی) · cockpit (متنِ containmentِ Project-F فقط UI) · هر مسیرِ Project-F.
گپ (MED): «Project-F↛Fugu guard» کدِ نام‌دار ندارد؛ containment فقط متنِ UIِ cockpit است. (توجه: «fugu» نامِ مدلِ LLM است نه مقصدِ داده.)
بساز: نقطهٔ enforceِ واقعی برای Project-F: صفر رسانه/هویت/PII بیرونِ پوشهٔ پروژه (چکِ مسیر + PII در هر خروجیِ Project-F)، draft-in-queue اجباری. نه صرفاً UI.
DoD: تلاش برای خروجِ داده/رسانهٔ Project-F از مرز → رد/alert؛ تستِ رفتاری؛ run_all سبز. commit path-scoped.
```

## P-S4 · سیاستِ third-party skill/کد (R16 OpenClaw)
```
بخوان: هر مسیرِ لود/اجرای skill/کدِ بیرونی · .agentignore · settings.json.
گپ (LOW): هیچ enforceِ زنجیرهٔ تأمین (~۱۲٪ registryِ OpenClaw مخرب بود).
بساز: قاعدهٔ سخت: هیچ skill/کدِ third-party بدونِ reviewِ ثبت‌شده در ledger اجرا نشود (allowlist + ثبتِ منشأ). فعلاً حداقل یک گاردِ propose-only + alert.
DoD: تلاش برای اجرای skillِ ثبت‌نشده → رد/alert؛ تست؛ run_all سبز.
```

---

# GROUP D — بهداشتِ اسناد (no-code — کارِ معمار/نوت)
- **P-D1 (CRITICAL):** ثبتِ هر ≥۶ referentِ «لنگر/LANGAR/Anchor» در قانونِ ALIAS/هم‌نامی (فعلاً ۳). **پیش از هر لمسِ کدِ named-langar.** (خودم می‌توانم بزنم.)
- **P-D2:** آشتیِ TINV-3 (heart-driven v0.4.6): ORGANISM-SPEC آپدیت + CHRONO ARCH §7 «stale» علامت.
- **P-D3:** اصلاحِ name-mapِ phantom (Brushline≠Octopus) در اسنادِ ورودی/ECOSYSTEM.
- **P-D4 (D-H):** لایهٔ نامیِ V2/alias حداقلی در repo authored شود — نگاشتِ **کاملِ** namespaceها: TINV-1..7↔(V2 ادعاییِ 1..11) · INV-*/AP-* (CHRONOS-FABLE) · E15–E25/C1–C12/R-x (کدهای سندِ تلگرام، غایب از repo) · **و تصادمِ D-code: گیت‌های V2 D1–D7/B1–B4 در برابرِ DECISIONS.md D-01..D-29 در برابرِ AGENT_QUESTIONS «open-decision #N»** — هر سه در یک جدولِ واحد آشتی شوند تا ایجنتِ بعدی D-code را اشتباه نگیرد. اسنادِ تلگرام به‌عنوان ثانویه ارجاع.
- **P-D5 (open #110):** تصمیمِ genome-system submodule vs plain — فعلاً plain، مستند در DECISIONS.
- **P-D6:** آشتیِ «۱۲ سندِ زنده» — فهرستِ صریحِ live/draft/absent بساز: فقط `SYSTEM_MAP.md` (06) و `AGENT_REGISTRY.md` (05) واقعاً live؛ `MASTER_ARCHITECTURE` فقط Inbox-draft؛ `KNOWLEDGE_GRAPH` غایب؛ بقیه؟ تصمیم: کدام واقعاً باید live باشد و کدام از فهرستِ «۱۲ سند» حذف شود (تا ادعای aspirational به واقعیت بخورد). خروجی: یک INDEXِ صادقانهٔ اسنادِ زنده.
