"""One-shot JetStream provisioning. The Sensorium agent must never import-call this at runtime."""

from __future__ import annotations

import asyncio

import nats

from octopus_sensorium.natsbus import STREAMS


async def ensure_streams(nc: nats.NATS) -> list[str]:
    js = nc.jetstream()
    created: list[str] = []
    for cfg in STREAMS:
        try:
            await js.add_stream(cfg)
            created.append(cfg.name)
        except Exception:
            await js.update_stream(cfg)
            created.append(cfg.name)
    return created
