---
type: report
status: done
tags: [research, architect, adversarial, blueprint-v3, inbox]
updated: 2026-07-04
created: 2026-07-04
related: "[[04 - Architect System/architect/01-Project/SYSTEM-BLUEPRINT-v3-proposal]]"
---

# گزارش adversarial — بازبینی v3 (2026-07-04)

*موضوع: تقویت/رد ادعاهای SYSTEM-BLUEPRINT-v3 و SCOUT و گزارش ۲۰ معماری. نویسنده: agent (اجرای زمان‌بندی‌شده، ترک ۲). روش: استخراج ادعاهای ضعیف با subagent + ۶ جستجوی adversarial، هر ادعا URL دارد. ورودی‌ها: Report - 20 AGI Architectures، SYSTEM-BLUEPRINT-v3-proposal، SCOUT-A/C. دامنه: فقط غنی‌سازی — verdict فعال‌سازی v3 با آری.*

> هدف: هر ادعای معماری کلیدی v3 را با شواهد وب یا تقویت یا رد کنیم. نتیجه سرجمع: **ستون فقرات v3 مقاوم است**؛ سه اصلاح مهم لازم است (Mem0 lock-in، عدد judge kappa، جایگاه Reflexion).

## ۱. حافظه لایه‌ای — انتخاب Mem0 (اقتباس ۱): **نیاز به اصلاح**

**ادعای v3:** «هدف کد: Mem0 OSS (Letta رد — lock-in؛ Zep CE مرده)».

