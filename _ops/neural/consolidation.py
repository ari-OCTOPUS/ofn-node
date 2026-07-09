#!/usr/bin/env python3
"""consolidation.py — NI-4: ConsolidationCycle (خوابِ عمیق / یادگیری).

+ Verification Gate (AlphaEvolve): فقط از نتایجِ verifyشده یاد می‌گیرد.
هر N beat همهٔ منابعِ یادگیری را synthesize می‌کند.
"""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent / "consolidation.json"


@dataclass
class VerifiedSource:
    """یک منبعِ یادگیری با verification status."""
    name: str
    data: dict
    verified: bool       # AlphaEvolve: فقط verified → یادگیری


@dataclass
class ConsolidatedInsight:
    """خروجیِ یک دورِ consolidation."""
    cycle: int
    insights: list[str]
    verified_sources: list[str]
    discarded_sources: list[str]
    timestamp: float = field(default_factory=time.time)
    # Phase 2: latent representation (backward compatible — None when no latent space)
    latent_vector: list[float] | None = None
    similar_keys: list[str] | None = None


def _verify_source(name: str, data: dict) -> bool:
    """Verification Gate (AlphaEvolve). آیا داده قابلِ اعتماد است؟
    - acquisition: فقط اگر upvotes/comments عددی واقعی باشند
    - doctor archive: فقط اگر outcome = approved/rejected
    - school: فقط اگر awareness data عددی باشد
    - calibration: فقط اگر verdict ثبت‌شده باشد"""
    if name == "acquisition" and isinstance(data, dict):
        return any(isinstance(v, (int, float)) and v > 0
                   for v in data.values() if isinstance(v, (int, float)))
    if name == "doctor_archive" and isinstance(data, list):
        return all(d.get("outcome") in ("approved", "rejected", "published")
                   for d in data if isinstance(d, dict))
    if name == "school_awareness" and isinstance(data, dict):
        return isinstance(data.get("mean_awareness"), (int, float))
    if name == "calibration" and isinstance(data, list):
        return all(isinstance(d, dict) and "verdict" in d for d in data)
    return False


class ConsolidationCycle:
    """خوابِ عمیق. synthesize همهٔ منابع. فقط verified."""

    def __init__(self, data_path: str | Path | None = None):
        self._path = Path(data_path) if data_path else _DATA_PATH
        self._history: list[dict] = self._load()
        self._cycle_count = len(self._history)

    def _load(self) -> list[dict]:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self) -> None:
        try:
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._history, ensure_ascii=False, indent=2),
                           encoding="utf-8")
            tmp.replace(self._path)
        except OSError:
            pass

    def run(self, sources: dict[str, dict]) -> ConsolidatedInsight:
        """یک دورِ consolidation. sources = {name: data}.
        فقط verified → ConsolidatedInsight. unverified → discard."""
        self._cycle_count += 1
        insights = []
        verified_names = []
        discarded_names = []

        for name, data in sources.items():
            if _verify_source(name, data):
                verified_names.append(name)
                if name == "acquisition":
                    best = max(data.items(), key=lambda x: x[1]) if data else None
                    if best:
                        insights.append(f"بهترین محتوا: {best[0]} (score={best[1]:.2f})")
                elif name == "doctor_archive":
                    approved = [d for d in data if isinstance(d, dict)
                                and d.get("outcome") in ("approved", "published")]
                    insights.append(f"فیکس‌های تأییدشده: {len(approved)}")
                elif name == "school_awareness":
                    ma = data.get("mean_awareness", 0)
                    insights.append(f"آگاهیِ میانگین: {ma:.2f}")
                elif name == "calibration":
                    insights.append(f"verdictها: {len(data)} رکورد")
            else:
                discarded_names.append(name)

        result = ConsolidatedInsight(
            cycle=self._cycle_count, insights=insights,
            verified_sources=verified_names, discarded_sources=discarded_names)
        self._history.append(asdict(result))
        self._save()
        return result

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    @property
    def history(self) -> list[dict]:
        return list(self._history)
