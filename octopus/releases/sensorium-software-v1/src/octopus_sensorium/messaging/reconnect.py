from __future__ import annotations

from collections.abc import Awaitable, Callable


async def on_disconnect(hook: Callable[[], Awaitable[None]] | None) -> None:
    if hook is not None:
        await hook()


async def on_reconnect(hook: Callable[[], Awaitable[None]] | None) -> None:
    if hook is not None:
        await hook()
