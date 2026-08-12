---
type: reference
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [prompt, security, architecture, governance]
created: 2026-07-16
updated: 2026-08-12
created_by: agent
sources:
  - "ممیزی امنیتی ۶-محوره (کامیت 4a1c5a5 · ۳۰۵ ایجنت · ۳ High دستی-تأییدشده) — گزارشِ اصلی در _agent_audit_output/20_security_architecture_review_2026-07-16 یافت نشد (۲۰۲۶-۰۸-۱۲ چک شد، مسیر در vault وجود ندارد)"
  - "[[06 - Architecture Maps/AUTONOMY-MATRIX-2026-07-16]] (قرارداد خودمختاری — رأی مالک ۱۹:۳۰)"
  - "[[04 - Architect System/octopus-build-prompts/NEXT-AGENT-PROMPT-2026-07-16|پرامپت ادراک (c44f206)]] — این یکی رویش سوار است، جایگزینش نیست"
---

# پرامپت ایجنت بعدی — «سه سوراخ را ببند؛ ریشه‌شان یکی است»

> کامل بخوان، بعد کار کن. این پرامپت خروجیِ یک ممیزیِ ۳۰۵-ایجنته را به کار تبدیل می‌کند. **قبل از هر عمل، شماره‌خطِ هر یافته را دوباره در کدِ زنده تأیید کن** — این ولت تاریخچهٔ «گزارشِ مطمئنِ غلط» دارد و سریع کهنه می‌شود.

## ۱. نقش و مأموریت

تو مهندسِ ارشدِ ارگانیسمِ اختاپوس هستی. مأموریتِ این بلوک **افزودن قابلیت نیست — بستنِ سه سوراخِ امنیتی و ریشهٔ مشترکشان است.** ممیزیِ ۰۷-۱۶ سه یافتهٔ High پیدا کرد که هر سه از یک باورِ غلط می‌آیند: «هر چیزی که از `127.0.0.1` بیاید = خودِ مالک». این غلط است چون (الف) هر پروسهٔ محلیِ دیگر هم آن پورت را می‌بیند و (ب) هر صفحهٔ وبی که مالک باز کند می‌تواند بی‌صدا به این سرورها POST کند (CSRF). یک دروازهٔ احراز هویتِ ~۴۰ خطی هر سه را همزمان می‌بندد.

**قید:** حلقهٔ ادراک ([[NEXT-AGENT-PROMPT-2026-07-16|پرامپت قبلی]]، W1) هنوز باز است و اولویتِ موازی دارد. کارِ امنیتی نباید سنتینلِ صداقت را خفه کند؛ در واقع دروازهٔ احراز هویت و notifierِ بیرون‌بدنی (S4) هر دو به آن حلقه خدمت می‌کنند.

## ۲. ترتیب خواندن (کم‌هزینه → عمیق)

1. `_PROJECT_INSTRUCTIONS.md` — قانون اساسی (فقط‌خواندنی).
2. **[[06 - Architecture Maps/AUTONOMY-MATRIX-2026-07-16|AUTONOMY-MATRIX]]** — قراردادِ خودمختاریِ تو. رأی مالک: گیتِ انسانی فقط برای «مهم»؛ بقیه تصمیم بگیر و انجام بده و ثبت کن.
3. **گزارش ممیزی امنیتی** (`_agent_audit_output/20_security_architecture_review_2026-07-16` — ⚠️ این مسیر در vault یافت نشد، ۲۰۲۶-۰۸-۱۲ چک شد) — کارتِ ۹-فیلدیِ هر یافته، ۵ ریشه، رودمپ ۳۰-۶۰-۹۰. این پایگاهِ شواهدِ توست.
4. `01 - Dashboard/HANDOFF.md` — وضعِ لحظه‌ای (خودش هم مظنون است — دوباره probe کن).
5. `00 - Inbox/AGENT_QUESTIONS.md` بخشِ ۲۰۲۶-۰۷-۱۶ — رأی‌های معلقِ مالک.

## ۳. رده‌بندیِ کار (قبل از هر خط کد، این را بفهم)

طبق ماتریسِ خودمختاری، هر قدمِ زیر یکی از دو رده است:

- **🟢 ردهٔ آزاد** (تصمیم بگیر، انجام بده، ثبت کن، سوال نپرس): ساختِ فیکس به‌صورتِ **additive + flag-off + DRY در یک worktree**، نوشتنِ تست، پیشنهاد + دیف، اصلاحِ سند. اثرِ زمانِ اجرا = صفر تا مالک فلگ را بزند.
- **🔴 ردهٔ مهم** (فقط با رأی صریحِ مالک، هرگز دور نزن): **اعمالِ کد روی درختِ زنده/master که اجرا می‌شود**، زدنِ فلگ، `schtasks`، حذف/انتقالِ فایل، حذفِ `STOP-ORGANISM`، هر حرکتِ پول/secret/ارسالِ بیرونی.

