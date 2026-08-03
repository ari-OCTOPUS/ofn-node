# Brushline — کاتالوگ کامل توانایی‌ها و کارایی سیستم
**تاریخ:** 2026-07-02 | **مبنا:** کد واقعی `60_code/` (نه طرح، نه وعده) | **وضعیت:** P1–P9 کامل، ۱۱ فایل تست سبز

> این سند جواب یک سؤال است: **«این سیستم الان، همین امروز، دقیقاً چه کارهایی می‌تواند بکند؟»**
> هر قابلیت با ماژول پشتیبانش آمده. بخش آخر صادقانه می‌گوید چه چیزهایی *نمی*‌تواند.

---

## ۰. در یک پاراگراف

Brushline یک **سیستم چندعاملی (multi-agent) بازاریابی و مدیریت سرنخ برای کسب‌وکار نقاشی ساختمان در سیدنی** است.
ورودی‌اش enquiry مشتری، ریویو، و دستور اپراتور است؛ خروجی‌اش **پیش‌نویسِ** پیام، پاسخ ریویو، صفحه‌ی suburb،
پست GBP/شبکه اجتماعی، و sync سرنخ به CRM است — و **هیچ خروجی‌ای بدون تأیید انسانی ارسال/منتشر نمی‌شود.**
همه‌چیز از تلگرام کنترل می‌شود، هر سنت هزینه سقف و لاگ دارد، و هر رویداد در یک زنجیره‌ی audit
دست‌کاری‌ناپذیر ثبت می‌شود.

---

## ۱. جریان‌های کامل end-to-end (چه کارهایی را از اول تا آخر انجام می‌دهد)

### 1.1 پاسخ سریع به سرنخ جدید (speed-to-lead) — هدف: زیر ۱۵ دقیقه
`orchestrator.intake_enquiry(raw_enquiry)`
1. **ثبت سرنخ:** Worker F سرنخ را با نام/تلفن/suburb/نوع کار در DB ذخیره می‌کند (PII فقط در DB، هرگز در audit).
2. **پیش‌نویس با Haiku:** Worker C اولین پاسخ را می‌نویسد — گرم، محلی، زیر ۹۰ کلمه، یک سؤال شفاف‌کننده،
   دعوت به quote رایگان؛ بدون هیچ ادعای اثبات‌نشدنی (ACL s29). اگر API در دسترس نباشد → template سازگارِ آماده.
3. **footer قانونی خودکار:** نام کسب‌وکار + ABN + «Reply STOP to opt out» (Spam Act 2003).
4. **Gate:** بررسی compliance (بخش ۳).
5. **صف تأیید:** کارت تلگرام با دکمه‌های Approve/Edit/Reject؛ priority=critical، SLA=۱۵ دقیقه.

### 1.2 پاسخ به ریویو (مثبت یا منفی)
`orchestrator.kickoff_review_response(review, platform)`
- Worker B با Haiku **sentiment ریویو را تشخیص می‌دهد** (positive/negative/neutral + score + تم‌های کلیدی).
- ریویو منفی → SLA پاسخ **۲ ساعت** و priority=high.
- Worker C پاسخ عمومی می‌نویسد (بدون opt-out چون پیام مستقیم نیست؛ با نام+ABN)؛ متن ریویو به‌عنوان
  «داده» تیمار می‌شود نه «دستور» (prompt-injection guard).
- Gate + صف تأیید مثل همیشه.

### 1.3 تولید صفحه‌ی suburb برای SEO محلی
`orchestrator.kickoff_suburb_page(suburb, service)`
- Worker A (Serper، geo=AU) تحقیق suburb/رقبا/کلیدواژه را جمع می‌کند — read-only و source-labelled.
- Worker C با **Sonnet** (مدل قوی‌تر برای کپی high-value) صفحه را می‌نویسد؛ superlative های رقبا را کپی *نمی*‌کند.
- Gate این‌جا **دولایه** است: اسکن deterministic + **semantic ACL با Sonnet** که ادعای ظریف
  اثبات‌نشده («trusted by thousands») را هم می‌گیرد (~AUD $0.016/draft، فقط روی draftهای پرریسک).

