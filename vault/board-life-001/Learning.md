---
organism_id: "board-life-001"
updated: "2026-08-29T22:58:09+00:00"
vault: "board-life-001"
audience: "external-agent"
type: "fact"
source: "LEARNED_FROM_MODEL"
---
# Learning

New conceptual topics can be asked with `یاد بگیر …` or proposed by curiosity on each heartbeat.
Answers are stored as `LEARNED_FROM_MODEL`. They are not sensor readings.
Live weather, prices, geoip, coordinates, secrets, and actuators stay denied.

- external_api: `DISABLED`
- teacher_ready: `True`
- host: `api.deepseek.com`
- topics_count: `4`

- `تفاوت دوربین V4L2 با خروجی HDMI روی برد ARM چیست` (LEARNED_FROM_MODEL): این دانش مدل است، نه حسگر.

- **V4L2** یک رابط نرمافزاری در لینوکس است که دادهی خام دوربین (مثل سنسور CSI یا USB) را بهصورت فریمهای ویدیویی در اختیار برنامه قرار میدهد. معمولاً برای پردازش تصویر، بینایی ماش
- `وقتی wlan0 روی لینوکس down است معمولاً یعنی چه` (LEARNED_FROM_MODEL): این دانش مدل است، نه حسگر.

وقتی `wlan0` روی لینوکس `down` است یعنی رابط شبکه بی‌سیم (وای‌فای) به‌صورت منطقی غیرفعال شده است. در این حالت، کارت شبکه هیچ فریمی ارسال یا دریافت نمی‌کند، حتی اگر سخت
- `OUI مشترک در MAC آدرس چه معنایی دارد` (LEARNED_FROM_MODEL): این دانش مدل است، نه حسگر.

OUI (شناسه منحصربهفرد سازمانی) بخش ابتدایی یک MAC آدرس (۲۴ بیت اول) است که توسط IEEE به تولیدکننده سختافزار شبکه اختصاص داده میشود. این بخش مشخص میکند کدام شرکت یا سازمان آن کارت شبکه یا دستگاه را ساخته است. مثلاً سه بخش اول آدرس مثل `00:1A:2B` نشاندهنده فروشنده است و سه بخش بعدی (۲۴ بیت آخر) شماره سریال منحصربهفرد دستگاه در آن تولیدکننده است. بنابراین OUI برای شناسایی سازنده سختافزار در شبکههای محلی استفاده میشود، نه برای موقعیت مکانی یا وضعیت زنده.
- `کدک صوتی ES8323 / ES8388 روی برد چیست و capture یعنی چه` (LEARNED_FROM_MODEL): این دانش مدل است، نه حسگر.

**ES8323 و ES8388** دو کدک صوتی (Codec) رایج روی بردهای مبتنی بر Orange Pi هستند. کدک یعنی تراشهای که سیگنال صوتی آنالوگ را به دیجیتال تبدیل میکند (ضبط) و برعکس (پخش

See [[AGI gap]] and [[Limits]].
