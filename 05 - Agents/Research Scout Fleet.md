---
type: agent
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
owner: آری
risk_level: low
model: claude-fable-5
trigger: cron
code: 'Documents/Claude/Scheduled/<scout>/SKILL.md — ۸ تسک زمان‌بندی، بدون کد اجرایی'
tags: [agents, ai, research, biomimicry]
created: 2026-07-04
updated: 2026-07-11
---

# Research Scout Fleet — ناوگان اسکات تحقیق میسیلیومی

**نقش:** یک ناوگان از اسکات‌های زمان‌بندی‌شده که هر روز موضوعاتِ زندهٔ هر پروژه را تحقیق عمیق می‌کنند و دیجست تاریخ‌دار به [[00 - Inbox/scout-digests/_README - Scout Digests|scout-digests]] می‌گذارند. طراحی رفتار: میسیلیومی (هیف = کوئری، اسپور = دیجست، مایکوریزا = لینک بین‌پروژه‌ای) — کاملاً در [[05 - Agents/Mycelium Scout|Mycelium Scout]].

**منبع تکِ حقیقتِ رفتار:** همین نوت + Mycelium Scout. هر تسک زمان‌بندی اول این دو را می‌خواند و بعد PROJECT.md پروژهٔ خودش را.

> **استثنای گیت امنیتی (دستور مستقیم آری، 2026-07-04):** طبق [[05 - Agents/AGENT_REGISTRY|AGENT_REGISTRY]] تا بسته‌شدن CRITICALهای [[ROTATION_CHECKLIST]] autonomy مؤثر همه read-only است. آری برای این ناوگان استثنای صریح داد: **نوشتن فقط در `00 - Inbox/scout-digests/`**. هیچ secret / `_code` / نوت canonical / اکشن خارجی. این استثنا فقط برای «فورج + دیجست» است.

## بودجه — تصحیح مهم

- این اسکات‌ها روی **اشتراک Claude آریِ (پلن Max 20x)** اجرا می‌شوند، نه کلیدهای API — پس سقف **D-25 (AU$30/ماه)** که مخصوص بات‌های مستقر است، این‌ها را throttle نمی‌کند. گیت مؤثر = لیمیت اشتراک.
- چون لپ‌تاپ ۲۴ ساعت روشن و دسکتاپ باز است (پنجرهٔ ۳۰ روزه)، ریتم **روزانه و موازی-پخش‌شده** انتخاب شد تا ظرفیت هدر نرود.
- **ضدهدررفت (مهم‌ترین قاعده):** هر اجرا اول با `rg` دیجست‌های قبلی همان اسکات را چک می‌کند و **فقط سیگنال نو** را سنتز می‌کند؛ اگر چیز نویی نبود، یک نوت کوتاه «بدون سیگنال نو امروز» می‌نویسد، نه پُرکنندهٔ تکراری. تراکم = ارزش، نه حجم.

## قرارداد خروجی (هر اسکات، هر روز)

یک فایل: `00 - Inbox/scout-digests/YYYY-MM-DD <slug>.md`

- **فرانت‌متر دقیق (تا اعتبارسنجی پاس شود):** `type: research` · `status: inbox` · `project: "[[…/PROJECT]]"` · `created_by: agent` · `sources:` (لیست ≥۲ لینک) · `tags: [research, …موضوعی]` · `created`/`updated` = امروز. (اسکات هرگز کلید خارج از [[06 - Architecture Maps/Property Schema|Property Schema]] نمی‌سازد.)
- **بدنه (میوه‌دهی):** ۱) سؤال تحقیق امروز (یک جمله). ۲) ۳–۵ یافته، هرکدام + لینک منبع + «این برای پروژه یعنی چه». ۳) ۱–۳ رشتهٔ مایکوریزایی (لینک به نوت‌های موجود vault). ۴) **Cross-domain (اجباری):** یک خط — «کدام دامنه/اسکاتِ دیگرِ ناوگان با این یافته وصل است و چرا؟» (به ماتریس [[00 - Inbox/scout-digests/_Mycorrhizal Map|نقشهٔ مایکوریزایی]] نگاه کن). ۵) ۱–۲ اسپور (سؤال باز فردا).
- **عمق:** از اسکیل `deep-research` برای یک سؤال متمرکز روزانه استفاده کن؛ اگر سنگین/در دسترس نبود، fallback: ۳–۵ سرچ هدف‌مند + fetch منابع برتر + سنتز.

## گاردهای سراسری (هر اسکات)

