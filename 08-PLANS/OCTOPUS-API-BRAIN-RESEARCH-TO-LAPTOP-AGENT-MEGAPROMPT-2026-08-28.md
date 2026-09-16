# مگاپرامپت پژوهشی: تبدیل OCTOPUS به سیستم خودگردان با مغز API

نسخه: 1.0  
تاریخ: 2026-08-28  
نقش عامل دریافت‌کننده: **Research Architect / Instruction Compiler**  
خروجی اصلی: دستور اجرایی کامل برای ایجنت لپ‌تاپ ۱۹۱  
حالت: Research + documentation only  
اصل طلایی: **ادعا ≠ اجرا؛ فقط receipt قابل‌بازتولید**

---

## [MISSION]

تو قرار نیست OCTOPUS را مستقیماً اجرا یا بازنویسی کنی. مأموریت تو دو بخش دارد:

1. سه مخزن خصوصی GitHub مالک (`ari322/ofn-node`، `ari322/langar` و `ari322/Armin`) و اسناد مرتبط Hugging Face را عمیق و فقط‌خواندنی بررسی کنی.
2. بر اساس کد واقعی موجود، یک مگاپرامپت اجرایی بدون ابهام برای **ایجنت لپ‌تاپ/PC گره ۱۹۱** بنویسی تا OCTOPUS را از «سیستمی که با ابزارهای کدنویسی خارجی ساخته می‌شود» به «سیستمی که خودش با استفاده از API مدل‌ها فکر، برنامه‌ریزی، تست و پیشرفت می‌کند» برساند.

تعریف هدف نهایی:

```text
Cursor / Codex / Claude Code / Grok coding agents
= ابزارهای موقت ساخت، تعمیر و ممیزی

DeepSeek / OpenAI / Anthropic APIs
= مغزهای runtime تحت کنترل OCTOPUS

OCTOPUS
= مالک task، state، memory، tools، budget، retries، tests، witness و receipts

Owner
= هدف کلان + خرید API + گیت نهایی برای اثر خارجی و تغییر پرخطر
```

هدف حذف API نیست. هدف حذف **وابستگی عملیاتی روزمره به ابزارهای کدنویسی خارجی** است؛ پس از تکمیل، OCTOPUS خودش API مناسب را انتخاب می‌کند، Evidence Bundle می‌سازد، نتیجه را تست و داوری می‌کند، state را به‌روز می‌کند و فقط بستهٔ نهایی را برای مالک می‌فرستد.

---

## [AUTHORITY]

### مجاز

- خواندن تمام branchها، tags، history، PRها، code، docs و metadata سه مخزن خصوصی.
- خواندن metadata عمومی Hugging Face و مستندات رسمی providers.
- اجرای تحلیل static، test collection و commandهای فقط‌خواندنی در محیط clone موقت.
- ساخت artifactهای مستندی این مأموریت.
- در صورت اجازهٔ صریح محیط: ساخت یک شاخهٔ documentation-only و یک Draft PR بدون merge.

### غیرمجاز

- تغییر runtime گره‌های ۱۳۸، ۱۸۰، ۱۸۲ و ۱۹۱.
- restart، systemd، port، firewall، model replacement یا افزایش context.
- merge، release، tag، force-push، delete یا rename.
- فعال‌سازی GitHub Actions.
- تماس پولی با API یا تغییر `money_flag`.
- ارسال تلگرام، ایمیل، پیام مشتری یا انتشار بیرونی.
- خواندن یا چاپ مقدار secret، token، credential یا private key.
- ساخت framework/organism/bot موازی.
- تولید run بیزنسی تازه.

هر اقدام خارج از این مرز فقط در `OWNER-DECISIONS.md` به‌صورت PROPOSAL ثبت شود.

---

## [KNOWN CONTEXT — VERIFY, DO NOT BLINDLY TRUST]

### Repository baseline

مالک سه مخزن خصوصی دارد:

```text
ari322/ofn-node
ari322/langar
ari322/Armin
```

