# RESEARCH LANE — Theoretical foundations
# مبانیِ نظریِ self-improvement برای AI agents — مرزِ واقعیِ ۲۰۲۶

> **DOMAIN:** سیستم‌های multi-agent خودمیزبان برای اپراتور تک‌نفره.
> **LANE (قفل‌شده):** فقط مبانیِ نظریِ self-improvement، سه سطح و محدودیتِ هر سطح، یافته‌های کلیدیِ ۲۰۲۶، و اینکه معماریِ LANGAR/Fusion از نظرِ نظری چقدر درست است.
> **archetype: math/theory.** عمیق برو، بر مفاهیم تمرکز کن، نه فقط نقلِ قول.
> **CONSTRAINTS:** VPS مشترک + لپ‌تاپ + Claude Cowork؛ تک‌نفره؛ weight update ممنوع در production.
> **تاریخِ ساخت:** ۲۰۲۶-۰۷-۰۱. منابع از web search زنده + مرورِ مقالات. برچسب: `[established] / [emerging] / [speculative]`.

---

## Summary

۱. **یافته‌ی کلیدیِ نظری:** self-improvement در سه سطح رخ می‌دهد — (A) in-context/skill edits با weights ثابت، (B) harness/scaffold edits با weights ثابت، (C) weight update. هر سطح **ترتیبِ بزرگ** تفاوت در capability، ریسک، و infrastructure لازم دارد. برای تو فقط A و B جایز است. `[established]`

۲. **مهم‌ترین یافته‌ی نظری ۲۰۲۵–۲۰۲۶:** Utility-Learning Tension (Wang et al.، arXiv:2510.04399). Self-modification که immediate performance را بهتر می‌کند **می‌تواند** شرایطِ آماریِ لازم برای generalization را از بین ببرد. این یک اتفاق است نه یک نگرانی فرضی. تضمینِ یادگیری فقط اگر family مدل uniformly capacity-bounded باشد حفظ می‌شود. `[established]`

۳. **SkillOpt (Microsoft، مه ۲۰۲۶):** اولین optimizer سیستماتیک برای SKILL.md به‌عنوانِ «trainable external state of a frozen agent». نتیجه: +23.5 امتیاز روی GPT-5.5، 52/52 سلولِ ارزیابی best-or-tied. معادلِ deep learning را برای text space پیاده می‌کند. این دقیقاً همان چیزی است که Fusion Phase 3 نیاز دارد و از نظرِ نظری justify می‌شود. `[established]`

۴. **HyperAgents (Meta، مارس ۲۰۲۶):** agent و meta-agent در یک برنامه‌ی خودقابل‌تغییر. «metacognitive self-improvement» — سیستم می‌تواند فرآیندِ بهبودِ خودش را بهبود بدهد. ولی: هنوز weights ثابت است؛ production-ready نیست؛ نیازِ به زیرساختِ evolutionary بزرگ دارد. `[emerging]`

۵. **معماریِ LANGAR/Fusion از نظرِ نظری:** تنظیمِ صحیح است. LANGAR به‌عنوانِ calibrated evidence store ← Fusion به‌عنوانِ skill library ← validation gate سه‌شرطی = دقیقاً «two-gate policy» که Wang et al. برای حفظِ learnability ضروری می‌دانند. `[Probable]`

---

## Landscape

### ۱) سه سطح — چارچوبِ اصلی

`[established]` — این taxonomy از SIA (arXiv:2605.27276، مه ۲۰۲۶) + ICLR 2026 Workshop on AI with Recursive Self-Improvement است.

---

**سطحِ A — In-context / Skill edits (weights ثابت)**

تعریف: همه‌ی تغییرات فقط روی **external state** هستند — SKILL.md، system prompt، tool descriptions، memory content — در حالی که base model هیچ تغییری نمی‌کند.

**چرا این سطح امن‌ترین است:**
- capacity bounded: مدل همان مدل است، فقط contextِ آن عوض می‌شود
- rollback trivial: یک git revert SKILL.md را برمی‌گرداند
- validation ممکن است: held-out eval می‌تواند improvement را تأیید کند قبل از commit

