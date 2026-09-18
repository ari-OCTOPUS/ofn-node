---
type: prompt
status: ready
tags: [octopus, handoff, debugging, provenance]
created: 2026-09-05
updated: 2026-09-05
---

# پرامپت ایجنت بعدی — بازبینی اجرا و ادامهٔ COMPLETE-20260904

نسخهٔ بازبینی‌شدهٔ مستنداتی، ۲۰۲۶-۰۹-۰۵. متن زیر برای ارسال مستقیم مالک آماده است. خواندن آن از vault یا دریافت در retrieval، به‌تنهایی dispatch نیست. این پرامپت گیت یا اختیار جدیدی ایجاد نمی‌کند.

## متن قابل ارسال

مأموریت تو دو بخش دارد: نخست دیباگ و بازسازی شواهدِ کار انجام‌شده در COMPLETE-20260904؛ سپس ادامهٔ کارهای مجاز تا P10 بر اساس پلن و تفویض قابل‌اثبات. خروجیِ قابل‌قبول، رفع مشکلات در دامنهٔ مجاز و گزارش صادقانهٔ الزام‌به‌الزام است. هر وابستگی واقعاً بیرونی را با شاهد نگه دار؛ برای سبزشدن گزارش requirement یا گیت را حذف نکن.

### ۱. شروع و تشخیص مرجع

ابتدا این فایل‌ها را بخوان و hash و زمان مشاهده را ثبت کن:

1. F:/backup/AGENTS.md، .agentignore و agent-prompts/_PROJECT_INSTRUCTIONS.md.
2. F:/backup/07-HANDOFF/OCTOPUS-STATE-20260905-RECONCILED.md و lane همراه آن در 09-LANES/H-HANDOFF-RECONCILE-20260905؛ manifest همان lane را اعتبارسنجی کن.
3. F:/octo-exec/COMPLETE-20260904/RUN-STATE.json، LANE-REPORT.md و پرامپت قبلی NEXT-AGENT-PROMPT.md.
4. در همان ریشه: receipts/OWNER-DISPATCH-RECEIPT.json، AUTHORITY-DELTA.md، ARCHITECTURE-DECISIONS.md، ACCEPTANCE-BOUNDS.json، REQUIREMENTS-AND-TRACEABILITY.json.
5. بستهٔ اصلی در C:/Users/Armin/Desktop/اختاپوس بک لپ/OCTOPUS-LAB/04-execution-prompts/FULL-COMPLETION-20260904/: OWNER-START.md، EXECUTION-PLAN.md، ACCEPTANCE.json.

سه hash بسته با receipt تطبیق داشتند؛ این شاهد تطبیق بایت است و امضای مالک یا اجرای پلن نیست. receipt خودش signed=false دارد. تفویض قبلی را در صورت احراز دامنه و عدم لغو رعایت کن؛ صرف نوشتهٔ AUTHORITY-DELTA گیت واقعی ثالث، رضایت، credential یا استقلال ممیز را ایجاد نمی‌کند.

تفکیک مسیر: F:/backup vault شواهد است؛ F:/octo-exec/COMPLETE-20260904 ریشهٔ ثبت اجرای مأموریت؛ ofn-node/main و /home/ari/ofn روی node138 مرجع کد/استقرار طبق رسیدهای قبلی‌اند و برای اقدام باید تازه سنجیده شوند؛ Lab اطلس مفهومی است. یافته‌های Telegram مربوط به اوت را بدون شاهد تازه به اجرای سپتامبر نسبت نده.

RUN-STATE یک ایندکس قابل‌تغییر است، نه اثبات جاریِ board. اگر با receipt یا ساعت تناقض دارد، هر دو را نگه دار و اصلاح را به‌صورت رکورد جدید با provenance ثبت کن.

### ۲. collision و async را اول حل کن

