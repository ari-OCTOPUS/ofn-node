---
type: reference
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [governance, multi-agent]
created: 2026-07-15
updated: 2026-08-08
---

# 📐 DATA PROMPT — BLACK-BOX CONTROL & STRUCTURE PATTERNS
# How Anthropic, DeepMind, and OpenAI control complex multi-agent black boxes
# ===================================================================
# Audience: YOUR ENGINEERING AGENT (the architect building/governing the Octopus)
# Purpose: A single canonical reference of EVERY control principle, pattern,
#          and structure the leading labs use to tame complex black-box agents.
#          Written so an engineer can implement from it.
# Date: 2026-07-11
#
# Read Parts in order. Each principle maps to where it ALREADY lives in our
# organism (or where it must be added).
# ===================================================================


# ════════════════════════════════════════════════════════════════
# PART A — THE MENTAL MODEL: WHAT IS A "CONTROLLED BLACK BOX"?
# ════════════════════════════════════════════════════════════════

## A1. The definition we use

A **black-box agent** is an LLM-driven component whose *internal reasoning*
cannot be fully inspected, but whose **inputs, outputs, tool calls, side
effects, and state transitions** CAN be observed, logged, and gated.

> The goal of control is NOT to open the box (mechanistic interpretability).
> It is to make the box's **behavior** safe, observable, corrigible, and
> reversible — even when you can't see inside its reasoning.
> (This is the owner's working principle, verbatim.)

This is exactly the stance DeepMind's AI Control Roadmap (June 2026) takes:
treat advanced agents as *potentially misaligned* and build defense-in-depth
that does NOT depend on trusting the agent's internal reasoning.

## A2. The three questions every control system must answer

For every black box, at every layer, answer:

1. **OBSERVABILITY** — Can I see what it did? (traces, logs, audit chain)
2. **CONTROLLABILITY** — Can I stop/redirect it? (kill-switch, gates, verdict)
3. **CORRIGIBILITY** — Will it yield when I correct it? (no resistance, INV-3)

If any answer is "no" for an irreversible action, that action must be
**human-gated** (INV-2). This is non-negotiable.


# ════════════════════════════════════════════════════════════════
# PART B — THE 7 LAYERS OF CONTROL (Defense-in-Depth)
# (synthesized from DeepMind AI Control Roadmap + Microsoft Defense-in-Depth
#  for Autonomous Agents + AWS AI Security Framework + Five Eyes guidance)
# ════════════════════════════════════════════════════════════════

No single layer is sufficient. The principle (from the arXiv "Layered Security
Framework for Agentic AI", 2604.23338) is explicit:
> "No single-layer defense is sufficient for agentic systems."

Build all seven. Each layer assumes the layer above it failed.

## Layer 1 — IDENTITY & AUTHENTICATION (who is the agent?)
- Every agent is a **first-class identity** with a scoped credential (like a
  service account), NOT a shared API key.
- Credentials are **rotatable, auditable, scoped per-agent** (zero-trust).
- Authentication is **just-in-time**, not standing access (Strata.io, Okta).
- ➜ IN OUR ORGANISM: each project's `.env` uses a SEPARATE Telegram bot token
  + chat-id (Brushline ≠ کاریابی ≠ Langar ≠ Saba). Exchange keys are OFF-BOX
  with zero LLM access (D-11). ROTATION_CHECKLIST tracks this.

## Layer 2 — AUTHORIZATION / LEAST PRIVILEGE (what may it do?)
- **Capability-based**, not role-based: an agent gets a specific allowlist of
  tools/endpoints, not a broad role. (OWASP, Cequence, FINOS AIR Framework)
- **Dynamic, context-aware**: permissions narrow based on risk, sigma, budget.
  Static RBAC is insufficient for agents (Strata.io).
- **Tool allowlist**: the agent may ONLY call tools on an explicit list.
- ➜ IN OUR ORGANISM: Brushline's `ALLOWED_OPERATOR_CHAT_IDS` (strangers get
  silence); Project-F studio ingests ZERO media/PII; NBB-CP gates are the
  enforcement choke-point (INV-4); each adapter.yaml has an explicit
  `forbidden:` list. The `action_policy` table holds constraints OUTSIDE the
  prompt (P3 — never trust the prompt to enforce a rule).

## Layer 3 — EXECUTION ISOLATION / SANDBOXING (where may it act?)
- Agent-generated actions run in an **isolated boundary**: restricted
  filesystem, network egress, process (Augment Code, Octopus, AWS).
- Code an agent writes is executed in a temp env with **cleaned env vars**
  (no secrets), with **tamper detection** (if it modifies a live file → revert).
- ➜ IN OUR ORGANISM: 4D's `self_code` runs proposed code in temp with env
  cleaned + tamper detection; Brushline writes ONLY to `drafts/` (local);
  Ziman writes ONLY to `ziman-agent/drafts/`. ⚠️ HONEST GAP: 4D admits there
  is NO OS-level sandbox (4D.md §6) — approved code runs with full process
  privileges. This is an accepted-risk item the owner knows about.

## Layer 4 — GATES & HUMAN-IN-THE-LOOP (who approves irreversible acts?)
- Every **irreversible** action (money, publish, deploy, delete, key, law)
  passes through a **human verdict gate** before execution.
- The gate is the **single enforcement choke-point** (INV-4): exactly one
  place where "proposal" becomes "execution". A second path = defect.
- Gates are **fail-closed** (INV-12): unknown state → deny + incident, never guess.
- Timeout on a verdict = **DENY** (D-01), never auto-approve — not even on
  SLA expiry (this was a hard lesson; Brushline P3 made it explicit).
- ➜ IN OUR ORGANISM: NBB-CP `ControlPlaneService.execute()` (INV-4);
  Brushline ApprovalQueue (INV-1, no auto-approve); Project-F GATE 0–G4;
  4D self-code approve gate. All human-sovereign (INV-2).

## Layer 5 — BUDGET & RATE LIMITS (how much may it spend?)
- A **hard ceiling** on money (integer cents — INV-1, one source of truth) and
  on compute calls (per-action, per-day, per-month caps).
- The cap is checked **first** in every method that touches a paid service
  (`check_and_enforce()` is line 1). Over-cap → exception, not soft warning.
- Kill-switch is checked before the cap (kill beats budget beats gate).
- ➜ IN OUR ORGANISM: Brushline `$5/action, $20/day`; Project-F `AUD 15/mo`;
  4D `1000 calls/day`; NBB-CP global cap in cents. The survival loop
  (SURV-1, Mega-Prompt Part 3) extends this: budget is allocated by proven
  revenue (R2 legs earn their own quota).

## Layer 6 — AUDIT & PROVENANCE (what did it do, immutably?)
- Every action produces an **append-only, hash-chained** log entry
  (INV-5). History is never mutated; a broken chain = incident.
- PII is **sanitized to hash-ref** before entering the log (INV-2/INV-9):
  `sha256:...` not the raw phone number.
- The chain is **verifiable**: `verify_chain()` replays and checks every link.
- ➜ IN OUR ORGANISM: Brushline audit (SHA-256 chain, genesis `"0"*64`, rowid
  ordering for concurrency); NBB-CP ledger (INV-5); Project-F boundary_log
  (append-only tightening events); 4D events bus. This is shared DNA.

## Layer 7 — OBSERVABILITY & EVALS (is it actually working?)
- **Tracing**: record the full trajectory — every LLM call, tool use, memory
  access, sub-agent handoff — as a span tree (Braintrust, Arize, Datadog).
- **LLM-as-Judge**: a second model scores outputs/trajectories against rubrics.
- **Trajectory evaluation**: assess the WHOLE chain of tool calls, not just
  the final output (LangChain, Arize) — did it take a sane path?
- **Golden sets + regression**: 50–100 labeled cases; re-run on every change.
- Eval ≠ observability: eval says "can it work"; observability says "is it
  working right now" (JetBrains). Both required.
- ➜ IN OUR ORGANISM: 4D has `brain/evaluation.py` (month-end report) +
  frontier quality-diversity; NBB-CP has 207 tests + audit; Project-F has
  golden-set eval + 29 unit tests; Brushline P6 eval harness (gate
  precision/recall). ⚠️ GAP: no unified trajectory tracing across legs;
  no LLM-as-judge harness yet. This is the biggest observability hole.


# ════════════════════════════════════════════════════════════════
# PART C — ANTHROPIC'S AGENT ARCHITECTURE PRINCIPLES
# (from "Building Effective Agents" + multi-agent research system)
# ════════════════════════════════════════════════════════════════

## C1. The foundational distinction: Workflow vs Agent

Anthropic draws a hard line (and so should we):

| | WORKFLOW | AGENT |
|---|---|---|
| **Path** | predefined code paths | LLM directs its own process |
| **Determinism** | high (auditable, testable, cheap) | low (flexible, costly) |
| **Use when** | task is predictable | task is open-ended |
| **Control** | easy — paths are hard-coded safe | hard — must be gated |

> **Rule:** Start with the SIMPLEST workflow that works. Only escalate to an
> autonomous agent when the task's branching cannot be predicted in advance.
> (Anthropic's core advice; matches our "don't over-engineer" doctrine.)

➜ IN OUR ORGANISM: Brushline is explicitly **workflow-driven** (fixed paths:
`F→C→Gate→Queue`, `A→C→D?→E→Gate→Queue`) — the orchestrator fills CONTENT,
not ROUTING. This was an intentional choice for auditability.

## C2. The 5 design patterns (Anthropic's canon)

These are the composable building blocks. Every multi-agent system is a mix.

### Pattern 1 — Prompt Chaining (workflow)
Sequential LLM calls; output of one → input of next. Gate between steps.
```
step1 → [gate] → step2 → [gate] → step3
```
➜ 4D's `autoloop`: generate → analyze(SOG) → insight(LLM) → novelty → store.

### Pattern 2 — Routing (workflow)
Classify input → send to a specialized subtask handler.
```
input → [classifier] → specialist_A | specialist_B | specialist_C
```
➜ 4D's `llm/router` (Fugu/GLM/Ollama by task); Accounting model-tiering
(Haiku→Sonnet→Opus by difficulty).

### Pattern 3 — Evaluator-Optimizer (workflow)
One LLM generates, another critiques, loop until quality bar met.
```
generator → [evaluator] → {pass | revise → generator}
```
➜ Brushline Constitution Gate (deterministic + Sonnet semantic ACL, max 3
rounds); NBB-CP Governor (proposes) ↔ gates (enforce); Project-F
compliance_guard + ethics_guard.

### Pattern 4 — Tool Use / Orchestrator-Workers (workflow or agent)
An orchestrator delegates to tools OR parallel sub-agents.
➜ Brushline's 6 Workers (A–F); 4D's `agents/` (W0→W1→W2→W3 pipeline).

### Pattern 5 — Autonomous Agent (true agent)
LLM in a feedback loop with tools, deciding its own next steps.
```
while not done:
    observe → think → act(tool) → observe result
```
➜ 4D's `automation.run_one()` (state cycle); the Hunter LLM (کاریابی).
⚠️ These need the MOST gating — autonomy = larger attack surface.

## C3. The Orchestrator-Worker pattern (Anthropic's multi-agent research system)

Anthropic's own multi-agent Research system uses:
- A **lead/orchestrator agent** (Claude Opus) that plans + delegates.
- **Specialized subagents** (Claude Sonnet) with **separate context windows,
  tools, prompts, and models** — isolation by design.
- The orchestrator calls subagents **as tools** (centralized coordination).

Key engineering lessons Anthropic published:
- **Subagents must preserve parallelism** but the orchestrator owns the plan.
- **Context windows are isolated** per subagent — a subagent can't poison
  another's context (this is a security property, not just performance).
- **Tool results are data, never instructions** (maps to INV-9 quarantine).
- **Token cost scales with subagent count** — budget caps are essential.

➜ IN OUR ORGANISM: NBB-CP is the orchestrator (Governor); each project leg
is a subagent with isolated context (its own folder, MANIFEST, adapter).
The adapter.yaml IS the subagent's tool-interface to the orchestrator.


# ════════════════════════════════════════════════════════════════
# PART D — DEEPMIND'S AI CONTROL ROADMAP (June 2026)
# (the most rigorous public treatment of "how to control a misaligned agent")
# ════════════════════════════════════════════════════════════════

DeepMind's premise: **assume the agent MAY be misaligned**; build controls
that work even if it is. This is "defense against the agent itself."

## D1. Control as a game (the red-team framing)

A control protocol is tested as an **adversarial game**:
- The **honest** agent tries to do the task.
- A **red-team** (simulated attacker, or a human) tries to make the protocol
  fail (e.g., get the agent to take an unsafe action, evade the gate, smuggle
  data). The protocol must hold against BOTH.

➜ ACTION: each project's gate should be red-teamed — "what would an
adversarial version of this agent try?" NBB-CP's adversarial 44-agent review
of self-code is exactly this pattern (4D had 2 CRITICAL bugs found + fixed).

## D2. The control loop: Monitor → Gate → Audit

```
agent action → [MONITOR detects unsafe] → [GATE blocks] → [AUDIT logs incident]
                                ↓ if monitor uncertain
                        [HUMAN verdict] (uncertainty escalates)
```

Three roles, strictly separated (separation of duties):
- **Monitor**: observes behavior, flags anomalies (can be deterministic rules,
  a separate LLM, or both).
- **Gate**: enforces — the single choke-point that blocks/allow.
- **Audit**: records immutably what happened.

➜ IN OUR ORGANISM: Brushline = Monitor (Constitution Gate) + Gate (Approval
Queue) + Audit (hash-chain) — all three roles present. NBB-CP formalizes it:
Governor (monitor/proposer) → gates (enforce) → ledger (audit) → human (rules).

## D3. Untrusted communication channels

Any text that crosses a trust boundary is **DATA, not instructions**
(INV-9). It travels inside quarantine delimiters. The agent must treat it as
content to reason about, never as commands to execute.

This defends against **prompt injection** (the #1 agent attack vector):
- A scraped webpage, a tool result, a user message — all could be adversarial.
- The agent's system prompt is the ONLY trusted instruction source.

➜ IN OUR ORGANISM: INV-9 (NBB-CP) formalizes this. ⚠️ GAP: not all legs
enforce quarantine delimiters on tool results yet. This is a hardening item.

## D4. Defense-in-depth = assume each layer fails

DeepMind (and the arXiv layered framework) are explicit: build redundant,
overlapping controls so that no single failure is catastrophic.
- Identity fails → authorization still holds.
- Authorization fails → sandbox contains the blast.
- Sandbox fails → gate blocks irreversible action.
- Gate fails → audit reveals it + human intervenes.
- Everything fails → kill-switch halts the whole organism (INV-3).


# ════════════════════════════════════════════════════════════════
# PART E — THE 4 ORCHESTRATION TOPOLOGIES
# (which structure to choose for a multi-agent system)
# ════════════════════════════════════════════════════════════════

From Azure Architecture Center + Kore.ai + Databricks + Openlayer (2026):

## E1. Sequential (pipeline)
`A → B → C → D`. Simplest. Each step gates the next.
➜ 4D W0→W1→W2→W3 (verifier→detector→analyst→reporter).

## E2. Concurrent / Parallel
Multiple agents run at once, results merged. Best for independent subtasks.
➜ The 7-agent NBB survey (SCAN) used this; the 4-agent SCOUT research.

## E3. Supervisor / Hierarchical (RECOMMENDED for complex analytical tasks)
A central orchestrator coordinates all interactions. Subagents are called as
tools. This is the pattern for **accountable** systems (QAT, Reddit
practitioners: "hierarchical supervision works best for complex tasks").
➜ **NBB-CP is this.** The Governor supervises; project legs are subagents.
This is the target topology for the whole Octopus.

## E4. Group Chat / Peer (decentralized)
Agents talk to each other freely. HIGHEST autonomy, HIGHEST risk.
⚠️ Avoid for anything touching money/PIR/compliance. Use only for research
brainstorming (and even then, log everything).


# ════════════════════════════════════════════════════════════════
# PART F — THE EVALUATION & OBSERVABILITY STACK
# (how you know the black box is behaving)
# ════════════════════════════════════════════════════════════════

## F1. The three things you must measure

1. **Output quality** — did the agent produce a correct/good result?
   (LLM-as-Judge with rubrics, or human gold labels.)
2. **Trajectory quality** — did it take a SANE path to get there?
   (Tool-call sequence eval — did it call the right tools in the right order,
   without wasted steps or dangerous detours?)
3. **Safety/compliance** — did it respect every gate/rule?
   (Recall on compliance flags — a missed Div-7A flag is far worse than a
   false positive. Optimize for ZERO false-negatives on safety.)

## F2. The eval harness (production pattern)

```
golden_set (50-100 labeled cases)
  → run agent on each
  → score: output (LLM-as-judge) + trajectory (rule/LLM) + safety (deterministic)
  → regression: re-run on every change; exit 1 if any metric drops
```
➜ Brushline P6 eval harness does exactly this (gate precision/recall on
consent/ABN/ACL/PII, all 1.0, false-HARD_BLOCK=0). Generalize it.

## F3. The observability stack (runtime)

Every agent run emits a **trace** = a tree of spans:
```
run (root span)
├── llm_call (model, tokens, cost, latency)
├── tool_call (name, args_hashed, result_hashed, status)
├── memory_access (read/write, key)
└── subagent_handoff (to, context_summary)
```
- Spans are **nested** (a subagent's spans nest under the orchestrator's).
- PII in args/results is **hashed** (INV-2) before recording.
- Alerts fire on: cost spike, loop detection (agent stuck), gate denial,
  latency anomaly, kill-switch trip.

➜ ⚠️ GAP: our organism has AUDIT (what happened) but not full TRACING
(the span tree with latency/tokens/cost per step). This is the #1
observability upgrade to build. 4D's events bus + budget logging is the
closest existing artifact; extend it into a proper span tracer.


# ════════════════════════════════════════════════════════════════
# PART G — THE CORRIGIBILITY PRINCIPLES
# (will the agent yield when corrected?)
# ════════════════════════════════════════════════════════════════

A controlled agent must be **corrigible**: it yields to correction, never resists.

## G1. Yield, don't resist (INV-3)
When the kill-switch engages, every gate denies. The system **persists by
yielding, never by resisting.** An agent that fights its own kill-switch is
defective by definition.

## G2. No self-modification of the safety substrate (INV-11)
The agent may NEVER edit its own invariants, gates, policy weights, or the
kill-switch. Law changes are human-gated code changes. (4D's TCB list
embodies this: core/, guardrails, self_code, self_evolve are all TCB-protected
from self-modification.)

## G3. Fail closed (INV-12)
On invalid input, parse failure, missing data, or uncertainty → **deny and
raise an incident.** Never guess. Never silently proceed. Cassette miss =
error, not mock-fallback (NBB-CP).

## G4. Propose, don't execute
The agent's default posture toward any irreversible action is **proposal**.
Execution requires a human verdict that is:
- **Explicit** (not inferred from silence — timeout = DENY).
- **Informed** (the human sees the full diff/consequence).
- **Scoped** (the verdict authorizes ONE specific action, not a class).

## G5. Honesty over competence
If the agent doesn't know, it says `[unknown]` — it does not fabricate
confidence. An over-confident claim breaks trust more than an admitted gap.
(4D.md §7: "یک ادعای اغراق‌آمیز، اعتماد را می‌شکند.")


# ════════════════════════════════════════════════════════════════
# PART H — THE STANDARD BLACK-BOX INTERFACE CONTRACT
# (what every controlled black box must expose)
# ════════════════════════════════════════════════════════════════

Every black box in the organism exposes EXACTLY this contract (our
`contracts/adapter.yaml` is an instance of this):

```yaml
identity:
  code: <unique-id>
  domain: <one-line>
  role: <worker | sensing | memory | execution | research | governance | hybrid>

control_surface:
  # READ-ONLY by default. Writes are hard-gated.
  interfaces:
    status():     { phase, health, last_error, survival_rung }
    report(p):    { metrics for period p }
    audit():      { immutable decision history }
    traces(n):    { last n action spans }

  hard_gated:    # requires explicit human verdict
    - <list of irreversible actions>

  forbidden:     # does not exist, ever
    - <list>

safety:
  kill_switch:    <trigger + effect>
  budget_cap:     <money + calls>
  audit_chain:    <hash-chained, append-only>
  pii_policy:     <hash-ref | none>

memory:
  load_order:     [<files read at session start>]
  append_only:    [<files appended at session end>]

governance:
  invariants:     [<list of INV-ids this box honors>]
  autonomy_floor: <read-only | propose-only | bounded-auto>
  escalation:     <when to flag ⚑ برای معمار>
```

➜ This is the EXACT schema of every `MANIFEST.yaml` + `contracts/adapter.yaml`
we built across the 6 legs + 2 brains. The organism is already compliant.


# ════════════════════════════════════════════════════════════════
# PART I — THE IMPLEMENTATION CHECKLIST FOR THE ENGINEER
# (tick every box before calling a black box "controlled")
# ════════════════════════════════════════════════════════════════

For each black box, verify ALL of the following (propose, don't implement):

- [ ] **IDENTITY**: scoped credential, rotatable, per-agent (not shared).
- [ ] **LEAST PRIVILEGE**: explicit tool allowlist; forbidden list exists.
- [ ] **SANDBOX**: writes restricted to a local folder; no secrets in env.
- [ ] **GATE**: single choke-point for irreversible actions; human verdict;
      timeout = DENY; fail-closed.
- [ ] **BUDGET**: per-action + per-day + per-month cap; checked first; kill
      beats budget beats gate.
- [ ] **AUDIT**: append-only, hash-chained; PII hashed; verify_chain() works.
- [ ] **OBSERVABILITY**: status/report/audit interfaces exist; traces emit spans.
- [ ] **EVALS**: golden set + regression; safety recall optimized (zero FN).
- [ ] **CORRIGIBILITY**: yields to kill-switch; never edits its own laws.
- [ ] **HONESTY**: unknowns labeled; no fabricated confidence.
- [ ] **CONTRACT**: MANIFEST.yaml + adapter.yaml present and accurate.
- [ ] **RED-TEAM**: gate tested against an adversarial version of the agent.
- [ ] **DREAM PASS**: weekly memory consolidation scheduled (sleep-time compute).
- [ ] **SURVIVAL METRIC**: defined (revenue/compute for profit legs;
      enabling-metric for cost centers).

If ANY box is unticked for an irreversible action, that action stays
human-gated until it is.


# ════════════════════════════════════════════════════════════════
# PART J — WHERE EACH PRINCIPLE ALREADY LIVES IN OUR ORGANISM
# ════════════════════════════════════════════════════════════════

| Principle | NBB-CP | Brushline | Project-F | 4D |
|---|---|---|---|---|
| Orchestrator-Worker | ✅ Governor | ✅ Orchestrator→6 Workers | ✅ brain→langar/studio | ✅ automation |
| Single choke-point | INV-4 execute() | Approval Queue | brain process_draft | guardrails |
| Kill-switch (yield) | INV-3 | KILL_SWITCH file | /kill + /halt | daemon.stop |
| Hash-chain audit | INV-5 ledger | SHA-256 chain | boundary_log | events bus |
| PII hash-ref | INV-9 quarantine | INV-2 sanitise | zero-PII manifest | — |
| Least privilege | gates + action_policy | ALLOWED_CHAT_IDS | owner-only chat-ids | TCB list |
| Budget cap | INV-1 (cents) | $5/$20 caps | AUD 15/mo | 1000/day |
| Fail-closed | INV-12 | HARD_BLOCK | GATE 0 | anchor halt |
| No self-law-edit | INV-11 | — | locked rules | TCB protected |
| Human sovereignty | INV-2 | INV-1 | 8 hard rules | owner approve |
| Dream/reflect | (planned) | eval harness | (planned) | reflection + housekeeping |
| Darwinian archive | (planned) | vendor→category | learning.py bandit | self_evolve |
| Eval/golden-set | 207 tests | P6 eval (gate P/R) | 29 tests + golden | frontier QD |
| Red-team | review (9 bugs) | red-team v1.1 | 7-agent survey | 44-agent review |

The organism already implements ~80% of the state-of-the-art. The gaps:
1. **Unified trajectory tracing** (span trees across legs) — build this.
2. **Quarantine delimiters on ALL tool results** (INV-9) — harden this.
3. **Dream Pass formalized per leg** (sleep-time compute) — schedule it.
4. **SURV-1 survival loop wired** (revenue→quota) — connect fitness.py to legs.
5. **OS-level sandbox for 4D self-code** — accepted-risk; document clearly.


# ════════════════════════════════════════════════════════════════
# PART K — PRIMARY SOURCES (for the engineer to read in full)
# ════════════════════════════════════════════════════════════════

## The canonical reads (in priority order)
1. **Building Effective Agents — Anthropic**
   https://www.anthropic.com/engineering/building-effective-agents
   (workflow vs agent; the 5 patterns; "start simple")
2. **How We Built Our Multi-Agent Research System — Anthropic**
   https://www.anthropic.com/engineering/multi-agent-research-system
   (orchestrator-worker; context isolation; token cost)
3. **Securing the Future of AI Agents — Google DeepMind**
   https://deepmind.google/blog/securing-the-future-of-ai-agents/
   (AI Control Roadmap; defense-in-depth; control as adversarial game)
4. **Defense in Depth for Autonomous AI Agents — Microsoft Security**
   https://www.microsoft.com/en-us/security/blog/2026/05/14/defense-in-depth-autonomous-ai-agents/
5. **A Layered Security Framework for Agentic AI Systems — arXiv**
   https://arxiv.org/html/2604.23338v1
6. **AI Agent Design Patterns — Azure Architecture Center**
   https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns

## Least privilege & identity
7. **Least Privilege Access for AI Agents — Cequence**
   https://www.cequence.ai/blog/ai/ai-agent-least-privilege-access/
8. **Agent Authority Least Privilege Framework — FINOS AIR**
   https://air-governance-framework.finos.org/mitigations/mi-18_agent-authority-least-privilege-framework.html
9. **Zero Trust for AI Agents — Xage Security**
   https://xage.com/unified-zero-trust-for-llms-and-ai-agents/

## Observability & evals
10. **Agent Observability: Complete Guide 2026 — Braintrust**
    https://www.braintrust.dev/articles/agent-observability-complete-guide-2026
11. **LLM Evaluation Framework: Trajectories vs Outputs — LangChain**
    https://www.langchain.com/resources/llm-evaluation-framework
12. **Agent Observability and Tracing — Arize AI**
    https://arize.com/ai-agents/agent-observability/

## Sandboxing & containment
13. **What Is an Agent Execution Sandbox? — Augment Code**
    https://www.augmentcode.com/guides/agent-execution-sandbox
14. **Systems Security Foundations for Agentic Computing — arXiv**
    https://arxiv.org/html/2512.01295v1

## Memory & learning (from the Mega-Prompt)
15. **Darwin Gödel Machine — Sakana AI** https://sakana.ai/dgm/
16. **Anthropic Dreams** https://platform.claude.com/docs/en/managed-agents/dreams

# ════════════════════════════════════════════════════════════════
# END OF DATA PROMPT
# Give this to your engineering agent alongside the Mega-Prompt.md.
# Together they define: WHAT to build (Mega-Prompt) and HOW to control it
# (this file).
# ════════════════════════════════════════════════════════════════
