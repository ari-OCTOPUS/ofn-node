---
type: note
status: active
tags: [octopus, owner-checklist, this-host-only]
created: 2026-09-05
updated: 2026-09-05
lane: U-WHY-NOT-LIVE-20260905
---

# چک‌لیست زنده‌کردنِ واقعی (نه سوکت)

زنده در این قرارداد: **یک حلقه حس → حکم → اثر خارجی** روی **یک هویت بدنی** با **گیت بازِ مالک**.  
کد، تست، MiniApp، harvest، یا beat لپ‌تاپ به‌تنهایی کافی نیست.

فاصلهٔ همین ساعت: لایه‌های ۱–۳ و انتخاب mesh و صف دونه‌دونه **کاغذی تمام** · اثر زنده هنوز نیست (ارسال نرفت؛ Season 5 روی ۱۳۸ `HOLD_EXTERNAL` مانده). مسیر بعد: [[09-LANES/U-WHY-NOT-LIVE-20260905/NEXT-TO-ALIVE]].

## لایه ۱ — ضربان کتابخانهٔ لپ‌تاپ (انجام‌شده، این میزبان)

- [x] این ماشین برد ۱۸۰ نیست (Wi-Fi `192.168.0.191`)
- [x] مرگ حلقه = STOP کالیبر سبک ۴ سپتامبر، نه کرش/ریبوت
- [x] B-safe: STOP آرشیو؛ `127.0.0.1:8771` / `8772` listen؛ `OCTOPUS-flags.cmd` اجرا نشد
- [x] API جلو می‌رود — `LAYER1-VERIFY.json` `pass=true` · `ts=2026-09-05T15:49:31` · `beat=61581` · `started=2026-09-05T15:41:32`
- [x] باگ ts کهنه (نوشتن فقط آخر تیک) رفع شد

این لایه **ارگانیسم زنده نیست**. outbound / ایمیل / تلگرامِ ارگانیسم بسته ماند.

## لایه ۲ — بدن کاننیکال همین ساعت

- [x] localhost 8791–8796 سنجیده شد (`LAYER2-LOCALHOST.json`) — 8792–8796 `not_listen`؛ 8791 = harvest ingest PID 2324
- [x] SSH فقط‌خواندنی `ari@192.168.0.138` — `LAYER2-138-SSH-RECEIPT.json`
- [x] `ofn.service` = active · PID 2986361 · `python3 -m ofn.run` · WD `/home/ari/ofn` · eth0 `192.168.0.138` (هویت جور است)
- [x] 8791–8794 مالِ همان PID `ofn.run`؛ `GET /healthz` روی هر چهار تا `200` و `ok=true` (`LAYER2-COMPLETE.json` · `verify_layer2.py` pass)
- [x] 8796 مالِ `octopus_bridge.run` PID 2986615 است، نه `ofn.run`
- [x] ۱۸۰ از لایهٔ ۲ خارج شد (بدن کاننیکال = ۱۳۸). auth `ari@192.168.0.180` همچنان رد است → لایهٔ ۳

## لایه ۳ — یک هویت + mesh (تا حد این میزبان)

- [x] بدن مشاهده‌شده = ۱۳۸ (`LAYER2-COMPLETE.json` + `LAYER3-RECEIPT.json` `canonical_body=node138`)
- [x] تونل لپ‌تاپ→۱۳۸ loopback: `127.0.0.1:18791-18794,18796` → `138:127.0.0.1:8791-8794,8796` · bind فقط `127.0.0.1` · ssh PID `26364` (`LAYER3-RECEIPT.json` `measured_at=2026-09-05T16:04:02+10:00`)
- [x] `GET /healthz` از همان فورواردها: 8791–8794 و 8796 همه `http=200` `ok=true` (ofn `n=12` · bridge `n=38` · `LAYER3-RECEIPT.json`)
- [x] ۱۸۰ ثبت شد: `ari@192.168.0.180` `Permission denied (publickey,password)` · `ssh_exit=255` · `host_reachable_tcp22=true` · `password_guesses=0` · `root_tried=false`
- [ ] تکلیف اثر زنده روی همان بدن (هنوز گیت بسته است؛ `HOLD_EXTERNAL` باز نشد)
- [x] تکلیف ۱۸۰: مالک گفت **lab** (`Q4-180-ROLE.json` · `2026-09-05T16:19:12+10:00`). Layer 3 همان ساعت `UNDECIDED` مانده (`LAYER3-RECEIPT.json`). Auth ۱۸۰ retry نشد.
- [ ] تونل ۱۳۸→۱۸۰ اندازه‌گیری نشد (auth ۱۸۰ رد است؛ SSH write روی ۱۳۸ ممنوع)
- [ ] `ofn.run` روی 8792–8794 **همین میزبان** همچنان خالی (`this_host_8792_8794_8796` همه `false` · `body_not_on_this_host`)

