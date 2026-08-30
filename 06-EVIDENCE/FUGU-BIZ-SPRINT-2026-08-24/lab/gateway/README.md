# Lab BrainPort gateway (shared infra)

**Policy:** Lab is shared infra only (not a main project). Same-day consume by ≥2 businesses (Ziman + Studio). Prefer **fugu**. ARMED=false.

## What marketing / Ziman / Studio import

```python
from brainport import get_provider, GenerateRequest
p = get_provider("copy")
print(p.generate(GenerateRequest(prompt="...")).text)
```

Do **not** import `FuguProvider`, `DeepSeekProvider`, or any vendor model id from business packages.

## Contract (`ModelProvider`)

- `generate` / `stream` / `tool_call`
- `health` / `estimate_cost` / `model_capabilities`

## Providers

| Provider | Status |
|----------|--------|
| FuguProvider | preferred; local stub without `FUGU_ENDPOINT` |
| DeepSeekProvider | stub only (`health.ok=False`) |

## Paths

- Package: `lab/gateway/brainport/`
- Example: `lab/gateway/examples/ziman_copy.py`
- Env (ops only): `BRAINPORT_PROVIDER`, `FUGU_ENDPOINT`, `FUGU_API_KEY`

## Hold

E6–E7 enrich cascade **HOLD**. No more Lab enrich unless money-loop unblock.
