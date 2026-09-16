# BIZ-LEGS PLAN — 2026-09-05 · GOV_VERSION=V8 · LADDER=L0 · VERIFIED_CASH=0

Owner order (2026-09-05): «تست بگیر، بهش پاهای بیزنسیش را یاد بده، برنامه‌ریزی کنه، عمل کنه — اسکن کن، زیرساخت هست.»
این سند نتیجهٔ همان سفارش است: اسکن سطح-۱ انجام شد، پاها به حافظهٔ production teaching شد
(۶ ردیف commit-شده via MemoryGate، پروب IGN-3)، و برنامهٔ زیر حالا در نقطهٔ تصمیم
`revenue-ignition plan` توسط `retrieval_router` cite می‌شود (`mem_59833820830b13ff`).

## وضعیت پاها (اسکن ۲۰۲۶-۰۹-۰۵، همه با رسید)

| پا | وضعیت سطح-۱ | بعدی تکی |
|---|---|---|
| painting-B2B | ۵۵ لید researched روی `board138:~/.local/share/ofn/painting.sqlite`؛ ۲۶ قابل‌تماس با شماره؛ PR #201 حالا **MERGED** (gh، 24 چک)؛ `outreach_permission=unknown` روی هر ۵۵ ردیف | کارت CALL-TODAY برای مالک (باز — تصمیم مالک) |
| shelf1-products | `products.sqlite` روی ۱۳۸ هست (204800B، 08-27) ولی `shelf1_readiness_probe.py` هیچ‌جا تحویل نشده ⇒ UNMEASURED | نوشتن پروب فقط‌خواندنی و اجرا روی ۱۳۸ |
| owner-channel | TRAFFIC-1 arm A LIVE: LEDGER ۱۳۸، msg_id=31، 08:19:19Z؛ پنجرهٔ L1 تا 09-07T08:19Z؛ score 09-08 | هیچ ارسال جدید تا بستن پنجره؛ arm B بعدش |
| checkout/payment | CHECKOUT-1 جام AU$25 منتظر خرید مالک؛ poller زنده؛ paid-call pattern 1/day؛ `monthly_ops_cap AU$45`، burnable AU$100 | poll ادامه؛ هیچ تراکنش خودکار |
| هدف مالک | `owner-goal.json`: اولین `attribution.claimed` از صفر با لید واقعی تازه (۶۶۷۹۵۱ SET_ASIDE — هرگز) | متر موفقیت همان است |

## ثبت حافظه (TEACH receipt)

- رسید: `09-LANES/BIZ-LEGS-TEACH-20260905/receipts/TEACH-BUSINESS-LEGS.json`
  sha256 `14968e87e56c43cb05ba5b010f6f13de5ea5d6b7bd8fe418b3471d4776333b83`
- ۶ ردیف `verb=commit`، trust=GRADED، readback همه true؛ ۱۰۹۳→۱۰۹۹ ردیف.
  mkeyها: `bizleg-painting-leads-20260905` · `bizleg-shelf1-products-20260905` ·
  `bizleg-traffic1-owner-channel-20260905` · `bizleg-checkout1-payment-20260905` ·
  `bizleg-goal-attribution-20260905` · `bizleg-plan-20260905`
- route-check (فلگ in-process، الگوی IGN-3): `revenue-ignition plan → [plan row]` ·
  `business legs painting callable leads → episodic+semantic شامل plan row` ·
  `ziman-rev1-shelf → همچنان cite می‌شود (حلقهٔ قبلی سالم)`
- فلگ‌ها فقط داخل پروسهٔ teach (آینهٔ `OCTOPUS-flags.cmd:359`)؛ self-loop خود سیستم
  هنوز `flag-off` است (نمونه: self-loop-ingest.jsonl 08:38:54Z verb=skip) — روشن‌کردن
  دائمی فلگ برای daemon = تصمیم مالک، نه این lane.

## status: open, requires: owner_decision

1. **کارت CALL-TODAY** (top-5 لید با شماره) به کانال تلگرام مالک — مسیر ارسال و گاردها
   پروب‌شده (traffic1_send الگو؛ BUDGET cap 25/day؛ HALT probe). یک کلمهٔ مالک کافی است.
2. **روشن‌کردن دائمی `OCTOPUS_WIRE_MEMORY_GATE` برای daemon** تا self-loop خود سیستم
   بتواند بیاموزد (الان فقط ایجنت‌ها teach می‌کنند).
3. **تأمین `shelf1_readiness_probe.py`** — در بستهٔ REV-1 نام برده شده ولی هیچ‌گز تحویل
   نشد (نه ۱۳۸، نه vault، نه Downloads).

## مرزهای سفت (تکرار، چون «عمل کنه» بود)

- تا `hold_external_until_L1` در ACK امروز: هیچ EXTERNAL_ACTIONS باز نمی‌شود؛ ارسال جدید ممنوع.
- ایمیل/پیام به مشتری بسته می‌ماند (AGENTS §4 + permission=unknown روی ۵۵ لید). تلفن = فقط انسان.
- سه ممنوعهٔ V7 و بند ۵ (خودارتقایی) به قوت خود است.
