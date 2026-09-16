# 2026-07-31 · RESTART VALIDATION CHECKLIST — Wave 0 + Telegram
**Use:** when owner says "restart now" (after TG agent finishes). Run step-by-step.
**Mechanism:** file-contract (stop-organism.ps1 → RUN-ORGANISM.bat), NOT manual kill.
**Owner runs the .bat; agent validates before/after.**

---

## PRE-RESTART (confirm before touching anything)

### P1. Confirm no global halt active
```
ls "F:\backup\_ops\HALT-ALL"           # must NOT exist
ls "F:\backup\04 - Architect System\STOP"  # must NOT exist
```
If either exists → DO NOT restart (RUN-ORGANISM refuses under global halt).

### P2. Confirm my Wave-0 changes are committed + clean
```
git -C F:\backup log --oneline -1          # expect 260a0f9 (Wave 0) + later commit
git -C F:\backup status --short _ops/wiring.py _ops/budget/opslib.py _ops/budget/telemetry.py _ops/budget/budgets.yaml _ops/outcomes/taxonomy.py
# if empty = all committed; if dirty = the signals-fix + VQ-closure (stage them first)
```

### P3. Decide: arm OCTOPUS_HEBBIAN_LEDGER now or later?
Owner choice (deferred in this session). If arming:
- Edit `_ops/OCTOPUS-flags.cmd`, insert after line 536 (`set OCTOPUS_HEBBIAN_RICH=1`):
  ```
  rem W2 (2026-07-31): Hebbian ledger — emit spine events for observed co-occurrences.
  rem Read-only instrumentation; changes no decision. Delete line to revert.
  set OCTOPUS_HEBBIAN_LEDGER=1
  ```
- No companion registration needed (no flag scanner exists).
- Default = leave OFF unless owner wants Hebbian logging visible immediately.

### P4. Capture baseline (before restart, for comparison)
```
python -X utf8 -c "import json; s=json.load(open(r'_ops/state/ORGANISM-STATE.json',encoding='utf-8')); print('PRE beat:', s['beat'], 'ts:', s.get('ts'))"
```
Record the beat number. After restart, beat should ADVANCE (proves new loop is live).

---

## RESTART (owner executes; agent supervises)

### R1. Owner runs the file-contract restart
```
F:\backup\_ops\RESTART-ORGANISM.bat
```
This script: (1) stop-organism.ps1 (clean STOP-ORGANISM file → old loop exits at next tick),
(2) RUN-ORGANISM.bat (fresh organism.py with new env).
**DO NOT manually kill PID.** The file contract is the safe path.
~10s downtime expected. A NEW black window opens = the organism. Leave it open.

### R2. Guard against double-spawn
RUN-ORGANISM checks port 8771 before booting. If a second .bat runs, it sees the listener
and exits ("already" branch). So only ONE organism will be live.

---

## POST-RESTART VALIDATION (agent runs these; all must pass)

### V1. Organism came back alive
```
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8771 -State Listen | Select OwningProcess"
# must show a PID (new one, not the old 1704)
```

### V2. Beat is ADVANCING (the single most important proof)
```
python -X utf8 -c "import json; s=json.load(open(r'_ops/state/ORGANISM-STATE.json',encoding='utf-8')); print('POST beat:', s['beat'], 'ts:', s.get('ts'))"
# wait 60s, re-run. beat MUST increase. If frozen → W0.2 fsync did NOT work, investigate.
```

### V3. ORGANISM-STATE healthy
```
halted=None, frozen=False, stop_organism=False  (all must be clean)
```

### V4. Wave-0 changes took effect
- **W0.2 fsync:** no `.tmp` files stranded beside state/*.json; no new entries in
  `_ops/state/write-failures.jsonl` (only grows on real failure).
- **W2 Hebbian:** IF OCTOPUS_HEBBIAN_LEDGER=1 was armed (P3), check spine.db:
  ```
  python -X utf8 -c "import sqlite3; c=sqlite3.connect(r'_ops/state/spine/spine.db'); print('hebb.observation count:', c.execute(\"SELECT count(*) FROM events WHERE event_type='hebb.observation'\").fetchone())"
  ```
  Should be >0 after the first 20-tick signal window closes (may take minutes if signals are sparse).
- **W0.3 doctor:** no `UNMAPPED:doctor` in telemetry (only matters if doctor spends, which it doesn't yet).

### V5. Ledger chain still valid (VQ-LEDGER-CHAIN-001 closed — confirm no regression)
```
cd _ops/tests && python -X utf8 test_ledger_reanchor_2026_07_31.py
# must stay 5/5 green
```

### V6. Telegram (if TG agent's work also needs validation)
- Per TG agent's own acceptance runbook (their domain). Agent checks organism didn't break TG wiring.

---

## ROLLBACK (if anything red)
- W0.2: `git -C F:\backup checkout 681907f -- _ops/budget/opslib.py` then restart again.
- W2: unset OCTOPUS_HEBBIAN_LEDGER (instant zero-I/O) — no restart needed.
- W0.3: revert the 2 telemetry/budgets lines.
- Nuclear: the Desktop backup zip (OCTOPUS-BACKUP-FULL-2026-07-31.zip, 4.23GB, all 99,068 files,
  SHA-256 logged) is the full restore point.

## DONE CRITERIA
V1+V2+V3 green = organism healthy. V4 confirms Wave-0 landed. V5 confirms no ledger regression.
Then mark D12 complete.
