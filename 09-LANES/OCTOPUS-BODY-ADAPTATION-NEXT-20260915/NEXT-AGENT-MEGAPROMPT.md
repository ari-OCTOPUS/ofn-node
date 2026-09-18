# OCTOPUS — سازگاری با بدن هفت‌بردی و تکمیل مغز ماندگار

GOV_VERSION=V8 · LADDER=L2 · تاریخ بسته: 2026-09-15

**این نقطه شروع جدید است.** از P0 یا نصب دوباره ورکرها شروع نکن. P5 ثبت‌شده است؛ P6 هنوز OPEN است. هدف مالک: **پاسخ بهتر + فراموش‌نکردن + ادامه بدون لپ‌تاپ**. کاربرد واقعی سخت‌افزار، کیفیت پاسخ و دوام را بهتر کن؛ هیچ امتیازی برای تعداد سرویس، پرکردن CPU/NPU یا گزارش‌های بیشتر وجود ندارد.

این سند برنامه ادامه است، نه اختیار تازه و نه رسید اجرای زنده. وضعیت‌های زیر از فایل‌های روی دیسک بازبینی شده‌اند؛ آغاز اجرای تو نیازمند تطبیق سبک با runtime و مالک فعلی مسیرهاست. هش، برابری بایت را ثابت می‌کند؛ به‌تنهایی امضای امنیتی، صحت آزمایش یا وضعیت فعلی سرویس را ثابت نمی‌کند.

## ۰. مسیرها، منابع و شروع سریع

| نام | مسیر |
|---|---|
| بسته جدید / NEXT | `F:/backup/09-LANES/OCTOPUS-BODY-ADAPTATION-NEXT-20260915/` |
| نسخه تألیف در worktree | `F:/octopus-body-adaptation-next-20260915/09-LANES/OCTOPUS-BODY-ADAPTATION-NEXT-20260915/` |
| اجرای مغز ماندگار؛ اختصار EXEC | `F:/backup/09-LANES/OCTOPUS-PERSISTENT-FLEET-EXEC-20260915/` |
| اجرای سخت‌افزار؛ اختصار HW | `F:/backup/09-LANES/OCTOPUS-HARDWARE-EXEC-20260915/` |
| پیشنهاد اولیه؛ فقط تاریخچه طراحی | `F:/hardware-handoff-review-20260915/09-LANES/HARDWARE-HANDOFF-REVIEW-20260915/PERSISTENT-FLEET-PROPOSAL.md` |
| قرارداد اصلی | `F:/backup/AGENTS.md` |
| آزادی عملیاتی | `F:/backup/06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/GOV-FREEDOM-V2-2026-09-13.md` |
| ورودی مهندسی | `F:/backup/07-HANDOFF/ENGINEERING-ENTRYPOINT-2026-09-04.md` |
| Owner Board | `F:/backup/06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/BOARD.md` و `CURRENT-TRUTH.md` |

ترتیب خواندن: قرارداد جاری و ورودی/برد مالک → این NEXT → `CURRENT-STATE.json` → `SOURCE-INDEX.json` و فقط رسیدهای مربوط به کار بعدی. `sources/` نسخه ثابت منابع بررسی‌شده است؛ در صورت تغییر منبع زنده، هر دو نسخه را حفظ و علت تفاوت را ثبت کن. همه پیوندهای نسبی این سند داخل بسته‌اند؛ EXEC/HW مطابق جدول بالا باز شوند.

فرمان بررسی بسته در PowerShell: `& '<مسیر بسته>/scripts/verify-packet.ps1'`. خروجی آن فقط سلامت بسته و اختلاف منابع را گزارش می‌کند؛ اجرای اختاپوس یا تأیید live انجام نمی‌دهد.

### نخستین چرخه کار

