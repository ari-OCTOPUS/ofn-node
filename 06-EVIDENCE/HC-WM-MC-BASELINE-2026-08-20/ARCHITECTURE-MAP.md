# Architecture map — telemetry is files, not Grafana

```text
Raw files under _ops/state/
  overwrite: *-latest.json, ORGANISM-STATE.json, identities-latest.json
  append:    arbiter-shadow.jsonl, events.jsonl, math-control-observe.jsonl,
             genome ledger.jsonl
        │
        ▼  (this slice: read-only snapshot → lab jsonl)
Telemetry Trust  (_ops/shadow_homeostasis/trust.py)
        │ VALID only into computation; others visible+excluded
        ▼
Homeostatic Core (homeostasis.py)  executable=false
        │
        ├─► World Model (world_model.py)  facts≠hypotheses
        └─► Metacontrol Gate (metacontrol.py)  BLOCK|ADVISORY|SHADOW
                    ▼
             Advisory only. executable=false
```

## Real sources (discovered, not guessed)

| What | Path | Mode | SoT? |
|---|---|---|---|
| arbiter color/period | `_ops/state/pulse/arbiter-latest.json` | overwrite | live now |
| arbiter history | `_ops/state/pulse/arbiter-shadow.jsonl` | append (gaps) | beats may skip |
| life_currency | `_ops/state/pulse/life-currency-latest.json` | overwrite | C-046 |
| organism | `_ops/state/ORGANISM-STATE.json` | overwrite | |
| identity | `_ops/state/identities-latest.json` | overwrite | |
| HRV | in-memory deque `chrono_rhythm/rhythm.py` | **not on disk** | restart WARMUP |
| health digest | `_ops/state/telemetry/health-digest.jsonl` | append | file digest |
| OTLP | `_ops/telemetry/criticality_metrics.py` → 127.0.0.1:4318 | exporter | **not** arbiter/lc source |
| Prometheus scrape of organism | **UNLOCATED** | — | Grafana is visualization only |
| genome ledger | `07 - Knowledge/genome-system/ledger/ledger.jsonl` | append | ≠ CONTRADICTIONS.md |
| Homeostatic Core / WM / MC prior | **0 glob hits** | — | new isolated build |

Forbidden reverse deps: Planner / `policy_gate` / money execution / `model_router`. AST test enforces.

## Existing incomplete cousins (not this package)

- `_ops/telemetry/health_digest.py` — file digest, not typed Observation
- `_ops/evidence_plane/` — different event log
- `octopus-research-sprint` — research only, no implementation
- `_ops/epistemics/test_planner.py` — **must not import**
