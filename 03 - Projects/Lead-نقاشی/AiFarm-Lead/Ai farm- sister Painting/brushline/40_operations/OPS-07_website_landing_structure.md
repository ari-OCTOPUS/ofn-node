# OPS-07 — Website / Landing / GBP Structure

> ساختارِ owned channel: وب‌سایت، landing/suburb pages، و Google Business Profile. تئوریِ ساختار، نه کد. ورودیِ Copywriting agent؛ منبع: KB-13/03.

---

## ۰. هدف
تبدیلِ بازدیدکنندهٔ قصد-بالا به **quote request**. owned channel که مرکب می‌شود و per-lead به‌سمتِ صفر می‌رود.

## ۱. ساختارِ وب‌سایت (sitemap مفهومی)

```
Home
├── Services
│   ├── Interior Painting
│   ├── Exterior Painting
│   ├── Strata / Body Corporate
│   ├── Property Manager / Real Estate
│   ├── Commercial
│   └── Feature Walls / Premium Finishes
├── Service Areas (suburb pages — OPS-06 §6)
├── Gallery (Before/After)
├── Reviews / Testimonials (واقعی)
├── About (مجوز، بیمه، فرایند، اعتماد)
├── Quote / Contact (فرمِ کوتاه)
└── Blog (education + seasonal)
```

## ۲. Home page (اجزا به ترتیب)
1. عنوان + ارزشِ روشن («نقاشِ دارایِ مجوز در [منطقه]، پاسخِ سریع، نتیجهٔ دیدنی»)
2. CTA اصلی: «درخواستِ quote رایگان»
3. Before/After نمونه
4. سگمنت‌ها (۵ کارت)
5. social proof (review واقعی + شمارهٔ مجوز)
6. service area map
7. CTA تکراری + اطلاعاتِ تماسِ آسان

> ⚠️ Gate: هیچ «بهترین نقاشِ سیدنی/#1/تضمینِ مادام‌العمر» (ACL).

## ۳. Suburb / Landing page (الگو)
هر صفحه: عنوانِ «Painter in [Suburb], Sydney» · محتوای محلیِ یکتا (نه کپیِ تکراری — Google جریمه می‌کند) · خدمت · «چرا این محله» (مثلِ coastal repaint cycle) · Before/After محلی · review محلی · CTA quote. (KB-10 B1)

## ۴. فرمِ Quote (کم‌اصطکاک = conversion)
حداقلِ فیلد: نام، تماس، suburb، نوعِ کار، توضیحِ کوتاه، (عکسِ اختیاری). 
- **consent checkbox غیر pre-ticked** (Privacy Act 2024 — no pre-ticked، KB-12).
- ثبتِ consent + provenance (KB-09).
- trigger: speed-to-lead <۱۵ دقیقه (KB-09/OPS-03).

## ۵. Google Business Profile (GBP) — مهم‌ترین owned asset محلی
- claim + verify؛ NAP یکدست؛ دسته‌بندیِ درست؛ service areas.
- عکسِ واقعیِ کار (نه stock)؛ به‌روزرسانیِ مستمر.
- Local Posts (API یا دستی)؛ پاسخ به **همهٔ** reviewها.
- ⚠️ Q&A API از نوامبر ۲۰۲۵ حذف شد → مدیریتِ دستی (KB-03).

## ۶. CMS (lock-in کم)
WordPress یا استاتیک (Astro/Next). انتخابِ Operator؛ Brushline فقط محتوا draft می‌کند، CMS را بازنمی‌سازد (KB-03). publish پس از approval.

## ۷. Privacy Policy (الزامِ ۲۰۲۶)
باید **افشای ADM** داشته باشد: «ما از AI در مدیریتِ enquiry/پاسخ استفاده می‌کنیم» (APP 1.7، از ۱۰ دسامبر ۲۰۲۶ — KB-12). + access/correction/deletion + breach response. **[verify-NSW با وکیل]**

## ۸. اتصال
محتوا: OPS-06. انتشار: KB-03. lead: KB-09. انطباق: KB-12/OPS-09. تأیید: TG-01.