1. یک lane/worktree اجرایی و مالک هر مسیر را ثبت کن. اگر PC_worker هنوز همان مسیر را اجرا می‌کند، writer دوم نساز؛ نتیجه‌اش را مصرف کن و کار مستقل بگیر.
2. تاریخچه مجوز را از جدول بخش ۲ و متن کامل gate بخوان. GOهای P5/P6 را دوباره نپرس.
3. فقط منابع فعال این برش را تازه‌سنجی کن: ساعت، host/node_id، boot_id، کد واقعاً بارشده، PID/unit، آخرین job/receipt، وضعیت lease و kill-switch. secret، env و command line حساس را نخوان/چاپ نکن.
4. ادامه PB-1 را از آخرین checkpoint پیدا کن؛ آیا scheduler/consumer واقعاً بدون فراخوانی دستی لپ‌تاپ جلو رفته؟ ساعت شروع به‌تنهایی شاهد پیشرفت نیست.
5. هم‌زمان در محیط مستقل، مسیر واقعی retrieve و آزمون PB-4 را بساز؛ T3 روی 193 برش جدا با مالک واحد دارد. منتظر اتمام ۲۴ ساعت برای کارهای مستقل نمان.

## ۱. وضعیت شروع؛ نتیجه تاریخی را با قابلیت کامل یکی نکن

| موضوع | آنچه فایل‌ها ثبت کرده‌اند | معنای محدود و ادامه لازم |
|---|---|---|
| T1 / heartbeat | چهار ورکر 100/160/193/114 وصل شده‌اند | heartbeat به معنی سرویس شناختی یا consumer دائمی نیست |
| P0 | NATS/JetStream روی 182، هشت stream و صفر consumer در snapshot | bus انتخاب‌شده `jsonl_138`؛ NATS_DURABILITY=NOT_CLAIMED |
| P1 | قرارداد سه‌نوعی حافظه، dry persist روی 138 | PB-4 فقط یک fact آزمایشی و هیچ harness اندازه‌گیری پیدا نکرده |
| P2 | ماشین حالت و index idempotency سایه | replay/locking/fsync/consumer خودکار باید روی بایت‌های جاری بررسی شود |
| P3 / PB-3 | 9/9 فایل restore روی 180 MATCH؛ RPO=0 در لحظه snapshot؛ انتقال+تطبیق حدود 3 ثانیه | این عددها زمان بازیابی سرویس/پاسخ و RPO پیوسته نیستند؛ خواندن معنایی و replay مستقل لازم است |
| P4 | mesh_ssh، registry و lease مجاز چهار ورکر؛ PASS ثبت‌شده | fingerprint مشترکِ کلید client، امضای مستقل هر worker نیست؛ HMAC ثابت نشده؛ سیاست هویت را خودسر عوض نکن |
| P5 | job `job-8f635a12d2cd4228` روی 100 CLOSED؛ QA PASS_WITH_CAVEAT | نوع واقعی `echo_capability_probe` است؛ retrieve واقعی و daemon ماندگار از آن نتیجه نمی‌شود |
| PB-1 | IN_PROGRESS؛ شروع `2026-09-15T04:03:36Z` | probe وابستگی لپ‌تاپ NOT_YET؛ earliest زمانی `2026-09-16T04:03:36Z` = 16 سپتامبر 14:03:36 سیدنی؛ عبور زمان کافی نیست |
| PB-2 | PASS ثبت‌شده برای کشتن sleep و ثبت UNKNOWN | lease تا سال 2099؛ آزمایش، انقضای واقعی و recovery خودکارِ consumer واقعی را ثابت نمی‌کند |
| PB-4 | NOT_RUN | مهم‌ترین شکاف «پاسخ بهتر»؛ retrieval/answer A/B واقعی بساز |
| PB-5 / NPU | ماتریس شش PASS و 138 NOT_RUN | اجرای مدل آزمایشی ثبت شده؛ checksum خروجی تصادفی، صحت معنایی detection نیست؛ اعداد end-to-end محصول نیستند |
| PB-6 | هفت ردیف و سلامت/auth ثبت شده | هفت قابلیت شناختی عملی از آن استنتاج نکن |
| T3 / 193 | نقش model_infer ثبت شده | خدمت واقعی مدل در این شواهد اثبات نشده |
| W24 | در پیام پیوست باز گزارش شده | فایل شاهد مستقیم این برش در بسته نیست؛ مسیر مستقل/مالک موجود؛ singleton poller حفظ شود |

