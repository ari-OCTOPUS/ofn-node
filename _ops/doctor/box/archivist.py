#!/usr/bin/env python3
"""archivist.py — Part 11: multiscale coarse-grain memory (MERA-like).

|leaf| → mid → G_t. |M_t| زیرخطی (boundary "area"). evict کم‌امتیازترین.
هیچ import از production."""
from __future__ import annotations
import math
from dataclasses import dataclass, field


@dataclass
class MemoryEntry:
    """یک ورودیِ حافظه: topic، summary، score، scale (leaf/mid/root)."""
    topic: str
    summary_vec: list[float]
    score: float = 0.5
    scale: str = "leaf"      # leaf | mid | root
    ts: int = 0


@dataclass
class Archivist:
    """build/maintain M_t. multiscale coarse-grain. bounded evict."""
    cap: int = 50                    # |M_t|_max (boundary area)
    entries: list[MemoryEntry] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.entries)

    def is_within_boundary(self) -> bool:
        """|M_t| زیرِ سقفِ مرزی می‌ماند."""
        return self.size <= self.cap

    def append(self, entry: MemoryEntry) -> None:
        """append + evict اگر از cap بشود."""
        self.entries.append(entry)
        self._evict()

    def append_many(self, entries: list[MemoryEntry]) -> None:
        for e in entries:
            self.entries.append(e)
        self._evict()

    def _evict(self) -> None:
        """evict کم‌امتیازترین/قدیمی‌ترین تا زیرِ cap."""
        if len(self.entries) <= self.cap:
            return
        # sort: score desc، ts desc → حفظِ برترها
        self.entries.sort(key=lambda e: (e.score, e.ts), reverse=True)
        self.entries = self.entries[:self.cap]

    def coarse_grain(self) -> list[MemoryEntry]:
        """MERA-like: leaf → mid → root. چندمقیاسی.
        خروجی: یک خلاصهٔ root از همهٔ entries."""
        if not self.entries:
            return []
        n = len(self.entries)
        # میانگینِ summary_vec به‌عنوان coarse-grain
        dim = max(len(e.summary_vec) for e in self.entries)
        mean_vec = []
        for d in range(dim):
            vals = [e.summary_vec[d] for e in self.entries
                    if d < len(e.summary_vec)]
            mean_vec.append(sum(vals) / max(len(vals), 1))
        mean_score = sum(e.score for e in self.entries) / n
        root = MemoryEntry(topic="_coarse_root", summary_vec=mean_vec,
                           score=mean_score, scale="root", ts=0)
        return [root]

    def summary_vec(self) -> list[float]:
        """خلاصهٔ فعلی برای feed به agents."""
        cg = self.coarse_grain()
        return cg[0].summary_vec if cg else [0.0]


def memory_is_sublinear(n_inputs: int, cap: int) -> bool:
    """|M_t| زیرخطی حتی با ورودیِ زیاد: |M_t| ≤ cap (ثابت)، نه O(n_inputs)."""
    return cap <= max(1, int(math.sqrt(max(n_inputs, 1))) * 10)
