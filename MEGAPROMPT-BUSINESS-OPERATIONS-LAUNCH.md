---
tags: [ofn, megaprompt, operations, panels, marketing, launch]
aliases: [مگاپرامپت عملیاتی‌کردن بیزنس‌ها, Business Operations Launch]
updated: 2026-08-10
status: 🔄 O1–O9 اجرا شد (۲۰۲۶-۰۸-۱۰) · O10–O12 فقط با حکم آری
---

# MEGAPROMPT — تبدیل پنل‌ها به سیستم عملیاتی سه بیزنس

> این سند برای ایجنت بعدی است. کار او طراحی دوباره نیست؛ باید فازها را به
> ترتیب اجرا کند، بعد از هر فاز دروازه را بسنجد، و هر جا حکم آری لازم است
> متوقف شود. هدف، یک «داشبورد نمایشی» نیست: آری و شریک‌ها باید بتوانند کار
> امروز، فروش، لید، محتوا، تأیید، اجرای دستی و نتیجه را از ابتدا تا انتها
> ثبت و کنترل کنند.

**پیوندها:** [[CLAUDE]] · [[HANDOFF]] · [[DECISIONS]] · [[INDEX]] ·
[[MEGAPROMPT-COMPLETE-FINISH]] · [[MEGAPROMPT-MARKETING-PLATFORM-INTEGRATION]] ·
[[PORTFOLIO-TENANT-MAP]] · [[VENDOR-EVALUATION]]

**نقشهٔ دیداری:** [Operations Launch Canvas](/home/ari/.cursor/projects/home-ari/canvases/ofn-business-operations-launch.canvas.tsx)

```
کرنل تصمیم می‌گیرد. مدل مشورت می‌دهد. انسان حکم می‌کند.
اول دستی و قابل‌اندازه‌گیری؛ بعد اتصال خارجی.
```

---

## ۰) نتیجه‌ای که باید تحویل شود

وقتی این مگاپرامپت تمام شد، این شش سفر باید واقعی و قابل تکرار باشند:

1. **مالک:** پنل را باز می‌کند و بدون گشتن بین تب‌ها می‌بیند امروز برای هر
   بیزنس چه کاری مانده، کدام کار دیر شده، چه چیزی منتظر تأیید است، چه چیزی
   دستی انجام شده و نتیجه‌اش چه بوده است.
2. **لید نقاشی:** لید وارد می‌شود، تکراری احتمالی دیده می‌شود، مسئول و موعد
   پیگیری می‌گیرد، متن جواب/قیمت آماده می‌شود، مالک تأیید می‌کند، انسان آن را
   دستی می‌فرستد، انجام‌شدن ثبت می‌شود و تعامل/وضعیت لید جلو می‌رود.
3. **زیمان / GiftMesh Sydney:** قطعه از ساخت به عکس و قیمت و «آمادهٔ معرفی»
   می‌رسد، بستهٔ انتشار دستی می‌گیرد، انتشار انسانی ثبت می‌شود، فروش واقعی
   با مبلغ و کارمزد معلوم/نامعلوم ثبت می‌شود و حاشیه فقط وقتی دادهٔ کافی هست
   نمایش داده می‌شود.
4. **استودیو:** رسانه بایگانی و برچسب‌گذاری می‌شود، draft و نسخهٔ هر پلتفرم
   آماده می‌شود، حساسیت و رضایت مستقل بررسی می‌شود، مالک تأیید می‌کند و تا
   وقتی `partner_precondition` بسته است هیچ completion یا خروجی رخ نمی‌دهد.
5. **بازاریابی دستی‌اول:** هر بیزنس فرضیه، مخاطب، پیشنهاد، کانال، کار این
   هفته، بستهٔ اجرا و نتیجهٔ اندازه‌گیری‌شده دارد. هیچ «کمپین فعال» بدون
   شاهد مستقل ثبت نمی‌شود.
6. **ورودی خارجی:** webhook فقط بعد از امضای معتبر و connector شناخته‌شده
   وارد inbox می‌شود، با شناسهٔ vendor dedup می‌شود، raw/PII نگه نمی‌دارد و
   هرگز مستقیم چیزی به بیرون نمی‌فرستد.

### تعریف «عملیاتی»

هر قابلیت فقط وقتی عملیاتی است که همهٔ این‌ها را داشته باشد:

- یک کاربر مشخص و یک کار بعدی روشن؛
- state machine بادوام، نه متغیر جاوااسکریپت یا متن UI؛
- API احرازشده و tenant-scoped؛
- ledger برای mutation؛
- empty/error/loading صادقانه؛
- معیار پایان و شاهد مستقل؛
- تست واحد + API + قرارداد UI + یک سفر end-to-end؛
- بعد از restart همان وضعیت را نشان دهد.

وجود کارت، دکمه، adapter یا جدول به‌تنهایی «عملیاتی» نیست.

