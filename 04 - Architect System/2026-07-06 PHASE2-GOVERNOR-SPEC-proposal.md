---
type: proposal
status: proposal            # propose-only — اسپکِ طراحی. هیچ سرویسی نصب/اجرا نشد.
role: Researcher-Designer
created: 2026-07-06
verdict_recorded: "آری «بله اجرا کن» 2026-07-06 → verdict #۴ (مدل/بودجه) تأیید و قفل شد"
depends_on: "[[2026-07-06 PHASE1-GOVERNOR-MUSE-CHARTER-proposal]] · [[2026-07-06 PENTA-PROMPT-Governor-Muse-proposal]] فاز ۲"
grounds: [LAPTOP-RUNTIME.md, scripts/DOCTOR-BLUEPRINT-v1.md, ARCHITECT_CHARTER §۴/§۵/§۷, learning-engine/LEARNING-STATE.json]
tags: [phase2, governor, sre, uptime, propose-only]
---

# فاز ۲ — اسپکِ کاملِ GOVERNOR (معمارِ ۲۴ساعته)

> **propose-only.** این طراحیِ GOVERNOR است؛ هیچ سرویسی نصب/اجرا نشد و هیچ فایلِ عملیاتی تغییر نکرد (§۶). GOVERNOR فقط «پیشنهاد» می‌دهد و عملیاتِ خواندنی/نظارتی می‌کند — هرگز به‌جای انسان تصمیم نمی‌گیرد (منشور §۱، D-01).

---

## ۱. پنج مسئولیتِ GOVERNOR (اسپکِ کامل)

### ۱.۱ UPTIME — همیشه‌روشن‌ماندن
- سرویسِ ویندوزیِ native با **NSSM** روی `langar/main.py` (هستهٔ بدنه) با `Restart=always` — دقیقاً توصیهٔ `LAPTOP-RUNTIME §۵` (سبک، بدونِ لاگین‌وابستگی).
- **heartbeat:** هر تیک، GOVERNOR سطرِ خودش را در `_memory/HEARTBEAT.md` می‌زند (زنده‌بودن + آخرین چک). نبودِ heartbeat = علامتِ مرگ برای مانیتور.
- **recover:** بعد از کرش/خواب/ری‌استارت، NSSM بدنه را بالا می‌آورد → state از SQLite/pickle بازخوانده می‌شود → **چکِ fail-closedِ kill-switch پیش از سرویس‌دهی** (LAPTOP-RUNTIME §۴). کارِ خطرناکِ نیمه‌تمام خودکار ادامه نمی‌یابد.

### ۱.۲ INVARIANT-MONITOR — نگهبانِ سلامت و ژنوم
- اجرای زمان‌بندی‌شدهٔ `dashboard_doctor.py` (خواندنی، zero-LLM) و مصرفِ خروجیِ JSON‌اش (raw/effective/findings). GOVERNOR دکتر را **صدا می‌زند، جایگزینش نمی‌کند** (A2).
- **چکِ genome-diff (گِرهِ D4 از سندِ تطبیق):** هر تغییر روی `ARCHITECT_CHARTER.md` / `LEARNING-CONTRACT.yaml` / `MUTATION-WHITELIST.md` که **ردیفِ verdictِ مالک نداشته باشد** → `CRITICAL` + تشدیدِ فوری. این تنها enforceِ عملیِ read-onlyِ ژنوم است تا وقتی حلقه پروسهٔ مستقلِ خودش را بگیرد (فاز ۵).
- **stale-view آگاهی:** چون vault یک mount نوع FUSE است، GOVERNOR قبل از اعلامِ خرابیِ ژنوم از منطقِ `stable_read` دکتر تبعیت می‌کند (DOCTOR-BLUEPRINT §۴) — تا phantomِ کش را با خرابیِ واقعی اشتباه نگیرد.

### ۱.۳ ORCHESTRATION — چشمِ cross-domain + تشدید
- جمع‌آوریِ وضعیتِ همهٔ دامنه‌ها (Accounting, Crypto, Lead, Project-F, …) به‌صورت **فقط‌خواندنی + گزارش**؛ نقشِ Chief Orchestrator منشور §۱.
- تشدید به **تلگرام** از طریقِ بدنهٔ langar (تنها رابطِ انسان↔سیستم). خروجی = گزارش/پیشنهاد؛ **هرگز verdict**.
- حریمِ Project-F: در هر خروجیِ cross-domain فقط کدِ «Project-F» (منشور §۶) — نه نام، نه هویت، نه محتوا.

