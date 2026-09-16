# Brushline — بازبینی کامل معماری و بهینه‌سازی
**تاریخ:** 2026-07-02 | **وضعیت backlog:** P1–P9 همه DONE؛ فقط P10 (استقرار VPS) باز است
**دامنه:** کل `60_code/` (۱۶ ماژول src + ۱۱ فایل تست + eval harness) + مرز آن با infra-control

---

## ۱. خلاصه‌ی سریع — این سند چیست و چه می‌گیری؟

بازبینی لایه‌به‌لایه‌ی کل سیستم روی کد واقعی (نه کلی‌گویی)، با ۲۱ یافته‌ی مشخص با ارجاع فایل/خط.
**۹ مورد همین امروز اصلاح و تست شد** (بخش ۴)، بقیه در roadmap اولویت‌بندی‌شده (بخش ۵).

قضاوت کلی: هسته‌ی معماری **سالم و بالغ** است — سه invariant واقعاً در کد enforce می‌شوند نه فقط
در مستندات، مسیر draft→Gate→Queue→approve یکپارچه است، و پوشش تست offline در سطحی است که
برای یک MVP تک‌اپراتوره کم‌نظیر است. ضعف‌های واقعی در **مرز بین منطقِ تست‌شده و آداپتور live**
بودند (تلگرام/scheduler) و چند **حفره‌ی حسابداری هزینه** — نه در طراحی پایه.

نمره‌ی کلی سلامت (۱–۱۰، بعد از اصلاح‌های امروز):

| محور | قبل | بعد | توضیح |
|---|---|---|---|
| Correctness هسته | 8 | 9 | INV-1/2/3 در کد enforce؛ حفره‌ی Worker B بسته شد |
| Security | 7 | 8 | allow-list دو-کاناله، hash-chain، PII hash-ref؛ باقی: SOPS (P10) |
| Scalability | 5 | 7 | index + sargable query + pool-rollback؛ سقف بعدی: SQLite writer |
| Maintainability | 8 | 8 | جداسازی ماژول‌ها تمیز؛ الگوی مشترک بین workerها |
| Observability | 6 | 6 | audit chain عالی؛ metrics/alerting هنوز صفر (P10) |
| Production readiness | 4 | 6 | آداپتور live تلگرام تعمیر شد؛ scheduler و sender هنوز غایب |

---

## ۲. نقشه‌ی سیستم (آن‌چه واقعاً در کد هست)

```
Telegram (تنها UI اپراتور)
   │  allow-list روی message + callback (KB-05 s7)
   ▼
main.py ──► BrushlineBot ──► Orchestrator (لایه‌ی فرمانده)
                                │ check_and_enforce اول هر مسیر
     ┌──────────┬──────────┬────┴─────┬──────────┬──────────┐
     ▼          ▼          ▼          ▼          ▼          ▼
  Worker A   Worker B   Worker C   Worker D   Worker E   Worker F
  Research   Sentiment  Content    Asset      Channel    Lead-capture
  (Serper)   (Haiku)    (Haiku/    (stub)     (draft-    (capture/consent/
   read-only  read-only  Sonnet)               only GBP)   sync ServiceM8-Tradify)
     │          │          │                     │          │
     └──────────┴────┬─────┴─────────────────────┴──────────┘
                     ▼
             ConstitutionGate (deterministic + semantic ACL با Sonnet)
                     ▼
             ApprovalQueue (HITL؛ SLA/priority؛ EDIT→REGATE؛ هرگز auto-approve)
                     ▼
             publish/send/sync — فقط بعد از APPROVED (INV-1)
                     
 لایه‌های عرضی: governance (kill switch + spend cap) · audit (hash-chain append-only)
                resilience (retry/backoff/idempotency) · database (SQLite WAL + pool)
```

نقاط قوت طراحی که باید حفظ شوند:
- **Gate جدا از Queue جدا از Channel** — سه مرحله‌ی مستقل که هر کدام جداگانه تست می‌شوند؛ هیچ shortcut ای بین‌شان نیست.
- **fail-safe defaults همه‌جا:** بدون API key → template fallback / dry-run / stub؛ بدون operator id → هیچ sync؛ SLA منقضی → فقط escalate.
- **الگوی واحد برای هر اکشن بیرونی:** `check_and_enforce → call_with_retry(idempotency) → log_cost → audit.append`. این الگو الان (بعد از fix امروز) در هر ۶ نقطه‌ی خرج‌کننده برقرار است.
- **تفکیک حقوقی direct/public در Gate** (Spam Act روی پیام مستقیم، نه پاسخ عمومی ریویو) — ظرافتی که اکثر سیستم‌های مشابه ندارند.

---

## ۳. یافته‌ها — لایه‌به‌لایه (Severity: 🔴 بحرانی / 🟠 بالا / 🟡 متوسط)

