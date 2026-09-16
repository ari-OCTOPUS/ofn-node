# 08 — آنبوردینگ همکار (کپی-پیست)

## قدم ۱ — دریافت کد (۲ دقیقه)
```bash
git clone https://github.com/ari-OCTOPUS/ofn-node.git
cd ofn-node
git log -1 --format="%H %s"     # باید ببینید: c1969bc sync: preserve board 138 runtime lineage and tests
```

## قدم ۲ — اجرای تست‌ها (۱ دقیقه)
```bash
python3 -m pytest -q
# انتظار: 2136 collected / 2131 passed / 5 skipped / 0 failed
# اگر متفاوت بود: نسخهٔ pytest شما یا env فرق دارد — گزارش بدهید، خودتان فلگ عوض نکنید
```

## قدم ۳ — شروع هر کار جدید
```bash
git checkout -b work/<اسم-کار-تاریخ>     # همیشه شاخهٔ تازه، هرگز مستقیم روی main
```

## محیط‌های واقعی (فقط اگر مالک دسترسی داد)
| دستگاه | ورود |چه چیزی آنجاست |
|---|---|---|
| برد ۱۳۸ | `ssh ari@192.168.0.138` | `/home/ari/ofn` — سیستم زندهٔ کسب‌وکار |
| برد ۱۸۰ | `ssh root@192.168.0.180` | `/opt/octopus/*` — سرویس‌های پیوستگی |
| برد ۱۸۲ | `ssh root@192.168.0.182` | `/opt/octopus*` — NATS + سنسوریوم |

## قوانین طلایی
1. بردها **زنده‌اند**: نه restart، نه deploy، نه دستکاری سرویس systemd.
2. `main` و `backup/*` فقط خواندنی‌اند؛ کار روی شاخهٔ خودت، تحویل با PR.
3. هیچ رازی (token/کلید/.env) را نخوان، در چت نگذار، کامیت نکن. قبل از هر commit: `git diff --cached` را خودت چک کن.
4. دیتابیس/لاگ/inbox/outbox/runtime-state هرگز کامیت نمی‌شوند.
5. چیزی که اثبات نکردی را ادعا نکن — بنویس NOT_VERIFIED.
6. بعد از هر تغییر: `pytest` و مقایسهٔ شمارش با 2136/2131/5.
