"""Command nonce cache. Duplicate nonce is a replay."""

from __future__ import annotations

from collections import OrderedDict


class NonceCache:
    def __init__(self, limit: int = 4096) -> None:
        self.limit = limit
        self._seen: OrderedDict[str, None] = OrderedDict()

    def accept(self, nonce: str) -> bool:
        if not nonce or nonce in self._seen:
            return False
        self._seen[nonce] = None
        if len(self._seen) > self.limit:
            self._seen.popitem(last=False)
        return True