### 3.1 Governance و حسابداری هزینه (INV-3)

**F1 🔴 Worker B هزینه‌ی واقعی می‌کرد بدون هیچ governance** — `audience.py: analyse_review`
فراخوان paid Haiku **بدون** `check_and_enforce` (kill switch و سقف روزانه آن را نمی‌دیدند)،
**بدون** `log_cost` (خرجش هرگز وارد cost_events نمی‌شد → سقف روزانه undercount)، و **بدون**
retry/idempotency (P8 این ماژول را جا انداخته بود). عملاً یک مسیر خرج نامرئی. **✅ اصلاح شد.**

**F2 🔴 (در ابتدای همین session) سقف روزانه از نیمه‌شب تا ~۱۰ صبح سیدنی صفر خوانده می‌شد** —
`governance.py`: mismatch بین `date.today()` محلی و timestamp های UTC. **✅ اصلاح شد** (`_utc_today`).

**F3 🟠 کوئری سقف روزانه روی هر اکشن، full-table scan بود** — `date(timestamp) = ?` تابع روی
ستون → index-ناپذیر؛ و اصلاً index ای وجود نداشت. `check_and_enforce` روی *هر* اکشن بیرونی این
کوئری را می‌زند؛ با رشد تاریخچه، هر draft کندتر می‌شد. **✅ اصلاح شد:** بازه‌ی sargable
`timestamp >= start AND < end` + `idx_cost_events_ts` (+۷ index دیگر روی مسیرهای داغ).

**F4 🟡 FX_AUD_USD هاردکد 1.45** — `config.py:39`. قاعده‌ی خود فایل («همه‌چیز از env») را نقض
می‌کند؛ با حرکت نرخ، سقف AUD عملاً جابه‌جا می‌شود. → env-override + یادآوری فصلی. (باز)

### 3.2 مرز live/tested — تلگرام و main.py

**F5 🔴 inline keyboard (قلب P3) در مسیر live اصلاً وصل نبود** — `main.py` هیچ
`CallbackQueryHandler` register نمی‌کرد؛ `handle_callback` که ۴۷ تست دارد از هیچ‌جا صدا زده
نمی‌شد؛ `/queue` کارت‌ها را بدون `reply_markup` (بدون دکمه) می‌فرستاد؛ و `bot.orchestrator`
که کامنت می‌گفت «injected by main.py» هرگز inject نمی‌شد. یعنی منطقِ کاملاً تست‌شده‌ی approve/
edit/reject در production غیرقابل‌دسترس بود. کلاسیک‌ترین شکاف «تست سبز، محصول شکسته».
**✅ اصلاح شد** (callback handler + دکمه‌های واقعی + inject؛ آفلاین AST-check شده — تست live
روی VPS در P10).

**F6 🟠 `parse_mode="Markdown"` روی متن دلخواه draft** — یک `*` تک در متن draft کل پیام
تلگرام را reject می‌کرد (اپراتور کارت را نمی‌دید = SLA از دست می‌رفت). **✅ اصلاح شد:** plain text.

**F7 🟡 `hash(chat_id)` در audit ورود غیرمجاز** — `hash()` پایتون per-process salt دارد
(PYTHONHASHSEED)؛ مهاجم تکراری بین دو restart قابل‌ربط نبود. **✅ اصلاح شد:** sha256 پایدار.

**F8 🟡 state ویرایش/reject در حافظه** (`_awaiting`) — restart وسط یک edit، جریان را می‌پراند.
برای تک‌اپراتور قابل‌تحمل؛ fix ارزان: جدول کوچک `operator_state`. (باز)

### 3.3 یکپارچگی جریان داده

**F9 🔴 مسیر enquiry هرگز Lead را persist نمی‌کرد** — `orchestrator.handle_enquiry` مستقیم
از dict ورودی draft می‌ساخت و `lead_capture.capture()` را صدا نمی‌زد → follow-up روز 2/5/10
(`_load_lead`) و sync CRM (`sync_lead`) آن lead را پیدا نمی‌کردند؛ follow-up با «unknown»
شخصی‌سازی می‌شد. **✅ اصلاح شد:** ورودی جدید `intake_enquiry` = capture سپس handle
(بدون دست‌زدن به `handle_enquiry` موجود → صفر ریسک regression؛ ۳۳ تست leadpath سبز ماند).

**F10 🟠 بعد از APPROVE پیام مستقیم، هیچ فرستنده‌ای وجود ندارد** — speed_to_lead/followup
تأییدشده به کجا می‌رود؟ integration SMS/email (مثلاً Twilio/SMS gateway یا email از دامنه)
هنوز ساخته نشده. این آگاهانه خارج از scope فازها بوده، ولی حالا که همه‌ی فازهای کد DONE اند،
**این گلوگاه واقعی go-live است**، بزرگ‌تر از P10. → پیشنهاد: «P11 — Worker G (Sender)» با همان
الگوی Channel: فقط پس از APPROVED، با retry+idempotency، هزینه per-SMS در cost_events. (باز)

