# Runbook — NTP و ساعت

**وقتی:** خرابی TLS/HMAC ناگهانی، امضای تلگرام رد می‌شود، یا بوت CRITICAL روی ساعت.

## بررسی
```bash
timedatectl status          # NTP synchronized: yes؟
date -u                     # با زمان واقعی مقایسه کن
```

## رفع
```bash
sudo timedatectl set-ntp true
sudo systemctl restart systemd-timesyncd
date -u                     # دوباره بسنج
```

## اگر همچنان drift
- برد باتری RTC ندارد؛ بعد از قطع برق، ساعت از صفر شروع می‌شود.
- drift بعد از boot می‌تواند TLS/HMAC را بشکند بدون اینکه SAFE MODE بیاید.
- اگر باز هم غلط بود: گزارش به آری؛ `timedatectl set-time` دستی با تأیید.

## هشدار
- تغییر `timedatectl` فقط با تأیید آری (قاعدهٔ systemd/ops).
- boot فقط یک‌بار ساعت را می‌سنجد؛ drift میانی دوره‌ای نیست (یافته ۴۹ باز).
