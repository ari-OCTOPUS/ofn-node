# Runtime در برابر Concept: توالی heartbeat واقعی

## sequence diagram

```text
heartbeat thread
  -> effective_measurement()
       -> procfs/sysfs/statvfs
       -> optional lab synthetic override
  -> LocalCortex.available()
  -> maybe_stable() + transition()
       -> identity health_transition if changed
  -> beat()
       -> identity_ledger append
       -> identity_heartbeat append
  -> enrich_snapshot()
       -> tools/world/season/growth
       -> recall recent episodes
       -> school/development/teacher
       -> self model
  -> life_cycle.tick()
       -> optional teacher learning
       -> inner speech
       -> school/maturity/rhythm
       -> world host persistence
       -> self-model persistence
       -> attention/growth
       -> EventKernel events
       -> optional deterministic utterance
       -> vault + attestation + LIFE.json
  -> write_public_status()
  -> heartbeat event commit
  -> outbox replay
  -> wait(heartbeat_interval_s = 210)
```

`[LOCAL-CODE] /opt/octopus/lab/ofn/organism/runtime/app.py:558-609؛ runtime/life_cycle.py:211-410`.

## stage-by-stage contract

### 1. Measure body

- file/function: `homeostasis/core.py::measure`
- input: procfs، PSI، sysfs thermal، root statvfs
- output: measured signals، alerts، proposed health
- state read: kernel/OS فقط
- state write: ندارد
- event: ندارد
- failure: signal به `UNKNOWN` تبدیل می‌شود؛ چهار unknown alert می‌دهد
- runtime evidence: public `STABLE` و soak envelope سالم

`[LOCAL-CODE] homeostasis/core.py:17-100`.

### 2. Apply optional lab override

- file/function: `runtime/app.py::effective_measurement`
- input: measurement + meta keys synthetic health/reason
- output: measurement ممکن است DEGRADED/SAFE_HALT شود
- state read: SQLite meta
- state write/event: ندارد
- failure/risk: test override اگر فراموش شود health را تغییر می‌دهد

`[LOCAL-CODE] runtime/app.py:134-144`.

### 3. Check cortex

- file/function: `cognition/backend.py::LocalCortex.available`
- input: local loopback health
- output: boolean
- state read: local service
- state write: ندارد
- event: در این stage ندارد
- failure: cortex down باعث DEGRADED می‌شود، نه identity loss
- runtime evidence: service active و public AVAILABLE

`[LOCAL-CODE] cognition/backend.py:50-76؛ runtime/app.py:560-577`.

### 4. Stabilize and transition health

- file/function: `maybe_stable` + `apply_health_state`
- input: measured health، alerts، consecutive count
- output: current state
- state read/write: SQLite meta `consecutive_stable_body`؛ process STATE
- event/write: identity `health_transition` فقط در تغییر
- failure: ledger error به alerts افزوده می‌شود

`[LOCAL-CODE] runtime/app.py:87-102,147-167,558-573`.

### 5. Identity heartbeat

- file/function: `identity/heartbeat.py::beat`
- input: boot، age، health، event sequence، cortex، unknowns
- output: chain status + body
- state read/write: identity_ledger و identity_heartbeat
- event: `identity_heartbeat` در ledger
- failure: chain write error report و verify می‌شود
- runtime evidence: chain valid، 195 ledger rows

`[LOCAL-CODE] identity/heartbeat.py:14-65`.

### 6. Enrich snapshot

- file/function: `life_cycle.py::enrich_snapshot`
- input: status + measured + LAN
- output: sensors، place، world، growth، recent memories، futures، school، teacher، self model
- state read: episodes، world_hosts، meta، lessons/futures/topics
- state write: seed/apply futures ممکن است DB بنویسد
- event: ندارد
- failure: retrieval gap metric ندارد

`[LOCAL-CODE] runtime/life_cycle.py:57-126`.

### 7. Tick cognition/growth

- file/function: `life_cycle.py::tick`
- input: enriched snapshot
- output: learned/inner/school/mature/world/self/growth/attention/utterance
- state reads: DB و local files
- state writes: learned_topics، inner_speech، world_hosts، self_models، utterances، meta، state JSON، vault، attestation
- events: world، self_model، utterance، inner، attention، growth
- failure: optional teacher می‌تواند fail و no-op شود؛ deterministic cycle ادامه دارد

`[LOCAL-CODE] runtime/life_cycle.py:211-410`.

### 8. Public state and heartbeat event

- file/function: `write_public_status`، `make_event("heartbeat")`، `kernel.accept`، `replay_pending`
- input: final snapshot/health alerts
- output: public JSON + committed event/episode projection
- state writes: file، events، outbox، episodes
- failure: queue saturation با outbox recover؛ file atomic replace
- runtime evidence: events/episodes/outbox هرکدام 319 و outbox pending صفر

`[LOCAL-CODE] runtime/app.py:591-609؛ runtime/public_status.py:58-129؛ event_kernel/kernel.py:37-104`.

## چرا 210 ثانیه؟

start wrapper nominal interval 180 می‌دهد، اما DB meta اکنون 210 است. رشد/parent policy می‌گوید بعد از stage مناسب rhythm از نزدیک‌تر به 210 کند می‌شود و test دقیق آن را assert می‌کند. `[LOCAL-CODE] start-organism.sh:41-46؛ growth/parent.py:194-204؛ tests/test_life.py:141-147؛ SQLite meta.heartbeat_interval_s=210`.

210:

- WBE exponent نیست.
- LLM output نیست.
- thermal threshold نیست.
- تصمیم deterministic growth/rhythm و persistent meta است.

## deterministic، LLM-dependent و optional

- **deterministic:** measurement، transition، identity hash، EventKernel، outbox، DB، school checks، growth rules، arbiter limits.
- **LLM-dependent:** پاسخ free-form local Qwen و teacher summary.
- **optional/fail-soft:** teacher learning، utterance در نبود change، external learning، Telegram.
- **side-effectful observer:** soak و LAN watcher.

## چرا school/growth دست را باز نمی‌کند؟

autonomy در snapshot و identity heartbeat hard-coded `PROPOSE_ONLY` است. curriculum limits آن را pass criterion می‌گیرد؛ parent صریحاً می‌گوید maturity mind را graduate می‌کند، نه hands. هیچ transition به ARMED در source وجود ندارد. `[LOCAL-CODE] runtime/app.py:195-215؛ identity/heartbeat.py:14-28؛ school/curriculum.py:71-76؛ growth/parent.py:194-204`.

### استعارهٔ «ضربان عملیاتی»

A) **Vibe Coding:** هر ۲۱۰ ثانیه بدن سنجیده، دفتر هویت امضا و شهر به‌روز می‌شود.  
B) **ترجمهٔ مهندسی:** periodic thread با measurement، DB writes، event dispatch و state export.  
C) **محدودیت:** timer و loop نشانهٔ قلب زیستی یا consciousness نیستند.

## Runtime/Concept verdict

- heartbeat v1: `LIVE`
- mandatory retrieval: `LIVE_WITH_GAP`
- school-to-autonomy unlock: `NOT_IMPLEMENTED` و عمداً ممنوع
- Active Inference policy heartbeat: `DOCUMENT_ONLY`
- OFN-L4 loop: `SCAFFOLD`
- vLLM scheduler heartbeat: `BLOCKED_NO_GPU`

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
