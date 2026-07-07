---
type: report
status: done
tags: [selfimprove, review]
created: 2026-07-05
updated: 2026-07-05
task: experience-review
run: "2026-07-05 ~21:35 AEST (اولین اجرای زنده) + بازاجرای ۲ catch-up ~۲۳:۵۴ AEST (دلتا در §۸)"
---

# Experience Review — دیجست هفتگی verdict (2026-07-05)

> **propose-only** — هیچ درسی اعمال نشد، هیچ ردیفی در ledger افزوده/بازنویسی نشد. تنها نوشته‌های این اجرا: همین دیجست + سطرِ خودِ experience-review در [[_memory/HEARTBEAT|HEARTBEAT]] (مشتق، §۸.۳). مرجع: [[00 - Inbox/Prompt - منشور استقلال مغز (Autonomy Ladder)|منشور]] · [[_memory/EXPERIENCE-LEDGER|EXPERIENCE-LEDGER]] · [[05 - Agents/AGENT_REGISTRY|AGENT_REGISTRY]].

> ⬆ **بازاجرای ۲ (~۲۳:۵۴):** pending ۱۱→**۱۲** · system-dashboard **دوباره enabled** شد (disable ماندگار نیست) · fleet-selection اجرای امشب را از دست داد → «Run now» لازم. جزئیات: §۸ پایین؛ اعداد بخش‌های ۰–۷ مالِ اجرای ۲۱:۳۵‌اند.

## ۰) TL;DR (فقط استثناها — §۶)

- **AUTONOMY: on** · **۰ نقض invariant** ✅ · ناوگان **۶/۶ ratified حاضر** → restore لازم نشد.
- **۱۱ ردیف pending-verdict** منتظر آری (۸ از build-loop + ۲ observe + ۱ regress). این **اولین** اجرای بازوی verdict است، پس هنوز هیچ pending→applied کامل نشده.
- **۳ self-correctionِ خودکار** (ردیف ۴۷/۵۴/۶۳) همه تمیز، revert لازم نیست · **صفر** ردیفِ formal §۳.۴ `auto-applied` → خزشِ دامنهٔ self-verdict رخ **نداده**.
- دو drift پایدار منتظر verdict: `system-dashboard` (ratified ولی disabled) و `build-planner-loop` (enabled ولی خارج ratified).
- گلوگاهِ ساختاری همچنان **rotation** (کار مالک): git-init → L2 fleet-restore را قفل کرده.
- ⚠️ **هشدارِ نو:** `build-planner-loop` امروز ۸ ردیفِ pending تولید کرد و اکنون در «حالتِ تحقیقِ پیوسته»ی بی‌انتهاست → رشدِ pending سریع‌تر از نرخِ پاکسازیِ بازوی هفتگی.
- 🔁 **متا:** همین review در خواندنِ آخرین ردیفِ ledger به stale-viewِ سندباکس خورد (mount دُم‌بریده، Windows-side کامل) → تأییدِ زندهٔ دوبارهٔ قاعدهٔ fresh-inode/verify؛ اعداد این دیجست از خواندنِ Windows-side است.

## ۱) pending-verdictها (۱۱ — توصیه؛ verdict با آری)

> ارجاع با شمارهٔ خطِ ledger (قاعدهٔ «ردیف NN» vault).

