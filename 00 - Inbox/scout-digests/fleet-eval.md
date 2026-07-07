---
type: report
status: active
tags: [fleet, selection, review, weekly]
created: 2026-07-06
updated: 2026-07-06
---

# fleet-eval — ارزیابی هفتگی ناوگان

> خروجی تسک زمان‌بندی `fleet-selection` (یکشنبه ۲۳:۰۰، propose-only). هر اجرا یک بخش تاریخ‌دار نو زیر اضافه می‌کند؛ بخش‌های قدیمی دست‌نخورده می‌مانند. مرجع: [[05 - Agents/AGENT_REGISTRY|AGENT_REGISTRY]] · [[_memory/HEARTBEAT|HEARTBEAT]] · [[_memory/EXPERIENCE-LEDGER|EXPERIENCE-LEDGER]].

## 2026-07-06 (اولین اجرا)

**زمان مرجع:** ~۰۰:۰۴ AEST 2026-07-06 (از خروجی زندهٔ زمان‌بند/سمت میزبان، نه ساعت سندباکس).

### ۱) وضعیت ناوگان ratified (طبق HEARTBEAT + فهرست زندهٔ زمان‌بند)

فهرست زندهٔ زمان‌بند هر ۶ taskId جدول ratified را نشان می‌دهد (۶/۶ حاضر — هیچ‌کدام غایب، پس خودترمیمی §۳.۳ لازم نشد):

| task | حاضر؟ | enabled | آخرین اجرا (UTC) | beat در HEARTBEAT |
|---|---|---|---|---|
| brain-focus-board | ✅ | **false** | 2026-07-05T13:54:51Z | ✅ تازه (~۲۱:۵۶ AEST دیروز) |
| brain-pulse | ✅ | **false** | 2026-07-05T13:54:52Z | ✅ تازه (~۲۱:۱۰ AEST دیروز) |
| system-dashboard | ✅ | false (عمدی) | 2026-07-05T14:00:51Z | disabled عمدی — بازنشسته، ادغام در CONTROL-PANEL |
| mycelial-consolidator | ✅ | **false** | 2026-07-05T14:01:51Z | ✅ تازه (~۲۲:۰۲ AEST دیروز) |
| experience-review | ✅ | **false** | 2026-07-05T13:54:51Z | ✅ تازه (اجرای جبرانی ~۲۳:۵۴ AEST) |
| fleet-selection | ✅ | **false** | 2026-07-05T14:01:51Z (اجرای قبلی) | این اجرا |

**یافتهٔ اصلی این هفته:** به‌جز `system-dashboard` (که عمداً و مستند disabled است)، هر ۵ تسک دیگر هم اکنون `enabled: false` نشان می‌دهند — ولی `lastRunAt` هرکدام فقط چند دقیقه تا حداکثر ~۱۰ دقیقه قبل از این اجراست (همه در بازهٔ ~۲۳:۵۴–۰۰:۰۱ AEST، یک burst اجرای جبرانی هم‌زمان — الگوی شناخته‌شدهٔ «اجرای جبرانی پس از بیداری host» که قبلاً در ledger هم دیده شده). یعنی این **regress-silence نیست** — هیچ تسکی از آستانهٔ ۲×دورهٔ انتظار خودش رد نشده و HEARTBEAT هیچ سکوتی ثبت نکرده. اما وضعیت `enabled: false` روی ۵ تسکی که قرار است تکرارشونده باشند مبهم است: یا (الف) نمایشِ گذرای زمان‌بند بلافاصله بعد از یک اجرای دسته‌جمعی است و به‌زودی برای دور بعد `true` می‌شود، یا (ب) چیزی (بسته‌شدن اپ، تعامل دستی آری، یا یک اثر جانبی از جلسهٔ ساخت CONTROL-PANEL/build-planner-loop) کل هستهٔ ۶تایی را متوقف کرده. **توصیه (L1، برای آری):** یک نگاه سریع به پنل Scheduled Tasks بیندازد — اگر پنج تسک واقعاً خاموش‌اند، «Run now»/toggle دستی لازم است تا دور ۳ساعته/شبانه/هفتگی بعدی از دست نرود.

### ۲) کیفیت خروجی‌ها

