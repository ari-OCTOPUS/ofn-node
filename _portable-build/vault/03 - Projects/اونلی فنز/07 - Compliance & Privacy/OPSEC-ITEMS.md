---
type: control
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: idea
created: 2026-07-12
updated: 2026-07-12
created_by: agent
sources:
  - "[[00 - Control/CARTOGRAPHY-2026-07-12]]"
  - "[[07 - Compliance & Privacy/_INDEX]]"
tags:
  - project-f
  - opsec
  - privacy
aliases:
  - OPSEC Items
  - OpsecGuard Gaps
  - PF-CODE-REFACTOR-V1
---

# OPSEC-ITEMS — Project-F

> کنترلِ opsec سطحِ‌کد. **دو** گافِ تأییدشده در ممیزیِ کدِ ۲۰۲۶-۰۷-۱۲. **propose-only** — هیچ rename/اجرا/پرکردنِ خودکار؛ اعمال = دستِ A. نگاشت به verdict **`PF-CODE-REFACTOR-V1`**. مرجعِ ممیزی: [[00 - Control/CARTOGRAPHY-2026-07-12]] (خط ۵۰ همان نوت هر دو گاف را بدون echoِ نام ثبت کرده).
>
> **قراردادِ حریمِ این نوت:** نامِ کوچکِ C هرگز نوشته نمی‌شود؛ داخلِ شناسه‌ها با توکنِ `⟦C⟧` جایگزین شده — هم‌سبک با `⟦x⟧`/`⟦geo⟧`ی خودِ `OpsecGuard`. اپراتور = A.

## خلاصه (at-a-glance)

| # | گاف | severity | سطحِ افشا | چرا guard نمی‌گیرد |
|---|-----|:---:|-----|-----|
| 1 | نامِ C در **خودِ شناسه‌های سورس** (module/class/env-var) | 🔴 High | repo working-tree + `git history` + نامِ متغیرهای محیطی/پروسه + User-Agent | شناسه، «دادهٔ پیام» نیست → از مسیرِ `clean()` رد نمی‌شود |
| 2 | `blocklist: []` خالی → عبورِ un-redacted (fail-open) | 🔴 High | هر پیامِ خروجیِ langar (تنها کانالِ guard-دار) | مکانیزم هست، داده نیست |

---

## گاف ۱ — نامِ C در شناسه‌های سورس  `[FACT، code-verified]`

**محلِ دقیق (بدون بازتولیدِ نام):**
- `studio/⟦C⟧_studio.py` — نامِ **فایل** + docstring (خط ۱–۲).
- کلاسِ اصلی `class ⟦C⟧Studio` (خط ۸۰)؛ `name = "⟦c⟧-studio"` (خط ۸۳)؛ در `__repr__` (خط ۱۰۵).
- env-varها: `TELEGRAM_⟦C⟧_BOT_TOKEN` (خط ۸۸) و `TELEGRAM_⟦C⟧_CHAT_ID` (خط ۸۹).
- **انتشارِ همان env-var در دو فایلِ دیگر** (blast-radius refactor): `studio/studio_telegram.py` (خط ۱۵ docstring، ۹۰، ۹۲) و `studio/studio_telegram_v3.py` (خط ۶۵، ۶۶).
- User-Agentِ ارسالی به سرورِ تلگرام: `"⟦c⟧-studio/1.0"` (`studio/⟦C⟧_studio.py` خط ۷۱ و ۷۶) — روی هر request به بیرون می‌رود.

**severity: 🔴 High** `[EST]` — پایدار، **غیرقابل‌redact**، و در `git history` ماندگار؛ likelihoodِ افشای بیرونی الان پایین است (repoِ محلی/pre-launch) ولی سطحِ ماندگاری بالا نگه‌اش می‌دارد High.

**سطحِ افشا:** working-tree + کلِ تاریخِ گیت، نامِ فایل روی دیسک، نامِ متغیرهای محیطی (دیده‌شدنی در process listing / shell history / فایلِ `.env` / tracebackِ کرش)، هر `ImportError`/stack-trace که نامِ ماژول یا کلاس را echo کند، و headerِ User-Agent به سرورِ تلگرام.

**چرا guardِ فعلی نمی‌گیرد** `[FACT]`: تنها گیتِ متن، `OpsecGuard.clean` است (`langar/langar_bot.py` خط ۹۳–۱۰۴) که فقط روی آرگومانِ `text`ِ خروجی در `send()` اجرا می‌شود (خط ۲۹۹). شناسه‌ها **دادهٔ پیام نیستند** که از این مسیر عبور کنند. دوم اینکه `name_map` (خط ۸۲ و config خط ۴) فقط فرمِ فارسیِ «⟦C⟧→C» را دارد؛ پس حتی اگر فرمِ رومانیِ شناسه در متنی هم بیاید، در جدولِ scrub نیست. (توجه: `clean()` مسیرِ ویندوزی را redact می‌کند — خط ۱۰۲ — ولی نه نامِ خالصِ ماژول/کلاس/env.)

