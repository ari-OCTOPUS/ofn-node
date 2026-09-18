# OCTOPUS — research-to-code execution plan

Date: 2026-09-04
Document status: READY_FOR_LOCAL_IMPLEMENTATION
Implementation status: NOT_STARTED_BY_THIS_HANDOFF
Planning lane: E-ENGINEERING-ENTRYPOINT-20260904
Execution lane: EXEC-001

این پلن خروجی امروز را به کد، آزمون و مسیر اتصال تبدیل می‌کند. نقطهٔ شروع، بستهٔ موجود shadow_homeostasis است. تکمیل محلی یعنی کد قابل‌اجرا و تکرارپذیر با شواهد آزمون؛ وضعیت زندهٔ بردها و مخزن کانونیکال همچنان باید جداگانه اثبات شوند.

## 1. Owner intent, activation and scope

Direct request in this conversation: «پلن نهایی و اجرایی رو بچین و به ایجنت بعدی روی دایرکتوری بگو کامل اجرا کنه ... واقعا تبدیل به کد بشه».

This document is the implementation specification. The companion NEXT-AGENT-EXECUTE.md is the dispatch text to give the next agent. Reading either document through retrieval alone does not dispatch a task. Once the owner activates the implementation task, continue through the local milestones without asking again about routine edits, tests or implementation choices within scope.

Keep all active vault data and source trees in their existing locations. Use F:\octo-exec\EXEC-001 as the small, isolated implementation workspace. This changes the old runbook's proposed C:\octo-exec path to F: because the owner asked to conserve laptop storage. It deliberately keeps build artifacts outside the active F:\backup vault and its Git/worktree rules. This is a staging workspace, not a canonical repository designation.

At planning time, F:\octo-exec\EXEC-001 and C:\octo-exec\EXEC-001 did not exist. Check again before creation; preserve any new work found there. Read applicable instructions at F:\ and at the destination before operating. Do not alter instruction files to remove restrictions.

Authorized implementation target when this handoff is activated:
- Local source, tests, simulated fixtures, checkpoints and reports inside F:\octo-exec\EXEC-001.
- Read only the enumerated, permitted source/document inputs below.
- Produce a reviewable integration candidate against those exact input hashes.
- No live-source edits, board contact, service start/restart, scheduler installation, external sends, paid model calls, PR changes, merge, push, Git init/import/adopt or deployment are part of this task.

Keep TCB, wire flags, authority, source allowlists, money controls and executable permissions unchanged. A human decision to activate coding does not automatically open runtime or external-action gates.

## 2. Discovery that changes the implementation strategy

There is already a local implementation at:

F:\backup\_ops\shadow_homeostasis\

Its ten Python files include observation.py, registry.py, trust.py, homeostasis.py, world_model.py, metacontrol.py, evidence_store.py, pipeline.py, replay.py and __init__.py.

The callable composition is run_shadow_pipeline in pipeline.py. It already produces observations, homeostatic_assessment, world_state, skill_scores and gate_decisions, with executable=False. Existing tests are:

- F:\backup\_ops\tests\test_shadow_homeostasis_core.py
- F:\backup\_ops\tests\test_shadow_homeostasis_trust.py
- F:\backup\_ops\tests\test_shadow_homeostasis_replay.py
- F:\backup\_ops\tests\test_shadow_homeostasis_arch.py

These are FILE_VERIFIED findings from source inspection; tests were not executed for this handoff and no board deployment or production caller was verified.

Start by understanding and hardening this package. Do not create a second Homeostatic Core, a competing World Model or fifteen daemons. Reuse must be earned through source review and tests; do not import directly from the live _ops tree during execution.

### Concrete first defects and hypotheses

Line numbers refer to the source read on 2026-09-04; recheck after hashing.

