---
id: MP-SHOPIFY-COMPLETE-01
title: تکمیل کامل شاپیفای + کشف پتانسیل‌ها — هر گزینه، هر امکان
version: 1.0
date: 2026-09-08
mode: EXECUTE_WITH_RECEIPTS
gov: V8 / L2
source_head: b6fd150
owner_decision_needed: [spend-any-kind, external-publishing-beyond-granted, domain-registrar-actions]
---

# MP-SHOPIFY-COMPLETE-01 — فروشگاه زیمان را تا آخرین گزینه کامل کن؛ پتانسیل‌هایش را کشف کن

> فرمان مالک (verbatim، 2026-09-08 بعدازظهر): «پرامپت بعدیو بنویس ایجنت بعدی اتوماتیک کنه هر اپشنی هست رو کامل کنه در شاپی فای و پرامپتی بنویس که پتانسیل هاش کشف بشه»

## ۰ — وضعیت لحظهٔ شروع (همه رسیددار؛ قبل از هر ادعا دوباره بسنج)

| چی | وضعیت | شاهد/مسیر |
|---|---|---|
| فروشگاه | زنده، ۳۵ محصول (۲۹ منتشر + ۶ پیش‌نویس) | `products.json` via 138 |
| قیمت‌ها | **×۱٫۵ انجام شد** (ZM-0013 = $67.50) | `board138:~/octopus-mesh/receipts/PRICE-X15-BEFORE/AFTER-20260908.json` |
| زبان کاتالوگ | صفر فارسی (اسکن یونیکد ✓) | همان رسید |
| قالب | **Atelier نصب شده به‌صورت Draft** (id `159672565860`)؛ **منتشر نشده** (متن دموی Hero مانده)؛ rollback = Balance | ادمین → Themes |
| دامنه | `ziman-gift.com.au` → DNS به GoDaddy Builder رفته (**مالک در حال برگرداندن**؛ رکوردها: A→`23.227.38.32`، CNAME www→`shops.myshopify.com`)؛ `.com` مرده | ریشه‌یابی در OWNER-APPROVALS §PRICE-X15 |
| توکن API (روی ۱۳۸، `~/.config/ofn/secrets.env`) | فقط `read_orders + read_products + write_products` — **دامنه/قالب/تنظیمات ندارد** ⇒ هر کار غیر-محصول = مرورگر روی ادمین | probing این جلسه |
| لاگین ادمین | نشست مرورگر زنده است (Shopify admin، فروشگاه ziman-gift) | همین جلسه کار کرد |
| رأی‌های حاکم | لوکس/انگلیسی/پولدارِ سیدنی · قیمت ×۱٫۵ · O-5=PayPal Invoice · تم رایگان رسمی + کاستوم | `07-HANDOFF/OWNER-APPROVALS-2026-09-07.md` — **قبل از هر سؤال از مالک، این را بخوان؛ رأی ثبت‌شده را دوباره نپرس** |

## ۱ — فاز A: دسترسی‌پذیری ویترین (اولِ همه)

1. `socket.getaddrinfo("ziman-gift.com.au", 443)` + GET صفحهٔ محصول myshopify:
   - اگر DNS برگشته و صفحه 200 می‌دهد ⇒ قفل D0_domain در `drive_loops` خودش باز می‌شود (task.resume + دوپامین). ثبتش کن و برو فاز B.
   - اگر نه ⇒ ثبتِ «منتظر مالک» و ادامه بده (فازهای B..D به دامنه وابسته نیستند — ادمین مستقیم کار می‌کند).

## ۲ — فاز B: تمام‌کردن قالب لوکس (نیم‌کارهٔ این جلسه)

1. ادیتور: `admin.shopify.com/store/pwqytn-kp/themes/159672565860/editor` (Draft Atelier).
2. متن Hero را با متن برند عوض کن (پیشنهاد، مالک‌قابل‌تغییر):
   - Headline: `Sydney's Atelier of Unforgettable Gifts`
   - Sub: `Handcrafted gift boxes, arranged with care in Sydney. Delivered Australia-wide.`
   - CTA: `Explore the Collection` → `/collections/all`
