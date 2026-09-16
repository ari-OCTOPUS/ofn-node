# Telemetry sources

Grafana is not source of truth.

Canonical live observations for this organism are **files** under `_ops/state/` (see ARCHITECTURE-MAP).

Optional exporter: `_ops/telemetry/criticality_metrics.py` OTLP/HTTP to `http://127.0.0.1:4318/v1/metrics` (Alloy). This is not the arbiter or life_currency source.

Prometheus scrape endpoint for organism pulse: **UNLOCATED**.

HRV window: process memory only (`_ops/chrono_rhythm/rhythm.py` deque maxlen=20). After restart: WARMUP in this slice, not false AMBER.
