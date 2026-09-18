# S1 integrated architecture candidate — 2026-09-17

GOV_VERSION=V8 · LADDER=L2. Owner: root, integration handoff from T5/T10 agents.
Status: LOCAL_CANDIDATE_E3_NOT_DEPLOYED. Source base: node138 Git HEAD
`fe0c55e0a952e0048ff6bd3ddb8ab9419cd1dc0d`, fetched read-only over authenticated SSH.
Local checkpoint `2b123d44394e02c683cad35ae2fc93ca065888d8` adds no source changes.

## Changes and actual consumer

- Existing self_model_producer accepts optional `--fleet-census`. Its read-only adapter
  validates the exact seven-node roster, timestamps, identity shapes, finite JSON,
  subprocess success evidence and size. It keeps job health UNKNOWN, signatures
  unverified and authority unchanged. Absent input preserves old producer behavior.
- One actual local producer invocation at 09:07:53Z consumed freshly authenticated
  observations of all seven nodes; fleet coverage was OBSERVED=7. Overall organism
  status stayed unverifiable. Output is local evidence, not node138 deployment.
- RevenueRun reuses existing receipt hashing and adds a strict ordered replay consumer.
  It never marks cash verified or authorizes dispatch. Real business producers remain
  unwired. Studio administrative pack remains in the contributing lane.
- USD API ceilings have one candidate source (100/month, 10/rolling24h, 2/task),
  composed with stricter runtime limits. CallBudget and fake_executor consume it.
  Existing node/Router callers still need durable cross-call monetary reservation;
  no globally enforced live dollar-budget claim follows.

## Verification and corrections

- integration-tests.xml: 146 passed, 56 subtests passed.
- executor-purity-tests.xml: 23 passed, 6311 subtests passed.
- Total main tests in these disjoint selections: 169. No full-repository claim.
- Independent fleet review found truthy malformed identities and NaN declared_role
  could pass. Both are fixed, with negative tests in the final selection.
- First local edit mistakenly added the optional parameter to a similarly named
  helper; first run failed 21 tests. Parameter placement was corrected and the same
  relevant selection passed. A later combined command named a nonexistent test file,
  ran zero tests, then was corrected; final XML receipts are the successful runs.
- git diff --check succeeded. No live source, flag, service or authority change.
- Budget patch checked clean; fake_executor/callbudget Git blobs are identical on the
  contributor's earlier baseline and the actual node138 base.

## Remaining and rollback

Deployment, authenticated signed heartbeat ingestion, recurring node138 consumption,
shared monetary reservation, business producer wiring and external settlement are
NOT_RUN/UNVERIFIED. A local input file hash is not a signature. The producer's
seven-node coverage is not seven proven useful jobs.

Only this isolated branch contains changes. Revert its candidate source commit for
rollback; preserve receipts. Do not reset or overwrite the dirty F:/ofn-node checkout.
Runtime-observation and XML files are retained in this lane; source hashes are in
SOURCE-RECEIPT.json. Parent authority/evidence index is S1-MATURITY-20260917 in vault.
