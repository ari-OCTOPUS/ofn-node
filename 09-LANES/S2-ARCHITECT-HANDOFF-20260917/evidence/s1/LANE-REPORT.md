# بلوغ اختاپوس — اجرای معماری‌محور ۲۰۲۶-۰۹-۱۷

GOV_VERSION=V8 · LADDER=L2 · Lane owner: root.
Status: PARTIAL_IMPLEMENTATION_WITH_MEASURED_EVIDENCE; FULL_MATURITY_NOT_ACHIEVED.

## اختیار ثبت‌شده

متن مستقیم مالک و هش دو پیوست در OWNER-SCOPE.json ثبت شد. اجازهٔ پیش‌برد D1–D5
به همراه شرط‌های خودشان پذیرفته شد؛ این ثبت امضای رمزنگاری‌شده نیست. توضیح بعدی
مالک: سقف ۱۰۰/۱۰/۲ به USD و فقط هزینهٔ API تعلق دارد. Studio همان کسب‌وکار
OnlyFans مورد اشارهٔ مالک است. اجازهٔ مهندسی جای رسید settlement، شروط rehearsal
یا release دوگامیِ خود قرارداد را نمی‌گیرد.

## نتیجهٔ قابل اثبات

| مسیر | انجام‌شده | مرز باقی‌مانده |
|---|---|---|
| T1 سنسوریوم | وصلهٔ transition و دوام؛ ۲۵ آزمون؛ SIGKILL روی ۱۰۰ و ۱۶۰ با بایت‌های یکسان | bundle NOT_READY: مصرف واقعی batch، replica کامل، retention/replay، genesis و RSS یک‌ساعته |
| T2 فلیت | مشاهدهٔ SSH احرازشدهٔ هر هفت نود و ثبت مدل/boot/حافظه/leaf | heartbeat امضاشده احراز نشده؛ نقش‌ها DECLARED |
| T3 خودمدل | مصرف واقعی مشاهدات ۷ نود در producer محلی روی مبنای کد فعلی ۱۳۸ | هنوز روی daemon یا timer زنده مستقر نشده |
| T4 کار ۱۰۰/۱۶۰ | ۱۰۰ اجرای rehearsal واقعی؛ ۱۶۰ بازاجرای مستقل همان کد و corpus | worker دائمی/صف کار سراسری هنوز برقرار نشده |
| T5 RevenueRun | قرارداد hash-chain و مصرف‌کنندهٔ replay با تست منفی | تولیدکننده‌های کسب‌وکار هنوز سیم‌کشی نشده‌اند؛ cash_verified=false |
| T6 Ziman | قیود canary و hold_external حفظ و ثبت شد | اجرای اقتصادی زنده NOT_RUN؛ release جداگانهٔ الزامی باقی است |
| T7 Painting | در دامنهٔ فعال Trident ثبت شد | intake→payment زنده و هشت lead این نوبت اجرا نشد |
| T8 Studio | بستهٔ اداری owner-ready مطابق پاسخ مالک | اتصال حساب، release و فروش واقعی اثبات نشده؛ انتشار صفر |
| T9 دریل | امضای آینه و بازیابی ۷/۷ فایل به replica با هش و parse برابر | بازیابی مصرف‌کنندهٔ واقعی و kill-switch سراسری NOT_RUN |
| T10 بودجه | یک منبع USD/API و اتصال به CallBudget/fake_executor، تست منفی | دفتر رزرو اتمیک و تمام callerهای پرداختی runtime هنوز متصل نیستند |

## تصحیح شواهد قبلی

عدد قبلی ۹٫۲× محصول monkeypatch حذف fsyncها بود، نه وصلهٔ batch آمادهٔ سرویس.
API واقعی جدید پیش از ACK یک fsync انجام می‌دهد و در دو میزبان با چهار نقطهٔ
SIGKILL سنجیده شد؛ ACK گم‌شده در موارد اجراشده صفر بود. بایت و replay روی ۳۰۰۰
رویداد واقعی برابر شدند. n=1 برای هر variant در هر میزبان: UNDERPOWERED؛ کاهش
RSS و سرعت سنسوریوم زنده ادعا نمی‌شود. SIGKILL معادل قطع برق نیست.