## لایه ۴ — انتخاب کانال (انجام‌شده) · اثر زنده (عمداً بسته)

بستهٔ انتخاب: [[09-LANES/U-WHY-NOT-LIVE-20260905/LAYER4-PACKET]] · رسید ماشین: `LAYER4-CHANNEL-SELECTION.json` · دست‌به‌دست: [[07-HANDOFF/U-LAYER4-CHANNEL-SELECTION-2026-09-05]] · گیت اثر قبلی (هنوز بسته): [[07-HANDOFF/U-LAYER4-ONE-GATE-2026-09-05]]

مالک انتخاب را تفویض کرد («خودت کانالاشو انتخاب کن»). این لن **پنج پای loopback ساخته‌شده روی ۱۳۸** را نام گذاشت — نه مسیر ارسال خارجی.

- [x] لایه ۴ انتخاب کانال mesh: **DONE** — هر پنج تا: 8791 ziman · 8792 lead · 8793 studio · 8794 owner · 8796 octopus_bridge
- [x] جفت روزمره: **ziman (8791) + bridge (8796)** (`config.py:294` + رسید لایه ۲/۳؛ تناقض پیدا نشد)
- [x] تونل لایه ۳ هنوز بالا بود (ssh PID `26364`)؛ `GET /healthz` این ساعت همه `200`/`ok=true` (`LAYER4-CHANNEL-SELECTION.json` `selected_at=2026-09-05T16:08:32+10:00`)
- [x] تلگرام / OF زنده / تبلیغ پولی به‌عنوان کانال ارسال لایه ۴ **انتخاب نشدند** (کلاس اثر خارجی؛ دیگر از مالک خواسته نمی‌شود بین این سه یکی را برای mesh برگزیند)
- [x] Q1 تلگرام: گیت **ثبت شد** (`Q1-TELEGRAM-GO.json` · `2026-09-05T16:16:37+10:00`) — ارسال نرفت
- [x] Q2 live OF: گیت **ثبت شد** (`Q2-LIVE-OF-GO.json` · `2026-09-05T16:17:28+10:00`) — منتشر نشد
- [x] Q3 paid ads: گیت **ثبت شد** (`Q3-PAID-ADS-GO.json` · `2026-09-05T16:17:58+10:00`) — خرج نشد
- [ ] لایه ۴ اثر زنده: **CLOSED** — ارسال / وایر همچنان بسته؛ Season 5 روی ۱۳۸ بازنویسی نشد (`status: open`)
- [ ] هیچ گیت اثر با GO تاریخ‌دار باز نشد — نه کل `flags.cmd`
- [ ] اولین اثر فقط در لجر ۱۳۸ ثبت شود (اینجا revenue/sent/booking ننویس؛ برندهٔ پیش‌نویس نقاشی اعلام نشد)
- [ ] اگر ادعای قابلیت اندازه‌گیری است: `SIG-IV` دیگر PENDING نباشد
- [ ] Gate B حافظه تا GO علمی جدید CLOSED بماند (`H1_STRONG_FAIL`)

## خط نزن مگر GO جدا

- `auto_email` — بسته (`AGENTS.md`)
- Enable کردن `organism-watchdog` — `RUN-ORGANISM.bat` را روشن می‌کند
- `B-full` / `OCTOPUS-flags.cmd` — ایمیل outbound را مسلح می‌کند
- چسباندن ریاضی N3V2 به runtime — `RUNTIME_ATTACHMENT: NONE`
- harvest را داخل `ofn.run` کردن
- cutover مهاجرت بدون grant
- ادعای `system_wide` بدون دو `node_id`

## حرکت بعدی

پلن اجرا شد تا سقف `AGENTS.md`: `PLAN-EXECUTE-RECEIPT.json` + `PLAN-EXECUTE-CONTINUE.json`. زنده نشد. روی ۱۳۸ `HOLD_EXTERNAL` کلید JSON نیست؛ `telegram_blocked.json` = `TELEGRAM_BLOCKED_CONFIG` / `adapter=fake`. این ایجنت آن فایل را عوض نمی‌کند و ارسال نمی‌کند.
