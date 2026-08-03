# OCTOPUS TRUTH MAP — نقشه‌ی حقیقتِ ارگانیسم برای مأموریتِ BODY

> Phase 0 scan · 2026-07-29 · عامل: Body/Math-Self Architect (swarm zone A)
> روش: خواندنِ مستقیمِ فایل‌ها از `F:\backup` — بدونِ حدس. برچسب‌ها:
> [OBS] مشاهده‌ی مستقیم · [INFER] استنباط از چند فایل · [OPEN] نامعلوم ·
> [LIVE] در runtime فعال · [MOCK] فقط UI/سند · [DEAD] نام‌برده ولی وصل نیست · [MISSING] پیدا نشد.
>
> ⚠️ این سند ثبتِ رسمی در `ARCHITECTURE-SOT.md` **ندارد** — پیشنهادِ ثبت در §۹ آمده؛ نیازمندِ verdictِ مالک.

---

## ۱. یک‌خطی

ارگانیسم **زنده است و همین الان می‌تپد** (`_ops/`, beat=16528 در 2026-07-29T00:25:36 [OBS])،
و مأموریتِ BODY نیاز به بازنویسی ندارد: **لایه‌ی بدن باید دقیقاً روی الگوی موجودِ
`synapse/` (اندامِ SENSE، flag-gated، propose-only، صفر-LLM) سوار شود.**
هر چیزی که مأموریت «معادله‌ی مغز/بدن» می‌خواهد، یا از قبل در ارگانیسم هست
(SOG anchors، phi، coherence_r، L/E/G/K/O) یا یک ماژولِ additiveِ نو است
(Hilbert/SNR/Kuramoto-lite) که همان الگو را تکرار می‌کند.

---

## ۲. وضعیتِ زنده‌بودن (شواهدِ خام)

| شاهد | مقدار | منبع | برچسب |
|---|---|---|---|
| beat | 16528 | `_ops/state/ORGANISM-STATE.json` ts=2026-07-29T00:25:36 | [OBS][LIVE] |
| پروسه‌ها | organism(8771) · cortex(8772) · live(8773) | handoff 2026-07-25 + watchdog scripts | [OBS][LIVE] |
| leg | `lead-naghshi` = alive، phi=0.29 (آستانه‌ی مرگ 16.0)، ack_samples=20 | ORGANISM-STATE → chrono.legs_diag | [OBS][LIVE] |
| arbiter | effective_period_s=57.11، driver=consensus، GREEN | ORGANISM-STATE | [OBS][LIVE] |
| تست‌ها | 389 فایلِ تست (گزارشِ self-model) | `_ops/state/cortex/self-model.json` ts=2026-07-29T00:12 | [OBS] |
| فلگ‌های wire | 122 فلگ | self-model.json → wire_flags | [OBS] |
| پروفایل | `paper-full`، doctor_every_n=1440 | ORGANISM-STATE.wiring | [OBS][LIVE] |
| ledger ژنوم | hash-chain فعال (NOTEهای scheduler تا 2026-07-28T14:25 UTC) | `07 - Knowledge/genome-system/ledger/ledger.jsonl` tail | [OBS][LIVE] |
| کارت‌های تأیید | M-* تا 2026-07-28 | `_ops/state/telegram/approvals/` | [OBS][LIVE] |

نکته‌ی ساعت: ledger بر UTC است و سیستم ‎+10:00 سیدنی — قبل از هر قضاوتِ «کهنگی» ۱۰ ساعت اختلاف حساب شود (درسِ handoff).

---

## ۳. ماتریس LIVE / MOCK / DEAD — بدن‌محور

### ۳.۱ LIVE — اندام‌های موجود که «بدن» را از قبل نصفه دارند

