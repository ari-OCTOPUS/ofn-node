# Architecture potential ? hybrid board organism

Claim level: OBSERVED for measurements on this board. Comparison below is reasoned, not a bake-off on other hardware.

## What is running

Three local loops, no off-board cognition:

1. Event kernel: SQLite is truth, asyncio/queue is acceleration, commit-before-ack.
2. Homeostasis: sensors (MemAvailable, PSI, thermal, disk, llama RSS) drive state, never the reverse.
3. Cortex cascade: rule -> cache -> local Qwen3-0.6B on 127.0.0.1:8081 -> owner. External API disabled.

Identity is an append-only hash chain. Memory is episodic rows tied to `source_event_id`. Systemd keeps llama, organism, and soak after process death and after reboot (OWNER_ALIVE_C proven once).

## Compared with common alternatives

### Cloud-first agent (laptop + API)

Potential: stronger language, faster iteration.
Cost on this mission: identity and memory live off-board; a network cut is a personality cut. Forbidden by lab boundary (no egress, model expendable, kernel not).

### Single-process chatbot on the board

Potential: fewer files, easier demo.
Cost: one OOM or llama crash takes identity and event log with it. We already measured the inverse: llama death degrades cortex only; kernel and heartbeat continue.

### Pure rules, no local model

Potential: deterministic, tiny RSS, no 400MB GGUF.
Cost: owner asks that need paraphrase fail closed as NEEDS_OWNER. Useful as the first two cascade steps; not a replacement for the third.

### Fine-tuned large local model (7B+)

Potential: better language.
Cost on 4GB RK35xx + eMMC: MemAvailable already the scarce resource. T4 showed large eMMC write deltas under inference. A bigger model would force SAFE_HALT sooner. Model is expendable; buying RSS with identity risk is the wrong trade.

### This hybrid (chosen)

Potential that is already evidenced here:

- Continuity after reboot without a human start (units enabled, asks recalled, chain internally consistent).
- Fail-closed cognition: invalid ask does not become a fake answer.
- Observable body: public JSON for other agents, letter only when health leaves OBSERVING/STABLE.
- Bounded growth: one habit (heartbeat 120s -> 180s) can be shadow-tested and rolled back.

What it does not buy:

- Intelligence. 0.6B is a local tool, not a mind.
- External trust. Chain scope is INTERNAL_HASH_CHAIN_CONSISTENCY only.
- Production OCTOPUS. This is BOARD-LIFE-001, lab only.

## Use cases that fit this architecture

- Night watch on a sensor/board that must remember what happened if power returns.
- Owner-gated local Q&A when the WAN is down.
- A rehearsal ground: any invariant proven here can later be copied into OCTOPUS, not invented there.

## Use cases that do not fit

- Customer chat, payments, genome, secrets, WAN actions.
- Anything that needs a silent quality downgrade when the local model is weak.

## Next cheap experiment

Keep soak as a unit. Compare morning hashes and heartbeat median against NIGHT-WATCH-PLAN.json. Do not reboot unless a unit fails to come back after a process kill.
