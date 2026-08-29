# Active Inference: مدل مولد، belief و EFE

## اجزای مدل گسسته

- `s`: حالت پنهان؛ چیزی که agent مستقیماً نمی‌بیند.
- `o`: observation؛ خروجی حسگر/دسته‌بندی.
- `A[o,s] = P(o|s)`: likelihood یا نگاشت حالت به مشاهده.
- `B[s',s,u] = P(s'|s,u)`: transition کنترل‌شده.
- `C[o]`: ترجیح مشاهده‌ها؛ «چه outcomeهایی مطلوب‌ترند».
- `D[s] = P(s0)`: prior حالت آغازین.
- `E[π]`: prior روی policyها/عادت‌ها.
- `qs`: belief posterior تقریبی دربارهٔ state.

`[DOCUMENTED] /opt/octopus/ofn-l4/docs/SCALE-AND-ACTIVE-INFERENCE.md:148-171`.

## belief update

state inference از observation و prior، `Q(s_t | o_≤t)` را تقریب می‌زند. این belief یک توزیع احتمال مهندسی است، نه «باور آگاهانه». `[DOCUMENTED] SCALE-AND-ACTIVE-INFERENCE.md:164-171`.

## Expected Free Energy

برای policy آینده، EFE دو خانوادهٔ مهم دارد:

- **risk/pragmatic value:** فاصلهٔ outcome پیش‌بینی‌شده با preference `C`.
- **ambiguity:** عدم‌قطعیت observation تحت state، مانند entropy ستون‌های `A`.
- **information gain/epistemic value:** policyهایی که uncertainty دربارهٔ state/model را کاهش می‌دهند؛ در decompositionهای دیگر EFE به‌صورت risk منهای information gain دیده می‌شود.

سند محلی برای یک گام می‌نویسد:

```text
G[u] = ambiguity + KL(predicted outcomes || preferences)
q(policy) = softmax(precision * -G + log E)
```

`[DOCUMENTED] SCALE-AND-ACTIVE-INFERENCE.md:173-206`.

### استعارهٔ «نقشه‌کش احتمالات»

A) **Vibe Coding:** عامل چند نقشه از جهان دارد، با حس تازه وزن نقشه‌ها را عوض می‌کند و راهی را ترجیح می‌دهد که هم امن باشد و هم ابهام را کم کند.  
B) **ترجمهٔ مهندسی:** Bayesian/variational state inference و policy selection با EFE.  
C) **محدودیت:** distribution و optimization تجربه، قصد یا آگاهی نیستند؛ ماتریس‌ها فقط محاسبات‌اند.

## معماری پیشنهادی، نه فعال

```text
sensor values
   -> discretized observations
   -> infer_states(A,D)
   -> infer_policies(B,C,E)
   -> deterministic safety arbiter
   -> PROPOSE_ONLY action
   -> optional language rendering
```

`[DOCUMENTED] SCALE-AND-ACTIVE-INFERENCE.md:208-234`.

## وضعیت واقعی پروژه

- package `pymdp` روی برد present نیست. `[BLOCKED_DEPENDENCY] import-spec snapshot`.
- هیچ فایل pymdp در `/opt/octopus` وجود ندارد. `[RUNTIME-VERIFIED] recursive filename search`.
- هیچ live `infer_states`/`infer_policies` در source organism یا OFN-L4 نیست؛ occurrences فقط سند هستند. `[IMPLEMENTED_DISCONNECTED] code search`.
- OFN-L4 daemon/policy loop ندارد. `[LOCAL-SCAFFOLD] /opt/octopus/ofn-l4 inventory`.
- arbiter deterministic pure وجود دارد و actهای خطرناک را owner-only/forbidden می‌کند، اما هیچ scheduler آن را صدا نمی‌زند. `[LOCAL-CODE] /opt/octopus/ofn-l4/ofnl4/arbiter.py:5-54`.

پس status برابر `DOCUMENT_ONLY` برای Active Inference و `BLOCKED_DEPENDENCY` برای اجرای pymdp است.

## Δθ چیست؟

`delta_theta()` چهار feature مهندسی را clamp و وزن می‌کند:

```text
0.35 * belief_change
+ 0.35 * homeostatic_error
+ 0.15 * action_relevance
+ 0.15 * memory_retention
```

اگر مقدار از 0.45 بیشتر باشد، flag `cognitive` true می‌شود. comment صریح می‌گوید inner time تجربه نیست و token/FLOP زمان درونی نیست. `[LOCAL-CODE] /opt/octopus/ofn-l4/ofnl4/theta.py:7-33`.

این تابع:

- pure و locally implemented است؛
- test اختصاصی ندارد؛
- writer `theta_ticks` ندارد؛
- scheduler ندارد؛
- به belief واقعی pymdp وصل نیست.

بنابراین `Engineering Delta Theta = IMPLEMENTED_DISCONNECTED`.

### استعارهٔ «ساعت درونی»

A) **Vibe Coding:** وقتی تغییر مهم‌تر است، ساعت مفهومی سریع‌تر تیک می‌زند.  
B) **ترجمهٔ مهندسی:** scalar salience/priority gate برای تصمیم‌گیری دربارهٔ اجرای cognition.  
C) **محدودیت:** Δθ زمان ذهنی یا نشانهٔ consciousness نیست؛ فقط metric انتخابی با وزن‌های قراردادی است.

## مرز با WBE و LLM

- WBE exponent نباید precision، threshold یا tick rate Active Inference شود.
- LLM می‌تواند evidence زبانی تولید کند، اما نباید belief state یا action authority را بدون arbiter بنویسد.
- KV cache vLLM هیچ‌یک از `A,B,C,D,E` یا episodic memory نیست.

`[DOCUMENTED] theta.py:7-10؛ SCALE-AND-ACTIVE-INFERENCE.md:218,318-334`.

معیار بلوغ بعدی: model کوچک discrete، observation contract، unit tests normalization/shape، EFE decomposition tests، shadow policy receipts، arbiter integration و owner-approved rollout. تا آن زمان هیچ claim دربارهٔ Active Inference زنده یا آگاهی مجاز نیست.

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
