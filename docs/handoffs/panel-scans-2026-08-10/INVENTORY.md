---
tags: [ofn, handoff, panels, scan]
aliases: [اسکن کنترل‌پنل‌ها]
updated: 2026-08-10
---

# اسکن پایهٔ چهار کنترل‌پنل — ۲۰۲۶-۰۸-۱۰

> شاهد قبل از ارتقا. ایجنت بعدی **قبل از ویرایش** دوباره اسکن زنده بگیرد؛
> این فایل فقط نقطهٔ شروع است.

**پیوندها:** [[AGENT-NEXT-PANEL-UPGRADE]] · [[INDEX]] · [[HANDOFF]] · [[MEGAPROMPT-MARKETING-PLATFORM-INTEGRATION]]

---

## وضعیت سرویس هنگام اسکن

```
ofn · hypno-fugu-mini · cloudflared → active
HTTPS panel/ziman/lead/studio → 200
collected tests OFN → 1657 (با tools/repo_baseline.py بسنج)
HEAD مرتبط → d140756 (marketing connector infra) + docs uncommitted
```

---

## چهار کنترل‌پنل

| # | پنل | فایل | پورت | دامنه | نقش |
|---|---|---|---:|---|---|
| ۱ | مالک / ارگانیسم | `web/panel.html` | ۸۷۹۴ | panel.master-painting.com | کوک‌پیت آری |
| ۲ | زیمان | `web/ziman.html` | ۸۷۹۱ | ziman.master-painting.com | شریک ملیحه · GiftMesh |
| ۳ | لید نقاشی | `web/lead.html` | ۸۷۹۲ | lead.master-painting.com | شریک عباس |
| ۴ | استودیو / چیدمان | `web/studio.html` | ۸۷۹۳ | studio.master-painting.com · /sabaapp | شریک سبا |

`hypno` WebApp جداست و در این مأموریت چهارتایی نیست مگر آری بگوید.

---

## ۱) panel.html — مالک

**عنوان:** ارگانیسم — کنترل پنل آری  
**اسکن مرورگر (بدون auth):** هدر + توقف اضطراری + «در حال اتصال…» + پیام ورود از تلگرام.

### بخش‌های موجود (حذف ممنوع)

```
توقف اضطراری / بنر kill
نقاشی ساختمان — لید و مارکتینگ (تب‌ها: لیدها · دیجیتال · مینی‌وب · B2B · منابع)
صف تصمیم (قرمز/زرد/سبز)
قلب — انرژی Fugu
بوت — چک‌ها
سلامت برد — زنده
سیستم عصبی
دریچه‌ها
درِ خروج — outbox
زنجیرهٔ لجر
سطوح — چه چیزی سرو می‌شود
```

### APIهایی که UI صدا می‌زند (نمونه)

`/api/v1/owner/status` · `queue` · `events` · `metrics` · `painting/*` ·
`kill` · `ledger/summary` · `brain` · `snapshot` · `risks` · `partners` ·
`mini-apps` · `mini-webs` · `telegram`

### شکاف نسبت به بک‌اند تازه (d140756)

```
⬜ inbox وب‌هوک در UI دیده نمی‌شود
⬜ connector metrics / health در UI نیست
⬜ correlation search نیست
⬜ observability endpoint اختصاصی برای panel نیست
⬜ وضعیت «اندازه‌گیری نمی‌شود» برای connectorها نیست
```

---

## ۲) ziman.html — ملیحه

**عنوان:** زیمان  
**اسکن مرورگر (بدون auth):** «سلام» · کارت «از داخل تلگرام باز کنید» · «وارد نشدید».

### موجود

```
فرم قطعه / قفسه محصولات
سؤال‌های کرنل
عکس قطعه
toLatinDigits برای ارقام فارسی
```

### APIها

`/api/v1/auth/session` · `status` · `questions` · `answers` · `products[+photos]`

### شکاف / بهبود بدون حذف

```
⬜ اسم قبل از auth خنثی بماند (درس ۷)
⬜ empty-state قفسه با کنش روی همان صفحه
⬜ اگر status/outbox خلاصهٔ شریک لازم است — اضافه شود، جایگزین فرم نشود
⬜ هیچ jargon فنی
```

---

## ۳) lead.html — عباس

**عنوان:** لید نقاشی  
**اسکن مرورگر:** پیش‌نمایش بدون auth (مثل بقیه).

### موجود

```
CRM پارتنر روی boot (refreshLeadCrm)
جستجو/فیلتر/وضعیت
جواب/قیمت (outbox RED)
escLike برای wildcard
```

### APIها

`painting/dashboard` · `painting/leads` · `…/reply` · `…/quote` ·
`status` · `questions` · `answers`

### شکاف / بهبود بدون حذف

```
⬜ امتیاز/score_json در کارت لید اگر هست نشان داده شود (غیرفنی)
⬜ empty-state گرم وقتی لید نیست
⬜ وضعیت outbox شخصی پارتنر اگر endpoint خواندنی دارد — اضافه
⬜ حذف دکمه/جریان موجود ممنوع
```

---

## ۴) studio.html — سبا

**عنوان:** چیدمان  
**مسیر سرو:** `/` و `/sabaapp`

### موجود

```
امروز / آرشیو / گالری / کسب‌وکار
دستیار چت
آپلود چندتایی + حذف تک‌عکس
marketing board خواندنی
shell/boot
```

### APIها

`studio/gallery` · `albums` · `media` · `drafts` · `assistant/*` ·
`marketing` · `board` · `overview` · `guidance` · `shell/boot`

### شکاف / بهبود بدون حذف

```
⬜ setHeaderColor/setBackgroundColor اگر هنوز باز است
⬜ وضعیت انتشار/outbox به زبان گرم (بدون technical)
⬜ marketing summary اگر endpoint داده می‌دهد ولی UI ناقص است — ادغام
⬜ partner_precondition را دور نزن؛ فقط صادقانه نشان بده
```

---

## قاعدهٔ اسکن مجدد برای ایجنت بعدی

برای هر پنل، قبل از ویرایش:

1. screenshot مرورگر (HTTPS)
2. HTML سرو‌شده از loopback با Host درست
3. فهرست headingها / idها / APIها
4. ماتریس «موجود / شکاف / ممنوع‌حذف»

بعد از ویرایش: restart + curl بایت + screenshot بعد.