| اندامِ مأموریت BODY | فایل(های) موجود | وضعیت | شاهد |
|---|---|---|---|
| **SensorHub (دیجیتال)** | `_ops/afferent/` (sensory_bus, ingest_raw, school_bridge) + `observability/` (leg/budget/flag monitors) + `events.py`→`state/events.jsonl` | [LIVE] | afferent_every_n=1440 در wiring [OBS] |
| **MathFilter / معادله روی تله‌متریِ خود** | `_ops/synapse/sense.py` (SOG: E_shadow/Δ_self/identity proxies) + `4d_system/core/metrics.py` (importِ read-only) | [LIVE-در-SHADOW] فلگ `SYNAPSE_ENABLED`/`OCTOPUS_SYNAPSE_ENABLED` پیش‌فرض خاموش | sense.py docstring + SOT §synapse [OBS] |
| **قلبِ ریاضیِ قفل‌شده** | `_ops/heart/sog_math.py` + `_ops/state/sim/PULSE-EQUATIONS-LOCKED.json` | [LIVE] anchors با rel_err ~1e-6 و dare_crosscheck ok قفل شده‌اند | [OBS] |
| **Heart/pacemaker (فازِ جهانی)** | `_ops/heart/` (control_law, pulse_arbiter, heartstate) + `_ops/chrono.py` (CHRONO_PERIOD_S=60) + `state/pulse/*` | [LIVE] wire_heart=true, wire_pulse=true | [OBS] |
| **livenessِ اندام (آمارِ سیگنال)** | `_ops/chrono.py` + `state/chrono.db` — phi = z-score→p-value با honest_tolerance | [LIVE] legs_diag در ORGANISM-STATE | [OBS] |
| **Self-model** | `_ops/cortex/self_model.py` + `state/cortex/self-model.json` (schema self-model.v1، 352 ماژول، self_awareness_pct=99.7*) | [LIVE] | [OBS] |
| **خودشناسیِ دکتر + کالیبراسیون** | `_ops/doctor/` (self_knowledge, calibration, self_accuracy, spectral) + `state/doctor/self-knowledge.jsonl` | [LIVE] | handoff 07-25 [OBS] |
| **اعتماد (trust engine)** | `_ops/memory/gate.py` — سطوح OWNER_CONFIRMED/GRADED؛ درسِ C3: trust از outcomeِ پس از اعمال، نه از اعتمادبه‌نفس | [LIVE] | handoff §C3 [OBS] |
| **Reward از outcome** | `_ops/outcomes/` (verdict_recorder, learning_gate, outcome_store) + `state/outcomes/outcomes.db` | [LIVE] | [OBS] |
| **بارِ انسانی (human burden)** | `_ops/budget/approval_fatigue.py` — ALLOW/THROTTLE/COOLDOWN/CUTOFF، dwell<8s = مشکوک | [LIVE] pure function | [OBS] |
| **ریتم/فازِ زیستی** | `_ops/chrono_rhythm/rhythm.py` (T_beat, hrv, tau, gamma, coherence_r) + `_ops/neural/circadian.py` | [LIVE] wire_rhythm=true, wire_circadian=true | [OBS] |
| **Order parameter r** | `_ops/coherence.py` + `nervous-system/neural-schema.json` فیلد `coherence_r` | [LIVE] | [OBS] |
| **Nociceptor (حسِ درد)** | `_ops/neural/nociceptor.py` + test_pain_calibration | [LIVE] wire_neural=true | [OBS] |
| **Ledger/audit spine** | `spine/spine.db` · `receipts/receipts.db` · `events.jsonl` · `action-audit.jsonl` · `approval-log.jsonl` · genome `ledger.jsonl` | [LIVE] | [OBS] |
| **Telegram cockpit** | bot#1 `_ops/budget/approval_channel.py` (تأیید خصوصی) · bot#2 `_ops/telegram_center/center.py` (فرمان گروه) + `live_commands.py` (/id /box /code /live /doctrine) | [LIVE] ۲ رباتِ زنده از ۹ | BOTS-REGISTRY [OBS] |
| **کالیبراسیونِ ادعا (Brier)** | arming order گروه ۰: `CORTEX_SELF_MONITOR`→self-claims.jsonl، `OCTOPUS_SELFKNOW_ACCURACY`→self-accuracy.jsonl — اولین Brier=0.293 (پروب) | [LIVE-طراحی، فلگها خاموش] | ARMING-ORDER-2026-07-29 [OBS] |

\* `self_awareness_pct=99.7` = پوششِ مستندسازیِ ماژول‌ها (module coverage)، نه ادعای پدیدارشناختی. با همین برچسب مصرف شود.

### ۳.۲ MOCK / visualization-only

