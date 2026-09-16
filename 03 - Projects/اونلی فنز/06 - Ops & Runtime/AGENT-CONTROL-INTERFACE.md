---
type: control-interface
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
audience: MASTER orchestrator agent (the Architect / رئیس‌کل)
created: 2026-07-10
created_by: agent (Claude Fable 5)
machine_contract: "[[PROJECT-F-CONTROL-MANIFEST.json]]"
tags: [project-f, control-interface, agent-to-agent, architect, governance]
aliases: ["Control Interface", "رابط کنترل", "Master Agent Interface"]
---

# رابطِ کنترلِ Project-F برای ایجنتِ مادر (Architect)

> این سند برای **ایجنتِ مدیریتِ کلِ پروژه‌ها** است تا بفهمد این‌جا چه ساخته شده و **چطور امن کنترلش کند**. قرارداد ماشین‌خوان و کانونی: `PROJECT-F-CONTROL-MANIFEST.json` (اول آن را بخوان). این فایل روایتِ همان است.
> **قاعدهٔ PII:** این دو فایل صفر هویت/محتوا دارند؛ شرکا فقط با کد **A=Operator** و **C=Creator**. بیرون از این پوشه فقط «Project-F». هرگز کد را باز نکن.

---

## ۱. در یک نگاه — این‌جا چه ساخته شده
Project-F یک node در اکوسیستمِ توست: کسب‌وکارِ **faceless فقط‌پا (غیر-explicit)**، تیمِ دونفرهٔ A/C، فازِ **validation**، **صفر اجرا** تا الان. سه لایه ساخته و تست شده (۲۹ تستِ سبز):

1. **مغز (`brain/`)** — control-plane + ۷ زیرعامل + دو Guard (Compliance/Ethics) + لایهٔ **یادگیرندهٔ اکتشاف‌دار** (Thompson/UCB bandit، از greedy ۴۹٪ بهتر). propose-only.
2. **کاکپیتِ A (`langar/`)** — رابطِ تلگرامیِ **خودآگاه**: وضعیت، گیت‌ها، صفِ verdict، پلِ صبا، پیشنهادِ ارتقای هفتگی. propose-only، OpsecGuard، kill-switch.
3. **استودیوی C (`studio/saba_studio.py`)** — رابطِ تلگرامیِ **جدا**: ثبتِ درفت، تقویم، ترند، ظرفیت، توقفِ مرزی. propose-only، صفر رسانه/PII.

هر سه با موتورِ مشترک (`ContentStudio` + فایل‌های state) و با هم سیم‌کشی‌اند؛ منبعِ حقیقت = فایل‌ها (نه کانِن دوم).

---

## ۲. مدلِ کنترل — تو چه می‌توانی و چه **نمی‌توانی**
کنترلِ تو بر این پروژه با همان survival-filterِ خودِ پروژه محدود است. سه فعلِ مجاز، یک لیستِ ممنوع.

**✅ مجاز (خودمختار):**
- **Observe:** خواندنِ کلِ state، گرفتنِ status از کاکپیت/استودیو، خواندنِ `explain()` مغز برای شفافیت.
- **Task (propose-only):** سپردنِ کارِ تحقیق/درفت/تحلیل به لایه‌های propose-only؛ خروجی همیشه *پیشنهاد* است، نه اجرا.
- **Kill:** فعال‌کردن هر kill-switch (کاکپیت/استودیو/بودجه).

**⛔ ممنوعِ مطلق برای تو (مثلِ هر ایجنتِ دیگر):**
- اجرای هر اکشنِ بیرونی (ساخت اکانت، پست، DM، پرداخت، login).
- دورزدنِ **GATE 0** یا هر Hard-Gated.
- **self-approve** کردنِ موردِ hard-gated به‌جای انسان — تو فقط به انسان route می‌کنی.
- تغییر/تضعیفِ هر یک از ۸ قاعدهٔ قفل‌شده.
- هر echo هویت/محتوا بیرون از پوشه.

> خلاصه: تو **رصدگر + صف‌بند + قطع‌کنِ اضطراری** هستی، نه مجری. مجریِ نهاییِ هر کارِ پرمخاطره = انسان (A).

---

## ۳. چطور رصد کنی (Observe)
ترتیبِ لودِ اجباری (طبق منشور): `_memory/…memory….md` → `STATE-REPORT-2026-07-05.md` → `CLAUDE.md` → `PROJECT.md`. جهت‌یابی: `INDEX.md`.
- **وضعیتِ زنده:** `PROJECT.md` بخشِ Active Context + `DecisionLog.md` (آخرین بندها).
- **صفِ تصمیم:** `THREAD-CLOSURE-D-2026-07-10.md §۹` (۱۱ verdictِ منتظر) و `OpenQuestions.md`.
- **از راهِ کاکپیت (اگر فعال):** `/status` · `/gates` · `/verdicts` · `/saba` · `/kpi`.
- **پلِ استودیو (فایل‌محور):** درفت‌های منتظر در `studio/drafts.json`، اعلان‌های C در `studio/to_ari.json`، وضعیتِ توقف در `studio/HALT`.