**شواهد ۲۰۲۶:**
- Zep CE **واقعاً deprecated شد** — رسماً آوریل ۲۰۲۵، بازنشستگی ویژگی‌های بیشتر فوریه ۲۰۲۶؛ کد به `legacy/` منتقل شد؛ open-source اکنون فقط **Graphiti** (Apache-2.0) است. ادعای «Zep CE مرده» **تایید شد**. ([Zep blog](https://blog.getzep.com/announcing-a-new-direction-for-zeps-open-source-strategy/))
- اما self-host فعلی Zep = Graphiti + یک graph DB (Neo4j/FalkorDB/Kuzu) = حداقل ۳ سیستم — سنگین برای solo/RK3588. تایید غیرمستقیم رد Zep.
- **نکته adversarial که v3 از قلم انداخت:** Mem0 هم lock-in دارد — **لایه گراف Mem0 فقط cloud/Pro است؛ SDK متن‌باز فقط لایه vector را می‌دهد**، نه گراف. ([Atlan 2026](https://atlan.com/know/best-ai-agent-memory-frameworks-2026/)، [Dev Genius 2026](https://blog.devgenius.io/ai-agent-memory-systems-in-2026-mem0-zep-hindsight-memvid-and-everything-in-between-compared-96e35b818da8))
- کیفیت: Zep در LongMemEval **۶۳.۸٪ در برابر ۴۹.۰٪ Mem0** (بنچ مستقل قدیمی‌تر)؛ Mem0 عدد self-reported آوریل ۲۰۲۶ را ۹۴.۴٪ می‌زند (**self-reported — با احتیاط**).

**اصلاح پیشنهادی v3:** انتخاب Mem0 را نگه دار ولی صریح کن که **فقط لایه vector متن‌باز استفاده شود** (نه گراف Pro)؛ اگر بعداً گراف زمانی لازم شد، **Graphiti مستقل** (Apache-2.0، بدون پلتفرم Zep) گزینه‌ای است که همان ضعف lock-in را ندارد. پرچم: بند «Mem0 OSS = آنتی lock-in» بیش‌ازحد خوش‌بینانه بود.

## ۲. ضدالگوی «جامعه چندایجنته زنده» (Task D بند ۳): **قوی‌تر از ادعای v3 تایید شد**

**ادعای v3:** multi-agent زنده رد (P7، D-02)؛ CrewAI «۳× سربار توکن».

**شواهد ۲۰۲۶ (پادزهر مستقل و قوی‌تر):**
- مطالعه Berkeley **«Why Do Multi-Agent LLM Systems Fail?»** (arXiv:2503.13657): تحلیل ۱۶۴۲ trace واقعی از ۷ فریم‌ورک → **نرخ شکست ۴۱٪ تا ۸۶.۷٪**. ([arXiv](https://arxiv.org/abs/2503.13657))
- سربار واقعی **۱۰× یا بیشتر** توکن/تأخیر گزارش شده — یعنی عدد «۳×» v3 **محافظه‌کارانه** بود. ([Berkeley Sky Lab / MAST](https://sky.cs.berkeley.edu/project/mast/))
- تفکیک علت شکست (MAST): **۴۲٪ بدسازی spec، ۳۷٪ فروپاشی هماهنگی، ۲۱٪ راستی‌آزمایی ضعیف** — دقیقاً سه چیزی که معماری تک‌ایجنته + گیت‌های deterministic v3 حذف می‌کند.

**نتیجه:** این قوی‌ترین یافته امشب. توصیه: MAST را به‌عنوان **استناد رسمی پشت P7/D-02** در v3 و منشور اضافه کن (نه فقط اصل سلیقه‌ای، بلکه شواهد کمی). ۱۴ حالت شکست MAST می‌تواند چک‌لیست منفی طراحی شود.

## ۳. حلقه تکاملی AlphaEvolve برای AiFarm (اقتباس ۴): **معتبر، با قید دامنه صریح**

**ادعای v3:** LLM = عملگر جهش؛ ارزیاب = دنیای واقعی (reply/booking rate)؛ پادزهر Goodhart.

**شواهد:**
- تایید مکانیزم: AlphaEvolve دقیقاً وقتی کار می‌کند که **تابع امتیاز پایدار، محاسبه‌پذیر و سخت‌برای‌گیم‌کردن** باشد؛ «فقط در دامنه‌های با ارزیاب خودکار». ([AlphaEvolve paper](https://msu.dvaoblaka.ru/media/2025/05/68271bf34ef55_AlphaEvolve.pdf)، [Medium tech review 2026](https://medium.com/@milesk_33/forget-the-benchmarks-heres-what-alphaevolve-truly-changed-3ecf95fdbd76))
- **قید مهم:** «به‌روشنی به بیشتر کارهای دانشی generalize نمی‌شود». یعنی reply_rate لید نقاشی **یکی از معدود دامنه‌های vault** است که این شکل را دارد؛ حسابداری/ماینینگ/محتوا این ارزیاب طبیعی را ندارند.
- LeCun critique مشخص درباره AlphaEvolve: **یافت نشد** (در نتایج نبود — علامت‌گذاری صادقانه).

**نتیجه:** اقتباس ۴ درست هدف‌گیری شده (روی AiFarm، نه سراسری). توصیه: در متن v3 صریح کن که این الگو **عمداً فقط به خطوطی با outcome قابل‌اندازه‌گیری محدود است** — همان satellite بودنش. پیش‌نیاز «≥۵۰ ارسال ثبت‌شده» را نگه دار (بدون آن، ارزیاب نویزی = Goodhart).

## ۴. Judge بین‌خانواده با kappa≥0.7 (اقتباس ۳): **عدد غیرواقعی — اصلاح کن**

**ادعای v3:** judge بین‌خانواده (Gemini)، **kappa≥0.7** برای promotion.

**شواهد ۲۰۲۵ (این ادعا را به‌چالش می‌کشد):**
- توافق بین‌مدلی LLM-as-judge در عمل **بسیار پایین‌تر**: Fleiss' Kappa میانگین **۰.۱–۰.۳۲**؛ حتی judgeهای SOTA حدود κ≈۰.۳. ([Adaline 2025](https://www.adaline.ai/blog/llm-as-a-judge-reliability-bias)، [arXiv 2512.16041](https://arxiv.org/pdf/2512.16041))
- سوگیری‌های مستند: self-enhancement (ترجیح خروجی خود)، verbosity، position bias (جابه‌جایی جای پاسخ رأی را برمی‌گرداند). در دامنه تخصصی توافق به ۶۰–۶۸٪ می‌افتد (زیر baseline انسانی ۷۲–۷۵٪).
- کاهش موثر: **prompt scaffolding با توضیح** (~۰.۰۵–۰.۱ بهبود kappa) و **majority-vote/ensemble**.

**نتیجه:** آستانه ثابت **kappa≥0.7 برای یک جفت judge غیرواقعی است** و در عمل تقریباً هرگز روی موارد ذهنی برآورده نمی‌شود → گیت promotion یا همیشه می‌بندد یا آستانه بی‌معنا می‌شود. **اصلاح پیشنهادی:** (الف) kappa را فقط برای مسیرهای **قابل‌عینی‌سازی** به‌کار ببر و برای بقیه، ensemble ۳-رأی + انسان به‌عنوان tiebreaker؛ (ب) هرجا ممکن، judge را با **گیت deterministic** (schema/test/allowlist — درس AlphaProof که v3 خودش دارد) جایگزین کن، نه رأی LLM. این با «judge تا حد ممکن deterministic» خود v3 (اقتباس ۳) سازگار است — فقط عدد ۰.۷ باید برود.

## ۵. Reflexion به‌عنوان episodic ارزان (اقتباس ۲): **معتبر ولی با قید ضد-echo قوی‌تر**

**ادعای v3:** بعد از هر شکست بازتاب کوتاه ذخیره و در تلاش بعدی تزریق؛ «self-critique تنها = echo chamber».

**شواهد ۲۰۲۴–۲۰۲۵ (قید v3 را تایید و تشدید می‌کند):**
- Reflexion روی کارهای پیچیده **plateau می‌کند و گاه خطای قبلی را تقویت می‌کند** (degeneration-of-thought / mental-set). ([Reflected Intelligence 2025](http://reflectedintelligence.com/2025/05/19/reflexion/))
- مشکل بنیادی: **بدون oracle حقیقت، مدل نمی‌تواند خطای خودش را قابل‌اعتماد تشخیص دهد**؛ بازده نزولی از تکرار؛ حتی افت کیفیت روی promptهای آسان. برخی مطالعات می‌گویند سود مشاهده‌شده به عوامل بیرونی برمی‌گردد نه خود reflection. ([arXiv MAR 2512.20845](https://arxiv.org/html/2512.20845))

**نتیجه:** قید v3 (ارتقا به procedural فقط از گیت اقتباس ۶) **درست و ضروری** است — این شواهد نشان می‌دهد بدون آن قید، Reflexion فعالانه مضر می‌شود. توصیه: به اقتباس ۲ اضافه کن که reflection فقط وقتی تزریق شود که **سیگنال شکست عینی** داشته باشد (خطای اجرا، رد validator، عدم‌پاسخ لید) — نه «حس بد مدل». این دقیقاً همان درس oracle است.

## ۶. CoALA به‌عنوان چارچوب رسمی (اقتباس/Task A): **تایید شد**

- CoALA (arXiv:2309.02427) همچنان چارچوب مرجع فعال است؛ اقتباس‌های ۲۰۲۵–۲۰۲۶ ادامه دارد (Maruyama Aug 2025؛ Liu Feb 2026). واژگان working/long-term × internal/external × decision-loop معتبر. ([Princeton](https://collaborate.princeton.edu/en/publications/cognitive-architectures-for-language-agents/)، [Cognee](https://www.cognee.ai/blog/fundamentals/cognitive-architectures-for-language-agents-explained))
- استفاده v3 از CoALA برای امتیازدهی وضع موجود (§۲) روش‌شناختی سالم است. هیچ اصلاحی لازم نیست.

## جمع‌بندی — دلتای پیشنهادی به v3 (همه additive، status=proposal می‌ماند)

| # | بخش v3 | یافته | اقدام |
|---|---|---|---|
| ۱ | اقتباس ۱ (Mem0) | Mem0 گراف = cloud/lock-in؛ Zep CE مرده تایید | تصریح «فقط لایه vector OSS»؛ Graphiti مستقل به‌عنوان مسیر گراف آینده |
| ۲ | Task D بند ۳ | MAST: شکست ۴۱–۸۷٪، سربار ۱۰×+ | افزودن MAST به‌عنوان استناد رسمی P7/D-02 |
| ۳ | اقتباس ۴ (AlphaEvolve) | فقط دامنه verifiable generalize می‌شود | تصریح محدودیت دامنه؛ حفظ پیش‌نیاز ≥۵۰ ارسال |
| ۴ | اقتباس ۳ (judge) | kappa بین‌مدلی واقعی ۰.۱–۰.۳ | **حذف عدد ۰.۷**؛ ensemble+انسان؛ ترجیح گیت deterministic |
| ۵ | اقتباس ۲ (Reflexion) | بدون oracle مضر است | تزریق فقط با سیگنال شکست عینی |
| ۶ | Task A (CoALA) | معتبر | بدون تغییر |

**پرچم قرمز رعایت‌شده:** کد `_code` لمس نشد؛ هیچ secret؛ v3 فقط غنی‌سازی می‌شود، فعال نمی‌شود. verdict با آری.