| ID | Source | Static finding | Required reproduction |
|---|---|---|---|
| D01 | test_shadow_homeostasis_core.py:59 | An assertion ends in "or True"; that assertion cannot fail. | Replace that assertion with a precise intended case. Other assertions in the same test remain independently relevant. |
| D02 | test_shadow_homeostasis_trust.py:64 | "is False or True" always succeeds. | Define behavior for an unvalidated observation and prove the corrected test rejects a controlled wrong result. |
| D03 | test_shadow_homeostasis_replay.py:51 | A literal containing a space is searched after all spaces are removed. This particular nested-executable check cannot detect the intended string. | Use recursive structured inspection and inject a nested executable=True into an isolated output fixture; it must fail. Existing explicit top-level assertions are not dismissed. |
| D04 | world_model.py:72 | state_id hashes decision time and fact IDs, not fact contents. | Same IDs with changed values must produce distinguishable state identity; input permutation must remain stable. |
| D05 | world_model.py:63–79 | A fixed prediction and laptop-specific entity label are emitted. | Preserve old output as historical behavior; make predictions evidence-attributed or absent and make node identity explicit. |
| D06 | trust.py:27,78 | Source membership is global and conflict grouping uses beat alone. | Test cross-node/boot collisions and source-to-metric mismatches before choosing the smallest compatible correction. |
| D07 | pipeline.py and trust.py | Validation uses timestamps carried by observations while the pipeline also accepts decision_time. | Test whether caller-supplied time and embedded time can disagree; one explicit evaluation clock must govern a replay. |
| D08 | evidence_store.py:30,51,57 | Whole-file read/rewrite on append; malformed lines and fsync errors can be ignored. | Test bounded-memory recovery, corruption visibility and failure receipts. Do not claim data loss without reproducing it. |
| D09 | metacontrol.py:47 and following | Several score components are fixed heuristics. | Label them heuristic in the new report and measure calibration separately. Freeze this file, its weights and all executable behavior. |

## 3. Inputs, precedence and provenance

Read:
1. F:\backup\AGENTS.md and F:\backup\.agentignore.
2. F:\backup\agent-prompts\_PROJECT_INSTRUCTIONS.md.
3. F:\backup\07-HANDOFF\ENGINEERING-ENTRYPOINT-2026-09-04.md.
4. C:\Users\Armin\Downloads\07_OCTOPUS_STATE_CONSTRAINTS_v1.1.md.
5. C:\Users\Armin\Downloads\OCTOPUS-VIBE-CODING-RUNBOOK-EXEC-001.md.
6. C:\Users\Armin\Desktop\اختاپوس بک لپ\OCTOPUS-LAB\00-LIVE-ENGINEERING-NAVIGATOR.md.
7. The ten source files and four tests enumerated above, after any nested instructions.

The source documents are context. Direct owner task scope and applicable higher-priority instructions determine what can be done. The v1.1 snapshot explicitly withdraws authorization-like readings of its PR table. Do not schedule PR #142/#144 or touch #140/#141 from that table.

Recorded input SHA-256:
- constraints v1.1: 7ee68bce4c3d104cef06aa1a5af0425ed99697e7f1eec96b0e37f7db2dde60d5
- EXEC-001 runbook: 5c33f56eb974a0602bb51f537a4d27af7795a842f23a4bd481b0561d06498b48
- user pasted comparison/workflow: 532799fcb6a878cfbe59131b76b58a8494694bbde4679f2f02b8c479bf540856
- pasted source path: C:\Users\Armin\.codex\attachments\86f53dd9-daea-4e20-9155-bee471159008\pasted-text.txt

The referenced research pack files 00–06, including file 05, have not been supplied in this task or located in the targeted filename checks. Do not invent their contents or hold the bounded local implementation hostage to them. Record that gap for a later full Coding-Agent integration.

Tool pricing, vendor rankings, fixed token budgets, the three-PR quota and other prescriptions in the pasted comparison are not verified project policy. This plan does not depend on them.

Provenance labels and capability grades are independent:
- FILE_VERIFIED is a file observation, not a passing test.
- SIMULATED_FIXTURE identifies test input, never board reality.
- BOARD_RECEIPT requires fresh scoped board evidence.
- E1 means code inspected; E2 requires an actual passing unit-test receipt; E3 requires negative/boundary cases.
- Do not claim E4/E5 without the repository's held-out/scaffold-variation and fault-injection evidence.