**محدودیتِ نظری:** Agent نمی‌تواند از ceiling مدلِ base خود فراتر رود. اگر base model نمی‌تواند یک task را انجام دهد، هیچ SKILL.md بهتری این را fix نمی‌کند — فقط efficiency روی taskهایی که قبلاً در capability‌اش بوده بهتر می‌شود.

**SkillOpt در این سطح:** rollout batch → minibatch reflection → bounded add/delete/replace edits → strict held-out validation gate → اگر بهتر شد → commit، اگر نشد → rejected-edit buffer. این loop IterLog دقیقاً معادلِ gradient descent در text space است. Edit budget = learning rate. Validation gate = test set.

```
Loop مفهومی SkillOpt:
best_skill = init_skill.md
for epoch in range(max_epochs):
    trajectories = rollout(agent, tasks, best_skill)
    edits = reflect(trajectories, budget=8_edits)  # bounded
    candidate = apply_edits(best_skill, edits)
    if eval(candidate, held_out) > eval(best_skill, held_out):  # strict
        best_skill = candidate
    else:
        rejected_buffer.append(edits)  # negative feedback
```

---

**سطحِ B — Harness/Scaffold edits (weights ثابت)**

تعریف: تغییر در **architecture**ِ agentی بدونِ تغییرِ weights — ترتیبِ tool callها، logic orchestration، state management، retry policy. این سطح بیشتر می‌تواند تغییر بدهد ولی ریسک بیشتری دارد.

**نمونه‌های ۲۰۲۶:**
- **Darwin Gödel Machine** (Zhang et al.، مه ۲۰۲۵، ICLR 2026): agent own source code را modify می‌کند. Darwinian selection: archive از variants، parent selection بر اساسِ quality + diversity. نتیجه: SWE-bench 20.0٪ → 50.0٪.
- **HyperAgents** (Meta، مارس ۲۰۲۶): task agent + meta agent در یک برنامه. Meta-agent خودش هم editable است → «metacognitive self-modification». Transfer across non-coding domains (paper review، robotics، Olympiad math).
- **Meta-Harness** (Lee et al.، ۲۰۲۶): LLM-driven harness mutation با end-to-end optimization.

**محدودیتِ مهم DGM:** «Self-improvement only worked well in domains where the task (coding) aligned with the modification substrate (also coding).» وقتی DGM coding code می‌نویسد و coding benchmark هم coding است، تقویتِ مهارتِ coding = تقویتِ توانایی self-modification. این alignment در coding وجود دارد، در ماینینگ یا حسابداری به این شکل نیست.

**محدودیتِ HyperAgents:** هنوز base model ثابت است. فقط scaffold editable است. و نیازِ به یک evolutionary infrastructure بزرگ دارد که برای VPS solo-operator فعلاً غیرعملی است.

---

**سطحِ C — Weight update (Fine-tuning / RL)**

تعریف: تغییر در **weights** مدلِ base — fine-tuning، RLHF، RL روی trajectories.

**چرا این سطح برای تو نیست:**
- نیازِ به هزاران trajectory labeled دارد
- نیازِ به compute زیاد دارد (GPU)
- Anthropic نوامبر ۲۰۲۵: reward hacking مستند شد — مدل sys.exit(0) زد تا تست‌ها pass شوند
- هیچ rollback ساده‌ای وجود ندارد — همان مدلِ اصلاح‌شده می‌ماند
- برای production یک اپراتورِ تک‌نفره: NOT recommended `[established]`

این همان چیزی است که LANGAR no-self-improvement rule (Lane 3) ممنوع می‌کند — و حالا می‌دانیم چرا از نظرِ نظری درست است.

---

### ۲) نظریه‌ی Gödel Machine — وعده و محدودیتِ آن

`[established]`

Schmidhuber (2007) یک framework نظری پیشنهاد کرد: یک self-improving AI که هر بار خودش را modify می‌کند فقط وقتی می‌تواند ثابت کند که تغییر utility انتظاری را افزایش می‌دهد.

