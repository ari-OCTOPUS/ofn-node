# ROADMAP-NEXT-AGENT — نقشهٔ راه ایجنت بعدی (رأی‌های مالک ۲۰۲۶-۰۹-۰۱)

**۱۰ رأی مالک در پرسشنامهٔ ساخت‌یافته ثبت شد. این سند دستور کارِ کدنویسیِ ایجنت بعدی است.
ترتیب اجرا (رأی Q10): گوش → کوت → زیرساخت (زیرساخت به‌عنوان پشتیبان موازی).**

## رأی‌های مالک (صدازده — منبع اقتدار این نقشه)

| # | موضوع | رأی مالک |
|---|---|---|
| Q1 | وضعیت حقوقی | **ABN + بیمه هر دو موجود** → ادعاهای ایمیل صادق‌اند؛ مالک شماره‌ها را می‌دهد تا سنددار شوند |
| Q2 | دامنه | **بله، دامنهٔ .com.au** → مالک می‌خرد؛ ایجنت DNS + SPF/DKIM/DMARC + ترنسپورت دوم |
| Q3 | گوش | **IMAP روی همان Gmail** — هر ۱۵ دقیقه؛ پارس خودکار reply/bounce/opt-out |
| Q4 | فالوآپ | **خودکار: حداکثر ۲ یادآوری، فاصلهٔ ۷ روز** → بعدش nurture-archive (نه حذف) |
| Q5 | استقلال کوت | **کاملاً خودکار — بدون سقف**؛ مالک فقط گزارش می‌گیرد |
| Q6 | قیمت‌گذاری | **از دادهٔ OCP بساز؛ مالک یک بار تأیید می‌کند** — بعد از تأیید، خودکار |
| Q7 | زیرساخت | **هر ۴ لایه**: بکاپ+آزمون restore، systemd+watchdog+heartbeat، digest روزانه، تمیزکاری+تست |
| Q8 | چرخش رمز | **نه، همین بماند** — ریسکِ آشکار-بودن رمز در لاگ چت، پذیرفته‌شدهٔ مالک |
| Q9 | پوش بورد | **deploy key** (این جلسه پیاده شد) — بورد مستقل پوش می‌کند |
| Q10 | ترتیب | **گوش → کوت → زیرساخت** |

---

## LANE E — گوش (اولویت ۱): سیستم بشنود

۵ ایمیل در هواست؛ جواب بی‌خواننده = بی‌جواب می‌ماند.

- **E1** `ofn/agents/imap_listener.py` — poll هر ۱۵ دقیقه از `imap.gmail.com:993` با همان
  `GMAIL_APP_PASSWORD` (IMAP همان رمز اپ را می‌پذیرد — بدون راز جدید). UNSEEN را می‌خواند،
  In-Reply-To/References را با message-id های ارسالی تطبیق می‌دهد (WAL نگه ندارد — از
  events.jsonl / sent mail Folder). طبقه‌بندی: `reply | bounce | optout | noise`
- **E2** reply → lead `status=engaged`، متن در digest مالک؛ اگر scope/قیمت خواست → تریگر LANE Q
- **E3** bounce parser (NDR استاندارد `multipart/report; report-type=delivery-status`) →
  اگر `wrong_recipient` بود: **کمپین envelope kill** (metric خودِ PAINT-L5-001) + آلارم
- **E4** opt-out (STOP/unsubscribe در متن) → فوری `consent_store.insert_suppression` —
  لایهٔ دومِ transport از قبل آن را می‌خواند؛ ارسال بعدی همان‌جا SUPPRESSED می‌شود
- **E5** فالوآپ مجری‌دار (رأی Q4): کرون روزانه؛ `next_action_at<=now AND status=contacted
  AND follow_up_count<2` → یادآوری از همان گیت‌لدر + WAL؛ بعد از ۲ سکوت → `status=nurture`
- **پذیرش**: باتری تست آفلاین برای پارسر (fixture های reply/bounce/stop) + یک canary واقعی:
  مالک یک جواب تست به خودش می‌فرستد و سیستم باید engaged کند

## LANE Q — کوت (اولویت ۲): سیستم پول بنویسد

- **Q1** `ofn/agents/quote_engine.py` — از scope (متراژ/سطح/نوع کار/محل) → کوت رسمی با
  شمارهٔ `QT-YYYYMMDD-NNN` (الگوی موجود در `_qt_number` ترنسپورت)
- **Q2** گسترش `nsw_ocp_harvest` → استخراج قیمت per-m² از قراردادهای مشابه →
  `data/painting_rate_card.json` با حداقل/حداکثر توزیع واقعی. **قفل تأیید مالک (رأی Q6):**
  موتور کوت تا `approved_by_owner: true` نباشد، کوتِ دارای قیمت نمی‌فرستد (فقط کوت بدون قیمت مجاز است)
