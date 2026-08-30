"""
mental_model.py — مدلِ ذهنیِ پویا از مالک (in-memory + قابلِ snapshot).

خالص است (به db وابسته نیست)؛ HumanCore مسئولِ ذخیره/بازیابیِ snapshot است.
"""

from __future__ import annotations

import json


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


_DEFAULT = {
    "stress_level": 0.5,        # 0..1
    "sleep_trend": "unknown",   # good | declining | low | unknown
    "engagement": 0.5,          # 0..1
    "preferred_tone": "direct", # direct | warm | minimal | probing
    "last_active_domain": None,
}


class MentalModel:
    def __init__(self, traits: dict | None = None):
        self.traits = dict(_DEFAULT)
        if traits:
            self.traits.update(traits)

    # --- به‌روزرسانی‌ها ---
    def update_from_log(self, row: dict) -> None:
        sleep = row.get("sleep")
        if sleep is not None:
            if sleep <= 2:
                self.traits["sleep_trend"] = "low"
                self.traits["stress_level"] = _clamp(self.traits["stress_level"] + 0.1)
            elif sleep >= 4:
                self.traits["sleep_trend"] = "good"
                self.traits["stress_level"] = _clamp(self.traits["stress_level"] - 0.05)
        self.traits["last_active_domain"] = "body_hrv"

    def update_from_insight(self, insight: dict | None, verdict: str | None) -> None:
        self.traits["engagement"] = _clamp(self.traits["engagement"] + 0.05)

    def update_from_interaction(self, itype: str, response_time: float | None = None) -> None:
        if response_time is None:
            return
        if response_time < 120:
            self.traits["engagement"] = _clamp(self.traits["engagement"] + 0.05)
        elif response_time > 1800:
            self.traits["engagement"] = _clamp(self.traits["engagement"] - 0.05)

    # --- نما/ذخیره ---
    def get_profile(self) -> dict:
        return dict(self.traits)

    def to_json(self) -> str:
        return json.dumps(self.traits, ensure_ascii=False)

    @classmethod
    def from_json(cls, s: str | None) -> "MentalModel":
        if not s:
            return cls()
        try:
            return cls(json.loads(s))
        except (ValueError, TypeError):
            return cls()
