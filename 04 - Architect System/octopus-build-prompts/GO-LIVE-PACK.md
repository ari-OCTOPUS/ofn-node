---
type: runbook
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft-for-execution
tags: [octopus, go-live, wiring, runbook, handoff]
created: 2026-07-08
updated: 2026-07-08
created_by: agent
relates_to: "[[OCTOPUS-BASE-MAP-v0]] · P1..P5 همه سبز · P6 قفل تا 2026-07-21"
---

# GO-LIVE PACK — از «۵ لایهٔ ساخته‌شده» به «ارگانیسمِ در حالِ اجرا»

> **وضعیت:** P1..P5 ساخته و تست‌سبز (verifyِ مستقلِ معمار). این pack همهٔ کارِ باقی‌مانده را به ترتیب می‌دهد. **دیباگِ نهایی = مرحلهٔ آخر (§۷).**
> **قفل‌ها بی‌تغییر:** پول قفل تا ۲۱-۰۷ · propose-only · human-append · kill-switch مطلق · secret فقط env · هیچ commit از سندباکس (فقط Windows-side).

---

## §۰ ترتیبِ اجرا (چک‌لیست)
- [ ] ۱. **CHECKPOINT COMMIT** (P1–P5) — §۱
- [ ] ۲. **پاسِ نهاییِ WIRING** (GLM، آخرین کدِ کد) — §۲
- [ ] ۳. **COMMIT دوم** (wiring) — §۳
- [ ] ۴. **راه‌اندازیِ فقط‌مالک** (bot، Scheduled Task، off-site) — §۴
- [ ] ۵. **اجرای ۲۴ساعتهٔ smoke** — §۵
- [ ] ۶. **اولین لیدِ paperِ واقعی** (Lead-نقاشی) — §۶
- [ ] ۷. **پاسِ دیباگِ نهایی** — §۷

---

## §۱ CHECKPOINT COMMIT (اول، پیش از هر چیز)
۵ فاز commit‌نشده است. اول یک چک‌پوینتِ امن. **Windows-side، path-scoped، `*.db` هرگز.**

```powershell
cd F:\backup
git status                     # اول نگاه کن چه M/?? هست
# فقط مسیرهای کدِ ارگانیسم + داک‌های فاز:
git add "_ops" "07 - Knowledge/genome-system" "04 - Architect System/octopus-build-prompts" "01 - Dashboard/HANDOFF.md"
# db/stateِ زنده را از stage خارج کن (نباید commit شود):
git reset -- "_ops/state/chrono.db" "**/*.db" "**/ledger.jsonl"
git status                     # تأیید کن چیزی که نباید، staged نیست
git commit -m "octopus P1-P5: heart+doctor+telegram+legs+survival (all suites green, propose-only)"
```
> اگر `ledger.jsonl` را می‌خواهی نگه‌داری (تاریخِ واقعی)، از reset حذفش کن — ولی هرگز `.env`/`*.db`/`chrono.db`.

---

## §۲ پاسِ نهاییِ WIRING — پرامپتِ GLM (آخرین کارِ کد)
> این ۵ لایهٔ تست‌شده‌ولی‌جدا را یک حلقهٔ زنده می‌کند. additive، non-destructive، همه shadow (پول قفل).

```
تو کارگرِ کدنویسِ Octopus (GLM) هستی. پاسِ نهاییِ wiring: ۵ لایهٔ ساخته‌شده را به یک حلقهٔ زنده وصل کن. propose-only، additive، non-destructive (مسیرِ قدیمی تا اثباتِ نو باقی)، commit با مالک.

گام ۰ — ضدِ تکرار: grep کن آیا wiring از قبل هست:
  grep -rln "run_cycle.*beat\|bus.publish\|dispatch.*lead\|on_beat" _ops/ | grep -v __pycache__
  هرچه کامل+سبز بود اثبات بده و رد شو.

گام ۱ — بخوان: _ops/organism.py · _ops/chrono.py (Pacemaker) · _ops/unified_bus.py · _ops/budget/approval_channel.py (poll_once) · _ops/legs/lead_leg.py · _ops/doctor/doctor.py (run_cycle) · _ops/budget/money_gate.py. اول PLANِ کوتاه.

کارها (هرکدام تستِ $0 آفلاین):
W-1 اتصالِ doctor.run_cycle به Pacemaker هر N ضربان (از organism.py). غیربلاک؛ خطای دکتر heartbeat را نکشد.
W-2 UnifiedBus = تنها مسیر: proposalهای legs + RFC/submitِ doctor + approvalهای telegram همه از unified_bus.publish → ledger + chrono عبور کنند. مسیرِ قدیمی deprecated نه deleted.
W-3 router↔poll تلگرام (seam P3): poll_once پیام‌ها را به handlerِ درست route کند (/lead، callbackِ approval، /status، /stop)، با allowlistِ owner؛ ورودی = DATA.
W-4 اتصالِ money_gate/organism به کارتِ approval: اثرِ گیت‌خورده یک کارتِ تلگرام بسازد؛ approve → human-append → EffectorGate.settle. money قفل بماند (shadow).
W-5 تستِ یکپارچهٔ end-to-end: یک proposalِ Lead-نقاشی → bus → gate → کارتِ تلگرام → human-append(mock) → settle → attribution → fitness، همه از یک حلقه؛ و doctor.run_cycle روی ضربان شلیک شود. $0، هیچ شبکه/پولِ واقعی.

Definition of Done (اثبات نه ادعا):
- خروجیِ خامِ ترمینال: python _ops/tests/run_all.py + تستِ یکپارچهٔ نو. paste کن.
- یک event واقعاً از یک مسیرِ واحد brain→leg→gate→telegram→ledger→settle عبور کند؛ مسیرهای قدیمی هنوز سبز.
- money همچنان قفل/shadow؛ هیچ اثرِ زنده.
- ORGANISM-SPEC + HANDOFF آپدیت. بخش‌های فقط‌مالک با «⚑ برای مالک». commit دستِ مالک.
- هر ابهام → «⚑ برای معمار (Claude)».
```

