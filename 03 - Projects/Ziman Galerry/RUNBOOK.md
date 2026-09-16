# 🎁 Ziman RUNBOOK — اجرای امن validation فروش هدیه

> وضعیت: propose-only. هیچ publish/spend/sale automation بدون verdict.

---

## اصول سخت

- capacity-first: هیچ کمپین بالاتر از سقف units/week.
- هیچ auto-post/auto-DM/auto-spend.
- محصول perishable فقط local delivery.
- عکس محصول فقط با اجازهٔ مالک/تولیدکننده public می‌شود.
- هر قیمت/offer تا تأیید انسان draft است.

---

## Graph search قبل از کار

1. Load `PROJECT.md`, `MANIFEST.yaml`, `contracts/adapter.yaml`, `OpenQuestions.md`, `DecisionLog.md`.
2. Follow edge `Ziman → Accounting` for income/COGS.
3. Check `RISK-LADDER.md`: low/propose-only.
4. If action is publish/spend/DM/list product → verdict request.

---

## مجاز

- product taxonomy
- draft captions/scripts
- first-sale funnel design
- price range worksheet draft
- capacity-aware campaign plan

## ممنوع

- posting/listing products
- paid credits/spend
- confirming delivery promises
- exceeding capacity ceiling

---

## First-sale validation checklist

```yaml
hero_product:
units_per_week:
price_range:
photos_ready:
delivery_mode:
channel:
owner_verdict:
```