---

## ۱) حقیقت فعلی — قبل از هر ویرایش دوباره اندازه بگیر

```bash
cd /home/ari/ofn
python3 tools/repo_baseline.py --tests
python3 -m pytest -q
python3 -m ofn.preflight
git status -sb && git log -5 --oneline
systemctl is-active ofn hypno-fugu-mini cloudflared
ss -lntp | rg ':(8791|8792|8793|8794|8895|8090)\b' || true
```

snapshot هنگام طراحی:

- suite: `1767 passed · 5 skipped · 1772 collected`
- boot: `31/31`
- پورت‌های ۸۷۹۱ تا ۸۷۹۴ و ۸۸۹۵ loopback؛ ۸۰۹۰ بدون listener
- `secret_rotation` بسته
- `partner_precondition` بسته
- دو فایل `.bak-*` untracked و نامرتبط؛ نخوان، stage نکن، commit نکن

اگر suite قرمز شد، قبل از هر کار گزارش بده و ادامه نده. عدد snapshot را در
اسناد آینده کپی نکن؛ عدد زنده را از baseline بگیر.

---

## ۲) آنچه امروز واقعاً وجود دارد

### پنل مالک — `web/panel.html`

موجود: kill، صف تصمیم، سلامت برد، boot، risks، ledger، outbox، connector
observability و میز غنی نقاشی.

شکاف: هنوز «میز کار امروز» برای کل پرتفوی نیست. `Node.owner_snapshot()` و
کارت‌ها بیشتر وضعیت سیستم را می‌گویند تا کار عملیاتی بعدی. owner باید از
storeهای واقعی projection بگیرد، نه DB موازی.

### لید — `web/lead.html`

موجود: ثبت، جست‌وجو/فیلتر، score قابل‌توضیح، تغییر وضعیت، draft جواب و quote.

شکاف: موعد پیگیری، overdue، مسئول، تشخیص تکراری، رسید ارسال دستی و attribution
تا نتیجه کامل نیست. `next_action` متن است ولی زمان و completion ندارد.

### زیمان — `web/ziman.html`

موجود: قطعه، عکس، قیمت، هزینه، lifecycle و ثبت sold/channel.

شکاف: «آمادهٔ بازاریابی → بستهٔ انتشار دستی → ثبت انتشار → فروش واقعی» یک
زنجیرهٔ بادوام نیست. مبلغ واقعی فروش و کارمزد مستقل از state محصول ثبت
نمی‌شود. کانال‌ها در پک خالی‌اند و نباید کارمزد حدس زده شود.

### استودیو — `web/studio.html`

موجود: آرشیو، گالری، draft، route preview، consent check، marketing week،
نسخه‌های پلتفرم و queue به outbox.

شکاف: API امن برای مدیریت metadata رضایت و لغو، completion دستی انتشار و
projection اثر لغو روی پست‌های قبلی کامل نیست. گیت انتشار عمداً بسته است.

### connector / inbox

زیرساخت rate، correlation، inbox و metrics وجود دارد؛ ولی مسیر زنده در
`Node.handle_webhook()` هنوز connector را `default` و vendor را `unknown`
می‌گذارد، `vendor_event_id` تصادفی می‌سازد و verifier واقعی را اجرا نمی‌کند.
این مسیر فقط اسکلت است، نه webhook production.

### outbox — شکاف حیاتی

`Node.owner_decide()` در approval مستقیماً `Outbox.claim()` را صدا می‌زند.
یعنی approval فوراً `pending → in_flight` می‌شود، در حالی‌که sender وجود
ندارد. نتیجه: کار تأییدشده نه ارسال شده و نه یک کار دستی قابل‌تکمیل است.

فاز O2 باید این را قبل از هر UI بازاریابی اصلاح کند.

---

## ۳) قوانین سخت این مأموریت

```
NEVER_1  راز را نخوان، چاپ نکن، در fixture/HANDOFF/commit ننویس
NEVER_2  OFN_WIRE_* یا OCTOPUS_WIRE_* را روشن نکن
NEVER_3  secret_rotation / partner_precondition / miner_isolation را دور نزن
NEVER_4  پیام، پست، ایمیل، quote، DM یا پرداخت واقعی نفرست
NEVER_5  outbox را drain نکن و approved را sent جا نزن
NEVER_6  کد login/credential برای حساب پیام مستقیم شریک نساز — D-13 دائمی است
NEVER_7  UI موجود را حذف نکن؛ فقط ادغام یا اضافه
NEVER_8  DB موازی برای چیزی که canonical store دارد نساز
NEVER_9  raw webhook، مدرک رضایت، credential یا PII را وارد ledger نکن
NEVER_10 systemd/timer/env/Cloudflare را بدون حکم همان جلسه عوض نکن
NEVER_11 dependency/daemon سنگین روی برد ۴GB اضافه نکن
NEVER_12 migration تخریبی، schema drop یا retention delete اجرا نکن
NEVER_13 `.bak-*`، `.env` یا state زنده را commit نکن
NEVER_14 متن فنی D-22 را در UI شریک نشان نده
```

