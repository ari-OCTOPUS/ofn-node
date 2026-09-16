---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, migration, boards, fpga]
created: 2026-08-16
updated: 2026-08-16
created_by: agent
sources:
  - "[[../../06-EVIDENCE/LIVE-VS-PASTE-SCAN-2026-08-16]]"
  - "[[57-LAPTOP-TO-ARM1-MIGRATION-2026-08-16]]"
  - "[[58-FPGA-REFLEX-LAYER-2026-08-16]]"
  - "[[56-OCTOPUS-V3-FREEDOM-P0-2026-08-16]]"
---

# ۶۰ — سه برد فیزیکی + FPGA: پیست را SoT نگیر

پیست شورا + Gemini P0 + Deep Research FPGA + «اسکن مرورگر» + پلن ۳ برد را روی **همین** `F:\backup` گذاشتم. معماری موازی نساز. نوت ۵۶–۵۹ باطل نشده‌اند.

## آزادی (اجماع، قبلاً کد شد)

آزادترین = حاکمیت: لایسنس وزن Apache/MIT · زیرساخت خودت · تو نویسندهٔ policy · داده اینجا می‌ماند. Abliteration مغز را خراب می‌کند. Qwen3.8-Max لایسنس اختصاصی است. سقف زنده AU$۲/روز نه ۳۰۰. P0 overlay unarmed است. جزئیات: نوت ۵۶.

## سه برد — نگاشت به رودمپ موجود (نوت ۵۷)

موجودی که گفتی: **۱ برد پاهای بیزنسی روشن + ۲ برد خالی**. لپ‌تاپ قلب می‌ماند تا M3. FPGA بازو نیست.

| قطعه فیزیکی | نقش در نوت ۵۷ | چه می‌آید | چه نمی‌آید |
|---|---|---|---|
| برد آماده (legs روشن) | **M4 — Legs Runner** | همان پاها، بعداً کلاینت `octopus.command.legs` | beat · بودجه · `ORGANISM-STATE` نویسنده · کلید مغز · killswitch |
| برد خالی ۱ | **M1 — Arm 2 شاهد لجر** | append-only events/head-hash · UID جدا · بدون اینترنت | `killswitch.py` · approvals نوشتنی · `.env` مغز |
| برد خالی ۲ | **M2 سپس M3 — Arm 1** | اول سایه ۷۲ساعت (صفر beat) · بعد lease | تا سایه سبز نشده هیچ execute |
| لپ‌تاپ | SoT + beat + مغز + dev تا cutover | fencing lease مالک | بعد از M3: کلاینت |
| ۲× Artix-7 200T | **M5 کوپروسسور Arm 3** نه لایه صفر | بعد از G1 داده؛ ترمز نه گاز | PolarFire RoT · LLM · بستن رله |

پیست «خالی۱ = آینهٔ control_plane / خالی۲ = شاهد state / آماده = legs» **نیمه‌درست** است. پاها روی برد آماده بمانند. آینهٔ `control_plane/` و کپی `killswitch.py` حتی فقط‌خواندنی را نکن — شاهد یعنی لجر، نه موتور سیاست دوم.

ترتیب امن (همه با هم نه):

1. M0 اسکن Windows روی لپ‌تاپ (هنوز کامل نیست).
2. خالی۱ = شاهد لجر. یک بایت دستی ⇒ verify بشکند.
3. خالی۲ = سایه. ۷۲ساعت اختلاف <۱٪ و **صفر beat**.
4. lease به خالی۲. لپ‌تاپ ۲۴ساعت بسته. مسیر برگشت باید یک‌بار قبلاً اجرا شده باشد.
5. پاها کلاینت می‌شوند. آزمون: Arm 1 خاموش ⇒ اکشن نو از legs نه.

هرگز سه actor با `killswitch` یا beat موازی.

## FPGA — Deep Research را روی Artix-7 نگذار

PolarFire (Microchip) PUF، anti-tamper mesh، JTAG monitor، zeroize دارد. **Artix-7 این‌ها را ندارد.** Artix-7: AES-256 bitstream + HMAC احراز ([UG908](https://docs.amd.com/r/2023.1-English/ug908-vivado-programming-debugging/Generating-Encrypted-and-Authenticated-Files-for-7-Series-Devices)). همان رمز 7-series شکسته شده ([USENIX SEC'20](https://www.usenix.org/system/files/sec20fall_ender_prepub.pdf)) — پس «قلعهٔ سخت‌افزاری تا ۲۰۳۰» روی این دو برد ادعا نیست. Vitis AI روی 7-series کار نمی‌کند (نوت ۵۸).

| ایدهٔ پیست | روی این دو 200T | تگ |
|---|---|---|
| Hardware RoT / PUF / zeroize قبل از بوت | خانوادهٔ غلط | [CORRECTED] |
| Kill-switch مستقل از OS در fabric | ممکن به‌عنوان **ترمز** بعد از M5؛ رلهٔ ESP32 را دور نزن | propose-only |
| شتاب SHA برای لجر | ممکن؛ کلید خام روی لپ‌تاپ نماند | propose-only |
| PQC (Kyber/Dilithium) crypto-agility | استدلال FPGA عمومی درست است؛ این سیلیکون + این هفته نه | [SPEC] آینده |
| Sandbox سیلیکونی Arm 4 | دیوار باس سفارشی = پروژهٔ HDL بعد از M6 | ایده |
| AI-FPGA Agent ۱۰× سریع‌تر / ۰.۲٪ افت دقت | همان ادعاهای [UNVERIFIED] نوت ۵۸ | رد برای تصمیم |
| لایه صفر زیر همهٔ Armها همین هفته | مهاجرت را می‌کشد؛ HDL جدا از beat است | رد |

معجزهٔ واقعی این دو برد برای اختاپوس تا ۲۰۳۰: **ترمز دترمینیستیک + در آینده crypto-agile**، نه مغز دوم و نه PolarFire قلابی.

## آنچه عمداً انجام نشد

rsync/scp به برد · کپی killswitch · روشن کردن `OCTOPUS_BEAT_LEASE` · لود ۲۷بی · pip vaara · خرید/سنتز FPGA · overwrite رودمپ ۵۷.

شواهد زنده: [[../../06-EVIDENCE/LIVE-VS-PASTE-SCAN-2026-08-16|LIVE-VS-PASTE]] · قفل ناوبری: [[61-OBSIDIAN-NIGHT-LOCK-2026-08-16|۶۱]]
