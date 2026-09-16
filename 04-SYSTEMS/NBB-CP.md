---
type: system-note
system: nbb-cp
created: 2026-08-15
owner_verdict: "«همش منم» (2026-08-15) — هر چهار نسخه یک پروژه‌اند؛ هیچ‌کدام به‌تنهایی canonical نیست"
sources:
  - "03 - Projects/NBB-Control-Plane/{MANIFEST.yaml, BACKUP-README.txt, CLAUDE.md, docs/SKELETON_HARDENING.md}"
  - "continuity/DR-NBB-CP-KRE-VERIFY-20260803.md"
  - "git log (کامیت ea69126)"
  - "اجرای زندهٔ pytest 2026-08-15"
---

# NBB-CP — Second Brain Super-Governor (کامپوننت B6)

## نسخه‌های در گردش (رأی مالک: همه یک پروژه‌اند — 2026-08-15)

| نسخه | وضعیت | شواهد |
|------|-------|-------|
| `03 - Projects/NBB-Control-Plane/` | BUILT + HARDENED — جای سندها | MANIFEST: 2551 LOC src · **اجرای زنده 2026-08-15: 171 passed** |
| `4d_system/nbb-cp-kre/` | ابزار فقط-خواندنی تأییدشده | DR-NBB-CP-KRE-VERIFY-20260803: `VERIFIED_SAFE_READONLY_TOOL` (venv ایزوله، dashboard:8599 موقت، watcher خاموش) |
| `4d_system/src/nbb_cp/` | پکیج ادغام‌شده در 4d_system | ساختار kernel/adapters/api/app — تست‌هایش این جلسه اجرا نشد → unknown |
| **مخزن کاری Desktop** (کشف 2026-08-15 عصر) | فعال‌ترین خط توسعهٔ فعلی | `C:\Users\Armin\Desktop\OCTOPUS-NBB-CP-WORKING\nbb-control-plane` · شاخهٔ `claude/second-brain-governor-v02-2a6e36` · HEAD `d964f5f` · adapter رصدخانه در `src/nbb_cp/adapters/observatory/` (۹۳ تست سبز) |
| `app/NBB-CP` | **حذف‌شده 2026-08-03** (کامیت ea69126) | فقط در snapshot ها (backup-SAFE-2026-07-19) → [[../01-TRUTH/CONTRADICTIONS.md|C-004]] |

> نتیجهٔ NBB-V1 (2026-08-15، امضای owner): این سیستم **حاکم بالای شش پا** است — حق stop یک پا، رد proposal، پیشنهاد بودجه بدون اجرا؛ عملیاتی→NBB-CP، معماری→Architect. منبع: `PHASE-1-DECISIONS.md`.

## تناقض تعداد تست (C-001)

- MANIFEST.yaml:15 → «207 tests green (83 l0 + 102 l1 + 5 l2 + 17 import-lint)»
- BACKUP-README.txt:4 → «Head: 02561ea (171 tests green)»
- **اجراهای زنده 2026-08-15: `171 passed in 2.50s`** (`py -m pytest -o addopts= -p no:warnings -q`)
- likely: ۱۷۱ · status: **open** — احتمال: شمارش ۲۰۷ شامل تست‌های محیطی/گیت‌های جدا بوده که در این محیط جمع نمی‌شوند

## فازها (طبق MANIFEST + docs)

| فاز | موضوع | وضعیت |
|-----|-------|-------|
| 1 | docs (SPEC, SECOND-BRAIN-SUPERGOVERNOR) | ساخته ✅ |
| 2 | vault scanner — فقط‌خواندنی (resolve-based exclusion) | ساخته؛ **بلوکر: vault path واقعی** (MANIFEST:19,60) |
| 3 | مغز Sakana Fugu (OpenAI-compatible) | live-verified (MANIFEST:62) |
| 4 | API گیت‌شده + آداپتورها | **PLANNED — نساخته** · رأی باز: NBB-V4 |
| 5 | داشبورد فقط‌خواندنی | **PLANNED** · رأی باز: NBB-V2 |
| B1–B8 | هشت مغز روی Obsidian Vault | «SPEC است، هنوز ساخته نشده» (CLAUDE.md) |

## باگ H1 — ثبت صریح

> `docs/SKELETON_HARDENING.md:28` — **«H1 — `execute()` idempotency (one verdict → N executions / N budget commits)»**
> زمان‌بندیِ اصلاح: Phase 4 (خط ۲۹). RLock سرویس پنجرهٔ race را می‌بندد؛ idempotency کامل هنوز پیاده نشده.
> مرتبط: `docs/CODING_AGENT_PROMPT.md:134` — «Idempotency keys on POST /proposals (client retry must not double-ledger)» — checklistunchecked.

## وضعیت اتصال

- MANIFEST:98 → «NBB-CP is built but **NOT connected to any project leg yet** — Phase 4-5 work»
- رأی‌های باز نقش/داشبورد/API/آداپتورها: [[../02-DECISIONS/OPEN-VERDICTS.md|OPEN-VERDICTS]] (NBB-V1…V4)

## قواعد غیرقابل‌مذاکره (خلاصه از CLAUDE.md پروژه)

INV-1..12 مقدس · kernel خالص stdlib · یک choke-point (`ControlPlaneService.execute`) · fail-closed · پول=integer cents · رازها هرگز وارد repo/ledger/cassette نمی‌شوند · suite همیشه سبز · **IMPROVE, DON'T REWRITE**
