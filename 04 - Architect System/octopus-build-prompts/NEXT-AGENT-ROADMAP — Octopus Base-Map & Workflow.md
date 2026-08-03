---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, roadmap, base-map, workflow, handoff]
created: 2026-07-08
updated: 2026-07-08
created_by: agent
---

# NEXT-AGENT ROADMAP — نقشهٔ پایه + ورکفلوِ واحدِ اختاپوس

> **برای ایجنتِ بعدی:** این سند بریفِ کارِ توست. آری (جلسه ۳۲، چیپ ۱۰سؤالی) تمرکزِ بعدی را انتخاب کرد: **«طراحیِ ورکفلو/نقشهٔ پایه برای همه‌چیز»** — نه ساختِ یک فازِ نو. یعنی: اختاپوس در ۳۲ جلسه اُرگانیک رشد کرده؛ قبل از هر build نو باید کلِ آن در **یک نقشهٔ پایهٔ منسجم** جمع شود. این فایل = همان مأموریت + تمام قیدهای قفل‌شده + ترتیبِ بعدش.

---

## ۰. وضعیتِ فعلی (از کجا شروع می‌کنی)
- **قلب ساخته شد (P1، جلسه ۳۱–۳۲):** `_ops/chrono.py` (HLC/phi/pacemaker/EffectorGate/scheduler=F19) + ledger ژنوم **v0.4.6** (فلشِ میرا `age_tick` حالا **heart-driven** و versioned). جزئیات: [[00 - Inbox/2026-07-08 OCTOPUS-P1-HEART-REPORT — قلب ساخته شد (chrono substrate)|P1-HEART-REPORT]] + [[07 - Knowledge/genome-system/CHANGELOG|CHANGELOG]].
- **مانده (Windows-side، دستِ مالک):** اجرای سوئیت (run_all ۱۳ + ژنوم ۶) → commit ِ path-scoped → restart ارگانیسم. بستهٔ فرمان در گزارشِ جلسه ۳۲.
- **مرجعِ معماری:** [[_ops/ORGANISM-SPEC|ORGANISM-SPEC]] (سه لایه + §۲.۵ Chrono) · [[04 - Architect System/octopus-build-prompts/00-INDEX|00-INDEX]] (فازها P1..P6).

## ۱. مأموریتِ واحدِ تو
یک deliverable بساز: **«نقشهٔ پایهٔ اختاپوس» (Octopus Base-Map)** — یک سند + یک دیاگرام که نشان دهد همهٔ قطعات چطور در **یک ورکفلوِ end-to-end** به هم وصل می‌شوند. **هیچ فازِ نوی کد پیش از ratify شدنِ این نقشه توسط آری ساخته نشود** (قانونِ ضدِ گنبد: از سقف شروع نکن، یک قدم).

## ۲. تصمیم‌های قفل‌شدهٔ آری (جلسه ۳۲) — نقشه باید این‌ها را encode کند
| # | موضوع | verdict آری |
|---|---|---|
| ۱ | money-path | اختاپوس فعلاً **فقط زیرساخت** است — می‌سنجد/پیشنهاد می‌دهد؛ دلارِ مستقیم جدا و بعداً |
| ۲ | گیتِ پولِ زنده | **بعد از هفتهٔ اولِ دیتا** تصمیم بگیر (الان قفل نکن) |
| ۳ | تمرکزِ بعدی | **طراحیِ نقشهٔ پایه/ورکفلو برای همه‌چیز** (همین سند) |
| ۴ | اولین پاها (legs) | **Lead-نقاشی · Ziman Gallery · Project-F** (نه Accounting) |
| ۵ | cadence سن | **روزانه** (`CHRONO_AGE_PER_N_BEATS=1440` — اعمال شد) |
| ۶ | مرگِ منطقی | **restore خودکار از germline backup** سپس ادامه (خود-ترمیم) |
| ۷ | خودمختاریِ دکتر | **non-critical خودکار** (پارامتر/داک) + **PROPOSAL برای هسته** |
| ۸ | always-on | **لپ‌تاپ + Windows Scheduled Task** (watchdog، restart خودکار) |
| ۹ | مدلِ orchestrator | **Fugu می‌ماند**؛ base_url را آری می‌دهد (تا آن‌موقع shadow) |
| ۱۰ | اتصالِ cross-project | **«ژنوم/بودجهٔ» هندآفِ nature-architecture = همین `genome-system` + `budget`** (یک Ledger واحد بین پروژه‌ها) |

