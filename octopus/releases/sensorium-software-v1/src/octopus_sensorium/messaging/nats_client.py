"""Runtime NATS client. Stream create/delete stays provisioning-only."""

from __future__ import annotations

from octopus_sensorium.natsbus import connect, list_streams, load_nats_url, publish_json

# Intentionally not re-exported: ensure_streams() is bootstrap-only.

__all__ = ["connect", "list_streams", "load_nats_url", "publish_json"]