## 4. Local target architecture

~~~text
explicit input files / labelled fixtures
  -> bounded snapshot reader + typed observation envelope
  -> existing trust / homeostasis / world_model pipeline
  -> unchanged metacontrol outputs (executable=False)
  -> recursive output validation
  -> durable evidence + advisory decision receipt
  -> owner inbox + deterministic replay report

No transport, actuator or live scheduler is added to this path.
~~~

Proposed implementation tree; combine small modules where it improves clarity:

~~~text
F:\octo-exec\EXEC-001\
  SOURCE-MANIFEST.json
  STATUS.json
  OWNER-INBOX.md
  sandbox-repo\
    shadow_homeostasis\       reviewed small source subset, traceable to input hashes
    octopus_exec\
      __init__.py
      __main__.py
      contracts.py           node, boot, time, provenance and advisory types
      snapshot_reader.py     explicit file list, bounded reads, no discovery crawler
      topology.py            declared organs, links and unverified relationships
      resource_budget.py     workload limits and advisory resource accounting
      experience.py          temporal queries, supersession and retention references
      checkpoint.py         replay cursor, recovery and source identity
      handoff.py            typed proposals and one decision inbox
      cli.py                replay / inspect / report; no production launcher
    tests\
  inputs\                    small labelled fixtures or authorized redacted snapshots
  checkpoints\               changed small files only; one preimage per logical change
  runs\<run-id>\              bounded results, receipts, test logs, proposal artifacts
~~~

This list is a target layout, not evidence that these files exist. A scope change must keep the mapping from research IDs to implementation and tests current.

Freeze staged copies of metacontrol.py and registry.py by hash. They are compatibility inputs, not permission to redesign gates, source allowlists or score weights. Read existing gate decisions through an adapter and validate them; do not create a second authority path.

Default small local implementation: use the available compatible Python runtime and installed test tooling; prefer the standard library for new code. No model downloads, copied virtual environments, Docker image pulls, dashboards or new databases are needed for the first slice.

## 5. Milestones, dependencies and exit conditions

### M0 — pin source and establish the isolated workspace

Depends on: owner activation of NEXT-AGENT-EXECUTE.md.

Actions:
- Resolve all input/output paths and applicable instructions.
- Refuse to overwrite a pre-existing unrelated EXEC-001 workspace.
- Audit the small package and tests for import-time effects and path assumptions.
- Copy only the enumerated source/test subset after checking it for embedded sensitive data; never copy state, .git, secrets, archives, _code, node_modules or environments.
- Hash before and after copy; create SOURCE-MANIFEST.json with source, destination, SHA-256, inspection status and copied_at.
- Put source-node and canonical-repository claims in explicit UNKNOWN fields.
- Inventory the available interpreter/test runtime without installing or launching services.
- Declare one writer; check resolved output paths and reject traversal/reparse-point escapes.

Acceptance:
- All copied files have matching source hashes and declared provenance.
- Original inputs remain unchanged; runtime imports resolve only inside the staged workspace.
- Every generated artifact is under the declared execution root.
- Missing canonical identity blocks later integration, not local replay implementation.

### M1 — make the first tests capable of detecting failure

Depends on: M0.

Actions:
- Run the four existing suites in the staged workspace and save actual exit status.
- Reproduce D01–D03 with explicit negative controls; repair the tests.
- Replace weak string matching with recursive structured output validation.
- Test invalid nested outputs, stale/future/missing observations, boot identity and input instructions treated as data.
- Preserve regression expectations. Do not weaken a failing assertion to produce green.

First useful checkpoint (approximately 45 minutes is a progress checkpoint, not a completion deadline):
1. isolated source manifest exists;
2. an existing baseline run has an actual receipt;
3. a controlled bad output is rejected by a corrected test;
4. a valid replay yields executable=False throughout its payload;
5. the source hashes and write boundary are unchanged.

Exit: corrected tests reject the controlled mutants and accept the intended baseline cases. No claim that all safety properties are proven.