3. Announcement bar: `Handcrafted in Sydney · Australia-wide delivery` (ت estimat/ارسال-رایگان جعل نکن — ارسال $20 است).
4. فوتر/منو: Shop · Catalog · Contact · Policies؛ لوگوی متنی «ZIMAN GIFT».
5. **Publish** کن (Balance سرِ جایش می‌ماند؛ rollback = یک کلیک). بعد از publish: اسکرین‌شات + GET صفحهٔ محصول (200 بدهد اگر DNS آماده بود).

**دستور پخت مرورگر (درس‌های این جلسه — وقت تلف نکن):**
- صفحات ادمین = iframe با کامپوننت‌های `S-INTERNAL-BUTTON` در **Shadow DOM**؛ `querySelector` ساده نمی‌بیند.
- کارکردِ اثبات‌شده: `frameLocator("iframe").locator("body").evaluate(...)` با پیمایش بازگشتی `el.shadowRoot` (نمونهٔ کامل در ترانسکریپت این جلسه: نصب Atelier با کلیک `S-INTERNAL-BUTTON` چهارم).
- `getByRole` نفوذ می‌کند ولی کلیک روی دکمه‌های سایه‌ای گاهی timeout می‌دهد ⇒ evaluate+click مطمئن‌تر است.
- اسکرین‌شات IAB گاهی اولین بار خالی است ⇒ `reload()` + انتظار ۱۰-۱۲ث + دوباره.
- برای هدف‌گیری بصری: `setViewportSize({1600,1000})` + `cua.click(x,y)` با مختصات از تحلیل تصویر.

## ۳ — فاز C: «هر گزینه» — چک‌لیست تکمیل ادمین (خودکار، رسیددار)

به‌ترتیب ارزش؛ هر ردیف یا ✅ اجرا (reversible و مجاز) یا 🟡 کارتِ رأی (پول/بیرون):

1. **Settings ← Shipping & delivery**: نواحی استرالیا + نرخ تخت $20 (اگر در تنظیمات نیست، ثبتش کن — کاتالوگ می‌گوید flat $20 AU-wide).
2. **Settings ← Taxes & duties**: GST استرالیا (۱۰٪) — قیمت‌ها شامل/به‌علاوه؟ با ABN موجود تنظیم کن؛ در تناقضِ «قیمت با مالیات» تصمیم لوکس: prices include tax.
3. **Settings ← Payments**: **PayPal Invoice (O-5، رأی ثبت‌شده)** + Shopify Payments اگر موجود؛ هر gateway پولی که فعال‌سازی هزینه ندارد = فعال کن، آنکه پول می‌خواهد = کارت.
4. **Settings ← Checkout**: guest checkout روشن؛ ایمیل/تلفن اختیاری؛ زبان انگلیسی.
5. **Content ← Pages**: About (لوکس، ۳ جمله)، Contact (ایمیل+تلفن نمایش 0493577719 اگر مجاز)، FAQ کوتاه. Policies: Refund/Terms/Privacy — از متن موجود کاتالوگ هم‌راستا (بدون وعدهٔ جعلی).
6. **Navigation**: منوی اصلی = Catalog / New Arrivals / Contact؛ فوتر کامل.
7. **Online Store ← Preferences (SEO)**: عنوان خانه = `Ziman Gift — Sydney's Handcrafted Gift Atelier`؛ توضیحات متا انگلیسی لوکس؛ `sitemap.xml` بعد از publish خودکار است — چک کن.
8. **Products**: ۶ پیش‌نویس را بازبینی/منتشر کن (عکس/توضیح/قیمت ×۱٫۵ — دیتای پایه از admin API با توکن ۱۳۸: `write_products` داری).
9. **Discounts**: یک کد `WELCOME10` بساز (۱۰٪ اولین سفارش) — **فعال ولی فقط با کارتِ اعلام به مالک در تلگرام توزیع شود؛ هیچ جا خودکار پخش نشود**.
10. **Sales channels**: Google & YouTube (فهرست رایگان) و Facebook/Instagram — نصب/اتصال free بخش‌ها را کامل کن؛ **انتشار بیرونی (publish به کانال عمومی) = 🟡 کارت رأی مالک**.
11. **Apps**: Nabu Google Feed موجود — فید را کامل کن تا محصولات به Google برسند (بعد از رأی publish).
12. **Notifications**: قالب‌های ایمیل سفارش — زبان انگلیسی، امضای Ziman Gift.
13. **Settings ← Locations**: آدرس零售 از کارت داشبورد (`settings/locations/90744291428`) — آدرس واقعی از پروفایل فروشگاه (Cheltenham NSW) ثبت/تأیید کن.

