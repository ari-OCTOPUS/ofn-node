# واژه‌نامهٔ API — namespaceها (یافته ۹۸)

**تاریخ: ۲۰۲۶-۰۸-۱۰ · intentional**

## قانون
`painting/*` = tenant `lead`. این قرارداد تاریخی است و **breaking rename
نمی‌شود** (NEVER_13) — alias اضافه می‌شود، نه جایگزینی.

## نگاشت رسمی

| مسیر API | tenant | چرا |
|---|---|---|
| `/api/v1/painting/...` | `lead` | قرارداد تاریخی از روز اول |
| `/api/v1/studio/...` | `studio` | مطابق نام tenant |
| `/api/v1/products` | `ziman` | محصولات زیمان |
| `/api/v1/owner/painting/...` | `lead` (owner view) | همان دادهٔ lead، نمای مالک |
| `/api/v1/webhooks/<tenant>/...` | از path | وب‌هوک‌ها tenant را در path دارند |

## چرا painting؟
تنانت lead (نقاشی ساختمان) پیش از استاندارد شدن نام‌ها ساخته شد و «painting»
نام اولین محصولش بود. تغییرش همهٔ کلاینت‌ها (تلگرام WebApp ها با URL های
ثابت) را می‌شکند — هزینهٔ rename از سودش بیشتر است.

## اگر بخواهیم alias بسازیم
`lead/*` به‌عنوان alias برای `painting/*` در router — فقط اضافه، بدون حذف.
این کار هنوز انجام نشده؛ این سند تصمیم «فعلاً همان painting» را ثبت می‌کند.
