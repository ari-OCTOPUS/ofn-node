#!/usr/bin/env python3
"""ab_tracker.py — #4: A/B Test Tracker. ثبت، track، تحلیل آماری."""
from __future__ import annotations
import json, math, os, time
from dataclasses import dataclass, field, asdict
from pathlib import Path

# state قابل‌انحراف با PF_BRAIN_DIR (تست/harness)؛ بدونِ env = کنارِ ماژول (production)
# ۲۰۲۶-۰۸-۰۳ fix: lazy resolution (الگوی saba_link._studio_dir) — قبلاً module-level
# constant بود و تست‌ها را به ترتیبِ اجرا حساس می‌کرد.
def _data_path() -> Path:
    env = os.environ.get("PF_BRAIN_DIR")
    base = Path(env) if env else Path(__file__).resolve().parent
    return base / "ab_tests.json"


SIGNIFICANCE_THRESHOLD = 0.15  # relative diff → declare winner


@dataclass
class ABTest:
    test_id: str
    name: str
    variant_a: dict   # {tag, description}
    variant_b: dict
    platform: str = "reddit"
    status: str = "running"  # running | won_a | won_b | inconclusive
    results_a: list[dict] = field(default_factory=list)
    results_b: list[dict] = field(default_factory=list)
    winner: str | None = None
    created_ts: float = field(default_factory=time.time)


class ABTestTracker:
    """A/B test: create → record → analyze → winner. persist (JSON)."""

    def __init__(self, data_path=None):
        self._path = Path(data_path) if data_path else _data_path()
        self._tests: dict[str, dict] = self._load()

    def _load(self):
        try: return json.loads(self._path.read_text(encoding="utf-8"))
        except: return {}

    def _save(self):
        try:
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._tests, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self._path)
        except OSError: pass

    def create_test(self, name: str, variant_a: dict, variant_b: dict,
                    platform: str = "reddit") -> str:
        test_id = f"AB-{len(self._tests)+1:03d}"
        test = ABTest(test_id=test_id, name=name, variant_a=variant_a,
                      variant_b=variant_b, platform=platform)
        self._tests[test_id] = asdict(test)
        self._save()
        return test_id

    def record_result(self, test_id: str, variant: str,
                      upvotes: int = 0, comments: int = 0, unlocks: int = 0):
        if test_id not in self._tests: return
        result = {"upvotes": upvotes, "comments": comments, "unlocks": unlocks, "ts": time.time()}
        key = f"results_{variant}"
        self._tests[test_id].setdefault(key, []).append(result)
        self._save()

    def analyze(self, test_id: str) -> dict:
        if test_id not in self._tests: return {}
        t = self._tests[test_id]
        ra = t.get("results_a", [])
        rb = t.get("results_b", [])
        if not ra or not rb: return {"status": "no_data"}
        def avg(data, key):
            vals = [d.get(key, 0) for d in data]
            return sum(vals)/len(vals) if vals else 0
        def score(data):
            return avg(data, "upvotes")/100 + avg(data, "comments")/20 + avg(data, "unlocks")/5
        sa = score(ra); sb = score(rb)
        diff = abs(sa - sb)
        relative = diff / max(sa, sb, 0.001)
        winner = "a" if sa > sb else "b"
        significant = relative >= SIGNIFICANCE_THRESHOLD
        return {"score_a": round(sa,3), "score_b": round(sb,3),
                "winner": winner, "significant": significant,
                "relative_diff": round(relative,3), "n_a": len(ra), "n_b": len(rb)}

    def auto_winner(self, test_id: str) -> str | None:
        result = self.analyze(test_id)
        if result.get("significant") and result.get("winner"):
            w = result["winner"]
            self._tests[test_id]["status"] = f"won_{w}"
            self._tests[test_id]["winner"] = w
            self._save()
            return w
        return None

    @property
    def tests(self): return list(self._tests.values())

    def get(self, test_id): return self._tests.get(test_id, {})
