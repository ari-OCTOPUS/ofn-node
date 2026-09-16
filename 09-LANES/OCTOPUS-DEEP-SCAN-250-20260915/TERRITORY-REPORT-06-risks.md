# TERRITORY-REPORT — 06-RISKS

findings: **3** · classes: RULING_UNEXECUTED 1 · DEBT_HIDDEN 1 · OPEN_WORK 1

## top findings (rank order)

- **[SML-2] r4.8 RULING_UNEXECUTED** TCB #3 ratify (C-035 anchor patch) PATCHED-UNSIGNED; real 3-key rotation D3 still open
  - `06-RISKS/OPEN-GATES.md` · `line 61-63: ratify TCB #3 (C-035 anchor patch) | PATCHED-UNSIGNED ... چرخش واقعی سه کلید (D3) | OPEN تا ابطال `
- **[SML-3] r4.8 DEBT_HIDDEN** P10 daily_cap wiring bug (daily_pool->0.0) recorded OPEN with fix promised in FASE 6, never landed
  - `06-RISKS/OPEN-GATES.md` · `line 76: P10 root-cause (daily_cap) | cardiac-budget.json بدون daily_cap -> daily_pool=0.0؛ اصلاح در FASE 6 | `
- **[SML-4] r2.6 OPEN_WORK** improve-to-digest chain READY-FOR-OWNER-VOTE since 2026-08-19, no vote recorded
  - `06-RISKS/OPEN-GATES.md` · `line 67: improve->digest | READY-FOR-OWNER-VOTE — کد بسته، فقط رأی زندهٔ مالک لازم | READY`

## coverage

- read: n/a (carried group; per-item anchors in FORGOTTEN-250.json)
