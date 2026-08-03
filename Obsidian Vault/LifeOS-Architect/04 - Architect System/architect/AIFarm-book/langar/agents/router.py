"""router.py — انتخابِ ایجنت و حوزه (با وزن‌دهیِ قابلِ‌تنظیم از SelfImprover)."""

from __future__ import annotations

import datetime as _dt

ALL_DOMAINS = [
    "body_hrv", "mind_emotion", "relationships",
    "work_engineering", "meaning_direction", "habits_environment",
]


class AgentRouter:
    def __init__(self, agents, weights: dict | None = None):
        self.agents = agents
        self.domain_to_agent = {}
        for a in agents:
            for d in a.domains:
                self.domain_to_agent[d] = a
        # weights: domain -> float (پیش‌فرض ۱.۰)
        self.weights = dict(weights or {})

    def weight(self, domain: str) -> float:
        return float(self.weights.get(domain, 1.0))

    def pick_domain(self, domain_counts: dict | None = None) -> str:
        """کم‌پوشش‌ترین حوزه (با وزن)، با چرخشِ روزانه برای تنوع."""
        counts = domain_counts or {}
        domains = [d for d in ALL_DOMAINS if d in self.domain_to_agent]
        # امتیاز بالاتر = اولویتِ بیشتر: وزن تقسیم بر (۱ + پوشش)
        scored = [(self.weight(d) / (1 + counts.get(d, 0)), d) for d in domains]
        best = max(s for s, _ in scored)
        top = [d for s, d in scored if abs(s - best) < 1e-9]
        idx = _dt.date.today().toordinal() % len(top)
        return top[idx]

    def route(self, domain: str):
        return self.domain_to_agent.get(domain) or self.agents[0]

    def choose(self, domain_counts: dict | None = None):
        d = self.pick_domain(domain_counts)
        return self.route(d), d
