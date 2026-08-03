# LANGAR — ارتقاهای این دور (به‌سمتِ چشم‌اندازِ Unified Agent Prompt)

تاریخ: ۲۰۲۶-۰۶-۲۸ · اصل: بدونِ حذف/بازنویسیِ کلی — فقط فایلِ جدید + تغییرِ کوچکِ ایمن.

## چه چیزی واقعاً ساخته و **تست** شد (۲۲ تستِ سبز)

**۱) لایه‌ی ۳ حافظه — بازیابیِ ترکیبیِ محلی** — `langar/core/retrieval.py` (جدید)
از غیرفعال → فعال. BM25 (sparse) + TF-IDF cosine (dense) + fusionِ min-max. کاملاً
**محلی و بدونِ کلید/embedding** (همسو با اصلِ privacy/local-first). فارسی‌آگاه (نرمال‌سازیِ ي/ك، حذفِ اعراب، توقف‌واژه).
به `core/memory.py` با تغییرِ کوچک وصل شد: `search_semantic()` حالا واقعاً از reflection/logهای db
یک corpus می‌سازد و top-k را برمی‌گرداند. (تستِ یکپارچه: کوئریِ «کافئین و خواب» سندِ درست را با score=۱.۰ آورد.)

**۲) BrainRouter — انتخابِ عمقِ استدلال و ردهٔ مدل** — `langar/brain/brain_router.py` (جدید)
طبقِ بخش ۳ پرامپت («کِی نَب، کِی عمیق»): task را به `simple/react/plan/deliberate` رده‌بندی می‌کند،
مدلِ `cheap/strong` را انتخاب می‌کند، و وقتی **بودجه کم است یا آفلاین است به‌صورتِ امن downgrade** می‌کند
(fail-degraded، نه fail-closed). budget تزریق‌پذیر است.

**۳) حلقه‌ی ACE — خودپیشنهاددهنده (نه خودویرایش)** — `langar/core/ace.py` (جدید)
طبقِ بخش ۶ + گاردریلِ no-self-edit: `Generator→Reflector→Curator`. از نتایجِ اجرا، الگوهای پرشکست را
می‌یابد و یک **proposalِ procedural** تولید می‌کند که به‌صورتِ `status="pending"` در db ذخیره می‌شود —
**هرگز خودکار اعمال نمی‌شود**؛ انسان approve/reject می‌کند (HITL). `applied_automatically=False` تضمین‌شده.

**۴) تست‌ها** — `langar/tests/test_upgrades.py` (جدید) — بدونِ pytest با `python3` اجرا می‌شود. **۲۲/۲۲ سبز.**

**۵) deploy.sh** (جدید، ریشه) — اسکریپتِ راه‌اندازی + smoke test: چک Docker → ساخت/گاردریلِ .env →
`compose up` → انتظارِ `/health` → گزارشِ وضعیتِ ۴ سرویس. هیچ کلیدی چاپ نمی‌کند، چیزی پاک نمی‌کند.

## نگاشت به ۸ گاردریلِ چشم‌انداز
- kill-switch (`/halt`/`/resume`) ✅ از قبل · owner-only ✅ · Constitution (۱۴ قانون، regex) ✅ ·
  budget cap ✅ · privacy local-first ✅ (retrieval حالا هم محلی است) ·
  **no-self-edit** ✅ (ACE فقط proposal) · data separation (scope در memory) ✅ · audit (event_log/tracer) ✅.

## آنچه هنوز **نیست** (صداقت — برای نسخه‌ی بعد)
- BrainRouter ساخته شد ولی هنوز در حلقه‌ی اصلیِ `bot.py` سیم‌کشی نشده (برای اجتنابِ بازنویسیِ ریسکیِ فایلِ ۱۹۰۰خطی). قدمِ بعد: فراخوانیِ `route()` پیش از مسیرهای سنگین.
- ACE ماژولِ کامل و تست‌شده است ولی جمع‌آوریِ `Outcome`ها از مسیرهای واقعی باید به bot وصل شود.
- retrieval روی reflection/log کار می‌کند؛ گسترش به منابعِ بیشتر و rerank در آینده.
- این یک vector-DBِ کامل نیست؛ برای حجمِ شخصی (هزاران رکورد) کافی است. مسیرِ ارتقا: همان رابط با backend برداری.

## چطور خودت تست کنی
```bash
cd AI-sume/langar
python3 tests/test_upgrades.py     # باید بنویسد: ۲۲ pass / ۰ fail
```

> صداقتِ فنی: همه‌ی منطق به‌صورتِ unit-test سبز شد؛ اجرای واقعیِ ۴ کانتینر و سیم‌کشیِ نهایی به bot
> روی سرورِ توست. این دور، شکافِ معماری را در «هسته» پر کرد، نه در «حلقه‌ی اجرای bot».
