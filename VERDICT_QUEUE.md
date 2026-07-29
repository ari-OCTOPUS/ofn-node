# ✅ VERDICT_QUEUE — تصمیم‌های انسانی کل پازل هشت‌پا

> صف تصمیم‌های مالک. هیچ secret/PII در این فایل نوشته نمی‌شود.

---

## P0 — ساختار حکمرانی

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| VQ-ROOT-001 | نسبت `app/NBB-CP` با `Architect/_ops` | A: portable sibling · B: adapter زیر Architect · C: جایگزین تدریجی · D: فقط آزمایش | open | مسیر اتصال مغزها |
| VQ-ROOT-002 | ادامه کار روی همین workspace یا vault کامل | A: همین workspace · B: mount vault اصلی | A selected | فعلاً روی `پازل هشت پا` ادامه می‌دهیم |
| VQ-ROOT-003 | آیا registry/risk-ladder همین نسخه معیار باشد؟ | yes/no/adjust | open | مبنای automation بعدی |

---

## Accounting

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| VQ-ACC-001 | انتخاب حسابدار / Tax Agent | نام/کد داخلی یا none | open | بدون آن قواعد مالیاتی unverified می‌مانند |
| VQ-ACC-002 | ساختار بیزنس | one Pty Ltd / multiple / sole+company / ask accountant | open | ساخت Chart of Accounts و tax flow |
| VQ-ACC-003 | نرم‌افزار حسابداری | Xero / MYOB / Excel / other | open | importer و workflow |
| VQ-ACC-004 | حساب بانکی جدا | yes/no | open | audit readiness |
| VQ-ACC-005 | GST status | registered/not/unknown | open | BAS workflow |

---

## Lead-نقاشی

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| VQ-LEAD-001 | کانال آزمایش #۱ | Google/GBP · Facebook · flyers · builders · strata · tenders | open | شروع lead experiment |
| VQ-LEAD-002 | segment اول | residential / strata / builder / commercial / insurance | open | copy و compliance |
| VQ-LEAD-003 | استفاده عمومی از portfolio photos | yes/no/some | open | social proof |
| VQ-SCORER-001 | دستهٔ مسکونیِ مستقیم در lead_scorer | A: دستهٔ پنجمِ flag-gated · B: دو لِین · C: فقط آستانه | ✅ **closed — A (2026-07-25)**: `residential_repaint_direct` base=50، پشتِ `OCTOPUS_LEAD_DIRECT_RESIDENTIAL=1`، additive، ۵ تستِ نو. بدونِ فلگ رفتار بایت‌به‌بایت identical. | لیدِ $715–$15k دیگر skip نمی‌خورد |

---

## Ziman

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| VQ-ZIM-001 | ظرفیت هفته‌ای | عدد units/week | open | D4 capacity gate |
| VQ-ZIM-002 | محصول hero | shadowbox / artificial flowers / gift basket / chocolate hamper | open | first-sale funnel |
| VQ-ZIM-003 | کانال اول | IG local / marketplace / local groups / website | open | validation |

---

## Project-F

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| VQ-PF-001 | GATE 0 | resolved/unresolved | open — رأی 07-20: ‏PF-V5 ‏REVOKED، ‏Branch A ‏attested؛ بستن G0 منوط به تکمیل منبع اقامت + تأیید مکتوب C + سؤال پرسشنامه («DL-2026-07-20-G0/RATIFICATION») | هیچ outward action تا حل G0 |
| VQ-PF-002 | Branch | A/B/unknown | **A (اظهار A ‏2026-07-20 — مدرک روی دیسک نیست)** → «DL-2026-07-20-G0» | legal/ops path |
| VQ-PF-003 | freeze body expansion | yes/no | ✅ **closed — FREEZE (امضای A ‏2026-07-20، «DL-2026-07-20-BODY-FREEZE»)** | hard-rule alignment |
| VQ-PF-004 | activate Langar/studio shadow | yes/no/later | open | cockpit only، no outward action |

---