## ۳. نقشهٔ پایه چه چیزهایی را باید نشان دهد
1. **لایه‌ها و اتصالاتشان:** آناتومی (ledger/LANGAR) ⊕ فیزیولوژی (heart/chrono) ⊕ متابولیسم (budget/governor/telemetry) ⊕ ژنوم (values/gates/doctor).
2. **ورکفلوِ end-to-end (ستون فقرات):** ادراک → `ledger`(LANGAR، `age_tick`) → `heartbeat`(chrono) → گیت‌ها (`organ_gate`→`budget_gate`→`money_gate`→`capability_gate`) → `PROPOSAL` → **انسان (تلگرام)** = human-append → `EffectorGate.settle` → اثر → `attribution`/`reconcile` → `fitness` → (شرطی) `replication`.
3. **نقشهٔ فازها:** P2..P6 به‌عنوان مراحلِ روی همین ورکفلو، هرکدام با گیتِ ورودی/خروجی‌اش.
4. **سه پا:** Lead-نقاشی · Ziman · Project-F — هرکدام یک instance روی ورکفلو (Project-F با قاعدهٔ حریم: فقط کد در خروجیِ cross-domain).
5. **money-path:** طبق §۲.۱ فعلاً infra-only؛ محلِ گیتِ زندهٔ Phase 6 و شرطِ بازشدنش (بعد از هفتهٔ اولِ دیتا) روی نقشه علامت بخورد.
6. **اتصالِ cross-project (§۲.۱۰):** یک بلاک که نشان دهد genome-system + budget همان «ژنوم/بودجهٔ» پروژهٔ `HANDOFF natures-architecture-project` است → یک Ledger مشترک؛ ابهامِ ثبت‌شدهٔ آن پروژه این‌جا بسته می‌شود.

## ۴. قواعدِ حاکم (از سه هندآفِ آپلودیِ آری — رعایتِ اجباری)
- **اصل صفر (پول بُعدِ اول):** پیش از هر پیشنهاد ۳ سؤال — (۱) کِی/چطور دلار می‌شود؟ (۲) ارزان‌ترین نسخه‌ای که همین را ثابت کند؟ (۳) اگر آری ۵ روز غیبت زد، می‌چرخد یا می‌میرد؟ اگر جوابِ ۱ مبهم بود → پیشنهاد نده، سؤال بپرس.
- **survival barbell + هیچ auto-executionِ مالی، هرگز** (kill-switch، per-trade cap، audit log — غیرقابل‌حذف).
- **یک Ledger واحد:** قبل از ساختِ چیزِ نو بپرس «کجای Ledger می‌نشیند؟». سندِ پراکنده نساز — به همین نقشه delta بزن.
- **صداقتِ معرفتی + برچسبِ شواهد** (`[تثبیت‌شده]`/`[فرضیه]`/`[مدل‌نظری]`/`[گمانه‌مهندسی]`/`[محل‌مناقشه]`)؛ **یک قدمِ بعدی** (لیستِ ۱۰تایی ممنوع)؛ **حالتِ روزِ دپ** (کم‌انرژی = یک جمله + یک اقدامِ ۱۰دقیقه‌ای).
- **bio-inspired (محور ۲/۸ پروژهٔ طبیعت):** برای اتصالِ پاها **partial-mesh محلی + سلسله‌مراتب + میانبرهای کمِ small-world**، نه full-mesh (هزینه O(N²)→~O(N log N)).