| مسیر | نقش | وضعیت |
|---|---|---|
| `OCTOPUS/` (worlds, gallery-3d, mobile, admin-telegram) | گالری HTMLِ تصویرسازی (nociceptor، metabolic-loop، genome-ledger...) | [MOCK] static؛ داده از extractors [OBS] |
| `nervous-system/` | extract_*.py → *.js برای داشبوردها | نیمه‌زنده: extractorها واقعی‌اند، مصرف‌کننده HTML است [INFER] |
| `_octopus/` | کنترل‌پلینِ قدیمی (2026-07-18): config/state/queue/manifests | [DEAD-نسبت به runtime] — SOT: «فقط `_ops/` ارگانیسمِ زنده است» [OBS] |

### ۳.۳ DEAD / DORMANT (کد دارند، runtime اثر ندارند)

| مسیر | SOT verdict |
|---|---|
| `survival-gateway/` (LiteLLM+Postgres) | NOT DEPLOYED [OBS] |
| `4d_system/` runtime | INDEPENDENT research؛ فقط `core/metrics.py` توسط synapse importِ read-only می‌شود [OBS] |
| `octopus_core/` (event_bus/actuator v2) | PARTIAL — consumer ندارد [OBS] |
| `app/` (NBB control plane) | DESIGN — not connected [OBS] |
| `_launchpad/.../control-brain/` | DEAD [OBS] |
| ربات‌های #3..#9 (Ziman/Saba/Painting/Accounting/ControlBrain/Langar/4D) | DORMANT — خطرِ 409 در BOTS-REGISTRY ثبت شده [OBS] |

### ۳.۴ MISSING — آنچه مأموریت BODY می‌خواهد و در vault نیست

| مورد | نتیجه‌ی جست‌وجو | برچسب |
|---|---|---|
| Kuramoto / Schumann / Hilbert / SNR (filename) | جست‌وجوی `*kuramoto*`, `*schumann*`, `*math*`, `*sensor*`, `*self*model*`, `*heartbeat*`, `*trust*`, `*body*` → **هیچ تطابقی** | [MISSING][OBS] |
| body_state schema / tick DB | وجود ندارد | [MISSING] |
| آداپتورِ سخت‌افزار (antenna/IMU/mic/ELF) | هیچ شاهدی | [MISSING][OPEN] |
| SQLiteِ math observations | وجود ندارد (DBهای موجود: chrono/memory/spine/outcomes/receipts/rfc-verdicts/consent/funnel) | [MISSING] |
| reward از audit_labels (lookup table) | outcomes/verdict_recorder نزدیک است ولی جدولِ lookupِ برچسب ندارد | [OPEN] |

---

## ۴. CONTROL PLANEِ فعلی (مسیرهای واقعی)

```
مالک ──Telegram──▶ bot#2 center.py (گروه) ──┐
                    live_commands /id /box /code /live   │ intent.py → routing
مالک ──Telegram──▶ bot#1 approval_channel.py (خصوصی) ──▶ state/telegram/approvals/*.json
                                                         │ (callback_token، verdict durable)
پایین‌دست: approvals → cockpit-requests.jsonl (+cursor/lock) ──▶ wiring.py:1184 ──▶ organism beat
Heartbeat: organism.py beat ──▶ ORGANISM-STATE.json (تک‌منبع) + events.jsonl + telemetry/YYYY-MM-DD.json
Ledger: genome ledger.jsonl (append-only hash-chain: prev/hash) + spine.db + receipts.db
Gateِ پرریسک: money_gate / organ_gate / capability_gate / arm_gate + approval_fatigue (THROTTLE..CUTOFF)
Kill: STOP-ORGANISM · STOP-TG-CENTER · ACTIVATION-*.flag (فقط دستِ مالک)
```

دستورهای زنده‌ی تلگرام (center): `/id` `/eq` `/box` `/code` `/live` `/doctrine` + منوها
(approval bot: `/start /status /stop /resume /panic /budget /now /doctor /money /wiring /health ...` — نگاه به TELEGRAM-DEEP-SCAN-REPORT).

---

## ۵. درزهای اتصالِ بدن (attachment seams) — با شاهد