## Crypto-eToro

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| VQ-CRYPTO-001 | پر کردن Portfolio Registry | yes/no | open | alerts/exit_rules |
| VQ-CRYPTO-002 | auto-sell فعلاً غیرفعال بماند؟ | yes/no | open | execution safety |
| VQ-CRYPTO-003 | EdgeClassifier bug fix as ticket | yes/no | open | paper-only scout accuracy |

---

## Mining

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| VQ-MIN-001 | Hardware Registry با وضعیت واقعی پر شود؟ | yes/no | open | fleet health |
| VQ-MIN-002 | mining فعال است؟ | yes/no | open | accounting/event flow |
| VQ-MIN-003 | electricity constraint وضعیت | <$0.05 / solar / no / unknown | open | experiment gate |

---

## Brains / Tools

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| VQ-NBB-001 | NBB-CP نقش آینده | governor / sibling / archive / later | open | اتصال به tenantها |
| VQ-4D-001 | اجرای ۳۰روزه 4D | yes/no/later | open | autonomous run |
| VQ-MAP-001 | اجرای scanner روی همین workspace | yes/no | open | fresh inventory |

---

## Synapse / AGI Capabilities

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| VQ-SYN-001 | روشن‌کردن SENSE و Trajectory Monitor | yes (propose-only) / no | open | تولید proposal بدون اثر روی runtime |
| VQ-EGR-001 | فعال‌سازی egress_policy به صورت audit-only | yes / no | open | لاگ ترافیک cloud بدون مسدودسازی |
| VQ-TRAJ-001 | اتصال منبع ۵ (Trajectory) به Event Bridge | yes (flag on) / no | open | دریافت هشدارهای burst و novel-chains |
| VQ-AGI-001 | نقشه‌راه Gapها و ادعای معماری | accept framework / reject / revise | open | چارچوب ابطال‌پذیر برای بستن C1..C8 |

---

