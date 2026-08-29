# OCTOPUS Shadow Validation (staging)

Complementary to the live Sensorium persistence world-model. Does **not** replace
`/opt/octopus/cognition` or `octopus-world-model.service`.

- Live predictor remains `persistence-v1` as user `octopus`.
- This package is for contracts, synthetic chaos (telemetry only), and fail-closed guards.
- Optional `ChaosGenerator` only POSTs JSON to loopback `:8080/v1/observe/synthetic`. Do not run it on this board.
- Optional `http_app.py` is unwired; FastAPI is not installed here and must not be systemd-enabled.
- Do not enable a second world-model unit. Do not bind `:9464`. Do not scrape LAN `:9101`.
- Metrics: SSH tunnel to `127.0.0.1:9101`.
- User `octopus-sense` does not exist on this board; live units use `octopus`.
- Torch / 768MiB neural runtime is **not** deployed on WAVE0.

```bash
cd /opt/octopus/shadow_validation
/opt/octopus/venv/bin/pytest -q tests/test_system.py
```