**F11 🟡 batch id فقط در audit ذخیره می‌شود** — بعد از restart، batch های در جریان را باید از
audit query کرد؛ جدول `pending_batches` تمیزتر است. (باز — ارزان)

**F12 🟡 `consent_status` روی leads بعد از `record_consent` به‌روز نمی‌شود** — denormalized و
stale؛ منبع حقیقت `consent_records` است (که sync درست همان را چک می‌کند)، ولی گزارش‌گیری از
روی leads گمراه می‌شود. (باز — یک UPDATE دوخطی)

### 3.4 لایه‌ی داده

**F13 🟠 pool رollback نمی‌کرد** — `_PooledConnection.close()` = no-op؛ اگر بین execute و
commit استثنا می‌خورد، transaction باز به caller بعدیِ همان thread نشت می‌کرد (نوشته‌ی نیمه‌کاره
می‌توانست با commit بعدیِ بی‌ربط persist شود). **✅ اصلاح شد:** rollback-if-in_transaction روی
هر hand-back + تست. 

**F14 🟠 `verify_chain` تمام جدول را روی هر `/status` می‌خواند** — O(n) روی کل تاریخچه.
پیشنهاد: checkpoint دوره‌ای (هر N entry، hash تا آن نقطه در brushline_meta) → verify فقط از
آخرین checkpoint؛ verify کامل هفتگی/دستی. (باز)

**F15 🟡 SQLite vs Postgres** — تصمیم فعلی (ماندن روی SQLite/WAL) برای این workload
(تک‌process، write-rate پایین، تک‌اپراتور) **درست** است:

| محور (۱–۱۰) | SQLite/WAL | Postgres |
|---|---|---|
| Cost | 10 (صفر) | 6 (سرویس/نگه‌داری روی VPS) |
| Complexity | 9 | 5 (migration، user، pool واقعی) |
| Concurrency نوشتن | 4 (تک-writer) | 9 |
| Backup سادگی | 8 (فایل + litestream) | 7 (pg_dump) |
| Fit با «DB جدا از LANGAR» | 10 | 8 |

نقطه‌ی سوئیچ: وقتی چند process هم‌زمان بنویسند (مثلاً bot + scheduler + webhook جدا) یا
`SQLITE_BUSY` در لاگ دیده شود. تا آن‌جا: WAL + `busy_timeout` کافی است. (تصمیم: بمان)

### 3.5 Gate و کیفیت compliance

**F16 🟡 semantic ACL بدون retry و بدون prompt caching** — `gate.py:_semantic_acl` مستقیم
`messages.create` می‌زند؛ P8 (retry) و P7 (caching روی system ثابتش که کاندید عالی cache است)
این نقطه را پوشش ندادند. خطای گذرا → این لایه silent skip می‌شود (advisory است، پس امن؛ ولی
پوشش کم می‌شود). → همان دو wrapper موجود، ~۱۵ خط. (باز — ارزان)

**F17 🟡 `sovereignty_ok` همیشه True** — چک sovereignty هیچ منطقی ندارد ولی در GateResult
گزارش می‌شود؛ «چکی که همیشه سبز است» اعتماد کاذب می‌سازد. یا حذف صادقانه از خروجی، یا
منطق واقعی (مثلاً: هیچ endpoint غیر-AU/US در call path). (باز)

**F18 🟡 حداقل cache-اندازه** — پرامپت‌های system فعلی Worker C زیر minimum کش API اند
(~۱–۲k token)؛ سیم‌کشی P7 درست است ولی سود read فقط وقتی می‌آید که بلوک ثابت بزرگ شود.
فرصت: template/KB ثابت suburb-page را داخل بلوک cache شده ببر. (باز — همراه F16)

### 3.6 عملیات (به سمت P10)

**F19 🔴 هیچ scheduler ای وجود ندارد** — سه کار زمان‌مند (follow-up روز 2/5/10، 
`escalate_overdue`، `collect_followup_batch`) فقط وقتی اجرا می‌شوند که اپراتور دستی `/queue`
بزند. یعنی SLA escalation عملاً «وقتی یادت افتاد» است. → در main.py یک `asyncio` background
task با tick هر ~۶۰s (escalate + collect) و یک tick روزانه (followup scan). باید در P10 همراه
deploy برود چون به event loop زنده نیاز دارد. (باز — بخشی از P10)

**F20 🟠 backup/DR صفر است** — brushline.db حاوی PII مشتری و زنجیره‌ی audit (تعهد حقوقی) است؛
دیتای ماندگار بدون backup. ارزان‌ترین راه متناسب: **litestream** به object storage (یا حتی cron
`sqlite3 .backup` + rclone). جزو THREAT_MODEL باز P10. (باز)

