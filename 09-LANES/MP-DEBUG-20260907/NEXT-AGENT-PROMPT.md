---
type: prompt
status: ready
tags: [octopus, handoff, debug]
updated: 2026-09-07
---

# دستور ادامهٔ ایجنت بعدی — از شواهد تازه، نه از PASS قبلی

این متن برای ادامه در دایرکتوری است؛ به‌خودی‌خود مجوز اثر بیرونی نیست.

## ابتدا بخوان

1. `F:/backup/AGENTS.md` و ورودی مهندسی مناسب؛ `ENGINEERING-ENTRYPOINT-20260906.md` نسبت به ۹/۴ جدیدتر است، ولی بعضی وضعیت‌ها/محدودیت‌های آن با v3 و ACK جدیدتر کهنه شده‌اند. جدیدبودن تاریخ، اختلاف دامنه یا امضای لازم را حذف نمی‌کند.
2. `C:/Users/Armin/Downloads/MEGAPROMPT-OCTOPUS-v3-EXECUTABLE-2026-09-07.md`؛ SHA256=`ca736a4724ddac884fd39108dc6089e907fba6f1439ba61ff71cc7681cdaa4e3`.
3. `F:/backup/09-LANES/MP-DEBUG-20260907/DEBUG-REPORT.md`، سپس `LANE-REPORT.md`، `TEST-RECEIPT.json` و رسیدهای تازهٔ همین پوشه.

## نقطهٔ واقعی توقف

- EX1 مطابق متن اصلی v3 پذیرفته نشده است. دو رکورد واقعی‌اند و prefix با fingerprint قبلی برابر است، اما فیلدهای خام لازم غایب‌اند و journal پیاده‌شده hash-chain نیست. دستور اصلی on_fail توقف می‌خواست. هیچ receipt-level field را به‌عنوان provenance تاریخیِ خود رکورد جا نزن.
- EX2 در `F:/wt-mp-exec-ex1-ex2-20260907` در commit `ba5d239fa7764d96a4694a7b8b347059aea18d29` baseline بررسی‌شده است. آن مسیر را تغییر نده.
- candidate دیباگ‌شده در `F:/wt-debug-mp-ex1-ex2-20260907`، branch=`codex/debug-mp-ex1-ex2-20260907` است؛ **تغییرات محلی هنوز commit/push/deploy نشده‌اند**. HEAD همان base است؛ هویت candidate از patch + پنج هش TEST-RECEIPT گرفته می‌شود، نه HEAD تنها.
- ۱۶۵ تست منتخب بدون skip/deselect سبزند: ۱۴ قرارداد، ۱۲ F1، ۱۲ adapter، ۱۲۷ regression جدید. سه گروه اصلاح: ارجاع/عدد نامعتبر، serialization بدون تغییر نوع/متن/Unicode، و parity مستقیم مولد. قفل قبلی F1 دست‌نخورده است.
- این سبزی نه EX1 را قبول می‌کند، نه خروجی witness را حل می‌کند، نه نقص قدیمی RuntimeTruthRow را رفع می‌کند. جهت مولد هنوز Python→YAML است؛ v3 عکس آن را خواسته. آن deviation باز است.

## نخستین کار مجاز بعدی

ابتدا محدودیت EX1 را به یک پیشنهاد اصلاح معیارِ صریح تبدیل کن: «چه چیزی دربارهٔ دو رکورد قدیمی واقعاً قابل اثبات است»، «چه چیزی برای همیشه UNKNOWN می‌ماند»، و «برای تصمیم‌های آینده چه provenance باید در زمان تصمیم ثبت شود». پیشنهاد را از تصویب و از اجرای آن جدا نگه دار. اگر گذر از on_fail نیاز به تغییر work order دارد، یک سؤال کوتاه از مالک بپرس و منتظر جواب بمان؛ خودت PASS یا waiver نساز. نگه‌داشتن candidate محلی اشکالی ندارد، ولی EX3 روی پایهٔ ظاهراً سبز شروع نشود.

قبل از هر ادغام مجاز، تبار را حل کن: HEAD مشاهده‌شدهٔ ۱۳۸ `a1f0fa8061fd6b7529ba6c37f7ddb0032a4ed546` با merge کامیت PR224 یعنی `b8340d0e757a7563583d99672b2912c30db03af3` در GitHub diverged بود (head دو ahead، هفت behind، merge-base=`1b53773a47b6af71b8b643df61cfa13454cd1340`). این graph، برابری working tree یا RAM را نمی‌سنجد. هیچ rebase، overwrite شش تغییر tracked ناشناخته، restart یا deploy خودکار انجام نده.

