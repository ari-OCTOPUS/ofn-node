# Runbook — چرخش چهار راز CRITICAL (پیش‌شرط O11)

**وقتی:** آری تصمیم گرفت O11 (خروجی محدود) را فعال کند. `secret_rotation`
بسته است تا این چهار راز بچرخند.

## چرا
`secret_rotation` گیت بسته است و O11 sender واقعی را ممنوع می‌کند تا
رازها عوض شوند. این دستور فقط آری اجرا می‌کند — ایجنت راز را **نمی‌بیند،
نمی‌خواند و چاپ نمی‌کند**.

## دستور (توسط آری، روی برد)

```bash
# 1) چهار راز را به‌روز کن (با مقادیر جدید خودت):
nano ~/.config/ofn/secrets.env
#    - OFN_SESSION_SECRET
#    - OFN_BOT_TOKEN_OWNER
#    - OFN_BOT_TOKEN_LEAD
#    - OFN_BOT_TOKEN_STUDIO  (+ studio_partner اگر جدا است)

# 2) مجوز درست (۶۰۰):
chmod 600 ~/.config/ofn/secrets.env

# 3) ری‌استارت:
sudo systemctl restart ofn
systemctl is-active ofn

# 4) تأیید بوت:
python3 -m ofn.preflight | grep boot
```

## بعد از چرخش
1. `secret_rotation` را در کانفیگ باز کن (env `OFN_EXTRA_CLOSED_GATES`
   را بدون آن بنویس).
2. برای studio: پیش‌شرط شریک را ثبت کن و `partner_precondition` را باز کن.
3. WIRE دقیق همان transport را با تأیید روشن کن.
4. `require_release_context()` بلافاصله قبل transport اجرا می‌شود.
5. یک tenant + یک platform + سقف یک آیتم + dry-run diff + confirmation دوم.

## بدون آری
این فایل فقط runbook است — چیزی را خودکار اجرا نمی‌کند. O11 تا حکم بسته
می‌ماند و manual-first حالت production است.
