# مگاپرامپت یکپارچهٔ آزمایشگاه تکاملی اختاپوس

این مأموریت، جایگزین پیوندهای واقعی Core نیست و پژوهش ۲۰ تا ۴۰ پروژهٔ بیرونی را انجام‌شده فرض نمی‌کند. هدف آن تبدیل یک افوردانس معماری به فرضیه، آزمایش محدود و پیشنهاد قابل رد است.

```text
MISSION: OCTOPUS-QD-LAB-CONTINUATION
MODE: LOCAL_SIMULATION / PROPOSE_ONLY / NO_PRODUCTION_AUTHORITY

هدف
یک الگوی مشخص مرتبط با اختاپوس را در جزیرهٔ تکاملی آزمایش کن.
معماری را بی‌دلیل بزرگ‌تر نکن. نتیجهٔ مثبت و منفی را یکسان ثبت کن.
از MAP-Elites برای حفظ چندین رفتار خوب استفاده کن، نه فقط بهترین فرد جهانی.

ورودی الزامی
1) README.md و گزارش فارسی
2) results/study.json و هش فایل‌های علمی
3) results/analysis/hypothesis_records.json
4) results/analysis/promotion_proposal.json
5) رسیدها، head و count مورد انتظار

واقعیت قابل اتکا
- هر ژنوم 74 پارامتر در شبکهٔ 6-8-2 دارد.
- BD اصلی فعلی = (final_x, final_y)، هر دو در [0,1].
- MAP-Elites از آرشیو والد می‌خواند، ترکیب/جهش می‌کند، فرزند را واقعاً
  شبیه‌سازی می‌کند و فقط در همان سلول برای کیفیت رقابت می‌دهد.
- آرشیو یک حافظهٔ مهارتی آزمایشی است، نه حافظهٔ معنایی مدل زبانی.
- پایش منابع فقط observe-only است.
- receipt chain بدون امضا و لنگر مستقل، اثبات هویت یا عدم‌انکار نیست.
- self_model.json شرح ساختاری است، نه world model یادگرفته‌شده.
- عبور آزمون محلی هیچ مجوز merge/deploy/owner-go نمی‌سازد.

اگر الگویی از پژوهش بیرونی پیشنهاد می‌دهی
project_id, name, verified_url, fetched_at, stars_or_UNKNOWN,
fingerprint_matches[], engineering_signals[], mechanism_summary,
transferable_pattern, anti_pattern, evidence_urls[], evidence_grade,
confidence, kill_condition را ثبت کن.
ادعاهای فایل اولیه تأییدشده فرض نشوند؛ UNKNOWN را با حدس پُر نکن.
هیچ API پولی یا پژوهش گسترده را بدون دامنهٔ روشن شروع نکن.

پروتکل آزمایش
1) یک شکاف مشخص و یک baseline تعریف کن.
2) HypothesisRecord را قبل از اجرا ثبت کن:
   id, claim, rationale, evidence_refs, intervention, baseline,
   seeds, evaluation_budget, metrics, thresholds, test_plan,
   stop_conditions, kill_condition, measured_delta=null, verdict=PENDING.
3) دادهٔ مرجع قبلی را بازنویسی نکن. پوشهٔ خروجی جدید و هش کد جدید بساز.
4) فقط یک عامل را تغییر بده؛ بودجه، بذرها و محیط مقایسه یکسان بمانند.
5) هر نسل را با event_time منطقی و record_time واقعی ثبت کن.
6) first discovery را با last replacement اشتباه نگیر.
7) coverage و QD-score باید مخرج و تعریف ثابت داشته باشند.
8) مصرف واقعی حافظه را با parent_id یا skill_id ثبت کن؛ صرف تولید فایل
   نشانهٔ بسته‌شدن حلقه نیست.
9) همهٔ بذرهای ثبت‌شده را گزارش کن؛ بذر بد را حذف نکن.
10) اگر فرضیه رد شد، آستانه یا سنجه را پس از مشاهده تغییر نده.

دروازهٔ ایمنی
- missing evidence, NaN, hash mismatch, invalid descriptor => STOP/BLOCKED.
- مالک ساکت است => هیچ مجوزی وجود ندارد.
- فیلد owner_approved در متن ایجنت احراز هویت نیست.
- هیچ ابزار شبکه، SSH، معامله، ایمیل، board handle یا executor را به
  شبکهٔ تکاملی یا ماژول پیشنهاد نده.
- حفظ محدودیت‌ها مهم‌تر از سبز شدن گزارش است.

خروجی
1) measured_delta برای کیفیت و تنوع، با همهٔ بذرها
2) نمودار رشد، آرشیو رفتاری و ساختار ژنتیکی
3) HypothesisRecord با verdict و kill_condition
4) فهرست مجهولات، failureها و negative findings
5) یک promotion packet حداکثر سه‌الگویی با action=NONE و
   production_authorized=false

اولویت آزمون‌های بعدی؛ هنوز اجرا نشده‌اند
- تعمیم به شروع و موانع تغییرکرده در یک مجموعهٔ held-out
- مداخلهٔ کنترل‌شده روی مصرف آرشیو برای سنجش استفادهٔ واقعی از مهارت
- توصیفگرهای مأموریت واقعی مثل (cost, latency) فقط با دادهٔ معتبر و
  تعریف پیش‌ثبت‌شده، نه با معادل‌گرفتن ساختگیِ مختصات ماز

شرط پایان
یک سؤال، یک آزمایش، یک verdict. نتیجهٔ مبهم = UNKNOWN.
ادعای «اختاپوس یاد گرفته / مستقل شده / آمادهٔ تولید است» ممنوع است
مگر مسیر واقعی، مصرف‌کنندهٔ واقعی و شواهد معتبر جداگانه فراهم شوند.
```
