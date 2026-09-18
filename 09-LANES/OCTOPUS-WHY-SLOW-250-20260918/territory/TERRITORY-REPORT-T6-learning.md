# TERRITORY-REPORT — T6-learning (یادگیری)

`checked: 15 hypotheses · sources: 11 file/probe families · refuted: 0 · confirmed: 6 · partial: 4 · unverified: 5 · owner-needed: 0 · verified-this-session: 9`

## چرا این قلمرو مشکوک بود

> ادعای یادگیری falsify شد؛ کلید تکراری متناقض

## یافته‌های تأییدشدهٔ برتر

- **W-133** (I4×F3) — پایگاه اثر خروجی (outbound-effects) صفر بایت است — هیچ outcome از ارسال‌ها به یادگیری نمی‌رسد
  - دلیل: outbound-effects.sqlite3 = 0 bytes (mtime 09-16T22:53)
  - شاهد: 138:state/revenue-drive/outbound-effects.sqlite3
  - مخرج: ارسال/پاسخ/سکوت را به‌عنوان سه outcome واقعی در همان DB بنویس
- **W-134** (I4×F3) — هیچ سیم‌کشی از پاسخ مشتری به ردیف یادگیری وجود ندارد؛ حلقهٔ بازار→یادگیری بسته نیست
  - دلیل: هیچ فایل feedback→learning در قیف؛ learningfeeder فقط روی منابع عمومی کار می‌کند
  - شاهد: 138:state/revenue-drive (ls), octopus-learningfeeder.timer
  - مخرج: پاسخ مشتری = outcome با decision_key؛ به outcomes.db تزریق کن
- **W-132** (I3×F3) — تنها کلید چندردیفی، متناقض است (هم accept هم reject روی یک پیشنهاد) — حافظه روی آن اجباراً برای یک ردیف غلط می‌شود
  - دلیل: mixed_polarity_key: 646d80a894ad3e8f (accept+reject on same proposal)
  - شاهد: 09-LANES/OCTOPUS-SELF-TEST-TRAIN-20260918/evidence/CYCLE-STTL-001.json
  - مخرج: کلید متناقض را با تفکیک context (زمان/نسخه) به دو کلید بشکن + قاعدهٔ polarity consistency
- **W-141** (I3×F3) — فایل حافظهٔ ایجنت‌ها از سقف خودش بزرگ‌تر است (۵۴.۸KB در برابر سقف ۲۴.۴KB) — حافظه بریده می‌شود
  - دلیل: هشدار سیستم: MEMORY.md 54.8KB > 24.4KB limit — only part loaded
  - شاهد: env: C:/Users/Armin/.zcode/.../memory/MEMORY.md
  - مخرج: نمایه را به یک خط <۲۰۰ کاراکتر خلاصه کن و جزئیات را به فایل‌های موضوعی ببر
- **W-143** (I3×F3) — حکم یادگیری در دو چرخه هیچ تغییری نکرده (delta 0/0/0) — گرادیان صفر
  - دلیل: LOO delta_vs_prev: changed 0, on 0, off 0
  - شاهد: 09-LANES/OCTOPUS-SELF-TEST-TRAIN-20260918/evidence/LOO-cycle1.json
  - مخرج: معیار موفقیت چرخه = رشد n کلیدهای تکراری غیرمتناقض (نه فقط verdict)
- **W-S08** (I4×F2) — نبود تصمیم تکرارشونده، یادگیری را صفر نگه داشته: تنها کلید تکرارشونده همان کلید متناقض است
  - دلیل: LOO cycle1: n=141, changed=1, on=138/off=139 → MEMORY_HURTS؛ mixed_polarity_keys=[646d80a894ad3e8f]
  - شاهد: 09-LANES/OCTOPUS-SELF-TEST-TRAIN-20260918/evidence/LOO-cycle1.json
  - مخرج: هر تصمیم مالک را با decision_key پایدار دوبار سطح کن تا ردیف تکرارشوندهٔ غیرمتناقض ساخته شود

## سایر ورودی‌ها (خلاصه)

- W-131 [PARTIAL] از ۱۸۷ ردیف واقعی فقط ۱۴۱ ردیف learnable است؛ ۲۵٪ دادهٔ تصمیم بی‌کلید می‌ماند
- W-135 [PARTIAL] recorder تصمیم فقط از ۰۹-۱۷ کلید می‌نویسد؛ همهٔ ردیف‌های قبل بی‌کلیدند و قابل یادگیری نیستند
- W-136 [PARTIAL] شرط تولید سیگنال (سطح‌کردن دوبارهٔ یک پیشنهاد با کلید مشترک) وابسته به رفتار مالک است، نه تولیدکننده — نرخ رشد سیگنال کند
- W-137 [UNVERIFIED] حافظهٔ معنایی همیشه صفر نوت می‌سازد؛ یا by-design است یا یال شکسته — هنوز تعیین نشده
- W-144 [PARTIAL] ریسک روش‌شناسی: چرخهٔ یادگیری قبلاً fixture آموزشی را به‌عنوان holdout استفاده کرده بود
- W-138 [UNVERIFIED] بازیابی معنایی هنوز extractive-v1 (keyword-only) است — آخرین بلاکر هوش باز مانده
- W-139 [UNVERIFIED] PB-4 (حافظهٔ پاسخ‌دهی) با corpus جدید هرگز دوباره آزمون نشد
- W-140 [UNVERIFIED] سیم‌کشی ظرفیت/تازگی (F2) به self-model فقط طراحی شده و هرگز وصل نشد
- W-142 [UNVERIFIED] دو قابلیت کشف‌شده (fake_executor، external_witness SILENT_FLIP) بدون سیم‌کشی مانده‌اند
