from __future__ import annotations

from collections import deque
from typing import Any


class OfflineBuffer:
    def __init__(self, maxlen: int = 256) -> None:
        self._q: deque[tuple[str, dict[str, Any]]] = deque(maxlen=maxlen)

    def append(self, subject: str, payload: dict[str, Any]) -> None:
        self._q.append((subject, payload))

    def drain(self) -> list[tuple[str, dict[str, Any]]]:
        pending = list(self._q)
        self._q.clear()
        return pending

    def __len__(self) -> int:
        return len(self._q)
