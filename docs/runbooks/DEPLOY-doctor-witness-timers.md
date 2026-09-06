# DEPLOY — تایمرهای doctor / witness / owner-absence روی board138

شناسه: `DEPLOY-DWT-2026-09-03` · پیش‌نیاز: merge شدن PRهای ۱ و ۳ و ۴ (دکتر،
شاهد، غیبت) و pull روی بورد. همهٔ فرمان‌ها از لپ‌تاپ مالک، تک‌خطی، بدون
گیومهٔ داخلی. هیچ restartی لازم نیست — همه oneshot/timer تازه‌اند.

## ۱) سرویس‌های oneshot + تایمرها (سه‌تایی، با آفست ساعتِ محلی)

```powershell
ssh ari@192.168.0.138 "printf '[Unit]\nDescription=OCTOPUS doctor tick\n[Service]\nType=oneshot\nUser=ari\nWorkingDirectory=/home/ari/ofn/ofn/agents\nExecStart=/usr/bin/python3 /home/ari/ofn/ofn/agents/doctor.py /home/ari/ofn/data/state/doctor/report.json\n' | sudo -n tee /etc/systemd/system/octopus-doctor.service >/dev/null"
```

```powershell
ssh ari@192.168.0.138 "printf '[Unit]\nDescription=OCTOPUS external witness tick\n[Service]\nType=oneshot\nUser=ari\nWorkingDirectory=/home/ari/ofn/ofn/agents\nExecStart=/usr/bin/python3 /home/ari/ofn/ofn/agents/external_witness.py\n' | sudo -n tee /etc/systemd/system/octopus-witness.service >/dev/null"
```

```powershell
ssh ari@192.168.0.138 "printf '[Unit]\nDescription=OCTOPUS owner-absence tick\n[Service]\nType=oneshot\nUser=ari\nWorkingDirectory=/home/ari/ofn/ofn/agents\nExecStart=/usr/bin/python3 /home/ari/ofn/ofn/agents/owner_absence.py\n' | sudo -n tee /etc/systemd/system/octopus-absence.service >/dev/null"
```

تایمرها (ساعتی؛ absence پنج دقیته با آفست تا بعد از doctor برود):

```powershell
ssh ari@192.168.0.138 "printf '[Unit]\nDescription=OCTOPUS autonomy timers\n[Timer]\nOnCalendar=hourly\nPersistent=true\n[Install]\nWantedBy=timers.target\n' | sudo -n tee /etc/systemd/system/octopus-doctor.timer >/dev/null; sudo -n systemctl daemon-reload; sudo -n systemctl enable --now octopus-doctor.timer"
```

(witness و absence هم همین قالب، با `OnCalendar=hourly` و آفستِ دلخواه از
طریق `AccuracySec`؛ در صورت تمایل پنج‌دقیقه‌ای: `OnCalendar=*:0/5` برای
absence.)

## ۲) راستی‌آزمایی (پنج‌دقیقه بعد)

```powershell
ssh ari@192.168.0.138 "systemctl list-timers | grep octopus-; ls -la /home/ari/ofn/data/state/doctor/ /home/ari/ofn/data/state/legs/claims-ledger.jsonl /home/ari/ofn/data/state/OWNER-QUEUE.md"
```

## ۳) بازگشت (rollback)

```powershell
ssh ari@192.168.0.138 "sudo -n systemctl disable --now octopus-doctor.timer octopus-witness.timer octopus-absence.timer; sudo -n rm /etc/systemd/system/octopus-doctor.* /etc/systemd/system/octopus-witness.* /etc/systemd/system/octopus-absence.*; sudo -n systemctl daemon-reload"
```

## یادداشت‌ها
- **هیچ restart سرویس زنده‌ای در این deploy نیست** — قاعدهٔ restart-ممنوع پابرجاست؛ سه oneshot تازه‌اند.
- قلاب conservation خودش با وجود کد فعال می‌شود (فایل حالت نبود = خاموش؛ اولین تیک absence می‌سازدش).
- مهرِ بازگشت مالک: `ssh ari@192.168.0.138 "date -u +%FT%TZ > /home/ari/ofn/data/state/owner-heartbeat.txt"` — تیک بعدی tier را present می‌کند و conservation خاموش.
