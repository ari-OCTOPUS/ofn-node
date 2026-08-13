---
type: architecture
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, source-of-truth]
created: 2026-07-18
updated: 2026-08-08
---

# ARCHITECTURE-SOT — نقشه‌ی منبعِ حقیقتِ اجرایی (Source of Truth)

> Verdict 2026-07-18 integration-debug: این فایل کانونی‌ترین مرجع برای اینکه
> بدانی برای هر کار، کدام فایل/دایرکتوری canonical است.
> هر تغییری در معماری باید این‌جا هم به‌روز شود.

## 🎯 اصلِ بنیادین

پروژه‌ی اختاپوس چند لایه دارد، ولی **فقط `_ops/` ارگانیسمِ زنده‌ی اجرایی است**.
بقیه‌ی لایه‌ها یا dormant هستند، یا visualization، یا independent research.
هر تغییری که قرار است runtime را تحت تأثیر قرار دهد، باید در `_ops/` باشد.

## 📍 Source of Truth بر اساسِ concern

### ۱. ارگانیسمِ زنده (Live Organism)
| concern | canonical | جایگزین/دوم‌دار | وضعیتِ دوم‌دار |
|---------|-----------|-----------------|----------------|
| **main loop** | `_ops/organism.py` (port 8771) | `04 - Architect System/scripts/organism-watchdog.ps1` | DIVERGENT TWIN — split-brain note R-19. آن فقط supervisor است. |
| **state snapshot** | `_ops/state/ORGANISM-STATE.json` | - | تک‌منبع |
| **events log** | `_ops/state/events.jsonl` | - | append-only |

### ۲. مغز (Brain / Cognition)
| concern | canonical | دوم‌دار | وضعیت |
|---------|-----------|--------|-------|
| **controller brain** | `_ops/cortex/cortex.py` (port 8772) | - | LIVE (coherence 0.91) |
| **LLM routing** | `_ops/cortex/model_router.py` | `4d_system/llm/router.py`, `survival-gateway/` | هر دو DORMANT — canonical فقط model_router |
| **local LLM** | `_ops/cortex/local_llm.py` (Ollama) | - | تک‌منبع |
| **doctor self-knowledge** | `_ops/doctor/self_knowledge.py` | `04 - Architect System/learning-engine/app/doctor_lite.py` | دومی standalone، NOT wired |

### ۳. بودجه و متابولیسم (Budget)
| concern | canonical | دوم‌دار | وضعیت |
|---------|-----------|--------|-------|
| **budget definitions** | `_ops/budget/budgets.yaml` | - | تک‌منبع (verdict-خورده) |
| **budget gate** | `_ops/budget/organ_gate.py` | - | تک‌منبع |
| **NBB Control Plane** | - | `app/src/nbb_cp/` | DORMANT — فاز ۴-۵ آینده، هنوز وصل نشده |