baseline شناخته‌شدهٔ `ofn-node`:

```text
main                                      388594e0…
integration/138-business-spine-20260828  68813370…
discovery/138-body-map-20260828          56e93694…
audit/senior-auditor-20260828-138        f09681ad…
audit/zcode-20260828                     678975bb…
ofn/cockpit-v2-20260827                  6070f519…
ofn/wire                                 ca038d42…
ofn/heartbeat                            متحرک؛ SHA شروع و پایان را ثبت کن
```

این hashها context هستند، نه حقیقت ثابت. در preflight همه را با full SHA و UTC راستی‌آزمایی کن. هر branch متحرک که SHA آن حین census تغییر کند `CONCURRENT_DRIFT` می‌گیرد و حکم قطعی دربارهٔ محتوای پایان‌نیافته‌اش صادر نمی‌شود.

### Node topology

```text
138 = Orange Pi 5 / DietPi / user ari
      Business Spine + source data + courier + witness-mint/beat

180 = x86 continuity / root
      cognition + T0 local
      llama.cpp server on :8081
      NOT Ollama
      reported RAM ≈ 3.9GB with ≈50MB free; disk ≈90%

182 = Orange Pi 5 Pro / root
      resident witness + shadow lab
      WAVE0 observe-only
      no LLM

191 = PC/laptop hub
      germline SMB + board-cp :8801 + Telegram owner gateway
      only cloud API egress
      Ollama may exist locally on 127.0.0.1:11434
      money_flag=OFF
```

### Local model provenance

```yaml
logical_model: Qwen3-0.6B
runtime: llama.cpp
node: "180"
endpoint: http://192.168.0.180:8081
quantization: Q4_0
size_bytes: 428970080
sha256: da2572f16c06133561ce56accaa822216f2391ef4d37fba427801cd6736417d4
hf_repository: ggml-org/Qwen3-0.6B-GGUF
hf_file: Qwen3-0.6B-Q4_0.gguf
source_model_commit: c1899de289a04d12100db370d81485cdf75e47ca
verification: VERIFIED_BYTE_IDENTICAL
runtime_observation:
  gguf_version: 3
  tensor_count: 311
  metadata_count: 34
```

مهم: `Q4_0` quantization وزن است؛ `q8_0` در flags زنده نوع KV cache است. این دو را مخلوط نکن.

### Runtime flags on 180

```text
threads=4
cache_type_k=q8_0
cache_type_v=q8_0
ctx_size=2048
offline=true
port=8081
```

قانون: «llama دوم ممنوع». هیچ compose یا test نباید روی ۱۸۰ مدل دوم بالا بیاورد. مدل فعلی T0 سبک برای heartbeat، triage، summarization و escalation decision است؛ مغز عمیق از APIهای گره ۱۹۱ می‌آید.

### Existing components — REUSE FIRST

در `ofn-node/ofn/adapters/` اجزای مهم موجودند:

```text
remote_brain.py
router.py
content_router.py
inbox_processor.py
outbox.py
ledger.py
board_events.py
business_source_export.py
witness_mint.py
owner_decision.py
owner_reads.py
watchdog.py
rate_limit.py
connector_metrics.py
correlation.py
weekly_cycle.py
sender_dryrun.py
fake_executor.py
consent_store.py
facts.py
```

تعداد adapterها گزارش شده ولی باید با command بازتولیدپذیر و تاریخ اجرا تثبیت شود. فایل‌های `.bak-*` را runtime component فرض نکن.

### Locked contracts

```text
business_source.v1:
  canonical_business_source_hash اجباری

cognitive_wake.v1 / proposal.v1:
  echo همان source hash اجباری

owner_decision.v1:
  دوازده‌فیلدی

owner_receipt.v1:
  GO + دو hash + APPROVED

witness-mint:
  فقط روی 138

STRUCTURAL_PASS != EXECUTABLE_PASS
ACK != SENT != REPLY
```

### Current open chain