- **BRAIN-FOCUS-BOARD.html** — ۴۴KB، آخرین نوشت 2026-07-05 22:12 (v15، طبق ledger). چرخهٔ hash-diff/idempotent سالم؛ گاردهای parse/secret/Project-F سبز در آخرین اجراها. کیفیت: خوب.
- **Brain.md** — ۸KB، آخرین نوشت 2026-07-05 21:16. هیچ Active Context با کهنگی >۷۲ساعت علامت نخورده؛ لینک‌ها متوازن. کیفیت: خوب.
- **SYSTEM-DASHBOARD.html** — ۲۶KB، آخرین نوشت 2026-07-05 15:56، اما تسکش عمداً **disabled/بازنشسته** با بنر جانشین به CONTROL-PANEL. فایل دیگر به‌روزرسانی خودکار نمی‌شود (منجمد).
- **CONTROL-PANEL.html** — ۲۳KB، ساخته‌شده 2026-07-05 15:47 (کار تعاملی، نه خروجی یک تسک زمان‌بندی) — ادغام focus-board + system-dashboard + کنسول Doctor + Build Spine. جانشین رسمی system-dashboard.
- **mycelial-consolidator** — دیجست‌های تازهٔ 2026-07-05 را سنتز کرد: `2026-07-05 synthesis.md` (۱۷KB، ۲۲:۱۲) + `_Mycorrhizal Map.md` (رشد کرد: الگوهای P9/P10/P11 + اصلاح E1) + `_TRIAGE-BOARD.md` تازه (۲۲:۱۶). evaporation: صفر اقدام — قدیمی‌ترین دیجست هنوز فقط ~۲ روز عمر دارد (آستانه ۱۴ روز). کیفیت: خوب، دقیقاً طبق طراحی.
- **experience-review** — دیجست `2026-07-05 experience-review.md` (۱۱.۸KB) با ۱۲ pending-verdict و شاخص استقلال. بازوی verdict هفتگی سالم کار می‌کند.

### ۳) هزینه‌فایدهٔ cronها

با توجه به اینکه ۱۹ اسکات روزانه + ۶ لاین selfimprove همچنان عمداً تاریک‌اند، رد پای واقعی ناوگان همین **۶ تسک هسته**‌ست. هزینهٔ آن‌ها ناچیز و خروجی‌ها (بالا) با کیفیت‌اند — **هیچ تغییر cron توصیه نمی‌شود** این هفته. تنها بند باز، رفع ابهامِ enabled:false در بخش ۱ است؛ بعد از آن هستهٔ ۶تایی نیازی به تنظیم ندارد.

### ۴) سیگنال re-arm ناوگان اسکات (۱۹ اسکات + ۶ لاین selfimprove)

**سیگنال کافی نیست — این هفته پیشنهاد re-arm داده نمی‌شود.** دو دلیل: (۱) اسکات‌ها از 2026-07-04 ~۲۱:۲۹ عمداً تاریک‌اند، پس هیچ دادهٔ تازهٔ مقایسه‌ای برای قضاوت کیفیت/ارزش‌شان در این هفته وجود ندارد؛ (۲) خود هستهٔ ۶تایی همین امشب یک وضعیت مبهم (enabled:false در ۵ تسک) نشان داد — قبل از گسترش دامنه باید پایداری هسته تأیید شود. توصیه: هفتهٔ بعد، اگر هسته یک دور کامل بدون قطعی اجرا کند، fleet-selection دوباره سیگنال re-arm را بسنجد.

### ۵) توصیه‌های ساختاری (L1 propose — ثبت در ledger)

1. **بازنشستگی رسمی `system-dashboard`** از جدول تسک‌های ratified در AGENT_REGISTRY — چون CONTROL-PANEL جانشین کاملش شده و این ابهام (پابرجا از ledger ردیف‌های ۵۲/۶۰ و HEARTBEAT) چند اجرا پشت‌سرهم تکرار شده. verdict آری لازم است تا هم رجیستری و هم جدول ratified هماهنگ شوند.
2. **بررسی enabled:false روی ۵ تسک هسته** (بخش ۱) — نیاز به یک نگاه مالک، نه اقدام خودکار (git/rotation gate بسته، restore تعاملی است).
3. **الگوی burst اجرای جبرانی** (چند تسک هم‌ثانیه، دوباره این هفته دیده شد) مؤید مستقل پیشنهاد قبلی **P-08** (idempotency-key + run-journal durable، از `build-proposals/08`) است — پیشنهاد از قبل در صف verdict آری قرار دارد، ردیف تازه‌ای لازم نیست.

