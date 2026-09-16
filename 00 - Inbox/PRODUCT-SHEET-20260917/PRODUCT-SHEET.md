---
title: PRODUCT-SHEET 2026-09-17 — عکس و اطلاعات ۵ محصول (پاسخ به «عکساشونو بیار»)
updated: 2026-09-17T06:35:00Z
tags: [octopus, ziman, shel, checkout1, owner-card]
---

# شیت محصولات — ۲۰۲۶-۰۹-۱۷

منبع: JSON عمومی فروشگاه `https://ziman-gift.com.au/products/<handle>.json` (کارت قدیمی CHECKOUT-1 آدرس را بدون `.au` نوشته بود — **دامنهٔ درست `ziman-gift.com.au` است**؛ کارت اصلاح شد).

دو منبع دادهٔ موجودی، دو روایت دارند و هر دو اینجا آمده‌اند (بدون جعل):
- **Admin API (2026-09-16 11:25Z، `rca/SHELF-1.json`)**: qty فیزیکی — دو محصول صفر.
- **صفحهٔ عمومی (امروز)**: «Add to cart» برای همه فعال است (Shopify این دو را `untracked` نگه داشته = قابل سفارش‌اند ولی عدد انبار ندارند).

## دو محصولی که پرسیدید («قهرمان»ها) — موجودی صفر در Admin

### ۱) Black & Gold Gift Box with Flowers, Balloons & Chocolates — **A$120.00**
- **وضعیت**: Admin qty=0 • صفحهٔ عمومی: قابل افزودن به سبد (untracked)
- **توضیح فروشگاه**: «Hand-arranged black & gold gift box with flowers, balloons and chocolates. Made to order in Sydney by Ziman Gift.» + flat-rate shipping A$20
- **عکس‌ها** (۴ تصویر؛ دو تای اول دانلود شد):
  - `img/black-and-gold-gift-box-with-flowers-balloons-and-chocolates__IMG_4418.jpg`
  - `img/black-and-gold-gift-box-with-flowers-balloons-and-chocolates__IMG_4487.jpg`
- **قهرمان یعنی چه؟** اصطلاح لِینِ من بود، نه دادهٔ فروش: یعنی گران‌ترین/شاخص‌ترین محصول کاتالوگ — **هیچ فروشی نداشته** (صفر سفارش؛ لجر `VERIFIED_CASH=0`).

### ۲) Blue Roses in a Blue Basket — **A$75.00**
- **وضعیت**: Admin qty=0 • صفحهٔ عمومی: قابل افزودن به سبد
- **توضیح**: ۵۵۹ کاراکتر (کامل‌ترین توضیح کاتالوگ)
- **عکس**: `img/blue-roses-in-a-blue-basket__IMG_4058.jpg`

## سه محصول موجودی‌دار (انتخاب‌های CHECKOUT-1)

| محصول | قیمت | عکس | لینک خرید |
|---|---|---|---|
| Black & Red Valentine Gift Box | **A$142.50** | `img/black-and-red-valentine-gift-box__5CCA6A78-7E5E-42F2.jpg` | https://ziman-gift.com.au/products/black-and-red-valentine-gift-box |
| Black Gift Box with Teddy | **A$135.00** | `img/black-gift-box-with-teddy__612325A8-00C5-4D93.jpg` | https://ziman-gift.com.au/products/black-gift-box-with-teddy |
| Black Gift Box with Pink Teddy | **A$90.00** | `img/black-gift-box-with-pink-teddy__500683F6-6BD5-4427.jpg` | https://ziman-gift.com.au/products/black-gift-box-with-pink-teddy |

## چه نیاز است از شما (اگر بخواهید ادامه دهیم)

۱. اگر موجودی واقعی $120 و $75 را دارید → عدد بدهید تا در Shopify ثبت شود (وگرنه همین untracked می‌ماند و سفارش می‌پذیرد).
۲. برای CHECKOUT-1 یکی از سه محصول بالا را بخرید و `order_id` + `payout_id` را بفرستید (یا بگویید کدام را من در پیش‌نویس سفارش بگذارم و شما فقط تأیید پرداخت بزنید).

JSON خام هر ۵ محصول در همین پوشه است (`*.json`) برای هر بازبینی فنی.