- فقط در `00 - Inbox/scout-digests/` بنویس. هیچ نوت canonical/PROJECT.md را تغییر نده. HANDOFF را دست نزن (دیجست خودش رکورد است).
- هرگز: `.git` · هر `_code` · `secrets-export/` · `_Archive`/`backup-Archive` · `_Duplicates` · `09 - People` · الگوهای `*wallet*`/`*key*`/`*seed*`/`*.env`/`*.pem` (`.agentignore`). نه خواندن، نه echo.
- هیچ اکشن خارجی (پیام/ترید/ایمیل). فقط خواندن منابع + نوشتن دیجست.
- در حالت autonomous برای سؤال شفاف‌سازی توقف نکن؛ سؤال روز را خودت از «open questions» پروژه + اسپورهای دیروز بساز.

## ناوگان (۸ اسکات — کران به‌وقت سیدنی)

| slug | دامنه | PROJECT | موضوعات زنده (نمونه) | منابع تخصصی | کران |
|---|---|---|---|---|---|
| `mycelium` | طبیعت/architect | [[04 - Architect System/architect/PROJECT\|architect]] | میسیلیوم، جنگل، بقا/antifragile، فلسفهٔ خودسازمان‌ده → معماری AGI چندایجنتی حافظه‌محور | bioRxiv، alphaXiv، HuggingFace papers | `0 7 * * *` |
| `crypto` | [[03 - Projects/Crypto - etoro/PROJECT\|Crypto-etoro]] | سیگنال on-chain، lunarcrush/cryptoquant، exit rules، محدودیت AU30 | web/exa، alphaXiv (quant/ML) | `0 6 * * *` |
| `mining` | [[03 - Projects/Mining/PROJECT\|Mining]] | Orange Pi 5 Pro + ESP32، بازده H/s، شکار کوین، death-watch | web/exa، alphaXiv (edge compute) | `0 8 * * *` |
| `lead` | [[03 - Projects/Lead-نقاشی/PROJECT\|Lead-نقاشی]] | لیدگیری نقاشی سیدنی، AiFarm، کانال‌های کاریابی، بازار محلی | web/exa (سیدنی) | `0 9 * * *` |
| `ziman` | [[03 - Projects/Ziman Galerry/PROJECT\|Ziman]] | برندسازی گالری، بازار هنر، Capacity & Channels | web/exa | `0 10 * * *` |
| `accounting` | [[03 - Projects/Accounting/PROJECT\|Accounting]] | ATO/ASIC، FY2025-26، اتوماسیون دفترداری، آستانه‌های مالیاتی | web (منابع رسمی AU) | `0 11 * * *` |
| `hypnosis` | [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/PROJECT\|هیپنوتیزم]] | خودهیپنوتیزم، HRV/نورو، خودآگاهی، فیوژن | bioRxiv/medRxiv، PMC، alphaXiv | `0 12 * * *` |
| `projectf` 🔒 | Project-F | فقط تحقیق عمومی/صنعتی creator-economy، مانیتایز پلتفرم‌ونداده، بازاریابی | web/exa | `0 13 * * *` |
| `ai-watch` | قابلیت‌های نو AI (خوراک architect) | مدل/ایجنت/حافظه/multi-agent/MCP/eval نو → «چه به معماری ما اضافه می‌کند» | deep-research، alphaXiv، HuggingFace | `0 14 * * *` |
| `security` | opsec/امنیت vault | چرخش secret، prompt-injection، امنیت ایجنت، advisoryها | web/exa، OWASP | `0 16 * * *` |
| `markets` | ماکرو/بازار | AUD/RBA/ASX/ریسک جهانی/کریپتو-ماکرو | web/exa | `0 15 * * *` |
| `jobs` | بازار کار/ترید سیدنی | تقاضای نقاشی/ترید، gig economy، نرخ‌ها | web/exa (AU) | `0 17 * * *` |
| `health` | سلامت/بدن | HRV، خواب، ورزش، تغذیه، استرس (+epistemic) | web/exa، peer-review | `0 18 * * *` |
| `tools` | ابزار/اتوماسیون | no-code، self-host، پلاگین Obsidian (+pricing/lock-in) | web/exa | `0 19 * * *` |
| `philosophy` | فلسفه/مدل ذهنی | فلسفهٔ ذهن، اپیستمولوژی، decision theory، اخلاق سیستم خودمختار | web/exa، SEP | `0 20 * * *` |
| `world` | ژئوپلیتیک/جهانی | نیروهای جهانی که ریسک/فرصت آری را شکل می‌دهند (even-handed) | web/exa | `0 21 * * *` |
| `science` | علم مرزی | فیزیک/زیست/مواد/پیچیدگی/نورو → الگو برای AGI طبیعت‌محور | bioRxiv، alphaXiv | `0 23 * * *` |
| `learning` | یادگیری/مهارت | علم یادگیری، حافظه، تمرکز، تمرین عامدانه | web/exa، peer-review | `0 2 * * *` |
| `local` | سیدنی/NSW محلی | شورا/رگولاتوری، هزینه زندگی، فرصت/گرنت محلی | web/exa (AU) | `0 4 * * *` |
| `architect-selfimprove` ★ | خودبهبودی architect | هر ۱۵دقیقه یک آیتم بک‌لاگ (REFACTOR_PLAN / Open Questions / Adversarial / Blueprint + **synthesis + اسپورهای mycelium**) را تحقیق و **پیشنهاد** می‌دهد | deep-research + همه | `*/15 * * * *` |