**F21 🟠 `make test` با pytest هیچ تستی جمع نمی‌کرد** — تست‌ها script-style اند (تابع `test_*`
ندارند)؛ pytest صفر تست collect می‌کرد → CI planned در P10 با «سبز دروغین» یا exit-5 گیج‌کننده
می‌رفت. **✅ اصلاح شد:** target `test` حالا خود اسکریپت‌ها + eval را اجرا می‌کند (`test-pytest`
جدا نگه داشته شد).

---

## ۴. اصلاح‌های اعمال‌شده در همین session (همه تست‌شده)

| # | یافته | فایل | تست |
|---|---|---|---|
| 1 | F2 سقف روزانه‌ی timezone-bypass | governance.py | phase0 12/12 |
| 2 | F21+Makefile شکسته (`check:` بدون tab) | Makefile | make eval سبز |
| 3 | F1 حفره‌ی INV-3 در Worker B (enforce+log+retry+import امن) | audience.py | quickwins 16/16 |
| 4 | F3 index×8 + کوئری sargable | database.py, governance.py | quickwins |
| 5 | F5+F6 آداپتور live تلگرام (callback+دکمه+inject+plain text) | main.py | AST + منطق تست‌شده‌ی موجود |
| 6 | F7 sha256 chat-id ref | telegram_bot.py | quickwins |
| 7 | F9 `intake_enquiry` (persist Lead در front door) | orchestrator.py | quickwins |
| 8 | F13 pool rollback-on-release | database.py | quickwins |
| 9 | schema_version 1.1→1.2، phase 3→5 | database.py | — |

**وضعیت suite بعد از همه‌ی تغییرات: ۱۱ فایل تست + eval — همه سبز.**
(phase0 12/12، leadpath 33/33، reviewslice 27/27، suburbslice، queue 47/47، channel 17/17،
leadsync 25/25، eval-P6، costopt 26/26، resilience، datalayer، quickwins 16/16)

---

## ۵. Roadmap باقی‌مانده — اولویت با ROI و survival filter

| اولویت | کار | یافته | Effort | چرا این ترتیب |
|---|---|---|---|---|
| 1 | **P11 — Worker G (Sender): SMS/email بعد از APPROVE** | F10 | متوسط | بدون آن، کل خط تولید به «کپی دستی اپراتور» ختم می‌شود؛ ارزش تجاری واقعی این‌جاست |
| 2 | **P10 — deploy + scheduler + SOPS + backup** | F19, F20 | متوسط (VPS لازم) | scheduler و litestream داخل همین بسته؛ بدون deploy هیچ‌چیز live نیست |
| 3 | Gate: retry+caching روی semantic ACL | F16, F18 | کم | ۱۵ خط با ابزار موجود؛ پوشش compliance پایدارتر |
| 4 | verify_chain checkpoint دوره‌ای | F14 | کم | قبل از بزرگ‌شدن جدول ارزان است |
| 5 | خرده‌کارها: FX از env (F4)، pending_batches (F11)، consent_status update (F12)، operator_state (F8)، sovereignty صادقانه (F17) | — | خیلی کم | یک session نظافت |

**توصیه‌ی صریح:** قبل از P10، مسیر Sender (P11) را حداقل تا سطح dry-run بساز — وگرنه deploy
چیزی را زنده می‌کند که خروجی نهایی‌اش هنوز دست انسان است و ROI واقعی deploy را نمی‌گیری.
(تصمیم با توست؛ استدلال مخالف: P10 اول = زیرساخت تست‌شده برای توسعه‌ی P11 روی سرور.)

---

## ۶. قدم بعدی بلافاصله

1. این سند را مرور کن؛ اگر ترتیب 5.1 (P11 قبل از P10) را می‌پذیری، پرامپت P11 را به سبک
   PROMPTS_BACKLOG اضافه می‌کنم.
2. روی VPS که آماده شد: P10 + scheduler + litestream در همان session.
3. قبل از اولین اجرای live: endpointهای ServiceM8/Tradify را با مستندات فعلی verify کن
   (در `lead_capture.py` علامت‌گذاری شده) و `ALLOWED_OPERATOR_CHAT_IDS` واقعی را در .env بگذار.

> **یادداشت صداقت معرفتی:** نمره‌ها قضاوت مهندسی‌اند نه اندازه‌گیری؛ یافته‌های 🔴 همه با تست
> reproduce و سپس رفع شدند؛ ادعاهای pricing مدل‌ها از KB-02 (Jun 2026) می‌آیند و قبل از تکیه‌ی
> مالی دوباره چک شوند. تست live تلگرام (F5) فقط روی VPS ممکن است — تا آن‌جا «اصلاح‌شده ولی
> smoke-test-نشده» است.
