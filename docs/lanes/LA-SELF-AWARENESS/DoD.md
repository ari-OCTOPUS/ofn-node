# DoD — Lane LA / Self-Awareness (Definition of Done)

Branch: `lane/self-awareness` (worktree `F:\wt-self-awareness`, base `origin/main` @ `33c94763005f5cf8c766701f408390c49bba0da7`).
This document is the first commit of the lane. Nothing in this lane is "almost done" — each item below is binary and each is proven with a receipt (command + SHA + timestamp + exit code + path).

## Baseline (measured before any lane change)

- Full CI suite (`python -X utf8 -m pytest tests/ -q --ignore=tests/test_live_control_panel_smoke.py --ignore=tests/test_root_hygiene.py`) at base `33c9476`: **2511 passed / 21 skipped / 0 failed** (59.46s, this host, 2026-09-02).
- Premise finding: "Day-7 reds" (2391/2340/40/11 @ `bbbf86b`) no longer exist on main — measured green above. Goal 3 of the owner order is therefore reframed as: **hold the green baseline** (regression gate) while delivering goals 1–2.

## Deliverables (all-or-nothing)

1. **Machine-written self-model** (`ofn/kernel/self_model.py` pure + `ofn/adapters/self_model_producer.py` I/O), schema `octopus.self-model.v2` per `docs/octopus-surgery/04-SELF-MODEL-SPEC.md` (concept source, unmodified). The artifact `SYSTEM-SELF-MODEL.json` is generated only by the producer from real producers. A hand-written file that claims what the system is = automatic lane failure.
2. The self-model carries, each with **per-value source + observed_at + freshness class**: live/absent member processes, active commit+branch, capabilities present/absent (registry-checked), component/sensor statuses with healthy/stale/absent/failed/unknown distinction, recent provable events (git log tail), generation time.
3. **Agent cockpit section** (`ofn/adapters/cockpit_self_model.py`) that reads from the producer (never from a hand-maintained file), reuses the cockpit envelope conventions, shows absence explicitly, never renders a fabricated/fallback number, and never paints unknown as green.
4. **Brain-probe status honesty**: probe verdict is derived fail-closed — absent evidence ⇒ `unknown`/`unverifiable`, never `healthy`; source+timestamp recorded on every verdict.
5. **Tests** (`tests/test_self_model.py`, `tests/test_self_model_producer.py`) covering the 10 mandated scenarios verbatim:
   (1) all producers present; (2) one absent; (3) several absent; (4) stale data; (5) malformed payload; (6) real zero value; (7) absent never confused with zero; (8) same input → semantically identical output (determinism); (9) cockpit never shows fake green for unknown; (10) probe fails closed without evidence.
   Fixtures mirror real producer output including absences (no `total_aud:0`-style masks).
6. **Regression gate:** full CI suite on the lane HEAD ≥ 2511 passed / 0 failed (skips may only grow).
7. **Real-run receipt:** at least one generation of the artifact from this host committed to the PR evidence, with the board member ports honestly reported `absent` (they live on board138, not this dev host) and the real HEAD sha of the lane branch.
8. **PR:** open against main, lane-only files, no forbidden path touched (see SCOPE.md), never self-merged.

## Exit statuses (exactly one)

`DONE` · `BLOCKED_BY_OWNER` · `BLOCKED_BY_FILE_COLLISION` · `FAILED_WITH_EVIDENCE`

## Rollback

Lane is additive-only: `git revert` of the lane commits or closing the PR restores base exactly; no shared file is edited; no flag, gate, workflow, or protection is touched.
