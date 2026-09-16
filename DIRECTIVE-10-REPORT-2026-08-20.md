---
type: evidence
task: directive-10
tags: [t52, t53, live-b, lab-1, lab-2, c-047, directive-10]
created: 2026-08-20T16:20+10:00
created_by: agent B (ZCode) — lease 4cc7c79f
paid_calls: 0/0 · executable=true: 0 · GAP-001: OPEN
---

# گزارش دستور مالک #۱۰ — ایجنت B

## §۶-۱ C-047 — DOCUMENTED (باز)

- incident note: [[INCIDENT-ORGANISM-GAP-2026-08-20]] — شکاف اول ~۴ دقیقه (14:33–14:36).
- **ریشهٔ عمیق‌تر در حین اصلاح پیدا شد:** کامنت سرِ فایل RUN-ORGANISM.bat هنوز
  پروتکل قدیمی «STOP+RESTART، هر دو پاک می‌شوند» را توصیف می‌کند؛ کد P2 فقط
  RESTART-REQUESTED را پاک می‌کند و با وجود STOP به `:stopped` می‌رود و launcher
  تمام می‌شود. **پروتکل درست: فقط RESTART-REQUESTED.** حین تصحیح، شکاف دوم
  ~۱۰۰ ثانیه‌ای افتاد (15:06–15:08) — هر دو از همین ریشه؛ ثبت شد.
- availability_incidents = **2** · crashes = 0.
- مستندسازی سرپرست‌ها در همان incident note؛ launch5.cmd فاقد حلقه است →
  daemon بدون سند بازیافت، ریاستارت نشد (طبق §۳).

## §۶-۲ T52 — SERVER TIMESTAMP: AVAILABLE (plumbed)

- تشخیص: کلاینت HTTP فقط بدنه می‌خواند؛ فیلد استاندارد `created` (unix seconds،
  ساعت سرور provider) موجود ولی دور ریخته می‌شد.
- اصلاح (زیر lease + flag، additive): `_ops/debate/client.py` فیلد
  `server_created` را برمی‌گرداند؛ `model_router` در emit مربوط به T48 اولویت
  را می‌دهد: `provider_server_created` (1s) > ‏`router_request_ts` (ms).
  انحراف ساعت در payload؛ skew>0 خودکار CLOCK_SKEW_SUSPECTED. تست‌ها ۳/۳.
- برچسب‌ها:
  - `producer_1_current = DELAY_BEARING_SAME_CLOCK` (۵ رویداد موجود، همه از
    کد قدیم؛ delta: ‏n=5 · median 8225.5ms · stdev 7234.5ms · max 21358.6ms —
    bearer تأخیر ✓ ولی هم‌ساعت)
  - `producer_1_target = INDEPENDENT_EXTERNAL_CLOCK` — کد مستقر؛ organism با
    ریاستارتِ C-047-مطابق بالا آمد (PID 9904)؛ اولین رویداد
    `provider_server_created` با اولین فراخوان روترِ کد جدید می‌آید (daemon
    هنوز کد قدیم — محدودیت شناخته‌شده).

## §۶-۳ T53 — PRODUCER_2: n=0 (معلق به پیام‌های تلگرامی مالک)

- spine: ‏`domain='telegram'` = 0 رویداد. مالک پیام‌ها را هنوز نفرستاده (§۷-۲).
- گزارش ۱۵:۴۹ اتوماسیون: هنوز نشده (در زمان بستن این گزارش).

## §۶-۴ BITEMPORAL REAL = **PASS** (اولین بار)

`research/bitemporal/real_data_check.py` روی ۷,۲۹۶ ردیف واقعی spine:
R1 future-use صفر ✓ · R2 یکنوایی as-of ✓ · R3 ماندگاری ✓ · R4 legacy ادعا
نمی‌کند ✓ (پس از رفع باگ چکر: NULL ردیف‌های پیش از migration مجاز است).

## §۶-۵ LIVE-B = **BLOCKED**