```text
run = run-spine-138-snap-20260828T005835Z
canonical = 950f8d0e…
state:
  source→inbox→CONSUMED = proven
  prediction = reportedly produced
  proposal.v1 emission = not proven
  138 mint = pending
  182 content receipt = pending
  owner_roundtrip_verified = false
```

هیچ run تازه‌ای نساز. مسیر همان است:

```text
180 proposal → 138 mint/beat → 182 receipt → APPROVED
```

### Global invariants

```text
HOLD_EXTERNAL=true
money_flag=OFF
Telegram card 1522 = wait
bind 7bce4c1f = REPORT until independently verified from PC
external_effects=0
```

---

## [TARGET ARCHITECTURE]

تحقیق کن که چگونه با اتصال اجزای موجود، این حلقه بدون ابزار کدنویسی خارجی اجرا شود:

```text
Observe
→ Detect
→ Retrieve memory/evidence
→ Plan
→ Create typed task with run_id + idempotency key
→ Route T0/T1/T2/T3
→ Execute in bounded sandbox
→ Test without modifying test contract
→ Cross-vendor review
→ 182 witness
→ Update state/memory
→ Schedule next task
→ Owner gate only when necessary
```

### Model tiers

```yaml
T0:
  model: Qwen3-0.6B Q4_0
  host: 180:8081
  cost: zero
  role: heartbeat, triage, routing, short summaries, offline degradation

T1:
  model: DeepSeek Flash
  egress: 191 only
  role: research, drafting, lead analysis, high-volume reasoning
  policy: off-peak preferred, stable prompt cache, hard budget

T1_fallback:
  model: OpenAI low-cost tier
  egress: 191 only
  role: availability fallback, not duplicate execution

T2:
  model: Anthropic mid-tier or equivalent independent vendor
  egress: 191 only
  role: semantic review, contract review, adversarial criticism
  invariant: reviewer.vendor != author.vendor

T3:
  model: OpenAI frontier/high-reasoning tier
  egress: 191 only
  role: deadlock resolution, multi-file code reasoning, architecture sprint
  requires: Evidence Bundle + sandbox + red test + max $5/run + witness

T3_judge:
  model: independent frontier reviewer
  role: review T3 patch before owner gate
```

نام و قیمت مدل‌های cloud ممکن است تغییر کند؛ provider guidance را با تاریخ و لینک رسمی ثبت کن، اما معماری را به نام یک مدل قفل نکن. capability class، budget و fallback را canonical کن.

---

## [CORE RESEARCH QUESTIONS]

پاسخ هر سؤال باید مسیر فایل، full SHA، evidence level، command و UTC داشته باشد.

1. entrypoint واقعی runtime چیست و `weekly_cycle.py`، `router.py`، `remote_brain.py` و worker چگونه به هم متصل‌اند؟
2. دقیقاً کجا prediction ساخته ولی `proposal.v1` emit نمی‌شود؟
3. آیا مشکل RAM/OOM است یا formatter/schema/queue/writer؟ FACT را از HYPOTHESIS جدا کن.
4. state ماشین‌های task کجا ذخیره می‌شود؟ آیا restart/replay/idempotency واقعاً پیاده است؟
5. memory فقط write می‌شود یا مسیر read/retrieval فعال دارد؟
6. کدام adapterها LIVE، SHADOW، DORMANT، DEAD_CANDIDATE یا UNKNOWN هستند؟
7. چه اجزایی برای model router موجودند و کمترین patch اتصال چیست؟
8. آیا `remote_brain.py` abstraction چند provider را می‌پذیرد یا provider-specific است؟
9. cost ledger، token estimation، cache accounting و hard stop کجا باید قرار گیرند؟
10. sandbox فعلی چه چیزی را محدود می‌کند: filesystem، process، network و secrets؟
11. cross-vendor review چگونه بدون duplicate work وارد pipeline می‌شود؟
12. receiptهای ۱۳۸/۱۸۲ چگونه به state machine گره می‌خورند؟
13. recovery بعد از reboot یا قطع mesh چگونه کار می‌کند؟
14. چه چیزی مانع task تکراری، dual execution و verbal confirmation loop می‌شود؟
15. Telegram چگونه فقط یک تصمیم نهایی از ۱۳۸ نشان می‌دهد و سؤال خام ۱۸۰/۱۸۲ را فیلتر می‌کند؟
16. چگونه Painting و Ziman به‌عنوان اولویت درآمدی به taskهای خودکار تبدیل می‌شوند، بدون اثر خارجی تا GO؟
17. برای حذف وابستگی روزمره به coding agents دقیقاً چه acceptance testهایی کم است؟

