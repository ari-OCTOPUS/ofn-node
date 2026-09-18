# TERRITORY-REPORT — T10-infra-fleet (زیرساخت فلیت)

`checked: 25 hypotheses · sources: 26 file/probe families · refuted: 3 · confirmed: 7 · partial: 4 · unverified: 11 · owner-needed: 5 · verified-this-session: 1`

## چرا این قلمرو مشکوک بود

> نجات‌های سخت‌افزاری ساعت خورده

## یافته‌های تأییدشدهٔ برتر

- **W-201** (I3×F2) — restore_drill هرگز اجرا نشده — بزرگ‌ترین ریسک پنهان به تعبیر رجیستر خودِ GOV-V8
  - دلیل: F-006: restore_drill NOT_RUN — unexecuted in three ruling docs
  - شاهد: 06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/GOV-V8 (F-006)
  - مخرج: یک drill بازیابی واقعی روی یک نود غیرحیاتی (۱۸۰) — نیم‌روز
- **W-203** (I3×F2) — ۱۳۸ هیچ بک‌اند snapshot ندارد (ext4 روی eMMC تک‌نقطه) — بازیابی فقط دستی است
  - دلیل: DC-03E0: NO snapshot backend exists (ext4 on one eMMC; btrfs/LVM/ZFS absent)
  - شاهد: 09-LANES (DC-03E0)
  - مخرج: قبل از هر تغییر بزرگ، export دلتا + pre-image (رویهٔ موجود) را اجباری کن
- **W-209** (I2×F3) — نود درآمد (۱۳۸) با load ۱.۰-۱.۵ مداوم کار می‌کند — سرِ ظرفیت، هر کار سنگین ریسک تأخیر دارد
  - دلیل: heartbeat pulses: 138 load1=1.19/1.2/1.1/0.98 در دقیقه‌های متوالی
  - شاهد: 06-EVIDENCE/FLEET-HEARTBEAT-CANONICAL.md
  - مخرج: کارهای سنگین را به نودهای بیکار (۱۷/۲۵/۱۸۰) منتقل کن
- **W-211** (I3×F2) — بازیابی کلاس B هرگز در production اجرا نشده — مسیر rollback در لحظهٔ واقعی آزموده نیست
  - دلیل: F-022: Class B recovery armed but never executed in production (G2)
  - شاهد: 06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md (F-022)
  - مخرج: یک drill کلاس B روی نود کم‌ریسک با پیش‌تصویر
- **W-214** (I2×F3) — تایمر heartbeat تا امروز هرگز اجرا نشده بود (LAST=-) — تازه نصب شده
  - دلیل: systemctl list-timers: octopus-heartbeat.timer LAST=-
  - شاهد: 138: systemctl list-timers
  - مخرج: اولین اجرا را تأیید کن و خروجی را در شاهد وال ببین
- **W-S14** (I3×F2) — آرشیو ۳۶.۴ گیگابایتی روی S: آفلاین است و ۲۶۶ هزار فایل در دسترس نیست
  - دلیل: disk crisis: S: went offline mid-op; deletions stopped
  - شاهد: 06-EVIDENCE, 99-ARCHIVE state (F-047)
  - مخرج: یک هدف آرشیو دوم (USB/دیسک محلی) وصل کن یا آرشیو را رسمی معلق اعلام کن

## سایر ورودی‌ها (خلاصه)

- W-S13 [PARTIAL] نجات زیرساخت (OOM/EROFS/SD/برق) ساعت‌های جلسه را بلعیده و کار درآمدی را عقب انداخته
- W-202 [UNVERIFIED] بررسی وضعیت دیسک (smartmontools) روی ۱۳۸ FAILED است — نودی که بحران دیسک را دیده بی‌پایش است
- W-210 [PARTIAL] آینهٔ وضعیت پول (mirror 138→182) با کهنگی ~۹.۳ ساعت گزارش می‌شود
- W-213 [UNVERIFIED] ارزیاب ۱۱۴ و ingestion ۱۶۰ با nohup اجرا می‌شوند و units آن‌ها نصب نشده — ریسک reboot
- W-218 [UNVERIFIED] پرچم GITWRITE-FAILED در مسیر push ساعتی هرگز پاک نشد؛ push خودکار سبز نیست
- W-219 [PARTIAL] مصرف‌کنندهٔ JetStream در ۰۹-۱۵ صفر بود (durability بدون مشتری) — الان vault-pulse وجود دارد ولی تاریخچهٔ سکوت جدی است
- W-204 [UNVERIFIED] ۴ برد هنوز بی‌استفاده‌اند و auth نودهای ۱۰۰/۱۶۰/۱۹۳/۱۱۴ معلق است
- W-205 [UNVERIFIED] احراز هویت مش نودها (node_id) روی ۴ کارگر PENDING_AUTH است
- W-206 [UNVERIFIED] NPU (ظرفیت محاسباتی رایگان نودها) صفر مصرف دارد
- W-212 [UNVERIFIED] طرح rollback مهار (sandbox escape/fire drill) هرگز تمرین نشده
- W-221 [PARTIAL] قواعد شکنندهٔ سخت‌افزاری (شروع نکردن مجدد برق، کارت ۳۲GB قبل از reboot) ریسک عملیاتی دائمی می‌سازند
- W-208 [UNVERIFIED] سرویس‌های unwired (effect-zero claim paths + http.server اعلام‌نشده) از ۰۸-۱۶ active مانده‌اند
- W-207 [UNVERIFIED] تونل‌ها/مسیرهای دسترسی خارجی غایب یا کهنه‌اند و hold_external فعال است
- W-216 [UNVERIFIED] کارت ۱۲۸GB روی ۱۸۲ در سه تلاش شناسایی نشد — کارت یا اسلات بدون تعیین‌تکلیف
- W-217 [UNVERIFIED] استراتژی MAC/DHCP برای تغییر رسانه (T4) طراحی/اثبات نشده
