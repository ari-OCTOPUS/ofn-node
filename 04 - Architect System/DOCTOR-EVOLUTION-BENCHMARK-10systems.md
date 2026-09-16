---
type: research
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft-for-verdict
created_by: agent
relates_to: "[[_ops/ORGANISM-SPEC]] §2.7 Doctor · [[DOCTOR-BOX-OF-AGENTS-SPEC]] · _ops/doctor/doctor.py"
tags: [doctor, evolution, benchmark, self-improving, research, propose-only]
created: 2026-07-08
updated: 2026-07-08
---

# دکترِ تکاملی — بنچمارکِ ۱۰ سیستمِ برتر + آپدیتِ سیستمِ ما

> گزارشِ present-day (وب، cited، جولای ۲۰۲۶) از بهترین «دکترهای تکاملی» صنعت + delta برای ارتقای دکترِ ما. برچسب: `[FACT]`=منبع‌دار · `[EST]`=استنتاج · `[SPEC]`=گمانه. **قاعدهٔ حاکم:** ما **هوش** این سیستم‌ها را برمی‌داریم، نه **خودمختاری**‌شان — merge همچنان human-append، sandbox، λ_persist منفی.

## بخش ۱ — ۱۰ سیستمِ برتر و تکنیکِ قابل‌انتقال

| # | سیستم / شرکت | «دکترِ تکاملی»‌اش چه می‌کند | تکنیکِ قابل‌انتقال به ما |
|---|---|---|---|
| ۱ | **Darwin Gödel Machine — Sakana AI** (مه ۲۰۲۵) | agentی که **کدِ خودش را بازنویسی می‌کند** و هر تغییر را empirically روی بنچمارک اعتبارسنجی می‌کند؛ یک **لینیجِ رو به‌گسترشِ variantها** نگه می‌دارد. SWE-bench ۲۰٪→۵۰٪، Polyglot ۱۴.۲٪→۳۰.۷٪ `[FACT]` | **آرشیوِ لینیجِ RFC/variant** + اعتبارسنجیِ تجربی (نه فقط «lift موردِانتظار») |
| ۲ | **AlphaEvolve — Google DeepMind** (مه ۲۰۲۵) | coding-agentِ تکاملی (Gemini + **ارزیاب‌های خودکار**) که کلِ codebase را evolve می‌کند؛ دیتاسنتر/چیپ/ضربِ ماتریسِ گوگل را بهبود داد `[FACT]` | **ارزیابِ خودکارِ کمی** که RFC را قبل از انسان gate می‌کند |
| ۳ | **FunSearch — DeepMind** | LLM + **ارزیابِ برنامه‌ای** برای کشفِ توابعِ نو (جدِ AlphaEvolve) `[FACT]` | جفتِ generator↔evaluator = هستهٔ propose+verify |
| ۴ | **AI Co-Scientist — DeepMind** (Nature، مه ۲۰۲۶) | **چند-agentِ** Generation/Reflection(peer-review)/**Ranking(tournament)**/Evolution که فرضیه‌ها را debate و evolve می‌کنند؛ مثلِ AlphaGo ولی «مناظرهٔ علمی» `[FACT]` | **رتبه‌بندیِ tournament/Elo** میانِ چند RFC — نه یک نمرهٔ تنها. مستقیم رویِ Inner Chamberِ ما می‌نشیند |
| ۵ | **SWE-RL / self-play — Meta Superintelligence Labs** | یک LLM بینِ نقشِ **bug-injector ↔ solver** جابه‌جا می‌شود و دادهٔ آموزشیِ خودش را با self-play می‌سازد `[FACT]` | **صدای bug-injector** در جعبه: falsifierهای سختِ خودساخته → Skeptic قوی‌تر |
| ۶ | **MAP-Elites / Quality-Diversity** (DeepMind/Uber و آکادمی) | **آرشیو/repertoire** از راه‌حل‌های **متنوع و باکیفیت**؛ هر سلولِ فضای رفتار بهترین‌اش را نگه می‌دارد؛ novelty search `[FACT]` | آرشیوِ RFC **ایندکس‌شده بر حسبِ نوعِ گلوگاه/اندام** — بهترین-در-هر-سلول |
| ۷ | **AWS DevOps Guru / self-healing** | لایه‌های detect→evaluate→remediate→**verify→escalate-to-human** برای auto-remediation `[FACT]` | لایهٔ **verifyِ صریح بعد از هر remediation** + escalation (مکملِ restart_from_known_good ما) |
| ۸ | **AutoGen / Copilot Studio — Microsoft** | ارکستراسیونِ چند-agent + پروتکلِ **A2A** برای واگذاریِ خودکارِ کار `[FACT]` | الگوهای hand-off بینِ صداهای جعبه (کران‌دار) |
| ۹ | **ADAS / Meta Agent Search** (آکادمی) | یک meta-agent که **agentهای نو را به‌صورتِ کد طراحی می‌کند** و آرشیوِ طرح‌ها نگه می‌دارد `[EST]` | جعبه می‌تواند **الگوی صداهای خودش** را (در sandbox) پیشنهاد دهد — human-gated |
| ۱۰ | **GEPA / STOP — reflective prompt evolution** | تکاملِ **بازتابیِ prompt/سیاست** که گاه از RL بهتر است `[FACT]` | دکتر prompt/سیاستِ خودش را evolve کند — **فقط sandbox + تغییرِ ژنومِ human-gated** |

