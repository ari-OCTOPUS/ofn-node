---
type: lane-output · lane: B (Pulse-IMAP/Board Diagnosis) · wave: 2026-09-03-night
order: OWNER-ORDER-THREE-LANES-2026-09-03.md · فقط systemctl status/cat + ss + ps خواندنی؛ NOTHING_RESTARTED=yes
premise-check: تشخیص موحد این لین از قبل موجود بود (PROCESS-DIAGNOSIS-UNIFIED-20260902.md) و پس از مرج #101 دو یونیت خودشان سبز شدند؛ این گزارش وضعیت زندهٔ پس از استقرار است
---

# PULSE_IMAP_DIAGNOSIS

```
MISSING_PROCESSES (سنسور خودمدل) = 5 پورت 8771-8776 → علت رتبهٔ ۱ (شاهد‌دار): expected-port obsolete / نقشهٔ سنسور مال نسل دیگری است؛ سرویس‌های واقعی روی 8791-8796/8895 سالم
IMAP_STATUS = RECOVERED — octopus-imap بعد از رسیدن اسکریپت‌ها (مرج #101 + pull بورد) با تایمر خودش سبز شد؛ در systemd --failed نیست (14:0xZ)
HEARTBEAT_STATUS = فیکس آماده: ریشه = import lazy «outbound_worker» گم‌شده → PR #106 (بلاک‌شده در صف review)؛ تا مرج، یونیت failed می‌ماند — درمان فقط merge، ری‌استارت ممنوع
PORT_LISTENERS = 8791-8794 وب فارسی · 8796 octopus-bridge · 8895 وب‌اپ تلگرام · 20241 محلی · 877x همه connection-refused
ROOT_CAUSE_RANKED = 1) expected-port obsolete (شاهد: هاردکد producer:47-51 + نبود هیچ bind یونیت روی 877x) 2) never-deployed-on-138 (نام‌ها = خانوادهٔ organism میزبان .180) 3) crashed — ردشده برای سرویس‌های زندهٔ 879x
REMEDIATION_OPTIONS_AWAITING_OWNER = (الف) اصلاح نقشهٔ سنسور به 879x (PR کوچک، پیشنهاد اول) (ب) استقرار stack پنج‌عضوی organism روی 138 (ج) retire سنسورها + مستندسازی — همه بدون اجرا تا رأی V2
جدول آشتی نسل‌ها = در PROCESS-DIAGNOSIS-UNIFIED-20260902.md بند «هم‌گرایی دو فرضیه»
NOTHING_RESTARTED = yes (حتی وقتی یونیت failed بود؛ تایمرها خودشان کردند)
خروجی رأی‌خواه این لین: هیچ — گزینه‌های remediation به لین C سپرده شد
```
