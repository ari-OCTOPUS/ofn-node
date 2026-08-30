#!/usr/bin/env python3
"""consolidation.py — 4D Brain consolidation (episodic → semantic memory).

REVIVAL 2026-08-02: 4d_system had NO consolidation module. Experiments and reflections
persisted as flat records with no distillation. This module forks the proven machinery
from `_ops/neural/consolidation.py` (ConsolidationCycle) and adapts the verification
gate for 4D-specific sources.

Sources consolidated:
  - frontier        : MAP-Elites archive (newly discovered cells)
  - conclusions     : synthesized mathematical conclusions
  - experiments     : recent experiment results from SQLite
  - self_growth     : learned capabilities / current focus
  - reflections     : self-reflection quality evaluations

Key machinery reused from _ops/neural/consolidation.py:
  - Verification Gate (AlphaEvolve): only verified sources → learned
  - Content-signature dedup with time-floor (prevents unbounded growth)
  - recall_reach() metric: the only metric that can prove "getting better at remembering"

Wiring: called periodically by the daemon alongside housekeeping (e.g. every
DAEMON_CONSOLIDATION_EVERY ticks, default = DAEMON_HK_EVERY).

Design principles (matching _ops original):
  - fail-soft: never crash the daemon; missing sources → skip
  - stdlib-only: no external deps
  - idempotent: same sources → same result
  - atomic writes: .tmp → replace
"""
from __future__ import annotations
import hashlib
import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path


def _now() -> float:
    """Single time source — patchable for tests (same lesson as _ops original)."""
    return time.time()


def _flag(name: str) -> bool:
    return os.environ.get(name, "0") == "1"


def _compress_on() -> bool:
    return _flag("OCTOPUS_4D_CONSOLIDATION_COMPRESS")


def _floor_seconds() -> float:
    """Time floor for dedup. Default 6h — same calibration as _ops (37 rows from 538)."""
    try:
        return float(os.environ.get("OCTOPUS_4D_CONSOLIDATION_FLOOR_SEC", "21600"))
    except ValueError:
        return 21600.0


def _default_data_path() -> Path:
    """4D outputs dir; env-overridable for isolated tests (same OPS_DIR lesson)."""
    ops = os.environ.get("OPS_DIR")
    if ops:
        return Path(ops) / "consolidation.json"
    # default: alongside self_evolved artifacts in 4d outputs
    return Path(__file__).resolve().parent.parent / "outputs" / "self_evolved" / "consolidation.json"


_DATA_PATH = _default_data_path()


@dataclass
class ConsolidatedInsight:
    """Output of one consolidation cycle for 4D brain."""
    cycle: int
    insights: list[str]
    verified_sources: list[str]
    discarded_sources: list[str]
    timestamp: float = field(default_factory=lambda: _now())
    latent_vector: list[float] | None = None
    similar_keys: list[str] | None = None


def _verify_source(name: str, data) -> bool:
    """Verification Gate — adapted for 4D sources.

    4D sources differ from _ops sources: they are research artifacts, not business
    metrics. Verification rules:
      - frontier:      must have dict with cells and a non-zero count of new discoveries
      - conclusions:   must have anchors_ok=True (math integrity verified)
      - experiments:   must be a list of valid experiment dicts with verdict
      - self_growth:   must have current focus / capabilities
      - reflections:   must be list of reflection dicts with score
    """
    if name == "frontier" and isinstance(data, dict):
        cells = data.get("cells") or data.get("n_cells") or 0
        return isinstance(cells, (int, float)) and cells > 0
    if name == "conclusions" and isinstance(data, dict):
        return bool(data.get("anchors_ok"))
    if name == "experiments" and isinstance(data, list):
        return all(isinstance(d, dict) and "verdict" in d for d in data if isinstance(d, dict)) and len(data) > 0
    if name == "self_growth" and isinstance(data, dict):
        return bool(data.get("current_focus") or data.get("capabilities"))
    if name == "reflections" and isinstance(data, list):
        return all(isinstance(d, dict) and "score" in d for d in data if isinstance(d, dict)) and len(data) > 0
    return False