### 1.4 پست Google Business Profile و شبکه‌ی اجتماعی
`orchestrator.kickoff_gbp_post(content)` / `channel.draft_social_post(...)`
- Worker E پست را با CTA فرمت می‌کند → Gate → صف.
- **publish فقط بعد از APPROVE ممکن است** و در MVP فعلی حتی آن هم preview برمی‌گرداند
  (`live_posted=False`) — تا OAuth واقعی GBP وصل شود هیچ مسیر کدی به پست زنده وجود ندارد.

### 1.5 پیگیری روز ۲ / ۵ / ۱۰ (follow-up)
`orchestrator.kickoff_followup(lead_id, day)` — تکی، یا **دسته‌ای با ۵۰٪ تخفیف:**
`kickoff_followup_batch(jobs)` → submit به Message Batches API → بعداً `collect_followup_batch(batch_id)`
→ هر draft باز از Gate و صف می‌گذرد. آیتم شکست‌خورده در batch → template fallback (هیچ پیگیری گم نمی‌شود).
لحن هر روز فرق دارد: روز۲=سؤال، روز۵=تعدیل scope/بودجه، روز۱۰=خداحافظی محترمانه بدون فشار.

### 1.6 ثبت رضایت (consent) و sync سرنخ به CRM
`lead_capture.record_consent(lead_id, method, evidence)` → مدرک consent با روش (express/inferred) ثبت می‌شود.
`orchestrator.sync_lead(lead_id, target, operator_chat_id)` → push به **ServiceM8 یا Tradify**:
- **بدون ConsentRecord → قطعاً بلاک** (SyncBlocked + ثبت در audit).
- فقط اپراتورِ allow-list شده می‌تواند trigger کند (fail-closed).
- payload محدود به whitelist ۸ فیلدی: name, phone, email, suburb, service_type, source_channel, consent_status, notes — هیچ‌چیز دیگر هرگز خارج نمی‌شود.
- بدون API key → **dry-run** (تمرین امن، بدون شبکه)؛ با key → retry+idempotency (رکورد تکراری در CRM ساخته نمی‌شود).

### 1.7 تحقیق بازار on-demand
Worker A: جست‌وجوی suburb/competitor/keyword/pricing (Serper، free tier 2500 query/ماه)؛
Worker B: شاخص فصلی تقاضا per suburb/month. هر دو read-only.

---

## ۲. رابط اپراتور — تلگرام (تنها UI؛ تک‌اپراتور)

| فرمان/دکمه | کار |
|---|---|
| `/queue` | کارت‌های در انتظار تأیید با دکمه‌های واقعی Approve/Edit/Reject؛ مرتب بر اساس priority+قدمت؛ SLA های گذشته خودکار escalate |
| **Approve** | draft آماده‌ی publish/send/sync می‌شود |
| **Edit** | پیام بعدی‌ات متن جدید می‌شود؛ تغییر ماهوی → **REGATE** (دوباره از Gate می‌گذرد؛ اگر flag خورد دوباره صف می‌شود — ویرایش انسانی هم نمی‌تواند ادعای خلاف را قاچاق کند) |
| **Reject** | با دلیل اجباری؛ ثبت دائمی |
| `/spend` | خرج امروز به AUD، سقف‌ها، تعداد رویداد، وضعیت kill switch |
| `/kill` | **توقف فوری همه‌ی اکشن‌های بیرونی** — هر شش نقطه‌ی خرج بلافاصله می‌ایستند |
| `/kill_off` | ازسرگیری |
| `/status` | سلامت سیستم: kill switch، صحت زنجیره‌ی audit، خرج، تعداد pending |

