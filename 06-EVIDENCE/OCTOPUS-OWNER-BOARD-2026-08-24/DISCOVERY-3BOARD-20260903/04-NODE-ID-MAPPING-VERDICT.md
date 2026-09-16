# 04-NODE-ID-MAPPING-VERDICT — حکم C4 (2026-09-03)

## ماتریس نگاشت (هویت ↔ میزبان)
| هویت/میزبان | نگاشت | سطح شاهد |
|---|---|---|
| `board-138` ↔ `BUSINESS` | **اثبات‌شده** | LIVE: ofn.run + ۴ پورت کسب‌وکار + یونیت‌های octopus-* + رکوردهای ارسال لید |
| `192.168.0.191` (DESKTOP-KA9RFN5) ↔ `LAPTOP` | **اثبات‌شده** | VANTAGE-PROOF: ipconfig + SourceAddress؛ ولی بدون سرویس 8801 — نقش «کنترل‌کننده» فقط به معنای والت+اجراایجنت‌ها، نه endpoint زنده |
| `board-182` ↔ `SENSORIUM` | **فرضیه (استنتاج حذفی)** | NODE_IDS سه‌تایی است؛ دو گزینهٔ دیگر رفته‌اند → SENSORIUM به 182 می‌رسد. بدون شاهد runtime (داخل 182 UNPROBED). ارتقا ممنوع تا probe داخلی |
| `board-180` ↔ ??? | **unmapped — واقعی** | 180 در NODE_IDS نیست؛ فرضیهٔ قدیمی «continuity/brain» هیچ شاهدی ندارد. سخت‌افزار همان بچ (MAC OUI واحد)، sshd publickey+password، احراز رد |

## قراردادها (FILE_VERIFIED، از main)
- `telegram_glass.py:71`: `NODE_IDS = ("BUSINESS","SENSORIUM","LAPTOP")` — فقط ۳ هویت.
- `board_events.py:30+557`: `BOARDS = frozenset(("board-138","board-180","board-182"))` + CHECKconstraint — ۱۸۰/۱۸۲ در قرارداد رویداد **رزرو** شده‌اند ولی هیچ رویدادی از آن‌ها دیده نشده.

## نتیجه برای طراحی
نگاشت هویت ناقص است: ۴ میزبان فیزیکی در برابر ۳ هویت منطقی + یک برد رزروشدهٔ بی‌هویت. هر طراحی transport/رویداد سه‌بردی تا تعیین تکلیف 180 (و احراز 182) باید 180 را «unmapped» فرض کند، نه Sensorium و نه Continuity.

FILES_I_MERGED=none · 2026-09-03