---

## ۴. چطور فرمان بدهی (Command)
همه از طریقِ سطحِ کنترلِ propose-only/فایل‌محور. هیچ actuatorی اکشنِ بیرونی نمی‌زند.

| هدف | چطور | اثر |
|---|---|---|
| گرفتنِ وضعیت | کاکپیت `/status`,`/gates` یا خواندنِ PROJECT.md | فقط‌خواندنی |
| دیدنِ کارِ منتظرِ C | کاکپیت `/saba` یا خواندنِ `studio/drafts.json` | فقط‌خواندنی |
| سپردنِ تحلیل | مغز `process_draft()` / `AcquisitionBrain.plan_week()` / `LearningBridge.recommend()` | خروجی = پیشنهاد |
| پاسخ به C | افزودنِ `{date,text}` به `studio/for_saba.json` | C در inbox می‌بیند |
| توقفِ اضطراریِ کاکپیت | `/kill` یا `touch langar/KILL` | کاکپیت جز /status,/revive رد می‌کند |
| توقفِ اضطراریِ استودیو | `touch studio/HALT` | استودیو halt؛ A مطلع |
| قطعِ خرجِ LLM | سقفِ AUD 15/ماه (fail-closed) | تماس LLM بلاک |
| route کردنِ verdict به انسان | ثبت در DecisionLog + flag `⚑ برای معمار` | منتظرِ حکمِ A |

---

## ۵. kill-switch و بودجه (کنترلِ ایمنی)
- **کاکپیت:** `/kill` / فایلِ `langar/KILL`.
- **مرزِ C (مقدمِ مطلق):** `/halt` / فایلِ `studio/HALT` — محدودهٔ C همیشه بر همه‌چیز مقدم است.
- **بودجه:** ابزار AUD 100/ماه · LLMِ کاکپیت AUD 15/ماه تا اولین درآمد · مغز ۲٪-cap توکن — همه fail-closed.
- **اخطارِ پلتفرم = توقفِ فوریِ همان اتوماسیون** + ثبت در DecisionLog (قاعدهٔ منشور).

---

## ۶. پروتکلِ تشدید (Escalation)
- **پروژه به تو flag می‌زند** وقتی چیزی با قاعدهٔ قفل‌شده تضاد دارد → اجرا نمی‌شود، با تگِ منبع flag و جایگزینِ امن.
- **تو باید به انسان (A) تشدید کنی برای:** تصمیمِ GATE 0 · هر Hard-Gated · هر تغییرِ قاعدهٔ قفل‌شده · هر اخطارِ پلتفرم · هر تصمیمِ قیمت/آفر.
- **تو خودمختار می‌توانی:** رصد، درخواستِ status، سپردنِ کارِ propose-only، فعال‌کردنِ kill-switch، اجرای تست‌ها.

---

## ۷. اجرا و تست (برای تأییدِ سلامت)
```
cd brain  && python3 -m unittest test_learning -v      # 11 tests
cd langar && python3 -m unittest test_langar -v        # 8 tests
cd studio && python3 -m unittest test_saba_studio -v   # 10 tests
```
- entrypointها: `python3 langar/langar_bot.py` · `python3 studio/saba_studio.py` · `python3 orchestrator.py`.
- ⚠️ `orchestrator.py` به `_ops/neural` (سطحِ vault) وابسته است؛ فقط با vaultِ کامل اجرا می‌شود. باتِ کاکپیت/استودیو و ماژول‌های learning مستقل‌اند.
- فعال‌سازیِ تلگرام = اکشنِ بیرونی (BotFather) = انسان؛ سپس یک هفته shadow-mode قبل از live.

---

## ۸. نقاطِ اتصالِ توصیه‌شده به رجیستریِ تو
- این پروژه را در رجیستریِ خود با **کدِ «Project-F»**، فایلِ قرارداد `PROJECT-F-CONTROL-MANIFEST.json`، و وضعیتِ `phase=validation، GATE 0=open` ثبت کن.
- برای «سلامت‌سنجیِ» دوره‌ای: اجرای سه سوییتِ تست + خواندنِ `PROJECT.md` Active Context.
- برای «داشبوردِ ناوگان»: از `status_snapshot` و `open_pending_verdicts` در manifest تغذیه کن (هر دو صفر-PII).
- هر به‌روزرسانیِ بزرگ در این پروژه، این manifest و `INDEX.md` را هم آپدیت می‌کند؛ manifest را به‌عنوان single-source برای cross-domain بخوان.

---
*این رابط، Project-F را برای مدیریتِ مادر شفاف می‌کند بی‌آنکه هیچ قاعدهٔ قفل‌شده یا حریمی را بشکند. کنترلِ مادر = رصد + صف + قطع؛ اجرا هرگز. GATE 0 همچنان بلاکرِ همه‌چیز.*