### ۴. تلگرام (Telegram)
| concern | canonical | دوم‌دار | وضعیت |
|---------|-----------|--------|-------|
| **private approval channel** | `_ops/budget/approval_channel.py` (bot #1) | - | LIVE |
| **group command centre** | `_ops/telegram_center/center.py` (bot #2) | - | LIVE |
| **creator studio (Saba)** | `03 - Projects/اونلی فنز/studio/saba_studio.py` | - | DORMANT (token ساخته‌نشده) |
| **bot registry** | `_ops/BOTS-REGISTRY.md` | - | مرجع |

### ۵. پاها (Legs / Business)
| concern | canonical | دوم‌دار | وضعیت |
|---------|-----------|--------|-------|
| **wiring hub** | `_ops/wiring.py` (133KB) | - | تک‌منبعِ اتصالِ پاها |
| **legs** | `_ops/legs/*.py` | - | هر پا یک ماژول |
| **Project-F (Saba)** | `03 - Projects/اونلی فنز/` | - | standalone، فاز برنامه‌ریزی |

### ۶. حافظه و داک (Memory / Docs)
| concern | canonical | دوم‌دار | وضعیت |
|---------|-----------|--------|-------|
| **genome ledger** | `07 - Knowledge/genome-system/ledger/ledger.jsonl` | - | append-only hash-chain |
| **memory** | `_memory/` | - | docs |
| **architecture maps** | `06 - Architecture Maps/` | - | docs |

### ۷. Visualization / Dashboards
| concern | canonical | دوم‌دار | وضعیت |
|---------|-----------|--------|-------|
| **live cockpit UI** | `_ops/live/server.py` (port 8773) | - | LIVE |
| **HTML worlds** | `OCTOPUS/worlds/` | - | static visualization |

## 🚫 دایرکتوری‌های NOT wired (DORMANT)

این‌ها کد دارند ولی در runtime فعال نیستند. هر تغییری در آن‌ها **تأثیری در ارگانیسم زنده ندارد**.

| دایرکتوری | نقشِ اسمی | وضعیتِ واقعی | علامت‌گذاری |
|-----------|-----------|--------------|-------------|
| `_launchpad/second-brain-live/control-brain/` | second brain | DEAD — فقط docs و batch files | DEPRECATED.md |
| `survival-gateway/` | LiteLLM proxy | NOT DEPLOYED — docker-compose موجود ولی راه‌نرفته | DEPRECATED.md |
| `4d_system/` | research brain | INDEPENDENT — standalone experiment، wired نیست | DEPRECATED.md |
| `octopus_core/` | rebuild v2 | PARTIAL — event_bus/actuator موجود ولی consumer ندارد | (توضیح در README) |
| `app/` | NBB Control Plane | DESIGN — 12 invariant، 207 تست، ولی not connected | (توضیح در README) |

## 🔌 سیم‌کشیِ اصلی (Bridge Files)

این فایل‌ها backboneِ اتصالِ اجزاست. همه در `_ops/state/`.

| فایل | نویسنده | خواننده | نقش |
|------|---------|---------|-----|
| `cockpit-requests.jsonl` + `.cursor` + `.lock` | approval_channel | wiring.py:1184 | تلگرام → organism |
| `telegram/center-config.json` | telegram_center | telegram_center, cortex | وضعیتِ گروه |
| `telegram/approvals/*.json` | approval_channel | telegram_center | verdictها |
| `ORGANISM-STATE.json` | organism.py | همه | status snapshot |
| `events.jsonl` | events.py | cortex consumers | event log |
| `saba-bridge.jsonl` | (آینده) saba_brain | (آینده) wiring beat | Saba → organism (scaffold) |

## 📐 قواعدِ تغییر

1. **هر تغییری که قرار است runtime را تحت تأثیر قرار دهد، در `_ops/` باشد.**
2. **هر فایلِ canonical جدید** باید در این فایل ثبت شود.
3. **هر دایرکتوریِ dormant** باید `DEPRECATED.md` داشته باشد که به canonical اشاره کند.
4. **هیچ کدِ تکراری نساز** — اول این فایل را بررسی کن که آیا canonical موجود است.
5. **معماری به‌صورتِ incremental تکامل می‌یابد** — این فایل snapshotِ امروز است.

## 🧬 ثبتِ ۲۰۲۶-۰۷-۲۴ — اندامِ synapse (additive، پیش‌فرضِ خاموش)

| concern | canonical | وضعیت |
|---------|-----------|-------|
| SENSE (SOG روی تله‌متریِ خودِ ارگانیسم) | `_ops/synapse/sense.py` | SHADOW — فلگ `SYNAPSE_ENABLED` خاموش؛ خروجی فقط `_ops/synapse/out/`؛ importِ read-only از `4d_system/core/metrics.py` |
| مانیتورِ trajectory (P3) | `_ops/synapse/trajectory_monitor.py` | SHADOW — فلگ `TRAJECTORY_MONITOR_ENABLED` خاموش؛ wiring به event_bridge = tapِ مالک |
| سیاستِ egress (P1) | `_ops/synapse/egress_policy.py` | policy-as-data — enforce/wiring = tapِ مالک؛ deny-by-default |
| تست‌های synapse | `_ops/tests/test_synapse_sense.py` | [UNKNOWN تا اولین اجرای pytest] |

قاعده: هیچ‌کدام از این‌ها در runtimeِ فعلی اثر ندارند (فلگ‌ها خاموش). هر wiring آینده
در همین فایل ثبت و با verdictِ مالک انجام می‌شود.

## 🧬 ثبتِ ۲۰۲۶-۰۷-۲۵ — دکتر، dedupe، و مغزهای پولی

### ۰) VQ-SCORER-001 — دستهٔ مسکونیِ مستقیم (closed 2026-07-25)
| concern | canonical | وضعیت |
|---------|-----------|-------|
| لیدِ مسکونیِ مستقیم ($715–$15k) | `_ops/legs/lead_scorer.py` → `residential_repaint_direct` | FLAG-GATED: `OCTOPUS_LEAD_DIRECT_RESIDENTIAL=1`؛ ۵ تستِ نو. base=50+18+8=76 → draft. |

### ۰b) LIVE path 2026-07-25 — هویت / جعبه / هم‌کدنویسی / romajan
| concern | canonical | flag |
|---------|-----------|------|
| مگا-معادلات هویت (L,E,G,K,O) | `_ops/identity_equations.py` | `OCTOPUS_WIRE_IDENTITY_EQ` |
| نقشهٔ جعبه‌سیاه‌ها | `_ops/blackbox_map.py` | `OCTOPUS_WIRE_BLACKBOX_MAP` |
| هم‌کدنویسی propose-only | `_ops/collab_coding.py` | `OCTOPUS_WIRE_COLLAB_CODING` |
| دستورهای تلگرام `/live /id /box /code` | `_ops/telegram_center/live_commands.py` + `center.py` + `intent.py` | always routed; organs flag-gated |
| پروب‌های romajan→C6 | `_ops/c6_probes.py` (`romajan_new_claims`, `romajan_engine_idle`) | `OCTOPUS_WIRE_ROMAJAN_PROBES` (default 0) |
| C6 producer schema v2 | `_ops/c6_producer.py` | `OCTOPUS_WIRE_C6_PRODUCER=1` |
| طراحی romajan wiring | `_program-deliverables/romajan-c6-wiring-2026-07-25/DESIGN.md` | design |

### الف) باگِ بسته‌شده: شرطِ dedupe در `Doctor.run_cycle` معکوس بود
`rfc.rfc_id not in _before_ids` یعنی هر RFCِ **تازه** کوتاه می‌شد، پس `chamber` /
`run_sandbox` / `_run_box_cycle` / `_evolve_rfc` / `_chord_shadow` و مهم‌تر از همه
**`submit_for_approval`** برایش اجرا نمی‌شد — عملاً هیچ کارتِ تأییدی به مالک نمی‌رسید.
علتِ مشترکِ ۴ فایلِ قرمزِ سوییت (evolution_wiring, box_wiring, chord_shadow, calibration).

**مرزِ کانونی (قاعدهٔ نو):** روی dedupe-hit فقط مسیرِ «تصمیمِ نو» می‌خوابد —
`chamber`, `run_sandbox`, `_evolve_rfc`, `_chord_shadow`, `submit_for_approval`.
ناظرهای **per-cycle** (امروز فقط `Box`) تیک می‌زنند. دلیل: شاهدِ خودِ T8 «۸ RFC با متنِ
یکسان» است، یعنی در تولید تکرارِ گلوگاه قاعده است و early-returnِ کامل حلقهٔ box را یخ
می‌زد. `chord` استثناست چون `shadow_assess(log=True)` می‌نویسد و تکرارش همان نویزی است
که dedupe جلویش را می‌گیرد. **هر ناظرِ per-cycleِ آینده باید در همین بند ثبت شود.**

### ب) استثناهای اعلام‌شده از قاعدهٔ additive + flag-gated + default-off
| مورد | چرا استثنا | دامنهٔ انفجار | وضعیت |
|---|---|---|---|
| T1 `severity` غیرعددی | bugfixِ مستقیم (`int('متوسط')` → ValueError) | صفر رفتارِ نو | پذیرفته |
| T3 ثبتِ علتِ شکستِ لِگ | فقط observability؛ هیچ شاخهٔ تصمیمی آن را نمی‌خواند | write به `state/legs/*` + یک ردیفِ selfheal | رأیِ باز: **VQ-T3-001** |
| T8 dedupeِ RFC | رفعِ نقص، نه قابلیتِ نو: صف ۸ کارتِ یکسان می‌ساخت | RFCِ نو mint نمی‌شود؛ هیچ حذفی نیست | رأیِ باز: **VQ-T8-001** |
| T8 `_reconcile_input_validity` | برچسبِ `stale-input`؛ هرگز delete نمی‌کند، fail-soft | statusِ RFCهای باز + صفِ نمایشِ مالک | رأیِ باز: **VQ-T8-001** |

### ج) مغزهای پولی — وضعیتِ *config*، نه رفتارِ زنده
با رأیِ مالکِ ۲۰۲۶-۰۷-۲۵ سه فلگ در `_ops/OCTOPUS-flags.cmd` به ۱ رفتند:
`OCTOPUS_GOVERNOR_USE_ROUTER`, `OCTOPUS_HEART_DOCTOR_USE_ROUTER`,
`OCTOPUS_DOCTOR_SELFKNOW_PAID`. فایل gitignored است، پس این تغییر در تاریخچهٔ git نیست
و تنها ردش همین بند است. فلیپ بایت‌سطح بود: ۳ بایت، طولِ ۱۳۹۵۳ و CRLF=416 دست‌نخورده،
loneLF=0، و `OCTOPUS_WIRE_C6_PRODUCER` همچنان ۰.
**اثر فقط با restart** — تا آن لحظه پروسهٔ زنده با مقادیرِ قدیم کار می‌کند.
هر سه reader تنها env را می‌خوانند (بدون arm-token/capability)، پس سقف‌های پایین‌دستی
تنها ترمزند: `cap_monthly=30 AUD`، burstِ روزانه `2 AUD`، Fugu `cap_monthly=100`.
baselineِ پیش از فلیپ برای پایش: `paid-calls.jsonl`=۲ خط، `fugu-quota` used_total=۲،
`self-knowledge.jsonl`=۹ خط.

### د) چه چیزی هنوز دروغ می‌گوید
1. **«سوییت سبز» دیگر ۲۹۷/۲۹۷ نیست.** بعد از فلیپ، `test_paid_router_dark_config`
   سه چکِ «آخرین assignment باید صفر باشد» را قرمز می‌دهد → **۲۹۶/۲۹۷**. آن گارد
   وضعیتِ *دیپلوی* را pin کرده، نه رفتار را. تا VQ-GUARD-001 بسته نشود، هر گزارشِ
   «همه سبز» دروغ است.
2. **T1/T3/T4/T8 فقط در تست اثبات شده‌اند، نه در بدنِ زنده** — restart انجام نشده.
   پس «۳۴۸ خطای digest بسته شد» و «RFCهای کهنه stale شدند» ادعای کد است، نه مشاهده.
3. **علتِ ریشه‌ایِ لِگِ lead-نقاشی ناشناخته است** — فقط می‌دانیم chrono آن را
   `phi-timeout:no-ack` می‌بیند؛ *چرا* ack نمی‌دهد هنوز معلوم نیست.
4. **T2 (`OCTOPUS_HONEST_OUTCOMES`) خاموش است** — تولید هنوز قاعدهٔ قدیمِ شمارشِ
   closure را اجرا می‌کند؛ کد آماده است، درمان فعال نیست.
5. **T6 فقط تحلیلِ مقدماتی است** — SIM آفلاین و hash-check انجام نشده.

### ه) دیباگِ زنده پس از ریستارتِ ۱۴:۱۴:۲۵ — شش باگ + دو مکانیزمِ کانونی
اثباتِ زندهٔ اهداف: T1 (۳۶۷ کرش تا ۱۴:۱۲:۴۷، صفر بعدش، **دایجست واقعاً ارسال شد** چون
`digest-nudge.json` فقط داخلِ `if sent:` نوشته می‌شود) · T4 (جفتِ قبل/بعد: `live=0.0,
gate0=true` → `live=raw=-0.027143, gate0=false`) · T5 (`self-knowledge` v10،
`source=llm:secondary`، `llm_calls=2`) · T8-dedupe (چرخهٔ ۱۴:۱۵:۵۰ به‌جای mintِ RFCِ نهم،
همان RFC-b23935ef را بازاستفاده کرد) · T3 نیمه (مسیرِ phi زنده؛ مسیرِ استثنا هنوز اجرا نشده).

**مکانیزمِ کانونیِ ۱ — پنجرهٔ bootstrapِ phi، نه کادنسِ حلقه.**
`phi=300.0` یک عددِ واقعی نیست؛ **دقیقاً سقفِ `p_later=1e-300`** است. با ۲ ack تنها یک
فاصله داریم → `var=0` → `std` به کفِ `0.1×mean` می‌افتد → یک سکونِ ~۲×mean کافی است تا
`z>10` و لِگ «مرده» اعلام شود. چون هر ری‌استارت پنجرهٔ ۲-نمونه‌ای را از نو می‌سازد، این
**در هر بوت** تکرار می‌شود (۶۶ ری‌استارتِ self-heal، ۱۰۰٪ روی lead-naghshi، همه با
`phi=300.0`) و بعد خودش می‌خوابد: در ۱۵:۰۵:۴۹ همان لِگ بدونِ هیچ فیکسی `alive` شد چون
ackها جمع شدند. پس thrash فقط در پنجرهٔ bootstrap رخ می‌دهد — ولی همان کافی است که
`legs` را به stress ببرد و ارگانیسم را در ترس نگه دارد.
**نشانهٔ تشخیصی: `phi=300.0` با `ack_samples` کوچک = آرتیفکتِ سنجش، نه مرگِ لِگ.**

> **دو تصحیحِ ثبت‌شده — بخوان تا اشتباهِ من را تکرار نکنی:**
>
> **(الف) ۱۵:۰۶ — تصحیحی که خودش غلط بود.** آن‌جا نوشتم «حلقهٔ بیرونی ~۹.۵ دقیقه» غلط
> است و ۶۰.۹s/beat را جایش گذاشتم. استدلالم این بود که استالِ ۱۴:۲۵→۱۴:۳۵ آرتیفکتِ بارِ
> ۱۴ ایجنتِ راستی‌آزماییِ خودم بود.
>
> **(ب) ۱۶:۲۵ — تصحیحِ تصحیح، با شاهدِ ابزارِ خودِ ارگانیسم.** ادعای اولیه **درست بود** و
> من دو حلقهٔ متفاوت را قاتی کردم:
> · **نبضِ pacemaker** = `CHRONO_PERIOD_S=60` → همان ۶۰.۹s که اندازه گرفتم. درست، بی‌ربط.
> · **حلقهٔ کاریِ بیرونی** = `arbiter.effective_period_s`، که الان **۹۰۰ ثانیه** است با
>   `driver="brake:cardiac"`، چون `cardiac.budget` تمام شده (`spent=288/daily_cap=288`,
>   `remaining=0`, `depleted=true`) و ارگانیسم در حالتِ resting است. سرعتِ *طراحی‌شده*
>   `bio_rhythm.period_s=42.4s` است — یعنی زیرِ ترمز ۲۱ برابر کندتر می‌شود.
> شاهدِ قطعی از ابزارِ نوِ `legs_diag`: `silence_ms=578098` (≈۹.۶ دقیقه) برای لِگ، در
> پنجره‌ای که ایجنت‌های من **بیکار** بودند — یعنی یک ackِ لِگ در هر دورِ حلقهٔ بیرونی.
>
> **درسِ دوگانه:** (۱) قبل از نسبت‌دادنِ کندی به بارِ خودت، از سیستم بپرس چه عددی را
> هدف گرفته (`arbiter.driver` همان‌جا نوشته بود `brake:cardiac`). (۲) «۶۰ ثانیه» و «۹.۶
> دقیقه» هر دو درست‌اند و به **دو حلقهٔ مختلف** تعلق دارند؛ هر ادعایی دربارهٔ «کادنسِ
> ارگانیسم» باید بگوید کدام حلقه. ابزاری که برای دیدنِ لِگ ساختم همان چیزی بود که این
> را حل کرد — نه استدلالِ بیشتر.

**مکانیزمِ کانونیِ ۲ — یالِ گرافِ رویداد فقط از «خطا» می‌آید:** پس ارگانیسمِ سالم گرافِ
بی‌یال دارد و سنسورِ طیفی آن را «σ≈1/critical» می‌خواند. منبعِ ۸ RFCِ یکسان. **هر
معیارِ ساختاری که روی `build_event_graph` بنشیند باید گاردِ گرافِ دژنره داشته باشد.**

فیکس‌ها (کامیت `66728db`، سوییت ۲۹۷/۲۹۸): گاردِ دژنرهٔ `spectral_mine` · persistِ
`created_ts` · تحمّلِ صادقِ phi پشتِ `OCTOPUS_CHRONO_PHI_HONEST` (خاموش=بایت‌به‌بایت) ·
`legs_diag` در snapshot · Gate-0 در `heart/shadow.py` حالا Δ>0 می‌خواهد (قبلاً Δِ منفی
هم بازش می‌کرد) · سه فلگِ پولی در `wire_summary`.

**عمداً دست‌نخورده، با دلیل:** مصرفِ سهمیه روی شکست = عمدی و مستند (`fugu_quota.py:2`
attempt-counted) · تایم‌اوتِ ۴۵s = knobِ `PAID_HTTP_TIMEOUT_S` که امروز تنظیم شد ·
بریکرِ Fugu از قبل هست (۸ شکستِ پیاپی → auto STOP-FUGU) · `Pacemaker.ack()` عمداً
بی‌caller می‌ماند — ackِ خودکار لِگِ واقعاً مرده را زنده اعلام می‌کند.

**قاعدهٔ نو:** هیچ فیکسی روی پروسهٔ در حالِ اجرا اثر ندارد. امروز اثبات شد:
`organ_dialogue.py` در ۱۲:۱۵ فیکس بود ولی `ValueError` تا ۱۴:۱۲:۴۷ ادامه داشت چون
ماژولِ کهنه در `sys.modules` مانده بود. **«فیکس شد» ≠ «زنده شد»؛ فقط ریستارت تحویل می‌دهد.**

## 🧬 ثبتِ ۲۰۲۶-۰۷-۲۸ — معیارِ دقتِ خودمدل (C3) + بیداریِ SENSE (C8)، additive، پیش‌فرضِ خاموش

دو قدمِ نخست به‌سوی «خود-اصلاحیِ صادق» (نردبانِ AGI: C3/C8 → C4). هر دو شکافِ
«حاضر ولی نه سنجش‌پذیر» از بازسنجیِ ۲۰۲۶-۰۷-۲۵ را می‌بندند.

| concern | canonical | وضعیت |
|---------|-----------|-------|
| معیارِ دقتِ خودمدل (C3) | `_ops/doctor/self_accuracy.py` | SHADOW — فلگ `OCTOPUS_SELFKNOW_ACCURACY` خاموش؛ wiring در `self_knowledge.run()`؛ خروجی append-only به `_ops/state/doctor/self-accuracy.jsonl` (سریِ زمانیِ صداقتِ C3) |
| بیداریِ SENSE (C8) — wiring | `wiring.synapse_beat()` ← `organism.py` tick | SHADOW — فلگ `OCTOPUS_SYNAPSE_ENABLED` خاموش؛ سه ماژولِ synapse حالا برای اولین‌بار از رانتایم صدا زده می‌شوند (تا امروز: صفر ادغام) |
| سریِ زمانیِ صداقتِ C8 | `_ops/synapse/sense.py::_append_trail` | هر چرخه ردیفی با `{ts, cpm, self_referential, gate0, delta, kind}` به `_ops/state/synapse-trail.jsonl` (شکافِ «sinkها self_referential نمی‌نوشتند» از ۰۷-۲۵) |
| تست‌های C3 | `_ops/tests/test_self_accuracy.py` | ۱۳ چک سبز؛ ثبت در `run_all.py` |
| تست‌های C8 (وصل‌کردن + trail) | `_ops/tests/test_synapse_beat.py` + `test_synapse_sense.py` (۳ چکِ trailِ نو) | ۷ + ۲۰ چک سبز؛ ثبت در `run_all.py` |

**چرا این دو با هم:** خودمدلِ صادق (C3) پیش‌نیازِ جراحیِ ایمن است، و حسِ Δ خودِ
ریاضیِ ارگانیسم (C8) خوراکِ همان پچ است. تا امروز ارگانیسم می‌توانست با اطمینانِ کامل
غلط بگوید (دروغِ ۰۷-۲۵: ۱ لِگ به‌جای ۴) و حسِ خود-ارجاعی نداشت — یعنی آمادهٔ جراحیِ کور بود.

**قاعدهٔ دوگانهٔ فلگ (compat):** `sense.flag_on()` هر دو نامِ `OCTOPUS_SYNAPSE_ENABLED`
(canonical، با prefixِ کلی) و `SYNAPSE_ENABLED` (backward-compat با README/SOT قدیمی)
را می‌پذیرد. اثر فقط با restart. هر wiring آینده (وصل‌کردنِ trajectory_monitor به
event_bridge = L3 نردبان) با verdictِ مالک انجام می‌شود.

## 🧬 ثبتِ ۲۰۲۶-۰۷-۲۹ — دکترِ اختاپوس (OCTOPUS-DOCTOR + os_v1 + doctor_link)، additive، پیش‌فرضِ خاموش

نصبِ دو بستهٔ نشست‌های ابری روی درخت (۲۲۱ تستِ سبز **روی همین لپ‌تاپ**) + پلِ
تلگرامِ آن‌ها به مرکزِ زنده. حلقهٔ هدف: چت/پتِ مالک در تلگرام → کارتِ نیت → worktree
→ سوئیت → کارتِ دیف → رأی → merge — با سه قفلِ سری روی merge.

| concern | canonical | وضعیت |
|---------|-----------|-------|
| چشم/ذهن/انگشت/مغز/صدای دکتر | `OCTOPUS-DOCTOR/doctor/` (والتِ Obsidian = حافظه‌اش) | نصب‌شده؛ `cli.py round` فقط‌خواندنی روی `_ops` (اولین اسکنِ زنده: beat 17352، ۶ یافتهٔ خودکار)؛ مغز بی‌کلید fail-closed؛ `test_doctor.py` ۱۴۸/۱۴۸ |
| کتابخانهٔ OS (سنجهٔ صادق/EFE/سکوت/mission_runner) | `_ops/os_v1/` | library-only، بدونِ فلگ؛ `mission_runner` حالا `env_root_key` دارد — سوئیتِ worktree با pinِ `ORG_ROOT` به خودِ worktree اجرا می‌شود (الگوی `code_autonomy.py:146`؛ بدونِ آن، گیتِ `day --live` همیشه درختِ زنده را می‌سنجید)؛ `test_os_v1.py` ۷۳/۷۳ |
| پلِ کارت/رأیِ دکتر ↔ تلگرام | `_ops/telegram_center/doctor_link.py` + دو هوکِ افزایشی در `center.py` (دنبالهٔ `beat` + پیش‌گیریِ `_handle_callback`) | **LIVE از ۰۷-۲۹** (رأیِ مالک VQ-DR-001؛ کارتِ تست message_id=323 + رأیِ برگشتی verdict=True)؛ فلگ `OCTOPUS_WIRE_DOCTOR_TG=1`؛ outbox با clientِ خودِ مرکز می‌رود (اتصالِ دومِ تلگرام باز نمی‌شود)؛ رأیِ سه‌تکهٔ `ok|no:gate:mission` قبل از fallbackِ approval جدا می‌شود؛ صفر import از پکیجِ دکتر (نامِ `doctor` ملکِ `_ops/doctor` می‌ماند)؛ `test_doctor_link.py` ۱۸/۱۸ + ثبت در `run_all.py` |

**سه قفلِ merge دکتر (سری):** رأیِ ✅ روی کارتِ دیف → `--apply` (نه dry-run) →
`OCTOPUS_DOCTOR_MAY_MERGE=1` (تنظیم **نشده** و بدونِ رأیِ مالک تنظیم نمی‌شود).
`day --live` تا رأیِ مالک روشن نمی‌شود — `run_all` تست‌هایی دارد که فایلِ زندهٔ
STOP می‌سازند؛ pinِ `ORG_ROOT` این را به worktree محدود می‌کند ولی اولین اجرای
زنده باید زیرِ چشمِ مالک باشد. اثرِ فلگ فقط با ری‌استارتِ TG-center.

## 🧬 ثبتِ ۲۰۲۶-۰۷-۳۰ — پلِ اقدام، سطحِ تلگرام، ساختِ خود (چهار رأیِ صریحِ مالک)

**درسِ کلیدیِ این روز: چیزی گم نبود، صداکننده گم بود.** پلِ اقدام سه قطعه‌اش از
قبل تست‌شده روی دیسک بود و صفر صداکنندهٔ تولیدی داشت. قبل از ساختنِ ماژولِ نو،
`resolve`/`prepare_records`/`enqueue` ِ موجود را با **AST** بگرد.

### الف) canonical ِ نو

| concern | canonical | وضعیت |
|---|---|---|
| پلِ اقدامِ SGC (prereg → mission → عمل → رسید) | `_ops/goal_action_bridge.py` | **LIVE** — فلگ `OCTOPUS_WIRE_ACTION_BRIDGE=1` (VQ-ACTION-BRIDGE-ARM-001)؛ اولین اجرای واقعی روی هدفِ پول افتاد و درست به A3/OWNER_GATE رفت، executor صدا نخورد |
| envelope و گذارِ قانونیِ mission | `_ops/mission_contract.py` | canonical؛ Mission Genome ِ ۱۲-وضعیتی هنوز ناسازگار — VQ-MISSION-RECONCILE-001 |
| سیمِ exact-row | `unified_control.pipeline.prepare_records` | حالا صداکننده دارد (`test_cycle.run`)؛ ردیفِ journal شناسهٔ prereg را حمل می‌کند |
| مسیریابیِ خروجیِ تلگرام | `_ops/telegram_center/surface_router.py` + `surface-routing.json` | **LIVE** — `OCTOPUS_TG_SPLIT_V1=1`؛ صداکننده `Center._route_send` |
| سیاستِ ورودیِ تلگرام | `_ops/telegram_center/input_surface_policy.py` | **LIVE** در `center.handle_update` |
| ماشینِ حالتِ HOLD/تحویل | `_ops/telegram_center/hold_policy.py` | **LIVE** — TG-HOLD-POLICY-LIVE (VQ-TG-HOLD-001) |
| کارتِ واحدِ مالک («مامور») | `_ops/owner_console/` | WIRED به Outer DM؛ گیت ۵ مالک باقی |
| مدلِ Task ِ پاها | `_ops/telegram_center/leg_tasks.py` | LIVE — ۴ وضعیت، ۴ دکمه، موتورِ read-only |
| هدایتِ کدنویسی از DM | `_ops/telegram_center/build_cmd.py` | LIVE — «بساز: …» → صفِ `code_brain` |
| پلهٔ محلیِ مغزِ کد ($0) | `code_brain._draft_via_local` (اولاما) | LIVE — knob `OCTOPUS_CODE_BRAIN_LOCAL_MODEL`، پیش‌فرض `qwen2.5:latest` |

### ب) بازنشسته‌شده

| مسیرِ قبلی | مقصد | چرا |
|---|---|---|
| `_ops/os_v1/` (کلِ بسته، ۹ ماژول) | `_Archive/_ops-retired-2026-07-30/os_v1/` | هرگز روی `sys.path` نبود ⇒ هیچ import ای به آن حل نمی‌شد؛ `mission_runner` اش تکرارِ `telegram_center/mission_runner.py`. **منتقل شد با `git mv`، حذف نشد**؛ `DEPRECATED.md` با جدولِ جایگزین و فرمانِ برگشت. ردیفِ ۲۶۲ همین سند دیگر معتبر نیست |

### پ) گاردهای ساختاری که امروز اضافه شدند

- **گاردِ ناوردیِ نحوی برای بازنویسیِ فایل** (`code_brain._defs_kept`): هر
  `def`/`class` ِ سطحِ ماژول باید در خروجی بماند. گاردِ نسبتِ بایت **کافی نیست** —
  پروبِ واقعی نشان داد مدل یک تابع را انداخت و بایتِ بیشتری تولید کرد.
- **`harness` حالا `OCTOPUS_STATE_DIR` را pin می‌کند** (VQ-HARNESS-STATEDIR-001):
  بدونش `MemoryStore()` در `memory.db` ِ **زنده** می‌نوشت.
- **گاردِ رشته‌ای ممنوع وقتی همان رشته دو بار در فایل است** — سنجهٔ رفتاری.
- **دفاعِ لایه‌ای بی‌سنجه بی‌صدا می‌پوسد** — هر لایه سنجهٔ خودش را لازم دارد.

⚠️ **دو تلهٔ ابزار که امروز خورد شد:** (۱) ابزارِ ویرایش line-ending ِ کلِ
`code_autonomy.py` را LF→CRLF کرد و دیف را به یک هانکِ کلِ-فایل تبدیل کرد —
روی فایلِ مشترک یعنی لِه‌شدنِ هانکِ بیگانه؛ بعد از هر ویرایش CRLF/LF را بسنج.
(۲) backtick داخلِ رشتهٔ bash، محتوا را می‌بلعد — متنِ بلند فقط با ابزارِ فایل.

## 🧬 ثبتِ ۲۰۲۶-۰۷-۳۱ — موجِ «اتصال، نه اندامِ نو» (durability + حافظه در تصمیم + پروندهٔ مأموریت)

مبنا: سندِ مقایسهٔ `06 - Architecture Maps/OCTOPUS-VS-FRONTIER-AGENT-ARCHITECTURES-2026-07-31.md`
(حکم: قابلیت زیاد، اتصال کم). برنچ: `claude/stoic-bartik-d3edbd` — merge/فعال‌سازی = رأیِ مالک.

| جزء | مسیر | وضعیت |
|---|---|---|
| دفترِ idempotency/nonce ِ persisted | `goal_action_bridge._load_ledger/_load_nonces` + پارامترهای نوی `unified_control.pipeline.prepare_records` | **کد روی برنچ** — crash وسطِ چرخه دیگر عمل را دوباره اجرا نمی‌کند: replay = `NOOP` ِ صادق (نه رسیدِ دوم، نه missionِ failed ِ دروغ) |
| باگِ CONFLICT ِ idempotency | `action_bridge/idempotency.py` | **فیکس** — `split(":",1)` با action_id ِ دونقطه‌دار (`act:<sha>`) هرگز CONFLICT نمی‌داد؛ حالا `rsplit`. تستِ durability رو کرد |
| هم‌راستاسازیِ mission_contract | `_ops/mission_contract.py` | هانکِ uncommitted ِ درختِ زنده (task_id/project_id/tenant/scope/critical) عیناً کامیت شد — روی این برنچ هر `prepare_records` با TypeError می‌مرد (VQ-COMMIT-HANDOFF-001) |
| حافظه در نقطهٔ تصمیم | `_ops/memory/retrieval_router.py` ← مصرف در `goal_action_bridge` | فلگ `OCTOPUS_WIRE_MEMORY_DECISION` **خاموش، خارج از PAPER_FULL_FLAGS** — فقط narrowing: citation روی envelope + veto ِ `owner_fact` می‌بندد، هرگز باز نمی‌کند؛ خطای router زنجیره را نمی‌خواباند |
| پروندهٔ واحدِ مأموریت | `_ops/mission_kernel.py` | read-only — `timeline(cycle_id)` / `resume_status` / `fsck` روی پنج دفترِ SGC؛ عمداً نه FSM ِ نو نه store ِ نو؛ envelopeها حالا `cycle_id`/`prereg_id` حمل می‌کنند (join ِ بی‌حدس) |
| ریشهٔ VQ-STATE-WRITE-001 | `opslib.LockedJson.write` | retry ِ محدودِ `os.replace` (WinError 5) + breadcrumb ِ `<path>.replace-failed.json`؛ happy-path بایت‌به‌بایت همان؛ شکستِ دائمی همچنان fail-loud |
| صداقتِ اسناد | `action_bridge/integration.py` + دو `capability-manifest.json` | `IMPLEMENTED_NOT_INTEGRATED` → `INTEGRATED_FLAG_GATED` — رجیستری/self-model دیگر دربارهٔ صداکننده دروغ نمی‌خوانند |
| گاردِ drift ِ قرارداد | `_ops/tests/test_action_schema_drift.py` | دو کپیِ مستقلِ اعتبارسنجِ `action-request.v1` به هم پین شدند (شاملِ تنها تفاوتِ عمدی: scope ِ خالی) |

تست: ۵ سوییتِ نو (۳۳ چک) در `run_all` ثبت شد؛ سوییت‌های داخلیِ هر دو بسته + پلِ اصلی سبز.
⚠️ صادقانه: `unified_control/tests/test_pipeline.py` روی checkout ِ بدونِ `_ops/state` قرمز است
(هر سه بندش `prepare()` ِ دیسک‌خوان را صدا می‌زنند) — محیطی و پیش‌موجود، در manifest ثبت شد.

**موجِ دوم (همان روز) — نجات + قرمزهای اصیل:** run_all روی هر checkout ِ تازه ۶۰ قرمز داشت
چون ۴۳ تستِ ثبت‌شده و ~۵۰ ماژولِ وابسته فقط uncommitted روی درختِ زنده بودند → کامیتِ
نجاتِ `96602e7` (۱۰۷ فایل؛ اسکنِ secret تمیز؛ state/flags.cmd عمداً نه). شش قرمزِ اصیلِ
باقی‌مانده در `0bc55ed` بسته شد: گیتِ halt ِ جاماندهٔ `_hebbian_eventclock_beat` در wiring ·
کورِ اسکنرِ یتیم‌ها (رشتهٔ denylist ≠ صداکننده؛ `arm_gate` دوباره دیده می‌شود) · فنسِ ورودیِ
`code_brain` (الگوی debate_loop) + ثبتِ `tool_request` در inventory · `chat.type=private` در
فیکسچرهای TG-P2 · پنجرهٔ شکنندهٔ چکِ `qt` · قراردادِ جدیدِ مسیریابیِ streamها (غیاب=DM).
دو قرمزِ ساختاری تا merge+deploy می‌مانند: `test_orphan_scan` (اسکنِ عمدیِ REAL_VAULT) و
`test_paid_router_dark_config` (نیازمندِ `OCTOPUS-flags.cmd` ِ زندهٔ gitignored).

## 📱 ثبتِ ۲۰۲۶-۰۷-۳۱ (عصر) — ساختِ ۴موجهٔ منشورِ UI تلگرام (TG-UI-CHARTER، ۲۴ رأی + ۴ حکمِ پایانی)

مبنا: `_ops/telegram_contract/TG-UI-CHARTER-2026-07-31.md` (حاکم) + `MEGAPROMPT-TG-UI-BUILD-2026-07-31.md`.
دفترِ حذفی‌ها: `_ops/telegram_contract/REMOVED-BUTTONS-2026-07-31.md`.

| concern | canonical | نکته |
|---------|-----------|------|
| **capture یک‌ژسته** | `_ops/telegram_center/capture.py` | DM-only + dedup ِ message_id؛ بایگانی در `10 - Telegram processing/Raw/`؛ کلیدهای فرانت‌مترِ نو در Property Schema §۲.۲ |
| **یادآوری + بریف** | `_ops/telegram_center/reminders.py` + `brief.py` | سوار بر beat ِ ۳۰۰ثانیه‌ای؛ سکوتِ ۲۳–۷ معوق-نه-حذف؛ cursor فقط بعدِ ارسالِ موفق |
| **سؤال-از-vault** | `_ops/telegram_center/ask_vault.py` | ripgrep + مغزِ محلی $0؛ «منابع:» اجباری؛ `.agentignore` محترم |
| **Mini App** | `live/server.py:/miniapp` + `miniapp_gateway.py` (8774) + `run-miniapp-tunnel.ps1` | tunnel فقط 8774 (initData-گیت)؛ دکمه فقط با url ِ تازهٔ <۲۴h |
| **ماشینِ لید** | `_ops/legs/lead_pipeline.py` + `lead_research.py` + `lead_outbound_transport.py` + `outbound_worker.drive_outbound` | `LEAD_DAILY_SEND_CAP=10` (رأی مالک ۰۷-۳۱)؛ سقف قبل از settle؛ transport بی‌creds = NOT_ARMED |
| **مرور هفتگی / بودجهٔ سؤال** | `weekly_review.py` + `question_budget.py` | شنبه ۰۸+؛ ۳۰ سؤال/هفته ISO-week |
| **رسیدِ ارسال** | `_ops/tg_send_log.py` | سه‌حالتی `state ∈ sent/held/blocked` + `bot_role/surface` (canonical؛ `disposition=` alias) |
| **گیتِ ورودی گروه** | `input_surface_policy.py` | deny-by-default: هر اسلش‌کامندی DM-only؛ callback ِ گروه فقط `GROUP_CALLBACK_VERBS`؛ system/mirror = core_conversation نه پا |
| **منوها** | `center.py:COMMANDS` (۸، scope=all_private_chats) | منوی گروه خالی؛ منوی inner تک‌نویسنده (approval_channel، ≤۴) |

آشتیِ دو خط: merge ِ `d3b448a` (سخت‌سازیِ ایجنتِ موازی) با ارشدیتِ خطِ منشور — redact-اول، دکتر→DM، fallback→DM، 409-detector، prune، ledger-reanchor حفظ شد.
ratchet ِ `tg_send_audit`: absent ‏۱۷ → **۷** (baseline ِ خودکار). run_all: تنها قرمزِ مجاز `test_paid_router_dark_config` (checkout-only).

## 🛠 ثبتِ ۲۰۲۶-۰۷-۳۱ (عصر، خطِ ارشد) — موجِ ۰ پایداری +.instrument Hebbian (پلِ به EFE)

مبنا: `04 - Architect System/2026-07-31 MASTER-PLAN — OCTOPUS repair-and-complete`. **خطِ ارشد** در موازیِ خطِ تلگرام، روی دامنه‌ی خودش (state/neural/budget) — تلگرام دست‌نخورده.

| concern | canonical | نکته |
|---------|-----------|------|
| **W0.2 state-freeze** (VQ-STATE-WRITE-001) | `_ops/budget/opslib.py::LockedJson.write` | بازگشتِ نسخهٔ `0a303af` (که در merge `681907f` ضعیف شده بود): `os.fsync` قبل از replace + retry ِ ۵گانهٔ bounded + رسیدِ واقعی → `state/write-failures.jsonl` (مصرف‌کننده: snapshot blocker). WinError-5 حالا fail-loud است نه بی‌صدا. `test_state_write_loudness` ۶/۶ سبز. |
| **W2 instrument Hebbian** (پلِ به EFE) | `_ops/wiring.py::_emit_hebbian_observation` + `taxonomy.py` | لایهٔ Hebbian واقعی (`hebbian.py`) تا حالا فقط به `hebbian.json` می‌رفت (بن‌بست). حالا هر بستنِ پنجره یک رخدادِ `hebb.observation` در spine.db می‌شود (payload: `window_n`, `signals`, `n_pairs`, `top_strength` بعد از decay). **پشتِ flag `OCTOPUS_HEBBIAN_LEDGER`** (خاموش = صفر I/O). EFE ساخته نشد (وجود ندارد) — مشاهده‌پذیری روی واقعیت است. hebbian ۱۸/۱۸+۱۰/۱۰، spine ۹/۹×۴. |
| **W0.3 doctor meter** (VQ-BUDGET-001) | `_ops/budget/telemetry.py::ORGAN_MAP` + `budgets.yaml` | `"doctor": "DOCTOR"` + `DOCTOR {floor:0}` — رفعِ UNMAPPED:doctor. doctor فعلاً $0 (chamber stub) ولی وقتی LLM صدا زند دیگر «دکترِ پولیِ کور» نیست؛ به AU$30 متصل. plumbing فقط (cap بعداً). budget/organ/money ۴/۴ سبز. |
| **W0.4 VQ-LEDGER-CHAIN-001** | `VERDICT_QUEUE.md` | fork هم‌زمان در record 9646 قبلاً با `ledger_repair_reanchor` حل شده بود؛ closure رسمی نوشته شد. |

**یکپارچگیِ زنده (تأییدِ پس از ری‌استارتِ خطِ TG):** commit‌های Wave 0 (`260a0f9`, `5d3b844`) در HEAD `accc0d0` هستن؛ organism زنده (PID 8488) کد Wave 0 رو load کرده (fsync در کد فعلی `True`، beat 19966+ advancing، صفر `.tmp` سرگردان). **هر دو خط در یک organism ادغام شدند.** LEAD_DISCOVERY با دو `set` (L177=1 قدیمی / L817=0 نو) خاموش شد — آخرین `set` در .cmd برنده. `RESTART-VALIDATION-CHECKLIST` procedure کامل + rollback دارد.

## 🧬 ثبتِ ۲۰۲۶-۰۸-۱۲ — hypothesis_engine + چارچوبِ benchmark + موتورِ آزمونِ معرفتی (ADR-037/039)، additive، پیش‌فرضِ خاموش

سه لایهٔ نو رویِ کابینِ مغزِ فرضیه — همگی propose-only / shadow / default-OFF. هیچ‌کدام
executor ندارند؛ `may_execute=False` سخت‌کدشده. سندِ کامل: [[../03 - Projects/research-spec-compiler/adr/ADR-039-epistemic-test-engine|ADR-039]].

| concern | canonical | وضعیت |
|---|---|---|
| کابینِ Pydantic مغزِ فرضیه (ADR-037) | `_ops/hypothesis_engine/impl/{schemas,hypothesis_brain}.py` | SHADOW — فلگ `CORTEX_HYPOTHESIS`؛ propose-only؛ wired در cortex زیرِ cadence `IMPROVE_EVERY_N` |
| چارچوبِ benchmarkِ deceptive-grid | `_ops/hypothesis_engine/experiments/` (`env_factory`, `agents`, `scenarios`, `runner`, `verdict`, `analysis`) | LIBRARY — ۹ سناریوی S0–S8، ablationها، red-team، verdictهای V0–V4، provenanceِ JSONL؛ ۵ سوییتِ تست (۳۶۵+ چک) همگی سبز؛ صداکنندهٔ تولیدی ندارد (آزمایشی) |
| موتورِ آزمونِ معرفتی (ADR-039، TCB-grade) | `_ops/epistemics/{schemas,canonical,policy,validator}.py` + `policy.yaml` | **C1 پیاده، نه wired** — schemas (Pydantic v2 strict/forbid/frozen) + canonical hashing + policy fail-closed + validatorِ pure؛ `test_epistemic_schemas.py` ۴۵/۴۵ سبز؛ default-OFF (`EPISTEMIC_TESTS=0`)؛ **بدونِ wiring تا C5** |

**نکتهٔ ADR-037 amend:** `_ops/epistemics/schemas.py` دومین کابینِ Pydanticِ `_ops` است (پس از
`hypothesis_engine/impl/schemas.py`). سطحِ Pydantic محدود به همان یک فایل است؛ بقیهٔ فایل‌های
epistemics stdlib-only. این amend در headerِ `epistemics/__init__.py` و `schemas.py` مستند شد.

**مرزهای سختِ ADR-039 §7 (در سطحِ schema):** `may_execute` همیشه False · `sandbox_profile`
همیشه `no_network` · `requested_authority` همیشه `propose` · testability>0 · prior∈(0,1).
مسیرِ راه: C1 ✓ → C2 ✓ (receipt chain+provenance، `31d3d7c`) → C3 (generator+runner) → C4 (bayes+multi-agent) → C5 (cortex wiring) → C6/C7.

## 🧬 ثبتِ ۲۰۲۶-۰۸-۱۳ — Conversation Hub (ADR-040) + لایهٔ صداقتِ چت، additive، پیش‌فرضِ خاموش

دو ریلگزدِ نو رویِ لایهٔ چت — هر دو propose-only / default-OFF / بدونِ `execute` از چت.

| concern | canonical | وضعیت |
|---|---|---|
| Conversation Hub (ADR-040) | `_ops/conversation_hub/{schemas,router,service}.py` + `test_conversation_hub.py` | **Phase 1** — درگاهِ یکپارچه‌سازِ چت (façade رویِ ask_vault/ask_brain/collaborator/MCP)؛ مسیریابِ قطعیِ intent (بدونِ LLM)؛ `OCTOPUS_UNIFIED_CHAT=0`؛ `execute` از چت ممنوع. ۱۱/۱۱ سبز. سند: [[../03 - Projects/research-spec-compiler/adr/ADR-040-conversation-hub-unified-chat\|ADR-040]] |
| بنرِ وضعیتِ چت (TASK 4) | `_ops/owner_console/status_banner.py` + GET `/api/chat-status` + `miniapp/app.js::startStatusBanner` | **LIVE پس از restart** — بنرِ فقط‌خواندنیِ halt/quota (بدونِ تماسِ پولی)؛ `status_banner()` + `runtime_truth` enrichment؛ 13/13 سبز |
| یکدست‌سازیِ auth (TASK 2) | `_ops/telegram_center/miniapp_gateway.py` | ۳ endpoint (`/api/actions`، `/api/miniapp`، `/api/pf/*`) به `_owner_initdata_ok()` وصل شدند (ردِ تکرارِ دستی) |

**لایهٔ صداقتِ چت (مگاپرامپت):** collab intro-exclusion را تست‌ها assert می‌کنند (TASK ۱) · `runtime_truth` حالا halt/quota را صادقانه می‌گوید (TASK ۳ path ب) · بنرِ پیشگیرانهٔ وضعیت (TASK ۴) · `honest-self` routing برای ادعای خودآگاهی (invariantِ ضدِ AGI تقویت شد).
