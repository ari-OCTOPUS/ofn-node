# SPECTRAL-DEF-2026-08-12

## Versioned Spectral Definitions

**Date:** 2026-08-12
**Scope:** `_ops/doctor/spectral_definitions.py` (new single-source module)

### Problem

Spectral heuristics (`sigma`, `connectivity_ratio`) were scattered across
`spectral.py` and `spectral_metrics.py` with no canonical formula ID or version
metadata. Consumers had to guess what formula was in use.

### Decision

Create `spectral_definitions.py` as the single source of truth for all spectral
formula definitions, including versioned identifiers.

### Formulas

#### Legacy Sigma (`legacy_sigma.v1`)

```
sigma = min(lambda_max / (lambda_2 + eps), 10)
```

- `eps = 1e-6` (مقدار تاریخیِ مسیر live؛ تغییر ممنوع بدون version bump)
- `cap = 10.0`
- Returns `None` when inputs are degenerate (non-finite, disconnected, etc.)
- `spectral.py::estimate_sigma` delegates to `compute_legacy_sigma` via an
  internal helper that falls back to `0.0` for empty/degenerate cases,
  preserving the historical public contract (`float`, never `None`).

#### Connectivity Ratio v2 (`connectivity_ratio_v2.v1`)

```
ratio = clamp(lambda_2 / (lambda_max + eps), 0, 1)
```

- `eps = 1e-9`
- Bounded to `[0, 1]` by construction.
- Returns `None` for non-finite, None, lambda_max <= 0, or λ₂≈0 inputs.
- disconnected/tiny graphs are `UNKNOWN`, not a fabricated healthy/critical zero.
- Higher values indicate more uniform connectivity; lower values indicate
  bottleneck-prone topology.

### Data Model Changes

| Component | Field | Type | Default |
|---|---|---|---|
| `SpectralMetrics` | `connectivity_ratio_v2` | `float \| None` | `None` |
| `CriticalitySnapshot` | `connectivity_ratio_v2` | `float \| None` | `None` |
| OTLP metric | `octopus.spectral.connectivity_ratio_v2` | gauge | new |

No existing fields were renamed. Legacy `sigma_heuristic` and its OTLP gauge
(`octopus.spectral.heuristic_sigma`) remain untouched.

### Constraints Preserved

1. **Legacy sigma formula unchanged:** `min(lambda_max/(lambda_2+eps), 10)`.
   Not flipped. All consumers see identical output.
2. **`spectral.py::estimate_sigma`** retains identical public signature
   `(eigvals: list) -> float` and output range `[0, 10]`.
3. **None instead of fake 0.0:** New functions and fields return `None` when
   inputs are empty, tiny, non-finite, or disconnected.
4. **Separate OTLP metric:** `octopus.spectral.connectivity_ratio_v2` is a
   new gauge. Legacy metrics are not renamed.
5. **Shadow-only v2:** `connectivity_ratio_v2` حقِ gate/actuator ندارد؛ ارتقا فقط با
   AUC/baseline مستقل و رأی مالک.
6. **No new dependencies:** `spectral_definitions.py` uses only `math.isfinite`
   from the standard library.

### Files Changed

- `_ops/doctor/spectral_definitions.py` -- **new**
- `_ops/doctor/spectral.py` -- `estimate_sigma` delegates to `compute_legacy_sigma`
- `_ops/doctor/spectral_metrics.py` -- added `connectivity_ratio_v2` field and computation
- `_ops/doctor/criticality_v2.py` -- added `connectivity_ratio_v2` field and export
- `_ops/telemetry/criticality_metrics.py` -- added new OTLP gauge
- `_ops/tests/test_spectral_definitions.py` -- **new**, focused tests
- `architecture/SPECTRAL-DEF-2026-08-12.md` -- this file