اصل: `reported_status` را از `accepted_scope` جدا نگه دار. ردیف PASS قدیمی را پاک یا بازنویسی نکن؛ محدودیت یا ابطال هم‌دامنه را با ارجاع به hash آن append کن. قرارداد پذیرش قبلی را برای سبزکردن نتیجه تغییر نده.

### نکته فنی NPU که باید قبل از توسعه benchmark حل شود

`HW/T2-PILOT/src/rknn_infer_bench.c` از ورودی deterministic pseudo-image استفاده می‌کند؛ 20 حلقه و 3 warm-up در log برد 193 است. `FPS` معکوس میانگین بازه inputs_set+run است، نه نرخ سرویس کامل شامل انتقال، صف و postprocess. خروجی یک بار خوانده و checksum می‌شود؛ مرجع صحت ندارد.
همچنین در مسیر خطای حلقه، کد break می‌کند ولی آمار را برای کل loops می‌سازد و در پایان بدون وابستگی به موفقیت همه مراحل `STATUS=PASS` می‌نویسد. این نقصِ منبع است، نه اثبات اینکه اجرای تاریخی خطا داشته. قبل از تکیه دوباره: شمار نمونه موفق، کد خروجی fail-closed، bounds ورودی/خروجی و مرجع صحت را اصلاح و به‌صورت نسخه جدید آزمایش کن؛ شواهد قدیمی را حفظ کن.

## ۲. مجوزهای موجود؛ اختیار را نه کم کن و نه زیاد

مالک قبلاً GO کامل طرح، GO P5 و GO P6 full battery را انتخاب کرده؛ attachment در sources حفظ شده است. مجوزهای scoped و شرایط فعلی در اسناد زیرند:

| gate | منبع | محدوده |
|---|---|---|
| P5 | EXEC `P5/SEC-P5-JOB-PATH-GATE-20260915.md`؛ hash `3e8bd525…` | یک job_type روی jsonl؛ lease فقط auth OK و eligible؛ سایر قیود متن کامل |
| P6 | EXEC `P6/SEC-P6-ACCEPTANCE-20260915.md`؛ hash `9cd862ef…` | PB-1…PB-6؛ fault محدود یک worker eligible؛ بدون fake 24h |
| P4 | EXEC `P4/SEC-NODE-ID-AUTH-ADDENDUM-20260915.md` | روش احراز پذیرفته‌شده و محدودیت‌ها |
| standing non-TCB | GOV-FREEDOM-V2 | read/code/test/package/shadow خودکار؛ انتشار پایدار با شاهد 182 و canary ترتیبی |

hash کامل و برابری با ارجاع‌های خوانده‌شده در SOURCE-INDEX است؛ خواندن یک فایل با نام SEC مساوی راستی‌آزمایی امضای آن نیست. seal P6 با hash `f9c68553…` در LANE-REPORT/attachment ذکر شده اما فایل مستقل آن در بسته محلی یافت نشده: `REFERENCED_NOT_LOCALLY_VERIFIED`. ابتدا از مسیر مالک QA پیدا کن؛ این فقدان مانع کدنویسی و آزمون محلی نیست، مانع ادعای پذیرش کلی است.

**مرزهای ثابت:** 138 sole commander/writer؛ 180 هرگز auto-promote؛ `may_authorize=false`؛ customer_send HOLD؛ صف درآمد/پول مصرف نشود؛ هیچ secret خام منتشر نشود؛ هیچ رسیدی حذف/بازنویسی نشود؛ 138 خاموش نشود؛ wipe و reboot جمعی ممنوع؛ MAC/DHCP فعلاً docs؛ هیچ consumer دوم یا اجرای هم‌زمان jsonl و NATS برای یک job. تعویض کلید/TCB/منشور خارج از این برنامه است.

وجود GO P6 مجوز اضافه‌کردن بی‌قید همه job_typeهای جدید نیست. retrieve/model_infer واقعی را به‌عنوان diff و بسته قابل بررسی بساز، scope جدید را با gate و شاهد لازم تطبیق بده و فقط برش مجاز را منتشر کن. برای کار داخلی غیر-TCBِ پوشش‌داده‌شده، GO عمومی را دوباره نپرس. مرز جدیدِ نیازمند مالک را با چهار مسیر کوتاه فارسی و یک انتخاب مشخص مطرح کن؛ کارهای مستقل ادامه یابند.

