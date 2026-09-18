# MEGAPROMPT-BRAIN-WIRING-SCAN — اختاپوس چند مغز دارد؟ سیم‌کشی‌ها کامل است؟ ۷ برد چه کم دارند؟

**GOV_VERSION=V8 · LADDER=L2 · Lane پیشنهادی: OCTOPUS-BRAIN-WIRING-SCAN-20260918**
**مأموریت: کالبدشکافی کامل «مغزها» و «سیم‌کشی‌ها» — و پاسخ عددی به این سؤال که کدام کدنویسی، بازدهِ ۷ برد را بالا می‌برد. تشخیص + اسپک اجرا؛ هیچ تغییری روی runtime.**

## ۰ — سه سؤال که مأموریت باید قطعی جواب بدهد
1. **چند مغز؟** (ریز و درشت): هر تولیدکنندهٔ inference/تصمیم — providerهای بیرونی، مغز محلی، لایه‌های decision-code، حافظه/یادگیری. برای هرکدام: چه کسی صدایش می‌زند، چند بار، چند دلار، چه چیزی برمی‌گرداند.
2. **سیم‌کشی‌ها کامل است؟** برای هر جفت producer→consumer در سه دامنهٔ «کسب‌وکار / ماژول / جعبه سیاه»: WIRED-LIVE · WIRED-DARK (سیم هست، مصرف‌کننده خاموش — نمونهٔ اثبات‌شده: JetStream با consumers=0) · DANGLING (تولیدکننده بدون مصرف‌کننده) · ORPHAN (مصرف‌کننده بدون تولیدکننده) · MISSING.
3. **۷ برد کدنویسی لازم دارند؟** برای هر برد: امروز چه چیزی اجرا می‌کند، چقدر بیکار است، و کدام کد (با اندازهٔ اثر تخمینی) بازدهش را بالا می‌برد.

## ۱ — قلمروها و سهمیه (قرارداد، نه آرزو)

| قلمرو | حداقل | چرا مشکوک است (دلیل وجودی) |
|---|---|---|
| B1 فهرست مغزها (بیرونی/محلی/decision-code) | ۲۵ مغز | لایه‌بندی واقعی ناشناخته است: broker پیش‌فرض `sakana-fugu` است و مسیر `local-insufficient` وجود دارد؛ هم‌زمان چند لایهٔ decision-code (ops_agent، cognition_factory، self-model، deep-scan، glass، money_executor، b2b_discovery، revenue-loop) هرکدام «مغز» کوچکی‌اند |
| B2 بودجه/مدل هر مغز | ۱۵ ردیف | دفتر `api-budget/budget-ledger.jsonl` (۸۹ ردیف، $۰.۸۹ در ماه) مدل/هزینه را ثبت می‌کند؛ نگاشت مغز→هزینه/روز باید استخراج شود |
| W1 سیم‌کشی کسب‌وکارها | ۲۰ یال | چهار کسب‌وکار (نقاشی B2B، زیمن، استودیو، CRM/call-log) — قیف نقاشی با ۹۱ سرنخ مجاز و ارسال صفر از ۰۹-۱۶، فروشگاه با ۴۸۲ بررسی صفر-سفارش |
| W2 سیم‌کشی ماژول‌ها | ۲۵ یال | F-024: از ۵۰ سیم گم‌شده فقط ۲ رفع شد؛ پکیج `ofn/enrichment/` تازه merge شد و reader برای `v_account_last_call` وجود ندارد |
| W3 سیم‌کشی جعبه‌سیاه‌ها | ۱۵ یال | `cognition_factory`، `self-model/organism-shadow`، glass/owner-path، NATS/fleet-bus، scheduler، TCB — برای هرکدام: ورودی/خروجی/مصرف‌کننده |
| N1 ظرفیت ۷ برد | ۷ ردیف کامل | نقش‌ها معلوم است (۱۳۸ Revenue Engine، ۱۸۲ Witness، ۱۶۰ Shadow-Verify، ۱۸۰ Telemetry، ۱۹۳ Research، ۱۰۰ Coding/Sandbox، ۱۱۴ Hardware) ولی بار: ۱۳۸ حدود ۱.۰-۱.۵ و بقیه ۰.۰-۰.۰۵ → پنج برد عملاً بیکار |
| N2 کارهای staged-but-not-installed | ۱۵ مورد | F-003: units آمادهٔ evaluator(114)+ingestion(160) نصب نشده؛ F-018 گام فیزیکی مالک؛ سرویس‌های unwired (F-076) |
| N3 اسپک افزایش بازده | ۲۰ آیتم | هر آیتم: کد مشخص، برد هدف، اثر عددی تخمینی، هزینه، Class A/B، نیاز به رأی مالک؟ |
| G بافر/بدهی نو | ۱۵ مورد | هر چیز تازه‌ای که در اسکن پیدا شد و در رجیستر فعلی نیست |