| ردیف | نوع | خلاصه | توصیه | دلیل یک‌خطی |
|---|---|---|---|---|
| ۵۰ | regress | «reset سوم» + قفلِ git/rotation روی L2 restore | ✅ بپذیر (درسِ ساختاری) | جزءِ «۳ غایب» را ردیف ۵۴ باطل کرد؛ ولی گیت‌بندیِ git-init پشتِ rotation معتبر و کلیدی است |
| ۵۳ | propose | codepack موج۱ Fable5 (M0–M3، همه MOCK) | ✅ بپذیر | کم‌شعاع (fusion-MOCK)؛ آمادهٔ Fable 5 |
| ۵۵ | propose | codepack موج۲/۳ (M4·M6·M5·M7·M8) | ⚠️ بپذیر با گارد | موج۲ کدِ باتِ **زنده** را لمس می‌کند → پشتِ M5 + rotation نگه‌دار |
| ۵۶ | propose | Reflexion روی MASTER-SPEC (۳ ضعف) | ✅ بپذیر به‌عنوان ورودی | هر ۳ ضعف معتبر (M5→موج۰ · گاردِ delete فقط policy · گپِ دامنهٔ validator) → ادغام در spec v0.2 |
| ۵۷ | propose | runbook امنِ git-init + `.gitignore` سخت | ⛔ بپذیر ولی **بلاک‌شده** | آماده؛ اجرا معطلِ تکمیلِ rotation (کارِ مالک، نه ایجنت) |
| ۵۸ | research | P-05 provenance + بلوکِ constitution | ✅ بپذیر | گپِ امنیتیِ حافظهٔ مسموم / safety-loss در compaction؛ در constitution v0.2 |
| ۵۹ | research | P-06 opsec/rotation (OWASP ۴-گام) | ✅ بپذیر | تأییدِ بیرونیِ «حذف≠چرخش» (ردیف ۴۹/۵۰)؛ runbook برای مالک |
| ۶۰ | observe | تناقضِ system-dashboard (ratified ↔ disabled) | ✅ **گزینهٔ الف** | حذف از جدولِ ratified + disableِ پایدار؛ عملاً در CONTROL-PANEL ادغام شده |
| ۶۱ | propose | REVIEW-PACKET (V1–V6) | ✅ بپذیر = **سطحِ تصمیم** | همهٔ پیشنهادها را یک‌جا در یک جلسه پردازش کن (به‌جای ۸ verdict جدا) |
| ۶۲ | observe | build-planner-loop خارج ratified، enabled | ⚠️ **تصمیم لازم** | یا افزودن به ratified (propose-only) یا خاموشیِ رسمی + مهارِ سیلِ pending |
| ۶۴ | research | P-08 durable-execution / idempotency-key | ✅ بپذیر | durable-checkpoint = ریشهٔ حفرهٔ bootstrap (ردیف ۴۴/۵۰)؛ در EffectorGate/spec v0.2 |

**جمع‌بندی:** ۸ مورد آمادهٔ accept، ۲ نیازمندِ تصمیمِ الف/ب (۶۰ و ۶۲)، ۱ بلاک‌شده پشتِ rotation (۵۷). مسیرِ کارا = **پردازشِ REVIEW-PACKET (ردیف ۶۱)** که ۵۳–۵۹ + ۶۴ را در یک برگه جمع کرده.

## ۲) auto-applied / self-healed این هفته (برجسته — §۳.۴)

| ردیف | گذار | مورد | revert؟ |
|---|---|---|---|
| ۴۷ | regress→applied | ابطالِ annotation غلطِ v10 روی DecisionLog (خرابیِ UTF-8 **واقعی** بود، نه stale) + سخت‌سازیِ قاعدهٔ verify | خیر (زیرْاقدامِ مالک: باز/ذخیره در Obsidian) |
| ۵۴ | regress→applied | ابطالِ «reset سوم»ِ ردیف ۵۰ (لیستِ زنده ۶/۶ داد) + قاعدهٔ کراس‌چک با beatِ خواهران | خیر |
| ۶۳ | tune→applied | رفعِ **بیش‌تعمیمِ** fresh-inode (اسکریپتِ ROOT-نسبی باید in-place اجرا شود) | خیر |

- **بازرسیِ خزشِ دامنه §۳.۴:** هر سه در لایهٔ **تشخیص/گزارش/قاعدهٔ‌عملیاتی**‌اند — هیچ‌کدام پرامپتِ canonical / charter / schema / secret را لمس نکرد. **پاک، بدون creep.**
- **formal `auto-applied` (§۳.۴ چهارشرطی):** **صفر** ردیف — self-verdictِ خودکارِ درسِ نمایشی هنوز فعال نشده (طبیعیِ هفتهٔ ۱).
- **رندرهای L3 تابلو:** v12→v14 با hash-diff + گاردِ parse/secret، همه تمیز؛ دو CRITICAL گذرای v13 در v14 خودترمیم شد (تأییدِ سومِ stale-view).

## ۳) شاخصِ استقلال (§۷ منشور — مبنای هفتهٔ ۱)

| شاخص | مقدار | هدف / یادداشت |
|---|---|---|
| سهمِ applied بی‌لمسِ انسانی | **۰٪** سخت‌گیرانه (§۳.۴) · ~**۱۱٪** گسترده (۳ self-correctionِ auto از ۲۷ applied) | هدف >۵۰٪ در ۴ هفته — هفتهٔ ۱ مبنا |
| میانگینِ pending→applied | **N/A** | هیچ pending هنوز چرخه را کامل نکرده (اولین review؛ هر ۱۱ pending <۲۴ساعت) → سنجش از هفتهٔ بعد |
| self-heal موفق ÷ reset | restoreِ خودکار=**۰** · resetِ واقعیِ auto=**۰** (ناوگان ۶/۶) · خطای‌مثبتِ reset مهارشده=**۱** (۵۰→۵۴) | restore تا rotation عملاً تعاملی |
| نقضِ invariant | **۰** ✅ | هدف محقق (secret پاک · محدودهٔ منفی محترم · ledger append-only · بدون اکشنِ خارجی) |

