---
type: proposal
status: active
subject: "مدل دو مغز (انسانی + دکتر) و حلقهٔ کنترل مشترکِ مغز دوم"
tags: [doctor, autonomy, two-brain, control-loop, architecture]
created: 2026-07-05
updated: 2026-07-06
related: "[[00 - Inbox/Prompt - دکتر مغز تکاملی (Evolutionary Doctor) 2026-07-05|دکتر تکاملی]] · [[00 - Inbox/Prompt - منشور استقلال مغز (Autonomy Ladder)|منشور استقلال]] · [[00 - Inbox/Prompt - لایه شناخت زمینه (Ground-Truth Perception Layer)|لایهٔ شناخت]] · [[_memory/LIVING-BRAIN-BLUEPRINT|LIVING-BRAIN-BLUEPRINT]] · [[00 - Inbox/SYSTEM-STATE-2026-07-05|SYSTEM-STATE]]"
---

# TWO-BRAIN-CONTROL-BLUEPRINT — دو مغز، یک حلقهٔ کنترل

> نقشهٔ مشترکِ کنترلِ «مغز دوم». سنتزِ سه سندِ موجودِ خودت (دکتر تکاملی + منشور استقلال + لایهٔ شناخت) در یک مدلِ اجراییِ کوچک که روی ارتیفکتِ زندهٔ `fleet-live-dashboard` سوار است.
> **status: active — مالک 2026-07-06 گفت «پیشنهاد تو پیش برویم» → هر ۴ verdict §۷ با توصیهٔ ایجنت بسته شد.** سند اجراییِ ساخت: [[_memory/FRANKENSTEIN-BUILD-PLAN|FRANKENSTEIN-BUILD-PLAN]].

## ۱. دو مغز و تقسیمِ اقتدار

| مغز | نقش | مالکِ چه چیزی است | فرکانس/اقتدار |
|---|---|---|---|
| 🧑‍✈️ **انسانی (آری)** | قاضی و قطب‌نما | تعریفِ «بهتر» (تابع برازندگی) · مرزِ invariantها · §Security Gate و charter (**human-only**) · بودجه · kill-switch | کم‌فرکانس، **اقتدارِ نهایی** |
| 🩺 **دکتر (Evolutionary Doctor)** | ادراک + تشخیص + پیشنهاد + خودترمیمیِ محدود | ۳ ستون: (۱) نگهبانِ سلامت [قطعی، صفر-LLM] · (۲) کاشفِ جهش · (۳) حلقهٔ فکری | پرفرکانس، **اقتدارِ محدود** (فقط پشت whitelist) |

اصل: انسان **ارزش و جهت** می‌دهد؛ دکتر **ادراک و کار** می‌کند. هیچ‌کدام جای دیگری را نمی‌گیرد.

## ۲. حلقهٔ کنترلِ مشترک

```
   ┌──────────────────────────────────────────────────────────┐
   ▼                                                          │
① ادراک ──▶ ② تشخیص ──▶ ③ پیشنهاد ──▶ ④ verdict ──▶ ⑤ اعمال ──▶ ⑥ سنجش ─┘
(SYSTEM-STATE)  (دکتر)     (دکتر,        (آری)      (L2/L3       (برازندگی+
                          propose-only)             محدود)       استقلال+health)

   گاردهای دورِ حلقه: §Security Gate · git rollback (پیش‌شرطِ ⑤) · kill-switch ۳سطحی · ledger append · دفاعِ تزریق
```

| گام | چیست | کجا انجام می‌شود (سندِ موجود) |
|---|---|---|
| ① ادراک | فایل‌سیستم + زمان‌بندِ زنده → یک نقشهٔ واحد | لایهٔ شناخت → [[00 - Inbox/SYSTEM-STATE-2026-07-05\|SYSTEM-STATE]] |
| ② تشخیص | سلامتِ قطعی (ستون۱) + کشفِ جهش (ستون۲) | `dashboard_doctor.py` + Mutation Ledger (آینده) |
| ③ پیشنهاد | حداکثر‌اهرم، propose-only (L1) | پنلِ ارتیفکت (`askClaude`) |
| ④ verdict | accept/reject انسانی | پنلِ ارتیفکت (`sendPrompt`) یا چت |
| ⑤ اعمال | فقط whitelist منشور، یا human-directed | نردبان §۳ |
| ⑥ سنجش | تابع برازندگی + شاخص استقلال + health | تابلو + [[_memory/EXPERIENCE-LEDGER\|ledger]] |

## ۳. تقسیمِ اقتدار = نردبانِ استقلال (قبلاً ratified)

L0 گزارش · L1 پیشنهاد · **L2 bounded-auto** (فقط لیست سفیدِ §۳ منشور) · **L3** مشتقِ idempotent. دکتر همیشه در L0–L1 کار می‌کند؛ ورود به L2/L3 فقط **پشتِ Gate + git**. لیستِ سیاه (charter/secret/پول/پیامِ خارجی/تغییرِ گیت) = **همیشه human-only**. مرجع: [[00 - Inbox/Prompt - منشور استقلال مغز (Autonomy Ladder)|منشور]].