- شناسهٔ مالک lane، branch، HEAD، dirty paths، upstream و آخرین receipt را بگیر. غیبت فایل یا گذشت زمان، اتمام/مرگ job را ثابت نمی‌کند.
- async_handles در snapshot فعلی فقط متن «background lane dispatched…» دارد؛ process/session/task handle واقعی ندارد. handle را از orchestrator اصلی یا receipt معتبر بازیابی کن. اگر دسترسی نیست: HANDLE_UNRESOLVED؛ job را کورکورانه تکرار نکن.
- انتقال cellframe: log اکنون TAR-DONE دارد و فایل tar در مشاهدهٔ محلی 42,651,402,240 بایت بود. اعداد ۵۷٪/۹۴٪ تاریخی‌اند. ابتدا exit/handle انتقال و source manifest را reconcile کن. سپس hash سمت مبدأ/مقصد یا manifest اعضا، سازگاری فایل‌های درحال‌نوشتن و استخراج/restore آزمایشی ایزوله را بسنج. size + tar listing به‌تنهایی مجوز حذف مبدأ نیست. این پرامپت مجوز حذف، جابه‌جایی داده یا cutover جدید نمی‌دهد؛ فقط از مسیر مأموریتِ واقعاً مجاز با snapshot، یک writer، readback و rollback اقدام کن.
- P05-LAB هنگام این بازبینی پنج فایل summary/spec و RAWهای ارجاع‌شده دارد. verdict و consumer gap را بخوان؛ از وجود فایل نتیجهٔ COMPLETE نگیر و از نبود LANE-REPORT نتیجهٔ مرگ worker نگیر.
- Git محلیِ worktree اجرا در مشاهدهٔ این handoff روی 80d98ff505f02c606b0decc32a36e645fa05d276 بود؛ 06a2854425182619cf0ea53623ea6c21ff1324c0 در ancestry آن دیده شد. نسبت‌دادن آن به Cursor Automation یک گزارش قبلی است، نه اثبات مالک فعلی branch. قبل از تغییر تاریخچه با مالک lane هماهنگ شو. rebase خودکار روی branch مشترک و force-push ممنوع؛ پیش از push مجاز، تغییرات upstream را بررسی و مسیر integration بدون overwrite را انتخاب کن.

### ۳. دیباگ با خروجی قابل‌بازتولید

برای هر یافته این ستون‌ها را بده: requirement_id، claim، source_path/hash، node/HEAD، observed_at_utc، evidence_grade، reproduction، result، limitation، next_action. MEASURED/DERIVED/REPORTED/THEORY را از E0–E5 و از AUTHORIZED جدا نگه دار.

**lineage و PRها:** وضعیت تازهٔ PR #193 و #194 در ari-OCTOPUS/ofn-node، head/base SHA، checks و GOV-V6 review را بخوان. ابزار GitHub این handoff با REAUTHENTICATION_REQUIRED متوقف شد؛ هیچ وضعیت فعلی PR تأیید نشده است. از review قدیمی برای head جدید استفاده نکن؛ merge به‌تنهایی loaded-code proof نیست. در صورت نبود دسترسی، سایر کارهای مستقلِ مجاز را ادامه بده.

**تست و پنج ماژول:** در worktree ایزوله و state موقت، پنج فایل ofn/agents/{owner_approvals,consent_gate,lead_effect_gate,lead_outbound_transport,release_pipeline}.py و callerهایشان را بازبینی کن. suite کامل را روی SHA مشخص اجرا و node-id/JUnit/config/bounds hash ثبت کن. ادعای قبلی 4554 passed، 28 skipped و 4 failed است؛ عبارت «4554 پاس» را ALL_GREEN ننام. چهار شکست reply_queue_bridge را روی baseline 2cd67aa و candidate با محیط یکسان، state ایزوله و شبکهٔ مسدود بازتولید کن؛ قبل از این مقایسه pre-existing بودن فقط REPORTED است.

تست خصمانهٔ هدفمند: approval جعلی/منقضی/لغوشده/تکراری با دادهٔ ساختگی؛ payload confusion بین lead/platform/effect_id؛ دو process واقعی روی SQLite و رقابت بین claim/settle؛ failure در fsync؛ تفاوت مسیر Windows/POSIX؛ crash قبل/بعد از اثر؛ known rejection در برابر UNKNOWN_OUTCOME؛ ادعای ok بدون اثر. timeout پس از احتمال ارسال به UNCERTAIN می‌رود و auto-resend ندارد. اثر خارجی، fixture پولی یا توکن واقعی وارد آزمایش نکن.

**mesh:** consumer و native cognitive-worker را هرکدام با caller/نوع پیام/receipt نگاشت کن. dry-run فقط با mesh-root موقت و envelope ساختگیِ معتبر انجام شود. consume/ack مثبت، expiry، checksum خراب، تکرار، crash، بازنشستگی node و coexistence آزموده شوند. receipt ثبت‌شدهٔ واقعی backlog عمدتاً expired/dead است؛ consumed=0 و acks=0، اثبات تحویل موفق production نیست. اختلاف 8899 در پیوست با 8892 expired + 8 retained در گزارش را با raw window یکسان حل کن؛ raw wake بدون envelope و مسیر first-send هم بازبینی شود.