کار آزاد: schema افزایشی، migration idempotent، API محلی، UI، تست، fake
connector، بستهٔ اجرای دستی، export/download و ثبت کاری که انسان بیرون از
نود انجام داده است.

---

## ۴) معماری هدف — یک حقیقت برای هر چیز

### منابع canonical

- محصول، قطعه و فروش زیمان: `products.sqlite` / `ProductStore`
- لید، کانال، کمپین و تعامل نقاشی: `painting.sqlite` / `LeadStore`
- رسانه و draft استودیو: `studio.sqlite` / `StudioStore`
- رضایت: `consent.sqlite` / `ConsentStore`
- variant و metric بازاریابی استودیو: `marketing.sqlite` / `MarketingStore`
- ورودی vendor: `inbox.sqlite` / `MarketingInbox`
- approval و delivery lifecycle: `outbox.sqlite` / `Outbox`
- audit: `ledger.sqlite`، فقط شاهد؛ هرگز state source
- owner workboard: projection خواندنی از storeهای بالا؛ **DB تازه ممنوع**

### قرارداد ثبت مستقل

هر ادعا یک شاهد دوم دارد:

- «تأیید شد» → outbox approval fields + ledger event
- «انسان فرستاد/منتشر کرد» → completion receipt + hash بستهٔ اجرا
- «فروش رفت» → sale event + state محصول
- «لید پیگیری شد» → interaction + timestamp لید
- «کمپین اجرا شد» → action completion + metric/evidence
- «webhook تکراری است» → vendor event ID + body hash
- «کار امروز است» → due timestamp در canonical store، نه متن کارت

### بودجهٔ دستگاه

- stdlib-first؛ هیچ Redis/Postgres/Celery/React build server
- یک پروسهٔ OFN، SQLite WAL + `synchronous=FULL`
- listها bounded و paginated
- poll پنل‌ها ۶۰ ثانیه یا بیشتر و فقط وقتی visible
- owner projection یک snapshot bounded؛ payload خام و عکس داخل آن ممنوع

---

## ۵) چرخهٔ صحیح approval و اجرای دستی

schema outbox را افزایشی migrate کن. نام stateهای قدیمی را فقط با migration
و alias سازگار نگه دار؛ breaking API rename ممنوع.

```text
pending_approval
  ├── rejected
  ├── approved_manual ──> manual_completed
  └── approved_adapter ──> in_flight ──> sent
                                  ├── held
                                  └── failed
```

در این مأموریت مسیر فعال فقط `approved_manual` است. `approved_adapter` و sender
تا حکم جداگانه وجود اجرایی ندارند.

ستون‌های افزایشی پیشنهادی:

```text
delivery_mode          manual | adapter
approved_at            ISO timestamp
approved_by            owner identity (safe identifier)
completed_at           ISO timestamp
completed_by           authenticated human identity
completion_channel     closed vocabulary
packet_sha256          hash exact manual packet
external_ref_digest    optional hash, never raw credential/proof
```

قواعد:

1. approval فقط approval است؛ `claim()` نمی‌کند.
2. reject از هر state نامعتبر fail-closed است.
3. completion روی `approved_manual` idempotent است.
4. RED برای approval و completion هر دو confirmation دوم می‌خواهد.
5. kill و gateهای بسته در enqueue، approval و completion دوباره سنجیده شوند.
6. manual packet transient است و از canonical record ساخته می‌شود.
7. completion projection به store بیزنس و ledger باید idempotent باشد.
8. crash وسط completion → reconciliation gap قابل‌دیدن، نه success جعلی.

---

## ۶) تجربهٔ نهایی هر پنل

### ۶-۱) پنل مالک: «امروز»

اولین نمای بعد از login، بدون حذف کارت‌های فنی موجود:

- خلاصهٔ چهار tenant، ولی portfolio totals فقط ziman/lead/studio
- «امروز»: کارهای overdue، امروز، این هفته
- «منتظر حکم من»: pending approval بر اساس ریسک
- «تأیید شده، منتظر انجام دستی»
- «گیر کرده»: held/failed inbox و outbox + reconciliation gaps
- سه کارت نتیجه: لید، زیمان، استودیو
- آخرین فعالیت موفق هر بیزنس و زمان freshness
- دکمهٔ ورود به میز تخصصی همان بیزنس

هر عدد باید drill-down داشته باشد یا صریحاً `اندازه‌گیری نمی‌شود` بگوید.
owner workboard فقط read model است.

### ۶-۲) پنل لید: «کار بعدی»

