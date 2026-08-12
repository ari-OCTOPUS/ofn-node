---
type: spec
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: built (activation awaiting verdict — §۹ ردیف ۱۰ THREAD-CLOSURE)
created: 2026-07-10
created_by: agent (Claude Fable 5)
relates_to: "[[architecture-blueprint-2026-07-04]] (معماری اصلی) · [[PROJECT-F-BRAIN-SPEC]] · orchestrator.py · studio/studio_telegram_v3.py · CLAUDE.md"
tags: [project-f, langar, telegram, cockpit, self-aware, hitl]
aliases: ["Langar", "لنگر", "Cockpit"]
---

# لنگر (LANGAR) — کاکپیت تلگرامیِ خودآگاه آری

> «لنگر» = رابط تلگرامی آری با مغز Project-F: **خودآگاه** (مدل زنده‌ای از وضعیت خودش و پروژه دارد)، **مسئول ارتقا** (هفتگی برای بهبود خودش و پروژه proposal می‌سازد)، و **همیشه propose-only**. ایده‌ها از معماری اصلی: چهار لایه/گیت‌های عددی بلوپرینت §۳، کنترل-پلین + دو Guard از BRAIN-SPEC، الگوی تلگرام از studio_telegram_v3 (stdlib-only، ‏$0، صفر رسانه/PII).

## ۱. جایگاه در معماری (بلوپرینت §۳ + BRAIN-SPEC §۱)
```
🎬 استودیوی صبا ──► 🧠 مغز (DualBrainV3/Orchestrator) ──► ⚓ لنگر ──► تلگرامِ آری
   (درفت/محدوده)        (تحلیل، دو Guard)                (کاکپیت/verdict-request)
                                                        هر verdict → دستی توسط آری در فایل‌ها ثبت می‌شود
```
لنگر **هیچ verdict را خودش اعمال نمی‌کند** و **هیچ اکشن بیرونی** (پست/DM/اکانت/پرداخت) ندارد؛ تنها خروجی‌اش پیام تلگرام به chat-id آری است.

## ۲. خودآگاهی (Self-Model) — عملیاتی، نه ادعایی
هر پاسخ بر پایهٔ snapshot زنده: (۱) **وضعیت پروژه:** GATE 0 باز/بسته (regex روی PROJECT.md)، تعداد سؤال‌های باز، آخرین ردیف‌های DecisionLog، وجود M2/M3؛ (۲) **وضعیت خودش:** hash و خط‌شمار سورس خودش، نتیجهٔ آخرین test-run، وضعیت kill-switch، هزینهٔ مصرفی ماه/سقف، uptime؛ (۳) **قواعد:** ۸ قاعدهٔ قفل‌شده hard-code شده و در `/rules` گزارش می‌شود. تا وقتی GATE 0 باز است، لنگر خودش اعلام می‌کند «همهٔ اکشن‌های outward قفل‌اند» و هیچ پیشنهاد اجرایی بیرونی نمی‌دهد (fail-closed).

## ۳. مسئول ارتقا (Upgrade Loop — دوکلیده)
- `/upgrade` یا تیک هفتگی جمعه: لنگر خودش را و state پروژه را می‌خواند و **حداکثر ۳ پیشنهاد ارتقا** می‌نویسد → `langar/upgrade_proposals/YYYY-MM-DD.md` + خلاصه به تلگرام.
- **هرگز خودش را patch نمی‌کند** (بدون self-modify): اعمالِ هر پیشنهاد = آری دستی (دوکلیدهٔ BRAIN-SPEC؛ λ_persist<0 — لنگر برای بقای خودش بهینه نمی‌شود و /kill همیشه فعال است).
- منبع ایدهٔ ارتقا: شکاف‌های ثبت‌شده (OpenQuestions)، خطاهای runtime خودش، الگوی استفادهٔ آری، و آستانه‌های داشبورد.

## ۴. مغز و هزینه
- **لایهٔ ۰ (پیش‌فرض، $0):** heuristics از `DualBrainV3` ‏(strategist/pricer/…) اگر import شود؛ وگرنه پاسخ‌های file-grounded.
- **لایهٔ ۱ (اختیاری):** اگر `ANTHROPIC_API_KEY` ست باشد → Haiku برای خلاصه/تحلیل، زیر **CostMeter** با سقف `LANGAR_MONTHLY_CAP_AUD` (پیش‌فرض 15 — verdict ‏V3) و fail-closed.
- ماژول‌های `_ops/neural` اگر در sys.path باشند استفاده می‌شوند؛ نبودشان هیچ‌چیز را نمی‌شکند.