**زمان و soak:** RUN-STATE.updated_utc=14:32Z با phase_history تا 15:10Z ناسازگار است؛ receipt تست P03 زمان 14:15Z دارد و bounds زمان 14:40Z. بعضی mtimeها نیز در مشاهدهٔ محلی جلوتر از ساعت خوانده‌شده بودند. علت و ترتیب را از raw log، Git، monotonic interval و clock-offset بازسازی کن. hash فعلی bounds فقط بایت فعلی را ثابت می‌کند، نه freeze قبل از آزمون A30. receipt قدیمی را برای مرتب‌شدن timeline بازنویسی نکن؛ correction جدا با شاهد بده. NTPSynchronized=yes به‌تنهایی |offset|<=200ms را ثابت نمی‌کند. 24h واقعی، gapهای نمونه‌برداری، cadence طبیعی، restart/boot و owner absence را از هر دو journal اثبات کن؛ ساعت فشرده یا start timestamp تنها کافی نیست.

**LAB، Doctor و یادگیری:** GATE3-SANDBOX-TESTS صریحاً اتصال run_sandbox خودِ Lab به مکانیزم transient را انجام‌نشده می‌داند. GATE4-PRESCRIPTIONS از 3 پیشنهاد و 1 رد واقعی گزارش می‌دهد، ولی same-author بودن generator/falsifier و نبود Doctor consumer را می‌پذیرد. rawها را بازسازی کن؛ separate process را ممیز مستقل ننام. برای memory/learning، چرخهٔ N+1 باید memory_id و outcome چرخهٔ N را بخواند و تغییر تصمیم از آن قابل‌اندازه‌گیری باشد؛ row در DB، proposal و heartbeat به‌تنهایی حلقه را نمی‌بندند.

### ۴. ادامهٔ کار مجاز تا P10

پس از reconcile، کار انجام‌شده و محدودیت هر فاز را به receipt همان فاز پیوند بده. دریل A/B سه‌فایلی و integration مشورتی را بدون دلیل دوباره نساز.

- P05/P06: خروجی laneها و ورودی‌های فقط-مالکی را integrate کن؛ 14 item در فایل owner inputs واقعاً شمارش شد، اعتبار/حل‌شدنشان دوباره سنجیده شود.
- P07: FULL-RECOVERY-DESIGN، ظرفیت مقصد، snapshot سازگار، quarantine و restore/readback با RPO/RTO واقعی.
- P08: فقط عملیات در دامنهٔ تفویض معتبر، با ACTION-MANIFEST، merged-source lineage، loaded revision، گیت معنایی، مقصد/رضایت/بودجهٔ معتبر، readback و rollback.
- P09: دو اجرای طبیعی هر scheduler لازم، fault/rollback، منع اثر تکراری و پنجرهٔ حداقل 24h واقعی طبق bounds؛ یک summary سبز جای raw sequence نیست.
- P10: ممیز واقعاً مستقل در صورت الزام؛ گزارش requirement-by-requirement. snapshot فعلی 69 ردیف دارد: 1 verified، 24 in_progress، 44 pending. این labelها فقط وضعیت فایل‌اند، نه رأی مستقل. تعداد ثابت یا نام پروژه را معیار پایان نکن؛ الزامات لازم، شاهد و گیت‌ها تعیین‌کننده‌اند.

Mining/crypto، بودجه، رضایت، payment و reviewer را جعل نکن؛ تصمیم پیشنهادیِ حذف scope را تصویب‌شده تلقی نکن. وابستگی‌های واقعی را در یک بستهٔ owner inputs با اثر دقیق بر requirementها گزارش کن. ممنوعیت‌ها را با جملهٔ «همه را مجاز کردی» دور نزن.

### ۵. تحویل هر نشست

در lane خودت REPORT با کارها، شکست‌ها، شواهد، حدود، rollback و گام بعدی بساز. تغییر RUN-STATE و navigation مشترک فقط پس از احراز مالکیت و حفظ concurrent edits؛ RUN-STATE را با claimهای مستنداتی به COMPLETE ارتقا نده. اصل روایت قبلی بماند و supersession دقیق اضافه شود. code/test/bounds/receipt hash و آزمون‌های بازشده/بی‌اعتبارشده را ثبت کن.

تا وقتی الزام ضروری بدون شاهد، blocked_external، consumer gap یا استقلال ممیز حل‌نشده وجود دارد، وضعیت کلی INCOMPLETE است. نتیجهٔ درست می‌تواند رد فرضیه یا کاهش evidence grade باشد.