- default sort: overdue → hot → warm → newest
- فیلتر: وضعیت، مسئول، موعد، منبع، duplicate candidate
- کارت لید: اولویت انسانی، دلیل score، کار بعدی، موعد، آخرین تماس
- timeline تعاملات
- ساخت reply/quote packet، نه ادعای ارسال
- دکمهٔ «متن را کپی کردم/دستی فرستادم» فقط بعد از owner approval
- ثبت outcome و next follow-up در همان sheet
- duplicate warning بر phone/email hash؛ merge خودکار ممنوع
- dashboard: new/contacted/quoted/won/lost، conversion و age، نه vanity count

### ۶-۳) پنل زیمان: «از ساخت تا فروش»

- laneهای در ساخت، آمادهٔ عکس، آمادهٔ معرفی، منتشرشده، فروخته‌شده
- checklist هر قطعه: عکس، قیمت، توضیح، کانال، marketing status
- ساخت listing packet با caption، SKU، قیمت و rendition محلی
- ثبت «دستی منتشر شد» با channel و optional external reference hash
- ثبت فروش: مبلغ واقعی یا `نامعلوم`، کانال، کارمزد واقعی یا `نامعلوم`
- نمایش gross/net فقط وقتی دادهٔ لازم هست
- dashboard: ready-to-list، stale، sold، revenue measured، margin measured
- CTA حالت خالی همان‌جا اولین قطعه/عکس/قیمت را ثبت کند

هیچ storefront عمومی یا order form بدون فاز O9 و حکم PII ساخته/فعال نشود.

### ۶-۴) پنل استودیو: «آماده‌سازی امن»

- pipeline: archive → select → **ساخت draft** → اتصال عکس‌ها → consent →
  route → owner approval
- CTA واقعی «پست تازه» داخل Today و Marketing؛ عنوان/متن/پلتفرم را می‌گیرد،
  `POST /api/v1/studio/drafts` را صدا می‌زند و بعد mediaهای انتخابی را با
  `POST /api/v1/studio/drafts/{id}/media` وصل می‌کند
- انتخاب media از gallery؛ upload همچنان فقط وارد library می‌شود و نباید
  بی‌صدا draft بسازد
- felt-right rating پیش از اولین metric از UI ثبت می‌شود
- reading/advisor موجود از UI قابل درخواست و accept/reject است، با وضعیت
  queued/ready/error صادقانه
- نشان جدا برای sensitivity، consent، gate، owner approval
- consent gap با کار بعدی قابل‌فهم، نه متن فنی
- partner می‌تواند metadata لازم را درخواست کند، ولی خودش release صادر نکند
- manual packet فقط برای رسانهٔ مجاز
- completion تا `partner_precondition` بسته است ممنوع
- revocation impact list برای owner
- metrics فقط پس از ثبت felt-right و publication receipt

### ۶-۵) بازاریابی مشترک: «آزمایش رشد»

یک زبان مشترک، نه الزاماً یک جدول مشترک:

```text
فرضیه → مخاطب → پیشنهاد → کانال → دارایی/متن
→ بازبینی → بستهٔ اجرای دستی → completion receipt
→ metric → نتیجه: ادامه | اصلاح | توقف
```

Lead از `painting_campaigns` استفاده می‌کند. Studio از week/draft/variant.
Ziman از product/listing lifecycle. facade مشترک فقط projection و vocabulary
می‌دهد؛ storeهای موجود را duplicate نمی‌کند.

minimum fields هر آزمایش:

- objective و success metric
- target audience بدون PII
- offer/claim source
- channel
- owner
- due date
- budget سقف‌دار یا `0/manual`
- state: idea/draft/approved/running_manual/paused/completed
- evidence و metric measured/not_measured

---

## ۷) API هدف

همهٔ endpointهای تازه زیر auth موجود و `Cache-Control: no-store`.

### owner

```text
GET  /api/v1/owner/workboard
GET  /api/v1/owner/outbox/{id}/packet
POST /api/v1/owner/outbox/{id}/complete
GET  /api/v1/owner/reconciliation
GET  /api/v1/owner/consent/subjects
GET  /api/v1/owner/consent/gaps
POST /api/v1/owner/consent/subjects
POST /api/v1/owner/consent/releases
POST /api/v1/owner/consent/releases/{id}/revoke
```

### lead

```text
GET  /api/v1/painting/workboard
GET  /api/v1/painting/leads/{id}/timeline
POST /api/v1/painting/leads/{id}/follow-up
POST /api/v1/painting/leads/{id}/reply-packet
POST /api/v1/painting/leads/{id}/quote-packet
POST /api/v1/painting/leads/{id}/manual-complete
GET  /api/v1/painting/duplicates/{id}
```

مسیرهای reply/quote قدیمی alias سازگار بمانند ولی دیگر success را «ارسال شد»
معنی نکنند؛ response صریحاً `queued_for_approval` یا `approved_manual` بدهد.

