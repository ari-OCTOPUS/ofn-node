# Octopus Runbook Quick Index

**Location:** `F:\backup\_ops\observability\`  
**Principle:** All scripts are read-only, stdlib-only, additive. They never write state, never FREEZE, and never restart the organism.

---

## Files

| File | Purpose | Run |
|------|---------|-----|
| `OPS_RUNBOOK.md` | Full troubleshooting playbook with symptom tree, decision map, and file reference. | Read |
| `health_check.py` | Broad system health: flags, organism state, organ state, budgets.yaml, germline, gitwrite, ledger fallback, organ gate, activation flags. | `python health_check.py` |
| `budget_monitor.py` | Budget-specific: per-organ cap vs spent, telemetry divergence, spike detection, recent organ_gate denials. | `python budget_monitor.py` |
| `flag_monitor.py` | Flag consistency: panic flags, activation flags, flag age (stale STOP/FREEZE). | `python flag_monitor.py` |
| `leg_monitor.py` | Worker isolation: static scan of leg files for wildcards, spawn, secrets, external imports; organ coverage check. | `python leg_monitor.py` |
| `RUN-HEALTH-CHECK.bat` | Windows batch that runs all four scripts in sequence and returns the highest exit code. | Double-click or `cmd /c RUN-HEALTH-CHECK.bat` |

---

## Exit Codes

All scripts use the same convention:
- **0** = healthy / no issues
- **1** = warning (review recommended)
- **2** = error (action required)

`RUN-HEALTH-CHECK.bat` aggregates: `max(exit_code)` across all scripts.

---

## Common One-Liners

```batch
:: Full suite (Windows)
cd _ops\observability
RUN-HEALTH-CHECK.bat

:: Individual checks
python health_check.py
python budget_monitor.py
python flag_monitor.py
python leg_monitor.py

:: Pretty-print just the overall result
python -c "import sys,json,health_check; sys.stdout=__import__('io').StringIO(); ec=health_check.main(); d=json.loads(sys.stdout.getvalue()); print(d['overall'])"
```

---

## Decision Tree (Condensed)

```
Any STOP / HALT / FREEZE active?
  YES → Read flag → Resolve root cause → Delete flag (owner only) → Re-run suite
  NO  → Run suite

budgets_yaml = err?
  YES → Restore from germline backup → Re-run

organ_spending = err?
  YES → Check caps in budgets.yaml → Propose diff or wait

gitwrite = err?
  YES → Resolve git issue → Delete GITWRITE-FAILED.flag

leg_files = err?
  YES → Fix wildcard / spawn / secrets → Re-verify
```

---

## Invariant Reminders

- **I1:** Scripts are append-only observers. They never write ledgers.
- **I2:** `budget_gate` is the single enforcer. Scripts only observe.
- **I3:** If divergence is detected, scripts **report** it (propose-only). They never auto-FREEZE.
- **I6:** Thresholds are read from `budgets.yaml`. Scripts have safe defaults for missing files.

---

*Index version: 2026-07-21*
