# BLACKBOX-REGISTRY — سرشماری جعبه‌های سیاه (2026-09-08, شواهد همین نشست)
قاعده: جعبه را باز نکن؛ لبه‌اش را پیدا کن. مصرف‌کنندهٔ صفر = وزنهٔ مرده (فهرست، نه حذف).

## طرف Airtasker
| جعبه | لبهٔ در دسترس | E | وضعیت |
|---|---|---|---|
| ایمیل هشدار | imap (زنده، تایمر 15min، last_uid پیش‌رونده؛ هنوز 0 ایمیل) | E2 سیم / E0 payload واقعی | منتظر اولین ایمیل مالک |
| صفحهٔ عمومی جستجو | HEAD صادق: root=302؛ URL رجیستری=404 stale | E2 | URL جدید = فقط با مرورگرِ تحتِ نظارت مالک |
| جزئیات تسک/پیشنهاد | هیچ (پشت login) | FOREVER-BLACK | جای انسان؛ ابزارش را ساده کن |
| ضدبات/Cloudflare | رد شده از مسیر پول | — | ثبت و رد |

## طرف اختاپوس
| ساختار | بدنه | خروجی | مصرف‌کننده | فهم | فاصله تا پول |
|---|---|---|---|---|---|
| imap+airtasker intake | 138 | لید+کارت TG+رسید | مالک (TG) | E2 | 1 پل (پیشنهاد دستی) |
| drive-loops | لپ‌تاپ | drive-state.json | drive_queue_consumer + mirror C2 | E2 | 2 (CASH_first_order) |
| C2 mirror→bridge pull | هر دو | commands.sqlite→138 | پل 138 (PULL=1) | E2 کد / E0 E2E تا restart دیمن | 2 |
| wake-spine/audit | 138 | audit 271,642 خط | settle/calibration | E2 تعداد / E0 verify_chain | 3 |
| doctor | هر دو | vitals (لپ‌تاپ ~7h کهنه) | — | E1 | 4 |
| octopus-drill | 138 | restore-drill.log | — (تازه تعمیر شد) | E1 | پشتیبان |
| پورت 20241 / journal perms | 138 | — | — | E0 (مالک ناشناخته بدون root) | — |
| بکاپ germline | لپ‌تاپ→E: | daily rc | — | E1 (لاگ این shell خوانا نبود) | پشتیبان |
| BUDGET.json | لپ‌تاپ | — | صفر (تازه متولد، advisory) | E0 | حفاظ |
| llama/chromium | 138 | — | صفر (غایب) | E0 | فرصتِ باز |

Drift-های گمراه‌کنندهٔ کشف‌شدهٔ امروز (ریسکِ آینده): clone لپ‌تاپ≠138 (CRLF + API bridge) · سورس bridge مفقود (بازیابی شد) · حافظهٔ «llama 8081» غلط · BUDGET.json غایب (ساخته شد) · URL رجیستری airtasker مُرده.