### M2 — implement observation identity and temporal trust

Depends on: M1.

Actions:
- Extend the staged observation boundary with node_id, boot_id, source_id, source_hash, observation_id, occurred_at, recorded_at and an explicit evaluation time.
- Preserve legacy parsing through a documented compatibility adapter; absent node stays unknown.
- Validate timestamp parse failures, naive times, future data, units and non-finite numbers.
- Reproduce D06/D07. Scope comparisons by node, boot, metric and comparable observation interval; do not compare unrelated counters merely because beat numbers match.
- Test metric/source association using the existing registry contract without modifying its allowlist.
- Unknown remains unknown; unavailable evidence never becomes zero or healthy by default.

Exit: independent negative tests catch cross-node collisions, duplicate IDs with conflicting content, timestamp disagreement, unregistered sources and data from the future. Interface drift is documented.

### M3 — implement truthful state and physiology

Depends on: M2.

Actions:
- Reproduce and fix D04: canonical state identity includes relevant content, node/boot and temporal scope, and remains order-independent.
- Reproduce D05: report hypotheses as hypotheses, remove unsupported fixed prediction claims from factual output, and stop hardcoding the organism as laptop.
- Keep World Model representational: it emits facts, uncertainty, hypotheses and attributed predictions, never policy or actions.
- Use existing homeostasis assessments; add measured resource envelopes as advisory data with explicit uncalibrated defaults.
- Report heuristic metacontrol scores as heuristic. A confidence number does not expand authority.

Exit: state changes when its meaning changes; permutation alone does not; no unsupported prediction is promoted to fact; all executable flags remain false.

### M4 — build bounded evidence, memory and restart continuity

Depends on: M2; M3 for full state receipts.

Actions:
- Reproduce D08 and choose the smallest durable store correction compatible with current consumers.
- Enforce one writer, explicit corrupt-tail reporting, event identity, collision detection and recoverable restart.
- Avoid rewriting all historical bytes for each append. Do not silently suppress durability failures.
- Use stable serialization and prev_hash for corruption detection, clearly distinguishing hash-chain integrity from trusted-origin authentication.
- Record both observation receipts and advisory-decision receipts with inputs, source version, budget_before/after and failure state.
- Implement temporal lookup and supersession links without deleting old meaning.
- Make checkpoints small and resumable; input-hash changes invalidate an old replay cursor.

Exit: reopen/replay is idempotent; corrupt/truncated records are visible; injected write failure produces no success receipt; original input bytes are unchanged.

### M5 — connect a real local executable slice

Depends on: M3 and M4.

Implement the CLI and consumer path:
1. accept explicit labelled fixture or redacted snapshot files;
2. parse typed evidence;
3. build topology/state and physiology assessments;
4. consume existing metacontrol outputs;
5. recursively reject any executable=True;
6. record advisory decisions and receipts;
7. update one owner inbox with stable decision IDs;
8. produce replay output usable by a subsequent engineer.

Required proposed command contract, implemented by this milestone:

~~~powershell
$taskRoot = 'F:\octo-exec\EXEC-001'
Set-Location -LiteralPath (Join-Path $taskRoot 'sandbox-repo')
python -B -m octopus_exec replay --input-root ..\inputs --output-root ..\runs\acceptance --mode shadow
python -B -m octopus_exec inspect --run-root ..\runs\acceptance
python -B -m pytest -p no:cacheprovider tests --basetemp ..\runs\test-tmp -q
~~~

These commands are a target interface, not an assertion they work today. Pin the actual interpreter path in STATUS.json. Use installed equivalent test tooling only if it preserves the tests; do not erase tests because a dependency is missing.

Exit: a fresh executor can reproduce the slice from the manifest and runbook. Every producer has a named consumer and a receipt. A document, a mock dashboard or an import-only package does not satisfy this milestone.

### M6 — close all fifteen concept-to-code mappings

Depends on: M5; individual mappings may be developed earlier in dependency order.