```text
independent_external_clock_sources = 0 live (plumbed, منتظر اولین رویداد)
delay_bearing_sources               = 1 (stdev 7.2s > 10ms ✓)
real_late_arriving_case             = 0 (معلق به تلگرام)
bitemporal suite on real data       = PASS
all read paths use decision_time    = PROVEN برای مسیر سیم‌شده (memory_read_loop)؛
                                       مسیرهای vault search/vector/kg/context-builder
                                       هنوز PROVEN نیستند (فهرست §۶-۳ دستور #۱۰)
```
پس از رسیدن پیام‌های تلگرامی (≥۵ رویداد + حداقل یک late-arriving) و اولین
رویداد server_created: حکم قابل صدور است — `PASS_WITH_CLOCK_CAVEAT` اگر فقط
router_request_ts+تلگرام، `PASS` اگر server_created هم مستقر شود.

## §۶-۶ LAB-1 فاز ۱ — DONE (تکمیل‌های امروز روی چارچوب دیروز)

- **همبستگی ناپایداری×اختلاف طول:** ‏n=3 جفت (|dlen|=32/105/8 در برابر
  |RSdiff|=0/0.22/1.0) — جهت ناسازگار؛ **UNDERPOWERED**؛ ادعا نمی‌کنیم.
- **توان آماری:** برای همبستگی ρ=0.5 با α=.05 و توان ۸۰٪ ≈ ۲۹ جفت لازم است؛
  با n=3 فقط اثر |ρ|>0.99 قابل تشخیص. برای تفکیک flip-rate ‏0.3 از 0.05 ≈ ۳۰
  قضاوت/شرط. نتیجه: فاز ۲ (امضایی) برای هر ادعای همبستگی ضروری است.
- **مجموعهٔ طلایی ۲۰تایی:** همان ۲۰ تسک چارچوب (R01–R10, C01–C10) به‌عنوان
  golden set پیشنهادی؛ پروتکل برچسب‌گذاری مالک: هر جفت کور (بدون نام داور)،
  امتیاز کیفیت ۱–۵ هر بازو + بازوی ترجیحی + TIE مجاز؛ فایل
  `research/judge_bias/GOLDEN-SET-LABELS-template.json` (باید مالک پر کند).
- چارچوب + ۷/۷ فرضیه: [[DISC-01-JUDGE-BIAS-2026-08-20]] (دستور #۹).

## §۶-۷ LAB-2 — DONE · mapping verdict: **NOT_READY_FOR_ACTIVE_INFERENCE (با نقشهٔ کامل)**

تمرین نگاشت (شبیه‌ساز: [[DISC-02-03-04-DIRECTIVE-9-2026-08-20]]):

| مؤلفهٔ Active Inference | معادل واقعی OCTOPUS | وضعیت |
|---|---|---|
| observation (o) | تلمتری per-beat با مهر کیفیت (trust.py) | موجود (shadow) |
| state (s) | بردار انحراف از setpointها (SETPOINTS_V1) | موجود (shadow) |
| transition (B) | دینامیک beat-to-beat | **غایب — مدل انتقال نیاموخته شده** |
| preference (C) | setpoints همان ترجیح‌ها | موجود |
| policy (π) | مودهای metacontrol (BLOCK/ADVISORY/SHADOW) | موجود |
| surprise/EFE | همبستگی surprise با AMBER/RED | **آزمون‌نشده (DISC-10 در backlog)** |

حکم صادقانه (§۵): تا یادگیری مدل انتقال و آزمون surprise، Active Inference
فقط شبیه‌سازی است؛ دادهٔ کالیبره‌شده کافی وجود ندارد. سه گام تا آمادگی:
(۱) DISC-10، (۲) fit یک transition ساده روی تاریخچهٔ spine، (۳) تعریف C از
setpoints و اندازه‌گیری value-of-information واقعی.

## سه جملهٔ §۸

مهم‌ترین فهم: نقطهٔ ضعف «زمانِ مستقل» فقط نبودِ فیلد نبود — فیلد `created`
همیشه در پاسخ بود و دور ریخته می‌شد؛ دیدنِ آن نیازمند پرسیدن «کدام ساعت؟»
به‌جای «چه تأخیری؟» بود. مهم‌ترین ندانسته: آیا ساعت سرور provider و تلگرام
در عمل skew قابل‌ملاحظه دارند و late-arriving واقعی در پنجرهٔ سنجش ظاهر
می‌شود یا نه (داده هنوز صفر است). خطرناک‌ترین باور: «suite سبز روی دادهٔ
واقعی یعنی spine دوزمانیِ زنده است» — این	suite سازگاریِ داخلی رکوردها را
می‌سنجد؛ تا دو منبع مستقل ساعت و late-arriving واقعی نیاید، VERIFIED نه.