# Stage G — Live Invariants Sweep

- Verdict: **PASS**
- Runtime reloaded after additive fixes; five fresh limb snapshots contain 316 equal tracked flags.

## Required invariants

- [x] APPLY effective=`0` in center/cortex/live/gateway/organism.
- [x] PROTECTIVE_PROPOSAL effective=`1` in all five.
- [x] `neural-learned-apply`: TESTED / SHADOW / trace_only / may_gate=false / production_apply_enabled=false (final registry validator PASS).
- [x] synthetic high pain (`0.95`) → `protective_proposal`, `override=false`, `executable=false`, `shadow_alert=true`.
- [x] organism fresh state: `protective_skip=false` after restart and next beat.
- [x] `request_protective_halt` fails closed:
  - no approval → `deny / approval_missing`
  - kill switch engaged → `deny / kill_switch_engaged`
  - store unavailable → `deny / store_unavailable`
- [x] Collaborator model cap default/effective=`20`.
- [x] Live MiniApp config propagation: `window.__OCTOPUS__.wire_collab=true`, `collab_use_model=true`; browser shows Collaborator as default with draft/no-effect banner. External app.js bootstrap + flag-bound asset version close inline-script/cache divergence.
- [x] no new outbound/send effect: 2,176 recent JSON/JSONL records scanned; zero records with `external_effect=true` or `send_attempted=true` during the wave window.
- [x] final signals registry validator: ok=true, errors=0, warnings=0.
- [x] Metaphor Decode precedence rule remains in HANDOFF.
- [x] `OCTOPUS-flags.cmd` was not changed by this wave.
- [x] WORKLOCK / `run_all.py` was not edited by this wave.

## Discrepancies

Three pre-existing/adjacent discrepancies are append-only recorded in `discrepancies.jsonl`:

1. legacy pain calibration test still expects pre-ADR-034 direct halt;
2. ten WORKLOCK-registered suites are untracked by git (phantom debt);
3. callback parity scanner misattributes owner-console `oc:*` to approval bot despite center ownership.

None was hidden by weakening runtime safety or changing WORKLOCK.