| # | درز | چرا امن است | شاهد |
|---|---|---|---|
| S1 | **`_ops/body/` تازه، با قراردادِ عینِ `synapse/`** | الگوی اثبات‌شده: flag پیش‌فرض‌خاموش، خروجی فقط به out/، trail در state/، cap روزانه، صفر-LLM، fail-closed، propose-only | sense.py docstring + SOT §synapse [OBS] |
| S2 | **دستورِ `/body` در `live_commands.py`** | افزودنِ یک head به handles/dispatch = پچِ کوچکِ مرکز، بدونِ دست‌زدن به policy | live_commands.py [OBS] |
| S3 | **tickهای بدن → `state/body/body-ticks.jsonl` + لنگرِ هفتگی در genome ledger (NOTE)** | با فرهنگِ ledger یکی است؛ ledger را اسپم نمی‌کند | الگوی synapse-trail + scheduler NOTE [OBS] |
| S4 | **ادغام در self-model از مسیرِ `state/cortex/self-model.json`** | self-model از قبل schema دارد (v1)؛ بدن یک بخشِ `body:*` اضافه می‌کند | self-model.json [OBS] |
| S5 | **reward فقط از `outcomes/verdict_recorder`** | درسِ C3: هیچ‌وقت trust را از روی اعتمادبه‌نفس ننویس؛ فقط outcomeِ پس از اعمال با مهرِ مالک | handoff §C3 + memory/gate.py [OBS] |

---

## ۶. یافته‌ی کلیدیِ Phase 0 — چرا بدن، synapse را کامل می‌کند

شاهد [OBS]: `_ops/state/synapse-trail.jsonl` پر است از ردیف‌های
`{"kind":"observation","degraded":true,"series_points":33,"delta":null}` (2026-07-28).
یعنی اندامِ SENSE کار می‌کند ولی **سریِ زمانی برای fit کردنِ SOG کم‌تراکم است** (MIN_SERIES_POINTS=20 با داده‌ی پراکنده‌ی رویدادمحور).
ریشه: ورودیِ synapse فقط `events.jsonl` است (رویدادمحور، گاه‌به‌گاه).
**راه‌حلِ طبیعی: بدن یک سریِ منظمِ cadence-دار (body ticks هر beat) تولید می‌کند →
همان سریِ متراکم، هم ورودیِ MathFilterِ بدن است هم بالاخره fitِ SOG را ممکن می‌کند.**
این دقیقاً «اتصالِ امنِ بدن» است: تولیدِ داده، نه تغییرِ تصمیم.

همچنین: phi-bootstrap artifact ثبت‌شده (handoff §ه): با ack_samples کوچک، phi=300.0 کاذب
→ درسِ طراحی برای بدن: **هر مقدارِ محاسبه‌شده با پنجره‌ی کوچک باید LOW_CONFIDENCE برچسب بخورد (SNR/evidence gate).**

---

## ۷. قوانینِ سختِ ریپو (از handoffها — برای همه‌ی فازها)

1. درختِ زنده است؛ سه پروسه کد را از دیسک می‌خوانند → اعمالِ کد **سریالی**، با بکاپ، assert count==1، compile قبل از نوشتن.
2. هر رفتارِ نو: **additive · flag-gated (پیش‌فرض خاموش) · fail-soft** (`flag()` در wiring.py:30).
3. `OCTOPUS-flags.cmd` توکنِ زنده دارد → هرگز dump/tail/echo نکن؛ فقط ویرایشِ بایت‌محور با حفظِ CRLF.
4. هرگز حذف نکن → انتقال به `_Archive/` / `_Duplicates/`. `git clean` ممنوع.
5. سوئیت: `python -X utf8 F:\backup\_ops\tests\run_all.py` — baseline قبل از تغییر ثبت و پس از تغییر پایین‌تر نباید بیاید.
6. ACTIVATION-*.flag فقط دستِ مالک. مسلح‌سازیِ فلگ فقط با جمله‌ی `OWNER_AUTH: ARM FLAG <نام>` (پروتکلِ ARMING-ORDER-2026-07-29).
7. ادعای «وصل نیست» فقط با reachability، نه grep. «نبودِ ❌» یعنی سبز نیست → عددِ صریحِ pass/fail بده.
8. رازها (OCTOPUS_CB_SECRET و...) را ایجنت نه می‌سازد نه می‌نویسد.
9. ارسالِ بیرونی و مصرفِ سهمیه‌ی پولی owner-gated است.
10. صفِ خالی، عددِ منفی و `None` شرافتمندانه‌اند؛ سبزِ دروغ ممنوع.

---

## ۸. FILE_INDEX (کلیدی — غیرجامع؛ جامع‌ترین نسخه = self-model.json با 352 ماژول)

