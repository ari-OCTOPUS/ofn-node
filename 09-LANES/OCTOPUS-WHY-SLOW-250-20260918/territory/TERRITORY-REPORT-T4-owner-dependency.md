# TERRITORY-REPORT — T4-owner-dependency (وابستگی به مالک)

`checked: 30 hypotheses · sources: 21 file/probe families · refuted: 0 · confirmed: 11 · partial: 11 · unverified: 8 · owner-needed: 20 · verified-this-session: 17`

## چرا این قلمرو مشکوک بود

> تک‌مالک = تک‌گلوگاه؛ ارسال دومرحله‌ای

## یافته‌های تأییدشدهٔ برتر

- **W-084** (I3×F3) — خرید سرویس تماس DIDWW (حدود $۲۰) هم‌چنان اقدام مالک است و هیچ کارتی برایش در رجیستر نیست
  - دلیل: تصمیم CARD2_CALL_SERVICE=A_DIDWW (09-15)؛ رجیستر کارت‌ها فقط MONEY-BATCH/TRAFFIC/TEST دارد
  - شاهد: 138:state/revenue-drive/owner-decisions.jsonl, owner-ask-registry.json
  - مخرج: یک کارت DIDWW با لینک خرید و مبلغ دقیق بفرست (money=RED پس فقط مالک)
- **W-092** (I3×F3) — erratum over-ACK: برای ۵ کارت ردیف ACK نشست درحالی‌که مالک فقط ۲ کارت را نام برده بود — ۳ رأی جعلی وارد دفتر شد
  - دلیل: owner_decision.v1.jsonl: سه ردیف با note «NOT owner vote» @09-16T20:25:59Z
  - شاهد: 138:state/owner_dialogue/owner_decision.v1.jsonl
  - مخرج: ۵ ردیف را به VOID ببر و قاعدهٔ «ACK فقط با نقل قول متنی مالک» را اعمال کن
- **W-093** (I3×F3) — هیچ قاعدهٔ رفتار برای غیبت مالک (absence) وجود ندارد که تصمیم‌های کم‌ریسک را جلو ببرد
  - دلیل: octopus-absence.timer زنده است ولی هیچ سیاست default-action در state نیست
  - شاهد: 138:systemctl list-timers, ls state/revenue-drive
  - مخرج: سیاست غیبت: وقتی مالک >۴۸h نیست، فقط اقدام‌های internal-green با log اجرا شوند
- **W-097** (I3×F3) — هیچ مکانیزم դեadline/expiry برای ردیف‌های رأی باز نیست؛ رجیستر رأی می‌تواند بی‌نهایت رشد کند
  - دلیل: F-009 backlog + رجیستر بدون فیلد expires_at
  - شاهد: 09-LANES/MP-CAPABILITY-GAP-01-20260907 (F-009)
  - مخرج: فیلد expires_at به هر رأی باز اضافه کن؛ بعد از expiry = پیش‌فرض محافظه‌کارانه
- **W-106** (I3×F3) — هیچ کارتی برای برداشتن hold زیمن وجود ندارد؛ یک قفل راهبردی بدون مسیر رأی مانده
  - دلیل: owner-ask-registry: هیچ کارت ZIMAN/HOLD
  - شاهد: 138:state/revenue-drive/owner-ask-registry.json
  - مخرج: کارت «Ziman: ادامهٔ hold یا آزادسازی محدود» را بساز
- **W-090** (I4×F2) — کل دفتر رأی مالک در ۵ روز فقط ۱۷ ردیف است — نرخ تصمیم‌گیری انسانی (~۲.۶/روز) با سرعت ماشین هم‌تراز نیست
  - دلیل: owner-decisions.jsonl: 17 ردیف از 09-13 تا 09-17
  - شاهد: 138:state/revenue-drive/owner-decisions.jsonl
  - مخرج: تصمیم‌های کم‌ریسک را از دست مالک بردار (لیست سفید ازپیش‌تأییدشده) و فقط RED بماند

## سایر ورودی‌ها (خلاصه)

- W-083 [UNVERIFIED] شمارهٔ تماس نمایشی مالک (AUTO1) هرگز تأمین نشد؛ صف تماس fail-closed از ۰۹-۰۸ خاموش است
- W-094 [PARTIAL] حالت گزارش important-only نویز را کم کرد ولی با قاعدهٔ no-re-ask ترکیب شد و سکوت تصمیم ساخت
- W-108 [PARTIAL] کارت‌های معلق مالک هیچ خلاصهٔ «پیامد ادامهٔ انتظار» ندارند — مالک هزینهٔ تأخیر را نمی‌بیند
- W-S05 [UNVERIFIED] فرمت رأی «تأیید <8hex>» تازه (09-17) است و نرخ تبدیل کارت→رأی هرگز اندازه‌گیری نشده
- W-086 [UNVERIFIED] کلیدهای deploy روی ofn-node غیرفعال‌اند (G1) و شاخه‌های autonomy نمی‌توانند push کنند
- W-091 [PARTIAL] دو ردیف از چهار رأی آخر تست self-addressed بوده، نه تصمیم واقعی — کانال رأی با تست اشغال می‌شود
- W-095 [PARTIAL] فارسی‌سازی کارت‌ها فقط از ۰۹-۱۷T23:29 فعال شده؛ همهٔ کارت‌های قبلی احتمالاً برای مالک سخت‌تر بوده‌اند
- W-099 [PARTIAL] دو کارت MONEY-BATCH پشت سر هم (۰۹-۱۷ و ۰۹-۱۸) همان درخواست را تکرار می‌کنند — ریسک خستگی مالک
- W-101 [PARTIAL] کارت TRAFFIC-DECISION سه گزینهٔ سنگین (بودجه ads / لیست outreach / انتخاب بازار) می‌دهد — هزینهٔ شناختی بالا = تأخیر
- W-102 [PARTIAL] رأی مالک در یک پیام دسته‌ای («همشو موافقم») نشان می‌دهد او batch-prefer است ولی کارت‌ها تکی فرستاده می‌شوند
- W-103 [PARTIAL] پاسخ مالک با پارس متن exact (`go:<id>:<channel>`) است؛ یک غلط تایپی یعنی رأی گم می‌شود
- W-104 [PARTIAL] مالک «director بدون جزئیات فنی» است ولی بعضی کارت‌ها همچنان متن فنی/طولانی دارند
- W-109 [PARTIAL] هر رأی مالک فقط یک‌بار مصرف می‌شود؛ هیچ pre-authorization دوره‌ای (مثلاً هفتگی) وجود ندارد
- W-087 [UNVERIFIED] زنجیرهٔ studio-consent با ۱۴/۱۴ بولت امضانشده، انتشار استودیو را قفل کرده
- W-105 [PARTIAL] تصمیم «هر دو کسب‌وکار هم‌زمان» توجه مالک را نصف می‌کند و هیچ‌کدام full-speed نیست
- W-107 [UNVERIFIED] اقدام فیزیکی مالک (کارت SD/برق بردهای باقی‌مانده) از ۰۹-۱۵ معلق است
- W-085 [UNVERIFIED] امضای owner-key (B1 ED25519) از چت معلق مانده و hash کیس هرگز بازتولید نشده
- W-088 [UNVERIFIED] KYC استودیو (FeetFinder 0/9 + OnlyFans HOLD) صد درصد وابسته به اقدام مالک است
- W-089 [UNVERIFIED] سه امضای pre-registration (K9، judge-bias phase2، four-arm ablation) هرگز زده نشده