## ۳. نقشه بدن که خود اختاپوس باید مصرف کند

فقط registry جدید درست نکن. روی registry/self-model موجود یک نمای سازگار بساز که consumer واقعی آن را بخواند؛ یک نویسنده canonical روی 138. برای هر هفت نود این‌ها لازم است:

`node_id, observed_endpoint, boot_id, auth_method, auth_status, evidence_at, loaded_code_sha,
primary_role, measured_capabilities[], service_state, resource_headroom, active_leases,
health_status, last_success_receipt, limitations[]`

هر capability با workload/model/input contract، نسخه، صحت خروجی، latency، حافظه، شرایط آزمون و آخرین رسید معرفی شود. نقش و قابلیت از هم جدا: `model_infer` عنوان نقش است؛ مدل معتبر و فراخوانی واقعی capability است. متادیتای قدیمی stale شود، حذف نشود. RAM هفت برد یک حافظه مشترک برای یک مدل نیست.

| node | نقش مقصد | اولین خروجی کاربردی |
|---|---|---|
| 138 | coordinator + memory/job writer | برنامه‌ریزی و ثبت کار بدون لپ‌تاپ، self-model مصرف‌شونده |
| 180 | quality + restore RO | ارزیابی مستقل پاسخ‌های منتخب و readback حافظه بازیابی‌شده |
| 182 | witness + sensorium موجود | سلامت و شاهد مهم با headroom محفوظ؛ بار اضافی شاهد را مختل نکند |
| 100 | knowledge_retrieve | سؤال → شواهد واقعی با source/hash/span و کنترل تازگی |
| 160 | knowledge_prep | سند مجاز → متن/بخش‌بندی/نمایه با provenance و حذف تکرار منطقی |
| 193 | model_infer | درخواست typed → مدل نسخه‌دار → خروجی معتبر و رسید |
| 114 | eval_batch | سنجش held-out و replay شکست‌ها؛ پیشنهاد اصلاح با گزارش اثر |

این جدول مجوز تغییر هم‌زمان سرویس‌ها نیست؛ ابتدا برش کاربردی 100 و سپس 193 و باقی نقش‌ها را ترتیبی منتشر کن. ظرفیت خالی برای کار کم‌اولویت استفاده شود؛ مصونیت شاهد و فرمانده اولویت دارد.

## ۴. مسیرهای اجرایی با خروجی و پذیرش

### A — تشخیص بدن و حفظ ادامهٔ موجود

**مالک:** coordinator/PC؛ read-only در آغاز. از P4 registry، heartbeat، job ledger و واحدهای واقعی service/timer نقشه مسیر بساز. caller و parent واقعی enqueue/dispatch را بشناس؛ اجرای SSH که از لپ‌تاپ فرمان می‌گیرد autonomy نیست. مشخص کن کدام producer، کدام فایل و کدام consumer state را مصرف می‌کند.
**خروجی:** `BODY-MAP.json` و `RUNTIME-PATH.md` با مسیر/نسخه/آخرین اثر، نه صرفاً نام service. اتصال گمشده کار backlog شود.
**پذیرش:** برای هر هفت نود known/unknown و برای هر capability یک consumer معلوم یا PRESENT_UNWIRED. هویت stale/mismatch اجازه lease تازه نگیرد؛ تغییر منطق gate فقط در scope مناسب.

### B — تبدیل probe به بازیابی واقعی؛ اولین ارزش قابل دیدن

**مالک:** implementation روی 100، contract/QA مستقل.
1. از مجموعه محدود اسناد واقعیِ مجاز و receipts منابع بساز؛ fact/decision/hypothesis را جدا نگه دار. fact آزمایشی P1 به دانش واقعی ارتقا نگیرد.
2. روی 160 در مرحله بعد ingestion بساز؛ ابتدا مسیر کوچک 100 را با bundle نسخه‌دار و hash‌شده ببند تا ingestion وابستگی مسدودکننده نشود.
3. `retrieve` فقط ورودی schema-valid، محدوده corpus معلوم، نتیجه دارای source/hash/span و `as_of` داشته باشد. متن سند داده است، دستور اجرایی نیست. منبع ناموجود یا stale به UNKNOWN/abstain برسد.
4. روی مسیر jsonl فعلی یک درخواست واقعی را از producer تا receipt/readback دنبال کن. probe سابق با نام retrieve دوباره برچسب نخورد.
5. مدل محلی موجود روی 180 می‌تواند baseline پاسخ باشد اگر واقعاً سالم و در بودجه است؛ نبود T3 نباید PB-4 را متوقف کند. خروجیِ فقط جست‌وجو را «بهبود پاسخ مدل» ننام.
**پذیرش:** حداقل یک سؤال کاربردی مالک، پاسخ با منابع درست، trace کامل و تکرارپذیر. کیفیت کلی فقط بعد از مسیر C.