## ۴. اتصال به ارتیفکت (کابینِ مشترک)

| لایه | کجای `fleet-live-dashboard` | وضعیت |
|---|---|---|
| ادراک | آشتیِ زندهٔ ۴کلاسه + KPI + بنر Gate | ✅ هست |
| صدای دکتر | پنلِ `askClaude` (propose-only) | ✅ هست |
| verdict/dispatch انسان | `sendPrompt` + Run now (`runScheduledTask`) + Emergency Stop | ✅ هست |
| حلقه | دیاگرام «♻️ حلقهٔ کنترل مشترک» | ✅ افزوده شد |

ارتیفکت = **تنها جایی که هر دو مغز هم‌زمان می‌بینند و عمل می‌کنند** — کابینِ خلبانِ مشترک.

## ۵. ترتیبِ ساخت (وفادار به گیت‌های موجود)

1. **فاز ۰ (اکنون):** ادراک (`SYSTEM-STATE`) + کابین (ارتیفکت + پنلِ دو مغز) + بازسازیِ watchdog (`brain-focus-board`,`experience-review`). — **جاری/انجام‌شده.**
2. **فاز ۱ (human-only، آزادکننده):** بستنِ §Gate (ویرایشِ دستیِ charter) + `git init` → L2 و rollback ممکن می‌شود.
3. **فاز ۲:** سخت‌کردنِ ستون۱ دکتر + زمان‌بندیِ `SYSTEM-STATE` به‌عنوان منبعِ ادراکِ همیشه‌تازه.
4. **فاز ۳:** ستون۲ — «جهش‌نامه» (Mutation Ledger): قرنطینهٔ ناهنجاری، آری برازندگی را رأی می‌دهد.
5. **فاز ۴:** ستون۳ — حلقهٔ فکریِ خودمختار، **پشتِ Gate + git + سقفِ بودجه**.

هر فاز فقط با verdict وارد فاز بعد می‌شود.

## ۶. متریکِ موفقیت

شاخصِ استقلال (هدف: >۵۰٪ درسِ کم‌ریسکِ applied بدون لمسِ انسانی در ۴ هفته) · **صفر نقضِ invariant** · health پایدار · نسبتِ promote÷revert جهش · هزینه به‌ازای چرخه.

## ۷. verdictها — بسته‌شده 2026-07-06 («پیشنهاد تو پیش برویم»)

1. **تابع برازندگی** ✅ — کیفی می‌ماند (درآمد/خروجیِ پروژه‌ها + سادگی/سرعتِ workflow)؛ آستانهٔ عددی **بعد از ~۴ هفته دادهٔ EXPERIENCE-LEDGER** کالیبره می‌شود، نه الان (عدد بدون داده = دعوت به metric-gaming — یافتهٔ [[07 - Knowledge/_doctor-research/fitness-function-design|P1]]).
2. **اولین فاز بعد از گیت** ✅ — **فاز ۲**: ادراکِ زمان‌بندی‌شده. تسک `perception-refresh` ساخته شد (هر ۲ ساعت، propose-only، فقط `_memory/SYSTEM-STATE.md` را بازتولید می‌کند) — چون کم‌ریسک است، پیش‌نیاز گیت ندارد، از امروز فعال.
3. **موتورِ ستون۳** ✅ — **Claude پلکانی**: Haiku برای ادراک/روتین → Opus/Fable 5 فقط برای تحلیلِ سختِ جهش. Fugu **پیش‌فرض نیست**؛ فقط escalation اختیاری پشتِ سقفِ بودجهٔ روزانه (راستی‌آزمایی وب 2026-07-06: Fugu واقعی است ولی Ultra ضریب پنهان ۵–۱۵× توکن دارد → ناسازگار با سقف AU$30/ماه D-25 به‌عنوان پیش‌فرض؛ ضمناً Fugu خودش Claude را صدا می‌زند، پس دوگانهٔ مطلق نیست).
4. **ریتمِ حلقه** ✅ — **burstهای زمان‌بندی‌شدهٔ کران‌دار**، نه daemon: هر burst = ۳–۵ round، بودجهٔ سخت per-cycle، kill-switch هر round، کفِ همگرایی دو-دوره (یافتهٔ [[07 - Knowledge/_doctor-research/loop-rhythm-convergence|P5]]: trigger-not-tick؛ polling پیوسته ۵–۱۰× گران‌تر) — سازگار با قید «فقط وقتی اپ باز است».

## مرتبط

- [[00 - Inbox/Prompt - اهداف دکتر مغز تکاملی (Evolutionary Doctor)|اهداف دکتر (۴ تصمیم قفل)]] · [[05 - Agents/AGENT_REGISTRY|AGENT_REGISTRY]] · [[01 - Dashboard/HANDOFF|HANDOFF]] · ارتیفکت: `fleet-live-dashboard`
