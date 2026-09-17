# LANE-REPORT — FLEET-NATS-7NODE-20260917
GOV_VERSION=V8 · LADDER=L2 · lane opened under owner fleet tokens (FLEET-PHASE0..5-PILLARS)

## چه شد
1. **Spec** (Tier1): `fleet-spec-7node/FLEET-HYBRID-TOPOLOGY.md` — ماتریس ۷ نود + NATS-Leaf هاب-لپ‌تاپ + secret-manifest اسکوپ‌شده (صفر توکن سراسری؛ فقط نام‌ها).
2. **Phase-0**: nats-hub لوکال — کلیدهای nkey (رجیستری هویت) + TLS + conf؛ کشف schema: leaf-users فقط user/pass ⇒ پسوردهای تصادفی per-leaf (URL-userinfo روی TLS).
3. **Phases 1-4**: deploy اثبات‌شده با cat-pipe (سفت‌سرور مستقل `nats-leaf-server` + unit سخت‌شده، پورت ۴۲۲۳): 114 → 180 → 193 → 182 (نمونهٔ دوم مستقل در کنار Sensorium موجود!) → 100/160 (کلید piggybank مالک). **۷/۷ متصل** (138 توسط مالک/موازی deploy شد — خارج از رسیدهای این lane، گزارش شد).
4. **JetStream** `OCTOPUS_EVENTS` (octopus.>، file، 2GiB) + اثبات ماندگاری با پاکت‌های تست.
5. **Time-sync**: SNTP تک‌شات دقیق → هر ۶ نود ±۳ms UTC (کشف: خطای اصلی سمت ساعت لپ‌تاپ بود).
6. **Telemetry خودکار**: تایمر 60s روی ۶ نود + پیلود کامل (uptime/mem/load/leaf-TCP-probe) — سه باگ cosmetic حین کار فیکس شد.
7. **5-PILLARS**: هاب دائمی (HKCU Run + launcher idempotent) · مصرف‌کنندهٔ Obsidian `durable=vault-pulse` → `06-EVIDENCE/FLEET-HEARTBEAT-CANONICAL.md` (ماتریس زندهٔ ۷ نود) · سختی‌کاری 640 مربوط به 138 · ۵/۵ پروب استعدادیابی · پشتیبان air-gap برای leads_master (sha256-locked).

## چه ماند
Phase-1.5 (تفکیک permissions هر leaf با accounts) · ثبت hub به‌عنوان سرویس ویندوزی واقعی (نیازمند admin) · ناشر telemetry مربوط به 138 (deploy بیرونی) نیازمند تبیین مالک · w32tm/resync لپ‌تاپ (اختیاری).

## چه شکست
160/100 در فازهای اول: دیوار اعتبار (حل با کلید piggybank مالک) · sftp غایب روی 114 (حل با cat-pipe) · سه باگ cosmetic پیلود (حل) · باینری مسیر نسبی یک‌بار (حل با absolute — درس ثبت شد).

## شواهد
`F:/recon-clones-20260917/nats-hub/RECEIPT-{PHASE1,PHASE2,PHASE3,PHASE4,FLEET-COMPLETE,TELEMETRY-TIMESYNC,5-PILLARS}.md` + `keys/PUBLIC-KEYS.md` + لاگ‌ها/پاکت‌ها در همان پوشه.

## rollback
هر نود: `systemctl disable --now nats-leaf && rm /usr/local/bin/nats-leaf-server /etc/nats-leaf -r`؛ هاب: حذف Run-key + kill پروسه؛ مصرف‌کننده: kill پروسه (فایل canonical افزاینده می‌ماند).
