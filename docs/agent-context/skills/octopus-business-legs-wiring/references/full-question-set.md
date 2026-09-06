# FINAL — چه چیزهایی از ایجنت بعدی بپرسی تا پاهای بیزنسی سه‌برد امن به لپ‌تاپ وصل شود و خودمختاری واقعی برقرار گردد

created: 2026-09-03 20:10 (UTC+10:00)
vantage: laptop (اختاپوس لپ‌تاپ) · mesh: 138 / 180 / 182
mode: READ-ONLY FIRST · NO APPROVE_ONCE · HOLD_EXTERNAL UNTIL OWNER GATE
purpose: کامل‌ترین فهرست دیتای موردنیاز، با شاهد اندازه‌گیری‌شده، قبل از هر سیم‌کشی اجرایی و قبل از اعلام خودمختاری

---

## خلاصهٔ تصمیم‌های معماری (این‌ها را قبل از سؤال‌ها بپذیر)

1. «برد ۳» = حلقهٔ سه‌بردِ 138/180/182 است (پاها روی یک برد نیستند؛ روی مش پخش‌اند). این فرض را از ایجنت بعدی تأیید بگیر.
2. نقش پیشنهادی نودها:
   - 138 = gateway / supervisor / telegram card / owner gate
   - 180 = brain / decision / rank / proposal
   - 182 = witness / verify / NATS / receipts
   - laptop = آینهٔ فقط‌خواندنی رسیدها + سطح APPROVE + vault (نه نود تصمیم‌گیر زنده)
3. خودمختاری امن = حلقهٔ «حس → تشخیص → پیشنهاد → verify → کارت → رسید» خودش بچرخد؛ ولی money/price/ads/publish/send/contact/secrets/restart/kill/policy پشت گیت انسانی بماند.
4. ترتیب کار: اول حقیقت و رسید، بعد بستن dead-letter و drift، بعد سیم‌کشی، بعد dry-run، و تازه بعد خودمختاری. برعکسش ممنوع.

---

## قوانین آهنین (تغییرناپذیر — به ایجنت بعدی هم تحمیل کن)

```text
- فقط READ-ONLY. هیچ APPROVE_ONCE.
- هیچ external action: send, contact, publish, price change, ads/budget, restart, kill, secret-read.
- هر چیزی UNKNOWN است تا رسید داشته باشد. بدون رسید = LIVE فرض نکن.
- بدون consumer، یک قابلیت «کار نمی‌کند».
- اگر دیتا ناقص است، سیستم باید بخوابد، نه حدس بزند.
- راز فقط دست مالک. ساخت/چرخش کلید فقط با اجازهٔ مالک.
- لپ‌تاپ نباید خودش را به‌جای برد ببیند (جلوگیری از split-brain / wrong-body).
```

## قالب پاسخ اجباری برای هر بند

```text
id:
claim:
node_id:
command / read_method:
output_excerpt:
evidence_path:
sha256_or_commit:
timestamp_utc:
status: LIVE | BLOCKED | PARKED | UNKNOWN | BROKEN | OWNER_DECISION
risk:
next_smallest_safe_step:
```

---

## 0) ابهام‌هایی که اول باید روشن شود

```text
0.1 «برد ۳» = مش سه‌برد است یا یک برد فیزیکی خاص؟
0.2 نقش دقیق 138 / 180 / 182 با شاهد تأیید شود.
0.3 «وصل به لپ‌تاپ» = mirror/approval فقط‌خواندنی است یا نود فعال؟ (پیشنهاد: اولی)
0.4 اگر نود فعال شود، دقیقاً چطور جلوی split-brain/wrong-body گرفته می‌شود؟
0.5 تعریف عملیاتی «خودمختاری واقعی» از نظر مالک چیست: تا کجا بدون APPROVE؟
```

---

## A) حقیقت runtime هر نود (138 / 180 / 182 / laptop)

```text
A1  hostname / IP / OS / uptime / کاربر ssh / سطح دسترسی
A2  کدام درخت کد واقعاً اجرا می‌شود؟ مسیر دقیق
A3  branch + HEAD + dirty state درخت اجرایی
A4  آیا 138 هنوز روی fix/env-independent-tests-20260903 @ 10de2e13 است یا به main برگشته؟
A5  origin/main فعلی چیست؛ هر نود چند ahead/behind است؟
A6  services و timers: systemctl list-units / list-timers 'octopus-*' + failedها
A7  پورت‌های LISTEN (ss -tlnp) هر نود
A8  روی 180: چرا :8081 گوش می‌دهد ولی HTTP گیر است؟ وضعیت دقیق
A9  روی 138: ofn / supervisor / settler / :8895 واقعاً سبزند؟ شاهد
A10 روی 182: NATS بالاست؟ subjectها و clientها
A11 organism روی 138 هست یا فقط 180 مغز است؟ (گزارش: نیست)
A12 ~/octopus-mesh روی 138/180 نسخه‌نشده است؟ حجم/فایل‌های اجرایی/mtime/manifest
```

