# FORGOTTEN LEADS — forensic discoveries easy to miss

1. **The stale-base deadlock pattern (now twice in one queue).** Any canary request whose
   base sha no longer matches live is refused forever (`OPS_B_STALE_BASE`) but *stays* in
   the queue consuming the component's 30-min budget window on every tick. G8-020 sat like
   this since 04:56Z; Z-SUCCESSOR-TRIO-001 (base `109e68c0` vs live `c2e290fd`) is queued
   to hit the same wall. Rule of thumb: **every failed stale attempt costs the lane 30
   minutes of budget** — supersede stale requests promptly (established dir:
   `state/superseded-tasks/`).

2. **The `\x08` regex corruption class.** Model-authored patches written through JSON can
   carry real backspace bytes inside `r"..."` strings: source *looks* right in grep, compiles
   clean, matches nothing at runtime. Acceptance harnesses that don't drive the exact
   function will pass anyway (C-001). Any future pattern-bearing artifact deserves one
   `repr()` runtime check before queueing.

3. **114/160 services are reboot-orphans.** Healthy now, but only because something/someone
   relaunched them ~15 min before the probe (nodes rebooted 01:12Z/02:46Z). Without systemd
   units the "closed learning loop" silently opens after the next power event (OW-4).

4. **`octopus-soak-witness.timer` exists and fires hourly** — the PB-1 soak has its own
   witness, independent of the Class-B witness. Not referenced in recent reports.

5. **Two queued requests were authored by `octopus-commander-editor/2026-09-14`** (TRIO,
   W3G30) — not by today's sessions. They are the tail of the G28 DAG, not orphans; do not
   "clean" them.

6. **`ops_agent.py.pre-*` backup chain lives in the live state dir** (pre-g28, pre-g28e,
   pre-g29, pre-preeffect, pre-retire, pre-retirefix) — the deploy history is reconstructable
   from these + receipt chain.

7. **The `agent_bridge` KeyError fragility**: 182's node entry in `~/octopus-mesh/config/nodes.json`
   must never be deleted (from hardware-enrollment memory; verified config still lists all 7).

8. **Email ingress is alive**: `octopus-imap.timer` fires every minute — customer replies to
   the 3 sent quotes will land even while nobody watches. No consumer alert exists for
   "reply arrived" though; the revenue loop picks it up at its 6h cadence.

9. **Worktree census**: 11+ registered worktrees across three drives; the forensic
   documentation worktree (`F:/octopus-forensic-reorientation-20260915`) completed its lane
   and can be archived by a future hygiene decision — not by this lane.

10. **Budget counter is per-component, not per-request**: superseding a stale request does
    NOT refund the budget its failed attempts burned. Expect the first G8-021 attempt only
    after ~05:52Z.