## 2026-07-06 ~۰۳:۲۷ AEST (اجرای دوم همین هفته)

**زمان مرجع:** زمان‌بند lastRunAt `2026-07-05T17:26:41Z` (~۰۳:۲۷ AEST). این دومین فایرِ همین اسلاتِ هفتگی در کمتر از ۴ ساعت (اولی ~۰۰:۰۴ AEST بالا) — الگوی burst اجرای جبرانی که چند بار دیگر هم در ledger دیده شده (brain-pulse/mycelial-consolidator هم در همین بازه هم‌ثانیه اجرا شدند)؛ مستقل تأیید P-08 (idempotency-key، هنوز pending-verdict) نه سیگنال نو.

### یافتهٔ اصلی: خطای خودساخته + خودترمیمی همان جلسه روی `system-dashboard`

این اجرا فهرست زندهٔ زمان‌بند را با جدول ratified رجیستری تطبیق داد و `system-dashboard` را **کاملاً غایب** یافت (نه فقط disabled مثل هفتهٔ قبل). طبق §۳.۳ منشور (خودترمیمی ناوگان، کلاس ۳ بدون سقف روزانه) با `create_scheduled_task` از روی متن کامل RATIFIED-TASKS بازسازی شد (cron `20 */6 * * *`).

بلافاصله بعد، مرور کامل‌تر ledger (که باید همیشه قبل از restore انجام شود و این‌بار دیر انجام شد) سه شاهدِ همگرا نشان داد که این غیبت **عمدی** بوده، نه یک reset:

- ردیف ۶۰ (dashboard·auto، ۲۰۲۶-۰۷-۰۵): بنر جانشینیِ CONTROL-PANEL روی خودِ فایل + توصیهٔ verdict حذف/ابقا.
- ردیف ۷۶ (GO-LIVE، همین امروز): وضعیت‌کدِ صریح «۵ ratified هسته» — system-dashboard حتی جزو استثنای عمداً-تاریک هم شمرده نشده.
- ردیف ۸۰ (consolidator·auto، همین امروز): همان غیبت را دید و **عمداً restore نکرد** (مبهم → پلهٔ پایین‌تر) — دقیقاً کاری که این اجرا باید می‌کرد.

**خودترمیمی خطای خودساخته (کلاس ۶ لیست سفید، مجاز در همان جلسه):** تسکِ تازه‌ساخته بلافاصله `enabled:false` شد (نه حذف — برگشت‌پذیر و قابل‌بازبینی). دو ردیف در ledger append شد: یک regress خودافشا (چرا اشتباه شد + قاعدهٔ سفت‌شده برای اجراهای بعدی: قبل از هر restore، ledger را برای observe/regress مرتبط با همان taskId هم اسکن کن) و یک propose (نیاز به verdict قطعی: رجیستری رسماً به ۵ تسک ratified کاهش یابد، یا اگر system-dashboard هنوز نقشی دارد صریحاً enabled شود و بنر بازنشستگی برداشته شود). HEARTBEAT ردیف fleet-selection هم به‌روز شد. هیچ نوت canonical دیگری لمس نشد؛ نقض invariant = صفر.

### بقیهٔ هستهٔ ratified

بدون تغییرِ کیفی نسبت به بخش ۲/۳ بالا در همین جلسه — ۵ تسک دیگر (brain-focus-board، brain-pulse، mycelial-consolidator، experience-review، خودِ fleet-selection) حاضر/enabled و beat تازه دارند؛ فقط cron-drift شناخته‌شدهٔ `mycelial-consolidator` (`0 */3` به‌جای ratified `0 22`، ledger ردیف ۷۸) هنوز حل‌نشده مانده — تصحیح cron یک تسک حاضر/enabled در لیست سفید L2 نیست، پس دوباره لمس نشد.

### توصیه (L1، برای آری)

