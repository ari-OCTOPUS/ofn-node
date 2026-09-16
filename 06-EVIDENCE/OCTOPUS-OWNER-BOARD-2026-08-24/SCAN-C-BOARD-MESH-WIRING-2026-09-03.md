# SCAN C — سیم‌کشی حافظهٔ برد‌ها و مش — گزارش کامل کاوشگر
شناسه: `SCAN-C-BOARD-MESH-WIRING-2026-09-03` · read-only · 138 (ari) + 180 (root) + 182 (root) · ~06:00-06:12Z

## تصویر یک‌خطی
**هر سه برد لوکال‌شان زنده و سالم است؛ تقریباً هیچ چیز بینشان حرکت نمی‌کند.** مشِ سه‌بردی در عمل یک تکنیک صف-پوشه‌ای است که فرستنده‌هایش مرده‌اند و درین‌هایشان وصل نیست.

## یافته‌ها (۱۱)
1. [H] **outbox شاهد ۱۸۲ dead-end**: `/root/octopus-mesh/outbox` = ۲٬۳۳۰ فایل `witness_response_*.json` (تازه‌ترین 06:03، یکی هر ~۱۵-۳۰ دقیقه از octopus_witness_worker.py). صفر `*.state.json` = **هیچ تلاش ارسالی هرگز**. هیچ unitی روی ۱۸۲ octomesh_send/process را اجرا نمی‌کند.
2. [H] **پای ۱۳۸→۱۸۲ از ۱ سپتامبر ۱۴:۰۶ مرده**: inbox ۱۸۲ = ۱۰٬۴۲۶ ping (روزی ~۱,۴۴۰ = دقیقه‌ای یکی؛ ۹/۱ در 14:06 قطع). worker شاهد (۵دقیقه‌ای) انتخابی درین می‌کند: processed=۲,۳۴۵ در برابر ۱۰٬۴۲۶ — همهٔ pingها expired (TTL ۶۰ث).
3. [H] **outbox ۱۳۸**: ۱۱ گیر — دوتای state.json «retryable» از ۲۸-۰۸ (خطای timeout به 182:22) و ۲۶-۰۸ به **203.0.113.1:22** (IP TEST-NET = همتای اشتباه در config) + سه wake-180 بی-state (هرگز تلاش‌نشده). `octomesh_process.py` هیچ unit/کرونی ندارد → هیچ‌وقت retry نمی‌شود.
4. [H] **inbox ۱۳۸**: ۵ پیام از ۲۶-۰۸ هضم‌نشده؛ هیچ پروسه‌ای inbox نمی‌خواند (پنج دیمن مش فقط processed را می‌خوانند — verify_dispatcher.py:50).
5. [H] **NATS تک‌کلاینت**: تنها اتصال = loopback خودِ sensorium (127.0.0.1↔4222). بقیهٔ استک ۱۸۲ file-wired است (stability_monitor:4 صراحتاً «does not subscribe to NATS»؛ fusiond/reflex/metacontrol/world-model فقط JSON file). روی ۱۳۸ و ۱۸۰: صفر ارجاع کد به 4222.
6. [H] **outbox ۱۸۰**: ۲۸ بی‌ارسال (از ۲۶-۰۸ تا ۱-۰۹؛ شامل partner-brief و megaprompt-build)؛ octopus-drain (۵دقیقه‌ای) فقط فایل‌های state-دارِ retryable را می‌گیرد → journal همیشه `{"ok":true,"retried":0}`. پیام‌های ۱۸۰ فقط با مُردن به rejected/ رسیده‌اند.
7. [M] **آینهٔ ۱۸۰ از لپ‌تاپ fail**: octopus-mirror.service هر ۱۵دقیقه rsync از 192.168.0.191 → rc=255 «CIFS credentials not configured» «no transport available». هیچ push به ۱۳۸ هم نیست.
8. [M] **ارجاع متقابل صفر**: هیچ کدی روی ۱۳۸ 180:8090/8081 را صدا نمی‌زند (فقط نثر بریف مهندس)؛ ۸۷۹x پای‌ها loopback-اند و بی‌مصرفِ بیرونی؛ ۱۸۲ فقط probe-level (crossnode_probe: 138:22 و .191:445/8801).
9. [M] **سبزِ دروغین اسکژولر ۱۳۸**: timer ۱۵دقیقه‌ای Result=success ولی تنها transportش octomesh_send (scheduler:550) از ۲۷-۰۸ هیچ نفرستاده.
10. [M] **چهار عیب ۱۸۲**: miniscientist-daily از ۰۲-۰۹ failed؛ world-model در stop هنگ می‌کند (stop-sigterm معلق)؛ sensorium pid اصلی D-state با ۵۲٪ RAM؛ `state/witness/events.jsonl` ۲۹MB بی‌هرس (پرون فقط snapshots را می‌گیرد).
11. [L] **ساعت‌ها**: ۱۸۰ chrony قفل (خطا ۰.۰۸ms)؛ ۱۳۸ NTP خاموش (+۰.۴-۰.۶ث جلو — با TTL ۶۰ث، ریسک آرام envelope-expire)؛ ۱۸۲ timedatectl dbus-خراب (وضعیت ناشناخته، الان ~۰.۲ث).

## آنچه وصل و زنده است (کنتراست)
- ۱۳۸: پایپ‌لاین داخلی زنده — processed=۲۸,۵۱۲ + receipts=۶,۹۸۰ (تازه‌ترین 06:03)، پنج دیمن، بریج board_cp فعال.
- ۱۸۲: باس فایلی محلی زنده (sensorium→evidence files→fusiond/reflex/...)؛ verdictها در state/witness/verdicts.jsonl (06:03) — تنها مصرف‌کنندهٔ آن، بستهٔ handoff لپ‌تاپ است («evidence files, not NATS»).
- ۱۸۰: حلقه‌های محلی زنده (drain ۵دقیقه‌ای، cognitive-worker ۴۵ثانیه‌ای، heartbeat 06:05، gateway/llama/organism بالا) — همه محلی، هیچ خروجی.

## شمارش صف‌ها (کوانتایز)
138: inbox 5 · outbox 11 · processing 0 · quarantine 11 · processed 28,512 · receipts 6,980 · snapshots 3 (کهنه)
182: inbox 10,426 (همه expired) · outbox 2,330 · processed 2,345 · witness/events.jsonl 29MB
180: outbox 28 · cognition 11,969 فایل · replies 9,331 · organism.db 221MB (WAL فعال)