- **Q3** قالب کوت ساده + امضای سنددار: **ABN و شمارهٔ بیمهٔ واقعی از `secrets/identity.json`** —
  پس از تحویل مالک؛ دیگر هیچ ادعایی hardcode نیست (بستن آیتم‌های ۵۳-۵۴ GAPS)
- **Q4** استقلال کامل (رأی Q5) ولی از همان گیت‌لدر: halt→flag→cap→consent→WAL→SMTP.
  مهارِ درونی بدون نقض رأی: بازهٔ قیمت از rate card (نه عدد آزاد) + جملهٔ اعتبار ۳۰ روزه در
  کوت (مسیر اصلاح اگر قیمت اشتباه شد) + گزارش هر کوت در digest
- **Q5** funnel: reply→quote→win در `funnel.db`؛ **نویسندهٔ `booked_amount_cents`** بالاخره
  ساخته می‌شود (آیتم ۵۲) — پول بستنِ قرارداد از ایمیل تایید استخراج شود با تأیید digest
- **پذیرش**: ۵ کوت نمونه از scope ساختگی با اعداد OCP واقعی؛ رندر بدون کلیشه (گیت `check()`)

## LANE I — زیرساخت (اولویت ۳، موازی)

- **I1** systemd: `octopus-survival.service` + timerها (imap/follow-up/beat/digest) + Restart=always
- **I2** heartbeat: بورد هر ساعت پالس به کانال تلگرام لاگ؛ غیبت >۲ ساعت برای مالک قابل‌دیدن است
  (سکوتِ خودِ بورد فقط از بیرون دیده می‌شود — dead-man-switch، نه self-report)
- **I3** بکاپ شبانه: `sqlite3 .backup` برای هر سه انبار + manifest + sha256 → pull از سمت
  ولت ویندوز؛ **آزمون restore** ماه اول واقعی (آیتم ۱۳ — هیچ‌وقت انجام نشده)
- **I4** digest روزانهٔ صبح تلگرام: ارسال‌ها، جواب‌ها، کوت‌ها، سلامت، پول
- **I5** تمیزکاری: job همگرایی outbox↔WAL↔leads؛ **timezone واحد UTC** (سقف روزانه هم UTC —
  ADR ثبت شود)؛ پاکسازی SHADOW-C1-LIVE؛ migration tracker
- **I6** باتری تست پاها روی بورد + **canary قبل از هر فعال‌سازی بزرگ** (درس آیتم ۷۱) +
  invariant شمارنده=WAL-sent-today
- **پذیرش**: ری‌بوت بورد → همه‌چیز خودش بالا بیاید؛ restore آزمایشی checksum بخواند؛ باتری سبز

## LANE G — هویت و حکمرانی (اقدام مالک + پشتیبانی ایجنت)

- **G1 (مالک)**: خرید دامنهٔ .com.au → (ایجنت) DNS + SPF/DKIM/DMARC + ترنسپورت دوم؛
  Gmail شخصی به fallback
- **G2 (مالک)**: تحویل ABN + شماره بیمه → `secrets/identity.json` روی بورد (نه در چت)
- **G3 (نیمه‌کاره — یک اقدام ۱ دقیقه‌ای مالک)**: کلید deploy ساخته شد (`~/.ssh/ofn_deploy` روی
  بورد) ولی ارگان GitHub «Deploy keys» را خاموش دارد → مالک در وب:
  Organization Settings → Security → Deploy keys → **Allow**. بعدش فقط یک فرمان
  `gh api repos/ari-OCTOPUS/ofn-node/keys` کلید را وصل می‌کند (رأی Q9)
- **G4**: allowlist رسمی OCP در `painting_source_registry.json` (G-51) + تاریخ انقضای
  allowlist دامنه‌های #63
- **G5 (مالک)**: ثبت‌نام buy.nsw eTendering + scheme های پیمانکار — ایجنت checklist می‌سازد

## قواعد ایجنت بعدی (غیرقابل مذاکره)

1. گیت‌لدر ارسال هرگز دور زده نمی‌شود — حتی «فقط یک تست»
2. قفل تأیید rate card تا رأی صریح مالک باز نمی‌شود
3. fake green ممنوع؛ تستِ اجرانشده = شکست
4. هر رأی جدید مالک = ایتسیوی گیت‌هاب؛ ایجنت خودش اقتدار تعیین نمی‌کند
5. شروع از `docs/DISCOVERY.md` و همین سند؛ ابسیدین = CURRENT-TRUTH کانونیکل (NBB-CP)

## پیوند ها

- GAPS-100 (ورودی این نقشه): `GAPS-100-2026-09-01.md` (همان پوشه)
- راهنمای کشف: ریپو `release/p0` → `docs/DISCOVERY.md`
- ایتسیوی گیت‌هاب این نقشه: see repo issues — «NEXT-AGENT ROADMAP»