## ۴) HEARTBEAT — نبضِ ناوگان

| task | دوره | آخرین beat | وضعیت |
|---|---|---|---|
| brain-focus-board | ۳س | ~۲۰:۰۸–۲۰:۴۰ AEST | ✅ سالم (nextRun ~۲۱:۵۵) |
| brain-pulse | ۳س | ~۲۱:۱۰ AEST | ✅ سالم |
| system-dashboard | ۶س | ~۲۰:۳۰ AEST | ⚠️ اکنون **disabled** → سکوت **عمدی**، بدون regress |
| mycelial-consolidator | ۲۴س | — | ⏳ اولین اجرا امشب ~۲۲:۰۲ (مهلتِ اولین beat) |
| experience-review | ۷ر | **~۲۱:۳۵ AEST (همین اجرا)** | ✅ اولین beat ثبت شد |
| fleet-selection | ۷ر | — | ⏳ اولین اجرا امشب ~۲۳:۰۱ (مهلت) |

- **هیچ regress-silence** در جدول. سه تسکِ شبانه/هفتگی در مهلتِ اولین beat‌اند (امشب fire می‌شوند).
- سناریوی «همه بی‌beat = ابزار pre-approve نشده» **منتفی است:** brain-focus-board و brain-pulse (و build-planner-loop) امروز چند بار fired و beat زدند (lastRunAt تازه) → ابزارها pre-approve‌اند و پیش‌شرطِ **تستِ پذیرشِ §۸.۶** (۲ beat موفق) در حالِ تحقق. نیازی به «Run now»ِ اضطراری نیست.

## ۵) drift ناوگان (تاریک/روشن — §۴ تسک)

- **۱۹ اسکات + ۶ لاین selfimprove:** در اسناد «تاریک»، در زمان‌بند هم **غایب** → **بدون drift** (هم‌خوان). پیشنهادِ retire/keep لازم نیست؛ همه درست تاریک‌اند.
- زمان‌بندِ زنده به **۷ تسک** تثبیت شده (۶ ratified + build-planner-loop) — از هرج‌ومرجِ «۴۹ تسک/۳۴ enabled»ِ بامداد (ردیف ۴۹) پاک شده؛ تسک‌های Research Radar×۳ / survival-heartbeat / bio-synthesis (drift ردیف ۵۶) **دیگر نیستند**.
- **دو drift باقی (هر دو pending، verdict آری):**
  - `system-dashboard` → در جدولِ ratified هست ولی زنده **disabled** → توصیه: **حذف از جدولِ ratified** (گزینهٔ الف ردیف ۶۰) تا self-heal §۳.۳ دیگر «غایب» نپندارَدش.
  - `build-planner-loop` → **enabled** ولی خارجِ جدولِ ratified → توصیه: ratify (propose-only) **یا** خاموشی؛ ضمناً سیلِ pending را مهار کن.

## ۶) اثرِ چرخه، جدا از گیتِ انسانیِ rotation (قاعدهٔ ledger)

- `health_score` روی **۵۱** ثابت است چون بازوی انسانیِ **rotation** باز است — این **شکستِ چرخه نیست** (قاعدهٔ سنجشِ ردیف ۹/۱۸). متریکِ چرخه = همین جدولِ ledger، نه health_score.
- **متریکِ خودِ چرخه:** ۳۹ ردیفِ ledger (۲۷ applied · ۱۱ pending · ۱ info) + اجرای تمیزِ لایهٔ autonomy (۰ نقض · رندرهای idempotent · ۳ self-correctionِ کارآمد).
- **گلوگاهِ واحد = rotation (مالک):** git-init را قفل کرده → L2 fleet-restore را قفل کرده → restore تعاملی/propose-only مانده. همگراییِ مستقلِ ردیف‌های ۴۹/۵۰/۵۷/۵۹ روی همین نقطه.

## ۷) اقدامِ مالک (اولویت‌دار)

1. **تکمیلِ rotation** ([[ROTATION_CHECKLIST]]) — بالاترین اهرم: هم‌زمان git-init + Security Gate + L2 restore + کلیدهای Lead/Crypto/Mining را باز می‌کند.
2. **verdict روی دو drift:** system-dashboard = حذف از ratified (گزینهٔ الف) · build-planner-loop = ratify-یا-خاموشی + سقفِ pending.
3. **پردازشِ REVIEW-PACKET** (ردیف ۶۱): V1–V6 + P-08 در یک جلسه → همگرایی به spec/constitution **v0.2**.
4. (اختیاری) تأییدِ چشمیِ اولین beatِ mycelial-consolidator (~۲۲:۰۲) و fleet-selection (~۲۳:۰۱) امشب.

