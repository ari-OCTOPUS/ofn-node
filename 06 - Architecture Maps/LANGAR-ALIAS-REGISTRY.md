---
type: reference
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
created_by: agent
sources:
  - "[[04 - Architect System/BIO-SYNTHESIS-MAP]] (قانونِ هم‌نامیِ کلی)"
  - "Report - Vault Relationship Map 2026-07-04 v3 (M14، ۳ referentِ اولیه)"
  - "recon workflow wthvcewz9 (کشفِ ۳ referentِ نو)"
tags: [octopus, naming, alias, homonymy, langar, reference]
created: 2026-07-09
updated: 2026-07-09
---

# 🪝 LANGAR / لنگر / Anchor — رجیستریِ authoritative هم‌نامی

> **پیش از هر لمسِ کدی که «langar/لنگر/Anchor» در نامش دارد، اینجا را چک کن.** واژهٔ «لنگر» (فارسیِ anchor) روی **≥۶ موجودِ کاملاً متمایز** افتاده. قاطی‌کردنشان = خطرِ فاجعه (به‌ویژه ساختِ ledgerِ موازی → دوپارگیِ منبعِ حقیقت، R2). این نوت رجیستریِ کامل است؛ قانونِ هم‌نامیِ کلی در [[04 - Architect System/BIO-SYNTHESIS-MAP|BIO-SYNTHESIS-MAP]]. مکملِ M14 در Relationship Map v3 (که فقط ۳ تای اول را داشت).

## ⭐ کدام «LANGAR» را کد منظور دارد؟
وقتی اسنادِ Octopus/Chrono می‌گویند **«LANGAR ledger»** یا **«LANGAR arrow»** یا **«Anchor Ledger»** → **همیشه یعنی #3 پایین: `genome ledger.py`**. هیچ جدولِ SQLiteِ `langar_ledger` ساخته **نمی‌شود** (قاعدهٔ extend-don't-rival؛ `chrono.py` عمداً آن را رد می‌کند). بقیهٔ referentها ربطی به قلبِ ارگانیسم ندارند.

## جدولِ ≥۶ referent
| # | نام | نوع | محلِ واقعی | وضعیت / قاعده |
|---|---|---|---|---|
| 1 | **بات langar** | کدِ legacy (ترید/فارم تلگرام) | `architect/_code/ai-farm/AI-sume/langar/` (langar.db شخصی، بودجهٔ D-25) | ممنوعه (`_code`)؛ زنده و **جدا**؛ ربطی به قلب ندارد |
| 2 | **Anchor Ledger** (مفهوم) | مفهومِ charter/spec | `MYCELIAL-MASTER-SPEC.md §6` · `ARCHITECT_CHARTER §4` | = نامِ مفهومیِ #3؛ ALIAS رسمی |
| 3 | **⭐ LANGAR ledger / arrow = genome ledger** | **کدِ واقعیِ قلب** | `07 - Knowledge/genome-system/ledger/ledger.py` (ledger.jsonl، age_tick/is_human/hash-chain) | **این قلبِ ارگانیسم است.** «Anchor Ledger» و «LANGAR arrow» همین‌اند |
| 4 | **Brushline LANGAR** | ماژولِ پروژهٔ نقاشی | داخلِ `_code`ِ پروژهٔ نقاشی (Brushline) | ممنوعه (`_code`)؛ **پروژهٔ نقاشی، نه اختاپوس**؛ کاملاً جدا |
| 5 | **PERSONA/موتورِ سنتزِ «لنگر»** | شخصیت/عاملِ سنتز | `07 - Knowledge/هیپنوتیزم و خودآگاهی/PERSONA - لنگر.md` | استعاره/عامل؛ نه ledger، نه کد |
| 6 | **langar_redteam / AUDIT-لنگر / لنگرزاد** | هیپنوتیزم + fiction | `07 - Knowledge/هیپنوتیزم و خودآگاهی/langar_redteam.py` · `PERSONA/AUDIT`؛ لنگرزاد = داستان | 🔥 firewall: جهتِ مجاز فقط الهام→spec؛ **fiction هرگز evidenceِ تصمیم نیست** |

## قواعدِ سخت
- «langar_ledger» به‌عنوان جدولِ SQLite **ساخته نشود** — #3 (genome JSONL) تنها قلب است.
- #1 و #4 زیرِ `_code`اند → **ممنوعه** (§۰-۲)؛ هرگز با قلب (#3) قاطی نشوند.
- #6 (هیپنوتیزم/داستان) 🔥: فقط الهام؛ هرگز به‌عنوان دادهٔ تصمیمِ سیستم.
- هر ایجنت پیش از edit روی هر فایلِ «langar»دار، اول این جدول را چک کند.

**اتصال:** قانونِ کلیِ 🔗/🌀/⚠️ → [[04 - Architect System/BIO-SYNTHESIS-MAP]]. گراندینگِ Chrono → [[04 - Architect System/2026-07-09 CHRONO-GROUNDING-PLAN — design↔reality + roadmap + decision-gates]].