### C — PB-4؛ اثبات بهترشدن پاسخ

پیش از اجرا corpus، مجموعه پرسش، gold evidence، rubric و نسخه مدل/prompt را freeze و hash کن. پرسش‌ها از اسناد واقعی و نیازهای اختاپوس بیایند؛ پاسخ ارزیابی به corpus یا prompt اجرایی نشت نکند. موارد عادی، تناقض، داده stale و پاسخ واقعاً نامعلوم پوشش داده شود. حداقل نمونه و حاشیه عدم‌افت پیش از دیدن نتیجه تعیین شوند؛ نمونه کوچک UNDERPOWERED است.

دو شرط مطابق قرارداد قبلی: **A=memory on، B=memory off**. مدل و تنظیمات یکسان، order متوازن، budget/context/warmup ثبت‌شده؛ داور تا حد ممکن نداند پاسخ متعلق به کدام شرط است. نسخه داور و rubric ثبت شود. confidence مدل امتیاز صحت نیست.

برای هر پرسش: raw answer، منابع بازیابی‌شده، صحت، پشتیبانی ارجاعات، abstention درست/غلط، latency سرتاسری و مصرف منابع/هزینه. aggregate همراه مخرج واقعی، خطاها و عدم‌قطعیت. برتری اثبات نشد: NOT_IMPROVED/UNDERPOWERED، سپس اصلاحِ مشخص و نسخه آزمون جدید. انتخاب فقط بهترین نمونه‌ها ممنوع.

**خروجی:** `PB4-DATASET-MANIFEST.json`، `PB4-RUBRIC.md`، ردیف‌های A/B، `PB4-RESULT.json` و receipt ثبت مصرف حافظه در پاسخ. این مسیر مهم‌ترین سنجه هوشمندی است.

### D — T3؛ خدمت مدل واقعی روی 193

قبل از نصب دوباره، PID/unit/endpoint/نسخه موجود را بررسی کن. workload را از نیاز واقعی انتخاب کن؛ YOLOv5s تشخیص تصویر است و benchmark آن اثبات LLM/embedding نیست. یک مدل کوچک سازگار را با RAM واقعی و کاربرد انتخاب کن؛ ادعای صرفاً RK3588 Plus مجوز مدل بزرگ نیست.

سرویس واحد با ورودی محدود، سقف concurrency/timeout، شناسه مدل و نسخه، check readiness و خطای قابل تشخیص. health سبز کافی نیست: از 138 درخواست typed برسد، مدل واقعاً اجرا شود، خروجی با مرجع صحت تطبیق بخورد و نتیجه پایدار readback شود. مدل/NPU/CPU backend واقعی در receipt مشخص باشد. fallback اندازه‌گیری‌نشده به‌عنوان NPU ثبت نشود.

**پذیرش:** `T3-SERVICE-RECEIPT.json` شامل unit/loaded code/model/runtime hashes، درخواست/پاسخ مرجع، correctness، latency سرتاسری، RAM/temp و canary/rollback. 138 را برای رسیدن به 7/7 NPU تحت بار نگذار؛ 6/7 با یک NOT_RUN دلیل‌دار قابل گزارش است.

### E — PB-1/PB-2/PB-3؛ دوام عملی

