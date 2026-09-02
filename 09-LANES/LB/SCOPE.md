# LB — Scope Registration

Registered BEFORE any code, per owner directive and AGENTS.md §8 (lane discipline).
Collision check done 2026-09-02: none of the owned paths below appear in any existing
lane's owns_paths in `09-LANES/LANE-MATRIX.csv` (L0–L3 rows reviewed); all owned paths
are NEW files on this branch.

## Owned paths (only here may this lane write)

- `ofn/doctor/**` (new package: contract copy, miniyaml, receipts, contract_map, round, backlog, destiny, cli)
- `tests/test_doctor_lane_*.py` (new tests, prefixed to avoid collisions)
- `09-LANES/LB/**` (DoD, SCOPE, LANE-REPORT, runs/ artifacts: findings, receipts, payloads)
- `.gitignore` — NOT owned; no need (all artifacts intentional)

## Forbidden paths (stop condition if touched)

- Lane A surface: anything matching `ofn/agents/cockpit*`, `ofn/agents/brain_probe*`,
  `ofn/agents/self_awareness*`, `docs/self-awareness/**` — untouched.
- `.github/workflows/**`, CODEOWNERS, branch protection, `.git/config` — untouched.
- `ofn/config.py`, `ofn/node.py`, `pytest.ini`, `09-LANES/LANE-MATRIX.csv` (shared — see payload).
- `F:\backup/**` — read-only source vault; zero writes (proven by integrity manifests).
- `F:\ofn-node/**` main checkout (occupied by fix/demand-harvest session) — untouched.
- `OCTOPUS-DOCTOR/**` vault code, `_ops/**` — read-only reference, untouched.

## Shared-file policy

`09-LANES/LANE-MATRIX.csv` is shared. This lane does NOT edit it. Append payload prepared
at `09-LANES/LB/runs/lane-matrix-append-payload.csv` (one CSV row, see file).

## External touchpoints (all read-only)

- `F:\backup\LAB-DOCTOR-CONTRACT.yaml` — copied byte-identical into the package
  (`ofn/doctor/contract/LAB-DOCTOR-CONTRACT.yaml`), source sha256 recorded in code.
- `F:\backup` vault — scanned by the read-only round; integrity manifests in receipts.
- `F:\backup\06 - Architecture Maps\نقشه-اختاپوس\VERDICT_QUEUE.md` — append payload
  prepared as artifact; NOT written directly (owner directive collision protocol).
