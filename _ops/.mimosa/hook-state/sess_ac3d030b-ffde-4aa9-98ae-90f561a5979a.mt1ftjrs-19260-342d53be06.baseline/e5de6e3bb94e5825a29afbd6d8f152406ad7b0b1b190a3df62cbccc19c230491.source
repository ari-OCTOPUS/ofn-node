"""shadow_evaluation.py — فاز L: مقایسه و ارزیابی مسیر واقعی vs سایه.

معیارها (حداقل ۷ روز یا آستانهٔ نمونه):
  1) divergence rate — چند بار سایه با واقعی فرق داشت
  2) shadow_slow_down — چند بار سایه «کندتر» پیشنهاد داد
  3) false_positive — سایه slow_down ولی واقعی continue بدون incident
  4) churn — نوسان بی‌دلیل shadow_decision
  5) integrity — هیچ applied=true / may_authorize=true در رکوردها

نتیجهٔ نهایی: KEEP_ADVISORY (داده کافی نیست) یا READY_FOR_VOTE (معیارها برقرار)
یا REVIEW_REQUIRED (نقض integrity / نرخ بالا).

fail-soft مطلق؛ فقط خواندن divergence.jsonl.
"""
from __future__ import annotations

import json
import os
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
STATE_DIR = Path(os.environ.get("OCTOPUS_STATE_DIR", str(_OPS / "state")))
DIVERGENCE = STATE_DIR / "shadow-influence" / "divergence.jsonl"

EVAL_SCHEMA = "shadow-evaluation.v1"
MIN_DAYS = 7
MIN_SAMPLES = 100


def _load_records() -> list[dict]:
    out: list[dict] = []
    try:
        if not DIVERGENCE.is_file():
            return []
        for line in DIVERGENCE.read_text("utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                if isinstance(d, dict):
                    out.append(d)
            except ValueError:
                continue
    except OSError:
        pass
    return out


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def evaluate(window_days: int = MIN_DAYS, min_samples: int = MIN_SAMPLES) -> dict[str, Any]:
    records = _load_records()
    now = datetime.now(timezone.utc)

    # پنجرهٔ زمانی
    cutoff = now - timedelta(days=window_days)
    in_window = [r for r in records
                 if (_parse_ts(r.get("ts")) or now) >= cutoff]

    integrity_violations: list[str] = []
    for r in records:
        if r.get("applied") is True:
            integrity_violations.append("applied_true")
        if r.get("may_authorize") is True:
            integrity_violations.append("may_authorize_true")

    n = len(in_window)
    if n < min_samples:
        return {
            "schema": EVAL_SCHEMA,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "verdict": "KEEP_ADVISORY",
            "reason": f"insufficient data: {n}/{min_samples} samples",
            "window_days": window_days,
            "records_in_window": n,
            "records_total": len(records),
            "integrity_violations": integrity_violations,
            "metrics": None,
        }

    diverged = [r for r in in_window if r.get("divergence")]
    slow = [r for r in in_window
            if r.get("shadow_decision") == "slow_down"]
    fp = [r for r in in_window
          if r.get("shadow_decision") == "slow_down"
          and r.get("real_decision") == "continue"]
    decisions = Counter(r.get("shadow_decision") for r in in_window)

    metrics = {
        "divergence_rate": round(len(diverged) / n, 4),
        "shadow_slow_down_rate": round(len(slow) / n, 4),
        "false_positive_rate": round(len(fp) / n, 4),
        "churn": len(decisions) - 1,
        "shadow_decision_distribution": dict(decisions),
    }

    if integrity_violations:
        verdict = "REVIEW_REQUIRED"
        reason = "integrity violation: " + "; ".join(sorted(set(integrity_violations)))
    elif metrics["false_positive_rate"] > 0.5:
        verdict = "REVIEW_REQUIRED"
        reason = f"false_positive_rate={metrics['false_positive_rate']} > 0.5"
    else:
        verdict = "READY_FOR_VOTE"
        reason = "shadow window complete; no integrity violation; FP within tolerance"

    return {
        "schema": EVAL_SCHEMA,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verdict": verdict,
        "reason": reason,
        "window_days": window_days,
        "records_in_window": n,
        "records_total": len(records),
        "integrity_violations": integrity_violations,
        "metrics": metrics,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