### ziman

```text
GET  /api/v1/products/workboard
POST /api/v1/products/{sku}/listing-packet
POST /api/v1/products/{sku}/manual-publish-complete
POST /api/v1/products/{sku}/sales
GET  /api/v1/products/{sku}/sales
```

### studio

```text
GET  /api/v1/studio/workboard
POST /api/v1/studio/drafts                       (موجود؛ UI باید وصل شود)
POST /api/v1/studio/drafts/{id}/media            (موجود؛ UI باید وصل شود)
POST /api/v1/studio/drafts/{id}/felt             (موجود؛ UI باید وصل شود)
GET  /api/v1/studio/reading                      (موجود؛ UI باید وصل شود)
POST /api/v1/studio/reading                      (موجود؛ UI باید وصل شود)
POST /api/v1/studio/reading/judge                (موجود؛ UI باید وصل شود)
POST /api/v1/studio/drafts/{id}/manual-packet
POST /api/v1/studio/drafts/{id}/manual-complete
GET  /api/v1/studio/drafts/{id}/consent-gaps
```

### webhook

```text
POST /api/v1/webhooks/{tenant}/{connector}
```

ترتیب اجباری: body cap → correlation → rate limit → connector lookup →
signature verify → tenant cross-check → normalize/scrub → dedup/store →
ledger. unknown connector یا verifier غایب = reject.

---

## ۸) فازهای اجرا — ترتیب و وابستگی قطعی

### فاز O0 — baseline، inventory و نقشهٔ تغییر

بخوان:

- `CLAUDE.md`, `HANDOFF.md`, `DECISIONS.md`
- این سند و دو مگاپرامپت لینک‌شده
- `node.py`, `http_api.py`, `run.py`
- storeها و چهار HTML

خروجی قبل از کد:

- فهرست فایل‌های نامرتبط که دست نمی‌خورد
- state diagram فعلی outbox و webhook
- ماتریس implemented / UI-only / backend-only / absent
- migration plan و rollback هر DB

دروازه: suite سبز؛ هیچ mutation روی state زنده.

### فاز O1 — قراردادها و state machineها

فایل‌ها:

- `ofn/adapters/outbox.py`
- `ofn/adapters/connector_contract.py`
- types کوچک در adapter layer، نه kernel با نام بیزنس

کار:

- DTOهای `ManualPacket`, `CompletionReceipt`, `WorkboardItem`
- state transition functionهای خالص و تست‌شده
- migration outbox افزایشی و idempotent
- compatibility projection برای statusهای قدیمی

تست تازه:

- `tests/test_manual_dispatch.py`
- migration روی DB قدیمی fixture
- transition matrix کامل

دروازه: هیچ API/UI هنوز؛ outbox قدیمی خوانده می‌شود؛ WAL/FULL؛ power-cut
test سبز.

### فاز O2 — جداکردن approval از send

فایل‌ها:

- `ofn/node.py:owner_decide`
- `ofn/adapters/outbox.py`
- `ofn/adapters/owner_reads.py`
- `ofn/adapters/http_api.py`
- `ofn/run.py`
- `web/panel.html`

کار:

- approval → `approved_manual`
- reject → state صریح `rejected` با alias سازگار برای گزارش قدیمی
- packet endpoint و completion endpoint
- packet hash و receipt
- UI صف «تأیید شده، دستی انجام بده»
- ledger برای approve/reject/complete

تست‌ها:

- `test_node.py`
- `test_owner_api.py`
- `test_painting_outbox.py`
- `test_studio_marketing_actions.py`
- `test_persistence.py`
- `test_mutation_ledger_pair.py`

دروازه: approval هیچ آیتمی را `in_flight` نمی‌کند؛ restart وضعیت را نگه
می‌دارد؛ completion تکراری duplicate effect ندارد؛ kill/gates fail-closed.

commit پیشنهادی:

```text
fix(operations): separate owner approval from manual completion
```

### فاز O3 — امن‌کردن webhook واقعی، بدون vendor واقعی

فایل‌ها:

- `connector_contract.py`
- `webhook_verify.py`
- `marketing_inbox.py`
- `inbox_processor.py`
- `node.py`
- `http_api.py`
- `run.py`

کار:

- registry connector با capability/verifier/normalizer
- حذف `vendor_payload` خام از contract
- event ID واقعی و hash collision handling
- safe normalized payload allowlist
- inbox item پردازش‌پذیر بدون raw body
- fake signed connector فقط در tests

تست‌ها:

- `test_connector_infra.py`
- `test_phase_a_security.py`
- `test_phase_b_inbox.py`
- تست same ID/same hash و same ID/different hash

دروازه: unsigned، unknown، tenant mismatch رد؛ fake signed یک بار ثبت؛ raw
body/PII در DB/ledger نیست؛ هیچ outbound reachable نیست.

