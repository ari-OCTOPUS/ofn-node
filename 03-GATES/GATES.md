---
type: gates-note
created: 2026-08-15
status: unverified
rule: "گیت بسته یعنی باز نشده؛ این یادداشت فقط ثبت می‌کند، باز نمی‌کند"
---

# GATES — گیت‌های بسته

## گیت‌های نامبرده در مگاپرامپت مالک (2026-08-15)

| گیت | موضوع | وضعیت راستی‌آزمایی |
|-----|-------|---------------------|
| `secret_rotation` | چرخش کلیدها/رازها | **تأیید به‌عنوان آیتم مسدود** (سطح B): گزارش نشست رصدخانه §10 آن را در فهرست «همچنان مسدود — نیاز به اقدام بیرونی» دارد؛ نامش در md های F:\backup نیست (مبدأ: پروژهٔ رصدخانه/Perplexity) |
| `partner_precondition` | پیش‌شرط شریک | همان وضعیت — مسدود، اقدام بیرونی لازم |
| `miner_isolation` | ایزوله‌بودن ماینینگ | همان وضعیت — مسدود؛ مفهوم مرتبط در F:\backup: D-10 (اجرای مالی هرگز) + D-23 (gVisor) |

```yaml
verified_at: 2026-08-15
verification_source: "گزارش نشست ۱۵ اوت (Downloads) §10 + PHASE-1-DECISIONS.md — خوانده‌شده مستقیم"
status: confirmed_blocked_items (سطح B) — منبع اولیهٔ نام‌ها همچنان بیرون از F:\backup
likely_origin: "CHECKPOINT.md نود میدانی (غایب در vault) / اسناد پروژهٔ رصدخانه"
```

## گیت‌های مستندِ موجود (برای کامل بودن ثبت شد)

- `halted` flag در DB = منبع حقیقت kill-switch (D-06) + فایل STOP mirror
- فاز ۴-۵ NBB-CP گیت‌شده (NBB-V2/V4 باز)
- `OCTOPUS_UNIFIED_CHAT=0` (ADR-040، خاموش)
- ADR-034/035: neural APPLY dual-mode ARMED (CURRENT-TRUTH 2026-08-12)
- `D7_EXECUTION_AUTHORIZED=FALSE` · `INDEPENDENT_THIRD_PARTY_PASS=FALSE` (CURRENT-TRUTH 2026-08-15)

## کار لازم

- [ ] از مالک: منبع اصلی سه گیت نامبرده (CHECKPOINT برد؟ سند غایب؟) → NEW در OPEN-VERDICTS


## به‌روزرسانی 2026-08-16 (مصاحبهٔ GOVERNANCE-GATES)
- **GATE 0 (Project-F):** مسیر امن ساخته شد (`_ops/state/owner-private/` — gitignored)؛ اطلاعات محل اقامت پارتنر پس از گذاشتنِ مالک ثبت می‌شود؛ **گیت تا آن لحظه بسته**.
- **سه گیت مبهم (secret_rotation/partner_precondition/miner_isolation):** منشأ همچنان خارج از F:ackup (سطح B) — جستجوی عمیق‌تر موکول شد؛ هم‌زمان کشف هماهنگیِ کامیت دوقلو ثبت شد (INTERVIEW-LOG-GOVERNANCE-2026-08-16 §کشف).