**مشکلِ اساسی:** «Proving that most changes are net beneficial is impossible in practice.» (arXiv:2505.22954 — همان مقاله‌ی DGM)

DGM این را با empirical validation جایگزین کرد — به‌جای proof، یک eval benchmark. این بسیار pragmatic‌تر است ولی یک ضعف دارد: اگر benchmark نمایندگیِ درستی از real-world performance ندارد، empirical validation هم گمراه می‌کند.

**ارتباط با LANGAR:** LANGAR's calibrated evidence store = همان empirical validation mechanism. وقتی LANGAR اعتمادِ یک decision را score می‌کند، دارد همان کاری را می‌کند که DGM با held-out benchmark می‌کند — ولی با real operational data به‌جای synthetic benchmark.

---

### ۳) Utility-Learning Tension — یافته‌ی اساسیِ نظری ۲۰۲۵

`[established]`

**Wang، Dorchen، Jin (Columbia University، arXiv:2510.04399، اکتبر ۲۰۲۵)**

**قضیه‌ی مرکزی (ساده‌شده):** در یک agent خودتغییردهنده، تغییراتی که performance فوری را بهینه می‌کنند می‌توانند شرایطِ آماریِ لازم برای generalization reliable را از بین ببرند.

به زبانِ ساده: **performance فوری بهتر ≠ system بهتر.** می‌توانی روی eval suite خودت خوب شوی ولی روی taskهای نادیده بدتر شوی.

**نتیجه‌ی دقیق:** «Distribution-free guarantees are preserved if and only if the policy-reachable model family is uniformly capacity-bounded; when capacity can grow without limit, utility-rational self-changes can render learnable tasks unlearnable.»

**چه می‌گوید:**
- bounded edits (مثلاً SKILL.md با max 8 edit per step) → learnability حفظ می‌شود
- unbounded self-modification (مثلاً DGM که همه چیز را عوض می‌کند) → learnability ممکن است از بین برود

**«Two-gate policy»:** Wang et al. یک راه‌حلِ عملی پیشنهاد می‌کنند: هر تغییر باید دو gate رد شود — (۱) immediate utility بهتر شود (eval score)، (۲) generalization degradation نشود (regression test). این دقیقاً همان validation gate سه‌شرطیِ تو است.

**ارتباطِ مستقیم با معماری تو:**
- LANGAR = generalization monitor (gate ۲)
- Fusion validation gate = immediate utility check (gate ۱)
- «No new failure categories» = boundary روی capacity growth

---

### ۴) SkillOpt در عمق — چرا این theoretical breakthrough است

`[established]`

**Yang et al. (Microsoft Research، arXiv:2605.23904، مه ۲۰۲۶)**

قبل از SkillOpt، سه رویکرد برای بهبودِ skill documents وجود داشت:
1. **Hand-crafted:** انسان می‌نویسد → performance varies → بهبود نیاز به انسانِ دیگر دارد
2. **One-shot LLM generation:** یک بار LLM می‌نویسد → better than random ولی plateu می‌کند
3. **Loosely controlled self-revision:** agent خودش edit می‌کند بدونِ کنترلِ دقیق → می‌تواند regression بدهد

**SkillOpt چرا متفاوت است:** معادلِ deep learning را وارد text space کرد:

| Deep Learning | SkillOpt |
|---|---|
| Model weights | SKILL.md content |
| Forward pass | Rollout batch |
| Loss function | Held-out eval score |
| Backward pass | Optimizer model reflection |
| Learning rate | Edit budget (max N edits per step) |
| Gradient clipping | Bounded add/delete/replace |
| Validation set | Held-out selection split |
| Early stopping | No-improvement-for-N-steps |
| Momentum | Slow/meta update |
| Negative examples | Rejected-edit buffer |

**نتیجه‌ها:**
- +23.5 امتیاز GPT-5.5 در direct chat
- +24.8 امتیاز داخلِ Codex CLI
- +19.1 امتیاز داخلِ Claude Code
- 52/52 سلولِ ارزیابی best-or-tied در برابرِ human-written، TextGrad، GEPA، EvoSkill، Trace2Skill