## تخصیص ۷۵٪ به خودبهبودی (دستور آری 2026-07-04)

آری خواست بخش عمدهٔ ظرفیت اسکجول صرف **خودبهبودیِ سیستم** شود. چون توکن مستقیماً درصدبندی نمی‌شود، با **فرکانس اجرا** تقریب زده شد:

- `architect-selfimprove` **هر ۳۰ دقیقه = ۴۸ اجرا/روز** (از 2026-07-04، دستور «تندتر» آری)؛ ۸ اسکات دیگر روزانه. نسبت ≈ ۴۸⁄۵۷ ≈ **~۸۵٪ اجراها روی خودبهبودی**.
- `architect-selfimprove` **adaptive** است: اگر بک‌لاگ آیتم نو نداشت، پاس سبکِ consolidation می‌زند نه دایو سنگین تکراری (ضدهدررفت).
- **دایال شدت:** تندتر → `*/15 * * * *` (~۹۱٪)؛ سبک‌تر → `0 * * * *` (ساعتی، ۷۵٪) یا `0 */2 * * *`. ⚠️ در عمل **سقف نرخ پلن Max حاکمِ واقعی** است: بالاتر از یک آستانه، اجراها صف/skip می‌شوند (خراب نمی‌شود، فقط throughput واقعی محدود می‌ماند) و سهم استفادهٔ تعاملی خودت کم می‌شود.
- خروجی این حلقه هم در scout-digests با slug `selfimprove` و نام `YYYY-MM-DD HHmm selfimprove.md` (چند‌بار در روز).

## لایهٔ ارکستراسیون — بستنِ حلقهٔ زیستی (forage → decompose → select)

ناوگان بدون این لایه فقط «جمع می‌کند»؛ این دو تسک آن را به یک ارگانیسمِ خود‌سازمان‌ده تبدیل می‌کنند:

| تسک | نقش زیستی | کران | کار (همه propose-only) |
|---|---|---|---|
| `mycelial-consolidator` | ساپروتروف (تجزیه‌کننده) | `0 22 * * *` (شبانه) | دیجست‌های امروز را می‌خواند → سنتز، **الگوهای بین‌پروژه‌ای مایکوریزایی**، پیشنهاد promote/prune و لینک‌های نو. خروجی: `YYYY-MM-DD synthesis.md` = «میوهٔ روزانه» که آری اول صبح می‌خواند. |
| `fleet-selection` | فشار انتخاب (تکامل) | `0 23 * * 0` (یکشنبه) | کیفیت سیگنال هر اسکات هفته را ارزیابی → پیشنهاد تنظیم فرکانس/موضوع، **retire/spawn** اسکات، تغییر نسبت ۷۵٪. آری با `update_scheduled_task` اعمال می‌کند. |

این «مرتب‌کردنِ همه» (خواستهٔ اولیهٔ آری) است: خام → مغذی → شبکه → انتخاب. `synthesis.md` و `fleet-eval.md` خواندنی‌ترین خروجی‌های ناوگان‌اند.

## لایهٔ اتصال — بافتِ مایکوریزایی ماندگار (2026-07-04)

قلبِ «شبکه از جمعِ اسکات‌ها بیشتر است». چهار مکانیزم تا اتصالات **کامل و دوطرفه** هندل شوند:

1. **flag در منبع:** هر دیجست خطِ Cross-domain اجباری دارد (بند ۴ قرارداد بالا) — اتصال جایی که متولد می‌شود ثبت می‌شود.
2. **حافظهٔ اتصالِ ماندگار:** [[00 - Inbox/scout-digests/_Mycorrhizal Map|نقشهٔ مایکوریزایی]] — ماتریس تغذیه (۱۹ اسکات × پروژه‌ها) + لجرِ انباشتیِ الگوهای بین‌دامنه‌ای. برخلاف synthesisِ روزانه، اینجا **انباشته** می‌شود.
3. **رشد شبانه:** `consolidator` هر شب نقشه را می‌خواند و اتصال/الگوی نوِ پایدار (در ≥۲ دامنه) را append می‌کند (dedup)؛ فایل `_`-دار از evaporation معاف است.
4. **بازخورد:** `selfimprove` از طریق synthesis این ساختار را می‌خواند تا پیشنهاد معماری با گراف واقعی اتصالات هم‌راستا باشد.