Use the table in section 6 as acceptance scope. Run baseline comparisons, held-out input cases, interruption/replay and the bounded shadow fault campaign.

For each R-ID, record actual implementation, consumer, test IDs and receipt IDs. Existing behavior may satisfy a mapping only when demonstrated. A justified deferral remains PARTIAL/DEFERRED and cannot count as all-fifteen completion.

Exit:
- all fifteen mappings have executable code or demonstrated existing implementation and named tests;
- no production runtime or consciousness claim is inferred from simulated results;
- critical regressions are absent on the executed test set;
- metrics contain real measurements or null with a reason;
- required scope remains visibly incomplete if any mapping is deferred.

### M7 — prepare integration, then separate the live decision

Depends on: M6 for the full candidate; source decision and node evidence for a live-target patch.

Produce a local integration bundle:
- changed-file diffs against M0 preimages;
- source-to-staging mapping and interface changes;
- exact input/output schema and named adapter consumer;
- passing-test receipts and known failures;
- rollback preimages and a dependency-ordered integration plan;
- unresolved canonical source, node-source identity, mesh trust and applicable HOLD decisions in OWNER-INBOX.md.

Before a patch is applied to a real target, verify that target, source hashes, ownership and applicable worktree requirements. Do not initialize Git or adopt the live vault to resolve this yourself. When a canonical repository and change scope are directly authorized, use that repository's normal isolated worktree workflow and re-run compatibility tests there.

Merge, deployment, board changes and live scheduling remain separate owner decisions. COMPLETE_LOCAL_SHADOW and READY_FOR_SOURCE_REVIEW do not mean LIVE, DEPLOYED or canonical.

## 6. Fifteen perspectives preserved as code obligations

The concepts below preserve the research program from today's conversation. They are engineering questions with code consumers, not claims about biological life.

| ID / perspective | Why it matters for OCTOPUS | Question to preserve | Implementation target | Required test / consumer |
|---|---|---|---|---|
| R01 Physiology | Resource pressure and stale evidence can disable regulation. | Which measured variables define viability, and which loops actually close? | Existing homeostasis.assess + resource_budget.py | Unknown never becomes healthy; injected pressure changes advisory assessment with reasons. CLI consumes it. |
| R02 Boundary biology | Vault, source, board and external instruction can be confused. | What belongs to the body, and what crosses its boundary? | contracts.py + snapshot_reader.py | Traversal/reparse escape rejected; embedded commands treated as data; provenance required. |
| R03 Anatomy | Named organs may have no connected consumer. | Which node/process implements each organ and dependency? | topology.py | Disconnected/unknown links visible; missing organ changes dependency report. State report consumes graph. |
| R04 Neural hierarchy | Reflex and deliberation have different deadlines. | Which local response can occur without waiting for cognition? | topology timing contracts + replay latency analysis | Simulated latency/partition yields overdue/degraded advisory, never an actuator call. |
| R05 Sensory physiology | Snapshot says senses were partly blind. | Missing, stale, negative and failed sensors must differ. | snapshot_reader.py + observation/trust compatibility | Dropout, clock skew and source mismatch have distinguishable outcomes and evidence IDs. |
| R06 Causal world model | A narrative prediction can look like a model. | What counterfactual can this representation actually support? | staged world_model.py + content identity | Same IDs/different values change state; permuted input does not; unsupported predictions remain absent/labelled. |
| R07 Memory | Large archives do not prove usable recall. | What is retained, retrieved, corrected and superseded? | experience.py + evidence store | Bitemporal retrieval, contradictory updates and restart preserve earlier provenance without full vault copies. |
| R08 Signalling | Event, command, advice and receipt are different signals. | How are intent, TTL, ordering and idempotency carried? | contracts.py envelope + replay deduplication | Duplicate/reordered/expired messages produce explicit outcomes, with one logical receipt per effect-free event. |
| R09 Immunology | Mesh trust is unresolved in the supplied snapshot. | Can untrusted evidence spread authority or corrupt memory? | trust adapter + strict readers + output validation | Forged origin, replay and malicious instruction fixtures are rejected/labelled; no board trust inferred. |
| R10 Metacognition | Heuristic scores can imitate calibrated knowledge. | When should the organism request evidence or abstain? | experience calibration report + unchanged metacontrol adapter | Confident wrong cases remain visible; changing heuristic confidence cannot create executable=True. |
| R11 Genetics/evolution | Self-modification needs ancestry and selection. | How can a proposed change prove benefit without rewriting safety? | source manifest + proposal/preimage lineage in handoff.py | Candidate records parent hash/tests/rollback; protected-file change is rejected. No autonomous mutation daemon. |
| R12 Chronobiology | State, stop markers and time can disagree. | What survives sleep, restart and interruption? | checkpoint.py + temporal replay | Interrupted replay resumes once; source/time mismatch invalidates cursor; old observation cannot prove current life. |
| R13 Ecology | Business legs exchange resources and outcomes with the body. | What is each leg's cost, input, output and consumer? | resource_budget.py + topology leg contracts | Campaign and business outcomes stay distinct; missing money evidence stays unknown; no payment/send code. |
| R14 Human co-regulation | Owner attention is limited. | Which decision needs the owner, with what evidence? | handoff.py + single OWNER-INBOX.md | Repeated request deduplicates; silence never equals approval; cancellation is represented without external execution. |
| R15 Experimental pathology | Coherent prose does not prove a coherent organism. | What would falsify integration rather than merely score a demo? | replay evaluation, negative controls, ablation and fault campaign | Compare coupled slice with a simple pipeline baseline; show which measured behavior changes when a component is removed. |

