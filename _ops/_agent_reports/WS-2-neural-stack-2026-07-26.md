# WS-2 · Neural Stack — does it learn from data or from noise? · 2026-07-26

> این گزارش یک pass مستقلِ read-and-measure روی WS-2 است. رفتار runtime را تغییر ندادم؛ فقط فایل گزارش نوشته شد. ابزار این نوبت امکان اجرای Python/pytest/SQLite نداشت، پس Q3های «تزریق نویز» را اجرا نکردم؛ هرجا نتیجهٔ Q3 آمده، صریحاً مشخص کرده‌ام که inspection/natural-state است یا تستِ پیشنهادی.

## 1. VERDICT

شبکهٔ عصبی **وصل است** و یک مسیر کنترلی واقعی دارد: `NeuralDriver → Nociceptor/ReflexArc → protective_override → organism protective_skip`. اما «یادگیری» به‌معنای تغییر تصمیم فعلاً اثبات نشده و در چند جزء تزئینی/دورمانت است. شواهد دیسک: `neural/hebbian.json` فقط یک association دارد (`green_mode` + `stable`) با `strength=1.0` و `co_occurrences=2234`؛ `consolidation.json` تا cycle=529 جلو رفته ولی cycleهای آخر فقط `school_awareness` تکراری با insight ثابت «آگاهیِ میانگین: 0.61» دارند؛ `state/bcm-weights.json` با وجود `step=59` هیچ key ندارد؛ و هیچ `latent-vectors.json` یا `sparse-predictor.json` در `_ops/state` پیدا نشد. بنابراین protective nervous system واقعی است، ولی Hebbian/BCM/latent/sparse هنوز تصمیمِ قابل مشاهده را عوض نمی‌کنند.

## 2. Table — object | what it computes | who consumes it | Q3 | falsifiable | verdict

> یادداشت line refs: ابزار فایل محلی line-number نمی‌دهد؛ بنابراین به‌جای `file:line` دقیق، `file:function` آورده‌ام. این یکی از موارد «نتوانستم تشخیص دهم» است.