جمع: **~۱۵۲ ردیف**. هر ردیف با anchor سطح ۱/۲.

## ۲ — بذرهای لنگرشده (همه باید دوباره راستی‌آزمایی شوند؛ حافظه/چت = سطح ۵ = ممنوع‌الاستناد)

| # | فرضیه | شاهدِ فعلی برای شروع |
|---|---|---|
| S1 | حداقل ۵ برد از ۷ عملاً بیکارند | پالس‌ها: load1 نودها ۰.۰-۰.۰۵ در برابر ۱۳۸ ~۱.۰-۱.۵ (`06-EVIDENCE/FLEET-HEARTBEAT-CANONICAL.md`) |
| S2 | NPUها صفر مصرف دارند | F-056: «NPU capacity unmeasured/unused; zero consumers» + `138 row NOT_RUN` |
| S3 | سیم‌کشی‌ها به‌شکل سیستمیک ناقص‌اند | F-024 (۵۰ گم‌شده، ۲ رفع)، F-042 (consumers=0)، F-076 (unwired services) |
| S4 | مسیر خطا/رخداد برخی سرویس‌ها به مسیر ناموجود می‌نویسد | `state/legs/` روی ۱۳۸ وجود ندارد ولی glass در خطا آنجا می‌نویسد (اثبات این جلسه) |
| S5 | لایهٔ decision-code چند مغز موازی دارد بدون هم‌مرجعی | ops_agent (`consume_decisions`)، `cognition_factory`، `self-model/organism-shadow`، `deep_scan_tick`، glass/owner-path |
| S6 | broker چند provider دارد ولی مسیر انتخاب/فیل‌اوور تازه است | `api_budget.py` (multiprovider + provider-failover 09-17)، پیش‌فرض `sakana-fugu`، مسیر `local-insufficient` |
| S7 | مغز محلی (رایگان) کم‌استفاده است | مسیر `local-insufficient` در دفتر بودجه ثبت می‌شود؛ llama/ollama روی بردها وجود نامعلوم |
| S8 | کسب‌وکارها سیم «پاسخ مشتری» ندارند | آلارم پاسخ فقط از ۰۹-۱۸ زنده شد؛ قبلش پاسخ‌ها تا چرخهٔ ۶ ساعته دیده نمی‌شدند (F-019) |
| S9 | CRM/call-log تازه merge شده ولی reader ندارد | `v_account_last_call` خوانده نمی‌شود (پیام الهه) |
| S10 | digest/enrichment تازه merge شده‌اند و باید سیم‌کشیشان سنجیده شود | #259+#260 merged 2026-09-18 (`88840181`, `3d74b757`) |

## ۳ — روش (انضباط اجباری)
1. **فقط خواندن.** runtime دست‌نخورده؛ اگر پیشنهادی نیاز به تغییر دارد، در THROUGHPUT-PLAN می‌نشیند نه در این مأموریت.
2. هر ردیف: `producer` / `consumer` / `trigger` / `file+line` / `last_observed` (زمان واقعی از دفتر/لاگ) / `state`.
3. **طبقه‌بندی یال:** برای هر یال یک «شاهدِ اثبات» بده (خطی که ثابت کند مصرف‌کننده وجود دارد یا ندارد). یال بدون شاهد → quarantine.
4. اعداد فقط از دفتر/لاگ/سیستم؛ تخمین‌ها `status: estimated`؛ تناقض = هر دو مقدار با `resolution: null`.
5. برای هر مغز: `calls/day` را از دفتر بودجه یا لاگ شمارش کن، نه حدس.
6. برای هر برد: بار، دیسک، سرویس‌های فعال، units نصب‌نشده، و ظرفیت بیکاری که *قابل استفاده* است.

