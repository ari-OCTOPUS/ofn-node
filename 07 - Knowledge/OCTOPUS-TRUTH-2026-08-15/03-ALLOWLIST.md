---
title: allowlist v1 و شواهد robots
type: note
tags: [octopus, observatory, allowlist, robots, evidence]
up: "[[00-INDEX]]"
signed_at: 2026-08-15T14:08:00+10:00
---

# allowlist v1 — امضاشده ۱۵ اوت ۲۰۲۶

فایل: `architecture/observatory-allowlist.yaml`

## پنج دامنهٔ مجاز

| ID | دامنه | پای مربوطه | مبنای حقوقی |
|---|---|---|---|
| A | `www.rba.gov.au` | حسابداری | robots اجازه می‌دهد — [robots.txt بانک مرکزی استرالیا](https://www.rba.gov.au/robots.txt) |
| B | `www.abs.gov.au` | رنگ سرب | robots اجازه می‌دهد |
| C | `blockchain.info` | استخراج | مسیر `/q/` باز است + نقل ToS از [API بلاک‌چین](https://api.blockchain.info/) |
| D | `api.frankfurter.dev` | حسابداری / زیمان | بدون robots + ToS صریح — [frankfurter.dev](https://frankfurter.dev/) |
| E | `data.api.abs.gov.au` | حسابداری | robots با ۴۰۳ CloudFront پاسخ می‌دهد = RFC 9309 §2.3.1.3 «unavailable» + [راهنمای ABS Data API](https://www.abs.gov.au/about/data-services/application-programming-interfaces-apis/data-api-user-guide) |

## چهار دامنهٔ رد شده — با شاهد

| دامنه | دلیل رد |
|---|---|
| `www.bom.gov.au` | `Disallow: /fwo/` **و** دو گروه تکراری `User-agent: *` — ابهام = fail-closed |
| `api.coingecko.com` | `Disallow: /api/v3` — یعنی خودِ API |
| `nemweb.com.au` | کل دامنه disallow |
| `www.aemo.com.au` | `/aemo/apps/api/report` disallow |

> [!tip] چرا ردیف E نجات یافت و BOM کشته شد
> هر دو به تصحیح معناشناسی RFC 9309 برمی‌گردند. E یک ۴۰۳ می‌دهد که طبق RFC
> «unavailable» است و دسترسی **MAY** باشد. BOM یک robots معتبر می‌دهد که صریحاً
> مسیر داده را می‌بندد. تفاوت بین «نمی‌توانم قواعد را بخوانم» و «قواعد گفتند نه».

## هزینهٔ از دست دادن BOM

حذف BOM حجم دادهٔ در دسترس را کم کرد، پس پنجرهٔ مشاهده از **۱۴ روز به ۳۰ روز**
افزایش یافت تا $n$ کافی برای آزمون آماری جمع شود.

> [!bug] تسک زمان‌بندی‌شده روی لپ‌تاپ هنوز **۱۴ روز** است، نه ۳۰.
> این یک کارِ باز است — [[09-OPEN-WORK]] مورد ۴.

## نقض فعال

`earthquake.usgs.gov` در اولین اجرای زنده fetch شد ولی **در allowlist امضاشده
نیست**. مالک پذیرش موقت داد با `needs_formal_allowlist: true`.
جزئیات در [[06-OWNER-DECISIONS]].