| object | what it computes | who consumes it | Q3 noise test result | falsifiable? | verdict |
|---|---|---|---|---|---|
| HebbianAssociator | از لیست signalهای هم‌زمان همهٔ جفت‌ها را می‌سازد؛ strength با `+0.1` تا سقف 1.0 بالا می‌رود و با decay ضربدر 0.95 کم می‌شود. | Writer: `_ops/wiring.py:neural_beat()` فقط وقتی `rhythm.mode_color == GREEN` و `spectral.sigma < 0.8` باشد `observe([green_mode, stable])` می‌زند؛ consumer تصمیمی برای `strong_associations()` یا `strength_of()` در مسیر زنده نیافتم. | اجرا نشد. inspection: اگر ورودی با نویز عوض شود `hebbian.json` عوض می‌شود، اما چون تصمیمی آن را نمی‌خواند، رفتار قابل مشاهده نباید عوض شود. | بله برای write-path: با signalهای متفاوت باید association عوض شود. نه برای decision-impact تا وقتی consumer ندارد. | **تزئینی به‌عنوان یادگیری.** دیسک فقط یک association aggregate دارد. |
| `hebbian.json` input distribution | توزیع واقعیِ ورودیِ Hebbian روی دیسک: یک جفت `green_mode/stable`، strength=1.0، co_occurrences=2234، raw event history ندارد. | فقط `HebbianAssociator._load()` می‌خواند و `_save()` می‌نویسد؛ مصرف تصمیمی پیدا نشد. | اجرا نشد. aggregate saturated است؛ با نویز فقط همین فایل تغییر می‌کند. | بله: اگر چند signal واقعی به stack برسد باید بیش از یک association دیده شود. | **یادگیری تک‌کاناله/اشباع‌شده، نه model غنی.** |
| ConsolidationCycle | verified sourceها را خلاصه می‌کند: acquisition→best content، doctor_archive→approved count، school_awareness→mean awareness، calibration→verdict count. | Writer: `_ops/wiring.py:consolidation_beat()` و `canonical_consolidation()`؛ consumer محتوایی نیافتم. `heart/producers.py:_count_consolidation()` فقط تعداد cycleهای فایل را برای velocity می‌شمارد، نه insightها را. | اجرا نشد. inspection: نویز در متن insight احتمالاً تصمیم را عوض نمی‌کند؛ فقط تعداد rowها ممکن است heartbeat/velocity telemetry را عوض کند. | بله: sourceهای unverified باید discard شوند؛ sourceهای verified باید در history بیایند. | **content تزئینی؛ row-count کمی operational.** |
| `consolidation.json` actual data | 529 cycle روی دیسک؛ cycleهای اخیر 523–529 همگی `verified_sources=[school_awareness]` و insight ثابت `آگاهیِ میانگین: 0.61` دارند؛ latent/bcm/sparse فیلدها null هستند. | `ConsolidationCycle._load()` و `_save()`؛ `heart/producers.py` فقط تعداد cycleهای اخیر را می‌شمارد. | اجرا نشد. اگر insight متن noise شود، تصمیمی پیدا نکردم که آن را بخواند. | بله: اگر acquisition/doctor_archive واقعی پاس داده شود باید sources متنوع و insight متفاوت ثبت شود. | **تکرارِ یک سنسور، نه یادگیری از دادهٔ متنوع.** |
| SharedLatentSpace | embedding R^32، cosine nearest، mean-pool integration، persist به `state/latent-vectors.json`. | `_ops/wiring.py:_enrich_with_latent()` می‌تواند آن را پر کند؛ `_apply_bcm()` keyها را می‌خواند. مصرف decision-path پیدا نشد. | اجرا نشد. search نشان داد `latent-vectors.json` وجود ندارد؛ بنابراین نویز فعلاً اثر observable ندارد. | بله: یک consolidation با encoded source باید فایل persist و non-null latent_vector بسازد. | **دورمانت/تزئینی فعلی.** |
| BCMStabilizer | قانون BCM: θ=EMA(y²)، `Δw=η*y*(y−θ)−β*w`؛ فقط retrieval index را prune می‌کند. | `_ops/wiring.py:_apply_bcm()` پس از latent enrichment؛ disk state: `state/bcm-weights.json` step=59 و `keys={}`. | اجرا نشد. با keys خالی، نویز ورودی هیچ decision effect ندارد. | بله: با known_keys غیرخالی باید weights/pruned/saturation non-empty شود. | **دورمانت؛ هیچ حافظه‌ای برای فراموش‌کردن ندارد.** |
| SparseInputFilter | EMA predictor per numeric key؛ novelty = prediction error؛ low-error numeric input فیلتر می‌شود؛ persist به `state/sparse-predictor.json`. | `_ops/wiring.py:consolidation_beat()` فقط روی `acquisition_data` اعمال می‌کند. در مسیر زندهٔ organism، `consolidation_beat()` بدون `acquisition_data` صدا زده می‌شود. | اجرا نشد. search نشان داد `sparse-predictor.json` وجود ندارد. | بله: دادهٔ عددی تکراری باید sparsity_ratio بالا و predictor file ایجاد کند. | **دورمانت؛ acquisition واقعی وارد مسیر فعلی نمی‌شود.** |
| Encoders | hash/statistical projection به R^32 برای observation/awareness/RFC/phi/calibration. | فقط `_enrich_with_latent()`؛ چون latent file absent و resultها null هستند، decision consumer فعلی دیده نشد. | اجرا نشد. نویز encoder تا وقتی latent consumer ندارد decision عوض نمی‌کند. | بله: deterministic same input→same vector؛ nonzero source→non-null vector. | **درست به‌عنوان ابزار، ولی فعلاً بی‌اثر در رفتار.** |
| NeuralDriver | pain/reflex/snapshot/brain_inputs advisory از rhythm/sensory/spectral/budget. | `_ops/wiring.py:neural_beat()`؛ `_ops/organism.py` بعدش `protective_override()` را می‌خواند. | اجرا نشد. این تنها جایی است که noise احتمالاً رفتار را عوض می‌کند: pain>0.7 باید protective_skip بدهد. | بله: budget/error/freeze/afferent/sigma شدید باید pain/reflex را فعال کند. | **مسیر عصبی واقعی، اما learning نیست.** |
| Nociceptor | pain از budget_pct، error_rate، freeze، partner_stress، afferent deficit، sigma proximity. | `NeuralDriver.evaluate()` و سپس `protective_override()`. | اجرا نشد؛ current `ORGANISM-STATE.protective_skip=false`. | بله: pain>0.7 باید protective redirect بدهد. | **واقعی/کنترلی.** |
| ReflexArc | sigma>1 critical throttle، budget>80 slow، afferent<0.1 alarm، RED pause، pain>0.7 critical pause. | `NeuralDriver.evaluate()` → `protective_override()`؛ organism می‌تواند non-essential work را skip/throttle کند. | اجرا نشد. | بله: synthetic snap با sigma>1 باید critical reflex بدهد. | **واقعی/کنترلی.** |