## ۵. ترتیبِ فازها — فقط پس از ratify شدنِ نقشه توسط آری
۱. **P3 تلگرام** (کانالِ کنترل/تأیید) — پیش‌نیازِ هر tentacleِ زنده و هر human-append؛ بدونِ آن دکتر/پاها به آری وصل نیستند.
۲. **P4 سه پا** (Lead-نقاشی · Ziman · Project-F) روی ورکفلو.
۳. **P2 دکتر** با خودمختاریِ §۲.۷.
۴. **اجرای ۳۰روزهٔ paper** (جمع دیتا، همه شادو/$۰).
۵. **تصمیمِ گیتِ زنده** (§۲.۲، بعد از هفتهٔ اول).
> هر مرحله زیرِ قیدهای §۲ و قواعدِ §۴.

## ۶. کارهای فوریِ کوچک (قبل/همراهِ نقشه — همه سبک، $۰)
- **commit ِ Windows-side** جلسه‌های ۳۱/۳۲ (بستهٔ path-scoped در گزارشِ جلسه ۳۲) — تا کار گم نشود.
- `CHRONO_AGE_PER_N_BEATS=1440` (روزانه) — **در کد اعمال شد**؛ فقط با همان commit می‌رود.
- **always-on (INC-1):** یک Windows Scheduled Task + watchdog که `RUN-ORGANISM.bat` را زنده نگه دارد و پس از kill/کرش restart کند. (ارگانیسم را از شلِ ایجنت روشن نکن.)
- **مرگ→خود-ترمیم (§۲.۶):** قلابِ `restore_from_germline` در مسیرِ verify-fail طراحی شود — **محتاط:** ضدِ حلقهٔ ترمیمِ بی‌پایان (بعد از N تلاشِ ناموفق → FREEZE + صف انسان، نه restore بی‌نهایت).
- **Fugu:** base_url را آری می‌دهد؛ تا آن‌موقع `routing.orchestr.base_url` در budgets.yaml روی TBD می‌ماند و مسیرِ orchestr فقط شادو است.

## ۷. گاردریل‌ها (نکن‌ها)
- پولِ زنده نه (پیش از Phase 6 + پرچمِ مالک) · auto-executionِ مالی نه · ارگانیسم را از شلِ ایجنت روشن نکن (INC-1) · به `.git` دست نزن · commit فقط **path-scoped** و **Windows-side** (سندباکس فایل‌های تازه‌ویرایش را **بریده/torn** می‌بیند — از سندباکس commit = خرابیِ ریپو) · **فازِ نوی کد پیش از ratify شدنِ نقشه نساز**.

## ۸. اولین قدمِ واحدِ امروز
طبقِ نقشِ Adaptive Architect — فقط یک کار: **نسخهٔ v0 نقشهٔ پایه را بکش** (یک دیاگرام + یک صفحه که ورکفلوِ end-to-end §۳ + جای هر فاز/پا/گیت را نشان دهد)، بگذار روی میزِ آری برای verdict. بعد از تأیید، ترتیبِ §۵ را شروع کن. گنبد نساز؛ از همین یک قدم شروع کن.

## منابع
- [[00 - Inbox/2026-07-08 OCTOPUS-P1-HEART-REPORT — قلب ساخته شد (chrono substrate)|گزارش P1-HEART]] · [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS (جلسه ۳۲)]] · [[04 - Architect System/octopus-build-prompts/00-INDEX|00-INDEX]] · [[_ops/ORGANISM-SPEC|ORGANISM-SPEC]]
- سه هندآفِ آپلودیِ آری (جلسه ۳۲): AI-AGI-Architecture-Handoff (Survival-Stack/اصل صفر) · HANDOFF bio-inspired-architecture · HANDOFF natures-architecture-project (اختاپوس = محور ۸).
