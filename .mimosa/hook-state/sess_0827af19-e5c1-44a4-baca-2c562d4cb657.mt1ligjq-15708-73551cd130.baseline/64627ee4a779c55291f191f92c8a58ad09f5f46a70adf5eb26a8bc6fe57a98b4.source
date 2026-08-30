"""telemetry.py — sensory loop / حلقهٔ حسی.

معماری:
  • هر worker/arm بعد از job، structured telemetry record می‌نویسد
  • fields: job_id, worker, intent, duration_ms, cost_aud, error, outcome, correlation_id
  • append-only JSONL — stdlib-only
  • feeds into learning brain (ThompsonBandit, calibration, baseline)

نقش در استعاره: حلقهٔ حسی — بازو حس می‌کند، به مرکز گزارش می‌دهد، مرکز calibration می‌کند.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional, List


class Telemetry:
    """Sensory loop: append-only structured telemetry per job execution.

    Usage:
        telem = Telemetry(Path("/tmp/octopus/telemetry.jsonl"))
        telem.record("job-123", "ziman-worker", "generate_draft",
                     duration_ms=450, cost_aud=0.02, outcome={"drafts": 1})
    """

    def __init__(self, path: Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, job_id: str, worker: str, intent: str,
               duration_ms: float, cost_aud: float = 0.0,
               error: Optional[str] = None, outcome: Optional[dict] = None,
               correlation_id: Optional[str] = None,
               meta: Optional[dict] = None) -> None:
        """یک رکورد telemetry append-only ثبت می‌کند."""
        record = {
            "ts": time.time(),
            "job_id": job_id,
            "worker": worker,
            "intent": intent,
            "duration_ms": round(float(duration_ms), 3),
            "cost_aud": round(float(cost_aud), 6),
            "error": error,
            "outcome": outcome or {},
            "correlation_id": correlation_id or f"CID-{int(time.time()*1000)}",
            "meta": meta or {},
        }
        try:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def query(self, worker: Optional[str] = None, intent: Optional[str] = None,
              since: Optional[float] = None, until: Optional[float] = None,
              has_error: Optional[bool] = None,
              n: int = 500) -> List[dict]:
        """فایل JSONL را می‌خواند و فیلتر می‌کند."""
        results: List[dict] = []
        if not self._path.exists():
            return results
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if worker and r.get("worker") != worker:
                        continue
                    if intent and r.get("intent") != intent:
                        continue
                    ts = r.get("ts", 0)
                    if since and ts < since:
                        continue
                    if until and ts > until:
                        continue
                    if has_error is True and not r.get("error"):
                        continue
                    if has_error is False and r.get("error"):
                        continue
                    results.append(r)
        except OSError:
            pass
        results.sort(key=lambda x: x.get("ts", 0))
        return results[-n:]

    def summary(self, worker: Optional[str] = None, since: Optional[float] = None) -> dict:
        """آمار خلاصه برای calibration brain."""
        rows = self.query(worker=worker, since=since, n=10000)
        if not rows:
            return {"count": 0, "total_cost_aud": 0.0, "avg_duration_ms": 0.0,
                    "error_rate": 0.0, "intents": []}
        total_cost = sum(r.get("cost_aud", 0) for r in rows)
        total_dur = sum(r.get("duration_ms", 0) for r in rows)
        errors = sum(1 for r in rows if r.get("error"))
        intents = {}
        for r in rows:
            i = r.get("intent", "unknown")
            intents[i] = intents.get(i, 0) + 1
        return {
            "count": len(rows),
            "total_cost_aud": round(total_cost, 6),
            "avg_duration_ms": round(total_dur / len(rows), 3),
            "error_rate": round(errors / len(rows), 3),
            "intents": intents,
        }


class TelemetryBus:
    """telemetry + event_bus integration: هر telemetry record به عنوان رویداد هم publish می‌شود."""

    def __init__(self, telemetry: Telemetry, bus=None):
        self.telemetry = telemetry
        self.bus = bus

    def record(self, *args, **kwargs) -> None:
        self.telemetry.record(*args, **kwargs)
        if self.bus:
            try:
                self.bus.publish("sensory.telemetry", {
                    "job_id": kwargs.get("job_id"),
                    "worker": kwargs.get("worker"),
                    "intent": kwargs.get("intent"),
                    "duration_ms": kwargs.get("duration_ms"),
                    "cost_aud": kwargs.get("cost_aud"),
                    "error": kwargs.get("error"),
                    "outcome": kwargs.get("outcome"),
                }, correlation_id=kwargs.get("correlation_id"),
                   source=kwargs.get("worker", "unknown"))
            except Exception:
                pass