commit پیشنهادی:

```text
fix(connectors): verify and normalize inbound events before inbox commit
```

### فاز O4 — owner workboard

فایل‌ها:

- `owner_reads.py`
- `node.py`
- `http_api.py`
- `run.py`
- `panel.html`

workboard از storeهای canonical این بخش‌ها را می‌سازد:

- approvals، manual completions، held/failed
- follow-upهای لید
- قطعات آماده/stale زیمان
- draftهای blocked/ready استودیو
- freshness و last-success
- missing required facts و closed gates

همان فاز، سه کنترل backend-only موجود را به بخش «ابزارهای مالک» وصل کند:

- brain probe: فقط queue job و نمایش queued/result؛ هرگز success مدل را پیشاپیش
  ادعا نکند
- owner ask: متن محدود، هزینه/سطح روشن، confirmation پیش از job پولی
- marketing cycle run: اجرای دستی cycle با وضعیت running/completed/failed؛
  timer را روشن نکند

این‌ها workboard mutation نیستند و endpointهای فعلی خودشان را نگه می‌دارند؛
UI فقط مسیرهای backend موجود را قابل‌استفاده می‌کند.

تست تازه: `tests/test_owner_workboard.py`

دروازه: endpoint workboard owner-only و read-only؛ countها از query مستقل
قابل بازتولید؛ hypno در inventory هست ولی portfolio KPI نیست؛ هر سه ابزار
operator owner-only، دارای pending/error واقعی و بدون timer/systemd change.

commit پیشنهادی:

```text
feat(owner): add cross-business daily workboard
```

### فاز O5 — عملیاتی‌کردن لید

schema افزایشی `painting_leads`:

```text
next_action_at
last_contacted_at
outcome_reason
assigned_to
contact_phone_hash
contact_email_hash
```

اصل contact در همان ستون‌های موجود canonical می‌ماند؛ hash فقط برای duplicate
warning است.

کار:

- follow-up due/overdue
- timeline interactions
- duplicate candidate، بدون merge
- reply/quote packet → owner approval → human completion
- completion یک interaction می‌سازد و lead را idempotent جلو می‌برد
- campaign dashboard از `painting_campaigns`
- attribution source/channel تا won/lost

تست تازه: `tests/test_lead_followups.py`

دروازه: عباس پنج سفر ثبت→موعد→packet→completion→interaction را روی fixture
انجام می‌دهد؛ consent از public contact استنتاج نمی‌شود؛ tender/vendor/DM
auto-submit وجود ندارد.

commit پیشنهادی:

```text
feat(lead): add due follow-ups and manual completion receipts
```

### فاز O6 — عملیاتی‌کردن زیمان

schema تازه در همان `products.sqlite`:

```sql
CREATE TABLE product_sale_events (
  event_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  sku TEXT NOT NULL,
  gross_cents INTEGER,
  amount_unknown INTEGER NOT NULL,
  channel TEXT NOT NULL,
  fee_cents INTEGER,
  fee_unknown INTEGER NOT NULL,
  sold_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (tenant_id, event_id)
);
```

قیدها را طوری بنویس که amount معلوم و unknown همزمان نباشند. sale event و
`products.state='sold'` در یک transaction. customer PII در این جدول ممنوع.

کار:

- product workboard و laneها
- listing readiness
- manual listing packet و completion receipt
- sale receipt
- measured revenue/margin و unknown صریح

تست تازه: `tests/test_ziman_sales.py`

دروازه: مبلغ/کارمزد حدس زده نمی‌شود؛ event idempotent؛ state و event با هم
commit/rollback؛ عکس و محصول موجود حفظ؛ empty-state کنش دارد.

commit پیشنهادی:

```text
feat(ziman): connect listing workflow to measured sales
```

### فاز O7 — رضایت و completion استودیو

فایل‌ها:

- `consent_store.py`
- `studio_store.py`
- `marketing_store.py`
- `node.py`
- `http_api.py`
- `run.py`
- `studio.html`
- `panel.html`

کار:

- UI ساخت draft از Today/Marketing با endpoint موجود
- picker انتخاب media از gallery و attach به draft با endpoint موجود
- draft تازه بعد از read-back در board دیده شود؛ API گفت `ok` کافی نیست
- felt-right از UI و قبل از اولین metric
- reading/advisor request + judge از UI، بدون raw rule یا jargon
- owner API برای subject/release/revoke/gaps
- فقط digest/location/scope/time؛ document bytes ممنوع
- partner فقط gap می‌بیند و review request می‌دهد
- packet از routed variant موجود
- completion projection به outbox، `media_sent`، draft و post history
- revocation impact

تست تازه:

- `tests/test_studio_draft_workflow.py`
- `tests/test_consent_api.py`
- گسترش `tests/test_studio_shell.py` و `tests/test_studio_api.py`

