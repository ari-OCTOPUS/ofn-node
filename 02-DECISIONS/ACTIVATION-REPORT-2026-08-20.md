---
type: report
decision_id: ACTIVATION-REPORT-v1
owner_directive: OWNER-DIRECTIVE-ACTIVATE-FULL-INTERNAL-EXECUTION-v1 + AskUserQuestion answers 2026-08-19
status: COMPLETE_WITH_TWO_OPEN_ITEMS
recorded: 2026-08-20
---

# Activation Report — 2026-08-20

## 1. Novelty gate — ACTIVE (live)

- Verdict `verdicts.wire_novelty_gate = 1` در `_ops/owner-verdicts.yaml` (15 رأی، ساختار سالم).
- کد: `novelty_gate_enabled()` (env برنده ← owner-verdicts؛ fail-soft) در debate_loop.
- تأیید زنده پس از ری‌استارت: `novelty_gate_enabled() = True`.
- رفتار: ایدهٔ تکراری/واریاسیون آرشیوشده در دور اول مناظره رد و ledger می‌خورد (پیش از هزینهٔ دور دوم).
- برگشت‌پذیر: `value: 0`.

## 2. B1 daily_cap — APPLIED (live, first nonzero allocation)

- `life_currency.daily_pool()`: cardiac → budgets.yaml `global.life_currency_daily_cap` (1000) → صفر.
- اعمال با رأی مالک؛ امضای Ed25519 **PENDING** (owner-key.enc تأییدنشده — ثبت، نه بلاک).
- rollback: حذف کلید از budgets.yaml.
- تأیید زنده (beat 42165): `daily_cap=1000.0 · 11 members · beat_pool=1.246` — **اولین تخصیص غیرصفر از زمان حیات life-currency.v1**.
- تست‌ها: `_ops/tests/test_life_currency_b1.py` (6) + 13 قدیمی — سبز.

## 3. K=9 pilot — DONE (hypothesis refuted)

- روش: هارنس منجمد GATE3 (JUDGE_PROMPT_V3 + judge_choice_v3 + single-token fallback) + model_router (seed پین‌شده، temp 0).
- بودجهٔ ازپیش‌ثبت: ≤30 فراخوان، سقف AU$1 — مصرف واقعی: 20 فراخوان، 0 VOID، هزینهٔ micro.
- نتیجه: RS_AB=1.0 **و** RS_BA=1.0 (۹ معتبر در هر ترتیب) → classify=CONSISTENT، gate=STABLE (k_min=9، یکدستی تصادفی ۰.۳۹٪).
- **فرضیهٔ «RS_AB=1.0 در K=5 فقط artifact نمونهٔ کوچک است» ابطال شد** — در K=9 هر دو ترتیب یکدست‌اند؛ داور روی این جفت جایگاه-مستقل است (نه ادعای صحت؛ فقط استحکام جایگاه).
- Wilson CI: [0.7008, 1.0] · برچسب: MEASURED.
- رسیدها: `_ops/state/pipeline/pilot-k9-receipts.jsonl` · نتیجه: `pilot-k9-result-20260820T001141.json` + `06-EVIDENCE/PILOT-K9-20260819/RESULT.json`.

## 4. Restart — COMPLETE (all limbs)

- Runbook `RESTART-ALL.ps1`؛ تلاش ۱ ناقص (fail-closed، بدون دو نمونه)؛ تلاش ۲ کامل.
- PIDs: organism 1196→26892 · cortex 3516→4564 · center 5484→9204 · gateway→28396 · live→14572.
- گیت پذیرش: OK همه + beat 42159→42165 + fresh state (boot 00:45:34) + بدون marker باقی‌مانده.
- WARN پیشین: drift فلگ 340 vs 345 (الگوی قدیمی، نه از این ری‌استارت).
- شواهد: `06-EVIDENCE/RESTART-ACTIVATION-20260820.md`.

## 5. Open items

1. **owner-key.enc — UNVERIFIED**: مالک «مسیر واقعی را می‌دهم» گفت ولی مسیر ارائه نشد و سؤال دوباره بی‌پاسخ ماند. ریسک بازیابی بقا باز و مستند است؛ فقط با ارائهٔ مسیر (یا ساخت تازه) بسته می‌شود.
2. **سیم‌کشی زندهٔ life_economy (rent/credit/sleep/retire)**: ماژول + شبیه‌سازی آماده است؛ به ارگانیسم وصل نشده (نیاز به تصمیم/ری‌استارتِ طبیعی بعدی دارد؛ با فلگ قابل‌فعال‌سازی).
3. امضای B1 (PENDING) — با بازیابی owner-key قابل تکمیل.

## Commits (این اجرا)

`06d68cf` (activation verdict + hook) · `34d7db6` (B1 apply) · `5a1c22d` (K9 pilot) · ری‌استارت + شواهد (آخرین).