**امنیت:** فقط chat-id های `ALLOWED_OPERATOR_CHAT_IDS` — هم روی پیام هم روی دکمه؛ غریبه silent-reject
می‌شود و تلاشش با hash پایدار در audit می‌نشیند.

---

## ۳. توانایی‌های compliance و ایمنی (Gate + سه invariant)

**هر draft قبل از صف، خودکار چک می‌شود:**

| چک | قانون | نتیجه |
|---|---|---|
| Superlative scan (deterministic، رایگان) | ACL s29 | «best/cheapest/guaranteed/#1/...» → SOFT_FLAG |
| Semantic ACL (Sonnet، فقط draft پرریسک) | ACL s29 | ادعای ظریف اثبات‌نشده → SOFT_FLAG |
| Consent | Spam Act 2003 | پیام مستقیم بدون consent → **HARD_BLOCK** |
| Opt-out | Spam Act 2003 | پیام مستقیم بدون STOP → **HARD_BLOCK** |
| Sender ID | Spam Act | خروجی بدون ABN → **HARD_BLOCK** |
| PII pattern | Privacy/INV-2 | موبایل/ایمیل خام در متن → SOFT_FLAG |
| تمایز direct/public | Spam Act | پاسخ عمومی ریویو: consent/opt-out لازم ندارد، ABN/ACL چرا |

HARD_BLOCK → اصلاً وارد صف نمی‌شود؛ SOFT_FLAG → صف می‌شود ولی flag روی کارت دیده می‌شود.

**سه invariant که در کد enforce می‌شوند (نه فقط روی کاغذ):**
- **INV-1:** هیچ publish/send/sync بدون تأیید انسان — publish بدون ApprovalAction تأییدشده، exception می‌دهد؛ انقضای SLA هرگز auto-approve نمی‌کند؛ تست دارد.
- **INV-2:** PII هرگز در audit — فیلدهای phone/email/name خودکار hash-ref می‌شوند؛ sync فقط با consent؛ تستِ اسکن کل audit دارد.
- **INV-3:** هر اکشن بیرونی اول از `check_and_enforce` می‌گذرد — kill switch + سقف per-action (AUD $5) + سقف روزانه (AUD $20) — روی هر ۶ نقطه‌ی خرج، شامل هر تلاش retry.

**Audit chain:** هر رویداد (دریافت enquiry، هر Gate check، هر تصمیم اپراتور، هر sync، هر retry، هر batch)
یک entry با hash زنجیر به قبلی — تغییر یک بیت در گذشته، کل زنجیره را قرمز می‌کند (`verify_chain` در `/status`).

---

## ۴. توانایی‌های هزینه و مقاومت (زیر کاپوت)

- **مدل ارزان-اول:** Haiku برای پیام‌ها (~$0.004/draft)، Sonnet فقط برای کپی high-value و semantic ACL؛ Opus عمداً خاموش.
- **Prompt caching سیم‌کشی‌شده:** بلوک system ثابت با `cache_control` — تا ۹۰٪ ارزان‌تر روی توکن تکراری وقتی بلوک از حد minimum کش API بزرگ‌تر باشد؛ هزینه‌ی *واقعی* پس از تخفیف (نه تخمین) در cost_events می‌نشیند.
- **Batch ۵۰٪:** پیگیری‌های غیرفوری دسته‌ای؛ تخفیف در حسابداری لحاظ می‌شود.
- **Retry هوشمند:** خطای گذرا (429/5xx) → exponential backoff + jitter + احترام به Retry-After؛ **idempotency key** یعنی retry هرگز draft/charge/رکورد CRM تکراری نمی‌سازد؛ هر retry در audit.
- **گزارش لحظه‌ای:** `/spend` همیشه جمع دقیق امروز به AUD (نرخ ۱.۴۵ ثابت از config).
- **Fallback در همه‌ی مسیرها:** بدون هیچ API key، کل سیستم offline کار می‌کند (template/stub/dry-run) — برای تمرین و تست امن.

