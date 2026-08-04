---
tags: [ofn, ops, firewall, security]
aliases: [فایروال, Apply]
updated: 2026-08-04
---

# اعمال فایروال — فقط آری

**پیوندها:** [[INDEX]] · [[DECISIONS]] · [[CLAUDE]]

> قاعده‌ها در `ofn-lan.nft` هستند و **اجرا نشده‌اند**. این فایل روش اعمال
> بدون قفل‌شدن است. ایجنت این مراحل را اجرا نمی‌کند — لایهٔ ۲ از D-8 است و
> تأیید مالک لازم دارد.

اگر SSH را از دست بدهی، تنها راه برگشت مانیتور و کیبورد روی خود برد است.
همهٔ این آیین برای اجتناب از همان است.

---

## ۰) قبل از هر چیز — قلم ۱ را تمام کن

```bash
# ورود با رمز باید خاموش باشد (باید -s -g را ببینی):
ps -o args= -C dropbear | head -1

# و کلیدت باید آنجا باشد (باید ≥۱ باشد، نه صفر):
wc -l < ~/.ssh/authorized_keys
```

هر دو تأیید شد (۲۰۲۶-۰۸-۰۴ ۱۴:۳۸). **قبل از رفتن به مرحلهٔ ۱، یک بار از
یک ترمینال تازه با کلید وارد شو** — اگر کلید کار نمی‌کند و رمز هم خاموش
است، فایروال گذاشتن یعنی سه قفل روی یک در.

## ۱) نصب nftables

روی این برد نصب نیست:

```bash
sudo apt update && sudo apt install -y nftables
sudo systemctl disable --now nftables   # فعلاً خودکار بالا نیاید
```

`disable` عمدی است: تا وقتی قاعده‌ها تأیید نشده‌اند، نباید بعد از ریبوت
خودکار اعمال شوند.

## ۲) بازبینی متغیرها

`ofn-lan.nft` را باز کن و این دو را چک کن:

```
define LAN   = 192.168.0.0/24     ← با  ip -4 -o addr show  مطابقت دارد؟
define ADMIN = $LAN               ← فعلاً کل LAN. سخت‌تر کردنش بعد از تست.
```

## ۳) بررسی نحوی — بدون اعمال

```bash
sudo nft --check --file ~/ofn/deploy/firewall/ofn-lan.nft
```

خروجی خالی یعنی سالم. **اگر اینجا خطا داد، جلوتر نرو.**

## ۴) dead-man switch را مسلح کن — قبل از اعمال

```bash
sudo systemd-run --on-active=300 --unit=fw-rollback \
     /usr/sbin/nft flush ruleset
```

پنج دقیقهٔ دیگر همهٔ قاعده‌ها پاک می‌شوند و شبکه به حالت باز برمی‌گردد.
اگر قفل شدی، پنج دقیقه صبر کن و برگرد.

## ۵) اعمال

```bash
sudo nft --file ~/ofn/deploy/firewall/ofn-lan.nft
sudo nft list table inet ofn_fw
```

## ۶) تست — از یک نشست **دوم**

نشست فعلی را **نبند**. یک ترمینال جدید باز کن و:

```bash
ssh ari@192.168.0.138 'echo ok'                         # باید ok بدهد
for p in 8791 8792 8793 8794; do
  curl -s -m 2 -o /dev/null -w "$p %{http_code}\n" "http://127.0.0.1:$p/healthz"
done                                                     # هر چهار: 200

systemctl is-active ofn cloudflared                      # هر دو active
curl -sI -m 5 https://panel.master-painting.com | head -1  # تونل هنوز زنده
```

از یک دستگاه دیگر روی LAN، برای اطمینان از اینکه default-deny واقعاً می‌بندد:

```bash
curl -m 3 http://192.168.0.138:8791/     # باید timeout بدهد، نه جواب
```

## ۷) اگر همه‌چیز سبز بود — رول‌بک را لغو کن

```bash
sudo systemctl stop fw-rollback.timer
```

## ۸) ماندگار کردن — فقط بعد از تأیید مرحلهٔ ۶

```bash
sudo cp ~/ofn/deploy/firewall/ofn-lan.nft /etc/nftables.conf
sudo systemctl enable --now nftables
sudo reboot          # و بعد از بالا آمدن، مرحلهٔ ۶ را دوباره بگیر
```

ریبوت اختیاری نیست: تنها راه اثباتِ اینکه قاعده‌ها بعد از برق‌رفتن هم
درست برمی‌گردند همین است.

---

## برگشت دستی

```bash
sudo nft delete table inet ofn_fw      # فقط جدول OFN
sudo nft flush ruleset                 # همه‌چیز — راه اضطراری
```

## بعد از اعمال — DECISIONS.md را تازه کن

جدول وضعیت D-8، قلم ۲: `⬜` → `✅` با تاریخ. گیت `miner_isolation` تا قلم
۳ (کانتینر) هم انجام نشود بسته می‌ماند.
