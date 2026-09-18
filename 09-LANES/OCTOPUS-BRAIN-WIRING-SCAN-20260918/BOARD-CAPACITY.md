# BOARD-CAPACITY — ۷ برد (اندازه‌گیری 2026-09-18)

| برد | نقش | load (1/5/15m) | هسته | دیسک آزاد | سرویس running | خوانش | توصیه |
|---|---|---|---|---|---|---|---|
| 138 | Revenue Engine | 1.0–1.5 (heartbeat pulses) | 8 | - | 45+ units, 25 timers | busiest of the fleet; runs the revenue loop | no spare for heavy batch |
| 182 | Remote Witness & Audit Latch | 1.68 / 1.47 / 1.45 | 8 | 31G free | 27 services running | very busy; witness duty + audit latch | keep as witness, avoid adding |
| 180 | Fleet Telemetry & Observatory | 1.26 / 0.53 / 0.28 | 8 | 43G free | 24 services | moderate; telemetry + llama-lab history | can take light batch |
| 114 | Hardware Discovery | 0.39 / 0.19 / 0.22 | 8 | 54G free | 14 services | light; evaluator staged-not-installed (F-003) | install unit → +1 compute lane |
| 160 | Shadow Verification & Watchdog | 0.34 / 0.24 / 0.15 | 8 | 53G free | 14 services | light; ingestion staged-not-installed (F-003) | install unit → +1 ingest lane |
| 193 | Hypothesis & Market Research | 0.47 / 0.20 / 0.12 | 8 | 54G free | 15 services | light; research role under-used | best candidate for model/research work |
| 100 | Coding Worker & Sandbox | 0.02 / 0.05 / 0.08 | 8 | 48G free | 16 services | essentially IDLE (load 0.02) | the fleet's spare capacity — use first |

**جمع‌بندی:** ظرفیت خالی واقعی در ۱۰۰ (بار ۰.۰۲) و سپس ۱۱۴/۱۶۰/۱۹۳ است؛ ۱۳۸ و ۱۸۲ سرِ ظرفیت‌اند و ۱۸۰ متوسط. پس مشکل «کمبود برد» نیست — **توزیع کار** است: ۱۳۸ هم revenue loop دارد هم batch.
> یادداشت: ۱۳۸ در این حلقه با کلید پیش‌فرض probe نشد (alias جدا)؛ بار آن از پالس‌های heartbeat گرفته شده.
