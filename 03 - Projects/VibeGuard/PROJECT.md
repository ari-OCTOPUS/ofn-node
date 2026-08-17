---
type: project
kind: project
project: "[[03 - Projects/VibeGuard/PROJECT]]"
status: active
owner: آری
start: 2026-08-17
risk_level: high
autonomy_level: read-only
tags: [vibeguard, security, ai-code, sast, mcp]
created: 2026-08-17
updated: 2026-08-17
---

# پروژه: VibeGuard (`vg`)

**هدف:** موتور امنیتی local-first و آفلاین برای مخزن‌های vibe-coded / تولیدشده با AI — یافتهٔ رتبه‌دار با شواهد، پویش agent-hijack، SBOM، و پیشنهاد پچ فقط پس از تأیید ماشینی. ادعا «امن است» ممنوع.

**نقش در اکوسیستم:** محصول جدا زیر نظارت architect. به ارگانیسم زندهٔ `_ops` وصل نمی‌شود مگر رأی صریح مالک. زبان خروجی: کاهش ریسک / ریسک باقی‌مانده / confidence / abstain.

## Active Context

- تمرکز فعلی: تحقیق و مشخصات v1.0 بسته‌اند (2026-08-17). پیاده‌سازی شروع نشده.
- تغییرات اخیر: ورود دو سند نهایی از Downloads + تکهٔ ۱/۵ چت در `chat-ingest/` (مشخصات فنی تا Technology Stack).
- ۳ قدم بعدی: (۱) تکهٔ ۲–۵ با «ادامه» · (۲) `vg` CLI MVP · (۳) واردات داسیه‌های `workspace/research/` اگر پیدا شد.
- تصمیم‌های باز: محل مخزن کد (این vault یا ریپوی جدا) · واردات ۷ داسیهٔ گم‌شده.

## Progress

- چه کار می‌کند: تحقیق ۷ مسیر + گزارش معماری (~۲۳۶۸ خط) + Project Specification (~۱۹۷۱ خط، SR/FR/NFR/INV/AC).
- چه مانده: کد `vg` · داسیه‌های `research/00_design_directive.md` و ۶ مسیر دیگر روی دیسک این vault نیستند (جستجو شد؛ فقط دو خروجی نهایی در Downloads بود).
- مشکلات شناخته: لایسنس CodeQL CLI و قوانین Semgrep مسیر تجاری را می‌بندند → Opengrep + قوانین خود. Skill-only رد شده.

## Next actions

- [ ] ایجنت پیاده‌سازی: فقط [[Project-Specification]] را SoT بگیرد؛ D1–D11 را دوباره بحث نکند.
- [ ] اگر داسیه‌ها پیدا شد: داخل `research/` کپی شود.
- [ ] رأی مالک: ریپوی جدا در برابر پوشهٔ همین پروژه.

## نوت‌های مرتبط

- ورود: [[00-START-HERE]]
- ایجنت بعد: [[NEXT-AGENT]]
- مشخصات Downloads: [[Project-Specification]]
- تکهٔ چت ۱/۵: [[chat-ingest/01-spec-chunk-1]]
- تحقیق: [[Deep-Research-and-Architecture-Report]]
- نوت شناخت: [[../../07 - Knowledge/شناخت-اختاپوس/65-VIBEGUARD-RESEARCH-INGEST-2026-08-17]]
- مگاپرامپت: [[../../agent-prompts/MEGAPROMPT-VIBEGUARD-IMPLEMENT-2026-08-17]]
