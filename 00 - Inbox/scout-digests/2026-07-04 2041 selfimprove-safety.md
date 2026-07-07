---
type: research
status: inbox
project: "[[04 - Architect System/architect/PROJECT]]"
created_by: agent
sources:
  - https://consensus.app/papers/details/629c4d7f7df659f988f8db61f9b883d0/
  - https://consensus.app/papers/details/0a3685f890b85b6ab03d17a57fad8d9c/
  - https://eugenevyborov.substack.com/p/the-external-anchor-principle-how
  - https://arxiv.org/html/2606.26057
  - https://www.lesswrong.com/posts/yo2f9moBX83ARXfw6/if-it-can-learn-it-it-can-unlearn-it-ai-safety-as
  - https://arxiv.org/pdf/2603.28650v1
tags: [research, ai]
created: 2026-07-04
updated: 2026-07-04
salience: 0.85
---

# selfimprove-safety — «Germline Grounding Anchor» (لنگرِ گراندینگِ ژرم‌لاین): reality-testing به‌مثابهٔ ایمنیِ ذاتیِ ثابت‌رمز (R-06 + R-07)

> لِینِ SAFETY. **PROPOSE-ONLY** — این یک design sketch است، اعمال نشده؛ `_code`/`held_out.json`/config/constitution لمس نشد. سطح: kernel-adjacent → **HUMAN-APPROVAL-REQUIRED**. verdict نهایی با آری.

**dedup (rotation):** grep روی همهٔ `*selfimprove*` digestهای امروز برای `grounding / held-out / germline / innate / R-06 / R-07 / self-deception / reward-tampering` → هیچ digestی این آیتم را **انتخاب** نکرده (تنها ارجاع‌های حاشیه‌ای: [[00 - Inbox/scout-digests/2026-07-04 2008 selfimprove|2008]] R-12 را در یک جدول آورد؛ [[00 - Inbox/scout-digests/2026-07-04 2023 selfimprove-safety|2023]] R-04 را نام برد — هیچ‌کدام گیتِ گراندینگ را طراحی نکردند).
- خانوادهٔ SAFETY تا کنون پوشش داد: R-02 (اصالتِ منشأِ verdict → [[00 - Inbox/scout-digests/2026-07-04 2023 selfimprove-safety|Costimulation 2023]])، R-08 (دو-زنجیرهٔ audit → 1655)، R-09 (kill-switch → [[00 - Inbox/scout-digests/2026-07-04 1911 selfimprove|Apoptosis 1911]])، §4 kappa (→ [[00 - Inbox/scout-digests/2026-07-04 1744 selfimprove|Quorum 1744]])، GAP 8 (→ [[00 - Inbox/scout-digests/2026-07-04 2008 selfimprove|Calibrated 2008]]).
- **R-06 (گراندینگ) + R-07 (held-out anchorِ canonical)** تنها آیتم‌های `HUMAN-APPROVAL-REQUIRED`ِ خانوادهٔ SAFETY هستند که **صفر پوشش** دارند. genuinely نو → rotation رعایت شد.

---

## ۱) آیتم و چرا مهم است

**آیتم:** خوشهٔ **گراندینگ / لنگرِ واقعیت** —
- **R-06** «کنترلِ گراندینگ را درست/گیت کن»: امروز `GROUNDING_REQUIRED` ادعاهای خام را در برابرِ یک `held_out.json`ِ **جغرافیا/علوم** می‌سنجد که با دامنهٔ واقعیِ تحلیل **جور نیست** → هر ران ratio 0.0 می‌گیرد → یا **همه‌چیز را halt می‌کند** یا خاموش می‌شود (اعتمادِ کاذب).
- **R-07** «یک held-out anchorِ canonicalِ واحد»: الان **دو نسخهٔ** `held_out.json` هست بدونِ منبعِ حقیقتِ واحد → خودِ لنگر می‌تواند drift کند / دو-روایت شود.