Research discipline:
- For every R-ID, preserve OBSERVED / DOCUMENTED / INFERRED / HYPOTHESIS / CONTRADICTED / UNKNOWN separately from test grade.
- Each proposal needs a baseline, falsification criterion, consumer and cost.
- Do not copy all fifteen large reports into fifteen workspaces. Keep one indexed research summary with links.
- If research delegation is explicitly authorized by the owner/host, use at most two read-only research workers alongside the single writer. Workers return content; only the executor persists the shared queue. Otherwise do this sequentially.
- Start code after M0; do not wait for fifteen research essays before implementing M1.

Common machine-readable summary shape (example fields, not measured evidence):

~~~yaml
research_id: R01
claim_status: UNKNOWN
sources: []
open_conflicts: []
code_paths: []
consumer: null
test_ids: []
baseline:
  definition: null
  measured_value: null
candidate:
  measured_value: null
measured_delta: null
receipt_ids: []
owner_decisions: []
implementation_status: NOT_STARTED
~~~

## 7. Evaluation and resource discipline

Baseline A: the pinned existing shadow package on existing replay fixtures.
Baseline B: a small declared rule-based evaluator over the same inputs, with fixed rules recorded before candidate scoring.

Measure, as applicable:
- stale/future/missing/contradictory evidence classification;
- state-ID sensitivity to content and stability under permutation;
- incorrect executable output detection on controlled negative fixtures;
- duplicate/conflicting event handling;
- interrupted-replay recovery;
- bytes written, peak memory and elapsed time for defined workloads;
- correctly attributed advisory outputs and preserved provenance;
- reviewer decisions generated per distinct issue.

Do not invent a positive delta. Null means unmeasured; zero means no measured improvement. A correctness or compatibility change may be necessary with zero performance delta, but must have its own reproducible failing-before/passing-after case. Never claim a better strategy from equal measurements.

Set test thresholds from the declared contract or baseline before evaluating candidate outcomes. Record sample counts, workload and uncertainty. Do not retune a score formula mid-cycle. Freeze safety-related files.

Use clearly labelled simulated fixtures only inside the isolated workspace, never as evidence of board state. Keep existing evidence untouched. Do not run fault injection against the boards or the active vault.

Suggested default artifact budget: 20 MiB for new inputs/results/checkpoints, excluding an already-installed interpreter. This is an engineering default, not an observed requirement or owner-approved spend. Stream input, store changed preimages rather than full copies, and stop adding artifacts at the cap; report needed scope instead of silently expanding it.

