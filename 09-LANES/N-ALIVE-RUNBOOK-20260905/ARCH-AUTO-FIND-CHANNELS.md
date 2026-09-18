---
type: research
status: proposal
lane: N-ALIVE-RUNBOOK-20260905
created: 2026-09-05
---

# چگونه اختاپوس با معماری فعلی کانال را پیدا می‌کند

Find ≠ send. هیچ فریم‌ورک تازه، هیچ بات تازه، هیچ `OCTOPUS_WIRE_*`.

## ۱. کانال از قبل کاتالوگ است، نه اقیانوس

معماری فعلی **کشف از صفر** نیست. یک فهرست ثابت دارد و باید بین همان‌ها حس کند کدام زنده است.

| منبع کاتالوگ | چه چیزی را نام می‌برد | مسیر |
|---|---|---|
| `ports={ziman:8791, lead:8792, studio:8793, owner:8794}` | چهار پای HTTP روی ۱۳۸ | `F:/ofn-node/ofn/config.py:294` |
| `hosts` (`ziman.` / `lead.` / `studio.` / `app.` + `panel.`) | نام عمومی همان پاها | همان فایل ~۲۹۵–۳۰۳ |
| `telegram_channel_id=OFN_TELEGRAM_CHANNEL_ID` | یک کانال پخش | `config.py:312` |
| `painting_marketing_channels` | کانال بازاریابی با `connection` ∈ planned/manual/connected/paused/blocked و `outbound_enabled` | `ofn/adapters/lead_store.py:219–234` |
| لجر `TELEGRAM_CHANNEL_SET` | کانالی که `set_telegram_channel` نوشته | `ofn/node.py:3486–3511` |
| LAYER4 | همان ۵ پورت + `8796` bridge با `/healthz` | `U-WHY…/LAYER4-CHANNEL-SELECTION.json` (لین دیگر؛ فقط خوانده شد) |

`set_telegram_channel` لینک `t.me/+` را رد می‌کند؛ فقط `-100…` یا `@username` (`node.py:3497–3503`).

کشف «گروه ناشناس اینترنت» در این کاتالوگ نیست. آن خوانش B است و هنوز مجاز نیست.

## ۲. حس از قبل هست — سه حسگر، بدون سازندهٔ جدید

```
CATALOG → SENSE → FILTER → SCORE → PROPOSE → (later) EFFECT
```

**SENSE مش**

- `GET /healthz` → `{ok:true}` فقط زنده بودن پروسس است، نه آمادگی و نه درآمد (`http_api.py:389–394`).
- `legs_healthz` در فایل سینک ضربان، کلید مجاز پنل (`sysmetrics.py:38–39`).
- LAYER4 همین کار را کرده: تونل `18791–18794,18796` → همه HTTP 200 در `2026-09-05T16:08:32+10`.

**SENSE تلگرام (خواندنی)**

- `TelegramReadOnlyAdapter`: `getMe`, `getWebhookInfo`, `getChatMemberCount` (`telegram_readonly.py`). `dry_run` همیشه. انتشار این‌جا نیست.
- انتشار جدا است: `publish_to_telegram` فقط آیتم `approved_manual` در outbox + `require_release_context` (`node.py:3513–3527`, `3615–3637`).

**SENSE لجر**

- آخرین `dispatch_receipt.v1` / `IGN1-CLOSEOUT` = کانال با مصرف‌کنندهٔ واقعی.
- تریاژ: بدون مصرف‌کننده کار نمی‌کند.

**SENSE لید (پشت فلگ خاموش)**

- `organism.py:1311–1320` می‌گوید `lead_discovery_beat` = SENSE→SCORE→propose پشت `OCTOPUS_WIRE_LEAD_DISCOVERY` (پیش‌فرض خاموش). `import wiring as _w` (`organism.py:294`).
- روی این vault فایل `wiring.py` با `def lead_discovery_beat` پیدا نشد (`unverified` اینکه روی ۱۳۸ هست). **فلگ را روشن نکن.**

## ۳. فیلتر و نمره — همان قوانین موجود

FILTER (همه از قبل نوشته شده‌اند):

- `outbound_enabled=0` یا `connection=blocked` در جدول کانال → حذف
- `HALT` / kill-switch → حذف
- L1 زیر D2=B تا `2026-09-07T08:19:19Z` برای مخاطب بیرونی تازه → حذف از EFFECT نه از SENSE
- بدون ردیف لجر و بدون healthz → حذف (تریـاژ)

SCORE (ترکیب، نه فرمول تازهٔ خودارتقا):

1. مسیر REV-1 زیمان (پول) — GOV-V8 §۵
2. تلگرام با `dispatch_receipt.v1` — TRAFFIC-1
3. چت مالک — IGN-1
4. پای مش با healthz سبز — LAYER4
5. `p_success` اگر مغز قبلاً برای همان سطح گفته (الگوی `traffic1-pick.json`؛ آن فایل محصول را چید نه کانال)