هاب‌ها (mother-tree): `architect` · `Crypto` · `Lead` · `هیپنوتیزم` — پراتصال‌ترین گره‌ها؛ کانتکست را به اسکات‌های کم‌کانتکست هدایت می‌کنند.

## بهینه‌سازی‌ها (بازنگری 2026-07-04)

بازنگری انتقادی ۴ گلوگاه یافت و رفع کرد؛ جالب اینکه راه‌حل مهم‌ترینشان را خودِ دیجست [[00 - Inbox/scout-digests/2026-07-04 mycelium|mycelium]] داد:

1. **بستنِ حلقهٔ طبیعت→معماری:** `selfimprove` حالا علاوه بر بک‌لاگ architect، از **آخرین `synthesis` + اسپورهای `mycelium`** هم آیتم می‌گیرد. یعنی یافتهٔ زیستی (مثلاً evaporation) مستقیماً به پیشنهاد معماری تبدیل می‌شود — همان «کپیِ طبیعت» که آری خواست. سود جانبی: در ۴۸ دورِ روزانه مادهٔ نو کم نمی‌آید (کمتر تکرار).
2. **Evaporation/TTL (توصیهٔ خودِ سیستم — stigmergy):** `consolidator` هر شب `status` دیجست‌های **>۱۴ روز** را in-place به `archived` می‌برد (فقط داخل scout-digests، فقط فایل‌های خود ناوگان، برگشت‌پذیر، نه حذف) تا «نقشهٔ فرمون» خوانا بماند و انباشت بی‌نهایت رخ ندهد. استثنای housekeeping با تأیید آری.
3. **بهداشت نوتیف:** هر ۱۰ اسکات **بی‌صدا**؛ فقط `consolidator` شبانه نوتیف می‌دهد → یک پینگِ «synthesis آماده است» در روز، نه ۱۰ پینگ پراکنده.
4. **حجم بالا (خواستهٔ آری — پلن Max 20x):** `selfimprove` روی `*/15` (۹۶/روز)؛ روز با ۱۴ اسکات متنوع پر شد (۶:۰۰–۱۹:۰۰ + شب selfimprove هر ۱۵دقیقه). منطق: **requisite variety** — تنوع اسکات‌ها سیگنالِ بیشتری از کوبیدن یک حلقه می‌دهد. سقف واقعی = پنجرهٔ نرخ پلن (با استفادهٔ تعاملی مشترک است؛ فراتر از سقف، دورها صف→اجرا، خراب نمی‌شوند). دایال سبک‌تر اگر تعاملی خفه شد: `*/30` یا `0 * * * *`.

**گارد ویژهٔ `hypnosis`:** هر یافته `epistemic_status` بگیرد (`peer-reviewed` \| `speculative` \| `fiction-canon`)؛ `fiction-canon` هرگز به‌عنوان evidence بیرون حوزه cite نشود (§Property Schema).

**گارد ویژهٔ `projectf` 🔒:** فقط تحقیق عمومی/صنعتی؛ **هرگز** نام واقعی، پلتفرم، یا محتوای شخصی نوشته یا echo نشود — همه‌جا فقط «Project-F» و مسیرها `[Project-F]`. اگر منبعی مجبورت کند به مشخصات هویتی، رد شو.

## Runbook

- **راه‌اندازی:** خودکار via ۸ تسک زمان‌بندی Cowork (slugها بالا). اجرای اول: فردا صبح (امروز فقط زیرساخت ساخته شد).
- **اجرای دستی:** هر تسک را از فهرست Scheduled اجرا کن، یا بگو «اسکات <slug> را بزن».
- **توقف/مکث یک اسکات:** تسک همان slug را در Scheduled غیرفعال کن.
- **تنظیم شدت:** ریتم روزانه است؛ برای کم‌کردن، کران هر تسک را به هفتگی ببر (مثلاً `0 9 * * 1`).
- **خروجی:** [[00 - Inbox/scout-digests/_README - Scout Digests|scout-digests]]. رجیستری: [[05 - Agents/AGENT_REGISTRY|AGENT_REGISTRY]].

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[03 - Projects/Accounting/Accounting|Accounting]]
- [[03 - Projects/Ziman Galerry/Capacity & Channels|Ziman — Capacity & Channels]]
- [[04 - Architect System/architect/04-Docs/fusion-audit/REFACTOR_PLAN|REFACTOR_PLAN]]
