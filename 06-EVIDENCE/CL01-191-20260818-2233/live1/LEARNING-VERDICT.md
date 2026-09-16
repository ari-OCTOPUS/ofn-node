# LEARNING VERDICT (LIVE-1)
label: MEMORY_LIVE_LEARNING_UNVERIFIED
dلیل‌ها:
  1) n=1 پیش‌بینی live — پنجرهٔ پایدار (روزها) برای Brier/calibration معتبر لازم است
  2) بهبود نسبت به baseline روی holdout هنوز سنجیده نشد (outcomeهای آیندهٔ holdout نیازمند اجرای مداوم)
سیگنال‌های مثبت ثبت‌شده (واقعی، نه ادعا):
  - evidence_changed_proposal=TRUE — اولین شاهدِ live که بازیابیِ episode با provenance،
    proposal بعدی را تغییر داد (سؤال کلیدی مالک)
  - حلقهٔ کاملِ prediction→outcome→امتیاز در مسیر append-only بسته شد
  - دیمون ۴d با حلقهٔ حافظه فعال برگشت (read-back فرضیه #1325)
