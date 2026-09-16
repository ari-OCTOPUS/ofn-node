---
type: unified-process-diagnosis
created: 2026-09-02T11:50Z (REV-3 task 3)
mode: READ-ONLY — هیچ restart/kill/bind/systemd change انجام نشد و نمی‌شود بدون رأی جداگانهٔ مالک
host: board138 (ari@DietPi) · repo ~/ofn @ 3cf9fa1
---

# تشخیص یکپارچهٔ پنج پروسهٔ غایب — دو فرضیه کنار هم

## واقعیت مشترک (هر دو گزارش تأییدش می‌کنند)

سنسور خودمدل پنج عضو را با TCP probe می‌سنجد و هر پنج «absent» است:

| سنسور | پورت | نتیجهٔ probe زنده (11:52Z) |
|---|---|---|
| process_organism | 127.0.0.1:8771 | connection refused (http=000) |
| process_cortex | 127.0.0.1:8772 | connection refused |
| process_live | 127.0.0.1:8773 | connection refused |
| process_gateway | 127.0.0.1:8774 | connection refused |
| process_center | 127.0.0.1:8776 | connection refused |

## فرضیهٔ ۱ — انحراف نقشهٔ پورت (877x در برابر 879x)

**متن:** سرویس‌های واقعی بورد سالم‌اند اما روی پورت‌های دیگری گوش می‌دهند؛ فهرست پورت‌های مورد انتظارِ سنسور با استقرار واقعی نمی‌خواند.

**شواهد:**
- فهرست مورد انتظار در کد سنسور هاردکد است: `~/ofn/ofn/adapters/self_model_producer.py` سطرهای ۴۷–۵۱: `organism:8771, cortex:8772, live:8773, gateway:8774, center:8776`. — *فرمان شاهد: `sed -n '45,52p' ~/ofn/ofn/adapters/self_model_producer.py`*
- گوش‌دهنده‌های واقعی و سالم: 8791–8794 (وب فارسی، `/healthz`→`{"ok":true}`)، 8796 (`{"ok":true,"name":"octopus-bridge"}`)، 8895 (hypno-fugu-mini = Telegram Web App، `Environment=HFM_PORT=8895` در یونیت)، 20241 (محلی). — *فرمان شاهد: `ss -tln` و `curl -s -m 3 http://127.0.0.1:PORT/healthz`*
- هیچ سرویس یا کانفیگی در `/etc/systemd`, `~/.config`, یا repo اشاره به 877x ندارد؛ ارجاع به 877x فقط در خود سنسور و خروجی‌هایش دیده می‌شود. — *فرمان شاهد: `grep -rn 8771 /etc/systemd /home/ari/.config 2>/dev/null` (خالی)*
- یونیت‌های فعال روی 138 از جنس octopus-mesh هستند: router, control-router, cycle-settler, supervisor, verify-dispatcher, bridge (+ hypno-fugu-mini). پورت‌ها در فایل یونیت‌ها تعریف نشده‌اند (جز 8895) — binding داخلی کد است. — *فرمان شاهد: `grep -H ExecStart /etc/systemd/system/octopus-*.service`*

**نقطهٔ ضعف شاهد:** نگاشت قطعی «کدام یونیت روی کدام پورت 879x می‌بندد» هنوز پیدا نشده (هیچ ref متنی به 879 در یونیت‌ها/کانفیگ نیست؛ باید از داخل کد mesh یا `/proc/<pid>/net` بیاید). **حکم صادر نمی‌شود تا این حلقه بسته شود.**

**تداخل با فرضیهٔ ۲:** نام‌های مورد انتظار سنسور (organism/cortex/live/gateway/center) دقیقاً خانوادهٔ `ofn.organism.runtime` هستند که روی `octopus-continuity-180` (192.168.0.180، پورت 8090/8780) اجرا می‌شود، نه روی 138. یعنی «انحراف نقشه» احتمالاً «نقشهٔ میزبان/نسل دیگر» است — دو فرضیه در عمل هم‌گرا می‌شوند.

## فرضیهٔ ۲ — mesh نسل قبل + یونیت‌های failed

**متن:** 877x متعلق به معماری/نسل قبلی است که روی 138 هرگز مستقر نبوده (یا بریده شده)؛ جدا از آن، یونیت‌های واقعی این نسل در حال فِیل‌اند.

**شواهد:**
- **سه** یونیت failed (نه دو، اصلاح گزارش اول): `octopus-heartbeat.service` (failed since **11:00:00Z**, exit status=2)، `octopus-imap.service` (failed since **11:30:00Z**, exit=2)، `octopus-quote.service` (failed since **11:30:00Z**, exit=2). هر سه static (timer-driven). — *فرمان شاهد: `systemctl --failed --no-legend` و `systemctl status octopus-heartbeat --no-pager`*
- زمان فِیل‌ها (11:00 و 11:30Z) در پنجرهٔ موج sync/استقرار امشب (10:45–11:37Z) است — هم‌زمانی است، علیت نیست.
- لاگ journal برای کاربر ari خوانا نیست (خروجی خالی) → **علت exit=2 بدون دسترسی root قابل تعیین نیست.** — *فرمان شاهد برای مالک/root: `sudo journalctl -u octopus-heartbeat -n 20 --no-pager`*
- سه یونیت failed از پنج «پروسهٔ غایب» سنسور جدایند: heartbeat/imap/quote از `~/ofn/ofn/agents/` هستند و در فهرست 877x سنسور اصلاً نیستند؛ پس فِیل آن‌ها «غیبت ۵ پروسه» را توضیح نمی‌دهد.

**حکم:** علت exit=2 سه یونیت = **UNKNOWN** (شاهد journal در دسترس نیست). درمان ممنوع تا رأی مالک.

## جمع‌بندی صادقانه (بدون حکم بی‌شاهد)

1. پنج پورت 877x روی 138 واقعاً بسته‌اند و هیچ چیز روی بورد آن‌ها را نمی‌بندد — قطعی.
2. سرویس‌های زندهٔ 138 از نوع octopus-mesh روی 879x/8895 سالم‌اند — قطعی.
3. سنسور خودمدل نقشهٔ 877x را از کد خودش می‌خواند، نه از استقرار — قطعی (سطر ۴۷–۵۱ producer).
4. آیا 877x «نسل قبل» است یا «میزبان دیگر (180)» یا «هرگز مستقر نشده» — **شاهد کافی برای تفکیک نیست؛ حکم معلق.**
5. سه یونیت failed (heartbeat/imap/quote) واقعیت جدا و تازه است (سومین اصلاح گزارش اول که دو تا گفت) — علت UNKNOWN، درمان ممنوع.
6. خودمدل با گزارش absent صادق مانده (fail-closed درست کار می‌کند)؛ status=unverifiable تا رأی مالک دربارهٔ (الف) اصلاح نقشهٔ سنسور یا (ب) استقرار stack پنج‌عضوی، سر جایش می‌ماند.
