#!/usr/bin/env python3
"""signal_hub.py — NI-1: SignalHub (نخاع / spinal cord) + observability.

هر beat همهٔ سنسورها را در یک snapshot واحد جمع می‌کند. advisory_only=True.
هیچ import از *_gate/chrono/money. $0 آفلاین.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field, asdict


@dataclass
class NeuralSnapshot:
    """snapshot واحدِ همهٔ سیگنال‌ها در یک لحظه."""
    beat: int = 0
    rhythm: dict = field(default_factory=dict)
    sensory: dict = field(default_factory=dict)
    spectral: dict = field(default_factory=dict)
    budget: dict = field(default_factory=dict)
    doctor: dict = field(default_factory=dict)
    acquisition: dict = field(default_factory=dict)
    school: dict = field(default_factory=dict)
    pain_level: float = 0.0
    timestamp: float = field(default_factory=time.time)
    advisory_only: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


class SignalHub:
    """جمعِ همهٔ سیگنال‌ها. هر منبع قابل‌تزریق. خروجی: NeuralSnapshot."""

    def __init__(self):
        self._snapshots: list[NeuralSnapshot] = []

    def collect(self, beat: int = 0,
                rhythm: dict | None = None,
                sensory: dict | None = None,
                spectral: dict | None = None,
                budget: dict | None = None,
                doctor: dict | None = None,
                acquisition: dict | None = None,
                school: dict | None = None,
                pain_level: float = 0.0) -> NeuralSnapshot:
        snap = NeuralSnapshot(
            beat=beat,
            rhythm=rhythm or {},
            sensory=sensory or {},
            spectral=spectral or {},
            budget=budget or {},
            doctor=doctor or {},
            acquisition=acquisition or {},
            school=school or {},
            pain_level=pain_level)
        self._snapshots.append(snap)
        return snap

    @property
    def latest(self) -> NeuralSnapshot | None:
        return self._snapshots[-1] if self._snapshots else None

    @property
    def history(self) -> list[NeuralSnapshot]:
        return list(self._snapshots)

    def latest_dict(self) -> dict:
        return self.latest.to_dict() if self.latest else {}