## ۵. خطوط قرمز کدشده (نقض = drop/halt)
فقط chat-id آری (غریبه = سکوت + لاگ) · صفر media (متد ارسال عکس اصلاً وجود ندارد) · **OpsecGuard روی هر پیام خروجی:** redact نام‌های واقعی (config)، «صبا/آری» → کد C/A، شهرها (Sydney/سیدنی)، مسیرهای فایل حساس؛ بیرونِ پوشه فقط «Project-F» · نوشتن فقط داخل `langar/` ‏(proposals/logs) · kill-switch فایل `langar/KILL` ‏(/kill می‌سازد، فقط /revive برمی‌دارد) · سقف هزینه fail-closed · هیچ auto-apply.

## ۶. دستورها
`/status` وضعیت دوگانهٔ پروژه+خودش (+یک‌خط وضعیت صبا) · `/gates` ‏G0–G4 با شرط عبور · `/verdicts` صف تصمیم‌های منتظر (از THREAD-CLOSURE §۹ + DecisionLog) · **`/saba` (=`/drafts`) پل به استودیوی صبا:** درفت‌های منتظر تأیید + ظرفیت اعلامی + اعلان‌های صبا + وضعیت ✋توقف (فقط‌خواندنی از `studio/drafts.json`,`to_ari.json`,`capacity.json`,`HALT`؛ تأیید = دستیِ درون‌پلتفرمِ آری) · `/brief` بریف هفته (مغز) · `/think <موضوع>` تحلیل propose-only · `/kpi` · `/report` (خروجی‌اش را آری در `studio/for_saba.json` می‌گذارد تا به صبا برسد) · `/upgrade` · `/rules` · `/kill` و `/revive` · `/help`.

## ۶.۵ پل استودیوی صبا (handoff)
لنگر و استودیوی صبا از طریق فایل‌های `studio/` سیم‌کشی‌اند (نه کانِن دوم): صبا درفت/اعلان می‌نویسد، لنگر می‌خواند؛ آری گزارش را در `for_saba.json` می‌گذارد. قرارداد این پل با تست جدا تأیید شد. جزئیات: [[studio/SABA-STUDIO-SPEC]] §۱.

## ۷. فعال‌سازی (گیت‌دار — THREAD-CLOSURE §۹ ردیف ۱۰)
ساخت bot در BotFather = اکشن بیرونی و **دست خود آری**؛ سپس طبق قاعدهٔ منشور («اتوماسیون جدید فقط بعد از یک هفته اجرای دستی موفق»): هفتهٔ اول **shadow-mode** (اجرای local، فقط /status و /report، بدون تیک خودکار) → بعد فعال‌سازی کامل. Runbook: [[langar/README-RUNBOOK|README-RUNBOOK]].

## ۸. تست‌ها (test_langar.py — $0، آفلاین)
۸ تست: گارد هویت redact می‌کند · گارد مسیر/شهر را می‌پوشاند · غریبه جواب نمی‌گیرد (سکوت) · KILL همه‌چیز جز status/revive را می‌بندد · proposal فقط داخل `langar/upgrade_proposals` می‌نویسد (هیچ فایل ریشه دست نمی‌خورد) · CostMeter در سقف و روی state خراب fail-closed است · تا نبودِ «Branch A» در PROJECT.md ‏outward_locked=True · هیچ متد رسانه‌ای وجود ندارد · خروجی send از گارد رد می‌شود.
> **وضعیت راستی‌آزمایی (2026-07-10):** منطق هستهٔ لنگر با یک test-build هم‌ارز اجرا شد → **۸/۸ سبز**؛ در run-all کامل هم ۸/۸ سبز + تست یکپارچگی `/saba` سبز. فایل کاملِ روی دیسک همان منطق + متدهای brief/think/LLM/poll را دارد و از نظر syntax معتبر است. قبل از فعال‌سازی، گام ۰ Runbook را روی سیستم خودت یک‌بار اجرا کن (`python3 -m unittest test_langar -v`).