## ۴ — فاز D: کشف پتانسیل — «پرامپت پتانسیال‌یابی»

خروجی این فاز = فایل `06-EVIDENCE/SHOPIFY-POTENTIALS-REGISTER-2026-09-08.md` با جدول:
| پتانسیل | هزینه | تلاش | اثر بر درآمد | مجوز لازم | قدم اول |

حداقل این‌ها را بسنج (هر کدام: در ادمین موجود؟ فعال؟ چی لازم دارد؟):
- **Shopify Email** (ایمیل مارکتینگ رایگان تا سقف ماهانه) — خبرنامه/بازگشت مشتری
- **Gift cards** — برای هدیهٔ لوکس بسیار هم‌راستا؛ فعال‌سازی رایگان
- **Markets** (فروش بین‌المللی) — فعلا AU-only بماند (سیاست ارسال)؛ ثبت وضعیت
- **POS** — برای فروش حضوری/بازار؛ سخت‌افزار = پول = 🟡
- **Blog/SEO content** — «راهنمای هدیه دادن در سیدنی» (انگلیسی، ۲-۳ پست) — رایگان، ترافیک بلندمدت
- **Shop App / Instagram Shopping** — بعد از رأی publish
- **Judge.me یا review app** اگر نصب است — جمع‌آوری نظر بعد از اولین سفارش‌ها (نظر جعلی مطلق ممنوع)
- **Analytics dashboards** — کدام funnel setup ناقص است (sessions=0 چون دامنه مرده)
- هر گزینهٔ دیگری که در ادمین می‌بینی و این فهرست ندارد — همین منطق را اعمال کن.

## ۵ — ممنوعه

- هیچ خرید/هزینه (اپ پولی، تم پولی، تبلیغ، سخت‌افزار) بدون رأی مالک.
- هیچ انتشار بیرونی (کانال عمومی، ایمیل انبوه، نظر) بدون رأی — آماده‌سازی آزاد.
- هیچ متن فارسی روی فروشگاه؛ هیچ وعدهٔ جعلی (ارسال رایگان نیست، موجودی ثابت نکن).
- `data/gates.json` و TCB و فلگ‌های wire دست‌نخورده.
- تم Balance را حذف نکن (rollback است). رکوردهای DNS دست نزن (قلمرو مالک).

## ۶ — ترتیب

```
A (DNS check) → B (تم: Hero→Publish→اسکرین‌شات) → C (چک‌لیست ۱..۱۳) → D (رجیستر پتانسیل‌ها) → گزارش
```
هر فاز با رسید تمام می‌شود؛ فاز بعدی شروع نمی‌شود تا قبلی ✅ یا 🟡-کارت شود.

## ۷ — گزارش نهایی

```text
ORDER=MP-SHOPIFY-COMPLETE-01
A_DNS_STATUS=             # fixed+200 | awaiting_owner | ...
B_THEME_PUBLISHED=        # yes + screenshot path | blocked:reason
C_COMPLETED=              # n/13 (فهرست)
C_CARDS_FOR_OWNER=        # n (فهرست)
D_POTENTIALS=             # n ردیف + مسیر رجیستر
LOCK_D0=                  # open|locked (drive_loops)
VERIFIED_CASH=            # عدد صادق
NEXT_SINGLE_ACTION=
```

## ۸ — جملهٔ آخر

فروشگاهِ لوکسِ زیمان یک قدم از کامل‌بودن فاصله دارد و آن قدم تایپ‌کردن سه خط است. بعدش هر گزینهٔ خاموشِ ادمین یا روشن کن، یا کارتش را جلو بگذار — و رجیستر پتانسیل‌ها به مالک بگوید این فروشگاه تا کجا می‌تواند برود.
