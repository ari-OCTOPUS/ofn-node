---
type: plan
status: propose-only
lane: N-ALIVE-RUNBOOK-20260905
created: 2026-09-05
---

# پرورش پاها و مشتری OnlyFans — با بدن فعلی

مالک: «همرو بهش اضافه کن و پرورش بده اختاپوس رو بتونه مشتری برای اونلی‌فنز و پاها پیدا کنه»

ارسال نشد. فلگ روشن نشد. API کوکی OF دست نخورده (`REJECT` در `ONLYFANS-CONNECT.md`).

## چه چیزی اضافه شد

- `CATALOG.json` — زیمان، فروشگاه، چک‌اوت، نقاشی (مش + استخر لید + ۷ کانال seed)، استودیو، مش، تلگرام، OF، X، FeetFinder، IG/FB با handle=TBD
- `find_channels.py` — رتبه از فایل محلی
- `CHANNEL-RANK.json` — خروجی همان اسکریپت

## تناقض باز — تعداد لید نقاشی

| n | منبع |
|---|---|
| ۸ | `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/GOV-V8-REVENUE-IGNITION-2026-09-05.md:92` |
| ۵۵ | `07-HANDOFF/BIZ-LEGS-PLAN-2026-09-05.md:12` (لین دیگر؛ فقط خوانده شد) |

`resolution: null` · `status: open`  
هیچ‌کدام انتخاب خاموش نشد. تماس با هیچ استخری زده نشد (`outreach_permission=unknown` در پلن پاها).

## مشتری OF چطور پیدا می‌شود

OF خودش منبع مشتری نیست. آداپتر تا GO دوم + `OFN_ONLYFANS_HTTP_ARM` به سوکت نمی‌رسد. پست خودکار HOLD. LAYER4 صریحاً live OF را انتخاب نکرد.

مسیر پرورشی سازگار با بدن:

1. **X @novasolmate** از قبل به `onlyfans.com/novasolesau` لینک است — فیدر شماره ۱ (`SOCIAL-HANDLES.md` · `ONLYFANS-CONNECT.md`).
2. **تلگرام کانال** با `dispatch_receipt.v1` (`message_id` ۳۱ و ۳۲) — فیدر شماره ۲.
3. **پست استودیو** `STUDIO-POST1-RECEIPT.json` `message_id=33` — فیدر استودیو/OF.
4. **پای استودیو :8793** — سلامت پروسس؛ مشتری نیست.
5. **FeetFinder** — `KYC_BLOCKED`؛ در کاتالوگ هست، برداشت نیست.
6. **IG/FB** — handle هنوز TBD؛ اسکرپ و اختراع @ ممنوع.

«پیدا کردن مشتری OF» = رتبه‌بندی همین فیدرها، نه اسکرپ لیست فن‌های پلتفرم.

## مشتری پاها

| پا | موجودی روی دیسک | پرورش بدون ارسال |
|---|---|---|
| زیمان | فروشگاه `ziman-gift.com` در CHECKOUT-1 README؛ TRAFFIC-1 | `find_channels` زیمان را بالا می‌گذارد؛ SALE-1 هنوز غریبه است؛ CHECKOUT-1 خرید خودِ مالک است نه مشتری |
| نقاشی | ۸ (GOV-V8) و ۵۵ (پلن پاها) — هر دو باز | امتیاز بده؛ تماس نزن |
| استودیو/OF | پروفایل + رضایت self + پست ۳۳ | فیدر X/TG؛ پست OF جدا GO می‌خواهد |
| حسابداری | — | پارک مالک |

`legs_cultivation_beat` در `_ops/organism.py:1341` پشت `OCTOPUS_WIRE_LEG_CULTIVATE` خاموش است. `lead_discovery_beat` همان فایل `:1317` پشت `OCTOPUS_WIRE_LEAD_DISCOVERY` خاموش است. این جلسه هیچ فلگی را روشن نمی‌کند. همان کار را `find_channels.py` روی لپ‌تاپ به‌صورت propose انجام می‌دهد.

کانال‌های seed نقاشی در `lead_store.py:379–386` نام دارند. فقط ردیف تلگرام `connection=connected` است و همان هم `outbound_enabled=0`. بقیه planned.

## حلقهٔ پرورش (propose)

```
CATALOG (همهٔ سطح‌های نام‌دار)
  → SENSE (فایل رسید / LAYER4 healthz)
  → FILTER (بدون مخاطب، KYC، handle TBD، ایمیل خودکار)
  → SCORE (پول زیمان → TG با رسید → فیدر OF → مش)
  → PROPOSE (CHANNEL-RANK.json)
  → EFFECT later (outbox + release؛ این جلسه نه)
```

## قدم بعدی روی ۱۳۸ (این لپ‌تاپ انجام نداد)

کپی `find_channels.py` + `CATALOG.json` به `~/ops-ign1/ops/` و تایمر موجود — فقط نوشتن `CHANNEL-RANK.json`. نه harvest، نه send، نه `OFN_ONLYFANS_LIVE`.
