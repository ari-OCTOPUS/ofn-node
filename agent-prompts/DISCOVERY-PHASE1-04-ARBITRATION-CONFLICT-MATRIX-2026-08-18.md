# DISCOVERY-PHASE1-04 — Multi-Model Arbitration & Conflict-Resolution Matrix
Bundle: OCTOPUS World-Discovery Phase 1 · 2026-08-18 · Status: READY
Used by: the Phase-3 merge prompt (appendix A is the in-prompt compression of this document) and by the owner when reviewing council outputs ("Where Models Agree / Disagree / Unique Discoveries" tables).

---

## 1. PRINCIPLES

1. **Merge is a join, not a vote.** Divergence is preserved as data (`alt_command`, CONTRADICTIONS.md rows). No averaging, no synthetic third option, no "compromise command".
2. **Convergence is not evidence.** Kimi+GLM agreement without a runtime envelope caps at `CLAIMED` / `MODEL_CONVERGENCE_NOT_RUNTIME_EVIDENCE`.
3. **Evidence outranks models; governance outranks evidence.** A binding owner record overrides any measurement; a measurement overrides any number of model opinions.
4. **Discovery decides nothing.** Governance calls (YELLOW/W3 semantics, .138 latency budget, canonical repo, .180 runtime state) are `OWNER_DECISION_REQUIRED` — the merge must surface them, never settle them.

**Resolution classes (exhaustive):** `KEEP_BOTH` · `HIGHER_TIER_WINS` · `UNKNOWN_UNTIL_EVIDENCE` · `OWNER_DECISION_REQUIRED`
**Truth-priority ladder:** `OWNER_DECISION > VERIFIED(fresh) > TEST_VERIFIED > STALE > GIT_CONFIG > CLAIMED > UNKNOWN` — and `CONTRADICTED` blocks everything above it.

## 2. THE MATRIX