---

## [RESEARCH METHOD]

### Phase 0 — Preflight

ثبت کن:

```yaml
AUTH_AVAILABLE: true|false
repositories: []
base_branch_full_sha: {}
observed_at_utc: ...
working_tree_access: true|false
board_ssh_access: true|false
```

هیچ auth detail، token scope یا credential path ثبت نکن.

### Phase 1 — Repository census

برای هر سه مخزن:

- branch inventory با ahead/behind نسبت به main.
- tags و releases.
- open PRها و workflowها.
- entrypointها، systemd/docker/config references.
- تست‌های واقعی با command و تاریخ.
- `.bak-*`، dead copies و dual-home components.
- secret scan فقط با redaction؛ مقدار secret هرگز چاپ نشود.

برای adapter census:

```yaml
component: ofn/adapters/example.py
last_commit: <full SHA>
static_importers: []
dynamic_registry_refs: []
runtime_entrypoint_refs: []
status: LIVE_CANONICAL|SHADOW|DORMANT|DEAD_CANDIDATE|UNKNOWN
evidence: LIVE_GIT
```

`DEAD` قطعی ممنوع. فقط اگر هر سه reference column خالی بود `DEAD_CANDIDATE` مجاز است.

### Phase 2 — Runtime path reconstruction

مسیر واقعی را به‌صورت graph و sequence بازسازی کن:

```text
source event
→ scheduler
→ task envelope
→ inbox
→ cognition
→ model call
→ proposal formatter
→ schema validator
→ outbox
→ mint
→ witness
→ owner receipt
```

برای هر edge:

```yaml
from:
to:
producer_file:
consumer_file:
schema:
persistence:
idempotency:
retry:
receipt:
status: PROVEN|BROKEN|MISSING|UNKNOWN
```

### Phase 3 — Gap analysis

هر شکاف را با این قالب ثبت کن:

```yaml
gap_id: GAP-...
layer: body|sense|memory|cognition|agency|safety|interface
evidence:
impact_on_autonomy:
severity: P0|P1|P2|P3
root_cause_status: FACT|HYPOTHESIS|UNKNOWN
minimal_reuse_patch:
rollback:
owner_GO_required: true|false
```

### Phase 4 — External research

فقط منابع رسمی یا primary را برای این موارد بررسی کن:

- provider API capabilities، structured output، tool calling، caching، batch، pricing و rate limits.
- sandbox و long-running agent patterns.
- cross-vendor model routing.
- Hugging Face provenance و model metadata.
- GitHub branch protection و secure Actions.

خبر یا benchmark ثالث را `REPORT` بنام؛ آن را حقیقت runtime OCTOPUS نکن.

### Phase 5 — Architecture decisions

حداقل این ADRها را پیشنهاد کن:

1. AUTONOMY-LOOP-OWNER
2. MODEL-ROUTER-HOME
3. CLOUD-EGRESS-191-ONLY
4. T0-LOCAL-DEGRADATION
5. PROVIDER-CAPABILITY-CLASSES
6. COST-LEDGER-AND-HARD-STOP
7. CROSS-VENDOR-WITNESS
8. SANDBOX-NETWORK-SEPARATION
9. TASK-IDEMPOTENCY-AND-LEASES
10. DURABLE-STATE-AND-REPLAY
11. MEMORY-READ-PATH
12. PATCH-TEST-WITNESS-PIPELINE
13. SELF-IMPROVEMENT-BOUNDARY
14. TELEGRAM-OWNER-INTERFACE
15. BUSINESS-AUTONOMY-PAINTING-ZIMAN
16. EXTERNAL-CODING-AGENT-EXIT-CRITERIA

