"""Bitemporal recall preserves superseded meaning; calibration is observed, not assumed."""
import math
from shadow_homeostasis.canonical import digest, finite_number
from shadow_homeostasis.observation import parse_dt


class Experience:
    def __init__(self, store):
        self.store = store

    def remember(self, memory):
        if set(memory) != {"id", "occurred_at", "recorded_at", "payload", "supersedes"}:
            raise ValueError("memory contract")
        if not isinstance(memory["id"], str) or not memory["id"]:
            raise ValueError("memory identity")
        occ, rec = parse_dt(memory["occurred_at"]), parse_dt(memory["recorded_at"])
        if occ is None or rec is None or occ > rec:
            raise ValueError("memory temporal order")
        history = self.history()
        parent = memory["supersedes"]
        if parent is not None and parent not in {m["id"] for m in history}:
            raise ValueError("superseded memory missing")
        if parent == memory["id"]:
            raise ValueError("self supersession")
        if parent is not None:
            prior = next(m for m in history if m["id"] == parent)
            if parse_dt(prior["recorded_at"]) > rec:
                raise ValueError("supersession recorded before parent")
        return self.store.append_record("memory", "memory:" + memory["id"], memory)

    def history(self):
        return [r["payload"] for r in self.store.records if r["kind"] == "memory"]

    def query(self, *, valid_at, known_at, include_superseded=False):
        va, ka = parse_dt(valid_at), parse_dt(known_at)
        if va is None or ka is None:
            raise ValueError("query time required")
        result = [m for m in self.history()
                  if parse_dt(m["occurred_at"]) <= va and parse_dt(m["recorded_at"]) <= ka]
        superseded = {m["supersedes"] for m in result}
        if not include_superseded:
            result = [m for m in result if m["id"] not in superseded]
        return sorted(result, key=lambda m: (parse_dt(m["recorded_at"]), m["id"]))


def calibration_report(trials):
    if not isinstance(trials, list) or len(trials) > 256:
        raise ValueError("calibration budget")
    for t in trials:
        if (not finite_number(t["confidence"])
                or not 0 <= t["confidence"] <= 1 or type(t["outcome"]) is not bool):
            raise ValueError("calibration needs probability and observed Boolean outcome")
    return {"n": len(trials),
            "brier_score": sum((t["confidence"] - int(t["outcome"])) ** 2 for t in trials) / len(trials) if trials else None,
            "confident_wrong_count": sum(t["confidence"] >= .9 and not t["outcome"] for t in trials),
            "claim": "provided trial outcomes only; no metacontrol recalibration",
            "executable": False}
