# Runbook — صندوق ورودی با آیتم‌های HELD

**وقتی:** پنل مالک تعداد `held` غیرصفر در صندوق ورودی نشان می‌دهد، یا
`recover_stale` آیتمی را HELD کرده (crash بین claim و mark).

## معنی
- آیتمی claim شده (pending → processing) و بعد پردازش‌گر وسط کار مرده.
- آیتم در `held` است: **معلوم نیست چه اتفاقی افتاده** — نه پردازش‌شده، نه شکست‌خورده.
- HELD عمداً «معلوم نیست» است تا آدم تصمیم بگیرد، نه خودکار.

## بررسی
```bash
cd /home/ari/ofn
python3 -c "
from ofn.adapters.marketing_inbox import MarketingInbox
from ofn import config
inbox = MarketingInbox(config.load().inbox_path)
print(inbox.counts_all())
"
```

## رفع
- آیتم HELD را با `recover_stale` دوباره claim نمی‌کنیم (عمدی — دو بار پردازش نشود).
- تصمیم انسانی: آیتم را `mark_failed` کن (رد) یا در صورت نیاز دستی دوباره ارسال کن.

## پیشگیری
- processor خشک (dry-run) با `recover_stale` دوره‌ای: آیتم‌های قدیمی را HELD می‌کند
  تا گیر نکنند. هنوز در production نیست (منتظر vendor واقعی).