## 3. Three highest-value next steps + smallest proving tests

1. **Probe: prove Hebbian is or is not decorative by noise-injection against behaviour.**  
   *Why necessary:* `hebbian.json` mutates, but no decision consumer was found. Without a noise test, “learning” remains a file write, not a behaviour.  
   *Smallest test:* in isolated `OPS_DIR`, create two neural stacks with identical rhythm/sigma/budget, monkeypatch `HebbianAssociator.strength_of()` to return random values in one stack, run one `neural_beat()` + one downstream decision path, and assert all externally visible outputs are identical. If identical, mark Hebbian decorative until a consumer is added.

2. **Close a learning→decision loop with lead scoring in shadow, or explicitly mark consolidation/latent/BCM as advisory-only.**  
   *Why necessary:* the only business-relevant near-term decision is lead scoring/drafting. Neural learning must change that decision to count as learning.  
   *Smallest test:* seed a semantic/latent insight such as “direct residential repaint above threshold should draft”; run a synthetic lead through scorer twice (without and with the learned signal) under a default-off flag; require action or reason to change and decision receipt to cite the learned source. If no change, the learning stack is advisory/decorative.

3. **Feed real numeric acquisition/outcome data into consolidation in a test harness and require durable non-null artifacts.**  
   *Why necessary:* live `consolidation.json` is mostly repeated `school_awareness`; latent/BCM/sparse artifacts are absent or empty.  
   *Smallest test:* isolated state with `acquisition_data={"lead_draft_rate": 3, "proposal_accept_rate": 1}` and `doctor_archive=[{outcome:"approved"}]`; call `consolidation_beat()` with `OCTOPUS_WIRE_BCM=1` and `OCTOPUS_WIRE_SPARSE=1`; assert `latent-vectors.json` exists, latest `latent_vector` non-null, `bcm-weights.keys` non-empty, and `sparse-predictor.json` exists.

## 4. Everything I could NOT determine

- I could not run Q3 noise-injection tests; tool access here was read/write filesystem only.
- I could not produce exact `file:line` citations because local file reads are not line-numbered. I used `file:function` anchors.
- I could not prove repo-wide absence of Hebbian/latent/BCM consumers with a content grep tool; I inspected the live wiring/organism path and relevant modules.
- I could not query `memory.db`/SQLite or run the full test suite.
- I could not determine whether current in-process env exactly matches `OCTOPUS-flags.cmd`; I could only verify the state snapshot and disk flags.

## 5. Predictions registered and outcomes

| prediction | outcome | note |
|---|---|---|
| P1: Hebbian state will not show diverse learning events. | **Confirmed.** `hebbian.json` has one association: `green_mode/stable`, strength=1.0, co_occurrences=2234. | This is aggregate tick co-occurrence, not a raw event distribution. |
| P2: BCM will be effectively empty. | **Confirmed.** `state/bcm-weights.json` is `{"step":59,"beta":0.02,"keys":{}}`. | No keys means no pruning/forgetting can affect retrieval. |
| P3: latent/sparse durable artifacts will be absent. | **Confirmed.** Search found no `latent-vectors.json` and no `sparse-predictor.json` under `_ops`. | Latest consolidation rows also have null latent/bcm/sparse fields. |
| P4: consolidation will be active but content-repetitive. | **Confirmed.** Latest cycles 523–529 all read `school_awareness` and repeat mean awareness 0.61. | Active file write ≠ demonstrated behavioural learning. |
| P5: neural control path will be real even if learning is decorative. | **Confirmed by code/state.** `NeuralDriver`/`Nociceptor`/`ReflexArc` feed `protective_override`; current `ORGANISM-STATE.protective_skip=false`. | This is protection/control, not learning. |
