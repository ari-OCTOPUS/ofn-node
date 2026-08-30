---
tags: [ofn, status, gates]
aliases: [چک‌پوینت, Checkpoint]
updated: 2026-08-11
---

# CHECKPOINT — دروازهٔ A بسته · دروازهٔ B تقریباً بسته

**پیوندها:** [[INDEX]] · [[HANDOFF]] · [[DECISIONS]] ·
[[docs/operations/REVENUE-STAGES|مراحل درآمد]]

**وضعیت زنده:** همیشه [[HANDOFF]] را بخوان — این فایل تاریخ ۲۰۲۶-۰۸-۰۴ را
حفظ می‌کند؛ گیت‌های موقت و هفتهٔ درآمد آنجا تازه می‌شوند.

**تاریخ این یادداشت تاریخی:** ۲۰۲۶-۰۸-۰۴ · **کد آن روز:** v0.8.0 + پچ پوسته‌ها ·
**کامیت پایه:** 08c47cd

**یادداشت ۲۰۲۶-۰۸-۱۱:** `secret_rotation` و `partner_precondition` تا
۲۰۲۶-۰۸-۱۷ UTC بازند؛ بعد auto-close مگر `OFN_KEEP_GATES_OPEN=1`.
جزئیات: [[docs/architecture/DECISION-open-gates]].

---

## ۱) دو قلم باز فاز ۱ — هر دو از قبل بسته بودند

هر دو در جلسهٔ قبل ساخته شده بودند. این جلسه **تأیید شد**، ساخته نشد.

### الف) `ofn-backup-alert.service`

یونیت وجود دارد: `/etc/systemd/system/ofn-backup-alert.service`

```
Type=oneshot · User=ari
ExecStart=/bin/sh -c 'echo "$(date -Is) ofn-backup FAILED — ..." | tee -a \
          /home/ari/.local/share/ofn/backup-alerts.log'
StandardOutput=journal+console
```

هیچ مسیر خروجی ندارد. نه ایمیل، نه پیام، نه شبکه — فقط یک اثر محلی بادوام
در لاگ و ژورنال. این عمدی است: یک هشدار ۳ بامداد دقیقاً همان چیزی است که
برای مفید بودن باید از گیت خروجی رد شود.

### ب) `PYTHONUNBUFFERED`

در `[Service]` یونیت `ofn` ست است:

```
Environment=PYTHONUNBUFFERED=1
```

---

## ۲) تست شلیک — دو مرحله، هر دو سبز

**مرحله ۱ — خودِ یونیت:**

```
$ sudo systemctl start ofn-backup-alert.service      # rc=0
$ cat ~/.local/share/ofn/backup-alerts.log
2026-08-04T12:33:26+10:00 ofn-backup FAILED — run: python3 -m ofn.backup_job
```

ژورنال هم همان خط را گرفت؛ یونیت با `Deactivated successfully` تمام شد.

**مرحله ۲ — زنجیرهٔ `OnFailure` (تست واقعی):**

لاگ خالی شد، بعد یک یونیت گذرا که تضمیناً شکست می‌خورد ساخته شد:

```
$ sudo systemd-run --unit=ofn-alert-probe \
      --property=OnFailure=ofn-backup-alert.service /bin/false
$ systemctl show ofn-alert-probe -p Result -p ExecMainStatus
Result=exit-code · ExecMainStatus=1
$ cat ~/.local/share/ofn/backup-alerts.log
2026-08-04T12:33:38+10:00 ofn-backup FAILED — run: python3 -m ofn.backup_job
```

یعنی systemd واقعاً روی شکست، این یونیت را شلیک می‌کند — نه فقط وقتی دستی
استارت شود. یونیت پروب با `reset-failed` پاک شد.

و طرف دیگر زنجیر هم وصل است:

```
$ systemctl show ofn-backup.service -p OnFailure
OnFailure=ofn-backup-alert.service
```

---

## ۳) وضعیت تأییدشدهٔ دستگاه در همین لحظه

```
۴۱۴ تست سبز (تاریخی)              (پیام کامیت 08c47cd می‌گوید ۴۰۸ — عدد واقعی ۴۱۴ است)
ofn · ofn-boot · cloudflared     هر سه active
۸۷۹۱ ۸۷۹۲ ۸۷۹۳ ۸۷۹۴             هر چهار ۲۰۰ روی /healthz
ofn-backup.timer                 enabled · بعدی ۲۰۲۶-۰۸-۰۵ ۰۳:۱۸ AEST
آخرین پشتیبان                    ۲۰۲۶-۰۸-۰۴ ۱۲:۱۴ · Result=success · وضعیت ۰
تایم‌زون                          Australia/Sydney (AEST +1000)
uptime                           ۲۹ دقیقه (ریبوت واقعی)
```

