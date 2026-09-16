# 06 RECOMMENDATIONS — A01 Repository Cartographer (2026-08-16)

All actions below are for the **owner or a wired lane**; none are taken by council agents (read-only).
Ordered by priority.

## Owner decisions needed (blocking)
1. **FREEZE incident (R-01)**: after A02/A03 root-cause the Errno 22 settle failure, decide: (a) clear FREEZE and re-run settle once the file-lock fault is fixed; (b) add a freeze reason journal + recovery runbook; (c) add a high-water alert if freeze persists > N hours. Do not clear before root cause — fail-closed is correct.
2. **NBB-CP canonical home (R-02)**: choose one of the three forks (recommendation: the Desktop `OCTOPUS-NBB-CP-WORKING` repo is the only actively-developed one — promote it; or move its remote from a bundle file to the germline bare repo). Mark the other two as read-only mirrors; record in an ADR.
3. **genome-system nesting (R-03)**: decide submodule vs untrack vs remove nested `.git`. Until decided, treat both statuses as expected noise; never `git clean` blindly in the vault.
4. **Flag posture (R-08)**: explicit owner word per dormant governance flag: `OCTOPUS_WIRE_DUAL_VETO`, `OCTOPUS_OBSERVE_4D`, `OCTOPUS_WIRE_MINING`-family, governor-LLM lane, `octopus_v3` WIRED. A single `FLAGS-INVENTORY.md` in `_ops/` would end flag drift.
5. **Vocabulary (R-04/C-01/C-06/C-07)**: adopt the 7-layer (0–6 + S) scheme; retire "L0–L8" and "Sensorium" unless new components are created; state explicitly what "viability loop" should be if it should exist.

## Wired-lane code/doc fixes (small, safe, after owner word)
6. Fix `organism.py` docstring: port 8768 brain-lock lore → remove or point at the real lock (the :8771 single-instance bind pattern). Port 8768 is currently unowned — do NOT claim it without a process.
7. Fix `4d_system/start.bat` → point at `F:\backup\4d_system` (or delete).
8. Fix `nbb-cp-kre/README.md` install path → `F:\backup\4d_system\nbb-cp-kre`.
9. Record a ports map (`_ops/PORTS.md`): 8770 dashboard, 8771 organism, 8772 cortex, 8773 live, 11434 ollama, board_cp + miniapp (dynamic), 8768 unowned.
10. Re-run the failing tests recorded in caches (root: 5; `_ops`: 1) and triage; then decide a policy for `lastfailed` hygiene.

## For the council waves (A02/A03/A04)
11. A02: sample the six live HTTP endpoints (`/api/organism`, `/api/telemetry`, `/api/fitness`, `/api/replication` on :8771; live :8773; cortex :8772) and verify tick progression across ≥2 beats; confirm which port each scheduled task actually launches.
12. A03: verify ledger append path from `budget` settle → genome ledger (the failing settle is the prime target); check whether "bitemporal" matters anywhere in code, or only in prose.
13. A04: audit money/effect paths for any route that bypasses `money_gate`; check `board_cp/config.is_armed()` semantics; verify `NotWiredStub` is truly the only channel wired in the live profile; test the claim "A4/A5 structurally pathless" against the action_bridge executor code.
14. Cross-wave: diff the three `nbb_cp` forks once more after owner decision to confirm the canonical one (A01 diff is in 03_EVIDENCE.jsonl F-018).

## Mapping-sustainability (follow-up)
15. The cartographer leg's own map is 18 days stale with 1,143 drifted files (F-025). After this wave, run its refresh (owner-approved) so the next wave starts from a fresh map; or schedule the refresh as an OCTOPUS task.
16. Keep `COUNCIL_REPORTS/` out of the cartographer leg's vault-scan corpus (it is a council-only write zone), or accept it as drift source.