**Transfer:** skills روی مدلِ A بهینه شده روی مدلِ B هم work می‌کنند. این به معنای model-portability است — اگر از Claude Sonnet به Gemini migrate کردی، SKILL.md‌هایت خراب نمی‌شوند.

**محدودیتِ اساسی:** «SkillOpt is most directly applicable when the target task has automatic verifiers, exact-match metrics, executable checks, or otherwise reliable feedback signals. For open-ended domains where success is subjective, the validation gate may require stronger human or model-based evaluation.»

**برای تو:** taskهایی که LANGAR می‌تواند objective score بدهد (مثلاً backtest P&L، eval precision/recall، code execution success) → SkillOpt مستقیماً قابلِ اعمال است. taskهایی که score ذهنی‌تر است (مثلاً quality تحلیل) → judge model برای validation gate لازم است.

---

### ۵) HyperAgents — frontier نه production

`[emerging]`

**Zhang et al. (Meta، UBC، Vector Institute، arXiv:2603.19461، مارس ۲۰۲۶)**

**معماری:** DGM-H = DGM با meta-agent mutizable. Task agent و meta-agent در یک program. Meta-agent می‌تواند خودش را rewrite کند.

**نتایج:** transfer across domains: SWE-bench، paper review (ICLR/NeurIPS acceptance decisions)، robotics reward design، Olympiad math grading (imp@50 = 0.630 vs human hand-designed = 0.0).

**چه معنایی دارد:** اولین سیستمی که meta-level improvement strategy خودش را بهبود می‌دهد — «metacognitive self-modification». SkillOpt فقط task skill را بهبود می‌دهد؛ HyperAgents فرآیندِ بهبود را هم بهبود می‌دهد.

**چه معنایی ندارد (برای تو):**
- Base model (Claude، GPT-4o) هنوز frozen است
- نیازِ به evolutionary infrastructure، archive از variants، population-based search
- هر «generation» صدها LLM call می‌زند
- برای VPS solo-operator: در حدِ $50–$500 per optimization round در compute و API هزینه
- production-ready: NO

**آنچه می‌توان از HyperAgents یاد گرفت:** ایده‌ی «meta-level skills» — مثلاً یک SKILL.md که «چطور SKILL.md خوب بنویسیم» را توضیح می‌دهد. این immediately applicable است بدونِ evolutionary infrastructure.

---

### ۶) Lineage نظریِ SkillOpt — از کجا آمد

`[established]`

این lineage مهم است چون نشان می‌دهد field به کجا می‌رود:

| ۲۰۲۲ | ReAct (Yao et al.) | reasoning + acting interleave |
|---|---|---|
| ۲۰۲۳ | Reflexion (Shinn et al.) | verbal reinforcement از failure |
| ۲۰۲۳ | Voyager (Wang et al.) | ever-growing skill library (فقط add، never refine) |
| ۲۰۲۳ | DSPy (Khattab et al.) | pipeline compiler؛ declarative LM calls |
| ۲۰۲۴ | TextGrad (Yuksekgonul et al.) | differentiation through text |
| ۲۰۲۵ | GEPA (Stanford) | reflective prompt evolution |
| ۲۰۲۵ | DGM (Zhang et al.) | open-ended evolution of agent code |
| ۲۰۲۶ | SkillOpt (Yang et al.) | bounded + validated skill optimization |
| ۲۰۲۶ | HyperAgents (Zhang et al.) | meta-level improvement mutability |

**چیزی که SkillOpt بهتر از TextGrad/GEPA می‌کند:** validation gate (strict improvement) + bounded edits + rejected-edit buffer. این سه با هم learnability را حفظ می‌کنند — دقیقاً آنچه Wang et al. نشان دادند ضروری است.

**چیزی که DSPy و SkillOpt مکمل هم هستند:** DSPy ساختارِ pipeline را optimize می‌کند؛ SkillOpt محتوایِ skill را optimize می‌کند. می‌توانی هر دو را با هم استفاده کنی.

---

### ۷) تحلیلِ معماریِ LANGAR/Fusion از نظرِ نظری

