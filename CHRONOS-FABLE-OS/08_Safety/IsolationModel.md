# Isolation Model — CFL-03 deep-drill (worker sandboxing + prompt-injection defense)

_The synthesis flagged isolation/injection as "unsolved by all four sources — biggest residual risk." This file records the concrete `[EST]` mitigation from Master Handoff §5.1–5.2. It reduces the risk; it does not solve it. Proposes INV-17* / AP-14* (pending operator ratification)._

## Threat model

Prompt-injection **will** sometimes succeed inside a worker. The design goal is not to prevent it but to make a compromised worker **harmless**: its maximum possible output is one inspectable proposal in a human-reviewed queue.

## Worker task-packet (capability-scoped, minimal)

- explicit **read allowlist** — specific document IDs; never wildcard, never the whole vault
- **scoped tools** only
- hard **budgets**: runtime, memory, tokens; `spawn = 0` by default
- **`secrets: []`** — ALWAYS empty; credentials never cross the boundary
- **output**: a single structured *proposal* to the parent; **no ledger write path**

## Process hardening (standard Linux, no special hardware) `[EST]`

separate non-root process per worker · `seccomp-bpf` syscall filter · dropped capabilities + user namespace · `cgroups v2` CPU/memory/PID caps (also enforces the cost-cap and stops spawn-bombs) · read-only rootfs · `tmpfs` scratch wiped on exit · no network namespace by default (egress only via a brokered proxy).

## Defense-in-depth (D1–D5)

| # | Layer | What it buys |
|---|---|---|
| **D1** | Process isolation | compromised worker can't reach secrets, unrelated files, or the ledger |
| **D2** | Capability-scoped context | nothing sensitive in-context to exfiltrate |
| **D3** | **Structural output confinement** (key lever) | worker can at most emit an inspectable proposal → injection buys "one suspicious item in a human queue," not an effect |
| **D4** | Brokered egress + content quarantine | external/fetched content tagged untrusted DATA at ingest; text that *looks like* a command is a claim to be tagged, not a directive |
| **D5** | Provenance integrity | proposals carry actor/clock/hash; approval is a separate human/settled event a worker cannot forge |

## Honest residual risk

- **R1** — model-layer injection: a worker can still produce a *convincingly wrong* proposal. Reduced by human review + Critic, **not eliminated**.
- **R2** — shared-silicon side-channels (timing/cache) on constrained hardware: **accepted**.
- microVM/hardware isolation is **out of scope** (no hardware) — this is the best available on Orange-Pi class.

## Proposed laws (ratify to promote)

- **INV-17\*** — *structural isolation*: a worker's max output is an inspectable proposal, by construction, not by trusting behavior.
- **AP-14\*** — *trust-boundary fallacy*: believing a worker is safe because it was *instructed* to behave; only a structural boundary holds.
