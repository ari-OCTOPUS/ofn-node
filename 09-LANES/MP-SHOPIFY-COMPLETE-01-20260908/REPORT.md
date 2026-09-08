---
order: MP-SHOPIFY-COMPLETE-01
date: 2026-09-08 (بعدازظهر — اجرای اول)
gov: GOV-V8 / L2
---

# گزارش اجرای MP-SHOPIFY-COMPLETE-01

```text
ORDER=MP-SHOPIFY-COMPLETE-01
A_DNS_STATUS=awaiting_owner      # .com.au هنوز به GoDaddy Builder می‌رود (13.248.243.5)؛ رکوردها در مگاپرامپت
B_THEME_PUBLISHED=blocked:editor-automation # متن دموی Hero از طریق اتوماسیون قابل تعویض نبود (جزئیات پایین)؛ قالب Atelier سرِ جایش Draft است
C_COMPLETED=2/13                 # C-7 سئو ✅ (متا ذخیره شد) · C-8 پیش‌نویس‌ها ✅ (۳۵/۳۵ فعال؛ رسید PUBLISH-DRAFTS-20260908.json)
C_CARDS_FOR_OWNER=11             # فهرست دقیق پایین — هرکدام با مسیر کلیک آماده
D_POTENTIALS=15 ردیف             # 06-EVIDENCE/SHOPIFY-POTENTIALS-REGISTER-2026-09-08.md
LOCK_D0=locked (awaiting owner DNS)
VERIFIED_CASH=0.00
NEXT_SINGLE_ACTION=مالک: (۱) DNS در GoDaddy؛ (۲) کارت B-1 (متن Hero، ۲ دقیقه تایپ در ادیتورِ باز)
```

## چرا B مسدود شد (صادقانه، برای ایجنت بعدی)

ادیتور قالب Atelier در سه لایه سایه-DOM/iframe رندر می‌شود و «target frame» بین فراخوانی‌ها
detach می‌شود (خطای `unable to attach frame target` تکرارپذیر). پنل تنظیمات Hero هیچ فیلد
متنِ قابل‌کشفی در اسکن‌های deep-walk نشان نداد (Media/Layout/Appearance فقط) — متنِ «The
Elements of Style» ظاهراً در بلوک‌هاست که با اتوماسیون این جلسه باز نشد. فرم صفحات (C-5)
هم同样的: مقدار تزریقی در DOM دیده می‌شود ولی state فرم («Title is required») آن را نمی‌پذیرد؛
کیبورد واقعی هم پذیرفته نشد. **نتیجه: فرم‌های Polaris این نسخهٔ ادمین در برابر ورودی
مصنوعیِ فعلی مقاوم‌اند — صفحات settings ساده (مثل preferences که C-7 را برد) کار می‌کنند.**

## کارت‌های مالک (هرکدام ≤۵ دقیقه در ادمین؛ ادیتور/صفحات از منوی چپ)

1. **B-1 قالب (مهم‌ترین):** Themes → روی Atelier کلیک → در ادیتور، روی متن «The Elements of Style»
   در پیش‌نمایش کلیک کن → تایپ: `Sydney's Atelier of Unforgettable Gifts` + زیرمتن
   `Handcrafted gift boxes, arranged with care in Sydney.` → Save → Publish. (rollback = Balance)
2. **C-1 ارسال:** Settings → Shipping → نرخ تخت A$20 برای Australia.
3. **C-2 مالیات:** Settings → Taxes → GST ۱۰٪ (قیمت‌ها شامل مالیات).
4. **C-3 پرداخت:** Settings → Payments → PayPal (O-5 شما) را وصل کن.
5. **C-4 چک‌اوت:** Settings → Checkout → guest checkout روشن.
6. **C-5 صفحات:** Pages → Add page → عنوان `About Ziman Gift` → متن آماده (در REPORT.md §متن)
   → Visible → Save. (Contact از قبل هست.)
7. **C-6 منو:** Navigation → هدر: Catalog · Contact.
8. **C-9 تخفیف:** Discounts → کد `WELCOME10` (۱۰٪) — توزیع فقط با اعلام مالک.
9. **C-10 کانال‌ها:** Google & YouTube → sync فید Nabu → (رأی نشر جدا).
10. **C-11/12/13:** فید Nabu کامل · Notifications انگلیسی · Locations آدرس Cheltenham.

**متن آمادهٔ About (کپی-پیست):** «Ziman Gift is a Sydney-based gift atelier crafting memorable,
generously styled gift boxes for life's meaningful moments. Every box is hand-arranged in our
Sydney workshop — fresh roses, premium chocolates, keepsake dolls and elegant balloons. We
deliver Australia-wide, with same-day care across Sydney metro. When the occasion matters, Ziman.»

## رسیدها

- C-8: `board138:~/octopus-mesh/receipts/PUBLISH-DRAFTS-20260908.json` (+ قیمت‌ها از قبل: PRICE-X15-*)
- C-7: ذخیرهٔ preferences (تأیید after-save در همان فرم؛ title فیلد نداشت)
- D: `06-EVIDENCE/SHOPIFY-POTENTIALS-REGISTER-2026-09-08.md`
- B/C-5 مسدود: شرح فنی بالا + ترانسکریپت جلسه