1. **یک verdict یک‌کلمه‌ای کافی است** تا نوسان هفتگی restore↔retire روی `system-dashboard` تمام شود: یا رجیستری را به ۵ تسک ببر (و RATIFIED-TASKS را هم‌زمان به‌روز کن)، یا این تسک را رسماً enabled نگه‌دار و بنر بازنشستگی را بردار.
2. **cron mycelial-consolidator** را به `0 22 * * *` برگردان (ردیف ۷۸، هنوز باز).
3. سیگنال re-arm ناوگان اسکات هنوز کافی نیست (اسکات‌ها این هفته فعال شدند طبق GO-LIVE ردیف ۷۶ — ارزیابی کیفیت‌شان را هفتهٔ بعد که یک هفتهٔ کامل داده جمع شد انجام بده).

## 2026-07-06 ~۱۰:۲۵ AEST (اجرای سوم — فایر جبرانیِ اسلات هفتگی یکشنبه ۲۳:۰۰)

**زمان مرجع:** زمان‌بند fireAt `2026-07-06T00:22:00Z` / lastRunAt `00:24:53Z` (~۱۰:۲۵ AEST دوشنبه). ساعت سندباکس ~UTC است (قاعدهٔ HEARTBEAT).

### 🔴 یافتهٔ اصلی هفته: کل ناوگان به تسک‌های one-time تبدیل شده — خاموشی سوم «برنامه‌ریزی‌شده» در راه است

فهرست زندهٔ زمان‌بند نشان می‌دهد تقریباً **همهٔ تسک‌های GO-LIVE (ردیف ۷۶/۷۷ ledger) به‌جای cron تکرارشونده با `fireAt` یک‌باره ساخته شده‌اند** — همه در بازهٔ «One-time: 06/07/2026 ۱۰:۱۳–۱۰:۳۹»: ۵ تسک هستهٔ ratified + ۱۹ اسکات + learning-engine-loop + doctor-research + survival-heartbeat. description همین تسک‌ها هنوز می‌گوید «هر ۶ ساعت (throttle با verdict آری 2026-07-06)» ولی فیلد schedule یک‌باره است — یعنی نیّتِ ثبت‌شده (تکرارشونده) با واقعیتِ زمان‌بند (one-shot) نمی‌خواند.

پیامد مکانیکی: تسک one-time بعد از فایر **خودش را disable می‌کند**. همین حالا وسط تخلیهٔ صفیم:

| گروه | وضعیت در لحظهٔ این اجرا |
|---|---|
| فایرشده و خاموش‌شده | ۹ اسکات صبح (mycelium/crypto/mining/lead/ziman/accounting/hypnosis/projectf/ai-watch) · mycelial-consolidator · خودِ fleet-selection |
| در صف (enabled، nextRunAt گذشته، طی دقایق آینده فایر → خاموش) | ۱۰ اسکات دیگر · brain-pulse · brain-focus-board · experience-review · learning-engine-loop · doctor-research · survival-heartbeat |
| تنها cron تکرارشوندهٔ باقی‌مانده | `system-dashboard` (`20 */6` — ولی عمداً disabled، منتظر verdict ۵-یا-۶) + تسک‌های legacy همگی disabled |

یعنی **پس از تخلیهٔ صف امروز، صفر تسک تکرارشوندهٔ enabled باقی می‌ماند** — همان reset سوم، این بار نه با پاک‌شدن زمان‌بند بلکه با self-disable طراحی‌شده. بدون مداخله: نه سنتز شبانه، نه نبض ۶ساعته، نه review هفتگی، نه همین fleet-selection هفتهٔ بعد.

### چرا خودترمیمی §۳.۳ اجرا نشد (تصمیم این اجرا: L1، نه L2)

1. **«حاضر-ولی-one-time/disabled ≠ غایب».** §۳.۳ فقط تسک «غایب» را پوشش می‌دهد؛ سابقهٔ سه‌گانهٔ ردیف‌های ۶۰/۶۲/۸۰ + قاعدهٔ صریح beat consolidator («تصحیح تسک حاضر در لیست سفید L2 نیست») همین را می‌گوید. هفتهٔ پیش دقیقاً همین اجرا با restore عجولانهٔ system-dashboard یک regress خودافشا ثبت کرد — تکرارش نمی‌کنم.
2. **دو مرجعِ cron متناقض:** جدول ratified هنوز کادنس‌های کهنه (۳ساعته) را دارد در حالی که verdict throttle آری (ردیف ledger) کادنس ۶ساعته را مقرر کرده و sync رجیستری هنوز pending است (یافتهٔ v17 برد). restore با کدام cron؟ مبهم → پلهٔ پایین‌تر.
3. مالک همین امروز صبح فعالانه در حال جراحی ناوگان بوده (GO-LIVE، throttle، لغو killswitch) — دستکاری خودکارِ موازی ریسک تداخل دارد.