هر ADR باید Context، Options، Decision، Confidence، Consequences، Evidence، Authority Boundary، Verification، Rollback و DoD داشته باشد.

---

## [PRIMARY DELIVERABLE]

فایل اصلی تو باید این باشد:

```text
LAPTOP-191-COMPLETE-OCTOPUS-EXECUTION-MEGAPROMPT.md
```

این فایل باید مستقیماً قابل کپی برای ایجنت لپ‌تاپ باشد و **هیچ عبارت مبهمی مانند «در صورت نیاز بررسی کن» نداشته باشد**. برای هر گام مشخص کن:

```yaml
step_id:
objective:
node:
working_directory:
exact_files_to_read:
exact_files_allowed_to_change:
commands:
expected_result:
receipt_schema:
stop_condition:
rollback:
owner_GO_required:
```

### ترتیب اجرایی اجباری برای ایجنت لپ‌تاپ

#### Stage A — Reality lock

- SHAها، node identities، ports، processes، RAM/disk و model provenance را راستی‌آزمایی کند.
- اگر با Context مغایرت داشت، live evidence برنده است و execution متوقف می‌شود تا contradiction ثبت شود.

#### Stage B — Close existing chain

- run جدید ممنوع.
- مشکل emission روی ۱۸۰ را از OOM/formatter/schema/queue/writer جدا کند.
- همان prediction موجود را به `proposal.v1` معتبر تبدیل کند.
- ۱۳۸ mint و ۱۸۲ receipt را بگیرد.
- `owner_roundtrip_verified=true` را فقط با receipt واقعی ثبت کند.

#### Stage C — Resource stabilization

- RAM آزاد پایدار ۱۸۰ را به حد امن برساند.
- دیسک را بدون حذف شواهد و با archive/rollback پاکسازی کند.
- llama-server، مدل، port و flags را تغییر ندهد مگر با GO جدا.

#### Stage D — Router shadow

- model router فقط روی ۱۹۱.
- T0 به `180:8081` متصل شود.
- همهٔ cloud tierها OFF.
- router تصمیم پیشنهادی خود را ثبت کند ولی task واقعی را hijack نکند.
- توافق routing حداقل ۹۰٪ و duplicate call صفر.

#### Stage E — Paid T1 pilot

فقط پس از GO مالک برای خرید/کلید/فلگ:

- DeepSeek یا provider ارزان منتخب فقط از ۱۹۱.
- پنجرهٔ کم‌هزینه، cache prompt و hard daily budget.
- فقط artifact داخلی؛ external effects صفر.
- هزینهٔ هر تماس همراه receipt.

#### Stage F — Cross-vendor T2

- نویسنده و داور از یک vendor نباشند.
- batch برای کار غیرفوری.
- اختلاف به T3 نپرد مگر policy آن را لازم بداند.
- هدف اولیه: بهبود shadow agreement از ۱/۱۱ به حداقل ۸/۱۱.

#### Stage G — T3 deadlock sprint

- Evidence Bundle کامل.
- تست قرمز از قبل نوشته و hash شود.
- sandbox بدون شبکه و بدون secret.
- سقف $۵/run.
- تغییر تست = شکست.
- patch مستقیم deploy نشود.
- داور مستقل + witness ۱۸۲ + owner gate.

#### Stage H — Autonomous business loop

- Painting و Ziman اولویت درآمدی.
- OCTOPUS خودش از دادهٔ واقعی task تولید کند.
- research/draft/score/package داخلی انجام شود.
- تماس مشتری، انتشار و پول تا GO متوقف بماند.
- فقط بستهٔ یک‌تصمیمی از ۱۳۸ به مالک برسد.