دروازه: یک شریک از UI واقعی draft می‌سازد، حداقل یک media موجود را وصل می‌کند
و همان draft را در board/route-preview می‌بیند؛ upload بی‌صدا draft نمی‌سازد؛
restricted/missing/expired/revoked/platform mismatch رد؛ `partner_precondition`
همچنان completion را می‌بندد؛ felt-right قبل از metric.

commit پیشنهادی:

```text
feat(studio): add owner consent administration and manual publish receipts
```

### فاز O8 — workbench بازاریابی دستی‌اول

DB عمومی تازه نساز. یک facade خواندنی/فرمان محدود روی workflowهای موجود
بساز:

- lead campaign ↔ lead outcomes
- ziman listing ↔ sale events
- studio week/draft/variant ↔ metrics

پنل مالک:

- هدف این هفته
- کار بعدی و مسئول
- کانال و بودجه
- تعداد اجراهای دستی
- outcome measured/not_measured
- ادامه/اصلاح/توقف با دلیل

هر بیزنس یک template شروع دارد، نه دادهٔ ساختگی:

- lead: پیشنهاد محلی + منبع inbound + follow-up
- ziman: یک خانوادهٔ محصول + یک کانال دستی + فروش
- studio: یک axis محتوایی + felt-right + metric، بدون انتشار تا بازشدن gate

تست تازه: `tests/test_growth_workbench.py`

دروازه: یک سفر کامل fake برای هر سه tenant؛ هیچ KPI بدون event source؛ هیچ
cross-tenant aggregate جز owner projection.

commit پیشنهادی:

```text
feat(marketing): add manual-first growth workbench across three businesses
```

### فاز O9 — surface عمومی جذب مشتری (RED، نیازمند حکم آری)

این فاز را **طراحی و تست محلی** می‌توان انجام داد، ولی فعال‌سازی عمومی چون
PII می‌گیرد و از دستگاه بیرون قابل‌دسترسی می‌شود، حکم جدا می‌خواهد.

پیش‌فرض امن:

- هیچ storefront کامل، checkout یا payment
- هیچ فرم تماس تا approval
- فقط catalog/read-only بدون PII برای ziman در صورت تأیید برند/قیمت
- فقط quote-intake برای lead بعد از تعیین privacy copy، consent text،
  retention و owner مقصد
- body cap، honeypot، rate limit، CSRF strategy، no indexing تا launch
- هر submission → inbox/local lead؛ پاسخ خودکار ممنوع

پیش‌شرط‌های آری:

1. مسیر و دامنهٔ public را تأیید کند.
2. متن privacy/consent و retention را تأیید کند.
3. مشخص کند چه کسی follow-up می‌کند.
4. service area و offer واقعی ثبت شده باشد.
5. backup/incident runbook مرور شود.

بدون این پنج مورد: code ممکن است local-only بماند، route عمومی deploy نشود.

### فاز O10 — vendor read-only pilot (نیازمند حکم آری)

قبل از کد، `VENDOR-EVALUATION` را با docs رسمی روز دوباره بررسی کن. انتخاب
قدیمی recommendation است، حکم نیست.

آری باید این چهار چیز را صریح بدهد:

- vendor
- tenant pilot
- scopeهای read-only
- معیار توقف/موفقیت

قواعد pilot:

- credential کم‌اختیار؛ مقدارش دیده یا log نشود
- یک tenant، bounded page، cursor after-commit + read-back
- health جدا از capability و permission
- صفر outbound
- rollback = disable connector + حفظ receipts

### فاز O11 — فعال‌سازی خروجی محدود (RED، خارج از اجرای خودکار این سند)

فقط اگر آری در همان جلسه حکم داد:

- secretها چرخانده و `secret_rotation` رسماً باز شده
- برای studio پیش‌شرط ثبت و گیت باز شده
- WIRE دقیق همان transport با تأیید روشن شود
- sender فقط public-content adapter؛ D-13 همچنان direct-message automation را
  مطلقاً ممنوع می‌کند
- `require_release_context()` بلافاصله قبل transport
- یک tenant + یک platform + سقف یک آیتم
- dry-run diff و confirmation دوم
- systemd/timer change تأیید جدا

اگر هر کدام غایب است، فاز O11 اجرا نمی‌شود و manual-first حالت production
باقی می‌ماند.

### فاز O12 — پایلوت ۱۴روزه

روز صفر:

- partner walkthrough واقعی هر پنل
- پنج سناریوی seeded اما بدون PII واقعی
- screenshot و زمان انجام هر سناریو

هر روز:

- overdue، manual completion، held/failed
- lead response lag
- listing readiness و sale receipts
- studio blocked reasons
- connector freshness

هر هفته:

- outcome measured
- funnel conversion
- کارهای دستی فراموش‌شده
- false blocker / unsafe bypass attempt
- partner friction notes

