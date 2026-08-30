# 00 EXECUTIVE SUMMARY — A01 Repository Cartographer
Observed 2026-08-16, ~23:30–24:00 local (+10:00). READ_ONLY. No project file modified.

## Headline answers (special questions)

1. **Is OCTOPUS one repository or multiple partial systems?**
   Multiple partial systems under one roof. The main organism runs from `F:\backup\_ops\` inside the
   vault repo `F:\backup` (branch `equip/g10-cognition-20260816`, HEAD `028fe81` 23:27 tonight,
   219 dirty entries, remote `germline` → `E:/germline/octopus.git`). Around it: a **nested git repo**
   (`07 - Knowledge/genome-system`, whose files are *also* tracked by the root repo), **5 active Claude
   worktrees + 2 orphaned archived ones**, a **separate actively-developed git repo on the Desktop**
   (`OCTOPUS-NBB-CP-WORKING`, commit today 16:02, remote = a git-bundle file inside the vault), and
   **~12 Desktop checkouts frozen at legacy commit a3000f0 (2026-07-14)**.

2. **What exact executable begins the main organism runtime?**
   `F:\backup\_ops\RUN-ORGANISM.bat` → `OCTOPUS-flags.cmd` (env flags) → `python -X utf8 organism.py`.
   Live right now: PID 29028 since 12:53, port 8771, beat 38507, state ts 23:49:11. Five more companion
   processes are live (cortex :8772, live-room :8773, telegram center, board_cp queue, miniapp gateway),
   plus **10 Windows scheduled tasks** (watchdogs, observatory, doctor-day, 4d poisoning watch).

3. **Which alleged L0–L8 layers exist in current code?**
   None under that scheme. The project's own architecture SoT (`_ops/ARCHITECTURE-LAYERS-2026-07-27.md`)
   defines **7 engineering layers — 0 Body … 6 Interface, + S Safety** — all with real components on disk.
   "L0–L8" matches no current document or module. (NBB-CP separately uses pytest markers l0/l1/l2 =
   kernel/adapter/replay test tiers.)

4. **Are Policy Gate and Viability Loop executable, test-only or documentary?**
   - **Policy Gate**: two distinct things. `_ops/policy/policy_gate.py` (ADR-033, fail-closed,
     DENY/QUARANTINE on ambiguity) is executable, imported by the live `wiring.py` and `talk_gate`,
     with tests → **VERIFIED_CODE_ONLY (wired; live enforcement not directly observed tonight)**.
     `4d_system/control_plane/policy.py` is a **pure, non-enforcing policy ladder by its own docstring**
     (documentary/shadow). A third, `_ops/octopus_v3/` P0 execution gate, is complete but explicitly
     **WIRED=False**.
   - **Viability Loop**: **NOT_FOUND** — zero Python matches for "viability" in any organism tree.
     Nearest real thing: the allostatic `heart/` (control_law, pulse_arbiter, work_pump) + FREEZE-on-
     conflict telemetry (I3). The claim as phrased is DOCUMENTED_NOT_IMPLEMENTED.

5. **Which source directories are imported during startup?**
   `_ops/budget` (opslib/telemetry/governor_epoch/fitness/replication/approvals/money_gate/organ_gate),
   `_ops` root modules via `wiring.py` (4,347-line composition root: legs, heart, neural, epistemics,
   spectral, chord, spine, policy…), `_ops/cortex` in its own process. **Not** imported: `4d_system/**`
   (observe-only lane), `nbb_cp` (no live process), `octopus_v3` (unwired), genome-system code (only its
   ledger file receives appends).

## Three things the council must know tonight

1. **LIVE INCIDENT — the organism is running FROZEN.** `_ops/budget/FREEZE.flag` exists since
   2026-08-16T20:09:05: "settle failed for ARCHITECT_SYS: [Errno 22] Invalid argument:
   budget-state.json" (Windows file-handle error). Live state confirms `frozen: true` while the loop
   keeps ticking. All budget grants are fail-closed frozen. Owner-visible spend this month: AU$0.74.
2. **The "OCTOPUS claims" map poorly onto the organism that actually runs.** Of the brief's hypotheses:
   VERIFIED_LIVE: propose-only legs, live hash-chained ledger (11,444 records, last append 13:44Z),
   live `identity_health` (0.542), money fail-closed in practice (stub approval channel ⇒ every
   >AU$20 request auto-denied). VERIFIED_CODE_ONLY: mutual-veto dual brain (tested, but behind an
   env flag that is NOT set; verdicts arrive as parameters, and neither 4d_system nor NBB-CP runs as
   a brain process tonight). CONTRADICTED: "L0–L8", "ledger is bitemporal" (it is a unitemporal
   append-only hash chain with an age_tick counter), "A2 bounded-auto / A4 needs approval" (the real
   ladder is A0–A6; A2 is currently BLOCKED by VQ-SELFGOAL-002; A3 generates owner vote cards;
   A4/A5 are structurally pathless per `action_bridge/integration.py`). NOT_FOUND: Sensorium,
   Viability Loop, physical legs ("legs" are business ventures: lead/ziman/mining/crypto/cartographer).
3. **NBB-CP exists as three divergent forks** (vault `03 - Projects`, embedded in `4d_system/src`,
   Desktop working repo — the only one under active development, today). Plus repo-in-repo anomaly at
   genome-system and stale lore inside live code (`app.py:8768` lock that has no app.py;
   `4d_system/start.bat` pointing at a non-existent Desktop path).

## Verdict

Maps are complete: a new engineer can find every startup path from `ENTRYPOINT_MAP.md` +
`FILESYSTEM_TREE.md` + `COMPONENT_INVENTORY.csv` without chat history.

**READY_FOR_NEXT_WAVE**
(with one urgent rider for A02/A03: observe the FREEZE incident live; it is the single most
information-rich runtime event available tonight, and it falsifies any claim that budget settle
is currently healthy.)