## بخش ۲ — شکافِ دکترِ ما (چه نداریم)
دکترِ فعلی (`_ops/doctor/doctor.py`): `mine`→RFC→sandbox+Critic→`submit_for_approval`، Inner Chamber (۴ صدا)، λ_persist=−1.0، RFCها روی دیسک. **اما:**
- ❌ **آرشیوِ quality-diversity ندارد** — RFCها ذخیره می‌شوند ولی sample/mutate/لینیج نمی‌شوند (نه DGM، نه MAP-Elites).
- ❌ **ارزیابِ کمیِ measured-lift ندارد** — «lift موردِانتظار» یک فیلد است، نه عددِ اندازه‌گیری‌شده روی held-out (برخلافِ AlphaEvolve/DGM).
- ❌ **tournament-ranking ندارد** — یک RFC، یک نمره؛ نه چند variant و رتبه‌بندی (برخلافِ Co-Scientist).
- ❌ **self-play falsifier ندارد** — Skeptic هست ولی bug-injectorِ خودساز نیست (برخلافِ Meta).
- ⚠️ لایهٔ **verify بعد از remediation** ضمنی است (restart با N-cap→FREEZE) — صریح نیست (برخلافِ AWS).

## بخش ۳ — آپدیتِ پیشنهادی (۵ adoption، همه داخلِ Evolution Guard)
هر کدام: تکنیکِ صنعتی → پیاده در دکترِ ما، **propose-only، sandbox، λ_persist منفی، human-append merge.**

1. **آرشیوِ لینیج (DGM + MAP-Elites):** `doctor.archive` = repertoireِ RFCها ایندکس‌شده بر حسبِ (نوعِ گلوگاه × اندام)، بهترین-در-هر-سلول. `mine` از آرشیو sample/mutate می‌کند → تکاملِ open-ended **ولی کران‌دار** (سقفِ اندازه، evict). `[EST]` بردِ اصلی، کم‌ریسک (فقط حافظه).
2. **ارزیابِ measured-lift (AlphaEvolve/FunSearch):** یک eval-harness در sandbox که lift **واقعی** را می‌سنجد؛ RFCِ زیرِ آستانه **خودکار drop** (هرگز به انسان نمی‌رسد) → بارِ review کم، کیفیت بالا. `[EST]`
3. **tournament-ranking (Co-Scientist):** Inner Chamber چند RFC-variant بسازد؛ Judge با **مسابقهٔ Elo** رتبه‌بندی کند؛ فقط بازمانده submit شود. `[EST]` — دقیقاً روی ۴ صدای موجود سوار می‌شود.
4. **صدای bug-injector (Meta self-play):** یک صدای نو در جعبه که falsifierِ سختِ adversarial می‌سازد؛ RFC باید از آن جان به‌در ببرد. `[EST]` — Skeptic را از self-play تقویت می‌کند؛ داخلِ sandbox، بی‌خطر.
5. **لایهٔ verify صریح (AWS):** بعد از هر `restart_from_known_good`، یک چکِ verify + در صورتِ تکرار → escalate به انسان (فرمالیزهٔ FREEZE فعلی). `[EST]`

