---
title: یافته‌های ایجنت GLM روی vault مالک
type: note
tags: [octopus, vault, glm, contradictions, evidence]
up: "[[00-INDEX]]"
run_date: 2026-08-15
evidence_level: A
---

# یافته‌های ایجنت GLM — بازسازی vault

ایجنت GLM 5.2 مگاپرامپت بازسازی Obsidian را روی `F:\backup` اجرا کرد.
**فقط‌خواندنی بود؛ هیچ فایل ردیابی‌شده‌ای تغییر نکرد.** خروجی: `00-INDEX.md` +
۱۰ پوشه + ۳۱ یادداشت.

> [!check] این یافته‌ها با اجرای واقعی pytest و git روی ماشین مالک به دست آمدند.
> سطح شاهد A. جدول [[11-EVIDENCE-LEVELS]] باید بر همین اساس ارتقا یابد.

## ۱۱ vault ابسیدین کشف شد

| # | مسیر | ماهیت |
|---|---|---|
| ۱ | `F:\backup\.obsidian` | **canonical** — فعال، git، تغییرات ۱۵ اوت |
| ۲ | `F:\backup\OCTOPUS-DOCTOR\.obsidian` | vault تودرتو، ساختار `00-INDEX`..`90-_meta` |
| ۳ | `F:\backup-Archive\مغز دوم\` | آرشیو |
| ۴ | `F:\backup-deploy-lab\` | آزمایشگاه دیپلوی |
| ۵ | `F:\backup-SAFE-2026-07-19\` | تنها جایی که `app/` هنوز هست |
| ۶ | `F:\backup-snapshot-20260723-121256\` | اسنپ‌شات ۲۳ ژوئیه |
| ۷–۸ | `F:\octopus-phase0-A-halt\` · `F:\octopus-phase0-isolated\` | ایزولهٔ phase0 |
| ۹ | `F:\romajan\` | vault پژوهشی |
| ۱۰ | `F:\_______Black Box\` | کد + second-brain |
| ۱۱ | `C:\Users\Armin\Documents\Obsidian Vault\` | تقریباً خالی |
| + | `F:\backup\04 - Architect System\architect\` | **vault تودرتوی دوازدهم** — بعداً پیدا شد |

حجم: **~۴۹۰۰ فایل md**؛ `4D-Vault` تنها ۳۰۵۵ فایل.

## تناقضات ثبت‌شده C-001 … C-007

هیچ‌کدام «حل» نشد. هر دو مقدار ثبت شد.

| کد | تناقض | مقدار الف | مقدار ب | حکم شاهد |
|---|---|---|---|---|
| C-001 | تعداد تست NBB-CP | MANIFEST: **۲۰۷** (83+102+5+17) | BACKUP-README: **۱۷۱** | **`171 passed in 2.50s`** → ب درست |
| C-002 | coherence / beat | مگاپرامپت: 0.958 / 36436 | فایل زنده: **0.95 / 36563** | فایل زنده درست |
| C-003 | خطای تست hypothesis-engine | «۵ سوییت سبز» در CURRENT-TRUTH | `ImportError: falsified_assists_at` | **ویرایش uncommitted** — HEAD سالم است |
| C-004 | `app/NBB-CP` | README ریشه (۱۰ اوت) «۲۰۷ تست سبز» | پوشه در `ea69126` (۳ اوت) حذف شد | ارجاع stale |
| C-005 | ADR-041 | مگاپرامپت فرض می‌کرد موجود است | دنبالهٔ ADR از **۰۴۰ به ۰۴۲** می‌پرد | غایب |
| C-006 | DECISIONS | مگاپرامپت: تا D-21 | فایل: **D-01..D-37** + O-01..O-04 | فایل درست |
| C-007 | تست‌های hypothesis | ADR-039: «۱۳۳ تست» | CURRENT-TRUTH: «۴۵+۲۰» | حل‌نشده |

## اسنادی که هرگز وجود نداشتند

`MEGA-PLAN-01/02` · `TYPED-EVENTS` · `DESIGN-DIRECTIVE` · `ARI-STUDIO-STEPS` ·
`UNIFIED-CHAT-MEGAPROMPT` · `ADR-041` · `CHECKPOINT.md`

جستجوی نام + محتوا + کل تاریخچهٔ git: **هیچ‌کدام هرگز در این مخزن نبوده‌اند.**

> [!warning] درس معرفت‌شناختی
> مگاپرامپت این فایل‌ها را به‌عنوان موجود فرض کرده بود. ایجنت **حدس نزد** و
> معادل نساخت. این رفتار درست است. اگر معادل حدس می‌زد، یک لایهٔ جعل به vault
> اضافه می‌شد.

## چهار نسخهٔ NBB-CP

| نسخه | شواهد |
|---|---|
| `03 - Projects/NBB-Control-Plane` | کامل‌ترین — MANIFEST، BACKUP-README (Head `02561ea`)، RUNBOOK، REGISTRY، cassettes |
| `4d_system/nbb-cp-kre` | `VERIFIED_SAFE_READONLY_TOOL` — dashboard:8599، watcher خاموش |
| `4d_system/src/nbb_cp` | پکیج پایتون: kernel / adapters / api / app |
| `app/NBB-CP` | **حذف‌شده** در `ea69126` |

**رأی مالک: «همش منم»** — هر چهار یک پروژه‌اند، هیچ‌کدام برتر نیست. مسئلهٔ
canonical دیگر حل نمی‌شود.

## حقایق زندهٔ تأییدشده

```
CURRENT-TRUTH.md (auto 2026-08-15T04:10Z)
coherence = 0.95   beat = 36563   members = 11
halted = False     HEAD = 9b6ed0c
```

```
pytest NBB-CP  -> 171 passed in 2.50s   (72 + 72 + 27)
```

- پورت‌های ۸۷۹۱–۸۷۹۴ **گوش نمی‌دهند**
- تاریخچهٔ git در پاکسازی ۳ اوت **squash** شد — پیام commit 414/408 دیگر نیست
- سه گیت `secret_rotation` / `partner_precondition` / `miner_isolation` **هیچ ردپایی در vault ندارند** — فقط در گفتگو زنده‌اند
- `TestPlan` در epistemics یک مدل Pydantic است، نه تست → ادعای ۴۵/۲۰ `unverified`
- `langar` در `03 - Projects/اونلی فنز/` است · `fusion-mvp` پیدا نشد

## پروژه‌های پرپلکسیتی — وضعیت در vault

| پروژه | وضعیت |
|---|---|
| hypothesis-engine | ✅ `_ops/hypothesis_engine/` + ADR-037 amend |
| octopus-unified-chat | ✅ ADR-040 + `_ops/conversation_hub/` (`OCTOPUS_UNIFIED_CHAT=0`) |
| math-atlas | ✅ `00 - Inbox` (۴ فایل) + `07 - Knowledge/شناخت-اختاپوس/40,41` |
| internet-observatory / ADR-041 | ⚠️ **غایب** — نه فایل، نه محتوا، نه تاریخچه |