هیچ threshold موفقیتی اختراع نکن. در روز صفر آری thresholdها را ثبت کند و
تست/گزارش همان‌ها را بخواند.

### فاز OZ — gate نهایی، deploy و handoff

```bash
python3 -m pytest -q
python3 tools/repo_baseline.py --tests
python3 -m ofn.preflight
```

با حکم deploy:

```bash
sudo systemctl restart ofn
systemctl is-active ofn
for p in 8791 8792 8793 8794; do
  curl -fsS -o /dev/null "http://127.0.0.1:$p/"
done
ss -lntp | rg ':8090\b' && exit 1 || true
```

سپس:

- API contract smoke
- migration read-back
- backup metadata/verify بدون خواندن archive
- screenshot چهار پنل
- HANDOFF و INDEX
- commit فقط فایل‌های همان فاز؛ `.bak-*` بیرون

---

## ۹) تست‌های معماری غیرقابل‌حذف

فایل‌های تازه/گسترش‌یافته باید این خواص را pin کنند:

1. هر mutation → canonical state + ledger event.
2. owner projection read-only است.
3. approval هرگز به‌تنهایی `in_flight/sent/completed` نمی‌شود.
4. manual completion دو بار، یک effect.
5. packet bytes/hash با receipt تطابق دارند.
6. kill و closed gates در completion دوباره سنجیده می‌شوند.
7. هیچ credential/raw webhook/PII در ledger یا owner aggregate نیست.
8. tenant A با ID حدس‌زده tenant B را نمی‌خواند/نمی‌نویسد.
9. هر schema تازه WAL/FULL و migration idempotent دارد.
10. power cut ambiguity → held، نه resend.
11. UI دکمهٔ بدون handler و success جعلی ندارد.
12. UI partner فارسی گرم، D-22 و D-19 را رعایت می‌کند.
13. every count has independent query/source.
14. old API aliases تا migration clientها باقی می‌مانند.
15. no direct-message credential or sender symbol anywhere in repository.

---

## ۱۰) سفرهای پذیرش نهایی

### A — لید

fixture لید → duplicate warning → follow-up due → reply packet → owner approval
→ manual completion → interaction exactly once → next_action تازه → owner
workboard count کم شود.

### B — زیمان

قطعه → عکس/قیمت → ready-to-list → listing packet → approval → manual publish
receipt → sale با amount/fee معلوم یا unknown → margin فقط با دادهٔ کافی.

### C — استودیو

media library → انتخاب در UI → ساخت draft → attach media → read-back board →
felt-right → route preview → consent gap → owner release metadata → packet.
با `partner_precondition` بسته completion باید رد شود و هیچ state موفقی ثبت
نشود. این سفر باید از UI شروع شود؛ fixture دارای draft از قبل، تست پذیرش
محسوب نمی‌شود.

### D — owner

چهار tenant دیده شوند؛ سه بیزنس در portfolio KPI؛ pending/approved/held/
overdue drill-down؛ refresh هیچ mutation نسازد.

### E — webhook

fake signed event → normalized safe receipt → duplicate retry no-op؛ same ID
با body متفاوت → held؛ unsigned/tenant mismatch → reject.

### F — restart/power

approved manual بعد restart باقی بماند؛ crash وسط completion reconciliation
gap بسازد؛ هیچ آیتمی خودکار دوباره ارسال یا completed نشود.

---

## ۱۱) تصمیم‌هایی که ایجنت حق ندارد به‌جای آری بگیرد

- بازکردن `secret_rotation`
- متن و زمان `partner_precondition`
- vendor رسمی و scope
- فعال‌سازی public PII form
- privacy/retention/delete policy
- sales/contact channel زیمان و کارمزدش
- هدف و بودجهٔ کمپین واقعی
- روشن‌کردن هر WIRE
- systemd/timer/Cloudflare change
- sender/public publish adapter
- merge/خاموش‌کردن `hypno-fugu-mini.service`

در UI و HANDOFF این‌ها را با «منتظر حکم آری» نشان بده؛ workaround یا default
پنهان نساز.

---

## ۱۲) دستور کوتاه برای ایجنت اجراکننده

```text
MEGAPROMPT-BUSINESS-OPERATIONS-LAUNCH.md را کامل بخوان.
فاز O0 را اجرا و baseline را ثبت کن.
O1 تا O8 را به ترتیب، هر کدام با تست کامل و commit جدا اجرا کن.
اگر فاز قبلی سبز نیست، وارد بعدی نشو.
O9 را فقط local-only طراحی/تست کن و برای public activation توقف کن.
O10 تا O11 بدون حکم صریح آری ممنوع‌اند.
هیچ outbound واقعی، secret read، WIRE change یا systemd change نزن.
در پایان هر فاز HANDOFF را با واقعیت زنده تازه کن.
```
