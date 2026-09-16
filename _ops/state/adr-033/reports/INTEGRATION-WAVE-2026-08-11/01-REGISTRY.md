# Stage B — Registry Truth

- Verdict: **PASS**
- Validator: `_ops/scripts/validate_signals_registry.py`
- Report: `registry-validate.json`
- Registry digest: `sha256:fcc153f20f03bbe4b8f93060ea03667326efcd8e9c4234634cf8864afaaf3ee0`
- Git SHA recorded by validator: `f7c1a5f2a2de0de9df2a1ecbf249c25dbc848b60`

## Validator result

```text
ok=true
errors=0
warnings=0
signals=9
```

## Neural containment record

| Field | Value |
|---|---|
| truth_status | `TESTED` |
| evidence_level | `SHADOW` |
| allowed_effect | `trace_only` |
| may_gate | `false` |
| production_apply_enabled | `false` |

## Capability separation

- `request_protective_halt` does **not** appear as an entry in `architecture/signals-registry.yaml`.
- It is present in `architecture/capabilities-registry.yaml` with entrypoint `_ops/wiring.py::request_protective_halt`.
- Registry semantics match ADR-034 and the explanatory-only Metaphor Decode note.
- No additive repair was needed.
