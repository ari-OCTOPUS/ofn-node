#!/usr/bin/env python3
"""school_bridge.py — پلِ afferent → School (یادگیری از «کلاس درسِ» اختاپوس).

حلقهٔ بازِ کشف‌شده را می‌بندد: sensory_bus مشاهده‌ها را به topic_id (لیبلِ School) نگاشت می‌کرد
ولی هیچ‌چیز آن‌ها را به گرافِ curriculum تزریق نمی‌کرد — پس «کلاس درس» هرگز واقعاً یاد نمی‌گرفت.
این پل: AfferentEventها → AwarenessField.observe → tick (ȧ=−L·a+input) → insightهای propose-only.
+ persistِ awareness (حافظه: یادگیری بین‌اجراها می‌ماند = «بهتر یادش می‌ماند»).

ایزوله: import فقط `curriculum` + `sensory_bus` (read-only، بدونِ تغییر). هیچ import از
*_gate/chrono/money/organism/wiring. $0 آفلاین، stdlib-only. insightها هرگز effector نیستند
(co-activation → پیشنهادِ یال، human-gated).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent            # _ops/afferent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[1] / "07 - Knowledge" / "school-memory"))
from curriculum import seed_curriculum, AwarenessField, detect_insights  # noqa: E402

AWARENESS_STATE = _HERE.parent / "state" / "school-awareness.json"       # _ops/state
OBSERVE_CAP = 0.5   # کرانِ شدتِ یک مشاهده روی awareness (ضدِ اشباعِ ناگهانی)


class SchoolBridge:
    """پلِ یادگیری. seed_curriculum → AwarenessField؛ awareness را از دیسک بازمی‌گرداند (حافظه)."""

    def __init__(self, graph=None, state_path=None):
        self.graph = graph or seed_curriculum()
        self.field = AwarenessField(self.graph)
        self.state_path = Path(state_path) if state_path else AWARENESS_STATE
        self._prev_gap = None
        self._load()                                   # remember: awarenessِ قبلی

    def _load(self) -> None:
        try:
            saved = (json.loads(self.state_path.read_text("utf-8")) or {}).get("awareness", {})
        except (OSError, ValueError):
            return
        for tid, v in saved.items():
            i = self.field.idx.get(tid)
            if i is not None:
                try:
                    self.field.a[i] = max(0.0, min(1.0, float(v)))
                except (TypeError, ValueError):
                    continue

    def _save(self) -> None:
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            aw = {tid: round(self.field.a[i], 4)
                  for tid, i in self.field.idx.items() if self.field.a[i] > 0.0}
            tmp = self.state_path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"awareness": aw,
                                       "mean": round(self.field.mean_awareness(), 4)},
                                      ensure_ascii=False, indent=2), "utf-8")
            tmp.replace(self.state_path)
        except OSError:
            pass                                       # fail-soft

    def learn_from(self, events, persist: bool = True) -> dict:
        """AfferentEventها → observe به field → tick → insightهای propose-only.
        فقط afferent=True یاد گرفته می‌شود (رویدادِ PII-رد/درونی نادیده). خروجی = گزارش."""
        mean_before = round(self.field.mean_awareness(), 4)
        taught = 0
        for ev in events:
            if not getattr(ev, "afferent", False):     # PII-رد یا internal → یاد نمی‌گیرد
                continue
            for tid in (getattr(ev, "topic_ids", None) or []):
                self.field.observe(tid, intensity=min(OBSERVE_CAP, float(getattr(ev, "intensity", 0.3))))
                taught += 1
        self.field.tick()
        insights = detect_insights(self.field, self.graph, self._prev_gap)
        try:
            self._prev_gap = self.graph.spectral_gap()
        except Exception:  # noqa: BLE001
            self._prev_gap = None
        if persist:
            self._save()
        return {"taught_signals": taught,
                "mean_before": mean_before,
                "mean_after": round(self.field.mean_awareness(), 4),
                "ignited": self.field.ignited_topics(),
                "insights": [{"kind": i.kind, "topic": i.topic_id, "detail": i.detail,
                              "propose_new_edge": i.propose_new_edge} for i in insights]}

    def awareness_of(self, topic_id: str) -> float:
        return self.field.awareness_of(topic_id)

    def mean_awareness(self) -> float:
        """میانگینِ آگاهی روی کلِ curriculum. delegate به field.
        این متدِ سطحِ bridge است تا wiring.consolidation از جزئیاتِ داخلیِ
        field مستقل بماند (موافق با awareness_of)."""
        return self.field.mean_awareness()

    def full_awareness_vector(self) -> list[float] | None:
        """کل awareness vector [0,1]^N — نه فقط mean.
        Phase 2: برای encode_awareness در latent space."""
        try:
            return self.field.awareness.tolist()
        except Exception:  # noqa: BLE001 — fail-soft
            return None


if __name__ == "__main__":
    sb = SchoolBridge()
    print(json.dumps({"nodes": sb.graph.n_nodes, "mean": round(sb.field.mean_awareness(), 4)},
                     ensure_ascii=False))
