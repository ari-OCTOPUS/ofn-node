# ARCHITECTURE FACTS — verified on board unless marked otherwise

## Project status
- OCTOPUS is NOT approved for production. PRODUCTION=FALSE, D7 not
  authorized, owner-signature/independent-audit gates remain blocked.
- Live authority (this boot, from state/snapshots/latest.json):
  readiness_profile=WAVE0_OBSERVE_ONLY, operational_mode=OBSERVE_ONLY,
  actuator_authority=NONE, leg_authority=DENIED, mqtt_state=DISABLED.
- The Observatory is read-only, fail-closed, one-gateway. External
  effects are prohibited. Stability metrics and NATS monitoring are
  loopback-only by design.
- Hypothesis Engine has simulation evidence only; default flag OFF,
  propose-only. Metacontrol exposes would_decide; executed is always none.
- GAP-001 (boot readiness): SOFTWARE_REBOOT_PASS_POWER_LOSS_UNTESTED;
  second consecutive PASS observed on boot 4dbf4819 (2026-08-17 10:27).
  Closing it and GAP-002 (DEFERRED_TO_WAVE1) is an owner decision.
- No git repositories exist on this board. Versioning = release trees
  (/opt/octopus/releases/*) + SHA256SUMS + hash-chained ledgers.

## Known incident (root cause already identified, fix applied by OWNER)
- persist_observation → _update_indexes rewrote six multi-MB JSON indexes
  per observation: ~22.6 MB written per observation, ~196 GB written
  06:40–09:39 on 2026-08-17 (eMMC wear risk). Evidence tuples and the
  tainted-window markings live in /var/lib/octopus/evidence/stage0/ and
  the session report SESSION-REPORT-20260817T0943Z.md.
- Owner applied CHG-2026-0817-019/020/021 (CPU fix, verifier boot_id,
  hostname) and performed an authorized reboot at 10:27 (boot
  4dbf4819-c7dc-4224-bb3b-2650f9d2aa6c). Post-reboot observation:
  sensorium steady-state ≈ 1.6 MB disk writes / 10 s and ~8% CPU
  (vs 135.7 MB / 10 s and ~100% CPU in the tainted window).
  CAUTION: the live code still contains the _load_index/_save_index
  pattern, and a fresh-boot window is a quiet window — this is
  INCONCLUSIVE as formal validation. That is exactly what the
  Mini Scientist frozen-criteria experiment (P2–P5) must prove.

## Evidence discipline (from prior sessions — keep following it)
- Direct terminal output outranks old planning documents; re-check
  reported values before relying on them.
- A reported "93 Observatory tests passing" exists in project history;
  the live release manifest records 79 passed / 0 failed at build time
  (RELEASE.json). Rerun tests from the correct repository root before
  asserting current validity — a wrong-root green run already happened.
- gap001/verifier.json is rewritten each boot by the probe; its hash
  changing across boots is expected. The other two authority hashes
  must be bit-stable.

## Sensor reality (2026-08-17 session)
- 103 sensors in registry: 4 ACTIVE, 2 discovered-unbound, 66
  MANIFEST_ONLY (heartbeat only), 29 disabled, 2 stale. 0 external
  physical sensors (only on-board SARADC). Power observability:
  NOT_INSTRUMENTED (INA219/INA226 proposed, owner decision).
- MANIFEST_ONLY emits heartbeat only; measurement is null; never
  zero-filled.

## Owner workflow (the only path to authority)
- Board exports unsigned artifacts to /var/lib/octopus/inbound/TO-LAPTOP/.
- Owner reviews (Obsidian vault) and signs on Windows (sign-*.bat with
  existing root-v2), drops bundles into inbound/SIGNED-*-BUNDLE/.
- Board path units verify and apply. Unsigned local JSON is not authority.