class ConsolidationCycle:
    """4D deep-sleep consolidation. Synthesize verified sources into persistent insights.

    Forked from _ops/neural/consolidation.py — same dedup/compression/recall machinery,
    4D-specific verification gate.
    """

    def __init__(self, data_path: str | Path | None = None):
        self._path = Path(data_path) if data_path else _DATA_PATH
        self._history: list[dict] = self._load()
        # seed cycle counter from max recorded cycle (same fix as _ops 2026-07-30)
        try:
            recorded = max(
                (int(r.get("last_cycle") or r.get("cycle") or 0)
                 for r in self._history if isinstance(r, dict)), default=0)
        except (TypeError, ValueError):
            recorded = 0
        self._cycle_count = max(recorded, len(self._history))
        self._sig_index: dict[str, int] | None = None

    def _load(self) -> list[dict]:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._history, ensure_ascii=False, indent=2),
                           encoding="utf-8")
            tmp.replace(self._path)
        except OSError:
            pass

    # ─── content-signature dedup (ported verbatim from _ops) ────────────────

    @staticmethod
    def _signature(rec: dict) -> str:
        """Content-only signature — no monotonic counters, no timestamps in the key."""
        payload = json.dumps([rec.get("insights"),
                              rec.get("verified_sources"),
                              rec.get("discarded_sources")],
                             ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def _build_sig_index(self) -> dict[str, int]:
        idx: dict[str, int] = {}
        for i, row in enumerate(self._history):
            if isinstance(row, dict):
                idx[self._signature(row)] = i
        return idx

    @staticmethod
    def _row_last_ts(row: dict) -> float:
        for k in ("last_ts", "timestamp"):
            v = row.get(k)
            if isinstance(v, (int, float)):
                return float(v)
        return 0.0

    def _foldable(self, rec: dict) -> dict | None:
        if self._sig_index is None:
            self._sig_index = self._build_sig_index()
        pos = self._sig_index.get(self._signature(rec))
        if pos is None or pos >= len(self._history):
            return None
        target = self._history[pos]
        if not isinstance(target, dict) or target.get("latent_vector") is not None:
            return None
        now = rec.get("timestamp")
        now = float(now) if isinstance(now, (int, float)) else _now()
        if (now - self._row_last_ts(target)) >= _floor_seconds():
            return None
        return target

    def run(self, sources: dict) -> ConsolidatedInsight:
        """One consolidation cycle. sources = {name: data}. Only verified → learned."""
        self._cycle_count += 1
        insights = []
        verified_names = []
        discarded_names = []

        for name, data in sources.items():
            if _verify_source(name, data):
                verified_names.append(name)
                if name == "frontier":
                    cells = data.get("cells") or data.get("n_cells") or 0
                    insights.append(f"frontier: {cells} cells discovered")
                elif name == "conclusions":
                    rate = data.get("detection_rate", "?")
                    insights.append(f"conclusions: anchors ok, detection rate {rate}")
                elif name == "experiments":
                    valid = sum(1 for d in data if isinstance(d, dict) and d.get("verdict") != "invalid")
                    insights.append(f"experiments: {valid} valid since last cycle")
                elif name == "self_growth":
                    focus = data.get("current_focus", "—")
                    caps = len(data.get("capabilities") or [])
                    insights.append(f"self_growth: focus='{focus}', {caps} capabilities")
                elif name == "reflections":
                    scores = [d.get("score", 0) for d in data if isinstance(d, dict)]
                    avg = sum(scores) / len(scores) if scores else 0
                    insights.append(f"reflections: avg quality {avg:.2f} over {len(scores)} runs")
            else:
                discarded_names.append(name)

        result = ConsolidatedInsight(
            cycle=self._cycle_count, insights=insights,
            verified_sources=verified_names, discarded_sources=discarded_names)
        rec = asdict(result)
        if _compress_on():
            target = self._foldable(rec)
        else:
            prev = self._history[-1] if self._history else None
            same = (isinstance(prev, dict)
                    and prev.get("insights") == rec["insights"]
                    and prev.get("verified_sources") == rec["verified_sources"]
                    and prev.get("discarded_sources") == rec["discarded_sources"]
                    and prev.get("latent_vector") is None)
            target = prev if same else None
        if target is not None:
            target["repeats"] = int(target.get("repeats", 1)) + 1
            target["last_cycle"] = self._cycle_count
            if _compress_on():
                ts = rec.get("timestamp")
                target["last_ts"] = float(ts) if isinstance(ts, (int, float)) else _now()
        else:
            rec["repeats"] = 1
            rec["last_cycle"] = self._cycle_count
            if _compress_on():
                ts = rec.get("timestamp")
                rec["last_ts"] = float(ts) if isinstance(ts, (int, float)) else _now()
                if self._sig_index is None:
                    self._sig_index = self._build_sig_index()
                self._sig_index[self._signature(rec)] = len(self._history)
            self._history.append(rec)
        self._save()
        return result

    def sync_latent(self, result) -> bool:
        """Write latent fields back to the persisted record for result.cycle (ported from _ops)."""
        if not self._history:
            return False
        rc = getattr(result, "cycle", None)
        if rc is None:
            return False
        scan = len(self._history) if _compress_on() else 1
        last = None
        for row in reversed(self._history[-scan:]):
            if not isinstance(row, dict):
                continue
            if int(row.get("cycle", -1)) == int(rc) or int(row.get("last_cycle", -1)) == int(rc):
                last = row
                break
        if last is None:
            return False
        changed = False
        for field_name in ("latent_vector", "similar_keys"):
            val = getattr(result, field_name, None)
            if val is not None and last.get(field_name) != val:
                last[field_name] = val
                changed = True
        if changed:
            self._save()
        return changed

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    @property
    def history(self) -> list[dict]:
        return list(self._history)


# ─── recall_reach metric (ported verbatim from _ops) ─────────────────────────

_CYCLE_RE_PREFIX = "cycle-"


def _key_cycle(key: str) -> int | None:
    s = str(key or "")
    if not s.startswith(_CYCLE_RE_PREFIX):
        return None
    head = s[len(_CYCLE_RE_PREFIX):].split(":", 1)[0]
    try:
        return int(head)
    except ValueError:
        return None


def recall_reach(history: list[dict]) -> dict:
    """Recall reach — the only metric that can prove 'getting better at remembering'.

    For each row that actually retrieved something (has similar_keys), take the distance
    |cycle(retrieved_key) - cycle(own_row)|. reach_median = median of all distances.

    Ported verbatim from _ops/neural/consolidation.py — same semantics.
    """
    rows = [r for r in (history or []) if isinstance(r, dict) and r.get("similar_keys")]
    deltas: list[int] = []
    selfhits = 0
    for r in rows:
        own = r.get("cycle")
        if not isinstance(own, int):
            continue
        for k in r.get("similar_keys") or []:
            kc = _key_cycle(k)
            if kc is None:
                continue
            d = abs(kc - own)
            deltas.append(d)
            if d == 0:
                selfhits += 1
    total_rows = len([r for r in (history or []) if isinstance(r, dict)])
    deltas.sort()
    n = len(deltas)
    if n == 0:
        median = 0.0
    elif n % 2:
        median = float(deltas[n // 2])
    else:
        median = (deltas[n // 2 - 1] + deltas[n // 2]) / 2.0
    return {"events": len(rows), "keys": n,
            "reach_median": median,
            "reach_max": (deltas[-1] if deltas else 0),
            "self_ratio": (selfhits / n) if n else 0.0,
            "coverage": (len(rows) / total_rows) if total_rows else 0.0}
