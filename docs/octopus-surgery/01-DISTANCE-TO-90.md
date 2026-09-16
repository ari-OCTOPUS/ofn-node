# Distance to 90% — evidence-bounded draft

Default claim envelope: `node_id=octopus-continuity-180`,
`asserted_ip=192.168.0.180`, `vantage=cursor-this-host-only`,
`scope=this_host_only`; evidence is HEAD `2a718aaa96235fcf5aa5219d25eba4a9b314eed5`
plus the reproducible commands in `receipts/`.

## Scores

| Dimension | Weight | Score | Reproduced evidence | Main blocker |
|---|---:|---:|---|---|
| Runtime correctness | 15 | 45 | NBB 189/189; isolated safety suites passed | Root runner is non-hermetic and full runtime was not exercised. |
| Safety boundaries | 15 | 45 | Action bridge 66/66; cognition 95/95; capability policy + architecture guard 11/11 | Narrow cognition is deny-list protected; broader provider inference and approved executor components are explicitly classified. |
| Evidence integrity | 15 | 53 | Receipt downgrade, hash-chain/replay tests, controlled detector fixture | Current observatory verifier and restore receipt are absent. |
| Real-world grounding | 15 | 30 | Observation/envelope code and offline fixtures | No current calibrated real sensor slice; `observation.v1` contract is partial. |
| Measurement quality | 15 | 20 | Historical Brier prose only | `run_observatory.py`, predictor and 27/27 verifier are absent from HEAD. |
| Governance | 10 | 40 | Owner-gate binding/replay tests | D1/D7 and owner signing remain closed; HMAC is not Ed25519 governance. |
| Operations/recovery | 10 | 35 | Local rollback test and historical runbooks | No restore drill reproduced at this commit. |
| Documentation/handoff | 5 | 55 | Extensive maps and handoffs | Material contradictions and stale paths remain. |

Weighted result:

```text
(15×45 + 15×45 + 15×53 + 15×30 + 15×20 + 10×40 + 10×35 + 5×55) / 100
= 39.20
```

Reported precision: **39% ± 7%**. The narrow cognition/planner/world-model set has no proven
shell, sender, payment or hardware handle and is now architecture-enforced. The active cap remains
**40%** because the broader operational system still has executor paths and no current independent
full-system verification.

Separate completion estimates:

- `CODE_COMPLETION: 56% ± 7%` — one machine-enforced architecture boundary was added.
- `EVIDENCE_COMPLETION: 41% ± 8%` — detector mutation and bounded source policy are reproducible.
- `OPERATIONAL_COMPLETION: 29% ± 9%` — live artifacts exist, but this vantage did not reproduce runtime,
  independent observatory measurement, governance promotion, or restore.

## Reproduction anchors

- NBB collection: 189; SHA-256 `7366ff5c446c2faa25ccb65f35db3ef6b5d74bed036e2509c7be3bca5df3fdd4`.
- NBB test: 189 passed; SHA-256 `a2c282c0737ea2fe45fa61ae5b0a8e219c99e9701c2b4d3ec01863b91bb17e54`.
- Action bridge: 5/5, 24/24, 25/25, 12/12.
- Cognition fixture suite: 95/95.
- Shadow-homeostasis: 18/18.
- Current runner registry: 820 present suites, not the historical 320.
- Gap probe SHA-256: `c9e9b14a336a4f7d6a5531be10b1132435b657e20aeb395fa892e6571c5c1320`.
- Cognition authority guard: 11/11; SHA-256 `3a4ffcdf50ecf2f0c0aac8438e09c4d9c428d336ffda4fb4e647575fc6296b3c`.
- Registered runner invocation: 1/1 suite; SHA-256 `c7aeae2fd4b5d34a469759c16b2be7938934a4ed20d9edb9c09147c4e614b0d7`.

## Scenarios

- Conservative: **33%** — treat runtime prose and historical receipts as unverified.
- Likely: **39%** — credit the executable authority guard and reproduced narrow suites.
- Optimistic under current gates: **40%** — the safety-separation cap still applies.

## Critical path to 90%

1. **Completed in Phase-1:** capability-aware cognition deny-list with controlled violation fixture.
   Next, address only newly detected boundary violations; do not split safe provider inference.
2. Recover or rebuild an independent observatory strategy and verifier at the current commit.
3. Complete one immutable, calibrated, uncertainty-bearing, read-only sensor slice with replay.
4. Reproduce a hermetic full baseline without network or live-state writes.
5. Complete owner signing verification while keeping private material outside the repository.
6. Exercise rollback and restore in a non-production environment with independent receipts.
7. Re-score only after every critical gate passes; test volume alone cannot raise the cap.
