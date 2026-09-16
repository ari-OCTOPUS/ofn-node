---
type: log
project: "[[03 - Projects/Crypto - etoro/PROJECT]]"
status: active
tags: [crypto, decisions]
created: 2026-07-04
updated: 2026-07-04
---

# DecisionLog — Crypto - etoro

> seed اولیه از [[03 - Projects/Crypto - etoro/PROJECT|PROJECT]] و [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]] §Trading Autonomy — 2026-07-04.

**حاکمیت معامله.** خرید همیشه انسانی؛ فروش خودکار فقط با exit_rule از پیش ثبت‌شده + ledger + نوتیف فوری تلگرام — و فقط بعد از باز شدن Security Gate.
**D-11 — کلیدهای exchange (Bybit/OKX) off-box.** صفر دسترسی LLM؛ .envها در secrets-export تا rotation.
**فعلاً alert-only.** eToro برای retail API معاملاتی ندارد `[Assumption]` → اجرا دستی؛ ساخت مسیر خودکار تصمیم باز است (OpenQuestions).
**قالب تحقیق اجباری.** هر thesis با [[03 - Projects/Crypto - etoro/Research Template|Research Template]] + invalidation + exit_rules (هدف ۱۰۰٪ پوزیشن‌ها).