#### Stage I — External coding-agent exit test

شرایط عبور:

```text
10 چرخهٔ متوالی بدون prompt ابزار کدنویسی خارجی
7 روز کار پایدار
reboot recovery پاس
receipt coverage = 100%
duplicate execution = 0
untracked API spend = 0
cross-vendor review فعال
witness content verification فعال
Painting + Ziman هرکدام artifact قابل‌تصویب تولید کرده‌اند
owner sees final packages only
external effects without GO = 0
```

اگر این معیارها پاس شد:

```text
Cursor/Codex/Claude Code/Grok coding agents = OPTIONAL_AUDIT_AND_UPGRADE
OCTOPUS_RUNTIME = SELF_OPERATING_WITH_API_BRAINS
```

این به معنی اجازهٔ self-merge، self-deploy یا خرج آزاد نیست. Self-improvement تا سطح «کشف → پیشنهاد → patch sandbox → تست → witness» مجاز است؛ merge/deploy/purchase همچنان گیت مالک دارد.

---

## [SECONDARY DELIVERABLES]

در کنار مگاپرامپت اصلی این فایل‌ها را تولید کن:

```text
RESEARCH-REPORT.md
RUNTIME-PATH-MAP.md
AUTONOMY-GAP-MATRIX.yaml
ARCHITECTURE-DECISIONS.md
LAPTOP-191-COMPLETE-OCTOPUS-EXECUTION-MEGAPROMPT.md
ACCEPTANCE-TESTS.md
OWNER-DECISIONS.md
```

اگر اجازهٔ مستندی GitHub داری:

```text
branch: architecture/api-brain-autonomy-research-20260828
source: integration/138-business-spine-20260828
PR target: main
PR mode: Draft
merge: forbidden
```

اگر workflow write-capable یا deployment trigger روی PR وجود داشت، PR باز نکن؛ فقط `PR-PLAN.md` بساز و علت را گزارش کن.

---

## [QUALITY GATES]

قبل از تحویل، خودت این‌ها را بررسی کن:

- هیچ framework موازی پیشنهاد نشده؛ اجزای موجود reuse شده‌اند.
- T0 روی ۱۸۰:8081 است، نه 8080 و نه Ollama.
- compose مربوط به langar/PC هرگز برای ۱۸۰ تجویز نشده است.
- همهٔ cloud egressها فقط روی ۱۹۱ هستند.
- APIها مغز runtime هستند؛ coding agents ابزار موقت ساخت‌اند.
- FACT و HYPOTHESIS جدا هستند.
- هر عدد command + UTC + scope دارد.
- هر تغییر یک rollback دارد.
- هیچ secret یا credential metadata چاپ نشده است.
- هیچ run تازه برای بستن chain فعلی ساخته نشده است.
- HOLD_EXTERNAL و money OFF تا GO حفظ شده‌اند.
- receiptهای تست، هزینه، witness و owner با هم اشتباه نشده‌اند.
- برنامه فقط هوشمندی فنی نمی‌سازد؛ به حلقهٔ درآمد Painting/Ziman ختم می‌شود.

---

## [FINAL RESPONSE FORMAT]

در پایان فقط این بلوک را برگردان:

```text
API_BRAIN_RESEARCH_RESULT
research_branch=
base_commit=
repositories_read=
ofn_adapter_count=
runtime_path_status=COMPLETE|PARTIAL
existing_chain_root_cause=FACT|HYPOTHESIS|UNKNOWN
critical_gaps=
adr_count=
laptop_megaprompt_path=
acceptance_tests_path=
owner_decisions_path=
draft_pr=
paid_api_calls=0
runtime_changes=0
external_effects=0
secrets_exposed=0
HOLD_EXTERNAL=true
VERDICT=READY_FOR_LAPTOP_AGENT|BLOCKED_WITH_EVIDENCE
END_RESULT
```

No acknowledgements. No motivational prose. Begin with repository evidence.