## ترتیب ادامه پس از رفع صریح مانع

1. اختلاف جهت مولد EX2 را مطابق work order حل کن یا مصوبهٔ تغییر طراحی را جدا ثبت کن؛ تست‌های round-trip/parity و قفل را حفظ کن. روی برد dependency اضافی لازم نیست اگر generation محلی و runtime stdlib باشد.
2. verifier واقعی و شاهدِ حل outcome را از شرح truth_source جدا کن. C3 به snapshot قفل/cap در همان decision نیاز دارد؛ lock فعلی را به زمان گذشته تعمیم نده.
3. EX3: انتخاب دوزمانی روی همان records و knowable set واقعی؛ event_time/record_time/as_of/scope/supersedes/read_snapshot؛ آزمون ترتیب و replay با timestamp واقعی. تا اثبات، TAIL_ORDER_SENSITIVE=true طبق v3؛ هیچ reorder تاریخ یا زمان جعلی برای سبزشدن.
4. EX4: S1 شامل هر mint یا deny واجدشرط است. eligibility قبل از calibration تعریف شود؛ شمار، denominator، UNDERPOWERED و CI طبق سند؛ telemetry را با بهبود هوش یکی نکن.
5. EX5: denial taxonomy برای threat/no_valid_data/legitimate_deny/tail bug/starvation؛ نه شل‌کردن guard یا افزایش cap.
6. EX6: دو consumer واقعی یعنی دو decision point متمایز با اثر روی تصمیم بعدی در همان ledger؛ کپی فایل، داشبورد، store دوم یا import اضافه کافی نیست.
7. EX7: فقط مسیر پول ازپیش‌انتخاب‌شده و شرایط شش‌گانهٔ تسویه. CHECKOUT-1 self-buy لغوشده است؛ دوباره مطرح/اجرا نکن. انتخاب PayPal Invoice، family fulfillment و توقف mining/accounting را دوباره تصمیم‌گیری نکن. API credit، dispatch، order و VERIFIED_CASH را جدا نگه دار.

## وضعیت تازه را دوباره کهنه نکن

- PR224 اکنون merge است؛ شرط قدیمی «منتظر PR باز» را تکرار نکن. read GitHub موفق بود؛ push authorization آزمایش نشده.
- ofn.service در ساعت ثبت‌شده فعال و از ۲۰۲۶-۰۹-۰۶ ۲۲:۲۲:۱۱ UTC شروع شده؛ loaded revision هنوز UNKNOWN. زمان شروع جدید، دستور restart تازه نیست.
- ۱۸۰: alias تنظیم‌شده `root`، سرویس مدل و listener یک PID، ctx=8192. این ثابت نمی‌کند مدل جواب درست می‌دهد یا actor تغییر معلوم است. هیچ generation/تعویض مدل در این lane اجرا نشده.
- ۱۸۲: board182 resolve نشد؛ خاموش یا retired نتیجه نگیر. برای probe از target قبلاً تأییدشده استفاده کن؛ IP/user یا secret نساز/نخوان.
- calibration تازه در ۴۳۲۶ رکورد، ۲۱۵۶ outcome unresolved با عدد خطا دارد. این co-presence را ثبت کن؛ قرارداد جدید هنوز آن داده را اصلاح نکرده. outcome_evidence در دو outcome آخر موجود بود ولی محتوایش در این خواندن بررسی نشد؛ فقدان همهٔ شواهد را هم ادعا نکن.
- actor تغییر ctx، مالک پورت 9101 روی۱۸۲، loaded code، S2 علمی، S3 درآمد، دو decision consumer و سلامت کل ارگانیسم هنوز شاهد کافی ندارند.

## قواعد پایان

هر ادعا node/path/revision/window/method/receipt خودش را داشته باشد. مدل ارگانیسم را حفظ کن: signal→producer→state→consumer→authority→effect→receipt→outcome→next decision. read-only، patch، candidate_ready، deployed و live_verified را جدا بنویس. نوت‌ها و رسیدهای قبلی append-only در معنا هستند؛ rollback هرگز حذف evidence lane نیست. دریل A→B، اسکن همهٔ vault، transfer قدیمی و پروژه‌های پارک‌شده را برای پرکردن پیشرفت دوباره اجرا نکن. نتیجه را در lane متعلق به خودت و یک handoff محدود Obsidian ثبت کن؛ هیچ سرویس/تایمر/مدل/secret/gate را از روی این prompt تغییر نده.
