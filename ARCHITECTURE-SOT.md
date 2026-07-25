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

## 🩺 ثبتِ ۲۰۲۶-۰۷-۲۵ — دکتر، dedupe، و مغزهای پولی

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

> **تصحیحِ ثبت‌شده (همان روز، ۱۵:۰۶):** نسخهٔ اولِ این بند گفته بود «حلقهٔ بیرونیِ
> organism ~۹.۵ دقیقه است». **غلط بود.** اندازه‌گیریِ تمیز: ۴۰ بیت در ۲۴۳۷ ثانیه =
> **۶۰.۹ ثانیه بر بیت**. آن استالِ ۱۰-دقیقه‌ایِ ۱۴:۲۵→۱۴:۳۵ یک‌بار رخ داد و دقیقاً در
> بازه‌ای بود که ۱۴ ایجنتِ راستی‌آزمایی ۵۶۴ فراخوانِ فایل روی همان دیسک می‌زدند — یعنی
> آرتیفکتِ **بارِ خودِ اندازه‌گیری**. درسِ ثبت‌شده: ابزارِ ناظر بخشی از سیستمِ تحتِ
> مشاهده است؛ عددی که زیرِ بارِ خودت گرفته‌ای را خاصیتِ سیستم نخوان.

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
