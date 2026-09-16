# OCTOPUS HEART DEEP-AUDIT — 2026-08-25

**Owner KEEP (locked):** three hearts + `pulse_arbiter` — do not delete / rewrite voting contract.
**Lane:** Ios vault audit only. No live production-wire flip without owner GO.

## Live snapshot (2026-08-24 ~23:37 AEST)
- arbiter: GREEN, consensus ~98.34s, 3/3 present, `wire_open=true`, `advisory_only=true`
- votes: cardiac ~42.4s (mice) | control_law ~264.9s | rhythm ~79.4s
- heart.shadow: period ~266.8s, `production_wire.open=false` (Gate-0 delta_self=0 + SIM hash)
- organ-heart registry: live_state=shadow, R2/L2

## KEEP (owner)
- `cardiac` / `control_law` / `rhythm` as the three vote producers
- `pulse_arbiter.py` consensus + color + brake contract
- `state/pulse/arbiter-latest.json` schema pulse-arbiter.v1

## ON THE TABLE (auditable — not yet GO)
1. **Shadow vs live split** — arbiter advisory vs hybrid `shadow.production_wire` CLOSED. Clarify single SoT period (organism sleep vs shadow 266s vs arbiter 98s).
2. **producers.py Gate-0** — velocity/CPI/Δ_self; delta_self=0 forever blocks wire. Audit whether Gate-0 is still the intended lock.
3. **doctor_setpoint + interface (ADR-001)** — Doctor proposes band, not period. Keep unless owner later says otherwise.
4. **work_pump / heart_wires** — jobs/thesis/coherence on beat; trim dead cadence?
5. **money_pulse / life_economy / fuel_meter / budget_judge** — adjacent pulses; confirm still heart-axis or move out.
6. **sog_math + sim_heart + locked equations** — hash mismatch is one CLOSED reason; audit lock freshness, do not silently rehash.
7. **State rot** — large jsonl (arbiter-shadow, fuel-stream, tick-timing, quarantines 2026-08-08). Archive, do not delete live latest.
8. **Metaphor docs vs code** — HEARTS-BRAINS-4D-STATUS / Metaphor Decode drift vs live 98s/266s.

## Do not do this wave
- Rewrite arbiter voting / remove a heart
- Flip `OCTOPUS_WIRE_PULSE` / production_wire without separate owner GO
- Invent Δ_self to open Gate-0

## P1 Gate-0 + P2 SIM lock (2026-08-25, no apply)

- GATE0-AUDIT.json: INTENDED_LOCK. Estimator healthy (336>=48, authoritative) but delta_self_live=0.0 because confirmed/effects have zero variance. Velocity is metronome-only (confirmed=0, effects=0). Do not invent CONFIRMED or flip Gate-0.
- SIM-LOCK-DIFF.json: HOLD_UNTIL_OWNER_GO. Live control_law.py sha256 != HEART-SIM-REPORT (2026-07-11). sog_math.py != lock provenance (2026-07-10). Do not auto-rehash.
- production_wire stays closed. Arbiter KEEP untouched.


## P0 + P3-P7 + full inventory (2026-08-25T08:16:03+10:00, no apply)

- SOT-PERIOD.json: sot=split. advisory 97.2s vs shadow 259s vs sleep 255s.
- ADR001-CHECK.md: HOLDS. live band 0.46-4.45, cap 2000. Doctor does not write period.
- WIRES-DEAD.md: search paid-skip; web_research ingest skip; life_economy RETIRED is stale; heart_wires 18h stale.
- BOUNDARY-MONEY-LIFE-FUEL.json: stay fuel+budget_judge; extract later money/life_*.
- JSONL-ARCHIVE-PROPOSE.json: 8 rotate candidates; never rm latest.
- DOC-DRIFT.md: 2026-08-25 live SUPERSEDE row. Named old status files not at vault roots.
- INVENTORY.json: all 22 heart/*.py + adjacent wires/off/uniqueness listed. Code unmodified.

## P6 rotate + P work_pump diag (2026-08-25T08:28+10, scoped GO B+C)

- JSONL-ROTATE.json + jsonl-archive-20260825T082805\: 6 ROTATED (observe sinks truncated, files kept), 2 ARCHIVED_NO_TRUNCATE (velocity-stream, fuel-stream — Gate-0/fuel readers). *-latest untouched.
- JSONL-ROLLBACK.md: copy /Y archive back over live for ROTATED only.
- WORK-PUMP-DIAG.md: INTENDED_LIVE. life_economy RETIRED is metaphor, not a gate. OCTOPUS_WIRE_HEART_WORK=1 left ON. No apply.