## بخش ۴ — خطِ تمایزِ ایمنی (چرا ما ≠ DGM)
DGM/AlphaEvolve اجازه می‌دهند AI **کدِ خودش را بدونِ نظارت deploy کند.** دکترِ ما **هرگز**: هر بهبود فقط پیشنهاد است، merge با human-append از تلگرام، λ_persist منفی (بقا پاداش نمی‌گیرد)، sandbox جدا از production. **ما موتورِ کشف را وام می‌گیریم، نه حلقهٔ خودگردانِ deploy را.** این تفاوت، همان Evolution Guard است.

## بخش ۵ — پرامپتِ GLM (پیاده‌سازیِ ۳ adoptionِ اولِ کم‌ریسک)
```
تو کارگرِ کدنویسِ Octopus (GLM) هستی. دکتر را با ۳ تکنیکِ صنعتی ارتقا بده: (۱) آرشیوِ quality-diversity، (۲) ارزیابِ measured-lift، (۳) tournament-ranking. propose-only، sandbox، additive، λ_persist منفی دست‌نخورده، هیچ auto-merge. commit با مالک.
گام ۰ ضدِ تکرار: grep -rln "class RFCArchive\|def measured_lift\|def tournament_rank" _ops/doctor/ | grep -v __pycache__ ؛ هرچه بود اثبات بده و رد شو.
گام ۱ بخوان: _ops/doctor/doctor.py + DOCTOR-EVOLUTION-BENCHMARK-10systems.md §۳ + DOCTOR-BOX-OF-AGENTS-SPEC.md. اول PLAN.
بساز:
1) RFCArchive (MAP-Elites-style): سلول = (نوعِ گلوگاه × اندام)، بهترین-در-سلول، سقفِ اندازه + evict. mine از آرشیو sample/mutate کند. non-destructive: mineِ فعلی باقی.
2) measured_lift(rfc): در sandbox lift واقعی را روی یک held-out/seed بسنج؛ زیرِ آستانه → drop خودکار (به submit_for_approval نرسد). هیچ تماسِ production.
3) tournament_rank(rfcs): چند variant → مسابقهٔ Elo/pairwise در Inner Chamber؛ فقط بازمانده submit.
خطِ قرمز: propose-only · sandbox · λ_persist منفی · human-append برای merge · بدونِ import از *_gate/chrono/money · بدونِ LLMِ گران (tierِ ارزانِ gateway یا stub).
تست‌ها ($0): آرشیو کران‌دار می‌ماند و بهترین-در-سلول درست است · measured_lift پایینِ آستانه را drop می‌کند · tournament بازمانده را برمی‌گرداند · production لمس‌نشده · λ_persist هنوز منفی. خروجیِ خامِ run_all را paste کن.
Definition of Done: ۳ ماژول تست‌سبز، صفر production-touch، merge هنوز human-gated. ORGANISM-SPEC §2.7 آپدیت. هر ابهام → «⚑ برای معمار».
```

## Sources
- [Darwin Gödel Machine (arXiv 2505.22954)](https://arxiv.org/abs/2505.22954) · [Sakana AI announce](https://x.com/SakanaAILabs/status/1928272612431646943)
- [AlphaEvolve — DeepMind blog](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/) · [AlphaEvolve — Wikipedia](https://en.wikipedia.org/wiki/AlphaEvolve)
- [AI Co-Scientist — DeepMind](https://deepmind.google/blog/co-scientist-a-multi-agent-ai-partner-to-accelerate-research/) · [Co-Scientist → Nature (Labcritics)](https://labcritics.com/blog/2026/05/21/google-deepminds-co-scientist-graduates-from-research-demo-to-nature-paper/)
- [Self-improving agents 2026 guide (o-mega)](https://o-mega.ai/articles/self-improving-ai-agents-the-2026-guide) · [Beam AI / production self-improving (beam.ai)](https://beam.ai/agentic-insights/top-5-ai-agents-in-2026-the-ones-that-actually-work-in-production)
- [MAP-Elites / Quality-Diversity (EmergentMind)](https://www.emergentmind.com/topics/map-elites-algorithm) · [QD frontier (Frontiers)](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2016.00040/full)
- [Self-healing AWS AIOps auto-remediation (Infosys)](https://www.infosys.com/iki/techcompass/self-healing-systems.html)
- [GEPA reflective prompt evolution (arXiv 2507.19457)](https://arxiv.org/pdf/2507.19457)