## B) نقشهٔ ارتباط سه‌برد (transport / mesh)

```text
B1  جریان واقعی event با یک نمونهٔ JSON: signal → 180 → 182 → 138 → owner → exec → receipt
B2  schema دقیق cognitive_wake.v1 + نمونهٔ واقعی
B3  چه چیزی حق دارد 180 را بیدار کند؟ فقط 138؟
B4  پروتکل WR به 182: مسیر/schema/TTL/ack/receipt
B5  NATS روی 182: subjectهای ۷ فید عمومی (weather/AQI/time/FX/BOM/Guardian/USGS)
B6  هر subject مصرف‌کنندهٔ واقعی دارد یا فقط publish می‌شود؟
B7  NATS هنوز تک‌کلاینت است یا مصرف‌کنندهٔ دوم واقعی دارد؟
B8  inbox/outbox هر نود کجاست؟ pending / oldest / newest / expired / rejected / sent
B9  پای 138→182 هنوز مرده است؟ علت ریشه‌ای؟
B10 پای 182→138 هنوز سالم است؟ آخرین receipt
B11 octopus-drain دقیقاً چه چیزی retry و چه چیزی skip می‌کند؟
B12 skip table و COMM-LOOP-v1-SKIP-20260901.json (sha 7ba4ef33) چه payloadهایی را دوباره verdict نمی‌دهند؟
B13 dual-outbox روی 138 چیست؟ هش‌ها چطور تطبیق می‌شوند؟ آخرین PASS
B14 دستهٔ 18/18 چیست، کجا deploy نشده، چرا 1522 دست‌نخورده؟
```

## C) وضعیت سه پای بیزنسی

### C1) Painting
```text
- payload کامل روی bizop-20260827T223048Z کجاست؟ مسیر + SHA
- چرا 1515/1516/1517 روی 138 EXPIRED_UNEXECUTABLE شدند؟ payload/TTL/علت/receipt هرکدام
- الان active است یا «خواب» طبق هارمونی؟
- signal ورودی از کجا؟ (IMAP / buy.nsw / فرم / دستی / sqlite)
- consumer واقعی کجاست؟
- چه چیزی autonomously مجاز است و کجا owner approve لازم است؟
- آخرین business receipt موفق کجاست؟
- outbound/WAL برای painting armed است یا disarmed؟
```

### C2) Ziman Gift
```text
- ziman-gift.com: روشن / password off / cart works / AUD / Basic / Sydney؟ (تأیید زنده)
- orders 30d = 0 هنوز درست است؟
- ایمیل owner-email (vault: ZIMAN-SEASON) فعال؟ contact فقط فرم است؟
- GST در admin exclusive؛ نمایش به مشتری چه باید باشد؟ (تصمیم مالک)
- کاتالوگ: 35 / 29 ACTIVE / 5 DRAFT / 1 ARCHIVED هنوز درست است؟
- 4 draft بی‌عکس: soft-flower-gift-basket / pink wooden nail-set / strawberry / light-green woven
- archived test SKU هنوز فارسی است؟ نیاز به اقدام دارد؟
- ziman-shopify-titles-20260903-b.json روی 138 (sha 161a167e) — تأیید مسیر/هش
- 180-ZIMAN-TITLE-REVIEW-20260903.json روی 180 (sha 526f852f…) — تأیید مسیر/هش
- shipping/policy 404: کدام URL؟ متن لازم؟ (تصمیم مالک)
- footer هنوز لینک demo Shopify دارد؟ کدام؟ حذف/جایگزینی؟
- هندل واقعی Instagram/Facebook — مالک باید بدهد
- Google & YouTube نصب ولی publish نشده — publish = external action، گیت مالک
- Judge.me / GA4 / Search Console: داده دارند یا فقط نصب؟
- first-wave ads (۸ محصول): فقط ranking است یا campaign draft؟ روشن نشده، درست است؟
- هیچ قیمتی تغییر نکرده؟ شاهد
- بدون عدد بودجهٔ مالک هیچ budget ساخته نشود — این guard کجاست؟
- توکن Pi فقط product/order — برای order-ingest / money loop چه scope کم است؟
- order-ingest واقعی از Shopify به اختاپوس هست یا شکاف parity؟
- آخرین receipt موفق Ziman کجاست؟
```