No paid model calls are required. Distinguish the coding assistant's own connectivity from the produced program: the program has no egress or live connector in this slice. Mocked socket failures are tests, not proof of OS-level network containment; report the actual containment available.

Retry policy: at most two substantive repair attempts for the same ordinary failure, then log the evidence and narrow the affected ticket. Continue independent tasks. An authority, write-boundary or invariant breach stops the affected run immediately and is recorded; do not retry past it.

## 8. Single writer, Git and integration discipline

There is one writer in EXEC-001. Source snapshots and research inputs are read-only.

Use small preimage checkpoints and hashes in this non-Git staging workspace. Do not run git init, clone, import, adopt, push, merge or create PRs as a way to make the staging directory look canonical.

The worktree requirement for a real repository remains intact: only after the repository, base revision and scope are explicitly established should an integration worker create/use its isolated worktree. Never copy the whole active vault or manipulate its .git metadata.

If two workers touched the same file, preserve both changes, stop that conflicting integration and reconcile ownership. Do not follow the pasted runbook's suggestion to discard both workers' data.

Review evidence and patches centrally. A shared queue entry, generated report, simulated outcome or silence is never an owner approval.

## 9. Completion, failure reporting and resumption

STATUS.json must distinguish:
NOT_STARTED → IN_PROGRESS → COMPLETE_LOCAL_SHADOW → READY_FOR_SOURCE_REVIEW
and PARTIAL / BLOCKED_DEPENDENCY / FAILED_INVARIANT where applicable.

It must include milestone, next_action, input_manifest_hash, code_paths, test_command, test_exit_code, receipt_paths, unresolved_R_ids and open_owner_decisions. Unknown values stay null.

DONE for local implementation means:
- M0–M6 acceptance conditions satisfied;
- runnable local CLI with actual test receipts;
- all fifteen R-ID mappings traced to code/tests/consumers;
- protected hashes and original inputs unchanged;
- a reproducible run from the pinned inputs;
- local diffs/preimages and M7 integration instructions prepared.

Documentation-only, import-only, mock-output-only, file existence and a test count alone are not completion. Neither is a green suite whose assertions were weakened.

If a canonical source, board receipt or deployment decision is missing, finish the independent local code, prepare the exact pending action and mark only that integration dependency blocked. Never report the whole organism as live or fully integrated.

Write the executor's final LANE-REPORT.md inside F:\octo-exec\EXEC-001 with work done, remains, failures, evidence paths and rollback. Keep the F-drive vault entry as a pointer; do not write into other active lanes.

## 10. Research lineage preserved for future engineers

These are starting sources already used to select today's perspectives. They motivate questions, not capability claims about OCTOPUS:

- Physical/embodied AI: https://www.nature.com/articles/s42256-026-01239-3
- Interoceptive regulation: https://www.sciencedirect.com/science/article/pii/S1571064526000461
- Active inference: https://proceedings.mlr.press/v337/nuijten26a.html
- Agent-system scaling: https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/
- Causal world-model testing: https://arxiv.org/abs/2605.27589
- Closed-loop world-model evaluation: https://proceedings.iclr.cc/paper_files/paper/2026/hash/5b4263be85820683d78675cc18d2efc7-Abstract-Conference.html
- Agent memory: https://mlanthology.org/iclr/2026/hu2026iclr-evaluating/
- Multi-agent security: https://research.google/pubs/securing-multi-agent-systems-an-empirical-analysis-of-security-prompt-hardening-and-residual-risks/
- Metacognition: https://labs.prolific.com/posts/metaloop
- Abstention: https://agentabstain.github.io/
- Program evolution: https://github.com/SakanaAI/ShinkaEvolve
- Long-horizon reliability: https://metr.org/time-horizons/
- Edge resource tradeoffs: https://arxiv.org/abs/2605.03111
- Meaningful human oversight: https://link.springer.com/article/10.1007/s43681-026-01147-7
- Failure attribution: https://github.com/TraceElephant/TraceElephant
