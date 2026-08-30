"""
The executable half: a generic ablation runner + decision-rule engine.

The point of this module is that `evaluation` and `decision_rule` are not prose
in a doc — they run. You register conditions (baseline + treatment variants),
the harness runs each over N seeds, then it:

  1. reads the primary condition's metric,
  2. checks the falsifiable failure_condition,
  3. applies the decision_rule bands,
  4. returns a machine verdict: DISCARD / OPTIMIZE / INTEGRATE (or your labels).

Conditions are just callables `run(rng) -> float`, so real experiments and the
seeded synthetic mocks in demo/mock_experiments.py plug into the same interface.
Nothing here is model-specific and nothing imports a heavy dependency.
"""
from __future__ import annotations

import math
import statistics
import zlib
from dataclasses import dataclass
from random import Random
from typing import Any, Callable, Dict, List, Optional

from .model import is_number


def _stable_hash(name: str) -> int:
    """Process-independent hash so runs are reproducible (unlike built-in hash())."""
    return zlib.crc32(name.encode("utf-8")) % 100000

OPS: Dict[str, Callable[[float, float], bool]] = {
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


@dataclass
class Condition:
    name: str
    run: Callable[[Random], float]   # given a seeded RNG, return one metric draw
    description: str = ""


@dataclass
class ConditionResult:
    name: str
    mean: float
    std: float
    values: List[float]


@dataclass
class RunResult:
    conditions: List[ConditionResult]
    primary: str
    primary_value: float
    direction: str
    failed: bool                     # failure_condition triggered?
    verdict: str
    ablation: Dict[str, float]       # treatment - baseline deltas vs the worst/first

    def best(self) -> ConditionResult:
        rev = self.direction == "higher_is_better"
        return sorted(self.conditions, key=lambda c: c.mean, reverse=rev)[0]


def run_ablation(conditions: List[Condition], seeds: int = 5,
                 base_seed: int = 1234) -> List[ConditionResult]:
    results: List[ConditionResult] = []
    for cond in conditions:
        values: List[float] = []
        for s in range(seeds):
            rng = Random(base_seed + s * 101 + _stable_hash(cond.name))
            values.append(float(cond.run(rng)))
        mean = statistics.fmean(values)
        std = statistics.pstdev(values) if len(values) > 1 else 0.0
        results.append(ConditionResult(cond.name, mean, std, values))
    return results


def check_failure(value: float, failure_condition: Dict[str, Any]) -> bool:
    """Return True if the failure predicate is satisfied (i.e. hypothesis rejected)."""
    op = failure_condition.get("op")
    thr = failure_condition.get("threshold")
    if op not in OPS or not is_number(thr):
        return False
    return OPS[op](value, float(thr))


def decide(value: float, decision_rule: Dict[str, Any]) -> str:
    """Apply decision_rule bands. Bands: {min?, max?, verdict}. min inclusive, max exclusive."""
    rules = (decision_rule or {}).get("rules", [])
    for r in rules:
        lo = r.get("min", -math.inf)
        hi = r.get("max", math.inf)
        lo = lo if is_number(lo) else -math.inf
        hi = hi if is_number(hi) else math.inf
        if lo <= value < hi:
            return str(r.get("verdict", "UNSPECIFIED"))
    return "NO_MATCHING_BAND"


def run_spec(spec: Dict[str, Any], conditions: List[Condition],
             primary: Optional[str] = None, seeds: Optional[int] = None) -> RunResult:
    metric = spec.get("metric", {}) or {}
    direction = metric.get("direction", "higher_is_better")
    n_seeds = seeds or (spec.get("evaluation", {}) or {}).get("seeds", 5)

    results = run_ablation(conditions, seeds=n_seeds)
    by_name = {r.name: r for r in results}

    if primary is None:
        primary = metric.get("primary_condition") or results[-1].name
    if primary not in by_name:
        raise ValueError(
            f"primary condition '{primary}' is not among the run's conditions "
            f"({', '.join(by_name)}) - refusing to silently judge another one.")
    primary_value = by_name[primary].mean

    failed = check_failure(primary_value, spec.get("failure_condition", {}) or {})
    verdict = "REJECTED (failure_condition met)" if failed else decide(primary_value, spec.get("decision_rule", {}) or {})

    # ablation deltas vs the first (baseline) condition
    base = results[0].mean
    ablation = {r.name: round(r.mean - base, 4) for r in results}

    return RunResult(
        conditions=results,
        primary=primary,
        primary_value=primary_value,
        direction=direction,
        failed=failed,
        verdict=verdict,
        ablation=ablation,
    )


def format_run(result: RunResult, spec: Dict[str, Any], title: str = "",
               provenance: str = "[SYNTHETIC/mock scores]") -> str:
    metric = spec.get("metric", {}) or {}
    mname = metric.get("name", "metric")
    lines: List[str] = []
    lines.append(f"# RUN  {title}")
    lines.append(f"metric = {mname}  ({result.direction})   {provenance}")
    lines.append("-" * 60)
    lines.append(f"{'condition':<26}{'mean':>8}{'std':>8}{'delta':>9}")
    for c in result.conditions:
        d = result.ablation.get(c.name, 0.0)
        lines.append(f"{c.name:<26}{c.mean:>8.3f}{c.std:>8.3f}{d:>+9.3f}")
    lines.append("-" * 60)
    lines.append(f"primary condition : {result.primary}  = {result.primary_value:.3f}")
    fc = spec.get("failure_condition", {}) or {}
    lines.append(f"failure_condition : {fc.get('metric')} {fc.get('op')} {fc.get('threshold')}  -> "
                 f"{'TRIGGERED (reject)' if result.failed else 'not triggered'}")
    lines.append(f"VERDICT           : {result.verdict}")
    return "\n".join(lines)
