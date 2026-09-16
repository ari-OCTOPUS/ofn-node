---
prompt_title: OFN-BOOT — راه‌اندازی ارتباط برد اورنج‌پای ↔ ویندوز OCTOPUS
version: "1.0"
written_by: ZCode (GLM-5.3) — به درخواست مالک آرمین، 2026-08-16 ~16:5x
audience: ایجنت Claude Code روی برد اورنج‌پای (Linux ARM)
duration: یک نشست (~۱ ساعت)
mission: (۱) فهمیدن کجایی و چیه (۲) سینک git برد→ویندوز (۳) راه‌اندازی heartbeat
---

# 🐙 OFN-BOOT — تو کی هستی، اون‌طرف کی هست، و چطوری وصل می‌شوید

## ۱. زمینه — دو دقیقه بخوان

سیستمی به اسم **OCTOPUS** روی کامپیوتر ویندوزی (IP `192.168.0.191`، hostname `DESKTOP-KA9RFN5`) اجرا می‌شود. OCTOPUS یک ارگانیسم چندایجنتی است: حافظه دارد، یاد می‌گیرد، خودش را ترمیم می‌کند، و شش «پای» کسب‌وکار دارد. تو روی **برد اورنج‌پای** هستی که چهار تا از این پاها را فیزیکی اجرا می‌کنی:

| پا | کسب‌وکار | وضعیت |
|---|---|---|
| اونلی‌فنز | محتوای اشتراکی | کد روی برد — **نسخهٔ جدیدتر از کپی ویندوز** |
| زیمان | هدیه/تجارت (گالری) | کد روی برد — **نسخهٔ جدیدتر** |
| لیدنقاشی | نقاشی و اخذ لید | کد روی برد — **نسخهٔ جدیدتر** |
| ماینینگ | استخراج کریپتو (ESP32) | کد روی برد — **نسخهٔ جدیدتر** |
| (پروژهٔ شخصی) | — | فقط روی برد |

**نکتهٔ حیاتی:** نسخهٔ کد روی برد از نسخهٔ کپی‌شده در ویندوز **جدیدتر** است — مالک روی برد کار کرده. جهت سینک اول: **برد → ویندوز** (هیچ‌وقت برعکس تا تأییدِ diff).

## ۲. قواعد خانه (نقض = توقف)

```
۱. شواهد نه ادعا — هر عدد را با اجرای کد بگیر
۲. بهبود نه بازنویسی — کد کارکرده را عوض نکن
۳. حذف ممنوع — فقط archive
۴. propose-only — پیشنهاد بده، اجرا نکن مگر مالک گفته
۵. fail-closed — شکست = بستن، نه ادامه
۶. راز: هیچ توکن/کلید/رمز را چاپ نکن، کپی نکن
۷. پول: هیچ اجرای مالی نکن
```

## ۳. قدم صفر — محیط خودت را بشناس

```bash
# این را اجرا کن و خروجی را ثبت کن:
uname -a
python3 --version 2>/dev/null || python --version
git --version
ip addr show | grep "inet " | grep -v 127.0.0.1
ping -c 3 192.168.0.191
```

اگر `ping` شکست خورد: **توقف** — شبکه در دسترس نیست، مالک را خبر کن.

## ۴. سینک Git (مهم‌ترین قدم)

ویندوز یک مخزن git خام (bare repo) دارد: `E:\germline\octopus.git`
پروتکل دسترسی: **SMB** (Windows File Sharing، پورت ۴۴۵ از قبل باز است)

### قدم ۴-۱: mount کردن سهم ویندوز

```bash
# اگر mount point نداری:
sudo mkdir -p /mnt/octopus-germline

# ویندوز پوشهٔ E:\germline را دارد — از admin share استفاده کن:
# (اگر مالک share خاصی ساخته، از آن استفاده کن)
sudo mount -t cifs //192.168.0.191/e\$ /mnt/octopus-germline \
  -o username=<USERNAME>,password=<PASSWORD>,domain=WORKGROUP

# اگر admin share کار نکرد، از مالک بخواه share بسازد:
# روی ویندوز: net share germline=E:\germline /grant:Everyone,FULL
sudo mount -t cifs //192.168.0.191/germline /mnt/octopus-germline \
  -o username=<USERNAME>,password=<PASSWORD>
```

