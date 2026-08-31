# Distance to 90% — evidence-bounded draft

Default claim envelope: `node_id=octopus-continuity-180`,
`asserted_ip=<redacted-private-ip>`, `vantage=cursor-this-host-only`,
`scope=this_host_only`; evidence is HEAD `2a718aaa96235fcf5aa5219d25eba4a9b314eed5`
plus the reproducible commands in `receipts/`.

## Scores

| Dimension | Weight | Score | Reproduced evidence | Main blocker |
|---|---:|---:|---|---|
| Runtime correctness | 15 | 46 | OWNER-09: 770/827 hermetic suites passed | 57 failed suites; 1 campaign scoring regression. |
| Safety boundaries | 15 | 48 | Live suite excluded; child env loopback-only | Tracked `_ops/state` and `06-EVIDENCE` were mutated during OWNER-09. |
| Evidence integrity | 15 | 68 | Full-suite sanitized log and verification-03 receipt | Residue had to be restored; Brier still absent. |
| Real-world grounding | 15 | 36 | Replay-safe observation.v1 record, fake/replay adapters, 15/15 tests | No calibrated real sensor slice; parser and record remain separate. |
| Measurement quality | 15 | 35 | OWNER-09 n=827 executed with classified failures | No Brier; 57 failures are not a quality score. |
| Governance | 10 | 40 | Owner-gate binding/replay tests | D1/D7 and owner signing remain closed; HMAC is not Ed25519 governance. |
| Operations/recovery | 10 | 34 | Clean post-test state and temporary runner artifacts | No restore drill reproduced at this commit. |
| Documentation/handoff | 5 | 68 | Artifact chain plus gap ledger plus replay-safe contract | Historical observatory narratives remain contradictory. |

Weighted result:

```text
(15×46 + 15×48 + 15×68 + 15×36 + 15×35 + 10×40 + 10×34 + 5×68) / 100
= 45.70
```

Owner 2026-08-31 accounting: table had 38 while the formula used 34.
Valid Recovery = **34**. Exact 34-weighted raw is 45.75. Official announced
figure stays **45.70** (rounding delta −0.05). See
`ACCOUNTING-CORRECTION-20260831.yaml`.

Reported precision: **45% ± 7%**. OWNER-09 measured the local suite; it did not raise
the 50% governance cap. Public status: `SELECTIVE_PUBLIC_EXPORT_OPEN_FOR_REVIEW`.
Local vault branch publication: `LOCAL_VAULT_BRANCH_PUBLICATION_FORBIDDEN`.

Separate completion estimates (stale 2026-08-31 — numbers unchanged; do not
mix with the 45.70 official announced score):

- `CODE_COMPLETION: 63% ± 7%` — no production code changed in OWNER-09.
- `EVIDENCE_COMPLETION: 57% ± 8%` — full-suite receipt exists; Brier remains unreproduced.
- `OPERATIONAL_COMPLETION: 31% ± 9%` — hermetic env held, but tracked state files leaked.

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

- Conservative: **39%** — treat runtime prose and historical receipts as unverified.
- Likely: **45%** — credit enforced boundaries, the provenance gap, and the replay-safe contract.
- Optimistic under current gates: **48%** — no credit for live grounding, governance or restore.

## Critical path to 90%

1. **Completed in Phase-1:** capability-aware cognition deny-list with controlled violation fixture.
   Next, address only newly detected boundary violations; do not split safe provider inference.
2. Recover or rebuild an independent observatory strategy and verifier at the current commit.
3. Complete one immutable, calibrated, uncertainty-bearing, read-only sensor slice with replay.
4. Reproduce a hermetic full baseline without network or live-state writes.
5. Complete owner signing verification while keeping private material outside the repository.
6. Exercise rollback and restore in a non-production environment with independent receipts.
7. Re-score only after every critical gate passes; test volume alone cannot raise the cap.