**remediation پیشنهادی (GATED — دستِ A):** `[SPEC]`
1. rename به شناسه‌های خنثی: `studio/creator_studio.py` / `class CreatorStudio` / `TELEGRAM_CREATOR_BOT_TOKEN` / `TELEGRAM_CREATOR_CHAT_ID` + User-Agent → `"creator-studio/1.0"`.
2. import-fix در همهٔ مصرف‌کننده‌ها: `studio/studio_telegram.py`، `studio/studio_telegram_v3.py`، هر launcher، و ارجاعِ `saba_bridge` در `langar/langar_bot.py` (خط ۱۸۲–۱۹۵ فقط مسیرِ پوشهٔ `studio/` را می‌خواند، نه نامِ کلاس — پس امن است ولی باید بازبینی شود).
3. تست‌های موجود سبز بمانند + یک تستِ رگرسیونِ «صفر شناسهٔ حاویِ نام».
4. **قید:** طبق CARTOGRAPHY خط ۴۶، **پوشهٔ پروژه/کد جابه‌جا نشود** (`orchestrator.py` عمقِ مسیر را فرض می‌کند)؛ rename داخلِ `studio/` مجاز است، move نه.

---

## گاف ۲ — `blocklist: []` خالی → fail-open  `[FACT، code-verified]`

**محلِ دقیق:**
- `langar/langar_config.json` خط ۲: `"blocklist": []` (و `_note` خط ۶ که خالی‌بودن را تأیید می‌کند).
- پیش‌فرضِ کد هم خالی: `OpsecGuard.DEFAULT` (`langar/langar_bot.py` خط ۷۹).
- حلقهٔ مصرفِ blocklist در `clean()`: خط ۹۹–۱۰۱ (روی لیستِ خالی هیچ redact نمی‌کند).
- **خودِ کد این را کاندیدِ #۱ ارتقا می‌داند:** `UpgradeEngine._candidates` خط ۲۲۳–۲۲۵ («…الان خالی است — redact نام‌ها فقط روی `name_map` پیش‌فرض»).

**severity: 🔴 High** `[EST]` — روی **کانالِ زندهٔ خروجی** fail-open است؛ هر نام‌خانوادگی، املای جایگزین، فرمِ رومانی، `@handle`، یا شناسهٔ دیگر که در `name_map`/`city_terms` نباشد، **un-redacted** عبور می‌کند.

**سطحِ افشا:** هر پیامِ خروجیِ `langar` (تنها کانالی که اصلاً `clean()` را صدا می‌زند — `send()` خط ۲۹۹). توجه: `SabaStudio.send()` (خط ۱۱۰–۱۱۷) **هیچ guard-ای ندارد** و متنش by-design redact نمی‌شود (C↔C)؛ پس خالی‌بودنِ blocklist دقیقاً همان یک کانالِ A-facing را ضعیف می‌کند.

**چرا guardِ فعلی نمی‌گیرد** `[FACT]`: `name_map` فقط دو نامِ کوچکِ فارسی («⟦C⟧»، «⟦A⟧») را پوشش می‌دهد و `city_terms` فقط شهر را؛ مکانیزمِ عمومیِ «هر شناسهٔ دلخواه» همان `blocklist` است — که خالی است. مکانیزم درست، دادهٔ آن غایب.

**remediation پیشنهادی (owner-only):** `[SPEC]`
- **A** فیلدِ `blocklist` را با نام‌خانوادگی/املاهای جایگزین/شناسه‌های حساس پر می‌کند. **ایجنت این نام‌ها را نمی‌نویسد** (قانون اساسی §۱۰ + قاعدهٔ privacyِ Project-F: نامِ واقعی نه در چت، نه در نوت، نه در کد).
- نقشِ ایجنت فقط: یادآوریِ ساختاری + پیشنهادِ محلِ درج (`langar/langar_config.json` → آرایهٔ `blocklist`) + یک تست که «خالی‌بودنِ blocklist در build نهایی = warning» بدهد. بدونِ محتوا.
- بهبودِ فرعیِ همراه: افزودنِ فرمِ رومانیِ نام‌ها به `name_map` (باز هم دادهٔ آن دستِ A) تا `clean()` هم فرمِ لاتین را بگیرد.

---

## نگاشت و بستن

- هر دو گاف ذیلِ verdict **`PF-CODE-REFACTOR-V1`** جمع می‌شوند (rename شناسه‌ها = GATED refactor؛ پرکردنِ blocklist = ورودیِ owner). این نوت **plan** است، نه approval و نه execution.
- تا زمانِ verdictِ A: هیچ rename، هیچ درجِ نام. صفِ verdict از طریقِ `/verdicts` و `THREAD-CLOSURE` پیگیری می‌شود.
- ارجاعِ ممیزی: [[00 - Control/CARTOGRAPHY-2026-07-12]] · فهرستِ حوزه: [[07 - Compliance & Privacy/_INDEX]].
