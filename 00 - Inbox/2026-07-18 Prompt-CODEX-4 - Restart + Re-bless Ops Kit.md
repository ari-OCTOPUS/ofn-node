---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, prompt, codex, ops, restart]
created: 2026-07-18
updated: 2026-07-18
created_by: agent
---

> **for:** Codex · **risk:** low-code / high-ops (read-only checks + runbook; هر اکشن زنده owner-gated)

# CODEX PROMPT 4/5 — Restart & Re-bless Ops Kit (پنجرهٔ خاموشی)

> نقش تو: **Runtime Verifier / Ops Engineer**. کد سبز روی دیسک است؛ گلوگاه واقعی «فعال‌سازی تمیز» است: ری‌استارت ارگانیسم + re-bless مهر CAPABILITY + smoke تلگرام. تو این مسیر را از «چند دستور پراکنده در HANDOFF» به یک kit قابل‌تکرار تبدیل می‌کنی. **هیچ فرایند زنده را خودت start/stop نکن مگر مالک صریحاً در چت گفته باشد.**

## 0) حقیقت زمین (verified 2026-07-18)

- Repo: `F:\backup` · master · HEAD `c9b9a03` · کد اختاپوس در `7742486` · ۱۲۰ تست tg سبز (runtime) · سوئیت کامل روی master قبلاً ۱۹۸/۱۹۸.
- نقاط ورود واقعی: `_ops\RUN-TG-CENTER.bat` (مرکز تلگرام) · `_ops\RUN-ORGANISM.bat` (ارگانیسم، پورت 8771؛ کورتکس 8772؛ ناظر 8773) · فلگ‌ها در `_ops\OCTOPUS-flags.cmd` (**gitignored — محتوایش را هرگز echo/commit نکن؛ token هم همین‌طور**).
- مهر CAPABILITY: **غایب (عمداً fail-closed)** — احیا فقط با `run_all.py` سبز روی **درخت زنده** در **پنجرهٔ خاموشی** (ارگانیسم off). مرجع: `01 - Dashboard/HANDOFF.md` بولت «مهرِ CAPABILITY».
- `tg_api.py` حالا `token_source` + `diagnostics()` دارد (fallback بی‌صدای token → alert؛ ریسک 409 دوبات).
- Smoke تلگرامی مستند: `/menu` → دکمه‌های 🗺 نقشه (`mn:map`) · 📮 صف تأیید (`mn:ap`) · 🧬 مأموریت‌ها (`mn:ms`) · و مسیر حسابداری `/sync` `/review` `/books` `/finance`.
- سه یافتهٔ High امنیتی ممیزی 2026-07-16 (هنوز باز، additive-fix پشت فلگ): CWE-93 (نوشتن CRLF-نشده در flags.cmd از `/save`) · OCT-AUTHZ-3 (پاک‌کردن STOP بی‌احراز روی 8773) · OWASP-A05 (`_write_env` مخرب). مرجع: `_agent_audit_output/20_security_architecture_review_2026-07-16.md`.

## 1) مأموریت

1. **`_ops/preflight_check.py` (نو، stdlib، ۱۰۰٪ read-only):** چک‌ها با خروجی PASS/FAIL/WARN: git روی master و بدون کار معلق کد (state-churn را جدا بشمار و OK بده) · وجود/تازگی مهر CAPABILITY + fingerprint · `token_source` بدون fallback (از `diagnostics()`) · offset تلگرام restart-safe · همهٔ STOP-flagها پایین · پورت‌های 8771/8772/8773 آزاد یا صاحب‌دار · وجود ≥۱ شاخهٔ backup. exit code معنادار. تست: `_ops/tests/test_preflight.py` (با tmp fixture، بدون لمس state زنده).
2. **`RESTART-REBLESS-RUNBOOK.md`** در `04 - Architect System/octopus-build-prompts/` — قدم‌به‌قدم قابل‌اجرا توسط مالک در ۵ دقیقه:
```bat
:: 0) پنجرهٔ خاموشی — ارگانیسم را ببند (دکمهٔ ♻️/STOP طبق روال مالک)
cd /d F:\backup\_ops
python -X utf8 preflight_check.py
:: 1) re-bless روی درخت زنده (فقط در خاموشی):
python -X utf8 tests\run_all.py
:: 2) استارت:
RUN-TG-CENTER.bat   و سپس در تلگرام: /menu
:: 3) smoke: mn:map → mn:ap → mn:ms → /sync → /finance
```
   + جدول «اگر X قرمز شد → کجا نگاه کن» (watchdog-log، telegram.log در `_octopus/logs/`، governor-alerts).
3. **(بخش اختیاری، فقط اگر scope ماند) فیکس‌های امنیتی S1/S2** به‌صورت additive + flag-off: sanitize مقدار `/save` قبل از نوشتن به flags.cmd (strip CR/LF/`&`) و `_write_env` merge-preserving. هر دو با تست. اعمال/فلگ = رأی مالک.

## 2) قانون اساسی
read-only بودن preflight مقدس است؛ هیچ start/stop/kill بدون رأی صریح مالک؛ token/فلگ‌ها هرگز echo نمی‌شوند؛ commit اتمیک بدون `git add -A`؛ سوئیت کامل فقط در worktree تازه (رانِ درخت زنده = فقط مرحلهٔ re-bless و فقط توسط مالک/در خاموشی)؛ هر ادعا با خروجی واقعی.

## 3) خروجی نهایی
1. preflight + تست سبز (خروجی paste) 2. RUNBOOK 3. `_agent_reports/RESTART-KIT-REPORT-<date>.md` + بولت HANDOFF/PROJECT 4. verdict: `READY TO RESTART / READY WITH WARNINGS / BLOCKED` + لیست دقیق آنچه فقط مالک باید بزند.
