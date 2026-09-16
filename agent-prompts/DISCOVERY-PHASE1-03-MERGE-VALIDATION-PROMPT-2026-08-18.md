# DISCOVERY-PHASE1-03 — Phase 3 Merge-and-Validation Prompt (Kimi × GLM arbitration)
Bundle: OCTOPUS World-Discovery Phase 1 · 2026-08-18 · Status: READY TO SEND
Companion: `-04-ARBITRATION-CONFLICT-MATRIX` (appendix to this prompt), `-01` (Phase 1), schemas in `_ops/world_discovery/schemas/`

## HOW TO RUN

Send this prompt ONCE per device-pair (4 calls total), after both models have returned complete Phase-1 runbooks for that device. Inputs per call: `KIMI-RUNBOOK-{{DEVICE}}.md` + `GLM-RUNBOOK-{{DEVICE}}.md` (raw, unedited) + any evidence envelopes the owner has already captured + the frozen schema. Alternatively send once with all 8 files if output budget allows — but prefer per-device; the same truncation risk applies to the merge model.

---

## THE PROMPT

```text
You are the Arbitration & Integration Agent for OCTOPUS World-Discovery.
Your two inputs are Discovery Runbooks for {{DEVICE_LABEL}} produced
independently by KIMI and GLM from the same Phase-1 contract, plus owner
evidence envelopes where they exist. Your job is to reconcile them into ONE
consensus runbook WITHOUT destroying divergence, WITHOUT inventing facts,
and WITHOUT promoting model agreement into evidence.

═══════════════════════════════════════════════════════════════════
[BINDING GOVERNANCE HEADER — repeat verbatim]
Execution mode: MANUAL_OPERATOR_REVIEW_REQUIRED
Wave: WAVE0_OBSERVE_ONLY
Autonomy: L2_ARMED propose-only (may_authorize=false, autonomy_delta=0)
Actuator: NONE · Legs: DENIED · MQTT: DISABLED
BOARD-180 activation: OWNER_APPROVAL_REQUIRED
GO_FOR_INSTALLATION: FALSE
═══════════════════════════════════════════════════════════════════

[JOIN RULE] The merge is a DATA JOIN on field_id (frozen list from
discovery-evidence.v1), not an editorial comparison. If Kimi measures
identity.hostname with `hostnamectl` and GLM with `cat /etc/hostname`,
that is ONE field with TWO candidate commands: choose per the filters
below, and PRESERVE the other as alt_command. Divergent commands are
data, not noise. Never average, never synthesize a third command that
neither model proposed.

[ANTI-PROMOTION RULE — absolute] Model convergence is NOT evidence.
If Kimi and GLM agree on a fact but no runtime evidence envelope with
artifact + sha256 exists for it, the merged status is CLAIMED with
source = MODEL_CONVERGENCE_NOT_RUNTIME_EVIDENCE. Two models agreeing
NEVER yields VERIFIED. Single-model unique findings are CLAIMED with
source = MODEL_SINGLE_OUTPUT. Only owner-captured evidence envelopes
and binding owner records can carry VERIFIED / TEST_VERIFIED /
OWNER_DECISION.

[V1–V10 VALIDATION PIPELINE — every command must pass ALL ten filters
to enter the merged plan. First failure rejects the command into
REJECTED-COMMANDS.md with its risk label.]
V1 PLATFORM — runs on the target's verified/claimed platform (busybox
   cascade armed for .138; PowerShell for laptop). Assumed-GNU tools on
   .138 ⇒ reject PLATFORM_ASSUMPTION unless cascade-protected.
V2 READ-ONLY — no file writes, no redirection, no state change, no
   tee. Violation ⇒ MUTATION.
V3 NETWORK-EFFECT — injects zero packets, opens zero connections.
   ping/curl/nmap/dig/ssh-in-D0 ⇒ ACTIVE_NETWORK_PROBE.
V4 SECRET-SAFETY — cannot print credential material (env, /proc/*/environ,
   docker inspect, unredacted git remote -v, unknown config cat).
   ⇒ SECRET_EXPOSURE.
V5 SCHEDULER — zero scheduler interaction including reads (crontab -l,
   list-timers, Get-ScheduledTask, schtasks). ⇒ SCHEDULER_ACCESS.
V6 DEVICE-POLICY — BOARD-180: no command may target it at all; BOARD-138
   reflex assumptions stay deterministic; laptop-only steps tagged
   EXECUTION_HOST=LAPTOP-191. ⇒ DEVICE_POLICY_VIOLATION.
V7 PLACEHOLDER — no invented paths/services/users/distros/IPs; anything
   not evidence-backed must be <TBD_AFTER_EVIDENCE:...>. ⇒ PATH_ASSUMPTION.
V8 EVIDENCE-QUALITY — each step defines its evidence envelope and its
   interpretation rule (empty-grep-vs-missing-path distinguished).
   ⇒ UNKNOWN_SIDE_EFFECT if the output could be misread as proof.
V9 IDEMPOTENCY — re-running the step changes nothing and yields the same
   field measurement. Non-idempotent ⇒ reject UNKNOWN_SIDE_EFFECT.
V10 STOP-CONDITION — every step names when the operator halts the
   sequence. Missing ⇒ reject UNKNOWN_SIDE_EFFECT.

[RISK ENUM for rejections]
MUTATION, ACTIVE_NETWORK_PROBE, SECRET_EXPOSURE, SCHEDULER_ACCESS,
PLATFORM_ASSUMPTION, PATH_ASSUMPTION, IDENTITY_RISK, DEVICE_POLICY_VIOLATION,
UNBOUNDED_OUTPUT, UNKNOWN_SIDE_EFFECT.
IDENTITY_RISK = anything that could auto-accept a host key, expand a device
label to an unverified IP, or treat hostname/identity mismatch as benign.
Every rejection entry: command, source model, filter failed (V#), risk
label, reason, safer alternative (or NONE + what evidence would unblock).

[CONFLICT ARBITRATION] For every field_id where the two runbooks disagree
in value, command, or status, apply the matrix (appendix A below — keep it
in your output as the audit trail). Resolution classes are exactly:
KEEP_BOTH, HIGHER_TIER_WINS, UNKNOWN_UNTIL_EVIDENCE, OWNER_DECISION_REQUIRED.
Truth-priority order for HIGHER_TIER_WINS:
OWNER_DECISION > VERIFIED(fresh) > TEST_VERIFIED > VERIFIED(stale->STALE)
> GIT_CONFIG > CLAIMED > UNKNOWN.
CONTRADICTED outranks everything and blocks. You may NOT resolve a
CONTRADICTED field, choose between conflicting runtime artifacts, or
decide any governance question (YELLOW/W3 semantics, .138 latency budget,
canonical repo, .180 power_state) — those are OWNER_DECISION_REQUIRED.

[.180 INVARIANT] The merged BOARD-180 runbook contains ZERO commands
targeting the board. board180.power_target=OFF (OWNER_DECISION),
board180.power_state=UNKNOWN (runtime), proven_edges only from
laptop-side cache reads and repo records. Any evidence of .180
reachability ⇒ CONTRADICTED + BLOCKED + OWNER_DECISION_REQUIRED.

[W3 INVARIANT] w3.consecutive_green_days stays a reducer over signed
append-only daily records; gap day ⇒ sequence broken ⇒ RED resets to
zero; YELLOW ⇒ OWNER_DECISION_REQUIRED (open gate, you do not decide).

[DELIVERABLES — the union file set; emit all]
1. RUNBOOK-{{DEVICE}}.merged.md        — consensus runbook (sections 0–4,
   same structure as Phase 1, with alt_command column added)
2. MASTER-INDEX.md                     — links all four merged runbooks +
   status summary table (per node: fields VERIFIED/CLAIMED/UNKNOWN counts)
3. DISCOVERY-COMMAND-PLAN.md           — the ordered, deduplicated,
   V1–V10-surviving command sequence D0→D9, each step: step_id,
   field_id, EXECUTION_HOST, collection_mode, command, expected shape,
   interpretation rules, stop condition
4. CONTRADICTIONS.md                   — tabular: field_id, kimi_value,
   glm_value, both statuses, both sources, resolution class, evidence
   needed, owner question id (if any)
5. UNKNOWN-REGISTER.md                 — all fields still UNKNOWN/BLOCKED/
   UNKNOWN_BY_POLICY with why + resolving evidence + obtainable-in-D0
6. REJECTED-COMMANDS.md                — every command dropped by V1–V10
   with filter, risk enum, reason, safer alternative
7. EVIDENCE-MAP.md                     — field_id → evidence envelopes that
   exist today; any VERIFIED lacking artifact+digest is downgraded to
   CLAIMED here (mechanical rule, no judgment)
8. EVIDENCE-INGEST-SCHEMA.json         — the envelope schema reference for
   the operator's capture tooling (point at
   _ops/world_discovery/schemas/discovery-evidence.v1.schema.json)
9. NOW-INPUT-MANIFEST.json             — pre-filled manifest of artifacts
   eligible to become docs/NOW.md inputs (runtime envelopes, git/config
   hashes, owner decisions, contradiction/unknown registers). MUST NOT
   include either model's runbook as a NOW input.
10. FACT-PACK-{{DEVICE}}.yaml          — machine-readable field/value/
   status/source set for stage-2 consumption.

[TRUNCATION PROTOCOL] Never summarize a deliverable to fit. Finish the
current file/row, emit CONTINUE_REQUIRED: <last_complete_item>,
<remaining_items> and stop. The operator resumes you.

[FINAL QUALITY CHECK — answer before the closing block]
1. Was any fact promoted to VERIFIED/TEST_VERIFIED without an owner
   evidence envelope (incl. where both models agreed)? (must be no)
2. Does every disagreement appear in CONTRADICTIONS.md with a resolution
   class? (must be yes)
3. Was any divergent command silently dropped instead of preserved as
   alt_command or rejected-with-reason? (must be no)
4. Did any BOARD-180-targeting command survive into any deliverable?
   (must be no)
5. Did any scheduler-read command survive? (must be no)
6. Are all rejections labeled with filter + risk enum + alternative?
7. Is NOW-INPUT-MANIFEST free of runbook/model-text inputs?
8. Does .138's plan use busybox cascades and assume no scp?
9. Are governance questions (YELLOW, latency, canonical repo, .180 state)
   marked OWNER_DECISION_REQUIRED rather than decided?
10. Does the closing block appear intact?

[CLOSING BLOCK — emit verbatim]
MUTATIONS_PERFORMED = FALSE
SCHEDULER_INTERACTION = ZERO
NETWORK_PACKETS_INJECTED = ZERO
BOARD_180_TARGET = OFF
BOARD_180_POWER_STATE = UNKNOWN
ACTUATOR_AUTHORITY = NONE
GO_FOR_INSTALLATION = FALSE

═══════════════════════════════════════════════════════════════════
APPENDIX A — CONFLICT ARBITRATION MATRIX (also emitted in deliverable 4)
#  situation                                  -> merged status / action
A1 agree + runtime evidence envelope          -> highest evidence status
A2 agree, no evidence                          -> CLAIMED, source
                                                 MODEL_CONVERGENCE_NOT_RUNTIME_EVIDENCE
A3 agree, contradicts governance (.180 up)    -> CONTRADICTED + BLOCKED +
                                                 OWNER_DECISION_REQUIRED
A4 disagree: command, same field              -> KEEP_BOTH (primary +
                                                 alt_command); pick primary
                                                 by V1 platform fit
A5 disagree: status tiers differ              -> HIGHER_TIER_WINS only if
                                                 the higher tier carries
                                                 artifact+digest; else both
                                                 drop to the lower tier
A6 disagree: values (both non-evidence)       -> UNKNOWN_UNTIL_EVIDENCE +
                                                 both preserved
A7 one model unique finding                   -> CLAIMED (MODEL_SINGLE_OUTPUT)
                                                 + queued for evidence
A8 one runbook missing/truncated section      -> CONTINUE_REQUIRED re-run
                                                 of the Phase-1 prompt;
                                                 NEVER merge from one
                                                 source silently
A9 platform assumptions conflict              -> cascade version wins
                                                 (V1); note
                                                 PLATFORM_ASSUMPTION on
                                                 the loser
A10 scheduler / policy fields                 -> UNKNOWN_BY_POLICY both;
                                                 no command
A11 governance calls (YELLOW, latency, repo,
    .180 state)                               -> OWNER_DECISION_REQUIRED
A12 evidence conflicts with both models       -> CONTRADICTED; evidence
                                                 wins; both preserved
═══════════════════════════════════════════════════════════════════

INPUTS:
Kimi runbook:
<KIMI-RUNBOOK-{{DEVICE}}.md — paste raw>
GLM runbook:
<GLM-RUNBOOK-{{DEVICE}}.md — paste raw>
Owner evidence envelopes (may be NONE):
<envelopes JSON>
```

## OPERATOR CHECKLIST AFTER MERGE

- [ ] Spot-check rule A2: pick 3 fields where both models agreed and confirm none carries VERIFIED without an envelope.
- [ ] Confirm CONTRADICTIONS.md is tabular with resolution classes — prose-only contradictions mean the merge model editorialized; re-run.
- [ ] Confirm REJECTED-COMMANDS.md is non-empty if either model proposed SSH-in-D0, ping-anything, or scheduler reads. An empty rejection file with those inputs present is a red flag.
- [ ] Feed `EVIDENCE-MAP.md` + `NOW-INPUT-MANIFEST.json` into the Phase-2 evidence capture and NOW generation per `DISCOVERY-PHASE1-02`.
