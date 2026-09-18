# آزمایش یادگیری و خودترمیمی واقعی

Status: ENGINEERING_DESIGN_NOT_RUN. این سند دادهٔ نتیجه نیست. ایجنت اجراکننده باید نسخهٔ preregistration، hash و timestamp را پیش از مشاهدهٔ holdout ثبت کند. معیارهای زیر طرح پیشنهادی شروع‌اند؛ هر اصلاح قبل از اجرای مقایسه و با توضیح انجام شود.

## یک: واحد یادگیری را مشخص کن

سطوح را جدا اندازه بگیر:

- retrieval/context adaptation: استفادهٔ قابل‌ردگیری از تجربه در تصمیم بعدی؛ وزن مدل ثابت.
- skill acquisition: artifact اجرایی versioned که روی مسئلهٔ جدید مصرف می‌شود.
- policy selection: انتخاب بین راهکارهای مجاز بر اساس outcome واقعی؛ خودتغییریِ اختیار نیست.
- code self-improvement: تغییر کد خارج از TCB، تولیدشده در حلقهٔ مجاز و پذیرفته‌شده بعد از ارزیابی مستقل.
- weight training: فقط اگر checkpoint، داده، optimizer و run واقعی وجود دارد. در S1 چنین شاهدی نداریم.

وجود lesson، cache-hit، سرعت بار دومِ یک سؤال یا امتیاز قضاوت مدل به‌تنهایی هیچ‌یک را اثبات نمی‌کند.

## دو: طرح مقایسه با هزینهٔ کنترل‌شده

چهار بازو روی replicaها و دادهٔ یکسان:

| بازو | رفتار | سؤال |
|---|---|---|
| B0 | قواعد ثابت/اسکریپت سادهٔ موجود | آیا اصلاً مدل لازم است؟ |
| B1 | همان agent/model/tools، حافظهٔ بین‌اپیزودی و self-edit خاموش | اثر orchestration و تکرار بدون یادگیری چقدر است؟ |
| C1 | حافظه/درس معتبر، کد agent ثابت | آیا حافظه روی مسئلهٔ تازه منفعت علّی دارد؟ |
| C2 | C1 + skill/patch پذیرفته‌شده، سایر عوامل ثابت | سهم تغییر رفتار/کد چقدر است؟ |

این نام‌ها فقط بازوی آزمایش‌اند؛ خاموش‌کردن حافظهٔ production یا حفاظ‌ها مجاز نیست. ablation فقط در replica. اطلاعات موردنیاز برای ایمنی در همهٔ بازوها ثابت بماند.

حداقل پایلوت مهندسی: ۱۰ جفت برای رفع اشکال harness، بدون ادعای پژوهشی. سپس طرح holdout حداقل ۳۰ جفت از پنج خانوادهٔ وظیفه با منشأ/زمان جدا. این تعداد تضمین power نیست؛ واریانس، هم‌بستگی خانواده و effect مورد انتظار اندازهٔ لازم را تعیین می‌کنند. اگر بودجه یا داده کافی نیست، UNDERPOWERED/INCONCLUSIVE بده، نه PASS.

خانواده‌های شروع: replay/restore، تشخیص خطای سرویس، پردازش ورودی malformed/stale، مصرف درس برای انتخاب ابزار، و یک workflow اداری واقعی بدون ارسال بیرونی. برای quality از expected-output مستقل یا test oracle استفاده کن. code fixture، fault مصنوعی و دادهٔ واقعی با label جدا ذخیره شوند. دادهٔ نگه‌داشته‌شدهٔ واقعیِ task با hash و رضایت دامنه همراه باشد؛ PII وارد بسته نشود.

train/dev/holdout را بر اساس خانواده/منشأ جدا کن، نه صرفاً shuffle سطرهای تکراری. evaluator روی ۱۶۰ یا ۱۸۲ مخفی بماند؛ سازنده outcome/جواب heldout را هنگام اصلاح نبیند. ترتیب بازوها را متوازن/تصادفی کن؛ caches، warmup، queue delay، ساعت و state reset ثبت شوند. holdout مصرف‌شده از آن پس dev است؛ برچسب heldout را روی تکرار همان آزمون نگه ندار.

مدل و provider revision، reasoning، temperature، ابزار، context budget، deadline و تعداد تلاش در بازوها یکسان یا عامل آزمایشیِ پیش‌ثبت‌شده باشند. هزینهٔ reasoning/token/cache/fallback و شکست نیز در صورت‌حساب آزمایش حساب شود. اگر نسخهٔ provider ناشناخته است، UNKNOWN ثبت و ادعای exact reproducibility محدود شود.

## سه: metricها و حکم

Metric اصلی را قبل از نتیجه انتخاب کن:

- quality: نسبت موفقیت وظایف holdout؛ مخرج همهٔ taskهای آغازشده در scope، timeout/refusal/error مطابق rule ثابت. abstention مجاز را جدا گزارش کن.
- سرعت یادگیری: تعداد outcomeهای مستقل تا رسیدن به کیفیت هدف روی holdout، همراه هزینه و wall-time؛ طول متن lesson معیار نیست.
- sample efficiency: موفقیت به ازای episode و دلار API؛ صفر دلار با تقسیم بر صفر امتیاز بی‌نهایت نمی‌سازد؛ در مسیر رایگان موفقیت/CPU-second نیز گزارش شود.
- latency: p50/p95 end-to-end و تفکیک queue، inference، tool، verify و انتظار مالک.
- کیفیت قضاوت: false-positiveِ «healthy/complete»، خطای confidence با Brier/calibration فقط اگر پیش‌بینی ثبت‌شده و outcome کافی وجود دارد، و نرخ تشخیص UNKNOWN.
- فراموشی: موفقیت روی regression ثابت پیش و پس از یادگیری و بعد از restart.

