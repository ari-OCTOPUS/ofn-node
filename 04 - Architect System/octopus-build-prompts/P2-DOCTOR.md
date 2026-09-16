---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, prompt, build, doctor, evolution]
created: 2026-07-08
updated: 2026-07-08
created_by: agent
---

# PROMPT — Octopus Build · Phase 2: THE EVOLUTIONARY DOCTOR (head-parasite)

> **برای آری:** دکتری که مثل انگل همیشه به سرِ ارگانیسم چسبیده و مدام نگاه می‌کند و پیشنهادِ بهبود می‌دهد — ولی **هیچ‌چیزش بدونِ یک تاییدِ تلگرامیِ تو اجرا نمی‌شود.** فقط در sandbox کار می‌کند. این همان لنگرِ ضدِ «AI که خودش خودش را عوض کند» است.

## 0. ROLE
Build the doctor as a **persistent supervisor co-located with the orchestrator** — always attached, always observing, but **structurally powerless to change production without a human-append.** Additive only.

## 1. PREREQUISITE
Phase 1 green (heartbeat + `restart_from_known_good` hook + effect-gate). Read `OCTOPUS-RECON-MAP.md` §5 (doctor(s)).

## 2. SOURCES
- `04 - Architect System/scripts/DOCTOR-BLUEPRINT-v1.md` — the stable-read gate (§4) + the current `dashboard_doctor.py` (178 lines) as one sensor.
- `CHRONOS-FABLE-OS/11_Agents/AgentInstructions.md` (AGENT-08 Evolution Doctor) + `08_Safety/HeartDesign_PulseCore.md` (Awareness Genome reward-integrity, `λ_persist`).
- Existing: `07 - Knowledge/genome-system/agents/doctor.py` (restart-only today), `genome-system/research_loop.py`, the KnowledgeFabric folders `/knowledge/{fable,external,internal}`.

## 3. LAWS (critical for this phase)
- **Sandbox-only (Evolution Guard):** the doctor builds/tests only in a sandbox; **NO auto-merge to production.**
- **Every merge needs a human-append (Telegram)** — evolution rate = human-presence rate, by design. This closes the self-referential/agreement-spiral risk (AP-03).
- **Reward-integrity:** the doctor's scoring must actively **disfavor self-preservation** (`λ_persist` negative). It never optimizes "stay alive / keep beating."
- Propose-only in scheduled runs; apply only interactively after a verdict. Every adjustment carries a `ledger_ref`.

## 4. STEPS (in order)

**D-1 · Stable-read sensor.** Implement `stable_read(path)` from `DOCTOR-BLUEPRINT-v1.md §4` (deterministic stale-view vs. real-corruption) + the **mandatory Windows-side confirm belt** for any `corrupt` verdict (the blueprint's §4 residual — a torn-but-self-consistent FUSE snapshot must be cross-checked). Replace the class-based `VERIFY_RULES` with the instance-based gate. Test: three fixtures (stable/stale/corrupt) classify correctly; a torn snapshot is NOT falsely marked corrupt.

**D-2 · Trace/metric mining.** Give the doctor read access to: heartbeat metrics (cost/latency/error per beat from Phase 1), the LANGAR ledger, and `/knowledge/{fable,external,internal}`. Implement `mine() -> bottleneck` (find the worst recurring failure/cost). Test: on a seeded trace with a known bottleneck, the doctor names it.

**D-3 · RFC generation (propose-only).** From a bottleneck, the doctor writes a structured **RFC** (problem, proposed prompt/tool/config fix, expected eval-lift, rollback) to `/knowledge/internal` — an event, never a code change. Test: an RFC is emitted as a proposal-event; nothing in production changed.

**D-4 · Sandbox build + Critic.** The doctor applies its RFC in a **sandbox copy** only, runs the offline suite there, and a Critic pass does an adversarial before→after review. Test: sandbox isolation proven (production untouched); Critic emits a verdict event.

**D-5 · Human-append merge.** The RFC + Critic result is packaged for the operator. **Only a Telegram human-append (Phase 3) settles it** → then a feature-flagged merge → log lesson to `/knowledge/internal`. This phase leaves a clean interface `doctor.submit_for_approval(rfc)` that Phase 3 renders as an [merge]/[reject] card. Test: with no human-append, the RFC stays pending forever; a mocked approval triggers a flagged merge.

**D-6 · Attach to the head + restart duty.** Run the doctor every N beats from `organism.py` (the "parasite"), and wire the `restart_from_known_good(leg)` hook from Phase 1 (OTP-style restart of a failed leg from ledger state). Test: a failed leg is restarted from known-good; the doctor loop runs on the heartbeat without blocking it.

## 5. DEFINITION OF DONE
- Doctor runs every N beats, co-located with the orchestrator.
- It produces ≥1 concrete RFC from a real trace, builds it in sandbox, Critic-reviews it, and **nothing reaches production without a human-append.**
- Stable-read gate replaces the class heuristic; no false-corrupt on torn snapshots.
- Restart-from-known-good works; suite green.

## 6. OPEN-DECISIONS
- Doctor cadence (every K beats?), the Windows-confirm belt on/off (blueprint §6 verdict), and whether the vault-health `dashboard_doctor` folds in now or stays a separate sensor.

## 7. HAND-BACK
Update `DOCTOR-BLUEPRINT-v1.md` status → implemented (additive note), `ORGANISM-SPEC.md`, `HANDOFF.md`; suite green; owner-gated commit. Leave `doctor.submit_for_approval(rfc)` for Phase 3.