شاهد قدیمی W1 هنگام خطای pgrep آرایهٔ خالی می‌نوشت؛ بنابراین کامل‌شدن زمان به‌تنهایی
اثبات موفقیت probe نیست. گزارش و collector قبلی حفظ شدند. sidecar مستقلِ فقط‌خواندنی
با ثبت returncode و خطا شروع شد، PID ثبت‌شده 764170 روی ۱۸۲، منبع دقیق با SHA
تأیید شد. پایان برنامه‌ریزی‌شده 2026-09-18T09:11:20Z، یعنی حدود ۱۹:۱۱ سیدنی.
اولین نمونه probe_status=OK بود؛ حکم نهایی هنوز RUNNING است. نمونه‌برداری پنج‌دقیقه‌ای
نمی‌تواند فرایند کوتاهِ بین نمونه‌ها را نفی کند. هیچ پنجره‌ای کوتاه یا سبز اعلام نشد.

## آزمون و منشأ

- بستهٔ یکپارچهٔ source-aligned: ۱۶۹ تست اصلی در دو انتخاب مجزا، XML در lane کد.
- validator/collector شاهد: ۱۴ آزمون مرزی/خطا؛ تغییر سرویس production ندارد.
- سنسوریوم: ۲۵ قرارداد component؛ خطاهای نسخهٔ اولیه و harness جداگانه حفظ شدند.
- تمام هفت اتصال فلیت authenticated بود؛ مشاهدهٔ کد Git ۱۳۸:
  fe0c55e0a952e0048ff6bd3ddb8ab9419cd1dc0d. این SHA به‌تنهایی revision بارشدهٔ daemon نیست.
- mirror manifest: 0628dafdbdd727121bdeea0a3298fae2a061812fc08d303d51a97c3f64726d4d.
  امضا با allowed_signers موجود تأیید شد؛ sourceها پس از restore دست‌نخورده بودند.

## مسیرهای دقیق

- کد یکپارچه: F:/wt-s1-fleet-self-model-20260917؛ lane
  09-LANES/S1-FLEET-SELF-MODEL-20260917/LANE-REPORT.md.
- سنسوریوم و رسید دو میزبان: F:/s1-t1-rehearsal-20260917/09-LANES/S1-T1-REHEARSAL-20260917/.
- بستهٔ Studio/RevenueRun: F:/ofn-revenue-contract-20260917/09-LANES/S1-REVENUE-CONTRACT-20260917/.
- سابقهٔ بودجه: F:/wt-s1-budget-canonical-20260917/09-LANES/S1-BUDGET-CANONICAL-20260917/.
- شاهد جدید روی ۱۸۲: /root/s1-maturity-w1-20260917/observations.jsonl.
- replica آینه روی ۱۸۲: /root/s1-maturity-mirror-replica-20260917/.

## ادامهٔ دقیق و rollback

اول actual batch consumer و reader مبتنی بر anchor/segment را در replica کامل تکمیل
کن؛ آستانهٔ مهندسی RSS=1536MiB در آزمون T+1h از پیش ثبت شده، هنوز اندازه‌گیری نشده.
سپس شاهد مستقلِ بایت‌های نهایی، backup و rollback، یک ریاستارت دقیق و read-back لازم
است. snapshot جدید بدون تغییر reader، به‌تنهایی واگرایی تاریخی را حل نمی‌کند.
هم‌زمان monetary reservation را در ModelRouter.ask پیش از brain.answer به دفتر پایدار
متصل کن؛ admission بدون رزرو اتمیک ضد overspend نیست. سپس producerهای یک RevenueRun
واقعی را به قرارداد مشترک وصل کن. هیچ پرداخت یا موفقیت مالی از fixture استنتاج نشود.

تغییرات production سنسوریوم/۱۳۸: صفر. تغییرات زندهٔ این نوبت فقط sandboxهای مستقل
۱۰۰/۱۶۰ و replica/collector خصوصی ۱۸۲ بودند. توقف sidecar فقط با احراز PID 764170
و مسیر همان اسکریپت مجاز است؛ evidence و watcher قبلی حفظ شوند. برای rollback کد،
فقط commit همین شاخهٔ ایزوله revert شود؛ checkoutهای کثیف و لِین‌های دیگر دست‌نخورده‌اند.
هیچ secret، پیام مشتری، پرداخت، انتشار، reboot یا تغییر quota اختیار انجام نشد.

بلوغ کامل هنوز قابل اعلام نیست: چرخهٔ زندهٔ lead→settled_cash، T1 کامل، self-model
زنده و دریل کامل دوگانه هنوز شواهد لازم را ندارند. مانع فعلیِ T1 فنی و آزمونی است؛
اجازهٔ کلی مالک دوباره درخواست نشده است.