| path | role | status | conf | notes |
|---|---|---|---|---|
| `_ops/organism.py` | main loop :8771 | LIVE | OBS | beat 16528 |
| `_ops/wiring.py` | wiring hub (~133KB) | LIVE | OBS | flag() خط 30؛ observerهای per-cycle |
| `_ops/cortex/cortex.py` | brain :8772 | LIVE | OBS | coherence 0.91 |
| `_ops/live/server.py` | cockpit UI :8773 | LIVE | OBS | |
| `_ops/synapse/sense.py` | SENSE organ (SOG روی events) | SHADOW/LIVE | OBS | الگوی بدن |
| `_ops/heart/sog_math.py` + `state/sim/PULSE-EQUATIONS-LOCKED.json` | قلبِ ریاضی | LIVE | OBS | anchors قفل |
| `_ops/chrono.py` + `state/chrono.db` | pacemaker + phi liveness | LIVE | OBS | CHRONO_PERIOD_S=60 |
| `_ops/identity_equations.py` | مگا-معادلات L,E,G,K,O | LIVE/flag-gated | OBS | تست دارد |
| `_ops/coherence.py` | order parameter r | LIVE | OBS | coherence_r در neural-schema |
| `_ops/cortex/self_model.py` + `state/cortex/self-model.json` | self-model v1 | LIVE | OBS | 352 ماژول |
| `_ops/doctor/` (self_knowledge, calibration, spectral, box/) | خودشناسی + falsif harness | LIVE | OBS | box/sensors.py موجود |
| `_ops/afferent/` | sensory bus | LIVE | OBS | every_n=1440 |
| `_ops/neural/` (bcm, hebbian, nociceptor, rhythm, circadian, consolidation, signal_hub) | لایه‌ی عصبی | LIVE | OBS | wire_*=true |
| `_ops/memory/gate.py` | trust levels | LIVE | OBS | C3 lesson |
| `_ops/outcomes/` (verdict_recorder, learning_gate, outcome_store) | reward-from-outcome | LIVE | OBS | outcomes.db |
| `_ops/budget/` (organ_gate, money_gate, approval_channel, approval_fatigue, circuit_breaker, drawdown_guard) | گیت‌ها + بارِ انسانی | LIVE | OBS | |
| `_ops/telegram_center/` (center, live_commands, intent, render, surface_policy) | cockpit گروه | LIVE | OBS | bot#2 |
| `_ops/state/events.jsonl` · `telemetry/*.json` · `ORGANISM-STATE.json` | تله‌متریِ خام | LIVE | OBS | ورودیِ بدن |
| `07 - Knowledge/genome-system/ledger/ledger.jsonl` | genome ledger (hash-chain) | LIVE | OBS | anchorِ بدن |
| `_ops/spine/` + `state/spine/spine.db` | event spine | LIVE | OBS | |
| `_ops/tests/run_all.py` | سوئیت | LIVE | OBS | baseline: 389 فایل (07-29) |
| `_ops/OCTOPUS-flags.cmd` | فلگ‌ها (+توکن‌ها) | LIVE/SECRET | OBS | هرگز dump نکن |
| `ARCHITECTURE-SOT.md` | SOT | DOC | OBS | ثبتِ فایل‌های نو لازم |
| `TELEGRAM-DEEP-SCAN-REPORT.md` · `_ops/BOTS-REGISTRY.md` | نقشه‌ی ربات‌ها | DOC | OBS | ۲ رباتِ زنده |
| `OCTOPUS/` ، `nervous-system/` | visualization | MOCK | OBS | |
| `_octopus/` | کنترل‌پلینِ قدیمی | DEAD | OBS | |
| `octopus_core/` · `survival-gateway/` · `4d_system/` · `app/` · `_launchpad/` | dormant | DEAD/PARTIAL | OBS | |

---

## ۹. پیشنهادِ ثبت در ARCHITECTURE-SOT.md (نیازمندِ verdictِ مالک — اعمال نشده)

```
| BODY sense+math organ | `_ops/body/` (پیشنهادی، Phase B) | flag: OCTOPUS_WIRE_BODY (پیش‌فرض ۰) | SHADOW تا verdict |
| body ticks | `_ops/state/body/body-ticks.jsonl` | append-only | Phase C |
| body telegram card | live_commands: /body, /بدن | read-only از state | Phase D |
| docs | `docs/architecture/*`, `docs/math/EQUATION-REGISTRY.md` | DOC | این پک |
```

پایانِ گزارشِ Zone A — READY_FOR_MERGE_A
