---
type: log
project: "[[03 - Projects/Mining/PROJECT]]"
status: active
tags: [mining, decisions]
created: 2026-07-04
updated: 2026-07-04
---

# DecisionLog — Mining

> seed اولیه از [[03 - Projects/Mining/PROJECT|PROJECT]] — 2026-07-04.

**D2 — معیار مرگ survival-based، نه payback.** payback/نقدشوندگی فقط فیلد اطلاعاتی است، معیار قطع نیست.
**D-10 — execution مالی HARD_STOP.** برای architect فقط INFORM؛ هر خرید/فروش/برداشت verdict انسانی.
**D-20 — SSH مستقیم به نودها ممنوع.** فقط مسیر repo + deploy gate؛ دسترسی کیف پول ممنوع (D-11).
**قید برق ساختاری.** فقط <$0.05/kWh یا خورشیدی — بالاتر، ماینینگ متوقف.
**انتخاب کوین فقط با چارچوب.** [[03 - Projects/Mining/Coin Scouting Framework|Coin Scouting Framework]]: CPU/ARM-پذیر، لانچ <۳ ماه، death-watch.

## 2026-07-18 — معماری Coin Hunter Bot + تصمیم Regime

**D-005 — معماری کاملِ «Coin Hunter Bot / Autonomous Accumulator» سنتز شد.** ۱۳ سند در `01 - Docs/Coin-Hunter-Bot Architecture/` (`00 - MASTER-ARCHITECTURE` + ۱۱ لایه + `[[_STATUS-and-HANDOFF]]`). حلقهٔ SENSE→SCORE→ACT + مغزِ چندلایهٔ LLM، روی ناوگانِ Orange Pi 5، survival-first. همهٔ قطعاتِ پراکنده (README/CORE_PRINCIPLES/tier-prompts، نقدِ ۷-نقصی، SCOUT-B، هابِ OPI) ادغام شد. additive — هیچ فایلِ موجودی حذف نشد. برگشت‌پذیر: بله.

**D-006 — Regime هزینه = A (صفر دلار). ✅ قطعیِ مالک (۲۰۲۶-۰۷-۱۸).** مالک (آری) صراحتاً تأیید کرد: **Regime A** = AUD 0/ماه، همه‌چیز روی ناوگانِ محلیِ موجود، بدون VPS، بدون API متری؛ LLMهای Tier-بالا روی Claude تعاملیِ خودِ اپراتور (نه per-call metered). **Regime B** (Hetzner + API پولی، ~$80–150/ماه، ۲۴/۷) owner-gated و **خاموش** می‌ماند؛ فعال‌سازی‌اش نقضِ قاعدهٔ R1 و نیازمندِ verdict جدید است. برگشت‌پذیر: بله.

**D-007 — تطبیقِ عددِ ناوگان با معماری.** فرضِ سخت‌افزاریِ معماری (۱۶–۵۰ Orange Pi 5 + ۵۰–۲۰۰ ESP32 + FPGAِ پارک، از CORE_PRINCIPLES) با تحقیقِ تازهٔ [[03 - Projects/Mining/04 - Research/2026-07-14 1512 solar-swarm-mining-research|solar-swarm]] (۱۶ Pi + ۱۴۰ ESP32 + ۲ FPGA = ۱۶۲ «نود») **هم‌راستاست**؛ «۶ نود» رقمِ کهنهٔ Hcash است. رقمِ فیزیکیِ نهایی تا تکمیلِ رجیستری (مالک) `[OPEN]` می‌ماند (OQ #۶). این یک تصمیم نیست، یک reconciliation ثبت‌شده است.