| # | Situation (detected how) | Merged status | Resolution class | Action | Escalation |
|---|---|---|---|---|---|
| A1 | Both agree **+** owner evidence envelope with artifact+digest | envelope's status (VERIFIED/TEST_VERIFIED) | HIGHER_TIER_WINS (trivially) | Adopt; cite envelope id in both deliverables | none |
| A2 | Both agree, **no** evidence (the default case) | CLAIMED | KEEP_BOTH | Record `source: MODEL_CONVERGENCE_NOT_RUNTIME_EVIDENCE`; queue field for Phase-2 evidence capture | none |
| A3 | Both agree, but the agreed fact **contradicts governance** (e.g. ".180 is reachable") | CONTRADICTED | OWNER_DECISION_REQUIRED | BLOCK the field; write contradiction row; never normalize ("good, it's up" is forbidden) | immediate owner |
| A4 | Disagree on **command** for same field_id (join key match) | keep each command's claim status | KEEP_BOTH | Primary = better V1 platform fit (busybox cascade beats GNU assumption); loser preserved as `alt_command` | none |
| A5 | Disagree on **status tier** (VERIFIED vs CLAIMED) | lower tier unless digest exists | HIGHER_TIER_WINS | Higher tier survives only with artifact+sha256; else both fall to lower tier; note in EVIDENCE-MAP | none |
| A6 | Disagree on **value**, neither evidence-backed | UNKNOWN | UNKNOWN_UNTIL_EVIDENCE | Both values into CONTRADICTIONS.md; add capturing command to DISCOVERY-COMMAND-PLAN | none |
| A7 | **Unique finding** in one model only | CLAIMED | KEEP_BOTH | `source: MODEL_SINGLE_OUTPUT`; tag for evidence verification before any use | none |
| A8 | One runbook **missing/truncated** or model returned nothing (CONTINUE_REQUIRED unanswered, empty return) | n/a | OWNER_DECISION_REQUIRED (re-prompt) | Re-run Phase-1 prompt for that device; NEVER merge a section from a single source as if concurred; a no-output model is a datapoint, not a veto | owner informed |
| A9 | **Platform-assumption conflict** (GNU/systemd vs busybox/dropbear) | cascade version wins on merit | HIGHER_TIER_WINS (by V1) | Adopt fallback-cascade command; label loser `PLATFORM_ASSUMPTION` in REJECTED-COMMANDS | none |
| A10 | **Scheduler/policy-forbidden fields** (svc.scheduler, timers) | UNKNOWN_BY_POLICY | — (no discretion) | Both models' outputs overwritten to UNKNOWN_BY_POLICY, `verification_command: NONE`; any scheduler-read command they proposed goes to REJECTED-COMMANDS (SCHEDULER_ACCESS) | none |
| A11 | **Governance question** presented as a technical choice (YELLOW semantics, .138 latency budget, canonical repo, .180 power_state, GAP handling authority) | OWNER_DECISION | OWNER_DECISION_REQUIRED | Surface as open gate with options + consequences; the merge picks nothing | owner |
| A12 | **Runtime evidence conflicts with both models** (or with one) | CONTRADICTED | KEEP_BOTH | Evidence wins the *value*; both model claims preserved in the contradiction row; drift analysis: which model was closer, recorded as calibration data | owner if safety-relevant |
| A13 | Both models propose the **same unsafe command** (e.g. both include `ping` for .180) | n/a | — | Command → REJECTED-COMMANDS (risk label) even though both agree; agreement confers zero safety | none |
| A14 | Disagreement about **.180 reachability evidence** (cache hit vs repo record) | CONTRADICTED | OWNER_DECISION_REQUIRED | Freeze: no further .180 observation; both sources timestamped; owner rules | immediate owner |
| A15 | Models disagree about **merge/deliverable format** (structure, not facts) | n/a | KEEP_BOTH (structural) | Owner/merge-model adopts the union structure (this bundle's file set); the losing structure's *content* is fully carried over | none |

## 3. PRECEDENCE AND PRECISION (advisory weights)

| Evidence class | Precision | Can appear as |
|---|---|---|
| VERIFIED_FRESH (runtime artifact + digest, inside window) | 1.00 | VERIFIED |
| OWNER_DECISION (binding record + digest) | 0.90 | OWNER_DECISION |
| TEST_VERIFIED (deterministic local test + digest) | 0.85 | TEST_VERIFIED |
| GIT_CONFIG (repo config as artifact) | 0.70 | VERIFIED with GIT_CONFIG source |
| VERIFIED_STALE (digest but past window) | 0.35 | STALE |
| CLAIMED (any model output, doc, repo record) | 0.20 | CLAIMED |
| UNKNOWN / BLOCKED / CONTRADICTED / UNKNOWN_BY_POLICY / NOT_APPLICABLE | 0.00 | as stated |

A CONTRADICTED field has weight 0 until resolved — it cannot move any downstream belief (this is the numerical form of "evidence conflict blocks").

## 4. PROCESSING THE COUNCIL TABLE FORMAT

Input shape (from your model-council rounds): three tables — *Where Models Agree* (finding × model ✓s × evidence note), *Where Models Disagree* (topic × positions × why-differ), *Unique Discoveries* (model × finding × why-it-matters).

- **Agree table row →** A1/A2/A3 by evidence column. A row whose "evidence" column is reasoning rather than an artifact/digest is A2 regardless of how confident the prose sounds.
- **Disagree table row →** A4–A6, A9, A11 by what kind of thing differs. If the "why they differ" column says one model simply never reached the topic (truncation/output-budget), that row is **A8-shaped**: the disagreement is an artifact of missing output, not a real conflict — re-prompt before arbitrating.
- **Unique discoveries →** A7. Never let a unique discovery from a prestigious-sounding model skip the CLAIMED queue; that is the status-inflation attack surface.

## 5. WORKED PRECEDENTS (from the 2026-08-17/18 council rounds — cite, don't re-litigate)

| Council divergence | Matrix application | Standing resolution |
|---|---|---|
| Passive taxonomy: Kimi two-tier vs GPT-5.6 three-tier (P0/P1/A1) | A15 + A7 (GPT-5.6's unique insight: "passive capture" is a distinct risk class) | **Adopted three-tier** P0/P1/A1, P1 owner-gated |
| Read-only SSH: Kimi conditionally allows, GPT-5.6 forbids in D0 | A11-adjacent (owner authorization boundary) | **Split into D0-PASSIVE (no SSH) and D0-REMOTE-READ (one owner authorization)**; hard-fail on host-key/hostname mismatch |
| Enforcement: stated rules vs V1–V10 mechanical pipeline | A15 | **V1–V10 pipeline with Kimi rule content** |
| NOW.md format: tables+YAML vs frontmatter+Mermaid+self-audit | A15 | **Union**: frontmatter + §16 diff + §19 self-audit + §9 homeostatic + §17 session closure |
| Claude returned nothing on round 2 | A8 | **No-output is a datapoint, not a veto**; re-prompt or proceed with 2 models, recorded |
| W3 YELLOW semantics | A11 | **OWNER_DECISION_REQUIRED** — neither two-model agreement nor any single model may define it |
| `scp` on .138 assumed by two models | A9 | **Assume absent**; transfer via `ssh host 'cmd' > local_file`; dropbear detected by `ps`, not config |

## 6. ARBITRATION REPORT TEMPLATE (emit per device-pair)

```markdown
# ARBITRATION-{{DEVICE}}-{{ts}}
Inputs: KIMI (sha256 …) · GLM (sha256 …) · envelopes (N)
Agree rows: N (A1: n, A2: n, A3: n) · Disagree rows: N (A4: n … A11: n) · Unique: N (Kimi: n, GLM: n)
Rejections: N commands (risk histogram: MUTATION n, ACTIVE_NETWORK_PROBE n, …)
Promotions blocked (A2 applied): list of field_ids that LOOKED verified but capped at CLAIMED
Owner decisions required: [ids + one-line question each]
Calibration note: where evidence existed, which model was closer (per A12)
Closing block: [verbatim 8 lines]
```
