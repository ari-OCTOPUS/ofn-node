# TERRITORY-REPORT — archive-cluster

findings: **5** · classes: SEASON_LEFTOVER 3 · DOC_RUNTIME_DISCREPANCY 1 · DEBT_HIDDEN 1

## top findings (rank order)

- **[ARC-1] r7.0 SEASON_LEFTOVER** Season handoff archived 2026-09-07 with EX1 criterion v3.0=NOT_PASSED and EX3 not started (live lane confirms unchanged)
  - `F:/backup/_Archive/Logs/HANDOFF-archive-2026-09-07.md` · `line 12: 🧭 **2026-09-07 — ورود EX1 (v3.0=NOT_PASSED، EX3 نه):** [[09-LANES/MP-EX1-CRITERION-20260907/CURRENT-S`
- **[ARC-2] r5.0 SEASON_LEFTOVER** Named metric defect P3-ORPHAN-SCALAR archived inside season worktree; 4 contradiction rows still status:open
  - `F:/backup/99-ARCHIVE/archive_wt-w1-scale-20260910/metrics/P3-DEFECT.md` · `line 5: status: named / date: 2026-09-02 (body: 'contradictions.csv rows L0-STRATEGY-BRIER ... all status: ope`
- **[ARC-7] r5.0 DOC_RUNTIME_DISCREPANCY** CURRENT-TRUTH mirror drift: archived mirror-cleanup-20260902 copy differs from live 01-TRUTH/CURRENT-TRUTH.md; 7 live co
  - `F:/backup/99-ARCHIVE/mirror-cleanup-20260902/01-TRUTH__CURRENT-TRUTH.md` · `line 1 (diff evidence): 60 lines vs live 64 lines — DIFFER; live copies also at 00 - Inbox/, 01 - Dashboard/, `
- **[ARC-3] r3.0 SEASON_LEFTOVER** Season W1-FREE lane evidence archived with 'HOLD_EXTERNAL: yes. No commit.' — findings never landed anywhere
  - `F:/backup/99-ARCHIVE/archive_wt-w1-free-20260910/09-LANES/W1-FREE/EVIDENCE.md` · `line 4: HOLD_EXTERNAL: yes. No commit. Source read-only. Live #64 send path untouched.`
- **[ARC-5] r2.8 DEBT_HIDDEN** worktree-rescue-2026-07-24: 1,120 md files from 3 dead worktrees (admiring-galileo, c3fix-verify, c7-wt) hold untracked 
  - `F:/backup/_Archive/worktree-rescue-2026-07-24/c3fix-verify/untracked/00 - Inbox/AGENT_QUESTIONS.md` · `line 152: 7. **D-G** = فقط effect-lease (idempotencyِ E18) پذیرفته؛ sleep-leg/quarantine-reader/lineage-archiv`

## coverage

- inventory files_total (md/json/txt ≤2MB): 2669
- read: 21/12901 content-examined (agent's own count incl. non-md)
- method: sampling + dup report + grep; READ-ONLY owner-deletion zone
- excluded: byte-copy masses mapped by _گزارش تکراری‌ها.txt; binaries; by-policy read-ban
