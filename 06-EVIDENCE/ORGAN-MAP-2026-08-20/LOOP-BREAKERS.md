# T71 — loop breakers (sidecar; not telegram files)

Implementation: `_ops/organs/loop_breakers.py`. State under `_ops/state/organs/` only.

## R1 sentinel

`metric_count(-1)` → `{semantic: UNKNOWN, render: نامعلوم, value: null}`. Non-negative metrics never publish a negative.

Live `c6_producer` still *stores* `baseline_count: -1` (honesty: not measured). This session does not patch that hot file; render must go through `metric_count`. RFC to wire render into doctor display (not telegram).

## R2 tool-request loop

- `request_key = hash(need + target + capability)`
- max 2 attempts then `TOOL_REQUEST_QUARANTINED` (24h)
- rejection reason returned to generator
- already-allowed capability → `DENY_ALREADY_ALLOWED` (no card)
- `shell.full` / `shell.raw` → `DENY_BY_POLICY`

Does **not** write `_ops/state/telegram/tool-request-state.json`.

## R3 RFC flood

`merge_rfcs` clusters by bottleneck prefix, cap 8 open. Live `doctor/rfcs.json` currently has **2** rows (1 stale-input, 1 applied) — flood is historical, not present. Duplicates-merged flag true (nothing to merge).

## R4 autotune zero-evidence

One incident → one card until evidence changes. Second `evidence=0.0` suppressed.

Not hooked into `cortex/improve.py` (live process). Filter is ready.

## R5 halt record

Each halt gets `cause_machine`, `repeat_count`, `root_rfc_id`. First record this session: `afferent_starved` → `RFC-halt-9052b82a`.
