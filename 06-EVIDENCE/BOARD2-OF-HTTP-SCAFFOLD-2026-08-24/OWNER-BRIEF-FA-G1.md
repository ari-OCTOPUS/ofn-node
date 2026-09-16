---
type: evidence-brief
status: complete-awaiting-second-go
created: 2026-08-24
tags: [board2, ofn, onlyfans, g1, http-scaffold, dry-hold, owner-brief]
related:
  - "../BOARD2-OF-LIVE-PATH-2026-08-24/NEXT-SLICE.md"
  - "../BOARD2-OF-LIVE-PATH-2026-08-24/SECOND-GO-CHECKLIST.md"
  - "RESULT.json"
---

# 🐙 بریف ari — اسلایس G1: کلاینت HTTP فقطفنز، پیشفرض خشک (۲۰۲6-08-24)

## یک خط

کلاینت HTTP فقطفنز روی Board2 ساخته شد، ولی از `publish()` **غیرقابل‌دسترس** است تا GO دومِ تو — حتی با LIVE=1 و کوکی، عمیق‌ترین نقطهٔ reachable قانونِ بدون‌سوکتِ `onlyfans:http-scaffold-dry-hold` است.

## قرارداد نهایی (کد + تست)

| وضعیت | خروجی | سوکت؟ |
|---|---|---|
| `dry_run=True` (پیشفرض) | ok + `adapter:dry-run` | ❌ |
| `dry_run=False` و `OFN_ONLYFANS_LIVE` ست نشده | `wire:disabled` | ❌ |
| LIVE=1 بدون کوکی | `onlyfans:no-credentials` | ❌ |
| LIVE=1 + کوکی، بدون قفل دوم | `onlyfans:http-scaffold-dry-hold` ← **تغییر G1** | ❌ |
| LIVE=1 + کوکی + `OFN_ONLYFANS_HTTP_ARM=1` + بدون URL | `onlyfans:endpoint-unconfigured` | ❌ |
| (فقط بعد GO دوم) همه + `OFN_ONLYFANS_POST_URL` | `_post_create`: POST واقعی، timeout ۱۵ث، خطاها→rule | تست با mock |

**قفل دوم:** `OFN_ONLYFANS_HTTP_ARM` — روی برد ست نشده و توسط ایجنت هرگز ست نمیشود. **اندپوینت هاردکد نشده** — `OFN_ONLYFANS_POST_URL` را خودت موقع GO ست میکنی (بعد از بازبینی قرارداد اندپوینت در G3/G5).

## تستها

- **۹/۹ سبز** — `tests/test_onlyfans_http_scaffold.py` (جدید؛ همهٔ مسیرهای خشک با urlopen ماکشده + بمب AssertionError تا اثباتِ «هیچ شبکه»؛ تستِ قناریِ لو رفتن کوکی در نتایج)
- **۳/۳ سبز** — `TestOnlyFansAdapter` قبلی دستنخورده پاس
- ⚠️ **دو FAIL از قبل موجود بود** (اثباتش: با فایل بکاپِ قدیمی هم FAIL ماندند) — تستهای کهنهٔ «سه adapter» و «eleven canonical» که هنوز shopify/onlyfans را نمیشناسند + drift فایل matrix. **خارج از اسلایس من**؛ پیشنهاد: اسلایس پاکسازی جداگانه بعد از تأیید تو.

## فایلهای تغییر یافته

| مسیر | تغییر | بکاپ |
|---|---|---|
| `Board2:/home/ari/ofn/ofn/adapters/platforms/onlyfans.py` | بازنویسی scaffold → HTTP double-locked (۱۸۶ خط) | `/home/ari/.local/share/ofn/bak-onlyfans-http-scaffold-20260824-161118/` |
| `Board2:/home/ari/ofn/tests/test_onlyfans_http_scaffold.py` | جدید (۹ تست) | — |

سرویس `ofn.service` فعال ماند و ریاستارت نشد (تفاوت رفتاری فقط زیر LIVE=1 قابل دسترس است که ست نیست). در `secrets.env` برد صفر کلید `OFN_ONLYFANS_*` هست — طبق قاعده.

## سکرت‌ها

- فقط **نام کلیدها** مستند شد: `OFN_ONLYFANS_SESSION_COOKIE` / `USER_AGENT` / `ACCOUNT_ID` / `POST_URL` / `LIVE` / `HTTP_ARM`
- مسیر vault برای پر کردن توسط تو: `F:\backup\_ops\secrets\onlyfans\session-cookie.env` (طبق VAULT-PATH.md پک قبلی)
- کوکی call-time از env خوانده میشود، لاگ نمیشود، در ruleها بازتاب ندارد (تست قناری سبز)

## مرزهای رعایتشده

LIVE ست نشد · مقدار کوکی جایی نوشته نشد · consent/publish_to_onlyfans دست نخورد (G3/G5) · Shopify/Etsy نه · کپشن/قیمت invent نشد.

## قدم بعدی (بعد از بازبینی تو)

G2 (فایل vault کوکی — نامها آماده، پر کردن با دست تو) → G3 (consent scope onlyfans) → G5 (OwnerRelease call-site) — و تا `SECOND-GO-CHECKLIST` کامل و GO صریح تو نرسد، هیچ LIVE/ARM ست نمیشود و هیچ پست زندهای نمیرود.
