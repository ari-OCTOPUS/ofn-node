# از اینجا شروع کن — اختاپوس و بدن هفت‌بردی

**فایل اصلی:** [NEXT-AGENT-MEGAPROMPT.md](NEXT-AGENT-MEGAPROMPT.md)

هدف: پاسخ بهتر، حافظه‌ای که واقعاً در پاسخ مصرف شود، ادامهٔ کار بدون لپ‌تاپ.
وضعیت بسته: **HANDOFF_READY / FLEET_ACCEPTANCE_OPEN**. این بسته نتیجه اجرای تازه روی بردها نیست.

## محتویات

| فایل | کاربرد |
|---|---|
| [NEXT-AGENT-MEGAPROMPT.md](NEXT-AGENT-MEGAPROMPT.md) | دستور ادامه کامل: دامنه، نقش‌ها، ترتیب اجرا، پذیرش و مرزها |
| [CURRENT-STATE.json](CURRENT-STATE.json) | وضعیت شروع ماشین‌خوان و تفاوت نتیجه گزارش‌شده با دامنه اثبات |
| [NEXT-ACTIONS.json](NEXT-ACTIONS.json) | backlog با وابستگی، مالک مسئول و خروجی قابل‌سنجش |
| [RECONCILIATION.md](RECONCILIATION.md) | رفع ناسازگاری پرامپت قدیمی و رسیدهای جدید |
| [SOURCE-INDEX.json](SOURCE-INDEX.json) | 40 منبع با مسیر اصلی، snapshot و SHA256؛ 14 تطبیق ارجاع داخلی |
| [ARTIFACT-MANIFEST.json](ARTIFACT-MANIFEST.json) | هش فایل‌های بسته، به‌جز خود manifest |
| [LANE-REPORT.md](LANE-REPORT.md) | کار انجام‌شده، محدودیت‌ها، ادامه و rollback |
| [scripts/verify-packet.ps1](scripts/verify-packet.ps1) | بررسی خواندنی سلامت بسته؛ با CheckOriginals تشخیص drift منابع |
| `sources/` | نسخه ثابت منابع؛ شامل attachment مالک، gateها و رسیدهای مربوط |

## نقطه ادامه

P5 از قبل ثبت شده؛ دوباره درخواست GO P5/P6 نکن. PB-4، retrieve واقعی و T3 مسیر ساخت ارزش‌اند.
PB-1 را با شواهد واقعی scheduler و وابستگی لپ‌تاپ ادامه بده؛ ساعت شروع به‌تنهایی کافی نیست.
ماتریس NPU هنوز شش PASS تاریخی + 138 NOT_RUN است؛ صحت کاربردی خروجی و سلامت benchmark جدا بررسی شوند.

این NEXT در ناوبری جایگزین توصیه «P5 را شروع کن» در NEXT قبلی است. سندهای تاریخی، gateها،
رسیدها و نتایج قدیمی عوض نشده‌اند. برای runtime، شواهد تازه مقدم بر این بسته است.

## متن کوتاه برای تحویل به ایجنت بعدی

```text
فایل F:\backup\09-LANES\OCTOPUS-BODY-ADAPTATION-NEXT-20260915\NEXT-AGENT-MEGAPROMPT.md را کامل بخوان و از بخش «نخستین چرخه کار» ادامه بده.
هدف: پاسخ بهتر + حافظه قابل‌استفاده و قابل‌بازیابی + ادامه بدون لپ‌تاپ.
P5 و GO P6 را از نو شروع نکن. اول مالک فعال و runtime را تطبیق بده؛ سپس retrieve واقعی/PB-4 و T3 را در مسیرهای مستقل جلو ببر و PB-1 را با زمان و شواهد واقعی ادامه بده.
هیچ PASS تاریخی را پاک نکن؛ caveatها و دامنه اثبات را حفظ کن. مجوزهای ثبت‌شده را دوباره نپرس و مرزهای SEC/شاهد/TCB را گسترش نده. با یک برش کاربردی کامل و رسید هم‌دامنه پیش برو.
```

نسخه تألیف: `F:/octopus-body-adaptation-next-20260915/09-LANES/OCTOPUS-BODY-ADAPTATION-NEXT-20260915/`.
نسخه تحویل: `F:/backup/09-LANES/OCTOPUS-BODY-ADAPTATION-NEXT-20260915/`.
نسخه‌ها در زمان تحویل فایل‌به‌فایل با hash بررسی می‌شوند؛ اصلاح بعدی باید نسخه/رسید جدید داشته باشد.
