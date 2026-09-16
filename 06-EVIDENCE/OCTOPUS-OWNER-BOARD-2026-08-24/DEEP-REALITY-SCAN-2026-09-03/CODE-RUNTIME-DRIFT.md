# CODE-RUNTIME-DRIFT — 2026-09-03

| # | چه چیزی | کد کجاست | ران‌تایم کجاست | طبقه | شاهد |
|---|---|---|---|---|---|
| D1 | ارگانیسم والت (organism/cortex/live/center/gateway) | `F:\backup\_ops\**` (خارج از مخزن گیت — نسخهٔ قابل‌ردیابی ندارد) | ۵ پروسهٔ python لپ‌تاپ، پورت‌های 8771-8777 | GIT_UNTRACKED_RUNTIME | cmdlineهای نسبی + پورت‌ها 07:22Z |
| D2 | miniapp_gateway | مسیر absolute `F:\backup\_ops\telegram_center\` | pid 19176 | GIT_UNTRACKED_RUNTIME + ORPHAN (پدر 16408 مرده) | watchdog receipts امروز |
| D3 | مغز مخزن | main=6e2bfd50 (repair_api) | 138 روی main=60dce961 | SHA_MISMATCH (deploy lag) | gh + ssh git HEAD |
| D4 | checkout لپ‌تاپ | fix/demand-harvest@34e63a0 dirty=33 («پرمحتواتر») | هیچ سرویسی از آن ران نمی‌شود | STALE_DOC/UNKNOWN نقش | git status |
| D5 | BB-×9 قراردادها | فقط octopus-phase0-A-halt | هیچ | DOC_ONLY (در کپی زنده) | find امروز |
| D6 | mesh «مغز» | مفهوم در سندها | F:\backup\mesh = فایل ۰ بایت | DOC_ONLY | ls -la |
| D7 | restore_drill | مخزن + تست | فقط fixture-run؛ live هرگز | TESTED_NOT_DEPLOYED | سورس+PRIME report |
| D8 | دکتر میراثی | _ops/doctor/doctor.py (1500L) | هر N ضربان لپ‌تاپ | IMPLEMENTED_NOT_WIRED(به ofn/doctor جدید) | سورس + معماری |
| D9 | دکتر جدید | ofn/doctor (merged #86) | CLI؛ فیدر ندارد | IMPLEMENTED_NOT_WIRED | پکیج + census#21 |
| D10 | board_events | قرارداد کامل | transport ندارد | DOCUMENTED_NOT_IMPLEMENTED | docstring (census#28) |
| D11 | NATS | پیکربندی 182 | صفر pub/sub بین‌بردی | WIRED_NOT_CONSUMED | census#42 |
| D12 | telegram_glass | شش فرمان | runner ندارد | IMPLEMENTED_NOT_WIRED | census#26 |
| D13 | ShopifyConnector | کد هست | در run.py ثبت نشده | IMPLEMENTED_NOT_WIRED | census#31 |
| D14 | BrainPort | کد هست | صفر فراخوان | IMPLEMENTED_NOT_WIRED | census#32 |
| D15 | watch-dog production | تسک ویندوزی → اسکریپت غلط (04 - Architect System) | watchdog.py واقعی بی‌ران | PATH_MISMATCH | census#3 |
| D16 | Observatory tasks | دو تسک ساعتی → Desktop حذف‌شده | fail بی‌صدا | PATH_MISMATCH | census#1 |
| D17 | 4d consolidation | تسک OCTOPUS 4d Consolidation Tick | از 08-23 خاموش | RUNTIME_ONLY(متوقف) | census#2 |
| D18 | journal visibility | systemd units | ari بدون گروه adm/systemd-journal | UNKNOWN(دید) | خروجی journalctl امروز |
| D19 | 138 dirty=5 روی deployed main | ~/ofn | تغییرات live کامیت‌نشده | GIT_UNTRACKED_RUNTIME | ssh git status |
| D20 | والتن ریپو F:\backup | برنچ rescue@8d8be71 | dirty=400 | GIT_UNTRACKED_RUNTIME | git status |