**PB-1:** پنجره موجود را حفظ کن. از نخستین زمانی که producer/scheduler/consumer خودکار واقعاً فعال بوده و dependency probe شاهد دارد، بازه معتبر را تعیین کن. اگر ساعت شروع قدیمی فقط marker بوده، elapsed آن را به اجرای بعدی نچسبان؛ یک window تازه با لینک به قبلی بساز. تغییر کد وسط soak، نسخه/segment جدید است. شمار expected/scheduled/started/completed/failed/unknown و بیشترین gap ثبت شود. حداقل یک Q/A محلی با شاهد عدم وابستگی لپ‌تاپ لازم است. گذشت تا 16 سپتامبر 14:03:36 سیدنی شرط زمانی حداقلیِ پنجره قدیمی است، نه فرمان PASS.

**PB-2:** نتیجه stand-in قبلی را حفظ کن. در scope fault موجود، یک worker eligible و job واقعی با اثر داخلی بی‌خطر و معلوم را انتخاب کن. lease کوتاه و واقعاً منقضی‌شونده، PID/loaded code دقیق، pre-image و rollback. قبل/بعد از persist و قبل از ACK را جدا تست کن؛ consumer/reconciler خودش recovery یا UNKNOWN را ثبت کند. دستی `mark_unknown` کردن، شاهد recovery خودکار نیست. خواندن نهایی پس از بازشدن مجدد state و dedup اثر مهم است؛ صرف همان job_id کافی نیست. فقط PID دقیق تست، بدون kill کلی و بدون reboot 138.

**PB-3:** snapshot جدید در مسیر جدا روی 180؛ manifest و سازگاری snapshot سپس replay/readback معنایی و پاسخ به یک query واقعی از state بازیابی‌شده. RPO نسبت به آخرین داده committed مبنا و RTO تا usable-readback تعریف شود؛ زمان کپی را جدا بنویس. writer/dispatch بازیابی‌شده فعال نشود. از بین بردن index idempotency برای rollback ممنوع؛ tombstone/cancel/reconcile قابل‌ردیابی به‌کار رود تا job دوباره اثر نسازد.

### F — سازگاری تدریجی و هوشمندی ماندگار

پس از مسیر کاربردی پذیرفته‌شده، scheduler غیر-TCB با ظرفیت **اثبات‌شده** انتخاب کند: capability match → تازگی/auth → headroom → ظرفیت lease → latency/خطای مشاهده‌شده. ابتدا پیشنهاد/ shadow، سپس canary ترتیبی با شاهد. hysteresis و cooldown تعریف کن تا نود با نوسان دما مدام نقش عوض نکند. محدودیت‌های حرارت را از سخت‌افزار/اپراتور بگیر؛ عدد دمای دلخواه را خطر قطعی ننام. توان بدون سنسور NOT_MEASURED بماند.

هر تغییر منابع باید اثر مصرف‌کننده داشته باشد: نود stale می‌شود → scheduler کار تازه نمی‌دهد → کار داخلی مجاز به eligible دیگر می‌رود/در انتظار می‌ماند → رسید نتیجه ثبت می‌شود → self-model و پنل همان را نشان می‌دهند. صرف تغییر dashboard کافی نیست.

114 خطاهای تکراری را به case ارزیابی و پیشنهاد اصلاح تبدیل کند؛ 160 منابع تازه را وارد حافظه نسخه‌دار کند؛ 100 بازیابی کند؛ 193 پاسخ/مدل بدهد؛ 180 موارد لازم را ارزیابی کند؛ 182 شاهد باشد؛ 138 چرخه را کنترل کند. ارتقای خودکار مدل یا اختیار از این چرخه نتیجه نمی‌شود: همان مسیر آزمون، شاهد، canary و rollback برقرار است.

**پذیرش:** یک تغییر واقعی و کنترل‌شده در وضعیت worker باعث تصمیم routing قابل توضیح و اثر درست شود؛ و یک خطای تکراری بعد از اصلاحِ نسخه‌دار روی held-out کاهش یابد یا صادقانه NOT_IMPROVED ثبت شود.

## ۵. موازی‌کاری بدون تداخل

کار مستقل را موازی پیش ببر؛ یک مالک برای هر مسیر و هر نود در پنجره تغییر. نقش‌های PC/ARCH/QA/SEC نام مسئولیت‌اند؛ حضور واقعی agent را بررسی کن و agent فرضی یا seal خیالی نساز. اگر تنها هستی پیاده‌سازی و ارزیابی را جدا ثبت کن؛ آن را independent QA ننام.