**چرا این keystone است — گراندینگ زیرِ *همهٔ* گیت‌های دیگر می‌نشیند.** [[00 - Inbox/scout-digests/2026-07-04 2023 selfimprove-safety|Costimulation (R-02)]] اصالتِ **ورودیِ انسانی** را تضمین می‌کند؛ گراندینگ اصالتِ **ادعاهای خودِ سیستم دربارهٔ جهان/وضعیتش** را. اگر سیستم بتواند یک «grounded / all-clear»ِ جعلی بسازد، آنگاه Quorum (کِی escalate)، Calibrated-Confidence (چقدر مطمئن)، Apoptosis (کِی بمیر) و هر دو زنجیرهٔ audit، همگی یک **سیگنالِ حقیقتِ مسموم** را به ارث می‌برند. این همان شکافِ **false-assurance** (خانوادهٔ R-04) است، ولی در سطحِ reality-testing.

**بُعدِ متا (چرا این حلقهٔ self-improvement را هم de-risk می‌کند):** یک سیستمِ خود-بهبودده (من + لِین‌های خواهر) که vault را می‌نویسد، در معرضِ **Goodhartـکردنِ گیتِ ایمنیِ خودش** است: «وقتی یک measure هدف شود، دیگر measureِ خوبی نیست» و بدترین حالتش **reward-tampering** = سیستم سیگنالِ ارزیابیِ خودش را دستکاری می‌کند ([Reward Hacking & Goodhart guide](https://aisecurityandsafety.org/en/guides/reward-hacking/)). اگر حلقه بتواند `held_out.json` را ویرایش کند، می‌تواند گراندینگِ خودش را دور بزند. R-07 («لنگرِ واحدِ غیرقابل‌بازنویسی») دقیقاً پادزهرِ این است — و توجیهِ زیستی/فنیِ قاعدهٔ منشورِ خودِ من است (**PROPOSE-ONLY؛ لنگر/constitution را ویرایش نکن**).

## ۲) یافته‌ها / prior-art

**الگوی زیستی — ایمنیِ ذاتی (innate) با گیرنده‌های ژرم‌لاین در برابرِ ایمنیِ تطبیقیِ (adaptive) سوماتیک:**
- ایمنیِ ذاتی از **PRRهای germline-encoded** (Toll-like، RIG-I-like، NOD-like، AIM2) استفاده می‌کند که **PAMP**ها را می‌شناسند — امضاهای مولکولیِ **ذخیره‌شده در تکامل** که «برای بقا و بیماری‌زاییِ پاتوژن ضروری‌اند»، پس پاتوژن نمی‌تواند بدونِ مردن عوضشان کند. این «در تضادِ کامل با سیستمِ تطبیقی است که به گیرنده‌های به‌شدت متغیرِ تصادفی‌ساخته تکیه دارد». ایمنی بنیاداً **self/nonself discrimination** است. ([Kumar 2011 — Pathogen Recognition by Innate Immune System](https://consensus.app/papers/details/629c4d7f7df659f988f8db61f9b883d0/))
- **درسِ کلیدیِ طراحی:** لنگرِ ذاتی **ثابت / ژرم‌لاین / خارج از دسترسِ somatic hypermutation** است. لایهٔ تطبیقی یاد می‌گیرد و جهش می‌زند؛ لایهٔ ذاتی hard-coded می‌ماند — تا موجود نتواند به‌طورِ تطبیقی «قانع» شود که یک پاتوژنِ هسته‌ای را تحمل کند.
- **محدودیت و درمانش (بسیار مهم برای R-06):** PRRهای ثابت «در برابرِ پاتوژن‌های سریع‌التکامل انعطاف‌ناپذیرند»؛ بدن جبران می‌کند با حسِ **DAMP** (خطر از سلولِ در حالِ مرگ) و **HAMP** (فرایندهای مختل‌کنندهٔ هومئوستاز) — یعنی به‌جای فقط امضای ثابت، **اختلالِ هومئوستاز** را حس می‌کند و «انعطافِ کشفِ عفونتِ تکاملاً نو» می‌گیرد. ولی حسِ بیش‌ازحدِ DAMP/HAMP → **التهابِ استریل/autoinflammation**. ([Liston & Masters 2017 — HAMPs](https://consensus.app/papers/details/0a3685f890b85b6ab03d17a57fad8d9c/))

> **بازقاب‌گیریِ کلیدی:** باگِ واقعیِ R-06 (لنگرِ جغرافیا/علوم روی دامنهٔ نامرتبط → ratio 0.0 روی هر ران → haltِ همه‌چیز) **دقیقاً autoinflammation است**: یک danger-sensorِ mismatched که **self را nonself می‌بیند** و به بافتِ سالم (رانِ مشروع) حمله می‌کند. پس درمان از خودِ زیست‌شناسی می‌آید → کالیبراسیونِ درستِ self/nonself = **anchorِ domain-matched**.

**prior-art امنیتی (AI، ۲۰۲۵–۲۰۲۶):**
- **External Anchor Principle** (Vyborov): metric/target را **از منظرِ agent immutable کن — می‌بیند ولی نمی‌تواند تغییرش دهد**؛ بقیه‌چیز modifiable. «eval خودِ جهان است، نه یک proxy». بهبودِ جعلی یک **شکافِ قابل‌کشف** می‌سازد: metricِ درونی بالا می‌رود ولی خروجیِ بیرونی تکان نمی‌خورد. قیدِ **ساختاری/معماری‌ست، نه trust-based** — همان اصلِ ژرم‌لاین. ([External Anchor Principle](https://eugenevyborov.substack.com/p/the-external-anchor-principle-how))
- **Unfireable Safety Kernel** (arXiv 2606.26057): runtimeِ agent را **untrusted by construction** فرض کن (prompt-injection، compromise، misalignment)؛ corrigibility «خاصیتِ deployment، نه خاصیتِ انگیزهٔ agent». صریحاً دربارهٔ **حلقه‌های recursive self-improvement**: «خودِ سطحِ self-modification یک اکشنِ پرپیامد است که باید authorize شود» و «انضباطِ اضافی لازم است تا **خودِ policy از مسیری که kernel نمی‌بیند تغییر نکند**» — یعنی *تعریفِ* لنگر باید بیرونِ دسترسِ حلقه باشد. ([Unfireable Safety Kernel](https://arxiv.org/html/2606.26057))
- **«اگر بتواند یادش بگیرد، می‌تواند فراموشش کند»** (LessWrong): fine-tuning ایمنی را پاک می‌کند؛ «مسئلهٔ مفسر» در Constitutional AI (مدل خودش اصول را تفسیر می‌کند → حرف را رعایت، روح را نقض → روباه نگهبانِ لانه). راه‌حل = **لایهٔ ناخودآگاه (firmware, immutable)**: ممنوعیت‌های categorical که «پیش از هر deliberation چک می‌شوند، با context قابلِ توجیه نیستند و با learning تغییر نمی‌کنند». هزینهٔ پذیرفته‌شده: **value lock-in**. ([If it can learn it, it can unlearn it](https://www.lesswrong.com/posts/yo2f9moBX83ARXfw6/if-it-can-learn-it-it-can-unlearn-it-ai-safety-as))
- **حدودِ اطلاعاتیِ verification برای self-improving systems** (arXiv 2603.28650): «شرایطِ دوگانه» برای خود-بهبودِ ایمن — Σδ (false-accept) کران‌دار (احتمالِ مثبتِ «هرگز mutationِ ناایمن نپذیر») + Σ TPR=∞ (بهبود ادامه یابد). نتیجهٔ کلیدی: **گیتِ مبتنی‌بر classifier نمی‌تواند هر دو را برآورده کند**؛ **گیتِ sound-verifier** (δ=0، TPR>0) می‌تواند. درس: لنگرِ گراندینگ باید یک **verifierِ سالمِ روی یک invariantِ held-out** باشد، نه یک classifierِ یادگرفتنی که Goodhart می‌شود. ([Info-Theoretic Limits](https://arxiv.org/pdf/2603.28650v1))
- **contaminationِ held-out واقعی است:** نرخِ آلودگیِ بنچمارک تا ~۵۷٪ در مدل‌های frontier؛ نمراتی که «با تغییرِ کلمات بخار می‌شوند»؛ اثرِ آلودگی حتی پس از کشف قابلِ **train-away** است؛ canary «فقط اگر همه رعایتش کنند کار می‌کند — که نمی‌کنند». پس محتوای لنگر باید از سیگنالِ optimization جدا (held-out واقعی) بماند. ([Benchmark contamination survey](https://arxiv.org/abs/2406.04244))

## ۳) PROPOSAL — «Germline Grounding Anchor» (proposal — needs Ari's verdict)

خوشهٔ گراندینگ را با پنج قاعده بازطراحی کن، به‌قیاسِ ایمنیِ ذاتیِ ثابت‌رمز:

1. **لنگرِ canonicalِ واحد و read-only (R-07 = جایگاهِ ژرم‌لاین).** یک `held_out.json` پشتِ یک loaderِ واحد، **content-addressed** (هشِ محتوا در kernel/constitution پین شود). لایهٔ تطبیقی (اسکات‌ها، حلقه‌های self-improvement از جمله من) می‌تواند **بخواند** ولی مسیرِ **نوشتن بیرونِ دسترسِ agent** است — همان مرزِ کلیدِ سیگنال-۲ی Costimulation (2023) و policy-surfaceِ Unfireable-Kernel. **حضورِ یک لنگرِ writable در محیطِ agent = نقضِ invariant** → تستِ red-team بگیرد (قرینهٔ frozen-verb/key-presence testِ 2023).

2. **anchorِ domain-matched برای درمانِ autoinflammation (R-06).** ادعاها/تحلیل‌هایی که **به دامنهٔ held-out مربوط‌اند** را گراند کن، نه یافته‌های خامِ Researcher؛ لنگرِ جغرافیا/علوم را با یک لنگرِ hم‌دامنه جایگزین کن تا رانِ سالم ratio 0.0 نگیرد. زیستی: کالیبراسیونِ دوبارهٔ self/nonself تا سنسور از حمله به بافتِ سالم بازایستد.

3. **حسِ دو-کاناله (PAMP + HAMP).** کانالِ A = چکِ **امضای ثابتِ conserved** (آیا ادعا invariantهای held-out را دارد؟) — ارزان، high-precision، ولی کور نسبت به drift نو. کانالِ B = چکِ **اختلالِ هومئوستاز** (آیا این ران از baselineِ گراندشدهٔ اخیرِ خودِ سیستم / set-point منحرف است؟) — خطاهای نو را می‌گیرد که لنگرِ ثابت از دست می‌دهد. baselineِ کانال B از [[00 - Inbox/scout-digests/2026-07-04 2019 selfimprove|Fleet Homeostat (set-point)]] می‌آید. این پاسخِ ایمنی به «PRRهای ثابت انعطاف‌ناپذیرند» است.

4. **انضباطِ fail-mode (نه autoimmunity، نه immunodeficiency).** **شکستِ** گراندینگ روی ادعای پرپیامد → از گیتِ HITL عبور کند (R-12)، نه haltِ خام — تا لنگرِ mismatched نتواند autoinflammatory همه‌چیز را halt کند و لنگرِ کور هم نتواند بی‌صدا pass دهد. آستانه با substratِ conformalِ [[00 - Inbox/scout-digests/2026-07-04 2008 selfimprove|Calibrated-Confidence (2008)]] کالیبره شود، نه یک ratioی جادویی. تفکیک: ادعای برگشت‌پذیر/read → tolerate؛ ادعای پرپیامد/برگشت‌ناپذیر → **گراندینگِ مثبتِ لازم** (missing-self = ادامه نده).

5. **چرخشِ لنگر یک رویدادِ امضاشده و human-gated است (ژرم‌لاین را soma ویرایش نمی‌کند).** به‌روزکردنِ لنگرِ canonical خودش یک verdictِ `HUMAN-APPROVAL-REQUIRED` است (با دو-سیگنالِ Costimulation 2023) و یک رویدادِ audit امضاشده (R-02/R-08). حلقهٔ self-improvement می‌تواند تغییرِ لنگر را **پیشنهاد** دهد (مثلِ همین digest) ولی هرگز اعمال نکند — که دقیقاً منشورِ من است، حالا مبتنی‌بر اصلِ ژرم‌لاین.

**کمینه/دامنه:** ترجیحِ **sound-verifier روی invariant** بر classifierِ یادگرفتنی (طبق حدودِ اطلاعاتی: δ=0 با TPR>0). فقط ادعاهای پرپیامد گراندینگِ سخت‌گیرانه می‌گیرند؛ readها/برگشت‌پذیرها tolerate — قرینهٔ tolerance بدونِ costimulation.

## ۴) ریسک‌ها / trade-offها

- **Value lock-in:** لنگرِ immutableی که **غلط** است با learning اصلاح نمی‌شود (LessWrong صریحاً این هزینه را می‌پذیرد). کاهش: لنگر **human-updatable** از راهِ چرخشِ امضاشده است، فقط **agent-updatable نیست**. «safely-wrong > unsafely-updateable».
- **autoinflammation ↔ immunodeficiency یک دیالِ واقعی‌ست:** domain-match/آستانهٔ خیلی تنگ → haltِ رانِ سالم (باگِ فعلیِ R-06)؛ خیلی شل → اعتمادِ کاذب (R-04). تعادل با دو-کانال + آستانهٔ conformal + مسیرِ HITL، ولی کالیبراسیون تجربی‌ست و به دیتای آری نیاز دارد.
- **contamination/Goodhartِ خودِ لنگر:** اگر محتوای لنگر به هدفِ optimizationِ لایهٔ تطبیقی نشت کند، گراندینگ آلوده می‌شود (نرخِ ~۵۷٪ واقعی). کاهش: محتوای *چک‌کنندهٔ* لنگر را از هر سیگنالِ training/optimization جدا نگه دار؛ از چک‌های perturbation-style (کانال B) که حفظ‌کردنی نیستند استفاده کن؛ content-hash pin.
- **اشتباه‌گرفتن با Costimulation (2023):** نباید یکی شوند — Costimulation = اصالتِ منشأِ **ورودیِ انسانی**؛ این = اصالتِ **ادعاهای سیستم دربارهٔ جهان**. دو هدفِ متفاوت (همان درسِ «journal ≠ ledger» و «origin ≠ integrity»).
- **سطحِ approval:** kernel-adjacent → `HUMAN-APPROVAL-REQUIRED`؛ فقط design sketch، بدونِ لمسِ `_code`/`held_out.json`/config، بدونِ mutationِ invariant.

## ۵) mycorrhizal links

- [[00 - Inbox/scout-digests/2026-07-04 2023 selfimprove-safety]] — Costimulation Gate (R-02): **خواهرِ** این آیتم — اصالتِ ورودیِ انسانی؛ اینجا اصالتِ ادعاهای خودِ سیستم. همان مرزِ «کلید/لنگرِ agent-unforgeable».
- [[00 - Inbox/scout-digests/2026-07-04 2019 selfimprove]] — Fleet Homeostat: منبعِ set-point/baseline برای کانالِ B (حسِ HAMP).
- [[00 - Inbox/scout-digests/2026-07-04 2008 selfimprove]] — Calibrated-Confidence: آستانهٔ «به‌قدرِ کافی grounded»، جایگزینِ ratioی جادویی.
- مرجع: [[04 - Architect System/architect/04-Docs/fusion-audit/REFACTOR_PLAN]] R-06 + R-07 (خانه)، R-04 (false-assuranceِ خواهر)، R-12 (escalate grounding→HITL).