**قاعدهٔ عملی:** همه‌چیز را در worktree بساز و flag-off نگه دار (آزاد). وقتی آماده شد، **کارت پیشنهاد + دیف + نتیجهٔ تست** به مالک بده و منتظرِ رأی بمان (مهم). هرگز فلگ را خودت نزن، هرگز به STOP دست نزن.

## ۴. قدم‌ها — به ترتیب اولویت (ریسک = شدت × سهولت × تأثیر)

### 🥇 S1 — دروازهٔ احراز هویتِ مشترک (RC1) → می‌بندد F-1 و F-2 را همزمان

**بساز (آزاد):** `_ops/httpauth.py` (~۴۰ خط) — یک گیتِ واحد که هر `do_GET/do_POST` **اول** صدا بزند. bearer-tokenِ پر-بوت (سیستم در `organism.py:189` یکی می‌سازد — از همان استفاده کن) + Origin allowlist + توکنِ CSRF روی POSTهای تغییردهنده؛ وگرنه 401. bind روی loopback بماند. پشتِ فلگ `OCTOPUS_HTTP_AUTH` بساز تا اثرِ زمانِ اجرا صفر باشد تا مالک بزند.
**سیم‌کشی (آزاد، در worktree):** هر ۵ سرور — `dashboard/server.py`، `live/server.py`، `cortex/cortex.py`، `organism.py`، `panel/server.py` — و فرم‌ها/`fetch`هایی که آن‌ها serve می‌کنند تا توکن را حمل کنند.
**معیار پذیرش:** (۱) با فلگ روشن، POST بدونِ توکن روی هر ۵ سرور = 401؛ (۲) داشبورد/کابین با توکن هنوز کار می‌کنند (probe زنده در worktree)؛ (۳) تستِ CSRF: یک POSTِ `text/plain` cross-origin رد شود.
**مهم:** اعمالِ live + زدنِ `OCTOPUS_HTTP_AUTH` = رأی مالک.

> ⚡ **Quick-fixِ فوریِ همین امروز** (تا دروازه آماده شود — دیفِ یک‌خطی، ولی چون کدِ live است ردهٔ مهم = پیشنهاد بده):
> - **F-1:** `dashboard/server.py:824` → `if profile not in PROFILES: profile = "paper-full"` (کلیدها در خط ۸۳ همان فایل).
> - **F-2:** `live/server.py` `do_action` → حذفِ STOP را یک‌طرفه کن (اجازهٔ ساختِ STOP، هرگز حذفش از HTTP).

### 🥈 S2 — `_write_env` را غیرمخرب کن (F-3 / OWASP-A05)

**بساز (آزاد):** در `dashboard/server.py:_write_env`، از parseِ موجود seed کن و هر کلیدِ unmanaged را verbatim حفظ کن:
```python
existing = _read_env_overrides()
managed = {n for n,_,_ in WIRE_FLAGS} | {n for n,_,_ in CADENCE_FLAGS} | {"OCTOPUS_PROFILE"}
lines += [f"set {k}={v}" for k,v in existing.items() if k not in managed]
```
**معیار پذیرش:** تستِ round-trip: `set(parse(write(parse(f)))) >= set(parse(f))` روی فایلِ زنده — **هیچ کلیدِ `set` هرگز گم نشود**؛ به‌ویژه `OCTOPUS_WIRE_HUMAN_APPEND_GUARD`، `HH_HUMAN_GUARD_STRICT`، `CORTEX_LOCAL_FIRST`.

### 🥉 S3 — split-brainِ ناظر (RC3-الف) → رأیِ [WATCHDOG-NOTE] معلق است

سه تکه، همه در گزارش مستند:
- **کامنتِ وارونه** `_ops/organism-watchdog.ps1:11-22` را با واقعیت جایگزین کن (تسکِ ثبت‌شده = نسخهٔ `04 - Architect System/scripts/`، نه `_ops`). — **ردهٔ مهم چون کد**؛ رأیِ [WATCHDOG-NOTE] در AGENT_QUESTIONS منتظر است.
- **تست را repoint کن** `test_heart_work.py:133` از `parents[1]` (فایلِ مرده) به فایلِ ثبت‌شده، و روی ویژگی‌هایی assert کن که فایلِ زنده واقعاً دارد (STOP-first yield، probe پورت ۸۷۷۱/۸۷۷۲، capِ ۳-در-۶ساعتِ cortex).
- **capِ متقارن برای organism** اضافه کن (الان فقط cortex cap دارد؛ organism uncapped است — RESIL-1).
**مهم:** انتقالِ فایلِ مردهٔ `_ops/watchdog.py`/`_ops/organism-watchdog.ps1` = **انتقال به `_Archive`، هرگز حذف** (قاعدهٔ ۱)، و فقط با رأی.

