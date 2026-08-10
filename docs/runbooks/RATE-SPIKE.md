# Runbook — موج درخواست (Rate Spike)

**وقتی:** وب‌هوک‌ها ۴۲۹ می‌دهند، یا پنل مالک `rejected` رو به رشد نشان می‌دهد.

## مکانیزم
- `InboundRateLimiter` یک instance process-scoped دارد؛ کلید = tenant.
- پیش‌فرض: ۶۰ درخواست / ۶۰ ثانیه / tenant (max_buckets ۱۰۲۴).
- وقتی limit رد شود: `429` + `Retry-After` برمی‌گردد و `record_rejected` ثبت می‌شود.

## بررسی
```bash
cd /home/ari/ofn
journalctl -u ofn --since "-30 min" | grep -i "rate\|webhook" | tail -20
# در پنل: کارت صندوق ورودی → chip «وصل نیست» + rejected در observability
```

## رفع
- **هشدار:** این محدودیت عمدی است. تنظیم آن = تصمیم عملیاتی (با تأیید آری).
- اگر موج از یک کلاینت قانونی است (مثلاً vendor چند رویداد هم‌زمان):
  `max_requests` را بالا ببر — نه اینکه limiter را خاموش کنی.
- اگر موج از خارج است: پنل مالک + لاگ را ببین؛ kill switch آخرین راه است.

## پیشگیری
- `max_buckets` سقف حافظه است — حتی موج با کلیدهای یکتا نمی‌تواند RAM را پر کند.
