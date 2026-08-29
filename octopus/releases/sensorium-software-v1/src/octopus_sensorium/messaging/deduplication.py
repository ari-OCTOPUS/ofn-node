from __future__ import annotations


class ContentHashDeduper:
    def __init__(self, limit: int = 4096) -> None:
        self.limit = limit
        self.seen: set[str] = set()

    def accept(self, digest: str) -> bool:
        if digest in self.seen:
            return False
        self.seen.add(digest)
        if len(self.seen) > self.limit:
            self.seen.clear()
            self.seen.add(digest)
        return True
