# Ziman Cycle Repair Runbook

## Package

Importable from worktree root:

```
cd F:\wt-ziman-cycle-repair-20260910
python -m ofn.ziman_cycle --help
```

No PYTHONPATH hacks required when run from worktree root (`ofn` is a package).

## Canonical runtime

Canonical Ziman cycle runtime is `ofn.ziman_cycle` (CLI/package). Do **not** treat `F:\backup\_ops\legs\ziman_leg.py` as the repair target or wire it into node/worker for this merge plan (G7 = discovery only; leg non-use).

## CYCLE-4 dry-run

```
python -m ofn.ziman_cycle dry-run-cycle4 ^
  --prior F:\backup\00-SEASON\ziman-internal-cycle-3\ZIMAN-INTERNAL-CYCLE-3b-20260910-SKU-CONFIRM.json ^
  --catalog "F:\backup\03 - Projects\Ziman Galerry\03-Offering\ziman-catalog.json" ^
  --out-dir F:\backup\00-SEASON\ziman-internal-cycle-4
```

Expected verdict/readiness: `READY_FOR_OWNER_INPUT_INTERNAL`

## Locks (fail-closed)

- publish=false
- external_send=none
- hold_external=true
- use_llm=false
- safe_to_claim=false

## SKU policy

Owner answered `YES_USE_PRODUCT_ID` — status `GROUNDED_OWNER_CONFIRMED` must be preserved.