### C3) Studio / Nova Soles
```text
- چرا هنوز BLOCKED است؟
- کدام فیلدها UNKNOWN: identity / offer / product / channel / contact / payment / policy / inventory؟
- کدام دیتا owner باید بدهد، کدام را agent می‌تواند read-only کشف کند؟
- تا unblock، چه rule باعث خواب/عدم بیدارباش 180 می‌شود؟
- آخرین payload/سند معتبر studio کجاست؟
```

## D) طراحی اتصال لپ‌تاپ (read-only first) — مهم‌ترین بخش

```text
D1  «laptop hop» / «Windows hop» که مدام drop می‌شود دقیقاً چیست؟ چرا down می‌شود؟ (این لینک همین حالا شکننده است — بدون پایداری‌اش خودمختاری بی‌معناست)
D2  PC_worker چیست، چه دسترسی‌ای دارد، و آیا 29-handle list را روی 138 drop کرد؟ مسیر/receipt
D3  الان دقیقاً چه مسیر شبکه‌ای بین لپ‌تاپ و بردها هست؟ (ssh؟ فقط GitHub؟ فایل‌کوریر دستی؟) با IP/پورت واقعی
D4  boards → laptop چه چیزی sync شود؟ (receipts / business events / queue summaries / blocked fields / owner cards / runtime-truth snapshots)
D5  laptop → boards چه چیزی مجاز باشد؟ فقط owner-approved decision یا event proposal — با schema
D6  laptop نباید چه چیزی مستقیم push کند؟ (external send / price / ads / publish / restart / secrets)
D7  بهترین مکانیزم sync: ssh pull / rsync read-only / git append-only / NATS bridge — مزیت و ریسک هرکدام
D8  اگر mirror فقط‌خواندنی است، schema فایل mirror چیست؟
D9  اگر approval surface است، owner decision چطور signed و receipted می‌شود؟
D10 چطور node_identity در همهٔ self-model/receiptها اجباری شود تا wrong-body تکرار نشود؟
D11 ارگانیسم لپ‌تاپ (8771–8776) باید از حلقهٔ بیزنس جدا بماند؟ اگر دخالت کند، ریسک split-brain چیست؟
```

## E) گیت‌ها و خودمختاری امن

```text
E1  WAL/outbound gate برای هر پا armed است یا disarmed؟ شاهد
E2  «تلگرام مال من نیست» یعنی چه؟ بات pi 4+1 مالک/محدوده؟ botهای فعال و scope هرکدام
E3  چرا مالک گفت APPROVE_ONCE نده؟ کدام مسیر خطرناک است؟
E4  کارت تلگرام روی 138 چطور ساخته می‌شود؟ schema کارت / command id / TTL / status / receipt اجرا
E5  HOLD_EXTERNAL دقیقاً کجا enforce می‌شود؟
E6  EXPIRED_UNEXECUTABLE چه حالت policy/runtime است؟ چه چیزی اجازهٔ execute را می‌گیرد؟
E7  فهرست دقیق actionهای مجازِ autonomous (scan/rank/proposal/card/verify/receipt/dry-run؟)
E8  فهرست دقیق actionهای owner-only + محل enforce در کد (file/function/flag)
E9  repair_api (اگر هست): whitelist و dry_run default تأیید شود؛ به business legs ربط دارد؟
```

## F) هارمونی بقا / خواب و بیداری

```text
F1  تعریف اجرایی «کم‌رویداد / یک مغز / دو شاهد / خواب وقتی ناقص» با کد یا receipt
F2  180 دقیقاً کِی بیدار می‌شود؟ فقط cognitive_wake.v1؟
F3  180 کِی «ول می‌کند»؟ (UNKNOWN / کارت مرده / پای غیر-سیزن / :8081 داغ) — کجا کد شده و قابل اندازه‌گیری است؟
F4  SAFE_HALT در supervisor 138 کجاست و چه triggerهایی دارد؟
F5  quiet hours / rate limit / TTL بیدارباش‌ها چیست؟
F6  اگر دیتا ناقص است، proposal بسازد یا بخوابد؟ rule دقیق
F7  جلوگیری از busy-loop چطور enforce می‌شود؟
F8  آخرین بار 180 به‌خاطر incomplete data خوابید/hold کرد کجاست؟ receipt
```