---

## ۴) گیت‌های بسته — دست نخورده

```
secret_rotation       — چهار راز CRITICAL هنوز چرخانده نشده‌اند
partner_precondition  — پیش‌شرط انتشار استودیو ثبت نشده
```

هیچ `OCTOPUS_WIRE_*` / `OFN_WIRE_*` روشن نشد. هیچ رازی خوانده یا چاپ نشد.
هیچ چیزی به بیرون نرفت.

---

## ۵) فاز B — تونل

`cloudflared` فعال · enable شده · از ۱۲:۰۴ بالا · رم ۵۳٫۸ MB · پروتکل quic

`ingress` در `/etc/cloudflared/config.yml` دقیقاً هر چهار نگاشت خواسته‌شده را
داشت. **چیزی عوض نشد، restart لازم نشد.**

### هر چهار آدرس از بیرون

```
panel   200 · 39865B · 0.32s
ziman   200 · 26047B · 0.12s
lead    200 · 25161B · 0.12s
studio  200 · 24878B · 0.11s
```

### فارسی — سالم است

هر چهار صفحه:

```
content-type: text/html; charset=utf-8      ← هدر
<meta charset="utf-8">                      ← داخل صفحه
<html lang="fa" dir="rtl">
decode بایت‌ها با utf-8: OK (بدون خطا)
```

عنوان‌ها درست می‌آیند: «ارگانیسم — کنترل پنل آری» · «زیمان — ملیحه» ·
«لید نقاشی — عباس» · «استودیو — سبا». به‌هم‌ریختگی نیست.

### احراز هویت از بیرون هم پابرجاست

این در متن فاز B نبود، ولی مهم‌ترین ریسکِ باز کردن تونل است — تا الان ۴۰۱
فقط روی loopback ثابت شده بود. از بیرون هم گرفته شد:

```
هر چهار میزبان × /api/v1/queue · /api/v1/owner/status · /api/v1/owner/events
  → ۱۲ درخواست، هر ۱۲ تا ۴۰۱

POST /api/v1/decide بدون احراز هویت (مسیر نوشتن)  → ۴۰۱
میزبان نگاشت‌نشده                                  → ۵۳۰ (تونل مسیر نمی‌دهد)
/healthz از بیرون                                  → ۲۰۰ · بدنه فقط {"ok": true}
```

یعنی تونل چیزی را دور نمی‌زند. `healthz` هم نسخه یا وضعیت داخلی لو نمی‌دهد.

### 🚪 دروازهٔ B

```
[x] هر چهار آدرس از بیرون ۲۰۰ با HTML غیرصفر
[x] فارسی درست می‌آید
[ ] آری از گوشی‌اش هر چهار را باز کند و تأیید کند   ← تنها قلم باز
```

---

## ۶) یک یافته — سرسخت نیست، ولی ثبت شود

روی پاسخ‌ها فقط `x-content-type-options: nosniff` هست. این‌ها نیستند:

```
Content-Security-Policy · Referrer-Policy · X-Frame-Options (frame-ancestors)
```

الان که ورود بدون توکن ممکن نیست ریسکش پایین است، ولی وقتی توکن‌های بات پر
شدند و نشست واقعی وجود داشت، نبودِ `frame-ancestors` یعنی پنل مالک را می‌شود
داخل iframe نشاند. اضافه کردنشان کار کوچکی است ولی می‌تواند فراخوان‌های API
پوسته‌ها را بشکند، پس بدون تست نکردم. **اگر بگویی، انجام می‌دهم.**

---

## ۷) دو چیز که باز مانده — تصمیم با آری

1. **`~/MEGAPROMPT-v2.md` روی این دستگاه نیست.** فقط `~/docs/agent-context/prompts/MEGAPROMPT.md`
   (۲۰۲۶-۰۸-۰۴ ۱۰:۴۸) هست که فازهایش A تا E است، نه ۰/۱/۲. یعنی نه بخش ۰
   (گسترش خودمختاری) خوانده شد و نه معلوم است «فاز ۲» کدام است. تا وقتی آن
   فایل نرسد، این جلسه زیر قواعد `~/CLAUDE.md` کار می‌کند.

2. **هیچ دیمن NTP فعال نیست** (`NTP service: inactive`). این برد RTC
   باتری‌دار ندارد. ساعت الان درست است، ولی بعد از قطع برق بی‌صدا خراب
   می‌شود و TLS و OAuth با آن. دستور — خودت اجرا کن:

   ```bash
   sudo timedatectl set-ntp true
   ```