`[Probable]` — این تحلیلِ من است، نه مستقیماً از مقالات.

**اعتبارِ نظری:**

۱. **LANGAR به‌عنوانِ calibrated evidence store:**
معادلِ «empirical validation» در DGM است. به‌جای یک static benchmark، LANGAR real operational data دارد. این از نظرِ نظری قوی‌تر از benchmark synthetic است — ecological validity بالاتر. ولی: cold-start problem (ledger خالی) = validation gate بی‌معنی می‌شود اگر داده‌ای نباشد.

۲. **Validation gate سه‌شرطی (regression ≤5٪، target metric بهتر، no new failure):**
این دقیقاً «two-gate policy» از Wang et al. است. Gate ۱ = immediate utility (target metric). Gate ۲ = generalization preservation (no regression، no new failures). **نظری** تأیید می‌کند این درست است.

۳. **LANGAR no-self-improvement rule:**
از lane 3: Fusion phase 3 می‌گذارد system prompt خودش را rewrite کند ولی فقط از طریقِ sequential unlocking. این capacity bounding در عمل است — system نمی‌تواند خودش را unboundedly modify کند.

۴. **Cold-start bottleneck:**
از نظرِ نظری، SkillOpt و هر validation-gated self-improvement «requires scored trajectories and a held-out selection split.» این یعنی بدونِ data، هیچ self-improvement ممکن نیست. این دقیقاً همان «cold-start ledger data» bottleneck است که از لِینِ 0 شناسایی شد. نه یک bug در طراحی — یک محدودیتِ بنیادیِ نظری.

۵. **LANGAR's no-self-improvement در phase 1 و 2:**
از نظرِ utility-learning tension: وقتی capacity بزرگ شود without proper bounds، learnability از بین می‌رود. وقتی LANGAR خودش را نمی‌تواند تغییر دهد تا Phase 3، این capacity growth را bound می‌کند. درست نه از روی احتیاطِ تجربی، بلکه از نظرِ نظری.

**آنچه از نظرِ نظری درست نیست (یا نیازِ به توجه دارد):**

- **Specification gaming روی eval suite:** اگر همان eval cases را برای self-improvement به کار ببری، agent می‌تواند آن caseها را overfit کند. Wang et al. این را explicit نمی‌گویند ولی utility-learning tension این را پیش‌بینی می‌کند. راهِ حل: held-out test set جداگانه که agent آن را ندیده.

- **Open-ended task validation:** SkillOpt گفت برای taskهایی که success ذهنی است، validation gate به evaluator نیازمند است. اگر evaluator (LLM-as-judge) family bias دارد، optimization به سمتِ satisfaction of judge می‌رود نه real quality. این همان «judge و production model از یک خانواده = false positive» از lane 5 است.

---

## Comparison table

> سه سطحِ self-improvement از نظرِ نظری + عملی. `[established]`

| بُعد | Level A (Skill edits) | Level B (Scaffold edits) | Level C (Weight update) |
|---|---|---|---|
| **Foundation model** | Frozen | Frozen | Modified |
| **What changes** | SKILL.md، prompt، memory | Orchestration، tool logic، harness | Weights |
| **Rollback** | git revert (trivial) | git revert (moderate) | دشوار یا غیرممکن |
| **Validation gate** | held-out eval ممکن | held-out eval + regression | نیازِ به test suite بزرگ |
| **Data requirement** | ≥20 scored trajectories per skill | ≥100 benchmark runs | هزاران trajectory labeled |
| **Learnability guarantee** | با bounded edits | با bounded scaffold | without proper setup |
| **Production-ready** | ✅ الان | ⚠️ برای coding domains | ❌ برای solo-operator |
| **Example tools** | SkillOpt، GEPA، TextGrad | DGM، HyperAgents | SIA، RLHF |
| **SkillOpt gain (GPT-5.5)** | +23.5pt (direct)، +24.8pt (Codex) | — | — |
| **DGM gain (coding)** | — | 20%→50% SWE-bench | — |
| **Cost برای solo-operator** | ✅ کم | ⚠️ متوسط (API calls برای optimization) | ❌ GPU intensive |

