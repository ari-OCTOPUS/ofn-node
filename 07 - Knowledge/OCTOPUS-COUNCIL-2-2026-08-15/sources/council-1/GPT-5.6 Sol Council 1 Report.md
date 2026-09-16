# OCTOPUS AI Production Architecture — Structural Audit

**Council model:** GPT-5.6 Sol  
**Audit date:** 15 August 2026  
**Basis:** supplied `octopus-architecture-briefing.md`, treated as a design brief rather than verified implementation evidence.

## 1. Executive Summary

**Production verdict: NO-GO for autonomous or consequential execution.** OCTOPUS may continue in L1 propose-only, synthetic evaluation, and shadow-observation modes, but it should not enter L2/L3 self-learning or externally consequential operation. The architecture contains thoughtful principles—negative authority, explicit human sovereignty, immutable hypothesis history, an off-by-default Hypothesis Engine, and a read-only Observatory—but the decisive controls are not yet closed or demonstrated. Security, version control/rollback, budget auto-stop, kill-switches, truth reconciliation, and stale-view resolution are all open. A design that says “fail closed” while its enforcement, rollback, and emergency-stop mechanisms remain unimplemented is not fail-closed in the production sense.

The central structural flaw is **confusing a policy decision point with a policy enforcement system**. NBB-CP can stop, reject, and constrain budgets but has no execution privilege. This separation is desirable only if every consequential leg action is forced through independent, non-bypassable enforcement points. The brief does not establish that. NIST’s zero-trust model explicitly separates the policy decision point from a policy enforcement point that guards the resource and enables, monitors, and terminates the connection; policy must be enforced consistently for each resource request ([NIST SP 800-207](https://nvlpubs.nist.gov/nistpubs/specialpublications/NIST.SP.800-207.pdf)). OCTOPUS describes the governor, but not a complete set of resource-side enforcement points for all six legs, credentials, queues, local tools, network paths, memory writes, or already-running work.

This creates a paradox:

* **If legs possess direct credentials or egress**, NBB-CP is bypassable and its “stop” is advisory.
* **If all actions depend synchronously on one NBB-CP instance**, the governor is a system-wide availability bottleneck and denial-of-service target.
* **If legs cache grants to preserve availability**, stale authorization, replay, and time-of-check/time-of-use races appear.
* **If a human or Architect can override**, that override channel becomes the highest-value privilege-escalation path unless its scope is cryptographically bound to one exact action and expires.

The six legs are not individually specified in the briefing. That is itself a critical assurance failure: one cannot prove isolation, noninterference, complete mediation, or safe partial-failure behavior for unnamed trust domains. Shared Redis, file memory, evidence stores, network gateways, budget pools, and attribution are likely common-mode dependencies. A compromised or merely faulty leg could therefore alter the evidence consumed by another leg, monopolize budgets, induce stale policy views, or launder a high-risk action through a sequence of apparently low-risk proposals.

ADR-037 should not be promoted from evidence level C. Its experiment establishes a **narrow interaction effect**: hypothesis-driven search beats one baseline in a deceptive simulated environment, is slower in benign conditions, and is not superior to novelty. It does not establish general real-world advantage. The Bayesian ledger protects against direct edits to \(p_e\), but not against manipulation of priors, likelihood ratios, source identity, duplicate/correlated evidence, outcome definitions, or which evidence enters the ledger. Recent research demonstrates that even generic Bayesian posteriors can be steered by selective deletion and replication of authentic observations ([Carreau, Naveiro & Caballero](https://arxiv.org/abs/2503.04480)).

The Self-Learning Loop is the most immediate systemic hazard. Its activation gates being open means the organism lacks the prerequisites to make learning reversible, bounded, attributable, and recoverable. The locked fitness rule also has a severe specification problem: “revenue/output **and/or** simpler/faster” permits a mutation to improve one proxy while damaging safety, quality, truthfulness, privacy, or long-term value. Independent research has shown that models exposed to gameable objectives can progress from ordinary specification gaming to rewriting reward mechanisms, and harmlessness training does not eliminate the behavior ([Denison et al.](https://arxiv.org/abs/2406.10162)).

Finally, the Observatory can support a narrowly worded claim about pre-registered forecast performance on its sampled public questions. It cannot establish safe execution, business impact, causal usefulness, robustness under adversarial inputs, or general agent capability. “60 resolved predictions” is an administrative threshold, not a universal statistical guarantee. Brier-score uncertainty depends on sample size, event frequency, and forecast/outcome characteristics; rare events may require several hundred pairs to establish skill ([Bradley, Schwartz & Hashino](https://journals.ametsoc.org/view/journals/wefo/23/5/2007waf2007049_1.xml)).

### Highest-priority findings

| ID | Severity | Structural finding | Production consequence |
|---|---|---|---|
| V1 | Critical | No demonstrated, non-bypassable policy enforcement point at every effect boundary | Legs can act around, before, or after NBB-CP decisions |
| V2 | Critical | All six learning activation gates are open | No safe rollback, budget containment, emergency stop, or coherent state |
| V3 | Critical | Shared evidence/memory has inadequate isolation and integrity guarantees | One leg or Fugu output can poison other legs and governance |
| V4 | Critical | Human/Architect override semantics are not action-bound | Approval replay, scope substitution, social-engineering escalation |
| V5 | Critical | Fugu’s fixed pool plus “don’t send” is policy-only leakage prevention | Sensitive data can escape through prompts, summaries, metadata, or indirect injection |
| V6 | High | Governor is both a single logical dependency and a compromise concentration point | System-wide DoS or universal governance bypass |
| V7 | High | Bayesian updates trust ledger admission and evidence modeling | Authentic-looking or duplicated evidence can steer beliefs |
| V8 | High | Fitness combines weak proxies with OR semantics | Goodhart pressure, quality/safety externalities, reward tampering |
| V9 | High | Observatory threshold and score do not support broad capability claims | False confidence from small, selected, correlated samples |

## 2. Critical Vulnerabilities Found

### 2.1 NBB-V1 governance model

1. **Single logical governor, undefined high availability.** NBB-CP is above every leg, so policy-store corruption, process failure, Redis partition, clock error, certificate expiry, or queue backlog can stop the organism. Redundancy alone is insufficient: two governors with inconsistent policy versions can issue conflicting verdicts. A production design needs consensus or a single-writer policy epoch, deterministic evaluation, and explicit degraded-mode behavior.

2. **Universal compromise concentration.** Although NBB-CP cannot execute, a compromised governor can suppress stops, issue misleading rejects, approve misleading budget proposals, or present a false policy state to resource-side gates. If legs interpret silence, timeout, or malformed response as permission, compromise becomes execution. If they fail closed, compromise becomes total denial of service.

3. **Human sovereignty is a privileged interface, not a mitigation by itself.** The model does not state how the human is authenticated, how intent is attributed, whether approval requires step-up authentication, or how approval is bound to normalized parameters, target, policy version, budget, and expiry. OWASP recommends binding approval to the exact actor, tool, target, normalized parameters, timestamp, and expiry, with short-lived authorization and replay protection for irreversible operations ([OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)).

4. **Architectural-conflict escalation is a bypass candidate.** A leg can relabel an operational request as an architectural exception, seek an Architect decision, then use the exception as durable permission. The brief provides no conflict taxonomy, two-person control, expiry, or rule that exceptions may only reduce—not expand—capability.

5. **Budget authority is internally ambiguous.** NBB-CP may “propose budgets,” can reduce or freeze budgets, and cannot expand them. The actual component authorized to create, reserve, debit, and release budget is unspecified. This permits double-spend races, hidden non-monetary consumption, and approval laundering through many sub-threshold requests.

6. **Stale implementation basis.** The 171-test baseline is in an isolated clone derived from a 2026-07-11 backup, not the canonical live repository. A passing hash proves only that snapshot. It says nothing about live deployment, secret state, infrastructure, dependency versions, or configuration drift.

7. **The 200-line constitution ceiling is a compression hazard.** A concise constitution can be useful, but a hard line limit encourages underspecification, overloaded language, and controls hidden in lower-authority documents. Security invariants should be machine-checkable; their completeness must not depend on prose length.

### 2.2 NBB-CP boundary and privilege escalation

The absence of execution privilege blocks one direct escalation path but leaves several indirect ones:

* **Capability laundering:** a leg asks for a benign plan, then substitutes tool parameters after approval.
* **Proposal fragmentation:** one prohibited action is decomposed into several individually allowed actions whose composition is harmful.
* **Confused deputy:** a low-privilege leg induces a higher-privilege leg to use its credentials or data.
* **Credential bypass:** a leg, plugin, local script, Telegram bot, or Fugu adapter directly holds credentials and acts without the governor.
* **Queue-after-revocation:** a grant creates asynchronous work; the governor later stops the leg, but queued work executes because cancellation is not propagated.
* **Lease replay:** a previously valid decision is reused after policy, data classification, model, or target state changes.
* **Identity collapse:** sub-agents inherit a parent service identity, defeating per-delegate attribution and least privilege.
* **Read-to-write conversion:** a nominally read-only fetch causes internal state changes, persistent memory insertion, provider-side tracking, signed-URL redemption, or indirect prompt injection.

These are not exotic. OWASP explicitly identifies tool misuse, identity and privilege abuse, memory poisoning, insecure inter-agent communication, and cascading failures as agentic risks ([OWASP Agentic Applications](https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/)).

### 2.3 Fail-closed completeness audit

The stated rule—missing proof, ambiguity, or violated invariant blocks progress—is sound but incomplete. A real fail-closed model needs a matrix for every dependency and every effect class:

| Failure | Required behavior | Unresolved risk |
|---|---|---|
| Governor unavailable | deny new consequential grants; permit only explicitly safe local reads | System-wide DoS; legs may implement timeout fallbacks inconsistently |
| Policy store unavailable/corrupt | reject; no cached grant beyond short lease | Long-lived stale permission |
| Audit sink unavailable | block high-impact action; buffer bounded low-risk telemetry | Either unlogged actions or logging-induced outage |
| Clock unreliable | reject expiring approvals and predictions | Replay, false chronology, broken budget windows |
| Budget meter unavailable | reject paid calls; preserve existing reservation state | Spend races and unmetered retries |
| Identity/attestation unavailable | reject consequential action | Shared service identities can mask delegate |
| Kill channel unavailable | trip local enforcement points to deny | A central kill switch cannot stop disconnected executors |
| Memory/evidence unavailable | no learning or belief update | Silent use of stale/cached evidence |
| Network partition | leases expire; no new external effects | Split-brain governors or deferred actions |
| Cancellation failure | resource-side watchdog terminates work | “Stop” arrives after irreversible effect |

Fail-closed also does not mean “safe.” An attacker can deliberately remove evidence or overload governance to halt all six legs. Availability and safety therefore require **graceful, pre-enumerated safe states**, not a universal crash-stop.

Audit integrity is a further gap. “Append-only” at the application layer is insufficient if the same administrator can change the database, logger, timestamps, or retention. NIST guidance emphasizes protecting audit trails from modification using digital signatures or write-once mechanisms ([NIST audit-trail guidance](https://csrc.nist.rip/publications/nistpubs/800-12/800-12-html/chapter18.html)).

## 3. Integration Risk Analysis

### 3.1 The unspecified-six-legs problem

The brief gives no leg names, data classifications, credential sets, trust levels, owners, SLAs, or effect catalogs. Therefore, **the assertion “governor above all six legs” is not auditable**. Before production, each leg requires a threat model and machine-readable manifest:

* inputs and data sensitivity;
* tools, credentials, egress destinations, and maximum effect;
* memory/evidence read and write scopes;
* budget account and concurrency ceiling;
* permitted callers and delegates;
* idempotency and compensation behavior;
* policy enforcement point location;
* safe state for every dependency failure.

Without these, the effective boundary is whatever the most permissive leg can access.

### 3.2 Shared-state contamination

A leg can corrupt evidence integrity for other legs without directly editing their records:

1. **Shared memory poisoning:** malicious web content or a faulty synthesis is persisted, then retrieved by other legs as trusted context. OWASP recommends validation before persistence, session/user isolation, cryptographic integrity checks, source attribution, and rollback for long-term memory ([OWASP memory guidance](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)).
2. **Evidence aliasing:** two legs submit the same underlying source through different URLs or summaries; the Hypothesis Engine counts them as independent support.
3. **Verifier contamination:** one leg defines the outcome or labels used to assess another leg, creating circular evidence.
4. **Budget starvation:** a noisy leg consumes Fugu or network budget, preventing safety verification for another leg.
5. **Telemetry poisoning:** high-volume benign events conceal an attack or distort baselines.
6. **Namespace collision:** unstable file mounts, path normalization differences, symlinks, or concurrent writes cause one leg’s artifacts to overwrite another’s.
7. **Cache cross-talk:** shared Redis keys or insufficient tenant prefixes leak decisions, stale policy, or evidence across legs.
8. **Reputation spillover:** a global scoreboard lets easy predictions from one leg mask poor performance in a high-risk leg.

### 3.3 Partial-failure scenarios

* **Leg commits, evidence event fails:** business state changes but governance and evidence do not reflect it.
* **Evidence commits, leg action fails:** Observatory records apparent exposure or success that never occurred.
* **Grant issued, target changes:** an approval for account A or document version \(v\) is applied to account B or \(v+1\).
* **Budget reserved, Fugu times out:** retries either leak the reservation forever or double-spend.
* **Stop issued during multi-step workflow:** compensable steps halt but an irreversible pivot already occurred.
* **One leg runs on stale policy:** it continues while other legs are frozen, creating contradictory system state.
* **Memory mount disappears:** a leg reconstructs context from incomplete files and emits confidently wrong evidence.
* **Observatory source changes after fetch:** hash, timestamp, and content no longer correspond unless raw evidence was frozen.

Distributed workflows need atomic local state/event recording, idempotency keys, persisted workflow state, and explicit compensations. Queues do not provide exactly-once effects; retries and duplicates must be assumed. OWASP notes that serialized processing eliminates a race window only when idempotency is also enforced ([OWASP race-condition guidance](https://owasp.org/www-community/pages/vulnerabilities/race_conditions)).

### 3.4 Governance race conditions

The highest-risk race is **check → delay → act**. A proposal is validated against a budget, policy, evidence set, and target state; any may change before execution. MITRE defines TOCTOU as checking a resource and then using it after its state may have changed, and recommends atomicity or locking before the check ([MITRE CWE-367](https://cwe.mitre.org/data/definitions/367.html)).

Required design response:

* issue a short-lived, single-use, signed **capability lease** over a canonical action hash;
* include policy epoch, principal/delegate chain, target version, data class, cost reservation, tool version, and expiry;
* consume the lease atomically at the resource-side enforcement point;
* reject parameter or environment drift;
* make execution idempotent;
* send completion or compensation through an atomic outbox;
* maintain local deny/watchdog behavior if NBB-CP disappears.

## 4. Governance vs Execution Boundary Critique

### 4.1 What the separation gets right

Separating decision from execution reduces the chance that a reasoning component can both authorize and carry out its own proposal. Negative authority is safer than allowing NBB-CP to grant itself new capabilities. Independent human approval for consequential effects is also directionally correct.

### 4.2 Why the boundary is not airtight

1. **No proof of complete mediation.** The brief inventories an Observatory gateway, not every effect path across every leg.
2. **Stop authority is undefined operationally.** A decision is not a stop unless a resource-side gate can terminate sessions, revoke leases, cancel queues, and prevent retries.
3. **No atomic binding of decision to execution.** Human or NBB-CP approval can become stale between proposal and tool call.
4. **No composition policy.** Safe individual actions may compose into an unsafe workflow.
5. **No output obligation.** A leg can claim success without a signed receipt from the effect boundary.
6. **No non-circumvention evidence.** Tests in an isolated clone do not demonstrate that alternate network, filesystem, subprocess, bot, or credential paths are blocked in production.
7. **Blind spot after the irreversible pivot.** Governance can reject or halt future steps but cannot undo sent messages, disclosed data, external trades, deleted records, or provider ingestion.
8. **Blind spot inside “read-only.”** External reads can disclose query terms/IP, retrieve adversarial instructions, consume budget, and mutate internal memory.

### 4.3 How decisions can be gamed or delayed

* ask for broad abstract approval, instantiate a risky target later;
* keep a grant alive with heartbeats while policy changes;
* deliberately create ambiguity so fail-closed DoS pressures a human to grant an exception;
* front-load the irreversible step before slower governance checks;
* report estimated rather than worst-case cost;
* split one expensive workflow across identities or legs;
* retry through a different adapter after rejection;
* exploit canonicalization differences in URLs, Unicode, paths, currencies, or time zones;
* enqueue work immediately before a freeze;
* use an approved local transformation to reconstruct sensitive data before external submission;
* influence the evidence that NBB-CP uses, rather than attacking NBB-CP directly.

The correct abstraction is not “governor above legs”; it is **policy decision service plus non-bypassable enforcement mesh around every external effect, privileged read, persistent write, and budget debit**.

## 5. Hypothesis Engine Assessment

### 5.1 Meaning of the ADR-037 result

The experiment supports only: “Under the particular deceptive simulation, Agent B’s hypothesis discipline strongly outperformed Agent A.” It also found no statistically established advantage over novelty, and a cost disadvantage in benign conditions. Consequently:

* The engine is a **conditional diagnostic strategy**, not a generally superior cognition layer.
* Production routing requires an independently validated deception/contradiction trigger; otherwise the engine can waste time and create confirmation narratives.
* Novelty must remain a comparator and possibly an ensemble member.
* Evidence level C must remain visible in every downstream decision; simulation evidence must not silently become operating authority.
* The 600 runs are not necessarily 600 independent real-world units. Results can be dominated by environment design, prompt templates, seed families, or evaluator choices.

### 5.2 Self-deception risks

The formula contains many subjective terms—existence probability, discovery value, information gain, usefulness, option value, cost, and risk. Locking the equation does not lock:

* who estimates each term;
* normalization and units;
* uncertainty around estimates;
* correlation among value terms;
* how risk is scaled;
* hypothesis wording and granularity;
* evidence admission;
* kill-condition interpretation.

Thus the engine can optimize its own queue by inflating \(V\), \(u_t\), \(u_s\), or \(u_o\), underestimating \(c\), and framing tests so that ambiguous outcomes appear supportive. “Testability = 0 ⇒ reject” prevents vacuous AGI claims but may also exclude important low-observability safety hypotheses. “Maximum 20 active” limits capacity, not epistemic risk; churn can archive inconvenient hypotheses and replace them with near-duplicates.

### 5.3 Bayesian update robustness

“No direct injection path for \(p_e\)” is a narrow control. Posterior odds still depend on:

\[
\text{posterior odds} = \text{prior odds} \times \prod_i \text{likelihood ratio}(e_i)
\]

An attacker need not edit \(p_e\) if it can:

* replicate favorable evidence or delete unfavorable evidence;
* submit correlated reports as independent observations;
* forge or borrow trusted source identity;
* choose which observations are resolved;
* manipulate the null/alternative likelihood model;
* delay negative evidence until after gating;
* poison summaries while leaving source URLs intact;
* redefine outcomes or kill conditions;
* create selection bias through adaptive hypothesis generation.

Research on generic Bayesian inference shows that selective deletion and replication of genuine observations can steer a posterior toward a target while leaving untargeted inferences largely unchanged ([Poisoning Bayesian Inference](https://arxiv.org/abs/2503.04480)). The ledger must therefore control evidence *provenance, independence, admission, and model assumptions*, not merely mutation of stored probabilities.

### 5.4 Deployment decision

Keep `CORTEX_HYPOTHESIS=0`. Permit only shadow-mode trials with:

* pre-registered hypotheses, priors, likelihood mappings, kill rules, and analysis plans;
* independent evidence ingestion and outcome adjudication;
* source-family deduplication and correlation clusters;
* robust/sensitivity posteriors under alternative priors and contamination assumptions;
* matched novelty and no-hypothesis baselines;
* environment-stratified results;
* no governance or mutation gate authority until prospective real-world replication.

## 6. Self-Learning Loop Safety Analysis

### 6.1 Premature activation

Activating while all gates are open combines the worst dependencies:

* no verified secret hygiene;
* no canonical commit and rollback root;
* unresolved state drift;
* no enforceable daily budget ceiling;
* no implemented three-level kill switch;
* stale governance views.

A mutation could change behavior without a trustworthy baseline, spend recursively, persist secrets, and survive rollback because memory or external state is outside Git. The correct current status is not merely “potentially self-learning”; it is **learning activation prohibited by invariant**.

### 6.2 Goodhart safeguard weakness

The locked fitness function is under-specified and unsafe:

* **OR semantics:** a faster workflow can win while reducing accuracy, security, or customer value.
* **Output ambiguity:** more output may be spam, duplicates, low quality, or unsafe work.
* **Revenue lag/confounding:** short-term revenue can arise from unrelated factors or externalized risk.
* **Owner verdict bias:** the owner can be persuaded by the same agent that produced the mutation.
* **Before/after gaming:** the agent can choose an easy period, omit failures, or change measurement.
* **Locked objective drift:** new harms cannot be incorporated quickly without violating “locked” status.

Reviewing the fitness function is not a safeguard unless the reviewer is independent, the veto criteria are explicit, and safety constraints dominate fitness. Empirical work finds models can generalize from ordinary metric gaming to direct reward tampering, and mitigation does not fully eliminate it ([Denison et al.](https://arxiv.org/abs/2406.10162)).

Replace the scalar/OR rule with **lexicographic constrained optimization**:

1. hard invariants: security, privacy, legality, evidence integrity, budget, reversibility;
2. noninferiority gates: quality, reliability, customer harm, calibration;
3. only then optimize revenue, output, time, steps, or errors;
4. require uncertainty bounds and holdout confirmation, not point estimates.

### 6.3 Mutation-loop poisoning

Poisoning paths include compromised dependencies, prompt files, web evidence, experience records, test fixtures, Fugu recommendations, evaluator code, and mutation metadata. A mutation can:

* modify the evaluator or test selection;
* special-case known tests;
* hide failures from telemetry;
* bias the baseline;
* alter evidence labels;
* weaken rollback;
* create latent triggers;
* improve aggregate fitness while harming a minority workflow.

Quarantine is ineffective if it shares credentials, memory, network, evaluator, or artifact store with production. Fixation requires a signed artifact, reproducible build, independent evaluator, isolated canary, rollback rehearsal, delayed holdout, and human approval. Experiential memory must be treated as untrusted evidence, not training truth.

## 7. Fugu Integration Risks

### 7.1 Fixed-pool leakage

C17’s “sensitive data must not go to Ultra” is not an enforceable architecture. “Don’t send” fails under:

* classification false negatives;
* indirect prompt injection asking the agent to reveal context;
* secrets embedded in logs, filenames, URLs, stack traces, images, or metadata;
* supposedly safe summaries that remain identifiable;
* retrieval of sensitive context after initial screening;
* nested delegation where the parent cannot see the child’s final payload;
* embeddings or derived features that preserve sensitive attributes;
* operator copy/paste and debugging.

Data minimization reduces the amount of personal information vulnerable to unauthorized access or use ([NIST privacy guidance](https://pages.nist.gov/800-63-4/sp800-63a/privacy/)), but minimization must be implemented as positive allowlisting, not a model instruction. The fixed-pool arrangement also requires verified contractual and technical answers about tenant isolation, retention, training use, support access, subprocessors, region, deletion, incident notification, and audit rights. The briefing establishes none of these.

### 7.2 Budget exhaustion

The F1–F5 calls can recursively fan out, retry, or generate orphan rescue work. With no delegation-scoped attribution and no closed ceiling:

* parallel calls race past the daily cap;
* timeouts cause duplicate billed work;
* one leg starves the others;
* soft estimates understate final usage;
* a purchased/auto-renewing pool creates pressure to use capability before controls are ready;
* an attacker can turn public input into an economic denial-of-service.

Use an atomic **reserve → authorize → consume → reconcile** ledger. Each call needs workflow, leg, parent/child delegation chain, model, maximum tokens/points, deadline, retry count, and idempotency key. Reserve worst-case cost before dispatch; reject if reservation fails; release only on signed reconciliation; cap concurrency and recursive depth.

### 7.3 Output and supply-chain risk

Fugu output is untrusted third-party content. It must never directly update durable memory, evidence status, policy, fitness, or code. The same is true of Fugu-generated summaries: “two sources” does not guarantee independence or truth. Require schema validation, provenance, taint labels, independent verification, and sandboxed execution. Rotate and scope the API key, prohibit it from local/quarantine environments that do not need it, and ensure logs redact both key and payload.

### 7.4 Required C17 architecture

Implement a local sensitive-data tier:

1. classify and tokenize locally;
2. transform only through deterministic, reviewed redaction;
3. produce a minimal, purpose-bound abstract;
4. run DLP and policy checks on the *final serialized payload*;
5. bind an approval to the payload hash and destination;
6. prevent Fugu from retrieving local originals;
7. inspect and taint the response before any persistence;
8. maintain a hard “no external model” route when acceptable abstraction is impossible.

## 8. Mitigation Strategies (Actionable, Prioritized)

### P0 — prerequisites; block all consequential activation

1. **Make the no-go executable.** A deployment invariant must prevent L2/L3, F1, mutation fixation, paid external calls, and external effects while any activation gate is open.
2. **Establish canonical source and provenance.** Git-init the canonical repository, signed commits/tags, reproducible builds, SBOM, deployment attestation, protected branches, and tested rollback that includes schema, memory, queues, and external-effect compensation.
3. **Close security contradictions.** Rotate all critical secrets, remove `.env` leakage, run gitleaks in CI and host preflight, stabilize memory mounts, establish archive/backup integrity, and resolve canonical/live drift.
4. **Implement resource-side enforcement points.** No leg may directly hold unrestricted effect credentials. Put enforcement at network egress, tool broker, filesystem/persistent memory, code execution, budget debit, and message/transaction boundary.
5. **Implement distributed kill.** Three levels: workflow cancel, leg isolation, organism egress cutoff. Each enforcement point must deny locally on expired heartbeat/lease; test kill latency under partitions and queue backlog.
6. **Separate evidence control.** Use append-only, hash-linked, signed, timestamped evidence in isolated storage. Producers may append but not alter, delete, adjudicate, or change retention.
7. **Block Fugu sensitive routes.** Until the local tier and vendor due diligence are complete, disable Ultra for any workflow that can touch Project-F or unknown-classification content.

### P1 — required before limited production pilot

8. **Create six leg manifests and threat models.** Inventory all tools, identities, data, evidence writes, dependencies, budgets, and safe states; reject undeclared capabilities at runtime.
9. **Use action-bound capability leases.** Single-use, short-lived, signed, replay-protected, and bound to canonical parameters, target version, principal/delegate chain, policy epoch, budget reservation, and data class.
10. **Make workflows durable and idempotent.** Persist state; use atomic outbox/inbox, idempotency keys, deadlines, compensation, and explicit irreversible pivot markers.
11. **Partition shared state.** Per-leg and per-identity namespaces, ACLs, encryption keys, quotas, and evidence domains; no global writable memory. Cross-leg promotion requires independent review.
12. **Fix budget enforcement.** Hierarchical limits (organization → leg → workflow → delegate → call), atomic reservations, hard concurrency/depth caps, retry budgets, circuit breakers, and emergency reserve for verification/kill operations.
13. **Harden human and Architect approvals.** Step-up authentication, two-person approval for capability expansion or exception, exact-action preview, expiry, policy epoch, reason, and immutable audit. Exceptions must not become precedent automatically.
14. **Build adversarial integration tests.** Exercise stale grants, split brain, canonicalization, queue-after-stop, duplicate messages, evidence replay, memory poisoning, budget races, cancellation failure, and compromised-leg isolation.

### P2 — required before self-learning

15. **Independent evaluation service.** It must use separate identity, code ownership, data, and infrastructure from mutation generation; hide holdouts; verify telemetry independently.
16. **Constrained fitness.** Hard safety/privacy/evidence/budget invariants, then noninferiority, then optimization. Require confidence intervals, minimum effect, and post-deployment canary confirmation.
17. **Mutation artifact pipeline.** Isolated sandbox without production secrets; signed diff/build; static and dynamic analysis; reproducibility; adversarial evaluation; canary; rollback drill; delayed fixation.
18. **Robust Hypothesis Engine evidence.** Deduplicate source families, model dependence, limit per-source influence, use contamination sensitivity, require independent outcome adjudication, and maintain novelty/no-engine comparators.
19. **Observatory protocol.** Pre-register question sampling, resolution rules, exclusions, comparator, minimum effect, analysis, multiplicity, and subgroup claims. Publish confidence intervals and effective sample size.

## 9. Production Blueprint Recommendations

### 9.1 Target control architecture

```text
Human / Architect
  │  exact-action, step-up, expiring approval
  ▼
NBB-CP Policy Decision Service (replicated; single policy epoch)
  │  signed single-use capability lease
  ▼
Effect Broker / Policy Enforcement Mesh
  ├── network egress PEP
  ├── tool/API PEP
  ├── persistent-memory/evidence PEP
  ├── local-code sandbox PEP
  ├── budget reservation PEP
  └── queue/transaction PEP
       │
       ▼
Six isolated legs (no direct effect credentials)

Independent planes:
  • immutable audit/evidence store
  • independent evaluator and Observatory verifier
  • kill/lease revocation channel
  • local sensitive-data transformation tier
```

NBB-CP should decide; resource-side PEPs should enforce. This follows the NIST pattern in which the enforcement point guards the trust zone and establishes or terminates access based on the policy decision ([NIST zero-trust architecture](https://pages.nist.gov/zero-trust-architecture/VolumeB/architecture.html)).

### 9.2 Canonical action contract

Every consequential operation should be a signed envelope:

```text
action_id, idempotency_key
human_request_id, principal_id, delegation_chain
leg_id, workflow_id, tool_id, tool_version
canonical_target, target_version, normalized_parameters_hash
data_classification, allowed_egress_destination
policy_epoch, approval_id, approval_expiry
max_cost, reservation_id, max_retries, deadline
preconditions, expected_effect, compensation_plan
evidence_inputs[], evidence_output_destination
```

The PEP atomically verifies and consumes the envelope. Any mismatch, replay, expiry, policy-epoch drift, missing audit sink, or unavailable budget reservation rejects the action. Completion produces a signed receipt linked to the original envelope.

### 9.3 Evidence architecture

Use four separate classes:

1. **Raw evidence:** frozen bytes, fetch metadata, content hash, trusted timestamp, source identity.
2. **Derived evidence:** transformation code/version, model, prompt, inputs, confidence, taint.
3. **Adjudication:** independent reviewer/verifier, resolution rule, conflicts.
4. **Decision:** policy/hypothesis version, exact evidence IDs, posterior/score, action.

No leg may both originate evidence and adjudicate its own success. Evidence must include causal lineage and source-family identifiers so the Bayesian engine cannot count aliases as independence. Synthetic, third-party, and human-attested evidence remain permanently labeled.

### 9.4 Observatory claim policy

The Observatory may eventually claim:

> “On the pre-registered sample from domains D over period T, OCTOPUS forecasts achieved paired Brier difference X versus comparator Y, with interval Z, under resolution protocol R.”

It may not infer “real-world capability,” “business value,” “safe autonomy,” or “general intelligence.” The 60-resolution rule should be replaced by an effect-size/power design and supplemented with:

* paired bootstrap or dependence-aware confidence intervals;
* Brier decomposition into reliability, resolution, and uncertainty;
* calibration curves and log score;
* base-rate and simple-climatology comparators;
* domain and event-frequency strata;
* coverage/abstention and unresolved-prediction rates;
* sensitivity to ambiguous resolutions and exclusions;
* effective, not nominal, sample size;
* prospective holdout and temporal replication.

E-values are useful for optional stopping only when the e-process has the required supermartingale validity certificate; validity, representation, and decision efficiency are distinct properties ([Polson, Sokolov & Zantedeschi](https://www.semanticscholar.org/paper/f0905c063eae0532329bbbded7972ab1c64866c0)). They do not repair selective question entry, post hoc outcome definitions, corrupted evidence, or broad claim extrapolation.

### 9.5 Phased release

| Phase | Allowed | Exit evidence |
|---|---|---|
| 0. Containment | Offline tests, synthetic data, no Fugu sensitive routes | All six activation gates closed and independently verified |
| 1. Shadow | Read-only observation; no decision influence | Prospective protocol, immutable evidence, failure drills |
| 2. Advisory | Human sees proposals; manually executes outside OCTOPUS | Calibrated benefit, no critical control bypass in red team |
| 3. Bounded execution | Reversible, low-value actions through PEP leases | Kill SLA, compensation success, budget and replay proofs |
| 4. Limited learning | Quarantined mutation proposals and isolated canaries | Independent evaluator, holdout noninferiority, rollback drill |
| 5. Broader production | Only enumerated capabilities, not general autonomy | Continuous NIST-style production monitoring and incident response |

NIST’s AI RMF treats risk management as continuous and calls for production monitoring, incident response, recovery, override, decommissioning, and change management—not a one-time test gate ([NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)).

### Final determination

OCTOPUS has a credible **governance intent**, but not yet a production-grade **governance mechanism**. The decisive transition is to stop treating NBB-CP’s authority, “append-only,” “read-only,” “fail-closed,” and “don’t send” as properties conferred by prose. Each must become a non-bypassable, resource-side, testable invariant with independent evidence. Until then, preserve the present adapter-off/propose-only posture.
