# 08 Open Questions — A02 Runtime Investigator (CONSOLIDATED)

## From the parallel observer

1. **Who/what restarted the fleet today?** cortex started 13:01, live/center/gateway/board_cp 16:36–16:43, organism 12:53 — staggered starts suggest manual or scripted relaunch; no supervisor identified this session (watchdogs run as scheduled tasks, not resident processes).
2. **Wire the WIRED=False overlay — when?** [owner] (OD items in CURRENT-TRUTH suggest pending owner verdicts.) What evidence will the owner require before voting?
3. **Is `frozen: true` intended?** Persistent across session while beats run. If a freeze was ordered, why do ACT-class internals continue? Needs owner/governance answer.
4. **Telegram `allowlist: false`** in channel-status — with owner_set true. Does any non-owner chat reach the center? (A04 to audit allowlist enforcement in code.)
5. **Where does `coherence 0.859` come from?** members_present=11 vs live process map of ~6 services — member accounting basis unknown.
6. **`workspace_ref` in heartbeat table** — points at what artifact? Potential observability gap if never populated.
7. **Second telegram token set (TG_ZIMAN_STUDIO_*)** — is the Ziman studio bot a separate active surface? Not observed in process map this window.
8. **chrono.db WAL 4.1 MB** — checkpointing policy unknown; crash-recovery behavior for the append contract untested.

## From the primary observer

9. **Which approval ledger is authoritative?** `_octopus/approvals.json`+`audit.log` still receive entries today (12:35:57, risk=medium) while adr-033 and cortex decision cards exist; `gated_effect` has 0 rows. Runtime cannot decide — A03/owner.
10. **[owner] Is AUTONOMY_FREE=1 + AUTONOMY_GRANT=1 intentional, and for how long?** They arm cortex free-tier auto-approval; A2 stays BLOCK only by a separate classifier vote.
11. **Is the Desktop NBB control-plane copy (C:\Users\Armin\Desktop\OCTOPUS-NBB-CP-WORKING) the intended canonical NBB-CP home?** It runs hourly outside the repo — intentional dual-brain location or accident?
12. **Why do chrono beats skip numbers?** Observed 38511→38513→38516 (2-3 advances per ~128 s window): protective skips, in-flight increments, or counter aliasing with `beat-state`'s 4163 counter?
13. **SPEND_CAP window expiry semantics**: after `UNTIL=2026-08-13`, is the AU$200/day cap meant to be open-ended (permanent gates only) or re-issued periodically?
14. **What does `OCTOPUS_QUIET_FROM=23`/`TO=7` actually suppress?** It matches the sparse events.jsonl pattern; confirm send/notify paths honor it (A04-adjacent).
15. **Heartbeat cadence variance**: base period 60 s, observed ~65 s and ~128 s in two adjacent windows, arbiter advisory 125 s — which loop decides the actual sleep (`sleep_s_after_bias` observed in state)? A15 may want a definitive model.

All items above are UNKNOWN from read-only runtime evidence; none blocks the next wave (verdict: READY_FOR_NEXT_WAVE).