---

## Blind spots

- **«Self-improvement = بهتر شدن همیشگی» اشتباه است.** `[established]` Utility-learning tension نشان می‌دهد بهتر شدنِ روی eval می‌تواند با بدتر شدنِ generalization همراه باشد. باید هر دو را همزمان monitor کنی. این چیزی نیست که intuition پیش‌بینی کند.

- **DGM alignment bottleneck.** `[established]` DGM در coding خوب کار کرد چون task = substrate. در ماینینگ/حسابداری این alignment وجود ندارد. بهبودِ «skill نوشتنِ ماینینگ» به بهبودِ «ماینینگ decision» کمک نمی‌کند به همان شکلِ خودکار.

- **SkillOpt فقط برای evaluatable tasks.** `[established]` «The validation gate may require stronger human or model-based evaluation» برای open-ended tasks. اگر success را نمی‌توانی objective اندازه بگیری، SkillOpt optimization loop به سمتِ proxy metric می‌رود. برای LANGAR: taskهایی با binary یا numeric output ایده‌آل هستند.

- **HyperAgents هنوز base model frozen است.** `[established]` خیلی‌ها این را miss می‌کنند. HyperAgents scaffold را عوض می‌کند، نه weights. «Only harness/scaffold is editable.» برای پرسیدنِ «آیا HyperAgents می‌تواند Claude را بهتر کند»، پاسخ نه است — فقط می‌تواند scaffold را بهتر کند.

- **Cold-start data = محدودیتِ بنیادی، نه limitation موقت.** `[established]` SkillOpt گفت «requires scored trajectories.» این یعنی هر self-improvement، هر چقدر هم که نظریِ پشتِ آن محکم باشد، بدونِ real operational data ممکن نیست. این اساسی‌ترین نکته است.

- **Capacity bounding ≠ performance ceiling.** `[Probable]` ممکن است بنظر برسد که «bounded capacity = محدودیت.» ولی Wang et al. نشان می‌دهند unbounded capacity یعنی unlearnable tasks. Bounded = stable generalization + یاد گرفتن. این tradeoff است نه limitation.

- **ICLR 2026 RSI Workshop signal:** «how do we build algorithmic foundations for powerful AND reliable self-improving AI systems?» این سؤالِ باز است. هنوز هیچ سیستمی نیست که هر دو را در production ثابت کند. `[established]`

---

## Recommendation

**آنچه این نظریه برای پیاده‌سازیِ فعلیِ تو می‌گوید:**

### ۱. SkillOpt را به عنوانِ Fusion Phase 3 engine بگیر

SkillOpt (MIT-licensed open-source، GitHub: `microsoft/SkillOpt`) دقیقاً آن چیزی است که Fusion برای skill evolution نیاز دارد:
- skill را به‌عنوانِ trainable external state تلقی کن (نه static prompt)
- هر بهبود از bounded edits بگذرد
- هر update باید validation gate را pass کند
- rejected edits را نگه دار (negative feedback برای optimizer)

**SkillOpt-Sleep** (preview، ژوئن ۲۰۲۶): نسخه‌ی scheduled که شبانه از session‌های گذشته یاد می‌گیرد و skills را بهبود می‌دهد — این دقیقاً معادل «dreaming» feature Anthropic است.

### ۲. Validation gate = two-gate policy از Wang et al.

قبلاً ۳ شرط داشتیم:
- regression ≤5٪ روی anchor set
- target metric بهتر
- no new failure categories

نظریه‌ی Wang et al. این را تأیید می‌کند: gate اول = utility check، gate دوم = learnability check. هر دو لازم‌اند. یکی بدونِ دیگری کافی نیست.

### ۳. Level A فقط — level B را برای وقتی که داده‌ی کافی داری

الان (cold-start): فقط manual skill writing + SkillOpt offline validation. بعد از اینکه ≥50 scored trajectory per project داشتی: SkillOpt loop را روی آن tenant اجرا کن. بعد از اینکه ≥200 trajectory داشتی: به Level B (scaffold optimization) فکر کن.