---

## ۵. داده — چه چیزهایی را نگه می‌دارد

SQLite جدا از هر سیستم دیگر (`brushline.db`، WAL): سرنخ‌ها (تنها جای PII)، مدارک consent،
همه‌ی draftها با هزینه/توکن/مدل، نتایج Gate، تصمیم‌های اپراتور با SLA/priority، sync jobها با id خارجی
CRM، رویدادهای هزینه (USD+AUD)، و زنجیره‌ی audit. همه index دار؛ pool اتصال per-thread با rollback امن.

---

## ۶. صادقانه: چه کارهایی *نمی*‌کند (هنوز)

| نمی‌کند | وضعیت |
|---|---|
| **ارسال واقعی SMS/email بعد از تأیید** | بزرگ‌ترین شکاف go-live؛ پیشنهاد P11 (Worker G — Sender) در سند بازبینی |
| پست *زنده* به GBP/اینستاگرام | preview-only تا OAuth واقعی؛ عمداً (INV-1) |
| اجرای خودکار زمان‌مند (follow-up روز ۲/۵/۱۰، escalation، جمع batch) | منطقش هست ولی scheduler ندارد — الان با `/queue` یا فراخوان دستی trigger می‌شود؛ در P10 |
| تصویر (before/after، brand overlay) | Worker D فقط اسکلت stub |
| ارزیابی Capital Works استراتا | stub |
| sync زنده‌ی تست‌شده با ServiceM8/Tradify | کد کامل ولی endpoint ها با مستندات فعلی verify نشده؛ dry-run امن است |
| backup خودکار DB | در THREAT_MODEL باز؛ litestream پیشنهاد شده |
| چند اپراتور / چند کسب‌وکار | طراحی تک‌اپراتور، تک‌برند |
| کار روی سرور | هنوز deploy نشده (P10) — همه‌چیز آماده‌ی استقرار است |

---

## ۷. مرجع سریع — هر قابلیت با ماژولش

| قابلیت | فراخوان | ماژول |
|---|---|---|
| ثبت سرنخ + draft اول + صف | `orchestrator.intake_enquiry(raw)` | orchestrator + F + C |
| پاسخ ریویو (sentiment→draft→صف) | `kickoff_review_response(review, platform)` | B + C |
| صفحه‌ی suburb (تحقیق→Sonnet→صف) | `kickoff_suburb_page(suburb, service)` | A + C |
| پست GBP → صف | `kickoff_gbp_post(content)` | E |
| publish پس از تأیید (preview) | `channel.publish(draft_id)` | E |
| پیگیری تکی / دسته‌ای ۵۰٪ | `kickoff_followup` / `kickoff_followup_batch` + `collect_followup_batch` | C |
| ثبت consent | `lead_capture.record_consent(...)` | F |
| sync به CRM (consent-gated) | `sync_lead(lead_id, target, operator_id)` | F |
| تأیید/ویرایش/رد | دکمه‌های تلگرام | queue + telegram_bot |
| توقف اضطراری | `/kill` | governance |
| گزارش خرج / سلامت | `/spend` / `/status` | governance + audit |
| سنجش کیفیت Gate (CI) | `make eval` — golden set ۱۵ موردی، precision/recall | evals/ |
| تست کامل offline | `make test` — ۱۱ فایل، بدون هیچ API | tests/ |

---

*اسناد هم‌خانواده: `ARCHITECTURE_MASTER.md` (طراحی کامل) · `ARCHITECTURE_REVIEW_2026-07-02.md`
(یافته‌ها و roadmap) · `PROMPTS_BACKLOG.md` (وضعیت P1–P10). ادعاهای pricing از KB-02 (Jun 2026)؛
پیش از تصمیم مالی دوباره verify شود.*