## Doctor / مغزهای پولی — ثبتِ ۲۰۲۶-۰۷-۲۵

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| VQ-PAID-001 | روشن‌کردنِ سه فلگِ router (governor · heart-doctor · selfknow-paid) | yes / no | **yes — رأیِ مالک ۲۰۲۶-۰۷-۲۵؛ config مسلح شد، منتظرِ restart** | مسیرِ مغزِ پولی در بوتِ بعدی باز می‌شود، زیر سقفِ AU$30 ماهانه / AU$2 burst |
| VQ-GUARD-001 | `test_paid_router_dark_config` صفربودنِ همان فلگ‌ها را pin کرده بود و با VQ-PAID-001 تضاد داشت | A: قرمزِ عمدی · B: گارد → «مطابقِ رأیِ ثبت‌شده» · C: فلگ‌ها را برگردان | **B اجرا شد ۲۰۲۶-۰۷-۲۷** — مرجعِ گارد از عددِ هاردکد به `_ops/PAID-FLAGS-DECLARATION.json` رفت | دلیلِ اجرا بدونِ انتظار: تستِ همیشه‌قرمز خودش نقص است (عادت‌دادن به نادیده‌گرفتنِ قرمز). گاردِ نو **سخت‌گیرتر** است: driftِ دوطرفه + الزامِ شاهد برای هر فلگِ روشن. هر دو با جهشِ عمدی سنجیده شد. **مالک می‌تواند با یک کلمه برگرداند** |
| VQ-T8-001 | dedupeِ RFC و `_reconcile_input_validity` غیرمشروط‌اند | A: پشتِ فلگِ پیش‌فرض‌خاموش · B: استثنای مکتوب در SoT (ثبت شد) | open — پیشنهاد **B برای dedupe، A برای reconcile** | قاعدهٔ additive + flag-gated + default-off |
| VQ-T3-001 | ثبتِ علتِ شکستِ لِگ غیرمشروط است | A: استثنای observability · B: پشتِ فلگ | open — پیشنهاد **A** | فقط writeِ تشخیصی؛ هیچ شاخهٔ تصمیمی نمی‌خواند |
| VQ-T2-001 | روشن‌کردنِ `OCTOPUS_HONEST_OUTCOMES` | yes / no | open | تا خاموش است، شمارشِ closure قاعدهٔ قدیم را اجرا می‌کند |
| VQ-RESTART-001 | restart ارگانیسم برای اعتبارسنجیِ زندهٔ T1/T3/T4/T8 و فلگ‌های نو | مالک اجرا کند / صبر | open — ایجنت restart نمی‌زند | تنها راهِ تبدیلِ «سبزِ تست» به «سبزِ زنده» |
| VQ-REPO-001 | `_worktree-rescue-2026-07-24` (۴۹۵MB) و dumpهای legacy/gallery-3d/ziman_os در checkpoint نیامدند | A: به `_Archive` منتقل شود · B: commit شود · C: untracked بماند | open — پیشنهاد **A** | حجمِ ریپو؛ قاعدهٔ «حذف نکن، منتقل کن» |
| VQ-COMMIT-002 | کارِ موج‌های W1→W5 + سه نقطهٔ کورِ CRIT (۲۰۲۶-۰۷-۲۷) uncommitted مانده | مالک `OWNER_AUTH: COMMIT <paths>` بدهد / صبر | open — ایجنت commit نمی‌زند (§۴ قراردادِ GENOME LOCK) | تا آن لحظه کلِ کار فقط روی worktree است؛ جزئیات: [[_ops/SESSION-2026-07-27-W1-W5\|SESSION]] |
| VQ-ARM-002 | چهار فلگِ تازه (`WIRE_BUDGET_JUDGE` · `WIRE_DECISION_GATE` · `WIRE_TRAJECTORY_LOG` · `WIRE_TEACHER_LOOP` · `AUTONOMY_GRANT` · `ENFORCE_MONEY_FSM`) همه خاموش‌اند | مالک per-flag `OWNER_AUTH: ARM FLAG <name>` بدهد | open | خاموش = رفتارِ امروز بایت‌به‌بایت. **`ENFORCE_MONEY_FSM` عمداً آخرین باشد** — فهرستِ گذارها از خواندنِ کد آمده نه از ترافیکِ زنده؛ اول چند روز بشمارد |
| VQ-ARM-003 | سه فلگِ تازهٔ ۲۰۲۶-۰۷-۲۷ (بخشِ دوم/سوم): `OCTOPUS_WIRE_IMPROVE_LEARN` · `OCTOPUS_WIRE_FUNNEL_CMD` · `OCTOPUS_WIRE_TRAJECTORY_LOG` | مالک per-flag `OWNER_AUTH: ARM FLAG <name>` بدهد | open — پیشنهاد: **IMPROVE_LEARN اول** | تا خاموش‌اند، رأیِ مالک چیزی یاد نمی‌دهد و نتیجهٔ بازار جایی ثبت نمی‌شود. هر سه propose-only، صفر پول، صفر ارسال |
| VQ-TWOBOT-001 | سیستم **دو بات** دارد (ارگانیسم + مرکزِ گروه) با دو پروسه و دو توکن. کارت‌ها از یکی می‌روند و بعضی handlerها در دیگری‌اند | A: هر کارت با روترِ همان بات (وضعِ فعلی، گاردِ `test_callback_routing`) · B: یکی‌کردنِ دو بات · C: یک روترِ مشترک | open — پیشنهاد **A** تا وقتی B رأی بگیرد | `iv:q` دقیقاً از همین‌جا مرده بود. B ریسکِ 409 Conflict دارد (درسِ ۰۷-۲۶) |
| VQ-FSM-001 | جدولِ گذارِ حالتِ پول (`MONEY_TRANSITIONS`) کامل است یا گذارِ مشروعی جا افتاده؟ | A: چند روز سایه، بعد تصمیم با عدد · B: همین حالا اجباری · C: رد | open — پیشنهاد **A** | اجبارِ زودرس = شکستنِ یک پرداختِ واقعی. شواهد در `_ops/state/money-fsm-violations.jsonl` |

