# TERRITORY-REPORT — 07 - Knowledge

findings: **7** · classes: OPEN_WORK 2 · DEBT_HIDDEN 2 · SEASON_LEFTOVER 1 · RULING_UNEXECUTED 1 · DOC_RUNTIME_DISCREPANCY 1

## top findings (rank order)

- **[KN-5] r9.8 OPEN_WORK** 60MB raw DNA + GenomeInsight PDF + derived دیتا.txt still inside vault vs rule O-04; old Silabi-Bot token revoke never c
  - `F:/backup/07 - Knowledge/_audit/OPEN_LOOPS.md` · `line 8: - [ ] **خروج داده‌ی ژنتیکی از vault** (~۶۰MB + GenomeInsight PDF… تا وقتی این پوشه در `backup` است، هر`
- **[KN-2] r5.0 OPEN_WORK** genome-system plan milestones never executed: off-site backup #3 (restic/rclone) + monthly restore drill, first real ANT
  - `F:/backup/07 - Knowledge/genome-system/plan.yaml` · `line 20: - { id: phase4_offsite_backup, done: false, note: "restic/rclone off-site copy #3 + monthly restore d`
- **[KN-4] r4.8 SEASON_LEFTOVER** Orphan quarantined in genome ledger dated 2026-09-02, file created 2026-09-08: SELF_IMPROVE_DIGEST broke hash-chain cont
  - `F:/backup/07 - Knowledge/genome-system/ledger/ledger-orphans-20260908.jsonl` · `line 1: {"type": "NOTE"… "SELF_IMPROVE_DIGEST", "n": 32, "improve_rate_pct": 16.7…"prev": "cb163d96…"}`
- **[KN-3] r4.8 DEBT_HIDDEN** genome-system daily backup promise broken: STATUS.json schedule says 'backup: daily' but _backups holds only 5 tar.gz, n
  - `F:/backup/07 - Knowledge/_backups` · `dir listing: genome-system-20260709-210644.tar.gz (newest of 5; none after 2026-07-09)`
- **[KN-8] r4.8 RULING_UNEXECUTED** OCTOPUS-TRUTH open-work list: independent verify_live_store.py never run on live DB, ADR-041 still missing from F:\backu
  - `F:/backup/07 - Knowledge/OCTOPUS-TRUTH-2026-08-15/09-OPEN-WORK.md` · `table row ۱: اجرای `scripts/verify_live_store.py` روی دیتابیس زنده… تا زنجیرهٔ زنده مستقل تأیید نشده، شاهد قاب`
- **[KN-9] r4.8 DEBT_HIDDEN** CURRENT-REALITY: 4 legs dead (mining/crypto/studio_pf/knowledge), daemon 4d stopped since Aug 2, 14 hypotheses untested 
  - `F:/backup/07 - Knowledge/Architecture/CURRENT-REALITY.md` · `line 11: - ۴ پا مرده (mining/crypto/studio_pf/knowledge)`
- **[KN-1] r3.0 DOC_RUNTIME_DISCREPANCY** genome-system loop retired 2026-07-17, but plan.yaml still status:active and Knowledge index still promises 'plan-gated 
  - `F:/backup/07 - Knowledge/genome-system/plan.yaml` · `line 9: status: active`

## coverage

- inventory files_total (md/json/txt ≤2MB): 723
- read: ~46/706
- method: AREA docs + STATUS/plan deep reads + marker grep
- excluded: knowledge-base bodies listed only
