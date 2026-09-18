# PROMPT-FIX-13 — بستن ۱۲ anchor ضعیف باقی‌مانده در WHY-SLOW-250

**GOV_VERSION=V8 · LADDER=L2 · Lane: OCTOPUS-WHY-SLOW-250-20260918 (ادامه) · فقط-خواندنی روی runtime (مگر fix نمادین)**

## وضعیت فعلی (اندازه‌گیری‌شده)
چک‌لیست ۲۵۰ تایی از نظر قرارداد کامل است (۲۵۰/۲۵۰، سهمیه‌ها برآورده، صفر فیلد ناقص، صفر reason قالبی) و anchorها الان **۲۳۸/۲۵۰ قابل‌بازکردن**‌اند.
`W-141` در همین سند fix شد (مسیر واقعی فایل حافظه). **۱۲ مورد باقی‌مانده** همه یک الگو دارند: ادعای «نبودن یک قابلیت» (E0) که anchor مستقیم فایل ندارد:

| id | قلمرو | حکم | ادعا |
|---|---|---|---|
| W-070 | T3 | UNVERIFIED | هیچ SLA پاسخ‌دهی به مشتری اعلام نمی‌شود |
| W-072 | T3 | UNVERIFIED | هیچ pricing مبتنی بر ارزش/نتیجه طراحی نشده |
| W-076 | T3 | UNVERIFIED | هیچ فایل بازخورد/رضایت مشتری وجود ندارد |
| W-078 | T3 | UNVERIFIED | زمان تحویل/ظرفیت اعلام نمی‌شود |
| W-079 | T3 | UNVERIFIED | تقویم فصل‌بندی هدیه (کریسمس/نوروز) نیست |
| W-082 | T2 | UNVERIFIED | کانال مارکت‌پلیس/آنلاین آتلیه وجود ندارد |
| W-144 | T6 | PARTIAL | risk روش‌شناسی: fixture آموزشی به‌عنوان holdout (E1) |
| W-228 | T11 | UNVERIFIED | مسیر رزرو/تقویم ملاقات نیست |
| W-229 | T11 | UNVERIFIED | سطح وضعیت/پیگیری برای مشتری نیست |
| W-230 | T11 | UNVERIFIED | کانال SMS/واتس‌اپ استفاده نمی‌شود |
| W-234 | T12 | UNVERIFIED | اندازهٔ بازار هدف اندازه‌گیری نشده |
| W-235 | T12 | UNVERIFIED | اعتبارسنجی پرسونا با خریدار واقعی انجام نشده |

## روش (پروتکل «اثبات نبود»)
برای ادعاهای نبودن، anchor درست **یک جست‌وجوی مستند** است. برای هر ۱۲ مورد:
1. یک فرمان جست‌وجوی دقیق بنویس که اگر آن قابلیت وجود داشت، پیدا می‌شد؛ مثلاً:
   `grep -rniE "booking|calendly|رزرو|SLA|whatsapp|sms|marketplace|etsy|persona|TAM" /home/ari/ofn/state /home/ari/ofn/ofn 2>/dev/null | wc -l`
2. فرمان + خروجی (۰ یا n) + زمان را در `evidence/ABSENCE-PROOFS.md` ثبت کن.
3. `verify_against` هر ورودی را به آن فایل با anchor دقیق (نام فرمان) تغییر بده و `anchor_quality: resolvable` بگذار.
4. اگر جست‌وجو **چیزی پیدا کرد** (یعنی قابلیت وجود دارد): حکم را به `REFUTED` تغییر بده، شاهد مثبت را ثبت کن — این هم نتیجهٔ معتبر است.
5. اگر نه شاهد مثبت و نه منفی پیدا شد: `anchor_quality: withdrawn` + یک خط دلیل. **ساختن مسیر نمایشی ممنوع است** (این چک‌لیست برای مبارزه با همان ساخته شد).

استثناها:
- `W-144`: باید در `tests/` و `state/self-test-train` دنبال سابقهٔ استفاده از fixture به‌عنوان holdout بگردی؛ اگر پیدا نشد → REFUTED با شاهد.
- `W-234`/`W-235`: در وال (`00-SEASON`, `05-BUSINESSES`, `08-PLANS`) و در `state/revenue-drive/owner-review.json` جست‌وجو کن؛ اگر واقعاً نشد → withdrawn.
- `W-141`: انجام شد (مسیر `C:/Users/Armin/.zcode/cli/memories/projects/backup-af03d0fc8a32ab4f/memory/MEMORY.md`).

## معیار پایان
1. `python3 09-LANES/OCTOPUS-WHY-SLOW-250-20260918/evidence/verify_250.py` → anchor quality = **۲۵۰/۲۵۰ resolvable** یا فهرست صریح `withdrawn` با دلیل برای هر استثنا.
2. `evidence/ABSENCE-PROOFS.md` موجود با فرمان‌ها و خروجی‌ها (قابل اجرای مجدد برای ممیز).
3. `MATRIX-250.csv` بازتولید شده و ستون `anchor_quality` برای همه `resolvable`/`withdrawn` (بدون «برچسب»).
4. LANE-REPORT: چند مورد مثبت تأیید شد، چند REFUTED شد، چند withdrawn — با شمار صریح.
