---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, architecture, memory, control-plane, agi-roadmap]
created: 2026-07-28
updated: 2026-07-28
created_by: agent
sources:
  - "[[ARCHITECTURE-LAYERS-2026-07-27]]"
  - "[[OCTOPUS-COMPONENT-REGISTRY]]"
---

# گزارش بازطراحی و پیاده‌سازی — Octopus 2030 Control Plane

## حکم اجرایی

بازنویسی مخرب انجام نشد؛ هستهٔ زندهٔ `_ops/` حفظ و معماری به‌صورت additive ارتقا یافت.
علت: شواهد vault نشان می‌دهد safety/governance بالغ‌تر از learning است و rewrite کامل
بیشترین دارایی سیستم را نابود می‌کند. تغییرات این نشست، چهار مرز کمبود را می‌بندد:

1. **plan ≠ permission ≠ act** به قرارداد ماشین‌خوان و hash-bound تبدیل شد.
2. مأموریت‌ها `trace_id/task_id/tenant_id/project_id/scope/policy_version` گرفتند.
3. حافظهٔ SQLite از store عمومی به canonical scoped store ارتقا یافت.
4. handoff ایجنت‌ها از chat/history dump به Context Bundle باریک و phase-based تبدیل شد.

## تحقیق: جهت معتبر ۲۰۲۷–۲۰۳۰

پیش‌بینی AGI قطعی نیست. الگوی قابل دفاع‌تر، «سیستم مرکب» است نه یک مدل یگانه:
مدل/مدل‌ها + retrieval + حافظه + ابزار + verifier + policy gateway + sandbox + انسان.

### یافته‌های قابل اتکا

| جهت | شاهد بیرونی | نتیجه برای اختاپوس |
|---|---|---|
| Compound AI Systems | BAIR: نتایج برتر increasingly از چند component، retrieval، sampling و verifier می‌آیند | `_ops` باید control plane باشد، نه ادعای یک مغز همه‌چیزدان |
| Simple composable agent patterns | Anthropic: workflow، routing، parallelization، orchestrator-workers و evaluator-optimizer | الگوی فعلی درست است؛ باید contract و eval آن کامل شود |
| Open-ended empirical self-improvement | DGM v3: archive + mutation + benchmark؛ SWE-bench 20→50 با sandbox و oversight | Doctor/self_patch باید lineage و measured lift واقعی بگیرد؛ نه auto-merge |
| Procedural memory | Agent Workflow Memory: workflowهای قابل‌بازیابی موفقیت را بالا و steps را کم کردند | log باید به playbook/workflow approved تبدیل شود |
| Test-time learning/compute | TTT: state در test-time با update rule تغییر می‌کند؛ long-context بالقوه بهتر | برای اختاپوس اول shadow decision و replay، نه تغییر وزن/رفتار زنده |
| Efficient local models | Mamba/SSM، sparse MoE و مدل‌های کم‌هزینه | model_router باید task/risk/uncertainty-driven و local/frontier hybrid بماند |
| MCP + A2A | MCP برای tool/context؛ A2A برای delegation بین agentهای مستقل | هر دو فقط پشت capability/policy gateway؛ protocol به‌تنهایی security نیست |

### اصلاح ادعاهای تحقیق ورودی

- «خودآگاهی» اثبات نشده؛ هدف عملی **self-model قابل‌تصحیح و calibrated** است.
- Vector DB منبع حقیقت نیست؛ SQLite/event ledger canonical و index برداری derived است.
- shared memory آزاد خطرناک است؛ اشتراک فقط از Verified Memory Gateway.
- swarm زودهنگام ارزش ندارد؛ specialist فقط وقتی یک bottleneck واقعی اثبات شده اضافه شود.
- افزایش beat/call/log سرعت self-build نیست. سرعت = کاهش زمان defect→verified patch→owner verdict.

## معماری target