قاعدهٔ پیشنهادی ارتقای آزمایشی: هیچ نقض invariant، و یکی از دو معیار از پیش انتخاب‌شده:
الف) افزایش حداقل ۱۰ percentage point در success و کران پایین فاصلهٔ اطمینان ۹۵٪ تفاوت بالاتر از صفر؛
ب) کاهش حداقل ۲۰٪ هزینه یا latency با non-inferiority کیفیت (حاشیهٔ ۳ percentage point از پیش ثبت‌شده).
این درصدها آستانهٔ مهندسی پیشنهادی‌اند، نتیجه یا قانون عمومی نیستند. روش فاصلهٔ اطمینان، واحد bootstrap و correction چندمقایسه‌ای را قبل از holdout freeze کن. هم‌بستگی وظایف یک خانواده را لحاظ کن. quality و budget violation را با سرعت میانگین جبران نکن.

شکست‌ها و retryها حذف نشوند. توقف زودهنگام فقط طبق stopping rule پیش‌ثبت‌شده؛ نگاه‌کردن مکرر تا سبزشدن p-value ممنوع. سقف اجرای بعدی را با ۱۰USD/rolling24h و ۱۰۰USD/month هماهنگ کن. نتیجهٔ نامعین را نگه دار و lane مهندسی مستقل را ادامه بده.

## چهار: خودترمیمی بدون دخالت پنهان مهندس

ابتدا baseline ثابت auto-restart/restore موجود را روی همان faultها اندازه بگیر؛ LLM فقط وقتی ارزش دارد که چیزی بیش از آن ثابت کند. حداقل شش خانواده: توقف worker ایزوله، timeout/disconnect transport، duplicate/reordered/stale message، torn write/fsync/ENOSPC شبیه‌سازی‌شده، config مجازِ ناسازگار، و شاهد خراب/غایب. faultها محدود به scope برگشت‌پذیر باشند؛ secret، TCB، دیتای یکتا و سرویس حیاتی هدف تزریق نیستند.

برای هر family حداقل سه تکرار در پایلوت و replay روی میزبان دوم. این ۱۸ مورد تخمین قابلیت همان faultهاست، نه قابلیت عمومی. شناسه و بایت payload/fault، source SHA، boot_id، وابستگی، منبع زمانی، expected failure، حداکثر زمان و cleanup/rollback قبل از اجرای fault ثبت شوند.

دو lane جدا: سازندهٔ سیستم و injector/evaluator. بعد از inject، مهندس فقط observer است؛ هر دستور اصلاحی دستی episode را ENGINEER_ASSISTED می‌کند. خروجی سیستم باید actionable diagnosis و مسیر اجرایی مجاز را نشان دهد؛ هم‌زمانی خوب‌شدن به‌تنهایی اثر تعمیر را اثبات نمی‌کند.

زنجیرهٔ receipt: `fault_id → observed_event → diagnosis_id → action_id → gate_receipt → commit/effect → readback → witness → retained_or_rolled_back`.

گزارش: detection latency، time-to-first-functional-recovery، زمان تا پایداری پنج probe متوالی در فاصلهٔ ۶۰ثانیه، false repair، harmful repair، rollback success، manual intervention count، recurrence بعد از restart و هزینه. SLO هر fault پیش از اجرا انتخاب شود؛ برای fault حل‌نشده p95 ساختگی نساز، censored/failed را با denominator گزارش کن.

در fault شاهد غایب/گیت نامعلوم، نتیجهٔ صحیح می‌تواند SAFE_HOLD باشد. این «تعمیر خودکار» نیست و در ستون جدا می‌آید. unsafe success=0 در موارد آزموده‌شده لازم است، ولی صفر مشاهده‌شده تضمین ایمنی عمومی نیست.

## پنج: شاهد و زنجیرهٔ علّی

میزبان دوم استقلال فیزیکی می‌دهد؛ اگر همان نویسنده، همان oracle و همان secret کنترلش کنند استقلال کامل ارزیابی نیست. hash اصالت هویت نمی‌دهد؛ امضای معتبر هم درستی علمی outcome را تضمین نمی‌کند. witness باید scope، source SHA، dataset SHA، boot/process identity، زمان، نتیجهٔ checker مستقل و صلاحیت signer را به هم bind کند.

برای «درس باعث بهبود شد»، trace بازیابی و مصرف را همراه ablation C1/B1 داشته باش. برای «سیستم خودش بهتر شد»، actor و هر intervention انسانی را ثبت کن. receiptها باید hash-chain معتبر، ترتیب، تکرار، missing link، tamper و fork handling داشته باشند؛ هیچ claim فقط از متن summary پذیرفته نیست.

## قالب artifact هر آزمایش

`EXPERIMENT.json`: hypothesis، causal_mechanism، primary_metric، minimal_effect، task_ids/dataset_hash، split_hash، baseline/candidate_sha، model/provider/revision، treatment، control، resource_caps، budget_policy_sha، clock_source، sample_plan، inference_method، stopping_rule، failure_rule، rollback، owner_scope_ref.

`TRIALS.jsonl`: trial/run/task/fault IDs، node+boot، actor، arm/order، input_hash، code_hash، memory_before/after_hash، memory_retrieved_ids، consumer_trace، stage receipts، timestamps، result، error، tokens، reserved/charged_USD، manual_interventions، witness_ref.

`VERDICT.json`: PASS_SCOPE/FAIL/INCONCLUSIVE/UNDERPOWERED/NOT_RUN، denominator، missing_count، effect/interval، invariants، independent_reproduction، deployment_scope، limitations. هیچ template با عدد نمونه به ledger واقعی افزوده نشود.
