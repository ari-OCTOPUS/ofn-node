# Runbook — تونل Cloudflare (۵ دامنه)

**وقتی:** یک دامنهٔ HTTPS ۵۰۲/۵۲۱ می‌دهد یا اصلاً باز نمی‌شود.

## بررسی
```bash
systemctl is-active cloudflared
journalctl -u cloudflared -n 30
curl -sI https://panel.master-painting.com | head -1
```

## پنج دامنه
```
panel.master-painting.com   → 8794
ziman.master-painting.com   → 8791
lead.master-painting.com    → 8792
studio.master-painting.com  → 8793   + /sabaapp
app.master-painting.com     → 8793   (ingress هست، DNS شاید نه)
```

## رفع معمول
```bash
sudo systemctl restart cloudflared
curl -sI https://panel.master-painting.com | head -1   # تأیید
```

## اگر هنوز قطع
- `journalctl -u cloudflared -n 50` برای خطای واقعی.
- credentials در `/etc/cloudflared/` — دست نزن.
- **هشدار:** اگر cloudflared با ofn.service هم‌بسته است (Wants=)، ری‌استارت ofn
  ممکن است tunnel را هم برگرداند. برای maintenance، unit را mask کن (با تأیید آری).

## هشدار
- خرابی tunnel هشدار مستقل ندارد (یافته ۴۸ باز) — probe دستی یا timer محلی پیشنهاد می‌شود.