### ۴. Alignment check قبل از هر skill domain

قبل از اینکه self-improvement loop برای یک tenant راه بیندازی، بپرس: «آیا task (مثلاً ماینینگ) و substrate (مثلاً نوشتنِ skill.md) به هم align هستند؟» اگر نه، بهبودِ skill writing لزوماً بهبودِ ماینینگ decision نمی‌دهد. باید یک explicit link باشد — مثلاً skill execution log → score → SkillOpt loop.

### ۵. DSPy + SkillOpt با هم

این دو مکمل هم هستند:
- DSPy: ساختارِ pipeline را compile و optimize می‌کند
- SkillOpt: محتوایِ skill document را optimize می‌کند
- هر دو با frozen base model کار می‌کنند
- هر دو با Anthropic Claude Sonnet/Opus کار می‌کنند

### دقیقاً چه چیزی را **نساز:**

- ❌ **HyperAgents production implementation** — نیازِ به evolutionary infrastructure بزرگ؛ هزینه‌ی compute بسیار بالا؛ solo-operator inappropriate
- ❌ **Unbounded skill self-modification** — از utility-learning tension: capacity بدونِ bound → learnability تهدید می‌شود
- ❌ **SkillOpt loop بدونِ held-out test set جداگانه** — specification gaming روی eval suite
- ❌ **Level C (weight update) بدونِ هزاران trajectory و GPU** — neither feasible nor necessary
- ❌ **Self-improvement قبل از داشتنِ real operational data** — validation gate بدونِ data = بی‌معنی

---

## TOOLING

| Tool | کاربرد | License | Cost | Lock-in |
|---|---|---|---|---|
| **SkillOpt (Microsoft)** | Text-space optimizer برای SKILL.md | MIT (verify آخرین version) | OSS رایگان + API cost برای optimizer | **2** |
| **SkillOpt-Sleep (preview)** | Scheduled nightly self-evolution | MIT (`verify`) | همان | **2** |
| **DSPy (Stanford)** | Pipeline compiler + prompt optimization | MIT | OSS رایگان | **2** |
| **TextGrad (Stanford)** | Text-space differentiation | MIT | OSS رایگان | **1** |
| **GEPA (Stanford)** | Reflective prompt evolution | — (`verify`) | OSS (`verify`) | **2** |
| **DGM (Sakana AI)** | Open-ended code evolution | MIT (`verify`) | Compute intensive | **3** |
| **Voyager pattern** | Growing skill library (add-only) | MIT (MC-based) | API cost | **2** |
| **claude-agent-sdk** | Skill + subagent runtime (Anthropic) | Proprietary | API billing | **7** |
| **Anthropic Dreaming feature** | Scheduled skill consolidation (Anthropic managed) | N/A | subscription | **8** |

---

## If-I'm-wrong

**قوی‌ترین ضدِ توصیه («SkillOpt برای open-ended tasks insufficient است»):** SkillOpt در کار کردن با closed benchmark tasks ثابت شده. برای taskهایی مثلِ «کیفیتِ تحلیلِ ماینینگ» که binary success ندارند، validation gate نیازِ به LLM-as-judge دارد که خودش biasهای خودش را دارد. اگر judge model با production model از یک family باشد، family bias → false positive → specification gaming. این یک محدودیتِ واقعی است ولی قابلِ مدیریت است با cross-model judge.

**ضدِ توصیه‌ی دوم («Level B (scaffold edits) را می‌توان الان در solo-operator استفاده کرد»):** درست است که DGM برای کدنویسی کار کرد ولی هزینه‌ی evolutionary archive maintenance برای solo-operator بالاست. با این حال، «meta-level skills» (SKILL.md که چطور SKILL.md بنویسیم) یک approximation ارزان است که می‌توان الان پیاده کرد — بدونِ evolutionary infrastructure کامل.