## G) دیتابیس / رسید / شاهد

```text
G1  sqlite زندهٔ 138 کجاست؟ (~/.local/share/ofn/*.sqlite) — command خواندن read-only
G2  جدول‌های business/event/receipt/queue + schema summary
G3  آخرین شمارش receipts / rejected / expired / pending
G4  receiptهای witness روی 182: WAIT-merge-20260901T141419Z.json (3bba2cf6…) / SKIP-1ab64100-4f75b619.json (604298a8) / COMM-LOOP-v1-SKIP-20260901.json (7ba4ef33)
G5  self_model.json (sha 0f9a3183) کجاست و مربوط به کدام نود؟ APPLY=false تأیید
G6  برای هر leg آخرین successful receipt (painting / ziman / studio)
G7  اگر receipt نیست → status باید UNKNOWN/BLOCKED باشد، نه LIVE
```

## H) GitHub / drift / آشتی

```text
H1  وضعیت PRهای business-related: #140 audit / #141 off-until-URL / #142 / #144 / #150 repair_api و ...
H2  کدام روی main است، کدام نیاز به merge از UI مالک دارد؟ («142 بعد 144» هنوز معتبر است؟ با gh read-only چک شود)
H3  board138 از main diverged است؟ اثرش روی business behavior چیست؟ merge یا revert؟ (تصمیم مالک)
H4  repo brain چه چیزی ندارد که mesh دارد؟ (economy/campaign / Shopify order-ingest / mesh runtime code / telegram glass)
H5  ~/octopus-mesh نسخه‌نشده: archive/manifest/git-init؟ (پیشنهاد بدون write)
H6  هر ادعای سند که با runtime تناقض دارد → DRIFT list
```

## I) تصمیم‌های مالک (فقط این‌ها را بخواه؛ چیزی اختراع نکن)

```text
I1  Ziman shipping policy: متن/قانون ارسال
I2  social: هندل واقعی Instagram/Facebook یا تصمیم حذف لینک دمو
I3  Google/YouTube: اجازهٔ publish یا hold
I4  ۴ draft بی‌عکس: عکس بده یا archive/hold
I5  GST display: tax-inclusive یا exclusive؟
I6  ads: بودجهٔ عددی + سقف روزانه؛ بدون عدد = no ads
I7  Telegram: مالک/محدودهٔ بات pi 4+1
I8  painting: این سیزن فعال باشد یا خواب بماند؟
I9  studio: هویت/offer/channel اولیه
I10 laptop: mirror/approval فقط‌خواندنی یا active node؟
I11 SSH/keys: اجازهٔ ساخت/چرخش کلید بین لپ‌تاپ و بردها؟
```

## J) تست پذیرش قبل از اعلام خودمختاری (dry-run بدون اثر خارجی)

```text
synthetic business signal
→ 138 creates cognitive_wake.v1
→ 180 ranks/decides (proposal only)
→ 182 verifies PASS/FAIL
→ 138 owner card با HOLD_EXTERNAL
→ laptop read-only mirror دریافت می‌کند
→ owner decision path دیده می‌شود ولی اجرا نمی‌شود
→ receipt روی همهٔ نودهای درگیر نوشته می‌شود

شرط قبولی:
1. node_id در همهٔ receiptها هست
2. SHA/branch runtime معلوم است
3. هیچ external action انجام نشده
4. دیتای ناقص = خواب، نه حدس
5. owner-only actions fail-closed
6. laptop دچار wrong-body نمی‌شود
7. هیچ queue در dead-letter نمی‌ماند یا صادقانه BLOCKED گزارش می‌شود
```

## K) خروجی‌هایی که ایجنت بعدی باید تحویل دهد

```text
1. BUSINESS-LEGS-RUNTIME-TRUTH.md      (A)
2. THREE-BOARD-COMM-MAP.md             (B)
3. BUSINESS-LEGS-BLOCKERS.md           (C)
4. LAPTOP-CONNECTION-DESIGN-READONLY-FIRST.md (D)
5. OWNER-DECISIONS-NEEDED.md           (I ≤ 11 آیتم)
6. AUTONOMY-DRY-RUN-PLAN.md            (J)
7. DO-NOT-TOUCH.md                     (همهٔ forbiddenها)
```

> قانون نهایی: تا این ۷ خروجی با شاهد نیامده، هیچ سیم‌کشی اجرایی، approve، publish، send، ads، price change، restart یا secret action انجام نشود؛ و «خودمختاری» اعلام نشود.