---

## دیباگِ زنده ۲۰۲۶-۰۷-۲۵ (پس از ریستارتِ ۱۴:۱۴:۲۵)

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| VQ-PHI-001 | روشن‌کردنِ `OCTOPUS_CHRONO_PHI_HONEST=1` | yes / no | open — پیشنهاد **yes** | حلقهٔ مرگِ جعلیِ لِگ را می‌بندد (۶۶ ری‌استارت، همه با phi=300). خاموش = بایت‌به‌بایتِ امروز. اثر فقط با ریستارت |
| VQ-FUGU-001 | پایین‌آوردنِ `FUGU_FAIL_CEILING` از ۸ به ۳ | 8 / 3 / عدد دیگر | **انجام شد (=3) ولی اثباتاً بی‌اثر** — به VQ-FUGU-002 گره خورده | Fugu سه‌از‌سه با تایم‌اوتِ ثابتِ ~۴۵s افتاد ولی سقف هرگز شلیک نمی‌کند (زیر را ببین) |
| VQ-FUGU-002 | شمارندهٔ شکستِ Fugu **سراسری** است، پس بریکرش ساختاراً غیرقابل‌شلیک است | A: شمارندهٔ per-tier مبنای حکم شود ولی فقط همان tier کنار برود (نه STOP-FUGUِ سراسری) · B: STOP-FUGU از شکستِ یک tier شلیک کند · C: بپذیر و فقط گزارش کن (وضعیتِ فعلی) | open — پیشنهاد **A**، صریحاً **نه B** | شاهد: سه تایم‌اوتِ پیاپیِ primary ولی `consecutive_failures=0`، چون هر موفقیتِ GLM صفرش می‌کند. **B خطرناک است:** STOP-FUGU سراسری است و اگر از شکستِ primary شلیک شود، مغزِ **سالمِ** GLM را هم می‌کشد. شمارندهٔ per-tier ساخته شد (فقط گزارش، صفر تغییرِ رفتار) تا tierِ مرده دیگر نامرئی نباشد |
| VQ-CB-001 | ست‌کردنِ `OCTOPUS_CB_SECRET` (کارِ **فقط مالک** — ایجنت هرگز secret نمی‌نویسد) | yes / no | open | تا وقتی خالی است، کارتِ تأییدِ دکمه‌دار mint نمی‌شود (`reason='no-secret'`). نیمهٔ کارتِ T8 تا آن لحظه غیرقابل‌مشاهده می‌ماند |
| VQ-LOOP-001 | **علت قطعی شد (۱۶:۲۵):** حلقهٔ کاریِ بیرونی ۹۰۰ ثانیه است با `driver="brake:cardiac"` چون `cardiac.budget` تمام شده (`spent=288/daily_cap=288`, `depleted=true`) — سرعتِ طراحی‌شده ۴۲.۴ ثانیه است، یعنی **۲۱ برابر کندتر**. تنها اهرم: سقفِ روزانهٔ ۲۸۸ | A: سقف را بالا ببر (setpointِ مالک) · B: بپذیر — «روزی ۲۸۸ چرخه کافی است» · C: اول ببین آن ۲۸۸ چرخه صرفِ چه شده، بعد تصمیم بگیر | open — پیشنهاد **C سپس A** | این تنها عددی است که نرخِ اقدامِ ارگانیسم را می‌بندد (C9). `velocity_per_hr=0.125` در برابرِ باندِ هدفِ خودش `[0.51, 5.05]` — ۴ برابر زیرِ کفِ خودش، و حالا دلیلش معلوم است. توجه: بالا بردنِ سقف مصرفِ توکن/برق را هم بالا می‌برد |

---

