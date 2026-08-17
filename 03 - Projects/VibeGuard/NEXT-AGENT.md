---
type: prompt
project: "[[03 - Projects/VibeGuard/PROJECT]]"
status: ready
tags: [vibeguard, next-agent]
created: 2026-08-17
updated: 2026-08-17
created_by: agent
sources:
  - "[[Project-Specification]]"
  - "[[00-START-HERE]]"
---

# ایجنت بعد — پیاده‌سازی VibeGuard

مگاپرامپت کامل: `F:\backup\agent-prompts\MEGAPROMPT-VIBEGUARD-IMPLEMENT-2026-08-17.md`

## قانون تقدم

1. کد زنده اگر وجود داشت.
2. [[Project-Specification]] — SoT. IDهای SR/FR/NFR/INV/AC را عوض نکن.
3. [[Deep-Research-and-Architecture-Report]] — شواهد.
4. این نوت.

`research/00_design_directive.md` در این vault **نیست**. تا وارد شود: تصمیم‌های قفل‌شده در [[00-START-HERE]] را D1–D11 عملی بگیر و دوباره بحث نکن.

## دامنهٔ MVP (گزارش §۲۱ / D10)

`vg scan` برای **JS/TS و Python فقط**. S0–S5، S7، S9 + repo-trust/agent-hijack. Auto-apply پچ در MVP نیست. IDE plugin نیست. DAST نیست. ابر multi-tenant نیست.

## نکن

- `git add -A` در `F:\backup` (درخت زندهٔ اختاپوس است).
- وصل کردن `vg` به `_ops` / فلگ OCTOPUS بدون رأی مالک.
- ادعای «secure / 100% safe / clean».
- Skill با `!` exec یا `allowed-tools` به‌عنوان محصول.
- CodeQL CLI یا قوانین Semgrep در توزیع.

## بکن

- ریپوی جدا یا زیرپوشهٔ `03 - Projects/VibeGuard/src/` طبق رأی مالک.
- تست برای هر invariant که لمس می‌کنی.
- Finding schema و SARIF 2.1.0 طبق spec.