Proposal Router در تیک ارگانیسم پیشنهاد پاها را rank می‌کند، approve/send نمی‌کند (`organism.py:1224–1226`).

## ۴. اثر فقط از در موجود

بعد از پیدا کردن:

- کارت / `CHANNEL-RANK.json` بنویس (PROPOSE)
- ارسال فقط از outbox + release + بات موجود
- بات ششم و ارکستراتور تازه = REJECT (`DO-NOT-REBUILD.md`)

## ۵. حلقهٔ اجرایی با قطعات فعلی — بدون ماژول تازه

روی ۱۳۸، هر ضربان (یا هر ۱۵ دقیقهٔ تایمر موجود، نه کرون تازه اگر تایمر هست):

1. بخوان `config.ports` + `telegram_channel_id` + ردیف‌های `painting_marketing_channels` با `connection=connected`.
2. برای هر پورت: `GET 127.0.0.1:{port}/healthz` (همان LAYER4).
3. برای کانال تلگرام پیکربندی‌شده: `TelegramReadOnlyAdapter.getChatMemberCount` — اگر توکن در store موجود است؛ مقدار توکن را چاپ نکن.
4. آخرین N ردیف لجر را برای `kind` اثر خارجی بخوان؛ هر `chat_id` / `channel` را به کاتالوگ بچسبان اگر قبلاً در کاتالوگ بوده.
5. فیلتر و نمرهٔ §۳.
6. یک فایل `CHANNEL-RANK.json` append-only با `prev_hash` بنویس. ارسال نکن.

کد تازه اگر لازم شد: یک اسکریپت stdlib در `ops/` روی ۱۳۸ که **فقط همین شش قدم را صدا می‌زند**. ارکستراتور نیست؛ اتصال صریح است (`DO-NOT-REBUILD`: «فقط explicit connection»).

این جلسه آن اسکریپت را روی ۱۳۸ نگذاشت (SSH write ممنوع).

## ۶. شکاف واقعی

| شکاف | چیست | کار غلط |
|---|---|---|
| آهنگساز | هیچ تابعی به نام find_channels همهٔ حسگرها را جمع نمی‌کند | ساختن LangGraph / bus تازه |
| `wiring.py` روی این vault | `lead_discovery_beat` ارجاع شده، بدن فایل اینجا نیست | روشن کردن فلگ روی حدس |
| کاتالوگ ≠ بازار | معماری کانال ساخته‌شده را می‌یابد نه مشتری تازه | اسکرپ گروه/ads |
| `/healthz` دروغ‌گو | فقط پروسس زنده | اعلام ALIVE از healthz |

## ۷. مشتری OF و پاها — همان حلقه، کاتالوگ بزرگ‌تر

مالک خواست همه‌چیز به کاتالوگ اضافه شود و اختاپوس مشتری OF و پاها را پیدا کند.

خوانش مجاز: **فیدرهای خودمان را رتبه بده**. خوانش ممنوع: اسکرپ فن‌های OF، کوکی API، تماس سرد با لید نقاشی، ads.

| مقصد مشتری | فیدر روی دیسک | حس |
|---|---|---|
| OF `@novasolesau` | X `@novasolmate` (لینک شده ۲۰۲۶-۰۸-۲۴)، TG کانال با رسید، پست استودیو ۳۳ | فایل پروفایل + `dispatch_receipt` / `studio.post.receipt` |
| زیمان | `:8791` + فروشگاه نام‌دار در CHECKOUT-1 README + TRAFFIC-1 | LAYER4 healthz + رسید ارسال |
| نقاشی | استخر لید موجود + ۷ کانال seed در `lead_store.py:379` | امتیاز؛ تماس نه |
| استودیو | `:8793` + پست ۳۳ | healthz + رسید |

کاتالوگ اجرایی: `CATALOG.json`. آهنگساز لپ‌تاپ: `find_channels.py` → `CHANNEL-RANK.json`. پرورش: `CULTIVATE-CUSTOMERS.md`.

تناقض باز: لید نقاشی ۸ (GOV-V8:92) در برابر ۵۵ (BIZ-LEGS-PLAN:12). `status: open`.

## ۸. جمع

با معماری فعلی «پیدا کردن خودکار» = **رتبه‌بندی کاتالوگ موجود با حسگرهای موجود**. LAYER4 نصف کار مش را کرده. لجر نصف کار تلگرام را کرده. مغز `traffic1-pick` الگو برای نمره است. مشتری OF از فیدر X/TG می‌آید نه از API پلتفرم. حلقهٔ گمشده روی ۱۳۸ هنوز کپی همین اسکریپت است، نه آزادی بی‌گیت.