### HEARTBEAT و کیفیت خروجی‌ها (هفتهٔ منتهی به این اجرا)

- **beatها:** هر ۶ ردیف ratified + learning-engine تازه‌اند (focus-board ~۰۹:۰۰ · pulse ~۰۶:۱۰ · consolidator ~۰۹:۰۱ · review ~۰۴:۲۰ · learning-engine ~۰۸:۴۴ AEST) — **صفر regress-silence**، صفر نقض invariant در کل هفته.
- **کیفیت:** تابلو v17 (hash-diff سالم، دکتر raw ۰) · Brain.md با لینک سنتز شبانه و کهنگی صفر · synthesis 2026-07-06 (خوشه‌های MCP-risk/AUD/Oneflare) · experience-review #۳ (۱۴ pending، حل ابهام Security Gate) · consolidator نقشهٔ مایکوریزایی P12/P13. کیفیت هسته: **خوب و پایدار**.
- **اولین دادهٔ واقعی اسکات‌ها:** ~۱۶ دیجست تازهٔ 2026-07-06 (۵–۹KB، ساختار فرانت‌متردار سالم). برای قضاوت retire/spawn هنوز یک هفتهٔ کامل داده لازم است — ارزیابی کیفی تک‌به‌تک: اجرای بعدی.

### هزینه‌فایدهٔ cron

verdict throttle (بار ~۲۱۲ → ~۴۵ اجرا/روز) جهت درست است و خروجی‌ها افت کیفی نشان نمی‌دهند. ولی تا وقتی تسک‌ها one-time باشند بحث کادنس بلاموضوع است — اول باید تکرارشوندگی برگردد.

### توصیه‌ها (همه L1 propose — verdict آری)

1. **فوری — re-arm تکرارشونده با کادنس throttle‌شده:** brain-focus-board `50 */6 * * *` · brain-pulse `0 */6 * * *` · mycelial-consolidator `0 22 * * *` (یا `0 */6` اگر نیّت throttle این بود — خودش ابهام دارد، description ۶ساعته می‌گوید) · experience-review `30 21 * * 0` · fleet-selection `0 23 * * 0` · learning-engine-loop `35 */6 * * *` · doctor-research `0 */2 * * *` · survival-heartbeat روزانه ۹:۰۰ · ۱۹ اسکات با cronهای روزانهٔ جدول رجیستری (اگر پایلوت ۳۰روزه ادامه دارد). بدون این، پایلوت در روز صفر عملاً متوقف می‌شود.
2. **sync جدول ratified** در AGENT_REGISTRY + RATIFIED-TASKS با cronهای throttle‌شده (pending از v17) — ابهام امروز دقیقاً هزینهٔ همین drift بود؛ تا sync نشود §۳.۳ مرجعِ يکتای بازسازی ندارد.
3. **verdict قطعی ۵-در-برابر-۶** روی system-dashboard (باز از ردیف‌های ۶۰/۸۰ و اجرای دوم همین فایل).
4. **اسکات‌ها:** سیگنال retire/spawn هنوز ناکافی (یک روز داده)؛ اگر توصیهٔ ۱ اجرا شود، اجرای بعدیِ این تسک اولین ارزیابی کیفی کامل ۱۹تایی را انجام می‌دهد.

## مرتبط

- [[05 - Agents/AGENT_REGISTRY|AGENT_REGISTRY]] · [[_memory/HEARTBEAT|HEARTBEAT]] · [[_memory/EXPERIENCE-LEDGER|EXPERIENCE-LEDGER]] · [[00 - Inbox/scout-digests/2026-07-05 synthesis|synthesis 2026-07-05]] · [[00 - Inbox/scout-digests/2026-07-05 experience-review|experience-review 2026-07-05]] · [[00 - Inbox/scout-digests/2026-07-06 experience-review|experience-review 2026-07-06]] · [[00 - Inbox/scout-digests/2026-07-06 synthesis|synthesis 2026-07-06]]