## AGI ladder — بازسنجیِ ۲۰۲۶-۰۷-۲۵ (جزئیات در `_program-deliverables/AGI-CAPABILITY-GAP-ROADMAP-2026-07-24.md` بندهای ۷–۹)

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| VQ-AGI-002 | **وارونگیِ حکمرانی:** نردبان، L8 (قابلیتِ **نوشتنِ** همتا) را روی «L2 = روشن‌کردنِ R5» باز می‌کند، ولی R5 اثباتاً هیچ‌چیز را رد نمی‌کند (فقط alert می‌زند و پرامپت را عبور می‌دهد) | A: پیش‌شرطِ L8 به «R5-**prevent** MET + یک refusalِ لاگ‌شده» بازنویسی شود و R5 به detect/prevent شکسته شود · B: همان بماند | open — پیشنهاد **A** | تا اصلاح نشود، یک قابلیتِ نوشتن به اعتبارِ مهاری آزاد می‌شود که هیچ مهاری نمی‌کند |
| VQ-ALERT-001 | `opslib.alert()` هیچ dedupe/throttle ندارد (append خالص) | A: پنجرهٔ throttle/هش مثل `_dialogue_gate` اضافه شود **قبل** از روشن‌کردنِ R5 · B: R5 با آلارمِ throttle-نشده روشن شود | open — پیشنهاد **A، و R5 تا آن‌وقت خاموش** | آلارم به تلگرام می‌رود؛ سیلِ آلارمِ fence توانِ دیدنِ اعلانِ **واقعیِ** halt را تخریب می‌کند |
| VQ-ARM-001 | `arm_gate` هیچ‌چیز اعمال نمی‌کند (`OCTOPUS_REQUIRE_ARM` ست نیست) و `cortex_paid` که امروز مسلح شد در `DANGEROUS` فهرست است ولی سایتِ فراخوانش چک نمی‌کند | A: `OCTOPUS_REQUIRE_ARM=1` + وصل‌کردنِ چک به سایتِ cortex_paid · B: بپذیر و مستند کن | open — پیشنهاد **A** | دومین قفلِ قابلیتِ پولی الان تزئینی است |
| VQ-C3-001 | فیکسِ کوریِ اندام در خودشناسی (`OCTOPUS_SELFKNOW_LEGS_UNWRAP`) روشن شود؟ | yes / no | open — پیشنهاد **yes** | تا خاموش است، مغزِ پولی «۱ لِگِ مرده» می‌بیند در حالی که **۴** لِگ هست. کد+تست آماده (پیش‌بینیِ پیش‌ثبت‌شده، ۸ چک) |
| VQ-C6-002 | ساختِ `_ops/ACTIVATION-C6-RESEARCH.flag` (یک فایلِ خالی) تا تک‌فرضیهٔ seedشده اجرا شود | yes / no | open | بدونِ آن `c6_research_beat` روی `flag-off` می‌ماند و **هیچ سنجهٔ C1 هرگز اجرا نمی‌شود**. برگشت: حذفِ همان یک فایل |
| VQ-C5-002 | ساختِ `_ops/state/legs/lead-inbox/` + انداختنِ **یک** لیدِ واقعیِ de-identified | yes / no | open | علتِ واقعیِ C5=0 نبودِ همان دایرکتوری است (`lead_sense.py:79-81`)، نه نبودِ لید. اولین گامِ سنجش‌پذیرِ درآمد |


---

## پارک‌شده با رأیِ مالک — ۲۰۲۶-۰۷-۲۵ ۱۷:۴۵

