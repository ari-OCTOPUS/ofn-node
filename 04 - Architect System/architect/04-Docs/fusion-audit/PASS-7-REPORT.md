---
type: reference
status: done
tags: [fusion-audit]
created: 2026-07-03
updated: 2026-07-03
---

# PASS 7 — Red Team Synthesis (attacking my own findings)

Role: adversary against Passes 1–6. For each material finding, ask: is it wrong, overstated, or
already mitigated? Then hand the surviving set to AUDIT.md.

## Self-challenges and rulings

**P1-01 / P4-02 (IGK silent downgrade).** Challenge: an in-process agent cannot itself kill the
subprocess, so is this really reachable? Ruling: the finding does not require an attacker — it fires
on *any* environmental failure and silently removes the primary control, which is the whole point.
But I downgrade the *attacker-triggered* variant to [Probable] and keep the *existence of the silent
downgrade* at [Certain]. Severity stays **High** (HITL remains a backstop in default config, so not
Critical). Survives.

**P2-01 (human verdicts in unsigned log).** Challenge: isn't finalize still gated by the signed
`consume`, so a forged approval changes nothing live? Ruling: correct — this is a **forensic**
integrity gap, not a live-bypass. I explicitly scoped it that way. It stays **High** because the
human verdict is the system's claimed root of trust and it is the one artifact with no cryptographic
protection; but I reject any framing that says a log edit alone flips a live decision. Survives, scoped.

**P4-01 (panel ignores LLM).** Challenge: maybe deterministic voting is an intentional MVP stub and
therefore not a defect. Ruling: even granting intent, it makes the #5 "no single point of decision"
claim misleading and hides judge-model failures — a silent-failure defect regardless of intent.
Survives at **High**, with the note that it may be deliberate scaffolding (so the fix is "wire it or
document it," not "it's broken").

**P1-02 (key deletion → clean forge).** Challenge: same-machine, same-user attacker who can delete
`.kernel_key` can do almost anything anyway. Ruling: true, but the specific loss — that `verify()`
would still return "intact" on a fully forged chain — defeats the explicit tamper-evidence claim and
deserves surfacing. Downgrade certainty to [Probable]; severity **High** → keep, but acknowledge it
lives in the same threat tier the README already disclaims. Survives.

**P1-03 (process-only isolation).** Challenge: this is documented, and no agent has a file tool, so
is it a finding or just a known limitation? Ruling: it is a known limitation; I keep it but at
**Medium** (not High) precisely because it is currently unreachable — its severity is contingent on a
future tool addition. Downgraded.

**P4-03 (MAX_STEPS unused) / P2-05 (external_write unused).** Challenge: harmless dead config?
Ruling: harmless to runtime, but each is a *claimed control that does not exist*, which is exactly
the kind of gap an audit must flag (false assurance). Keep both at **Medium**.

**P1-04 (grounding advisory + mis-wired).** Challenge: overstated — it is off by default on purpose.
Ruling: the "off by default" part is a config choice, but the *mis-wiring* (validating raw findings
against a geography/science held-out set so it would halt every run if enabled) is a genuine design
defect that makes the control unusable, evidenced by the persisted `ratio: 0.0`. Keep **Medium**.

**P5-02 (single-writer audit).** Challenge: is concurrency realistic here? Ruling: `self_update.py`
and `run.py` both write the same default log with independent in-memory heads; interleaving in time
(not even true threads) corrupts the chain. Realistic. Keep **Medium**, certainty [Probable].

**P6-01 (blocking IPC, no timeout).** Challenge: MVP, low traffic. Ruling: still a correctness hole
that also undercuts kill-switch latency. Keep **Medium**.

## Findings I am withdrawing or explicitly softening
- No Critical findings. The strongest security defects (P1-01, P2-01) each have a surviving backstop
  (HITL for the first; the signed `consume` for the second), so I decline to rate anything Critical.
  Overstating severity would itself be an audit failure.
- I withdraw any implication that an ordinary in-process agent can, *today*, disable IGK or forge a
  human approval that causes actuation. It cannot: agents hold no file tool (`src/tools.py:24-26`),
  no `igk` import (`src/agents.py`), and no `AuditLog` handle beyond what the orchestrator injects.
  The real exposures are (a) environmental/operator-level (spawn failure, key deletion, config
  mutation before construction) and (b) forensic (unsigned verdict log).

## What I could NOT verify (and why)
1. **LIVE mode** — no `ANTHROPIC_API_KEY` (moved out today) and the sandbox is offline. Every
   real-provider branch (`src/llm.py:40-52`, `src/providers.py:21-22`) is unexercised; all evidence
   is MOCK-path only.
2. **OS/TEE key isolation** — single-machine assumption; not testable in this environment.
3. **Secret values / git history for leaked secrets** — `.env` and `.kernel_key` were moved out and
   correctly not read. Additionally, `git` was **not accessible** from the workspace mount for the
   vault path (`git` reported "not a git repository" at the mount boundary), so I could not scan
   commit history for previously-committed secrets. This is a real gap: pre-move secret exposure in
   history is unverified. `.gitignore` does list `.env`, `*.key`, `**/.kernel_key`,
   `logs/igk_state/` (evidence: repo `.gitignore`), which is the correct posture going forward, but
   says nothing about what was committed before those rules existed.
4. **LANGAR bot** — not in the granted path (Pass 3); entirely unverified.
5. **Real concurrency** — the suite is single-threaded; P5-02/P6-01 concurrency claims are reasoned,
   not observed.
