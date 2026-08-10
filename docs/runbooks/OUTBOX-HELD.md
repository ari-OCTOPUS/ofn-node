# Runbook — صف خروج (Outbox) با آیتم HELD

**وقتی:** پنل مالک `نگه‌داشته` (held) در درِ خروج نشان می‌دهد.

## معنی
- آیتمی در flight بود (claim شده) وقتی فرایند مرد — مثلاً قطع برق بین ارسال و
  ثبت acknowledgment.
- `recover_stale` عمداً **دوباره ارسال نمی‌کند**: نمی‌دانیم ارسال تمام شده یا نه.
  ارسال دوباره = مشتری پیام تکراری می‌بیند. نگه‌داشتن = آدم با زمینه تصمیم می‌گیرد.

## بررسی
```bash
cd /home/ari/ofn
python3 -c "
from ofn.adapters.outbox import Outbox
from ofn import config
from ofn.kernel.tenancy import TenantRegistry
from ofn.adapters.packloader import load_dir
cfg = config.load()
reg = TenantRegistry(load_dir(cfg.packs_dir))
ob = Outbox(cfg.outbox_path)
for t in reg:
    s = reg.scope(t)
    for it in ob.held(s):
        print(t.value, it.idem_key, it.kind, it.note)
"
```

## رفع
- هر آیتم HELD: تصمیم انسانی.
- اگر می‌دانیم ارسال نشده: `mark_failed` + در صورت نیاز ارسال دستی.
- اگر می‌دانیم ارسال شده: `mark_sent` (فقط از in_flight/held مجاز است).

## قانون
- `resend=True` در `recover_stale` فقط برای transport های واقعاً idempotent —
  هرگز سراسری.
