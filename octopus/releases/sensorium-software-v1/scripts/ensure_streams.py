#!/usr/bin/env python3
"""One-shot JetStream provisioner. Not a daemon. Requires sensorium-provisioner."""

from __future__ import annotations

import asyncio
import os

import nats

from octopus_sensorium.natsbus import STREAMS


async def main() -> None:
    url = os.environ.get("NATS_URL", "nats://192.168.0.182:4222")
    user = os.environ["NATS_USER"]
    password = os.environ["NATS_PASSWORD"]
    if user != "sensorium-provisioner":
        raise SystemExit("refusing to provision with a non-provisioner identity")
    nc = await nats.connect(url, user=user, password=password, name="sensorium-provisioner")
    js = nc.jetstream()
    for cfg in STREAMS:
        try:
            await js.add_stream(cfg)
            print("created", cfg.name, "max_bytes", cfg.max_bytes)
        except Exception:
            await js.update_stream(cfg)
            print("updated", cfg.name, "max_bytes", cfg.max_bytes)
        info = await js.stream_info(cfg.name)
        if not info.config.max_bytes:
            raise SystemExit(f"{cfg.name} missing max_bytes")
    await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())