---

## §۳ COMMIT دوم (بعد از wiring)
```powershell
cd F:\backup
git add "_ops" "04 - Architect System/octopus-build-prompts" "01 - Dashboard/HANDOFF.md"
git reset -- "_ops/state/chrono.db" "**/*.db"
git commit -m "octopus wiring: one live loop (bus+doctor-beat+telegram-router), shadow, propose-only"
```

---

## §۴ راه‌اندازیِ فقط‌مالک (⚑ فقط تو — نه GLM)

### ۴.۱ باتِ تلگرام (لازم برای human-append)
1. در تلگرام به `@BotFather` → `/newbot` → یک توکن بگیر.
2. chat_idِ خودت را بگیر (به بات یک پیام بده، بعد `https://api.telegram.org/bot<TOKEN>/getUpdates` را باز کن، `chat.id` را بردار).
3. در `.env` (هرگز در repo/چت):
```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_OWNER_CHAT_ID=...
```

### ۴.۲ Scheduled Task (زنده‌ماندنِ ۲۴/۷ — علتِ INC-1: از شلِ ایجنت نه)
- Task ۱: `organism-watchdog.ps1` هر ۵ دقیقه (at logon).
- Task ۲: `germline-hourly.ps1` هر ساعت.
- در Task Scheduler: Trigger = At log on + Repeat؛ Action = `powershell -File F:\backup\scripts\organism-watchdog.ps1`.

### ۴.۳ off-site backup (S-5)
- یک مقصدِ رمزنگاری‌شده (مثلِ Backblaze B2) بساز؛ credential فقط در `.env` تو.
- `restore-drill.ps1` را یک‌بار اجرا کن تا سبز بودنِ restore ثابت شود.

---

## §۵ اجرای ۲۴ساعتهٔ smoke
- ارگانیسم را **via Scheduled Task** بالا بیاور (نه دستی از شل).
- بعد از ۲۴ساعت: `python _ops/smoke_24h.py` → باید PASS بدهد (state تازه، heartbeat ساعتی، صفر freeze، verify، $0، epoch-log).
- اگر قرمز شد → §۷ دیباگ.

---

## §۶ اولین لیدِ paperِ واقعی (Lead-نقاشی، اصلِ صفر)
- در تلگرام: `/lead` → نام/کار/کانال بده → بات یک draft quote با `LEAD-YYYYMMDD-nnn` می‌سازد (proposal).
- یک CSVِ دستیِ اپراتور در پنجرهٔ ۷ روزه بگذار → `reconcile` باید CONFIRMED کند.
- `/status` باید `attribution_coverage` را نشان دهد.
- **هیچ پولِ واقعی، همه paper.**

---

## §۷ پاسِ دیباگِ نهایی — پرامپتِ GLM (طبقِ «اخرش دیباگ میکنیم»)
```
تو کارگرِ دیباگِ Octopus (GLM) هستی. حالا که همه‌چیز وصل شده، یک پاسِ عیب‌یابیِ کامل بزن. فقط گزارش + فیکسِ propose-only؛ commit با مالک.

۱. python _ops/tests/run_all.py → خروجیِ خام. هر قرمز را ریشه‌یابی کن.
۲. یک اجرای واقعیِ کوتاه (چند ضربان) با STOP/kill تست کن: watchdog تسلیمِ STOP می‌شود؟ heartbeat پایدار؟ doctor بدونِ بلاک run می‌شود؟
۳. حلقهٔ end-to-end را دستی دنبال کن: /lead → proposal → gate → کارت → approve(mock) → settle → attribution. کجا می‌شکند؟
۴. چک‌لیستِ نشت: هیچ توکن/کلید در لاگ؟ هیچ مسیرِ money زنده؟ هیچ commit از سندباکس؟
۵. خروجی: جدولِ «باگ · ریشه · فیکسِ پیشنهادی · فایل:خط»، مرتب بر اساسِ شدت. هیچ فیکسی را بدونِ verdictِ مالک apply نکن.
هر ابهامِ معماری → «⚑ برای معمار (Claude)».
```

---

## §۸ P6 (پولِ واقعی) — دست نزن
قفل تا **۲۰۲۶-۰۷-۲۱** + پرچمِ صریحِ تو + همهٔ گیت‌ها سبز. تا آن‌موقع کلِ سیستم shadow/paper است. این‌جا تصمیمِ انسانیِ توست، نه کارِ ایجنت.

## §۹ بازمانده (موازی، هر وقت خواستی)
۶۵٪ دادهٔ خامِ Crypto/Accounting/Mining هنوز خوانده‌نشده → آن سه پا منجمد تا ingestion (گزارشِ `DEEP-DOUBLECHECK-2026-07-08`).