---

**منابع:** [[_memory/EXPERIENCE-LEDGER|EXPERIENCE-LEDGER]] (۳۹ ردیف) · [[_memory/HEARTBEAT|HEARTBEAT]] · [[05 - Agents/AGENT_REGISTRY|AGENT_REGISTRY]] (جدولِ ratified) · [[00 - Inbox/Prompt - منشور استقلال مغز (Autonomy Ladder)|منشور §۳/§۵/§۷/§۱۰]] · خروجیِ زندهٔ زمان‌بند (۷ تسک، ۲۰۲۶-۰۷-۰۵ ~۲۱:۳۵ AEST).

## ۸) بازاجرای ۲ — catch-up ~۲۳:۵۴ AEST (دلتا نسبت به اجرای ۲۱:۳۵)

> زمان از lastRunAtِ زمان‌بند `13:54:51Z` (نه `date` سندباکس). علتِ دو اجرا: fireِ جبرانی پس از بیداری/ری‌استارتِ host — سه تسک هم‌ثانیه (13:54:51–52Z)، همان الگوی «اجرای جبرانی» ردیف ۶۲ و مصداقِ زندهٔ P-08 (ردیف ۶۴). لیستِ زنده **×۲ متوالی** خوانده شد (قاعدهٔ re-listِ ردیف ۵۴).

| # | دلتا | جزئیات / توصیه |
|---|---|---|
| ۱ | pending: ۱۱ → **۱۲** | ردیف **۶۵** (P-09 حافظهٔ دوفازی + retrieval هیبرید/RRF/rerank) پس از اجرای ۱ افزوده شد. توصیه: ✅ بپذیر — جزءِ «لایهٔ consolidated که orientation از آن بخواند» مستقیماً context-rotِ خودِ حلقه را کم می‌کند (کنارِ P-05/P-08 در spec v0.2). ledger اکنون **۴۰ ردیف** (۲۷ applied · ۱۲ pending · ۱ info) |
| ۲ | ⚠️ system-dashboard **دوباره enabled** | لیستِ زنده (×۲) enabled با nextRun ~۰۰:۲۹ بامداد؛ description همچنان «بازنشسته/disabled». v15 (~۲۱:۵۶) آن را «disabled پایدار» دیده بود → **disable در برابرِ reset/restart ماندگار نیست**. این یافته استدلال را به نفعِ **گزینهٔ الفِ ردیف ۶۰ به‌شکلِ سخت** جابه‌جا می‌کند: حذف از جدولِ ratified + **حذفِ تسک** (نه صرفاً disable). تا verdict، هر اجرایش طبق ردیف ۶۰ propose-only می‌ماند (بنرِ جانشین حفظ) |
| ۳ | ⚠️ fleet-selection اجرای امشب (~۲۳:۰۱) را **از دست داد** | بدون lastRunAt؛ nextRunAt پرش به **2026-07-12** (host هنگام 13:01Z خواب بود؛ catch-up فقط سه تسکِ پرتکرار را گرفت). هنوز regress-silence نیست (آستانه ۲×۷روز) ولی بدونِ مداخله تا یک هفته بی‌beat می‌ماند → **اقدامِ مالک: یک «Run now»** |
| ۴ | ✅ mycelial-consolidator اولین beat را زد | ~۲۲:۰۲ AEST، synthesis نوشته شد؛ لیستِ زنده lastRunAt ندارد ولی طبق قاعدهٔ ردیف ۵۴ با beatِ HEARTBEAT کراس‌چک شد؛ nextRun فردا ۲۲:۰۲ سازگار → reset نیست |
| ۵ | build-planner-loop از لیستِ زنده **غایب** شد | اجرای ۱ آن را enabled دیده بود؛ غیر-ratified → طبق قاعدهٔ سخت restore **نشد**؛ عملاً خاموش. verdict ردیف ۶۲ همچنان باز، ولی نگرانیِ «سیلِ pending» فعلاً خودمهار شد |
| ۶ | ناوگان ratified | **۶/۶ حاضر** (این‌بار هر ۶ enabled) → restore لازم نشد · ۰ نقضِ invariant · propose-only، ledger دست‌نخورده — درسِ «ماندگارنبودنِ disable» همین‌جا ثبت شد؛ append به ledger با تشخیصِ boardِ بعدی یا verdictِ آری |

**به‌روزرسانیِ اقدامِ مالک (جایگزین بندهای مرتبط §۷):** (۱) **Run now** برای fleet-selection؛ (۲) verdictِ الف/بِ system-dashboard — ترجیحاً پیش از fireِ بعدی‌اش (~۰۰:۲۹)؛ (۳) بقیه طبق §۷.
