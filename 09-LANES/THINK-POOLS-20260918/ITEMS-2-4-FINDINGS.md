# RUN-TO-COMPLETION — آیتم‌های ۲ و ۴ (یافته‌های اندازه‌گیری‌شده)

## آیتم ۲ — بازتعریف شد (فرضِ خود پلن غلط بود)

`state/revenue-drive/lead_enrich.py` (۹۷ خط) **هیچ فراخوانی مغزی ندارد** — grep
روی brain/llm/model/api/urllib صفر نتیجه داد. پس اسکریپت‌های لید **نمی‌اندیشند**؛
فقط داده جابه‌جا می‌کنند.

مصرف‌کننده‌های واقعی مغز همان ۱۵ فایلی هستند که در `PERFUSION-REPORT.md` §رگِ مغز
فهرست شدند — یعنی `remote_brain` و `brainport` و `coding_worker` و
`cognition_factory` و `capaware_scheduler`. **آیتم ۲ باید روی این فهرست اجرا شود،
نه روی lead_enrich.** (اصلاح پلن با اندازه‌گیری — درس همیشگی.)

## آیتم ۴ — جدول نام مدل‌ها، تأییدشده از رجیستری

| پروایدر | standard | strong | frontier |
|---|---|---|---|
| gemini | gemini-3.8-flash | gemini-3.1-pro-preview | **gemini-3.8-flash** ⚠️ |
| deepseek | deepseek-flash | **deepseek-flash** ⚠️ | **deepseek-flash** ⚠️ |
| openai | gpt-5.6-terra | gpt-5.6-sol | gpt-6-astra |
| anthropic | claude-sonnet-5 | claude-opus-5 | claude-fable-5-1 |
| sakana-fugu | fugu | fugu-ultra | fugu |

### دو ناهمخوانی مفهوم↔تنظیمات (همان چیزی که ممیزی دنبالش است)

۱. **`frontier` گوگل از `strong` خودش ضعیف‌تر است** — frontier یک مدل *flash*
   می‌گیرد در حالی که strong مدل *pro-preview* می‌گیرد. یعنی اگر روزی
   `tier=frontier` استفاده شود، کیفیت **پایین‌تر** از strong می‌آید. احتمالاً خطای
   تنظیم، نه طراحی.

۲. **deepseek هیچ پله‌ای ندارد** — هر سه tier همان `deepseek-flash` است. پس
   مسیریابی به deepseek در tier قوی، «مدل قوی‌تر» نمی‌دهد؛ فقط همان مدل است.
   در جدول‌بندی هزینه/کیفیت باید لحاظ شود.

هر دو مورد **بدون تغییر** ثبت شدند (تصمیم تنظیمات پروایدرها بیرون از مرز این
نشست است) — گزارش می‌شود تا در گام بعد با GO رفع شوند.