**ضدِ توصیه‌ی سوم («Utility-Learning Tension فقط برای weight update مهم است»):** Wang et al. نشان می‌دهند این tension برای هر نوعِ self-modification صادق است — شامل text edits. ولی severity در Level A خیلی کمتر از Level C است چون capacity bounded است. این یعنی توصیه‌ی bounded edits در SkillOpt کافی است برای Level A، ولی در Level B (scaffold edits بزرگ‌تر) نیازِ به monitoring دقیق‌تر است.

---

## Confidence

**High** برای Utility-Learning Tension result، SkillOpt results، و DGM limitations. **Medium** برای HyperAgents production implications (emerging، Feb 2026) و ارتباطِ مستقیم با معماریِ LANGAR/Fusion (تحلیلِ من). **Low** برای پیش‌بینیِ اینکه Level B چه زمانی production-ready می‌شود؛ و اینکه DGM alignment bottleneck چقدر severe است در non-coding domains (limited empirical evidence).

---

## Claims table

| claim | evidence | confidence (H/M/L) | source + date |
|---|---|---|---|
| سه سطحِ self-improvement: A (skill/in-context)، B (scaffold)، C (weight update) | SIA taxonomy | H | arXiv:2605.27276، ۲۰۲۶-۰۵ |
| Utility-Learning Tension: utility-driven changes می‌توانند generalization را از بین ببرند | formal theorem + experiments | H | arXiv:2510.04399، Columbia، Oct 2025 |
| Distribution-free guarantees preserved iff capacity uniformly bounded | central theorem | H | arXiv:2510.04399 |
| «Two-gate policy»: immediate utility + learnability preservation = safe self-modification | paper result | H | arXiv:2510.04399 |
| Gödel Machine: provably beneficial self-modification theoretically possible ولی practically impossible | Schmidhuber 2007 + DGM paper | H | arXiv:2505.22954 |
| DGM: SWE-bench 20%→50% از طریقِ open-ended code evolution، ICLR 2026 | benchmark results | H | arXiv:2505.22954، Sakana AI |
| DGM limitation: only works where task aligns with modification substrate (coding) | explicit in paper | H | arXiv:2505.22954 |
| HyperAgents (Meta، March 2026): merge task agent + meta agent؛ metacognitive self-improvement | Meta research | H | arXiv:2603.19461، ICLR 2026 |
| HyperAgents: transfer to non-coding (paper review، robotics، Olympiad math imp@50=0.630) | benchmark results | H | ai.meta.com/research/publications/hyperagents |
| HyperAgents: base model frozen؛ only scaffold editable | explicit in paper | H | arXiv:2603.19461 |
| SkillOpt: +23.5pt GPT-5.5 direct، +24.8pt Codex، +19.1pt Claude Code؛ 52/52 best-or-tied | benchmark | H | arXiv:2605.23904، Microsoft Research، May 2026 |
| SkillOpt: SKILL.md به‌عنوانِ trainable external state of frozen agent | core claim | H | microsoft.github.io/SkillOpt |
| SkillOpt-Sleep: nightly self-evolution companion برای Claude Code/Codex (June 2026، preview) | GitHub release | H | github.com/microsoft/SkillOpt |
| SkillOpt limitation: requires automatic verifiers؛ open-ended tasks need human/model gate | paper limitation section | H | arXiv:2605.23904 |
| DSPy + SkillOpt complementary: pipeline structure vs skill content optimization | SkillOpt author quote | H | venturebeat.com، May 2026 |
| ICLR 2026 Workshop on AI with RSI: RSI moving from thought experiments to deployed systems | workshop summary | H | openreview.net |
| Reflexion (2023)، TextGrad (2024)، GEPA (2025) = ancestors of SkillOpt | lineage documented | H | pebblous.ai 2026-05 |
| SkillOpt skills transfer across models و harnesses | transfer table in paper | H | arXiv:2605.23904 |
| Voyager (2023): first growing skill library ولی only add، never refine | Wang et al. 2023 | H | standard reference |
| Level C (weight update): Anthropic Nov 2025 reward hacking documented | lane 3 (confirmed) | H | lِین 3 گزارش |

---

*فایل: `14-research-theoretical-foundations.md` — آماده‌ی merge با سایرِ laneها با همین ۸ سرفصلِ ثابت.*
