"""Graceful shutdown helpers. No reboot, no power-cycle."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable


async def stop_plugins(stoppers: list[Callable[[], Awaitable[None]]]) -> None:
    for stop in stoppers:
        try:
            await stop()
        except Exception:
            continue


async def drain_nats(nc, timeout: float = 2.0) -> None:  # noqa: ANN001
    if nc is None:
        return
    try:
        await asyncio.wait_for(nc.drain(), timeout=timeout)
    except Exception:
        try:
            await nc.close()
        except Exception:
            return