| مسیر | مالک مسئول | می‌تواند هم‌زمان با | تداخل ممنوع |
|---|---|---|---|
| PB-1 observer/continuity | PC/coordinator | طراحی و آزمون محلی PB-4 | تغییر پنهانی مسیر زیر soak |
| retrieve + PB-4 | worker implementation + QA | T3 تا وقتی node/resource جداست | دو writer روی queue/state 138 |
| T3 روی 193 | model-service implementer | corpus/held-out در محیط جدا | fault/restart هم‌زمان همان 193 |
| evidence verification | QA | همه مسیرها read-only | seal صرفاً از گفته implementer |
| bounded deploy gates | SEC/182 | ساخت محلی | تغییر gate توسط نویسنده کد |
| W24 | مالک فعلی W24 | به‌صورت کار مستقل | دومین getUpdates یا ارسال مشتری |

W24 شرط موفقیت حافظه/PB-4 نیست. HOLD ارسال مشتری برقرار است؛ اتصال viewer جدید را با اجازه ارسال اشتباه نگیر. در صورت نبود مالک/شاهد W24، این مسیر را با reference باز بگذار و مغز ناوگان را جلو ببر.

## ۶. خروجی نهایی و تعریف اتمام

در lane اجرایی: `LANE-REPORT.md`, `ACTIONS-LOG.md`, `BODY-MAP.json`, `CAPABILITY-MATRIX.json`, `ACCEPTANCE-MATRIX.json`, `PB4-*`, `T3-SERVICE-RECEIPT.json`, `CONTINUITY-WINDOWS.jsonl`, `RESTORE-READBACK-RECEIPT.json`, `NEXT-ACTIONS.json` و پوشه receipts. نام‌ها قرارداد خروجی پیشنهادی‌اند، وجود فعلی ادعا نشده است.

هر receipt: شناسه/UTC، node/boot_id، نسخه واقعاً اجراشده، input/model hash، عمل و exit code، اثر/نتیجه/readback، دامنه، caveat، rollback، شاهد لازم. صفر external_effects به معنی «هیچ تغییر داخلی رخ نداد» نیست.

سه verdict جدا منتشر کن:

1. **QUALITY:** پاسخ با حافظه روی held-out و rubric از پیش ثابت بهتر شده یا نشده؛ داده واقعی.
2. **MEMORY:** تجربه/تصمیم معتبر بعد از restart/restore واقعاً بازیابی و در پاسخ مصرف می‌شود.
3. **CONTINUITY:** چرخه مفید بدون وابستگی اجرایی لپ‌تاپ در پنجره معتبر ≥24h با مخرج کارها و QA.

به‌علاوه هفت‌ردیفی capability matrix: NPU_RUN، NPU_CORRECTNESS، HEARTBEAT، AUTH، REAL_JOB، ROLE_SERVICE را جدا نشان بده. هیچ 7/7 از 6/7 یا heartbeat ساخته نشود. آماده‌شدن گزارش یا QA seal محدود، پذیرش کلی نیست. overall فقط با تکمیل معیارها و شاهد هم‌دامنه؛ در غیر این صورت OPEN/PARTIAL همراه next action دقیق.

گزارش فارسی کوتاه: چه قابلیت جدیدی واقعاً به کار افتاد؛ کدام receipt آن را ثابت می‌کند؛ چه چیزی هنوز UNKNOWN/NOT_RUN است؛ گام اجرایی بعدی چیست. در طول انتظار زمانی به کار مستقل ادامه بده. اگر ادامه به موعد آینده نیاز دارد، task/checkpoint موجود را پیدا کن؛ monitor تکراری نساز و بدون ابزار زمان‌بندی ادعای پیگیری خودکار نکن.

**فرمان نهایی به ایجنت:** از کار نیمه‌تمام واقعی ادامه بده. اختاپوس باید بدن خود را بشناسد، قابلیت‌ها را در تصمیم مصرف کند، کار مفید را با حافظه انجام دهد و نتیجه را بعد از اختلال به یاد بیاورد. برش کوچک ولی کامل را اجرا و اثبات کن، سپس دامنه را با همان قواعد افزایش بده.
