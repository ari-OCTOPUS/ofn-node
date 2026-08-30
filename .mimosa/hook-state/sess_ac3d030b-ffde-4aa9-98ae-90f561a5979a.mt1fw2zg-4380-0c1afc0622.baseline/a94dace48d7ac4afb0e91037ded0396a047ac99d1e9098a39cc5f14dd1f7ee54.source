#!/usr/bin/env python3
"""circadian.py — NI-3: CircadianMap (ساعتِ زیستی).

time-of-day awareness. peak/maintenance hours. readiness ∝ time-of-day.
قابل‌تنظیم از config.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class CircadianMap:
    """ساعتِ زیستی. می‌داند چه ساعت‌ای peak/maintenance است."""
    # AEST hours (Sydney)
    peak_hours: dict = None     # {platform: [(start, end), ...]}
    maintenance_hours: tuple = (2, 6)   # 02:00-06:00
    rest_hours: tuple = None    # none = 24/7

    def __post_init__(self):
        if self.peak_hours is None:
            self.peak_hours = {
                "reddit": [(9, 12)],     # US prime evening = Syd morning
                "x": [(18, 20)],         # AU evening
                "of": [(20, 22)],
            }
        if self.rest_hours is None:
            self.rest_hours = ()   # 24/7

    def phase(self, hour: int) -> str:
        """phase برای یک ساعتِ given. peak/maintenance/active."""
        for platform, hours in self.peak_hours.items():
            for (s, e) in hours:
                if s <= hour < e:
                    return "peak"
        m_s, m_e = self.maintenance_hours
        if m_s <= hour < m_e:
            return "maintenance"
        return "active"

    def readiness(self, hour: int) -> float:
        """readiness ∝ time-of-day. peak=1.0, maintenance=0.3, active=0.7."""
        p = self.phase(hour)
        return {"peak": 1.0, "active": 0.7, "maintenance": 0.3}.get(p, 0.5)

    def best_platform(self, hour: int) -> str:
        """بهترین پلتفرم برای این ساعت."""
        for platform, hours in self.peak_hours.items():
            for (s, e) in hours:
                if s <= hour < e:
                    return platform
        return "reddit"   # default

    def is_maintenance(self, hour: int) -> bool:
        return self.phase(hour) == "maintenance"