```text
Telegram / API / Voice
        |
Identity + Consent + Policy
        |
Thin Orchestrator / Mission Graph
        |
Typed Context Bundle (tenant/project/task/phase scoped)
   |          |            |
Research    Coding       Operations       <- specialists, private scratchpads
   |          |            |
Evidence + ActionProposal + MemoryProposal
        |
Evaluator / Verifier / Sandbox
        |
ApprovalDecision (exact action hash, expiry, human authority)
        |
Single Execution Gateway / EffectorGate
        |
Real-world effect
        |
Outcome + Decision Receipt + Event Spine
        |
SQLite canonical memory -> derived FTS/vector index -> workflow archive
```

## کد پیاده‌شده

### ۱. Typed control protocol

فایل نو: `_ops/control_contracts.py`

- `ActionSpec`: action دقیق، target، operation، args، reversibility، sandbox.
- `ActionProposal`: mission/task/trace/tenant/project/agent + risk/confidence/evidence.
- `ApprovalDecision`: reviewer، expiry و `action_sha256`.
- `authorization()`: fail-closed؛ sensitive/high/critical/low-confidence بدون انسان رد.
- ضد TOCTOU: تصمیم فقط روی همان hash دقیق معتبر است؛ تغییر target/args مجوز را باطل می‌کند.
- هیچ executor/network/write زنده داخل این ماژول نیست.

### ۲. Context discipline

فایل نو: `_ops/context_bundle.py`

- bundle مخصوص task/role/phase با TTL.
- فقط objective، constraints، verified facts، refs، tool allowlist و output contract.
- هیچ field برای chain-of-thought/private scratchpad وجود ندارد.
- `personal_core` برای specialist عادی رد می‌شود.
- `_ops/telegram_center/mission_runner.py` در هر run یک
  `context-bundle.json` کنار evidence می‌نویسد؛ runner هنوز فقط allowlist و worktree است.

### ۳. Mission envelope v2-compatible

فایل‌های ارتقایافته:

- `_ops/mission_contract.py`
- `_ops/telegram_center/mission.py`

افزوده شد:

```text
tenant_id · project_id · task_id · scope · trace_id
schema_version · policy_version · critical risk
```

سازگاری حفظ شد: REQUIRED_FIELDS قدیمی شکسته نشد و فیلدهای نو additive هستند.

### ۴. Scoped canonical memory

فایل‌های ارتقایافته:

- `_ops/memory/memory_store.py` → schema v3
- `_ops/memory/gate.py`

metadata افزوده‌شده:

```text
tenant_id · project_id · scope · agent_id · task_id
classification · policy_version
```

zoneها:

```text
scratchpad · session · project · verified_shared · personal_core
```

قواعد:

- query scoped مستقیماً در SQLite canonical فیلتر می‌شود؛ tenant پرنویز نمی‌تواند
  candidate window پروژهٔ دیگر را حذف کند.
- dedupe در `(namespace,mkey,tenant,project,scope)` انجام می‌شود.
- `verified_shared` و `personal_core` از agent/model فقط proposal می‌شوند.
- schema migration additive است؛ رکوردهای قدیمی default metadata می‌گیرند.
- FTS همچنان derived recall index است، نه authority.

### ۵. تست‌ها

فایل نو: `_ops/tests/test_control_contracts_v2.py`

پوشش:

1. exact proposal↔decision hash binding و رد TOCTOU.
2. رد authorization غیرانسانی برای action حساس.
3. Context Bundle scoped و بدون reasoning channel.
4. isolation حافظه بین پروژه‌ها و owner-only verified-shared promotion.

در `_ops/tests/run_all.py` ثبت شد.

## وضعیت صداقت آزمون

- **[IMPLEMENTED]** فایل‌ها نوشته و integration points و suite registry به‌روز شدند.
- **[STATICALLY REVIEWED]** کد دوباره از دیسک خوانده و قراردادها بررسی شدند.
- **[NOT RUNTIME VERIFIED]** این نشست shell/runner نداشت؛ هیچ ادعای pass-count ساخته نمی‌شود.
- ایجنت بعدی باید ابتدا تست تکی را اجرا کند؛ `run_all` فقط وقتی live organism پایین است.

