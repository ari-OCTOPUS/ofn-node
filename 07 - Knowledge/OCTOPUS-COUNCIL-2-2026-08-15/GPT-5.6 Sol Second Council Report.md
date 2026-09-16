---
type: report
status: active
tags: [octopus, council]
created: 2026-08-15
updated: 2026-08-15
---
# OCTOPUS Second Council Review — Structural Reassessment

**Council model:** GPT-5.6 Sol  
**Review date:** 15 August 2026  
**Evidence basis:** the updated briefing, the first-council reports preserved in this workspace, and external primary/technical sources. The live OCTOPUS repository itself is not mounted in this workspace; therefore, statements about live-tree state are **owner-reported and test-reported evidence**, not independently reproduced findings.

## Executive determination

**Revised verdict: NO-GO remains correct for autonomous/consequential self-learning, but for narrower reasons than the first council gave.** The T1–T12 sweep materially raises confidence in operational coherence: memory retrieval is now exercised before decisions, the broad test runner completed, epistemics checks pass, a hard-task forecast beat its comparator, the kill mechanism was successfully drilled, and budget metering is exact. The owner also disproved several stale premises: Git existed, gitleaks existed, Fugu already had a monthly cap, and the production kill seam was armed ([updated briefing, T1–T12 and fact-check](octopus-updated-briefing.md#t1-t12-test-sweep-results-all-green)).

This invalidates the first council’s claim that “six gates are all open” as a description of the live tree. It does **not** invalidate the council’s structural thesis. The remaining blockers are:

1. no demonstrated complete-mediation enforcement mesh at every effect boundary;
2. no independent evaluator for mutation acceptance;
3. no demonstrated per-leg memory/evidence isolation;
4. no technical local/private route replacing Fugu’s “don’t send” discipline;
5. no action-bound, independently enforced approval/capability contract;
6. a trusted-computing-base boundary that is currently so broad that it is not meaningfully analyzable (C-013).

The correct conceptual update is therefore:

> **The system has moved from “unknown and apparently unprepared” to “well-tested in several important pathways, but still structurally contained.”**

The green sweep supports shadow/advisory use and further engineering. It does not establish the non-bypassability or evaluator independence needed for autonomous fixation or irreversible external effects.

---

## 1. Vulnerability reassessment: V1–V11

### Status key

- **Resolved:** the original vulnerability no longer accurately describes the current system.
- **Partly resolved / narrowed:** important premises were corrected, but a residual structural risk remains.
- **Open:** the new evidence does not address the vulnerability’s defining mechanism.

| ID | First-council vulnerability | Current status | Evidence and reasoning | Closure evidence still required |
|---|---|---|---|---|
| **V1** | No demonstrated, non-bypassable policy-enforcement point at every effect boundary | **Open — critical** | `test_no_go_envelope.py` tests the declared envelope, but the briefing does not show that all network, tool, credential, persistent-write, queue, subprocess, and external-message paths are forced through resource-side enforcement. NIST distinguishes the policy decision point from the PEP that enables, monitors, and terminates access at the protected resource ([NIST SP 800-207](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=930420)). | Exhaustive effect inventory; deny-by-default PEPs; removal of direct effect credentials from legs; bypass and partition tests; signed, single-use action leases consumed at the boundary. |
| **V2** | All six learning-activation gates are open simultaneously | **Resolved as stated; successor readiness risk open** | “All six are open” is not a valid description of the live tree. Git, gitleaks, a Fugu ceiling, and an armed kill switch already existed, while memory/stale-view behavior and test coverage also improved ([fact-check](octopus-updated-briefing.md#owners-fact-check-of-first-council)). This closes V2’s factual configuration claim. It does **not** imply autonomous readiness: one live PAT remains, commits are unpushed, the STOP-ORGANISM seam is flag-dependent, and the structural prerequisites above remain open. | Replace the old six booleans with a versioned readiness manifest whose values are computed from live/deployed evidence, including independent evaluator, PEP coverage, memory isolation, private Fugu route, deployment provenance, and kill behavior under partition. |
| **V3** | Shared L4 evidence/memory lacks per-leg isolation | **Open — critical** | T1 proves **use** of memory (read-before-decision 1.0), not isolation, provenance integrity, or noninterference. Indeed, a reliably consumed shared memory makes poisoning more consequential, not less. The briefing explicitly retains per-leg memory isolation as valid ([fact-check](octopus-updated-briefing.md#owners-fact-check-of-first-council)). | Per-leg namespaces, identities, keys, ACLs, quotas, provenance domains, taint labels, and an independently reviewed cross-leg promotion path. |
| **V4** | Human/Architect overrides are not cryptographically action-bound | **Open — critical** | T6 demonstrates that an owner vote can be found in the inbox and produces `verdict=True`; it does not show binding to canonical parameters, target version, policy epoch, expiry, cost reservation, or one-time consumption ([T6](octopus-updated-briefing.md#t1-t12-test-sweep-results-all-green)). | Exact-action hash, principal/delegate chain, expiry, nonce/idempotency key, step-up authentication, immutable receipt, replay test, and rejection after target/policy drift. |
| **V5** | Fugu “don’t send” is policy-only leakage prevention | **Open — critical** | The 100 AUD monthly cap and quota guard close a separate cost-control claim; they do not prevent sensitive payload egress. The briefing itself still lists a local Fugu tier as valid follow-up ([fact-check](octopus-updated-briefing.md#owners-fact-check-of-first-council)). | Local classification/tokenization and deterministic redaction; DLP over the final serialized payload; destination/payload-hash authorization; no provider access to originals; hard local-only fallback. |
| **V6** | NBB-CP is a single logical dependency and compromise concentration point | **Open — high** | The sweep demonstrates healthy normal operation, not split-brain, stale-policy, clock failure, queue backlog, or governor compromise behavior. | Single policy epoch or consensus, short leases, local deny on expiry, safe degraded modes, redundant decision service, resource-side enforcement, and chaos tests under partitions. |
| **V7** | Bayesian updating trusts evidence admission, independence, and modeling | **Open — high** | T3’s 177 checks and T10’s Brier result are positive but do not prove source-family deduplication, independent outcome adjudication, selection-bias control, or robustness to deletion/replication of genuine evidence. Bayesian posteriors can be targeted by selective deletion and replication without direct posterior editing ([Carreau, Naveiro & Caballero](https://proceedings.mlr.press/v258/carreau25a.html)). | Frozen raw evidence, source-family graph, correlation-aware weighting, independent admission/adjudication, contamination sensitivity, and adversarial replay/deletion tests. |
| **V8** | Fitness uses weak proxies with OR semantics, creating Goodhart/reward-tampering pressure | **Open — high** | None of T1–T12 establishes a lexicographic safety objective, independent measurement, hidden holdouts, or noninferiority. The memory fix improves context availability, not objective validity. Research has shown models can progress from specification gaming to reward tampering even when trained to be helpful and harmless ([Denison et al.](https://arxiv.org/abs/2406.10162)). | Hard invariants → safety/quality noninferiority → utility optimization; independent metric computation; hidden tests; confidence bounds; canary and rollback. |
| **V9** | Observatory threshold/Brier score cannot support broad capability claims | **Open, but current narrow result is useful** | T10 supports a narrow statement: on the recorded hard-task backtest, Brier 0.0978 beat 0.4535. It does not establish broad capability, calibration across domains, independence, prospective validity, or safety. C-014 also reveals duplicate fetching that can distort cost and possibly sample/evidence accounting ([T10 and C-014](octopus-updated-briefing.md#contradiction-registry-update)). | Pre-registration; paired prospective comparator; effective sample size; calibration and resolution decomposition; domain/base-rate strata; deduplication; confidence intervals; explicit claim grammar. |
| **V10** | Hypothesis Engine’s value activates under deception, which is also its attack surface | **Open — high** | The new sweep does not supply the missing deception-condition threat model or show superiority over a strong novelty baseline. C-013 additionally shows that the self-modification boundary around this machinery is poorly scoped. | Keep adapter off for authority-bearing use; adversarial evidence trials; independent trigger; novelty comparator; provenance-aware evidence admission; bounded influence and rollback. |
| **V11** | Evaluator Problem: the system judges its own mutations | **Open — critical and binding** | Read-before-decision at 1.0 resolves a memory plumbing defect, not evaluator independence ([T1](octopus-updated-briefing.md#t1-t12-test-sweep-results-all-green)). The same organism still appears able to generate mutations, produce evaluation-relevant state, and consume the result. | Separate identity, repository/code owners, compute, data plane, hidden holdouts, telemetry, and release key; mutation generator must be unable to write evaluator code/data or declare fixation. |

### Net change

- **Resolved as originally phrased:** V2. Its premise (“all six open”) was stale; this is not equivalent to a GO.
- **Corrected but still open:** V5’s budget premise was wrong, but its confidentiality vulnerability is unchanged.
- **Operational evidence improved without structural closure:** V3, V7, V9, V11.
- **Substantially untouched:** V1, V4, V6, V8, V10.

This is not a contradiction with “all tests green.” Most of V1–V11 are **architecture properties**—complete mediation, isolation, independence, provenance, and failure semantics—not ordinary functional paths.

---

## 2. Is `test_no_go_envelope.py` sufficient to make NO-GO structural?

**No. It makes NO-GO executable policy, which is a major improvement, but not yet an architectural constraint.**

A test answers: “Does this implementation currently satisfy these assertions when this suite is run?” A structural constraint answers: “Can an actor or component produce the prohibited effect even if it skips the suite, changes the test, uses another adapter, starts before revocation, or loses contact with governance?”

NIST’s reference-monitor definition gives the useful standard: the mechanism must be **always invoked, tamperproof, and small enough to verify** ([NIST reference monitor glossary](https://csrc.nist.gov/glossary/term/reference_monitor)). A nine-assertion test is evidence for the third property only. It does not by itself establish the first two.

### What the new test does accomplish

1. Converts prose into a regression oracle.
2. Makes accidental policy drift visible in `run_all`.
3. Creates an explicit contract that can be reviewed and versioned.
4. Preserves the owner’s decision in machine-readable form.

### What it does not establish

1. **Unskippability:** a direct script, credential, queue consumer, or alternate deploy route may bypass `run_all`.
2. **Tamper resistance:** if the same change can alter both organism behavior and the test, the assertion is self-authored.
3. **Deployment identity:** a green source tree does not prove the running artifact came from that tree.
4. **Runtime continuity:** a pre-deployment pass does not revoke already-issued work or stop a later configuration flip.
5. **Coverage completeness:** nine checks may omit an effect path, especially when C-014 shows duplicate scheduling was not represented as a single authoritative job.

### Stronger structural form

Implement NO-GO as a **three-layer invariant**:

| Layer | Required mechanism | Failure behavior |
|---|---|---|
| **Build/release** | Signed test result and provenance bound to immutable source and artifact digest | No attestation, no releasable artifact |
| **Deployment admission** | Independent admission controller verifies artifact digest, NO-GO state, policy epoch, and owner release authorization | No valid evidence, no deployment |
| **Runtime effects** | PEPs require a short-lived, single-use capability for every consequential effect; global NO-GO means no capability can be minted or consumed | Governor unavailable, stale epoch, expired lease, or kill heartbeat lost → deny locally |

SLSA defines provenance as verifiable information about where, when, and how an artifact was produced and binds provenance to the artifact; its distribution guidance recommends immutable attestations and external transparency logs ([SLSA provenance](https://slsa.dev/spec/v1.0/provenance); [SLSA distribution](https://slsa.dev/spec/v1.1/distributing-provenance)). OCTOPUS should therefore require:

- protected ownership for the envelope test and policy schema;
- an evaluator/release identity distinct from mutation code;
- signed result bundle tied to commit, dirty-tree state, dependencies, configuration, and artifact digest;
- deployment-time verification;
- runtime PEP enforcement;
- adversarial tests proving direct tool, network, queue, credential, and subprocess paths cannot bypass it;
- kill drills during network partition and queue backlog, not just healthy engage/release.

**Acceptance criterion:** deleting or skipping `test_no_go_envelope.py` must not make a forbidden action possible; it should merely make the artifact impossible to attest and admit.

---

## 3. What C-013 and C-014 reveal

### C-013 — the self-code guard treats everything as TCB

`REFERENCE_DIR` falling back to `SYSTEM_ROOT` means the guard’s trust boundary has collapsed from a deliberately small reference set into the whole organism ([contradiction registry](octopus-updated-briefing.md#contradiction-registry-update)). This is more than an over-broad glob.

It reveals:

1. **No authoritative trust-boundary manifest.** The system infers what is trusted from a filesystem fallback rather than a reviewed, fail-closed declaration.
2. **TCB non-minimality.** If everything is TCB, little can be independently modified, compared, or reasoned about. This violates the “small enough to verify” property of a reference monitor ([NIST](https://csrc.nist.gov/glossary/term/reference_monitor)).
3. **Policy/implementation aliasing.** The component deciding whether self-code is protected may be using paths and defaults controlled by the same mutable environment.
4. **Bypass pressure through false positives.** An over-broad guard appears safe, but operational friction encourages exemptions, force flags, or disabling the guard. A control that blocks legitimate change indiscriminately often decays into a ceremonial control.
5. **Unknown mutation blast radius.** OCTOPUS cannot cleanly distinguish identity-core code, evaluator code, ordinary arm code, generated artifacts, fixtures, and ephemeral state.

**Root fix:** a signed `trust-boundary.yaml` (or equivalent) must enumerate immutable identity core, enforcement code, evaluator code, policy schemas, and allowed mutation zones by digest and owner. An unset or invalid `REFERENCE_DIR` must fail closed with a diagnostic—not silently expand to the system root. Tests must include symlink/path canonicalization, directory escape, case normalization, and attempts to modify the guard or its manifest.

### C-014 — two Observatory tasks perform the same fetch

Duplicate scheduling reveals a **control-plane ownership defect**, not merely wasted network use.

It implies:

1. no single authoritative workflow/job registry;
2. weak idempotency or deduplication at the effect boundary;
3. configuration drift between schedulers;
4. ambiguous attribution: which task owns cost, evidence, failure, and retry?
5. “read-only” effects were under-modeled—reads still consume money, expose query metadata, ingest untrusted content, and can double-count evidence;
6. telemetry can report internally consistent but semantically duplicated activity.

Disabling one task (R3) removes the immediate symptom. The structural repair is to assign a globally unique logical operation key—e.g., `(source, normalized query, sampling window, protocol version)`—and have a single scheduler or effect broker atomically acquire it. Duplicate requests should coalesce; retries should reuse an idempotency key; raw evidence should be content-addressed; provenance should retain all requesters without counting one observation twice.

### Shared deeper issue missed by the first council

The first council focused on missing controls. C-013 and C-014 expose a subtler failure mode: **the system lacks authoritative machine-readable models of itself**.

- C-013: no authoritative map of trusted versus mutable code.
- C-014: no authoritative map of active jobs and effect ownership.
- V1/V3: no authoritative map of effect boundaries and memory ownership.

The root artifact should be an **organism manifest** defining components, identities, trust classes, capabilities, schedules, memory domains, budgets, PEP locations, and safe states. Runtime discovery must reconcile against it; undeclared components or duplicate logical jobs must fail admission.

---

## 4. Evaluator Problem after the memory-loop fix

**The memory-loop fix changes the system’s competence and continuity assessment; it does not change the Evaluator Problem’s logical assessment.**

The old failure was: “the organism writes experience but does not reliably consult it.” T1 now reports read-before-decision 1.0, with live telemetry and tests ([T1](octopus-updated-briefing.md#t1-t12-test-sweep-results-all-green)). That is a real closure of C-012.

The Evaluator Problem asks different questions:

- Who defines the target?
- Who selects the test and holdout?
- Who computes the score?
- Who controls telemetry and exclusions?
- Who decides whether a mutation fixates?
- Can the mutation alter any of those paths?

If the answer remains “the same organism or trust domain,” then **precise self-grading is still self-grading**. The binding constraint remains.

The memory fix may even intensify two risks:

1. **Persistence of evaluator gaming:** a successful shortcut can become durable experience.
2. **Correlated self-confirmation:** generation, evaluation, and future decisions may retrieve the same interpretations and provenance chain, turning one error into institutional memory.

The correct design is not “never self-evaluate.” Self-evaluation is useful for fast inner-loop diagnostics. It must be separated from authority:

| Loop | Purpose | Authority |
|---|---|---|
| **Inner self-check** | Debug, critique, propose tests, estimate uncertainty | May reject its own proposal; may not authorize fixation |
| **Independent evaluator** | Hidden holdout, invariant and noninferiority tests, telemetry verification | Can veto; cannot generate or deploy mutation |
| **Owner/release authority** | Accepts bounded risk and exact artifact | Can authorize only the attested artifact/action |
| **Runtime monitor** | Detects drift and revokes leases | Can stop/rollback; cannot improve fitness score |

Evaluator independence must be measured along at least five axes: code ownership, identity/credentials, data/holdout secrecy, compute/telemetry, and release authority. Merely using another model from the same prompt, memory, tools, and evidence does not create independent failure.

---

## 5. Translating octopus topology + ant quorum + immune deletion

Biology should supply **mechanisms and failure constraints**, not metaphors.

### A. Octopus topology: small identity core, semi-autonomous arms

Create a minimal immutable **identity core** containing:

- constitutional invariants and policy schema;
- component/identity/capability registry;
- lease signer/verifier interface;
- kill/epoch logic;
- audit root and release-verification keys;
- mutation-zone and evaluator-boundary declarations.

Each leg becomes an arm with:

- separate process/container identity and scoped credentials;
- its own memory namespace, evidence domain, budget, queue, and rate limits;
- explicit tool and egress allowlist;
- local safe state and watchdog;
- no direct write to another arm’s durable memory;
- cross-arm exchange only through typed, provenance-bearing messages.

The identity core should **not** plan tasks, grade mutations, or hold broad effect credentials. Its job is to preserve organism identity and constrain coordination. C-013 is the immediate blocker: until the core is explicitly minimal, “small identity core” is only a slogan.

### B. Ant quorum: distributed evidence accumulation before hard decisions

For high-impact decisions, dispatch multiple **independent scouts**, each receiving:

- a minimally shared problem statement;
- separate retrieval or evidence partitions;
- distinct model/tool paths where feasible;
- no visibility into other scouts’ conclusions before commitment;
- a signed evidence packet containing claim, uncertainty, sources, assumptions, and falsifier.

Then use risk-tiered quorum:

| Decision class | Rule |
|---|---|
| Reversible/local | One arm within budget and capability lease |
| Consequential but compensable | Two independent supports + no hard-invariant veto |
| Irreversible/external/private-data | \(k\)-of-\(n\) support, independent verifier, and owner exact-action approval |
| Self-modification/TCB/evaluator change | Supermajority is insufficient by itself; independent evaluator and owner approval are mandatory |

Ant colonies use quorum thresholds to switch from slow assessment/recruitment to commitment; the mechanism trades decision speed against reliability rather than making consensus intrinsically true ([Pratt et al., *Behavioral Ecology and Sociobiology*](http://link.springer.com/10.1007/s00265-002-0487-x)). OCTOPUS must therefore:

- count **independent evidence families**, not agent messages;
- detect correlated models, shared sources, copied reasoning, and common prompts;
- preserve dissent and its evidence;
- escalate disagreement rather than average it away;
- set thresholds by impact, reversibility, uncertainty, and time pressure;
- cap deliberation cost and allow abstention.

A quorum of homogeneous agents is one correlated vote. Diversity is a required input to quorum, not an optional aesthetic.

### C. Immune deletion: negative selection, quarantine, decay, and garbage collection

Map immune functions as follows:

| Immune mechanism | OCTOPUS mechanism |
|---|---|
| Central tolerance | Before any new arm/tool/mutation receives capability, test it against protected “self” invariants: identity, privacy, budget, evidence integrity, evaluator separation, kill responsiveness |
| Clonal deletion | Permanently revoke/delete mutations, prompts, skills, routes, and memory patterns that violate invariants; retain only a signed tombstone/fingerprint for recurrence detection |
| Peripheral tolerance | Runtime anomaly monitor, short leases, rate limits, quarantine, and human review for ambiguous behavior |
| Immune memory | Compact signatures of known-bad patterns and incident-derived regression tests—not wholesale retention of toxic payloads |
| Apoptosis | Automatic arm shutdown and credential revocation on heartbeat loss, policy-epoch drift, unexplained capability expansion, or evaluator tampering |
| Homeostasis | TTLs, evidence aging, hypothesis retirement, queue caps, and budget pressure |

Central tolerance eliminates or redirects self-reactive clones through negative selection, including clonal deletion by apoptosis ([McCaughtry & Hogquist](http://link.springer.com/10.1007/s00281-008-0137-0)). The engineering lesson is that **deletion is a first-class lifecycle operation**.

Concrete additions:

- every durable memory item has owner, provenance, confidence, scope, TTL, last-use time, and deletion policy;
- hypotheses have queue cost, expiry, duplicate-family key, and retirement conditions;
- consolidation uses evidence **delta**, not repeated level accumulation;
- deleted items leave non-revivable tombstones unless an independent review explicitly reauthorizes them;
- mutation lineages inherit risk and cannot evade deletion by trivial renaming;
- garbage collection is budgeted and tested like ingestion.

---

## 6. R1–R29: root causes, symptoms, and optimal order

### Important evidence limitation

The supplied briefing names R1–R3 individually, describes R4–R21 mainly by block, and lists R22–R29 as short labels rather than a complete one-to-one specification ([R1–R29 matrix](octopus-updated-briefing.md#r1-r29-megaprompt-matrix-for-next-agent)). The classification below is therefore exact where the item is named and block-level where it is not; it does not invent missing item text.

### Structural classification

| Item/range | Classification | Why |
|---|---|---|
| **R1 PAT rotation** | **Immediate containment; symptom repair** | Removes a live credential exposure but does not fix secret-prevention architecture. Pair with pre-commit/CI/host scanning and scoped short-lived credentials. |
| **R2 push to germline** | **Evidence/recoverability prerequisite** | Not a root safety control alone, but essential for a canonical, recoverable audit root. A push without signed provenance and deployment binding is insufficient. |
| **R3 disable duplicate Observatory task** | **Symptom repair** | Stops double fetching now. Root repair is a single job registry, idempotency keys, coalescing, and effect-level deduplication. |
| **R4–R14 test debt** | **Mixed; triage by invariant impact** | The open orchestrator breaker and unreachable `ask()` role are structural execution-path defects. C-013 is a structural TCB defect. API drift, allowlist/flag/inventory updates can be contract debt; they become structural if stale inventories control admission. |
| **R15 daemon 4d bring-up + continuous telemetry** | **Structural operationalization, but unsafe if premature** | Continuous memory operation matters, but should follow per-leg isolation and evaluator separation. |
| **R16 1062-hypothesis queue policy** | **Structural** | Introduces scarcity, retirement, deduplication, and bounded attention. |
| **R17 FUZZY flag vote** | **Policy decision; structural only if enforced** | A vote is not a mechanism. Bind it to versioned policy and runtime admission. |
| **R18 delta-not-level consolidation** | **Structural epistemic fix** | Prevents repeated accumulation from masquerading as new evidence and reduces self-reinforcement. |
| **R19 regenerate briefing from live tree/re-audit** | **Structural audit-integrity fix if automated and attested** | A manually refreshed document will become stale again. The artifact must be generated from a frozen revision and deployed-state evidence. |
| **R20 decision artifacts: evaluator, per-leg memory, local Fugu tier** | **Structural design work** | These address V11, V3, and V5 directly, but ADRs alone do not close them; implementation and bypass tests must follow. |
| **R21 external D1 audit** | **Structural assurance** | Useful only after evidence is immutable, reproducible, and tied to the deployed artifact; otherwise it repeats the stale-briefing failure. |
| **R22 leg README** | **Cosmetic unless generated from manifest** | Human documentation helps, but a machine-enforced leg manifest is the real control. |
| **R23 Ziman `run_tests`** | **Quality infrastructure** | Important for uniform evidence, but not a root cause by itself. |
| **R24 jobs `sqlmodel`** | **Implementation debt / potentially structural** | Structural if it establishes schema constraints, idempotency, ownership, and migrations; cosmetic if it is only a library migration. |
| **R25 commit hard-task work** | **Evidence hygiene** | Preserves reproducibility; does not validate the breadth of the claim. |
| **R26 SMTP gate exemption** | **High-risk policy exception** | Do not treat as micro/cosmetic. Exemptions can puncture complete mediation. Require a narrow, expiring, action-bound rule and negative tests. |
| **R27 `ask` quality bug** | **Product-quality symptom, possibly routing structural** | Escalate if it affects governance role reachability or evidence quality; otherwise ordinary defect. |
| **R28 `brain_core` shadow→live** | **Structural activation** | Must occur only through the same independent evaluator, provenance, canary, and rollback process as any high-impact mutation. |
| **R29 4d shadow→live** | **Structural activation** | Same as R28; additionally requires memory isolation, deletion/TTL, and poisoning tests. |

### Optimal execution order

The supplied block order is sensible for operator convenience but not optimal for structural risk. Use this dependency order:

#### Phase 0 — preserve NO-GO and contain live risk

1. Keep autonomous fixation and consequential execution disabled.
2. **R1:** rotate/revoke the GitHub PAT; inspect its access log and scope; replace long-lived PAT use with the narrowest available credential.
3. Put the 9 NO-GO assertions under protected ownership immediately.

#### Phase 1 — establish one trustworthy evidence root

4. **R2:** push the complete, reviewed state to germline; record commit, dirty-tree state, submodules/dependencies, and deployment digest.
5. **R19:** generate the audit bundle from that frozen revision and from live runtime attestations—not from prose.
6. Run gitleaks and the formal suite in a clean checkout; sign results and bind them to the artifact.

This must precede the external audit. Otherwise the auditor can once again inspect a coherent but irrelevant snapshot.

#### Phase 2 — repair the trusted core and execution graph

7. Fix **C-013** first among code debts: define and minimize the TCB; eliminate fallback-to-root; protect the guard and evaluator boundary.
8. Repair the orchestrator’s open breaker and unreachable governance role.
9. Replace ad hoc allowlists/flags/inventories with the organism manifest.
10. Fix **C-014** structurally: **R3** plus authoritative scheduler ownership, idempotency, content addressing, and deduplication.
11. Treat **R26 SMTP exemption** as an architecture review, not a micro-task.

The test harness cannot be trusted to authorize later work while its own TCB and control routes are ambiguous.

#### Phase 3 — implement the four retained structural controls

12. PEP mesh and canonical action lease across network, tools, queues, persistent memory, code execution, budgets, and messages.
13. Per-leg memory/evidence isolation.
14. Local/private Fugu route with final-payload DLP and technical no-egress fallback.
15. Independent evaluator with separate code, identity, data, telemetry, and release authority.
16. Action-bound human approval and distributed kill/lease expiry.

These controls are more important than most of R22–R29 and should be added to the execution matrix explicitly; R20 currently asks only for decision artifacts.

#### Phase 4 — make learning bounded and subtractive

17. **R16:** hypothesis queue policy with family dedup, quotas, expiry, and retirement.
18. **R18:** delta-based consolidation.
19. Implement memory TTL, deletion/tombstones, quarantine, and independent cross-leg promotion.
20. Decide **R17** and encode the result as versioned, enforced policy.
21. Then perform **R15** continuous daemon/telemetry bring-up in shadow.

#### Phase 5 — assurance before activation

22. Complete the remaining R4–R14 contract/API/test debts.
23. Complete R22–R25 and R27 as reproducibility/quality work.
24. **R21:** external D1 audit against the signed evidence bundle and deployed artifact.
25. Red-team bypass, stale-lease, duplicate-job, poisoned-memory, evaluator-tamper, and kill-under-partition scenarios.
26. Only then consider **R28/R29** shadow→canary→bounded-live transitions, separately, with observation periods.

Do not activate `brain_core` and 4d together. Sequential activation preserves causal attribution and rollback clarity.

---

## 7. Audit integrity: ensuring future councils inspect live evidence

The stale briefing was not merely a documentation error; it was an **evidence-selection failure**. OCTOPUS needs an audit protocol in which “what is being audited?” is cryptographically and operationally unambiguous.

### A. Replace briefing-first audits with evidence-first audits

Every audit should begin from a generated **Audit Evidence Bundle (AEB)**:

```text
audit_id, observed_at, expires_at
source_repo, commit_sha, signed_tag, dirty_tree_state
unpushed_commit_count, branch_protection_state
artifact_digest, build_id, provenance_attestation
deployed_instance_ids, process/image digests
runtime_config_hash, feature_flag_values, policy_epoch
database/schema versions, queue/scheduler inventory
component/leg manifest and capability inventory
test commands, tool versions, raw outputs, exit codes, result hashes
secret-scan result and exception ledger
kill-drill receipt and measured latency
budget/quota state and meter reconciliation
open contradictions with evidence links
auditor identity/signature
```

Narrative briefing text should be generated **from** this bundle and clearly label:

- **declared** — appears in policy/docs;
- **implemented** — code exists;
- **tested** — a bound artifact passed;
- **deployed** — that artifact digest is running;
- **drilled** — behavior was observed under a realistic failure;
- **independently reproduced** — an auditor reran or directly verified it.

The first council confused declared historical status with deployed current status. This state ladder prevents that category error.

### B. Bind source, build, deployment, and runtime

SLSA provenance lets consumers verify which build platform produced an artifact from which inputs ([SLSA provenance](https://slsa.dev/spec/v1.0/provenance)). OCTOPUS should:

1. build from a clean, immutable revision;
2. emit signed provenance and SBOM;
3. store the artifact by digest;
4. require deployment admission to verify source, builder, test bundle, and owner authorization;
5. have each running process expose or attest its artifact/config/policy digest;
6. reject an audit if the source bundle and running digests do not match.

NIST’s SSDF recommends generating audit artifacts, verifying release integrity, archiving each release, protecting provenance separately or by signature, and updating provenance when components change ([NIST SSDF](https://csrc.nist.gov/files/pubs/sp/800/218/final/docs/nist.sp.800-218.ssdf-table.xlsx)).

### C. Make freshness a machine-enforced property

- Every fact carries `observed_at`, source, method, and TTL.
- Volatile facts—PIDs, flags, budgets, queue consumers, deployed digest—expire quickly.
- Structural facts—signed code and schema—remain valid only for their digest.
- Any expired or mismatched critical fact renders the audit **INDETERMINATE**, never silently “green.”
- Councils receive both the frozen bundle and a final live-delta report generated immediately before review.

### D. Give auditors read-only live verification

Provide a constrained audit runner that can independently:

- query current Git and deployment digests;
- enumerate processes, scheduled jobs, adapters, credentials-by-scope (never secret values), queues, PEPs, and network routes;
- rerun selected tests in a clean environment;
- challenge kill, budget, replay, dedup, and memory-isolation controls;
- compare actual inventory with the organism manifest;
- export raw, signed receipts.

The system under audit may collect evidence but may not be the sole adjudicator of that evidence.

### E. Make contradiction detection continuous

Turn contradictions into executable reconciliation rules:

- two jobs claim one logical operation → C-014-style conflict;
- runtime component absent from manifest → undeclared capability;
- documented flag differs from runtime → stale-view violation;
- deployed digest differs from tested digest → release-integrity failure;
- TCB path expands without owner-approved manifest change → C-013-style violation;
- one evidence hash appears under multiple “independent” source IDs → dedup/correlation violation.

Every contradiction gets an owner, severity, first/last observation, exact evidence, and closure receipt. Closing a contradiction means the conflicting live observations can no longer be reproduced—not that a prose line was edited.

### F. Preserve external independence

For consequential audits:

- auditor selects challenge cases after artifact freeze;
- hidden holdouts and challenge seeds are inaccessible to mutation code;
- audit outputs go to append-only storage outside the organism’s write authority;
- owner approval binds to the exact audited digest;
- re-audit is mandatory after any TCB, evaluator, policy, scheduler, PEP, or memory-schema change.

---

## Final decision and activation gates

### Current allowed posture

- functional testing and T1–T12 continuation;
- shadow observation;
- advisory proposals;
- synthetic and non-consequential experiments;
- memory-loop operation only within current containment and with poisoning monitoring;
- owner-executed actions outside autonomous fixation.

### Current prohibited posture

- autonomous consequential external effects;
- self-authorized mutation fixation;
- activation of authority-bearing Hypothesis Engine behavior;
- sensitive Fugu egress based only on “don’t send”;
- simultaneous `brain_core` and 4d live activation;
- any TCB/evaluator modification based only on the organism’s own green tests.

### Minimum evidence for a bounded GO

1. signed live-evidence bundle tied to the deployed artifact;
2. C-013 closed with a minimal, explicit TCB;
3. C-014 closed with scheduler ownership and effect-level idempotency;
4. all consequential effects mediated by tested PEPs;
5. exact-action, single-use approval/capability leases;
6. per-leg memory/evidence isolation;
7. local/private Fugu route;
8. independent evaluator and hidden holdout;
9. kill and lease-expiry drills under partition/backlog;
10. external audit reproduction;
11. one bounded capability activated at a time with a canary, observation period, and rollback receipt.

**Bottom line:** The owner’s fact-check substantially improves the evidentiary picture and corrects the first council’s stale claims. It does not reverse the autonomous-execution verdict. OCTOPUS now has better tests and fewer missing operational controls than previously believed; the remaining work is more precise and more architectural: minimize and attest the trusted core, enforce policy at effects, separate evaluators, isolate memories, make deletion native, and ensure every future audit is tied to the exact code and runtime it claims to judge.
