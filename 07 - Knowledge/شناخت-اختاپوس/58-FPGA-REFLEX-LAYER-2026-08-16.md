---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: idea
tags: [octopus, hardware, fpga, reflex]
created: 2026-08-16
updated: 2026-08-16
created_by: agent
sources:
  - "[[57-LAPTOP-TO-ARM1-MIGRATION-2026-08-16]]"
  - "[[56-OCTOPUS-V3-FREEDOM-P0-2026-08-16]]"
  - "[[60-THREE-BOARD-AND-FPGA-CORRECTED-2026-08-16]]"
---

# ۵۸ — FPGA لایهٔ رفلکس (۲× Artix-7 200T) — propose-only

ایده تأییدشده، **propose-only**. تا outbound/execution قفل است هیچ سیم و هیچ اتصالی به Arm 3 نیست. نیاز به ADR جدا یا ذیل NBB-V1. خرید قبل از G1 لازم نیست.

بدنه **۴ بازو می‌ماند**. FPGA بازوی جدید نیست.

| قطعه | جایگاه | دلیل |
|---|---|---|
| 200T #1 | کوپروسسور Arm 3 — نه بازو | هویت مستقل ندارد؛ بدون Arm 3 بی‌معناست |
| 200T #2 | معلق — کاندید Arm 5 Deterministic Guard | فقط بعد از گیت‌های ۱–۶ + هویت جدا + مسیر حذف ۳۰ دقیقه‌ای |

## قانون سخت: فقط ترمز، هرگز گاز

FPGA حق دارد: veto، brake، alarm، «این الگو را دیدم» با `taint=true`.

FPGA حق ندارد: آغاز اکشن، بستن رله، کلاس fact.

bitstream وسط کار خواندنی نیست. رله‌های fail-closed ESP32 دست‌نخورده می‌مانند.

## سه اصلاح قبل از خرید

1. **Vitis AI روی Artix-7 کار نمی‌کند.** مسیر درست: Brevitas → FINN. منبع: [Vitis AI 3.5 workflow](https://xilinx.github.io/Vitis-AI/3.5/html/docs/workflow.html) · [UG1414](https://docs.amd.com/r/en-US/ug1414-vitis-ai/Vitis-AI-Compiler) · [FINN](https://xilinx.github.io/finn/).
2. «۸ بیت» را به **few-bit** (۱–۴) عوض کن. 200T نه AI engine دارد نه HBM.
3. AXI لینک برد-به-برد نیست. اتصال فیزیکی به Arm 3: UART / SPI / Ethernet. Artix-7 پردازندهٔ سخت ندارد.

## [UNVERIFIED] — حق تأثیر روی تصمیم ندارند

«تا ۱۰× سریع‌تر از CPU» · «۲–۳× کم‌مصرف‌تر از GPU میان‌رده» · «افت دقت ۰.۲٪» · «سنتز زیر ۲ ساعت».

## آنچه این سیلیکون نیست (پیست Deep Research)

PolarFire PUF / anti-tamper mesh / JTAG zeroize مال Microchip است، نه Artix-7. روی این دو 200T آن ادعاها [CORRECTED] غلط‌اند. جزئیات: نوت [[60-THREE-BOARD-AND-FPGA-CORRECTED-2026-08-16|۶۰]].

PQC و sandbox سیلیکونی استدلال آینده‌اند، دستور خرید این هفته نیستند.

## گیت‌ها

G1 ضبط ≥۱۰۰۰ نمونهٔ واقعی + نرخ پایه. بدون این بقیه بی‌فایده است.

G2 طبقه‌بند کوچک بهتر از baseline قاعده‌محور — اگر یک `if` کافی است، پروژه همین‌جا موفق تمام می‌شود.

G3 کوانتیزه few-bit با Brevitas. افت دقت اندازه‌گیری‌شده.

G4 سنتز FINN روی 200T #1 + سه عدد میز (دقت، p99، توان). هنوز وصل به Arm 3 نه.

G5 UART/SPI به Arm 3 با `taint=true` و provenance. PolicyGate/NBB-CP عوض نشود.

G6 متریک در اسکیمای تلهمتری موجود. جدول موازی = رد.

G7 بررسی 200T #2 — باز هم propose-only تا ADR.

قدم بعدی واقعی: **ضبط داده**، نه خرید.

وابسته به مهاجرت: نوت [[57-LAPTOP-TO-ARM1-MIGRATION-2026-08-16|۵۷]] فاز M5.