## شکاف‌های باقی‌مانده، به ترتیب

### P0 — Verification

1. اجرای `test_control_contracts_v2.py`, `test_memory_gate.py`,
   `test_tg_mission.py`, `test_tg_mission_runner.py`.
2. migration smoke روی یک copy از memory.db؛ count/hash قبل و بعد باید ثابت بماند.
3. اثبات artifact واقعی `context-bundle.json` در یک mission dry/isolated.

### P1 — Single execution gateway

`control_contracts.authorization()` را در یک مسیر کوچک و واقعی وصل کن:
ابتدا `code.apply` یا external message در **shadow**. هیچ bypass موازی باقی نماند.
ExecutionResult جدا ثبت شود؛ ApprovalDecision هرگز به معنی executed نباشد.

### P2 — Memory read policy

- `get_scoped()` یا الزام Context Bundle در consumerهای جدید.
- consumer قدیمی unscoped فقط compatibility؛ برای wiring نو ممنوع.
- promotion receipt برای verified_shared به approval store وصل شود.
- conflict/dedup/consolidation شبانه فقط proposal/retraction، نه حذف فیزیکی.

### P3 — Procedural workflow memory

از fixهای accepted یک `WorkflowRecord` بساز:
trigger، prerequisites، steps، tools، tests، failure modes، outcome، lineage.
فقط workflowهای owner-approved یا deterministic وارد procedural شوند.

### P4 — DGM-lite self-build

```text
defect → variants → isolated test → held-out eval → measured_lift
→ tournament/archive lineage → owner card → approved merge
```

Auto-merge ممنوع بماند. معیار سرعت:
`defect_to_verified_patch_s`, `frontier_calls_per_accepted_fix`,
`repeat_defect_rate`, `regression_rate`, `workflow_reuse_rate`.

### P5 — Protocol adapters

- MCP adapter: فقط tools allowlisted از Context Bundle و capability registry.
- A2A adapter: فقط Context Bundle/Result contract، نه chat/history/raw memory.
- هر دو پشت policy، auth، rate limit، timeout، audit و cancellation.

## فایل‌های لمس‌شده

```text
_ops/control_contracts.py                         NEW
_ops/context_bundle.py                            NEW
_ops/tests/test_control_contracts_v2.py           NEW
_ops/mission_contract.py                          UPDATED
_ops/memory/memory_store.py                       UPDATED
_ops/memory/gate.py                               UPDATED
_ops/telegram_center/mission.py                    UPDATED
_ops/telegram_center/mission_runner.py             UPDATED
_ops/tests/run_all.py                              UPDATED
```

## منابع بیرونی

- BAIR — The Shift from Models to Compound AI Systems:
  https://bair.berkeley.edu/blog/2024/02/18/compound-ai-systems/
- Anthropic — Building Effective Agents:
  https://www.anthropic.com/research/building-effective-agents
- Darwin Gödel Machine v3:
  https://arxiv.org/abs/2505.22954
- Agent Workflow Memory:
  https://arxiv.org/abs/2409.07429
- Test-Time Training:
  https://arxiv.org/abs/2407.04620
- Mamba:
  https://arxiv.org/abs/2312.00752
- Mixtral of Experts:
  https://arxiv.org/abs/2401.04088
- Google Agent2Agent announcement:
  https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/

## فرمان به ایجنت بعدی

اول verify کن، بعد فقط یک vertical slice را ببند:

> `mission → context bundle → proposal → exact approval → sandbox execution →
> result/outcome receipt → scoped workflow memory`

قابلیت تازهٔ موازی نساز. اگر خروجی consumer ندارد، نساز. اگر falsifier ندارد، ادعا نکن.
