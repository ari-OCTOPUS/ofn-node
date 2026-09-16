#!/usr/bin/env python3
"""hebbian.py — NI-6: HebbianAssociator (fire-together wire-together).

co-occurrence → association. strength رشد با تکرار، decay با غیاب.
persist (JSON). فقط aggregate.
"""
from __future__ import annotations
import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from collections import defaultdict


def _default_data_path() -> Path:
    """env-اول (OPS_DIR) تا تستِ harness-ایزوله state واقعی/repo را آلوده نکند
    (همان درسِ bcm 2026-07-10)؛ بدونِ env = کنارِ ماژول (production)."""
    ops = os.environ.get("OPS_DIR")
    base = Path(ops) / "neural" if ops else Path(__file__).resolve().parent
    return base / "hebbian.json"


_DATA_PATH = _default_data_path()

DECAY_RATE = 0.95     # per tick without co-occurrence
LEARN_RATE = 0.1      # per co-occurrence
MAX_STRENGTH = 1.0
PRUNE_THRESHOLD = 0.01


@dataclass
class Association:
    signals: tuple    # (sig_a, sig_b)
    strength: float = 0.0
    co_occurrences: int = 0
    last_seen: float = field(default_factory=time.time)


class HebbianAssociator:
    """نورون‌هایی که با هم فعالند، وصل می‌شوند."""

    def __init__(self, data_path: str | Path | None = None):
        self._path = Path(data_path) if data_path else _DATA_PATH
        self._assocs: dict[tuple, Association] = self._load()

    def _load(self) -> dict:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            out = {}
            for r in raw:
                key = tuple(r["signals"])
                out[key] = Association(signals=key, strength=r["strength"],
                                       co_occurrences=r["co_occurrences"],
                                       last_seen=r.get("last_seen", time.time()))
            return out
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self) -> None:
        try:
            data = [{"signals": list(a.signals), "strength": a.strength,
                     "co_occurrences": a.co_occurrences, "last_seen": a.last_seen}
                    for a in self._assocs.values()]
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self._path)
        except OSError:
            pass

    def observe(self, signals: list[str]) -> None:
        """ثبتِ هم‌وقوعی. همهٔ جفت‌ها."""
        unique = sorted(set(signals))
        for i in range(len(unique)):
            for j in range(i + 1, len(unique)):
                key = (unique[i], unique[j])
                if key not in self._assocs:
                    self._assocs[key] = Association(signals=key)
                a = self._assocs[key]
                a.strength = min(MAX_STRENGTH, a.strength + LEARN_RATE)
                a.co_occurrences += 1
                a.last_seen = time.time()
        self._save()

    def decay(self) -> None:
        """یک tick از عدمِ تکرار → strength کم می‌شود.

        ۲۰۲۶-۰۷-۳۰ — «چرخهٔ خالی زوال ندارد». نسخهٔ قبلی روی جدولِ **تهی** هم
        `_save()` می‌زد، پس `hebbian.json` روی درختِ زنده هر تیک بازنویسی می‌شد
        در حالی که محتوایش `[]` بود (mtime~۰ ثانیه = ظاهرِ «زنده و فعال»، صفر
        اطلاعات). آینهٔ همان قراردادِ `neural/bcm.py::step` (FIX #214): وقتی
        چیزی برای زوال‌دادن نیست، دست به دیسک نزن.
        هیچ محاسبه‌ای عوض نمی‌شود — روی جدولِ غیرخالی رفتار بایت‌به‌بایت همان
        است؛ فقط I/Oِ بی‌محتوا حذف می‌شود.
        """
        if not self._assocs:
            return
        to_prune = []
        for key, a in self._assocs.items():
            a.strength *= DECAY_RATE
            if a.strength < PRUNE_THRESHOLD:
                to_prune.append(key)
        for key in to_prune:
            del self._assocs[key]
        self._save()

    @property
    def associations(self) -> list[Association]:
        return sorted(self._assocs.values(), key=lambda a: a.strength, reverse=True)

    def strong_associations(self, threshold: float = 0.3) -> list[Association]:
        return [a for a in self.associations if a.strength >= threshold]

    def strength_of(self, sig_a: str, sig_b: str) -> float:
        key = tuple(sorted((sig_a, sig_b)))
        return self._assocs.get(key, Association(signals=key)).strength
