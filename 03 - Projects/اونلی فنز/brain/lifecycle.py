#!/usr/bin/env python3
"""lifecycle.py — #5: Subscriber Lifecycle + Churn Predictor. aggregate فقط، صفر PII."""
from __future__ import annotations
import json, math, os, time
from dataclasses import dataclass, field, asdict
from pathlib import Path

# state قابل‌انحراف با PF_BRAIN_DIR (تست/harness)؛ بدونِ env = کنارِ ماژول (production)
_DATA_PATH = Path(os.environ.get("PF_BRAIN_DIR")
                  or Path(__file__).resolve().parent) / "lifecycle.json"
STAGES = ("new", "active", "engaged", "at_risk", "churned", "win_back")


@dataclass
class PeriodRecord:
    period: str  # e.g. "2026-W28"
    total: int
    new_count: int
    churned_count: int
    ppv_buyers: int
    timestamp: float = field(default_factory=time.time)


class SubscriberLifecycle:
    """چرخهٔ حیاتِ aggregate. churn prediction. win-back. صفر PII."""

    def __init__(self, data_path=None):
        self._path = Path(data_path) if data_path else _DATA_PATH
        self._periods: list[dict] = self._load()

    def _load(self):
        try: return json.loads(self._path.read_text(encoding="utf-8"))
        except: return []

    def _save(self):
        try:
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._periods, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self._path)
        except OSError: pass

    def track(self, period: str, total: int, new_count: int = 0,
              churned_count: int = 0, ppv_buyers: int = 0):
        rec = PeriodRecord(period=period, total=total, new_count=new_count,
                           churned_count=churned_count, ppv_buyers=ppv_buyers)
        self._periods.append(asdict(rec))
        self._save()

    def churn_rate(self) -> float:
        """churn rate از آخرین دوره‌ها."""
        if len(self._periods) < 2: return 0.0
        recent = self._periods[-4:]
        total_churned = sum(p.get("churned_count",0) for p in recent)
        total_subs = sum(p.get("total",1) for p in recent)
        return min(1.0, total_churned / max(total_subs, 1))

    def growth_rate(self) -> float:
        if len(self._periods) < 2: return 0.0
        last = self._periods[-1].get("total",1)
        prev = self._periods[-2].get("total",1)
        return (last - prev) / max(prev, 1)

    def predict_at_risk(self) -> dict:
        """تخمینِ at_risk از trend."""
        if len(self._periods) < 2:
            return {"at_risk_pct": 0.0, "status": "no_data"}
        churn = self.churn_rate()
        growth = self.growth_rate()
        # اگر churn بالا و growth پایین → at_risk زیاد
        at_risk = max(0, min(1.0, churn * 1.5 - growth))
        trend = "declining" if growth < 0 else ("stagnant" if growth < 0.05 else "growing")
        return {"at_risk_pct": round(at_risk, 3), "churn_rate": round(churn,3),
                "growth_rate": round(growth,3), "trend": trend}

    def win_back_strategy(self) -> list[str]:
        """پیشنهاد برای win-back."""
        pred = self.predict_at_risk()
        strategies = []
        if pred.get("churn_rate",0) > 0.3:
            strategies.append("increase wall content frequency (churn above target)")
        if pred.get("growth_rate",0) < 0:
            strategies.append("emergency: 50% discount PPV + DM campaign")
        strategies.append("standard: win-back DM for lapsed >14 days")
        strategies.append("segment: VIP personalized message")
        return strategies

    @property
    def period_count(self): return len(self._periods)

    @property
    def history(self): return list(self._periods)
