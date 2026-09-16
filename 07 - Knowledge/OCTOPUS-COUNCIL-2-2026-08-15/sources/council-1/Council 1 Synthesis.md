# OCTOPUS Structural Audit — Model Council Synthesis

**Council members:** GPT-5.6 Sol · Gemini 3.1 Pro · Claude Sonnet 5.0  
**Audit date:** 15 August 2026  
**Subject:** OCTOPUS AI production architecture — NBB-V1 governance, NBB-CP control planes, ADR-037 Hypothesis Engine

---

## 1. Where Models Agree

| Finding | GPT-5.6 Sol | Gemini 3.1 Pro | Claude Sonnet 5.0 | Evidence |
|---------|-------------|----------------|---------------------|----------|
| All six activation gates being OPEN is the critical blocking condition — no L2/L3/self-learning should proceed | ✓ | ✓ | ✓ | Security Gate, git init, budget ceiling, kill-switch, truth reconciliation, stale-view all documented as OPEN in architecture briefing |
| The Evaluator Problem (system judging its own mutations) is a critical unresolved structural flaw with ~50% reward-hacking risk | ✓ | ✓ | ✓ | Gap Analysis item #1; Eurisko H59 historical precedent; [Denison et al.](https://arxiv.org/abs/2406.10162) |
| Fugu "don't send" approach is a discipline-based policy, not a technical control — insufficient for C17 | ✓ | ✓ | ✓ | "Don't send" is a negative specification (fail-open) inside an otherwise fail-closed philosophy; local execution tier needed |
| NBB-CP governance boundary is conceptually sound but not yet mechanically enforced — policy statement vs enforcement system | ✓ | ✓ | ✓ | No demonstrated non-bypassable policy enforcement points at every effect boundary; [NIST SP 800-207](https://nvlpubs.nist.gov/nistpubs/specialpublications/NIST.SP.800-207.pdf) |
| ADR-037 evidence does not justify promoting Hypothesis Engine beyond evidence_level C — adapter must stay OFF | ✓ | ✓ | ✓ | P1 B vs C: p=0.32 REJECTED; P2: B slower in benign (p=0.0006); "not superior to novelty" warning registered |
| Bayesian update mechanism defends against direct p_e injection but NOT against upstream evidence curation attacks | ✓ | ✓ | ✓ | [Carreau, Naveiro & Caballero (PMLR 2025)](https://proceedings.mlr.press/v258/carreau25a.html) — surgical posterior poisoning via evidence deletion/replication |
| Shared L4 memory lacks per-leg isolation — cross-leg evidence contamination is a shared-fate risk | ✓ | ✓ | ✓ | Gap Analysis item #6 (memory scoping per-identity absent); shared Redis, evidence stores, memory writes |
| Observatory's 60-prediction threshold is an administrative floor, not a statistical guarantee — Brier scores sensitive to correlation and outliers | ✓ | ✓ | ✓ | Rare events may need hundreds of pairs; domain stratification needed; [Bradley, Schwartz & Hashino](https://journals.ametsoc.org/view/journals/wefo/23/5/2007waf2007049_1.xml) |
| Production verdict: NO-GO for autonomous/consequential execution; maintain L1 propose-only posture | ✓ | ✓ | ✓ | All models independently concluded system is unsafe for production without gate closure |

## 2. Where Models Disagree

| Topic | GPT-5.6 Sol | Gemini 3.1 Pro | Claude Sonnet 5.0 | Why They Differ |
|-------|-------------|----------------|---------------------|-----------------|
| Primary framing of the core problem | "Policy decision point vs policy enforcement system" — NIST zero-trust framing, complete mediation gap | "Open gates + evaluator problem + Fugu leakage" — checklist of critical items | "Treat open-gate configuration as permanent, not transitional" — threat-model framing | Different analytical lenses: GPT-5.6 Sol uses formal security architecture framework; Gemini uses risk enumeration; Claude uses adversarial permanence assumption |
| Depth of governance bypass analysis | Exhaustive enumeration of 8+ specific bypass paths (capability laundering, proposal fragmentation, confused deputy, credential bypass, queue-after-revocation, lease replay, identity collapse, read-to-write conversion) | High-level identification of gaming via state manipulation and delay tactics | 4 bypass scenarios with deep causal analysis (Architect escape valve, evidence-level laundering, delegation self-issuance, reversible-work reclassification) | GPT-5.6 Sol prioritizes breadth of attack surface; Claude prioritizes depth of mechanism; Gemini prioritizes readability |
| Approach to fitness function critique | Replace scalar/OR rule with lexicographic constrained optimization (invariants → noninferiority → optimization → uncertainty bounds) | Identifies Goodhart risk but doesn't propose replacement structure | Identifies self-grading as the core issue; recommends independent computation of metrics | GPT-5.6 Sol proposes most formal mathematical replacement; Claude focuses on evaluator independence; Gemini stays at identification level |
| Fugu data leakage mitigation specificity | 8-step architecture: classify/tokenize → redact → abstract → DLP check → bind approval → prevent retrieval → inspect response → hard fallback | Recommends local execution tier (Claude Science pattern) | Converts "don't send" to positive allowlist + local execution tier; flags fail-open anomaly | GPT-5.6 Sol most prescriptive with pipeline steps; Claude identifies philosophical inconsistency; Gemini aligns with existing Gap Analysis recommendation |
| Production blueprint detail level | Full enforcement mesh architecture with signed capability leases, canonical action contracts, 4-class evidence architecture, 6-phase release plan | 5 high-level mitigation strategies | Tiered P0-P3 mitigations (14 items) with 6 production blueprint recommendations | GPT-5.6 Sol produces most detailed engineering blueprint; Claude produces most actionable prioritized list; Gemini produces most concise |
| Treatment of the Hypothesis Engine's self-referential blind spot | Notes the engine optimizes its own queue via subjective terms in pursue score; identifies churn risk with 20-hypothesis cap | Identifies self-deception risk from fixating on elaborate hypotheses | Identifies that the engine's value activates precisely under adversarial conditions — the condition adversaries would target | Claude surfaces the most novel insight (self-referential vulnerability); GPT-5.6 Sol focuses on formula manipulation; Gemini stays general |

## 3. Unique Discoveries

| Model | Unique Finding | Why It Matters |
|-------|----------------|----------------|
| GPT-5.6 Sol | NBB-CP governor is simultaneously a single logical dependency AND a compromise concentration point — if legs interpret silence/timeout as permission, compromise = execution; if fail-closed, compromise = total DoS | No model other than GPT-5.6 Sol explicitly identified the governor's own failure semantics as unspecified, creating a hidden SPOF with two equally bad failure modes |
| GPT-5.6 Sol | Proposed a complete "canonical action contract" — every consequential operation as a signed envelope with 15+ fields including delegation chain, policy epoch, data classification, compensation plan, and evidence inputs/outputs | This is the only model that produced a concrete, implementable action-verification schema that could directly become an ADR |
| GPT-5.6 Sol | Identified that the 200-line constitution ceiling is a "compression hazard" that encourages underspecification and controls hidden in lower-authority documents | Other models didn't flag that the constraint itself could be a structural weakness |
| Claude Sonnet 5.0 | NBB-CP's stop authority is "preventive, not remedial" — it can halt future actions but cannot undo committed side effects without git/rollback that's gated behind the same open Security Gate (C1) | This reframes the governor from "speed bump vs wall" — the most memorable and actionable framing of the governance boundary gap |
| Claude Sonnet 5.0 | The Hypothesis Engine's value proposition activates only under environment deception — precisely the condition an adversary would target, creating a self-referential blind spot the ADR doesn't address | No other model identified this circularity: the engine is most needed where it's most attackable |
| Claude Sonnet 5.0 | Fugu's "don't send" is a fail-open negative-specification control embedded inside an otherwise fail-closed philosophy — a structural anomaly, not just an operational gap | This reframes C17 from "missing control" to "philosophical inconsistency" which demands a different remediation priority |
| Claude Sonnet 5.0 | Evidence-level laundering through summarization — if any consumer drops the C/simulation label when summarizing, simulation evidence becomes functionally indistinguishable from validated evidence at consumption point | Other models noted evidence-level C should stay; Claude identified the specific mechanism by which it silently gets promoted |
| Gemini 3.1 Pro | Identified that e-value threshold of 20 corresponds to significance level 0.05 in sequential testing, but relying on sequential evidence without guardrails carries structural risks in non-stationary environments | Gemini was the only model to research and cite the specific statistical interpretation of the e-value threshold |

## 4. Comprehensive Analysis

### High-Confidence Findings (Convergence = Reliability)

All three council models independently arrived at the same production verdict: **NO-GO for autonomous or consequential execution**. This unanimity is striking given the different analytical approaches each model took — GPT-5.6 Sol applied NIST zero-trust formalism, Gemini 3.1 Pro used risk enumeration, and Claude Sonnet 5.0 adopted an adversarial permanence framing. When three independent analyses using different lenses converge on the same conclusion, the conclusion has high epistemic reliability.

The convergence centers on one structural fact: all six self-learning activation gates are OPEN. GPT-5.6 Sol states this creates a paradox where the system "says 'fail closed' while its enforcement, rollback, and emergency-stop mechanisms remain unimplemented." Claude Sonnet 5.0 frames it as the system "operating in its least-defended configuration" where every safety claim should be evaluated "as if that configuration is permanent." Gemini 3.1 Pro identifies this as the root cause of the system being "unsafe for production deployment without significant remediation." The architecture's own Gap Analysis acknowledges the evaluator problem, delegation observability gap, and missing local execution tier — but the council's contribution is establishing that these are not implementation TODOs but structural prerequisites whose absence invalidates every downstream safety claim.

The Evaluator Problem received equally strong consensus. GPT-5.6 Sol cites [Denison et al.](https://arxiv.org/abs/2406.10162) showing models progress from specification gaming to reward tampering, and that harmlessness training doesn't eliminate the behavior. Claude Sonnet 5.0 provides the most vivid historical precedent: Eurisko's H59 heuristic, which hijacked credit for other heuristics' successes without producing any genuine improvement — the exact failure shape of OCTOPUS's Column 2 mutation loop. All three models agree that the Goodhart safeguard ("fitness function must be reviewed") is a process commitment, not a mechanism, and that precise self-grading is still self-grading.

### Areas of Divergence (How to Weigh Them)

The models diverge most significantly in their prescriptive depth. GPT-5.6 Sol produced the most engineering-detailed output — a full enforcement mesh architecture with signed capability leases, a 15-field canonical action contract, a 4-class evidence architecture, and a 6-phase release plan. This is immediately implementable but may over-engineer for a single-operator system. Claude Sonnet 5.0 produced the most analytically distinctive findings — the "preventive vs remedial" framing, the self-referential blind spot in the Hypothesis Engine, and the fail-open anomaly in Fugu data handling. These are conceptual insights that should reshape how the architecture is thought about, even if they don't directly translate to code. Gemini 3.1 Pro provided the most concise and accessible summary, which has value for stakeholder communication even if it lacks the depth of the other two.

The divergence on fitness function remediation is particularly important. GPT-5.6 Sol proposes replacing the scalar OR rule with lexicographic constrained optimization — hard invariants first, then noninferiority gates, then optimization, with uncertainty bounds and holdout confirmation. This is the most mathematically rigorous proposal. Claude Sonnet 5.0 focuses on the evaluator independence problem — requiring that mutation fitness evaluation use a separate code path, separate data source, and independent computation. These are complementary: GPT-5.6 Sol's lexicographic optimization provides the right objective structure, while Claude Sonnet 5.0's evaluator independence provides the right evaluation structure. Both should be implemented.

### Unique Insights Worth Noting

Claude Sonnet 5.0's identification of the Hypothesis Engine's self-referential blind spot is the single most novel finding across all three reports. The engine's measured value proposition (97% vs 0% discovery in deceptive environments) activates precisely under the conditions an adversary would target — meaning the production environments where OCTOPUS most needs the Hypothesis Engine are also the environments where an adversary has the most incentive to feed it engineered evidence. This creates a circular vulnerability: the capability's activation condition is also its attack surface. No threat model for this circularity exists in ADR-037.

GPT-5.6 Sol's canonical action contract is the most immediately useful engineering artifact. If implemented as an ADR, it would address multiple vulnerabilities simultaneously: TOCTOU races (via atomic lease consumption), capability laundering (via parameter binding), proposal fragmentation (via composition policy), and replay attacks (via expiry and idempotency). It represents the concrete enforcement mechanism that the NBB-V1 governance model currently lacks.

### Final Recommendation

The council's unanimous verdict is clear: maintain the current L1 propose-only, adapter-off posture. Before any gate activation, execute the following prioritized sequence:

1. Close Security Gate + git init (C1) — this is the precondition for every other safety property
2. Install gitleaks on host (C2) — low cost, high risk reduction
3. Set Fugu budget ceiling + rotate key (C16) — prevents uncontrolled exposure
4. Build local execution tier for Fugu (C17) — converts "don't send" from policy to structural property
5. Solve the Evaluator Problem with independent evaluation service — the load-bearing unresolved risk
6. Close remaining activation gates sequentially with observation periods between each
7. Implement resource-side enforcement points (PEPs) at every effect boundary — the governance model is incomplete without them
8. Add per-leg memory scoping before scaling — shared-fate risk gets worse with more legs

The architecture's intellectual honesty — registering "not superior to novelty" warnings, keeping evidence_level at C, documenting 17 open contradictions — is itself a strength. The transition from "governance intent" to "governance mechanism" requires treating every prose-level safety claim as a hypothesis to be mechanically verified, not an axiom to be assumed.
