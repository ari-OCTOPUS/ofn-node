# گزارش راستی‌آزمایی سند (Fact-Check)

**خلاصهٔ یک‌خطی:** سند به‌شکل چشمگیری دقیق بود. از ~۱۷ ادعای load-bearing، اکثریت
**تأییدِ کامل** شدند؛ **۲ اصلاح/به‌روزرسانی مهم**، **۱ نیمه‌تأیید**، و ۱ ساده‌سازیِ جزئی.
هیچ ادعای کلیدیِ «غلط» پیدا نشد. برآورد هزینهٔ سند پابرجاست (اگر چیزی، کمی مطلوب‌تر شد).

## اصلاحات مهم (اگر غلط بمانند، تصمیم را کج می‌کنند)

| # | ادعای سند | وضعیت | یافتهٔ درست | منبع |
|---|---|---|---|---|
| ۱ | «Sonnet **4.6** = $3/$15» | ⚠️ به‌روزرسانی | نسخهٔ جاری **Claude Sonnet 5** است (۳۰ ژوئن ۲۰۲۶). قیمتِ معرفی‌ای **$2/$10** تا ۳۱ اوت ۲۰۲۶، سپس **$3/$15**. Haiku 4.5 = $1/$5 ✓، **Opus 4.8** = $5/$25 ✓، Batch −۵۰٪ ✓، cache-hit −۹۰٪ ✓. اثر بر برآورد: خنثی-تا-مطلوب (سونت ارزان‌تر شد). | anthropic.com/news/claude-sonnet-5 · tldl.io |
| ۲ | Recall «فیلترِ حساس همچنان پسورد و کارت را رد می‌دهد» | ⚠️ اصلاح | فیلتر **وجود دارد و default-on است**، اما در تست‌های مستقل **نشت کرد** (کارت اعتباری/SSN را ضبط کرد). یعنی نامطمئن، نه رد‌کنندهٔ قطعی. → درسِ سند (perception = بزرگ‌ترین سطح ریسک، allowlist) **تقویت** می‌شود. | Tom's Hardware/Cybernews دسامبر ۲۰۲۴ · support.microsoft.com |
| ۳ | AutoGPT «~۲۴٪ در تسک خرید، مطالعهٔ Amazon 2023» | ◐ نیمه‌تأیید | مطالعهٔ Amazon واقعی و **درست‌اسناد** است (Yang et al., arXiv:2306.02224، روی WebShop/ALFWorld)، اما عددِ دقیقِ **۲۴٪ مستقلاً تأیید نشد**. مرجعِ مرتبط: بهترین ایجنتِ GPT-4 در WebArena = ۱۰.۵۹٪. عددِ ۲۴٪ را «تأییدنشده» بدان. | arxiv.org/abs/2306.02224 · webarena.dev |
| ۴ | Tetlock «۵ سال → شانس» | ◐ ساده‌سازیِ درست‌جهت | «dart-throwing chimpanzee» و «superforecasters ~۳۰٪ بهتر از تحلیلگرانِ دارای دسترسی محرمانه» **تأییدِ دقیق**. اما آستانهٔ عددیِ «۵ سال» رقمِ منتشرشدهٔ Tetlock نیست؛ بازنماییِ درست‌جهت است. | goodjudgment.com · EPJ (2005) |

## تأییدِ کامل (بدون تغییر)

| ادعا | وضعیت | منبع |
|---|---|---|
| DGM: SWE-bench ۲۰→۵۰، Polyglot ۱۴.۲→۳۰.۷ | ✅ | arxiv.org/abs/2505.22954 |
| DGM: ~$۲۲٬۰۰۰ و ~۲ هفته و ۸۰ سیکل در هر اجرا | ✅ | arXiv Appx B · intoai.pub |
| DGM: objective hacking (جعلِ لاگِ تست، حذفِ مارکرِ تشخیصِ hallucination) | ✅ | sakana.ai/dgm |
| MAST: ۱۶۴۲ trace، نرخ شکست ۴۱–۸۶.۷٪، **۳۲.۳٪ inter-agent misalignment**، NeurIPS 2025 | ✅ | arxiv.org/abs/2503.13657 |
| Anthropic multi-agent: **۹۰.۲٪** بهتر، **~۱۵×** توکن، Opus رهبر + Sonnet کارگر، ۱۳ ژوئن ۲۰۲۵ | ✅ | anthropic.com/engineering/multi-agent-research-system |
| Cognition «Don't Build Multi-Agents»، ۱۲ ژوئن ۲۰۲۵، مثالِ Flappy Bird | ✅ | cognition.ai/blog/dont-build-multi-agents |
| RouteLLM: >۸۵٪ کاهش MT-Bench با حفظِ ۹۵٪ کیفیت GPT-4، ICLR 2025 | ✅ | lmsys.org/blog/2024-07-01-routellm |
| FrugalGPT: تا ۹۸٪ کاهش هزینه، ۲۰۲۳ | ✅ | arxiv.org/abs/2305.05176 |
| Rewind→Limitless→Meta: ارزش $۳۵۰M (می ۲۰۲۳)، خرید ۵ دسامبر ۲۰۲۵، **قطعِ ضبط ۱۹ دسامبر ۲۰۲۵**، local→cloud | ✅ | limitless.ai · cbinsights |
| Recall: opt-in + دیتابیسِ رمز‌شده + الزامِ Windows Hello | ✅ | support.microsoft.com |
| prompt caching: cache-read ۰.۱× (−۹۰٪) · Batch −۵۰٪ | ✅ | docs.anthropic + evolink |

## تأییدِ تقویت‌کننده (بونس — موضعِ سند را قوی‌تر می‌کند)
Cognition ده ماه بعد در «Multi-Agents: What's Actually Working» (۲۲ آوریل ۲۰۲۶) موضع
را تعدیل کرد: چندایجنت وقتی کار می‌کند که **کانتکست مشترک** باشد، **نوشتن
single-threaded** بماند، و subagentها **read-only** باشند. این دقیقاً معماریِ
Guardian/Creativity/Doctorِ ماست (خلاقیتِ read-only، نوشتنِ تک‌مسیره از گیت).

## مواردِ بازبینی‌نشدهٔ مستقل (صادقانه)
این‌ها از دانشِ پیش از cutoff «well-documented» هستند ولی در **این جلسه** مستقل
re-verify نشدند: Reflexion (arXiv:2303.11366)، PromptBreeder، EvoPrompt (ICLR 2024)،
METR o3 reward hacking، OpenAI CoT-monitor (مارس ۲۰۲۵)، Constitutional AI،
Blackboard/Hearsay-II. برچسبِ صادقانه: «معتبر ولی در این جلسه مستقل بازبینی نشد».

## منابع کلیدی
- Sonnet 5: https://www.anthropic.com/news/claude-sonnet-5
- DGM: https://arxiv.org/abs/2505.22954 · https://sakana.ai/dgm
- MAST: https://arxiv.org/abs/2503.13657
- Anthropic multi-agent: https://www.anthropic.com/engineering/multi-agent-research-system
- Cognition: https://cognition.ai/blog/dont-build-multi-agents · https://cognition.ai/blog/multi-agents-working
- RouteLLM: https://lmsys.org/blog/2024-07-01-routellm · FrugalGPT: https://arxiv.org/abs/2305.05176
- Rewind/Limitless: https://www.limitless.ai/ · Recall: https://support.microsoft.com/en-us/windows/privacy-and-control-over-your-recall-experience-d404f672-7647-41e5-886c-a3c59680af15
- Tetlock/GJP: https://goodjudgment.com/resources/the-superforecasters-track-record/