### قدم ۴-۲: snapshot برد را push کن

```bash
# در ریشهٔ پروژه‌های برد (هر جا که کد پاها هستند):
cd /path/to/board/projects

# اگر هنوز git نیست:
git init
git add -A
git commit -m "ofn: board snapshot $(date +%Y-%m-%d) — newer than Windows copies (NBB-V5)"

# push به شاخهٔ جدا (هیچ‌وقت مستقیم روی master):
git remote add germline /mnt/octopus-germline/octopus.git
git push germline master:ofn/board-snapshot-$(date +%Y%m%d)
```

### قدم ۴-۳: تأیید

```bash
# بگو ویندوز بیاورد:
# (این فرمان را در گزارشت بنویس تا مالک/ایجنت ویندوز اجرا کند:
#  cd F:\backup && git fetch germline ofn/board-snapshot-* && git log --oneline germline/ofn/board-snapshot-*)
```

## ۵. Heartbeat — لینک همیشه-برقرار

پس از سینک، یک heartbeat ساده راه بینداز:

```bash
# اسکریپت: /opt/ofn-heartbeat.sh
#!/bin/bash
# OFN heartbeat — هر ۳۰ ثانیه به ویندوز می‌گوید زنده‌ایم
BEAT_FILE="/mnt/octopus-germline/ofn-heartbeat.txt"
while true; do
    echo "$(hostname) $(date -Iseconds) $(uname -r)" >> "$BEAT_FILE"
    # فایل را بزرگ نکن — فقط ۱۰۰ خط آخر:
    tail -100 "$BEAT_FILE" > "$BEAT_FILE.tmp" && mv "$BEAT_FILE.tmp" "$BEAT_FILE"
    sleep 30
done
```

```bash
# فعال‌سازی:
chmod +x /opt/ofn-heartbeat.sh
echo '/opt/ofn-heartbeat.sh &' >> /etc/rc.local  # یا systemd unit بساز
/opt/ofn-heartbeat.sh &  # همین الان شروع کن
```

## ۶. گزارش بده

در پایان، این را در فایل `/opt/ofn-boot-report.md` بنویس و به مالک نشان بده:

```markdown
# OFN-BOOT Report — [تاریخ]

## محیط
- OS: [uname -a]
- Python: [version]
- Git: [version]
- IP برد: [ip]
- دسترسی به ویندوز: [ping ok/fail]

## سینک
- شاخهٔ push شده: [name]
- تعداد فایل: [count]
- حجم: [size]

## Heartbeat
- مسیر: /opt/ofn-heartbeat.sh
- وضعیت: [running/stopped]

## پاها روی برد
- [لیست پوشه‌ها + تعداد فایل .py + آخرین تغییر]

## مشکلات
- [اگر چیزی نشد، صادقانه بنویس]
```

## ۷. مرز — چه نکنی

- هیچ فایلی از ویندوز روی برد copy نکن (برد مقدم است)
- هیچ پروسه‌ای را kill نکن
- هیچ کلید/توکنی را print نکن
- هیچ اجرای مالی انجام نده
- اگر به چیزی دسترسی نداری، **بگو نتوانستی** — حدس نزن

## ۸. بعد از boot

وقتی این نشست تمام شد، ایجنت روی ویندوز شاخهٔ `ofn/board-snapshot-*` را fetch می‌کند، diff را گزارش می‌دهد، و ادغام per-پا با رأی مالک انجام می‌شود. تو بعداً heartbeat را نگه می‌داری و برای هر تغییر جدید دوباره push می‌زنی.

---
*نوشته‌شده توسط ایجنت ویندوز (ZCode/GLM-5.3) — 2026-08-16. هر سؤال داری، از مالک بپرس: آرمین.*