| ID | تصمیم | وضعیت | اثر |
|---|---|---|---|
| VQ-ACCT-PARK | **مسیرِ حساب‌کتاب/reconcile متوقف است.** رأیِ مالک: «حساب‌کتاب‌ها را قاطی نکن چون همهٔ داده‌ها را نداده‌ام.» | **PARKED — دست نزن** | هیچ `claims_backfill`، هیچ reconcile، هیچ ثبتِ CONFIRMED، هیچ استنتاجِ درآمد تا مالک دفترِ کامل را بدهد. اعدادِ BUSINESS-SPEC فقط برای کالیبراسیونِ قیمت معتبرند |
| VQ-RECON-001 | پنجرهٔ ۷ روزه + قاعدهٔ `cohort-partial` روی قراردادِ progress-claim (۹۳ هزار دلاری، پرداخت در ۲۶ ژوئن و ۲۳ جولای) قطعاً شکست می‌خورد | open — **زیرِ PARK** | راهِ بدونِ کد: هر ردیف = یک پرداخت، تاریخ = تاریخِ واریز. ولی تا لغوِ PARK اجرا نمی‌شود |
| VQ-INV-001 | شمارهٔ فاکتور دستی است و مبهم شده (`00270` و `002701` هر دو موجود؛ ترتیبِ تاریخ یکنوا نیست) | open | ریسکِ مغایرت‌گیری و ظاهرِ حسابداری. پیشنهاد: شمارنده از سیستم |
| VQ-INS-001 | تاریخِ انقضای **بیمهٔ جدید** | open — تنها ورودیِ لازم | تا پر نشود، ناظرِ انقضا همان نقطهٔ کورِ قبلی را دارد |

---

## 🐙 LIVE path 2026-07-25 — آنچه فقط مالک باید انجام دهد

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| VQ-LIVE-001 | ری‌استارت ارگانیسم با فلگ‌های جدید | restart / defer | open | ۶ فلگِ جدید در flags.cmd روشن شده ولی تا restart بی‌اثرند |
| VQ-LIVE-002 | OCTOPUS_CB_SECRET | set in .env / defer | open — فقط مالک | بدونش دکمه‌های تلگرام inert؛ ایجنت حق ندارد بسازد |
| VQ-LIVE-003 | دود تست: `/live /id /box /code` در تلگرام | test / defer | open | اولین smoke test رابط زنده |
| VQ-LIVE-004 | ROMAJAN_PROBES=1 | on/off | open — وقتی F:\romajan تأیید شود | سیمِ romajan→C6 روشن شود |

---

## 🩺 دکترِ اختاپوس 2026-07-29 — نردبانِ اعتماد (هر پله رأیِ جدا)

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| VQ-DR-001 | `OCTOPUS_WIRE_DOCTOR_TG=1` + ری‌استارتِ TG-center | on / defer | ✅ **انجام و اثبات شد ۰۷-۲۹** — به دستورِ صریحِ مالک در چت. کارتِ تست `message_id=323` رفت، مالک ✅ زد، رأی به inbox رسید و `verdict("wire","test")=True` — رفت‌وبرگشتِ کامل با اثر سنجیده شد، نه فلگ | کارت‌های دکتر (نیت/دیف) واردِ گروهِ تلگرام می‌شوند و رأیِ دکمه‌ای به دکتر می‌رسد |
| VQ-DR-002 | کلیدِ مغز | — | ✅ **بسته شد ۰۷-۲۹ — setx لازم نبود.** تصحیحِ مالک: کلید از قبل با نامِ `FUGU_API_KEY` در `.env` بود (Fugu = Sakana). دکتر حالا alias را می‌پذیرد و تسکِ روزانه از `_ops/run_doctor_day.py` (env_loader ِ خودِ ارگانیسم) env می‌گیرد — دکتر همچنان خودش `.env` را نمی‌خواند. اولین ask واقعی: `fugu·high·418tok·15s·exit 0` | پله‌های ۱–۲ زنده؛ سقف: ۶۰ فراخوان + $۲/روز در کد |
| VQ-DR-003 | اولین `day --live` زیرِ چشمِ مالک (بدونِ `--apply`) | run / defer | open — بعد از VQ-DR-001 | اولین اجرای MissionRunner روی worktree با pinِ ORG_ROOT؛ `run_all` تستِ STOP-ساز دارد — به همین دلیل فقط با نظارت |
| VQ-DR-004 | `OCTOPUS_DOCTOR_MAY_MERGE=1` | on / never-yet | open — **پیشنهاد: فعلاً نه** | قفلِ سومِ merge؛ تا این ست نشود دکتر حتی با دو ✅ هم merge نمی‌کند |
