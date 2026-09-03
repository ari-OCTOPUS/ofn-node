# 03-CONTROL-URL-VERDICT — حکم C2 + C3 (2026-09-03)

## وضعیت زندهٔ octopus-bridge (اندازه‌گیری‌شده از یونیت + فایل env — سازگار)
```text
Unit            = /etc/systemd/system/octopus-bridge.service · active (pid 589802)
WorkingDirectory= /home/ari/octopus-bridge   ← checkout جدا از ~/ofn
ExecStart       = /usr/bin/python3 -m octopus_bridge.run · Restart=always
CONTROL_URL     = https://cp.master-painting.com      (نه 192.168.0.191:8797 — منسوخ)
OUTBOUND_ENABLED= 1
BOARD_CP_PULL   = 1
EnvironmentFile = ~/.config/ofn/octopus-bridge.env (همان مقادیر + API_KEY که چاپ نشد)
Listener        = 127.0.0.1:8796 · /healthz → {"ok":true,"name":"octopus-bridge"}
```
فرمان تکرارپذیر: `ssh ari@192.168.0.138 systemctl cat octopus-bridge --no-pager`

## احکام
1. **پرسش قدیمی «پورت و اسکیم و هاست CONTROL_URL چیست؟ (192.168.0.191:8797؟ تانل؟)» منسوخ است** — CONTROL_URL یک دامنهٔ HTTPS عمومی است (cp.master-painting.com؛ بورد cloudflared با ۵ دامنه دارد) و روی لپ‌تاپ هیچ سرویسی روی 8801/8797 نیست.
2. **سه‌قفل فعلاً بازند** — این با روایت «سه‌قفل خاموش تا G7» ناسازگار است.
3. **telegram_bridge دو موجودیت جدا است** و deploy نشده (فقط فایل در octopus_survival/، بدون unit/پروسه) — هیچ هم‌پوشانی اجرایی با octopus-bridge ندارد.
4. در کد bridge دفاع loopback هست (`config.py:36` — سطوح خود بورد را reject می‌کند) و در connectors وضعیت CONTROL_URL-خالی = disabled دیده می‌شود؛ ولی README و `deploy/bridge.env.example` هنوز می‌گویند CONTROL_URL باید خالی بماند «تا استقرار اختاپوس» — **مستندات کهنه در برابر پیکربندی زنده**.

## ⚠️ آیتم باز حاکمیتی تازه (ثبت در OWNER-QUEUE)
**کدام رأی `OCTOPUS_BRIDGE_OUTBOUND_ENABLED=1` + `CONTROL_URL=cp.master-painting.com` را مجاز کرده است؟** این یک مسیر ارسال بیرونی زندهٔ سوم است (کنار لید-ایمیل و تلگرام→مالک) که در بند تفکیک کانال‌های OWNER-GO-LOCKS (2026-09-03 صبح) **نیست** — جدول کانال‌ها باید ردیف bridge را بگیرد یا bridge قفل شود. اینجا حدس زده نشد؛ فقط ثبت شد.

FILES_I_MERGED=none · اندازه‌گیری 2026-09-03 ~01:05Z
