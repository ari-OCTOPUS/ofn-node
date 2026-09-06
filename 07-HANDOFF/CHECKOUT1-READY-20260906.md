---
title: CHECKOUT-1 READY — بستهٔ خرید تستی مالک
updated: 2026-09-06T01:55:00Z
tags: [octopus, checkout1, verified-cash, draft]
---

# CHECKOUT-1 — آمادهٔ خرید تستی توسط مالک

**هدف:** بستن `CHECKOUT-1` با رسید واقعی (`order_id` + `payout_id`) — نخستین نقطهٔ داده در مسیر `VERIFIED_CASH`.
**مالکِ عمل:** آری (پرداخت با کارت خودش — `REPORTED_NOT_VERIFIED` تا رسید مستقل).
**نقش ایجنت:** آماده‌سازی + بستن رسید پس از خرید. صفر ارسال، صفر action.

## محصول (از OWNER-GO-CHECKOUT1-AUTONOMOUS-20260905)

```text
sku        : ZM-GALLERY-0013
product    : Kitty Bubble Balloon Gift Box with Pink Roses and Chocolates
url        : https://ziman-gift.com/products/kitty-bubble-balloon-gift-box-with-pink-roses-and-chocolates
price_aud  : 45
buyer      : owner_self
```

## گام‌های مالک (۵ دقیقه)

1. لینک بالا را در مرورگر باز کن — **صفحه باید بدون خطا لود شود** (همین = بسته‌شدن SHELF-1 اگر تصویر/قیمت/توضیح/موجودی/هزینهٔ ارسال کامل بود؛ اگر چیزی ناقص بود، اسکرین‌شات بده تا کامل کنم).
2. Add to cart → Checkout → پرداخت با کارت خودت (A$45).
3. دو رشته را برای من بفرست: `order_id` و `payout/confirmation_id`.

## آنچه من می‌بندم (پس از رشته‌های بالا)

```text
CHECKOUT-1 = CLOSED with order_id + payout_id   → REPORTED_NOT_VERIFIED
atp_reserve   = 30% of 45 = A$13.50 (ledger)
SETTLEMENT-BRIDGE (C7-1) رسید درگاه را با order تطبیق می‌دهد → VERIFIED_CASH مسیرش باز می‌شود
OMLL_LOOP     = این تراکنش، outcomeِ بازوی baseline/مدل رتبه‌بندی لید هم می‌شود
```

## اگر صفحه ناقص بود

اسکرین‌شات + نام فیلد ناقص → همان یک محصول را کامل می‌کنم (CAP-3 با همین بسته می‌شود؛ محصول تازه لازم نیست).