## ۴ — خروجی‌ها (همه اجباری)
| فایل | قالب | محتوا |
|---|---|---|
| `BRAIN-CENSUS.json` + `.md` | JSON+MD | هر مغز: نام، نوع (external/local/decision-code/memory)، provider/model، callerها، calls/day، هزینه/روز، ورودی/خروجی، شاهد |
| `WIRING-MATRIX.csv` | CSV | `edge_id, domain(business/module/blackbox), producer, consumer, trigger, state(WIRED-LIVE/WIRED-DARK/DANGLING/ORPHAN/MISSING), proof_path, last_observed` |
| `BOARD-CAPACITY.md` | MD | جدول ۷ برد: نقش، بار، سرویس‌ها، بیکاری قابل‌استفاده، محدودیت‌ها (eMMC/کارت/برق) |
| `THROUGHPUT-PLAN.md` | MD | ۲۰ آیتم رتبه‌بندی‌شده: کد لازم، برد، اثر تخمینی، هزینه، Class A/B، نیاز به رأی مالک؟ |
| `GAP-REGISTER.json` | JSON | هر یافتهٔ تازه با id (`BW-###`)، حکم، شاهد، state |
| تزریق به لجر | رسید | GAP-REGISTER با `--import-seed` به `138:state/deep-scan/seed/` + شمار صریح import |
| `LANE-REPORT.md` | MD | + rollback (همه additive) |

## ۵ — معیار پایان
1. `BRAIN-CENSUS` ≥۲۵ مغز با caller و calls/day شاهددار.
2. `WIRING-MATRIX` ≥۶۰ یال؛ هر یال با شاهد؛ صفر یال بی‌طبقه‌بندی.
3. `BOARD-CAPACITY` هر ۷ برد کامل (بار اندازه‌گیری‌شده + units نصب‌نشده).
4. `THROUGHPUT-PLAN` ≥۲۰ آیتم رتبه‌بندی‌شده با اثر عددی تخمینی و برچسب Class.
5. صفر ادعا بدون anchor؛ quarantine گزارش‌شده.
6. اعتبارسنج‌ها با شمار صریح + CJK-clean + LANE-REPORT.

## ۶ — مرزهای سرخ و تله‌های شناخته‌شده
- runtime فقط‌خواندنی · secrets فقط نام · هیچ فلگ/دروازه‌ای تغییر نمی‌کند · لین R1 و لین‌های فعال لمس نمی‌شوند.
- تله‌ها (هرکدام قربانی گرفته): ssh+heredoc (فایل را با `cat >` بفرست) · `pgrep` خودش را match می‌کند · CRLF هش را می‌شکند · **`git show :N:path > path` وقتی stage نباشد فایل را صفر بایت می‌کند** · هر push تأییدهای PR را باطل می‌کند · دو CURRENT-TRUTH زنده (mtime) · `state/legs/` ممکن است نباشد · کارت‌های مالک فقط با تپ/متن معتبر ثبت می‌شوند.
- برای سنجش بار نودها: پالس‌های heartbeat (نه load من)؛ و NPU روی RK3588 یک دستگاه DRM است نه `/dev/rknpu` (F-056 + تلهٔ ثبت‌شده).

## ۷ — نقطهٔ شروع
1. `06-EVIDENCE/FLEET-HEARTBEAT-CANONICAL.md` (نقش‌ها و بار ۷ برد)
2. `138:state/deep-scan/findings-current.json` (۵۷۳ ردیف؛ شامل ۲۴۶ ردیف WHY-SLOW تازه)
3. `138:state/api-budget/{api_budget.py,budget-ledger.jsonl}` (مغزهای پولی + مسیر انتخاب provider)
4. `09-LANES/OCTOPUS-WHY-SLOW-250-20260918/` (تشخیص قبلی؛ یال‌های شکستهٔ قیف/مالک)
5. `138:state/ops-agent/ops_agent.py` (decision-code اصلی) + `state/cognition/cognition_factory.py` + `state/self-model/`
6. `git log --oneline -15` روی `ari-OCTOPUS/ofn-node` (mergeهای تازه: #259/#260) و `README`/`docs/` برای نقشهٔ ماژول‌ها

*نوشته 2026-09-18 برای سپردن به ایجنت بعدی — این مأموریت تشخیصِ نقشه است: چند مغز، کدام سیم، و کدام کد بازده بردها را بالا می‌برد.*