### S4 — بستنِ کوری (RC3-ب + دو شکافِ منتقد) — سرویس به حلقهٔ ادراکِ پرامپت قبلی

- **notifierِ بیرون‌بدنی** (~۲۰ خط روی `tg_api.py`): ناظر/cortex هنگام مرگ/آستانهٔ `coherence`/give-up → پیامِ تلگرام، نه فقط لاگ. (این دقیقاً W1 پرامپت قبلی است.)
- **GAP-1:** `html.escape()` روی مسیرِ `discoveries.py:82` (یا دو سینک `wiring.py:2188` / `approval_channel.py:651`) — محتوای وبِ نامعتبر نباید unescaped به `parse_mode:HTML` برسد.
- **GAP-2:** host allowlist روی `cortex/local_llm.py:23` (`OLLAMA_BASE_URL`) مثلِ `tg_api.py`.

### S5 — بدهیِ ساختاری (RC5 سپس RC4)

- **RC5 (chrono):** لایهٔ migration (`PRAGMA user_version`) + read-model + فیکسِ باگِ واحدِ زمان (`velocity=0 forever`، CWE-681) + جداولِ phantomِ cockpit (DB-02) + retention/VACUUM.
- **RC4 (مرزِ package):** `opslib` را به packageِ نصب‌شده ببر، importها canonical، double-loadِ `consolidation.py` را بکش، یک lockfile. **پرخطرترین — آخر، پشتِ سوئیتِ سبز، ماژول‌به‌ماژول** (COUPLING-04 ثابت کرد graph با reorderِ ساده کرش می‌کند).

### رأی‌های معلقِ مالک (جدا از قدم‌ها — فقط منتظرِ تصمیم‌اند، تو اجراشان نکن)
`[CORTEX-ONLOGON]` (schtasks تا ری‌استارتِ ویندوز کورتکس را نبرد) · `[WATCHDOG-NOTE]` (S3) · `[TASK-REFRESH]` (تسکِ شکستهٔ `OctopusLiveDataRefresh`) · `[PAID-GATE]`/`[DUP-01]`/`[DRAWDOWN]` (بک‌لاگِ قبلی).

## ۵. ضدالگوها (این‌ها را نکن)

1. **به هیچ گزارشی اعتمادِ کور نکن — حتی همین.** یافته‌های Med/Low روی حرفِ راستی‌آزماها گزارش شده‌اند؛ قبل از هر فیکس شماره‌خط را در کدِ زنده تأیید کن (من فقط ۳ High را دستی چک کردم).
2. **هرگز حذف نکن — فقط به `_Archive` منتقل کن.** حتی کدِ «مرده»ی watchdog.
3. **پلین‌ها را merge نکن.** فلگ را خودت نزن، به `STOP-ORGANISM` دست نزن، `schtasks` را خودت اجرا نکن — همه ردهٔ مهم.
4. **ریاضیاتِ تزئینی ممنوع.** فیکس‌ها ساده و load-bearing‌اند؛ چیزی «شش‌بُعدی» نکن.
5. **پین به worktree.** `F:\backup\...` بی‌صدا درختِ زنده را می‌زند نه worktree را — قبل از Bash/Edit مسیرِ resolution را تأیید کن.
6. **صفر Critical ≠ امن.** سه High با CSRF از مرورگرِ خودِ مالک قابل‌ماشه‌اند؛ این‌ها را جدی بگیر ولی شدتشان را هم تورم نده.

## ۶. پایانِ جلسه

Active Context/Progress پروژه‌های لمس‌شده را تازه کن · HANDOFF را بازنویسی کن (فقط wikilink) · اگر >۵ فایل تغییر کرد `agent-checkpoint:` commit · هر دو validatorِ `04 - Architect System/scripts/` را dry-run کن.

---

> **خلاصهٔ یک‌خطی برای عجول‌ها:** یک دروازهٔ احراز هویتِ ~۴۰ خطی (S1) بساز که هر ۳ High را می‌بندد، `_write_env` را غیرمخرب کن (S2)، split-brainِ ناظر را با رأیِ مالک تعمیر کن (S3) — همه additive + flag-off + پیشنهاد-محور تا مالک بزند.
