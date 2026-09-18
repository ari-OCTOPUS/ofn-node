# M0 — Scope and identity (REVALIDATED)

GOV_VERSION=V8 · LADDER=L2 · 2026-09-17 (S2-MATURITY-EXEC lane) · no authority expansion.

## Owner scope
`evidence/s1/OWNER-SCOPE.json` (D1–D5) read verbatim; not re-asked. D2 budget = USD 100/mo,
10/rolling-24h, 2/task, stricter runtime wins. D3 real dispatch stays two-step released;
Ziman hold_external=true. D5 parallel work — subagent pool unavailable this session
(model-not-found), work serialized with per-path single writers instead; recorded as a
tool limitation, not an owner blocker.

## Fresh identity (this session's own probes, 2026-09-17 ~09:35–10:00Z)
- 138 (commander): ssh AUTHENTICATED; load 2.06; swap ACTIVE (S1 L-E); mirror sender v2 live
  (`push.sh` sha f8779ca2…, sender-ledger seq 1). Standing orders honored (no reboot, no restarts).
- 182 (witness): ssh AUTHENTICATED (root); mirror receiver v2 live (ledger seq 1,
  `0628dafd…`); W1 sidecar PID 764170 RUNNING since 09:11:20Z (planned end 2026-09-18T09:11:20Z);
  S1 frozen-window watcher PID 762748 RUNNING (sample 13 @ 09:33:21Z). Both histories preserved.
- 180/100/160/193/114: roles per handoff DATA (captured 09:07Z, AUTHENTICATED_OBSERVATION);
  persistent_job_wiring NOT_VERIFIED — carried as UNKNOWN, not re-observed this session (no
  blocking dependency taken on them).

## Halt oracle map (applicable)
- 138 organism: `ofn/budget/opslib.py` HALT-ALL + `master_halted()` fail-closed; layer-3 `ofn/kernel/halt.py`.
- 182 apply-path: two `.path`/`.service` pairs, activations frozen 07:18:32/41Z (both watchers live).
- Laptop kill-switch file path per AGENTS (F:\ofn-node\HALT) — untouched.

## Path ownership
- NEW worktree `F:/wt-s2-maturity-20260917` (branch s2-maturity-20260917 @ 31a39ee6) — single writer: this session.
- Candidate T1 files read-only from `F:/s1-t1-rehearsal-20260917/…` (bytes recorded before use).
- Node staging: `/home/ari/s2-replica-20260917/` on 138 (replica, isolated), `/root/s2-maturity-*` on 182
  (pre-existing, other-lane — read-only for me).
- Vault lane: `F:/backup/09-LANES/S2-MATURITY-EXEC-20260917/`.

## Loaded revision honesty
- S1 integrated candidate 31a39ee6 = worktree HEAD (verified). Live 138 runtime still executes its
  worktree state (S1POL/DC-03D lineage); NO deploy of the candidate is claimed anywhere in S2 so far.
- 182 sensorium live bytes = pre-candidate (originals hashed in handoff DATA).
