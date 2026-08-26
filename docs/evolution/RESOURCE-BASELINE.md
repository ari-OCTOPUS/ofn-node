# RESOURCE-BASELINE — BOARD 180

scope: this_host_only | vantage: local | generated: 2026-08-26 anatomy pass

| resource | value | threshold (V2 §12) | trend | verdict |
|---|---|---|---|---|
| CPU load (1m) | 0.32 | — | idle | OK |
| RAM available | ~2.1Gi / 3.8Gi | — | steady | OK |
| swap used | ~2Mi / 4Gi | — | negligible | OK |
| disk / | 89% (49G/58G, 6.2G free) | 80% → limited ingest + safe archive | high | **WARN: over 80%** |
| inodes / | 3% used | — | low | OK |
| soc temp | 27.8C | — | cool | OK |
| failed units | 0 | — | — | OK |
| organism events | 1394 and growing | — | +~170 since first scan | ALIVE |
| uptime | 1d 6h | — | — | OK |

## اقدام پیشنهادی (GREEN، بدون اثر خارجی)
- disk 89% از آستانهٔ 80% سند V2 گذشته است. طبق §12: ingest محدود و archive امن (نه حذف). این یک proposal است؛ اجرای پاک‌سازی/archive نیازمند بررسی مالک/۱۳۸ است چون ممکن است شامل evidence باشد.
- کاندیدای بررسی حجم (فقط مشاهده، بدون حذف): llama.cpp-src، models، validation_campaign_*، llama.cpp build artifacts. تصمیم حذف/archive خارج از اختیار 180 است.