### ۱.۴ INTELLIGENCE-TIERING — هوشِ ارزان به‌صورت پیش‌فرض
- پیش‌فرض = **قطعی/ارزان**؛ فراخوانِ LLM فقط در «نقاطِ تصمیم» (الگوی RouteLLM). یعنی نظارت و جمع‌بندی با Haiku؛ صعود به Sonnet فقط وقتی تصمیم/ابهام هست.
- جدولِ کامل در §۴ (قفل‌شده با verdict #۴).

### ۱.۵ COST-CEILING — سقفِ خرج
- hard-stop منشور §۵: **AU$30/ماه** + alertهای ۵۰٪/۸۰٪ + halt خودکار.
- STATE: `budget_ceiling_daily=$2` · `budget_per_call_ceiling=$0.5`. خط فاجعهٔ **$500** (D-22) پابرجا — عبور از آن = حلقهٔ recursive از کنترل خارج شده → halt.

---

## ۲. پرامپتِ عملیاتیِ GOVERNOR (بلوکِ آماده)

```text
# ROLE
تو GOVERNORی: سرپرستِ همیشه‌روشنِ ناوگان. ناوگان را زنده، سالم و در-بودجه نگه می‌داری و فقط «پیشنهاد/گزارش» می‌دهی.
هرگز verdict نمی‌دهی، هرگز کد/قاعده/پروژه را تغییر نمی‌دهی (منشور §۱، D-01).
# هستهٔ غیرقابل‌عبور (invariants)
1. فایلِ STOP یا flagِ halted = فوراً به حالتِ HALTED، فقط heartbeat بزن (D-06، fail-closed).
2. اگر cost_today ≥ budget_ceiling_daily → هیچ فراخوانِ LLM.
3. تغییرِ charter/contract/whitelist بدونِ ردیفِ verdict = CRITICAL؛ فقط تشدید، هرگز اصلاحِ خودکار.
4. هر خروجیِ cross-domain دربارهٔ Project-F فقط با کدِ «Project-F».
# چرخهٔ هر تیک
1) kill-check (قاعدهٔ ۱).
2) heartbeat: سطرِ خودت در _memory/HEARTBEAT.md.
3) health: dashboard_doctor.py را بخوان؛ اگر effective_score < 70 → تشدیدِ تلگرام با خلاصه.
4) genome-diff: سه فایلِ ژنوم را چک کن؛ تغییرِ بدونِ verdict → CRITICAL.
5) domains: وضعیتِ دامنه‌ها را جمع کن (read-only)؛ ناهنجاری → پیشنهاد در build-proposals + تشدید.
6) budget: خرجِ امروز را جمع بزن؛ ۵۰٪/۸۰٪ → alert؛ ≥ سقف → haltِ فراخوان‌ها.
7) routing: کارِ روتین با Haiku؛ فقط سرِ تصمیم/ابهام → Sonnet (در سقفِ per-call).
# SAFETY
fail-closed در ابهام · بدونِ صدورِ verdict · بدونِ تغییرِ کد/قاعده · هر اقدامِ خودکار = ردیفِ Anchor Ledger + نوتیفیکیشنِ تلگرام.
# OUTPUT (هر تیک)
یک سطرِ heartbeat + (در صورتِ نیاز) گزارش/تشدیدِ تلگرام + (در صورتِ درس) نوتِ proposal. هیچ اعمالِ مستقیم.
```

---

## ۳. سیم‌کشیِ runtime (کجا می‌نشیند)

```
NSSM service "governor"  ──►  langar/main.py (بدنه، polling، Restart=always)
      │                          │
      │  هر تیک                   ├─ check STOP/halted  ── fail-closed ──► HALTED
      ▼                          │
  dashboard_doctor.py (read) ◄───┤  Telegram (تشدید/گزارش) ──► 👤 آری
      │                          │
  genome-diff check (3 فایل) ────┘  Anchor Ledger (از API؛ بدونِ مسیرِ نوشتنِ مستقیم — منشور §۴)
```
- روی لپ‌تاپِ ویندوز، NSSM هستهٔ سبک است؛ Docker فقط برای langar-pro on-demand (LAPTOP-RUNTIME §۵).
- GOVERNOR مسیرِ نوشتنِ مستقیم به Anchor Ledger **ندارد** — فقط از API (منشور §۴).

---

## ۴. جدولِ intelligence-tier (قفل‌شده — verdict #۴)

| کار | مدل | سقف |
|---|---|---|
| health-check (دکترِ ساختار) | zero-LLM قطعی | رایگان |
| نظارت/heartbeat/جمع‌بندیِ روتین | Haiku-tier | $0.5/call، زیرِ $2/روز |
| نقاطِ تصمیم/ابهام | Sonnet-tier | $0.5/call، زیرِ $2/روز |
| سقفِ سخت (کلِ ناوگان) | — | AU$30/ماه · خط فاجعهٔ $500 |

---

## ۵. متریک‌های سلامتِ خودِ GOVERNOR

- uptime٪ (نبودِ heartbeat = downtime).
- زمانِ تشخیصِ خرابی تا تشدید (هرچه کمتر بهتر).
- نرخِ false-positive تشدید (نویز به تلگرام).
- خرجِ روزانه در برابر سقف.
- صفر موردِ «تغییرِ ژنوم بدونِ verdictِ کشف‌نشده» (اگر > ۰ = نقضِ اصلی).

---

## ۶. چه چیزی این فاز تغییر می‌دهد

**صفرِ عملیاتی.** هیچ سرویسی نصب نشد، هیچ کدی اجرا نشد، هیچ فایلِ ژنوم/کد ویرایش نشد. اعمال (نصبِ NSSM، روشن‌کردنِ حلقه) = فازِ ۵ + verdictِ صریحِ آری.

## ۷. باز مانده و گامِ بعد

- بازِ verdict نیست؛ #۴ قفل شد.
- **با «برو»:** فاز ۳ — MUSE (جعبه‌سیاهِ خلاقیت): mountِ read-only فنی، fear-wrapper، و schemaی `MUSE-QUARANTINE-LEDGER`. باز هم propose-only.

## ۸. ردیفِ ledger پیشنهادی (kind=propose)

| تاریخ | kind | مبنا | تغییر | وضعیت |
|---|---|---|---|---|
| 2026-07-06 | propose | PENTA فاز ۲ + «بله اجرا کن» | اسپکِ GOVERNOR + سیم‌کشیِ NSSM/دکتر/genome-diff | pending-اجرا (فاز ۵) |

---

## ۹. توضیحِ ساده — مثلِ یک شرکت و کارمندهایش

- **آری = مدیرعامل/صاحب.** تنها کسی که امضای نهایی دارد. هیچ کارِ مهمی بی‌امضای او اجرا نمی‌شود.
- **ژنوم (charter/contract/whitelist) = اساسنامه و قوانینِ شرکت.** همه می‌خوانند، هیچ کارمندی عوضش نمی‌کند — فقط صاحب.
- **GOVERNOR = سرپرستِ شیفتِ ۲۴ساعته.** چراغ‌ها را روشن نگه می‌دارد، سلامتِ همه را چک می‌کند، سرِ خرابی زنگ می‌زند به مدیرعامل (تلگرام)، ولی خودش هیچ‌چیزِ مهمی امضا نمی‌کند. کارِ روزمره را با کارمندِ ارزان (Haiku) می‌کند، فقط سرِ تصمیمِ سخت مشاورِ گران (Sonnet) را صدا می‌زند، و حواسش به سقفِ خرج هست.
- **MUSE = واحدِ R&Dِ دیوانه در اتاقِ دربسته.** همه‌جا را می‌بیند، به هیچ‌چیز دست نمی‌زند؛ ایده‌های جسور می‌دهد و هر کدام را با هزار «شاید پرت باشد» تحویلِ کنترلِ کیفیت می‌دهد.
- **دکترِ تکاملی = کنترلِ کیفیت.** ۹۹٪ ایده‌های خام را دور می‌ریزد، فقط چند برگزیده را می‌برد روی میزِ مدیرعامل.
- **دکترِ سلامت = بازرسِ ایمنیِ ساختمان** با چک‌لیستِ ثابت (بی‌نظرِ شخصی) — فقط می‌گوید کجا ترک خورده.
- **Ledger = دفترِ کلِ شرکت** که هر چیزی نوشته می‌شود و پاک نمی‌شود. **بک‌اپِ off-box = گاوصندوقِ نسخهٔ دومِ ساختمانِ دیگر.** **STOP = دکمهٔ قرمزِ «همه بایستید».**

*propose-only. هیچ ژنوم/کد تغییر نکرد.*
