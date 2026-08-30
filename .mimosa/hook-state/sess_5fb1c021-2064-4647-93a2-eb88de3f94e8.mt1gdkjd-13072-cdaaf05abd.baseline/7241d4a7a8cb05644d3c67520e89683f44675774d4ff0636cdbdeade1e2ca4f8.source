"""
The linter that enforces closure.

A spec PASSES only if every BLOCKER gate passes. Blocker gates are the five
killers plus structural completeness. Consistency checks are WARN-level: they
do not fail the build but flag specs that are internally incoherent (e.g. the
kill line sits outside [baseline, expected]).

Design: no dependencies, pure dict inspection, so it runs identically in the
CLI, in CI, and (re-implemented) in the HTML tool.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .model import CANONICAL_FIELDS, is_number

VALID_OPS = {"<", "<=", ">", ">=", "==", "!="}
VALID_DIRECTIONS = {"higher_is_better", "lower_is_better"}

BLOCKER = "blocker"
WARN = "warn"


@dataclass
class Gate:
    id: str
    ok: bool
    level: str          # BLOCKER | WARN
    message: str
    killer: bool = False  # one of the five named killers


@dataclass
class Report:
    ok: bool
    gates: List[Gate] = field(default_factory=list)

    @property
    def blockers(self) -> List[Gate]:
        return [g for g in self.gates if g.level == BLOCKER]

    @property
    def warnings(self) -> List[Gate]:
        return [g for g in self.gates if g.level == WARN]

    @property
    def score(self) -> str:
        passed = sum(1 for g in self.blockers if g.ok)
        return f"{passed}/{len(self.blockers)}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "score": self.score,
            "gates": [g.__dict__ for g in self.gates],
        }


def _nonempty_str(x: Any) -> bool:
    return isinstance(x, str) and x.strip() != ""


def _nonempty_map(x: Any) -> bool:
    return isinstance(x, dict) and len(x) > 0


def validate(spec: Dict[str, Any]) -> Report:
    gates: List[Gate] = []

    # ---- G0: structural completeness -------------------------------------
    missing = [f for f in CANONICAL_FIELDS if f not in spec or spec[f] in (None, "", {}, [])]
    gates.append(Gate(
        id="structure.complete",
        ok=(len(missing) == 0),
        level=BLOCKER,
        message="all 11 canonical fields present & non-empty"
        if not missing else f"missing/empty fields: {', '.join(missing)}",
    ))

    prediction = spec.get("prediction") or {}
    metric = spec.get("metric") or {}
    failure = spec.get("failure_condition") or {}
    api = spec.get("api_contract") or {}
    mvp = spec.get("mvp") or {}
    decision = spec.get("decision_rule") or {}

    baseline = prediction.get("baseline") if isinstance(prediction, dict) else None
    expected = prediction.get("expected") if isinstance(prediction, dict) else None
    direction = metric.get("direction") if isinstance(metric, dict) else None

    # ---- KILLER 1: metric is measurable ----------------------------------
    metric_ok = (
        isinstance(metric, dict)
        and _nonempty_str(metric.get("name"))
        and direction in VALID_DIRECTIONS
        and is_number(baseline)
        and is_number(expected)
    )
    gates.append(Gate(
        id="killer.metric",
        ok=metric_ok,
        level=BLOCKER,
        killer=True,
        message="metric has name + direction, and prediction has numeric baseline & expected"
        if metric_ok else
        "NO MEASURABLE METRIC -> useless. Need metric.name, metric.direction "
        "(higher_is_better|lower_is_better), and numeric prediction.baseline & prediction.expected.",
    ))

    # ---- KILLER 2: falsifiability ----------------------------------------
    fc_op = failure.get("op") if isinstance(failure, dict) else None
    fc_thr = failure.get("threshold") if isinstance(failure, dict) else None
    fc_metric = failure.get("metric") if isinstance(failure, dict) else None
    falsifiable = (
        isinstance(failure, dict)
        and _nonempty_str(fc_metric)
        and fc_op in VALID_OPS
        and is_number(fc_thr)
    )
    gates.append(Gate(
        id="killer.falsifiability",
        ok=falsifiable,
        level=BLOCKER,
        killer=True,
        message=f"failure_condition is a testable predicate ({fc_metric} {fc_op} {fc_thr})"
        if falsifiable else
        "NOT FALSIFIABLE -> pseudo-research. Need failure_condition.metric, "
        ".op (< <= > >= == !=) and numeric .threshold.",
    ))

    # ---- KILLER 3: api_contract (connectable) ----------------------------
    api_ok = (
        isinstance(api, dict)
        and _nonempty_str(api.get("endpoint"))
        and _nonempty_str(api.get("method"))
        and _nonempty_map(api.get("request"))
        and _nonempty_map(api.get("response"))
    )
    gates.append(Gate(
        id="killer.api",
        ok=api_ok,
        level=BLOCKER,
        killer=True,
        message="api_contract has endpoint, method, non-empty request & response"
        if api_ok else
        "NO API CONTRACT -> not connectable. Need api_contract.endpoint, .method, "
        "and non-empty .request and .response shapes.",
    ))

    # ---- KILLER 4: mvp (runnable) ----------------------------------------
    mvp_ok = (
        isinstance(mvp, dict)
        and _nonempty_str(mvp.get("stack"))
        and _nonempty_str(mvp.get("effort"))
    )
    gates.append(Gate(
        id="killer.mvp",
        ok=mvp_ok,
        level=BLOCKER,
        killer=True,
        message="mvp declares a stack and an effort estimate"
        if mvp_ok else
        "NO MVP -> not runnable. Need mvp.stack and mvp.effort (e.g. '< 1 day').",
    ))

    # ---- KILLER 5: decision_rule (closure) -------------------------------
    rules = decision.get("rules") if isinstance(decision, dict) else None
    rules_ok = False
    rule_msg = (
        "NO DECISION RULE -> no closure. Need decision_rule.rules: a list of >=2 "
        "bands, each with a verdict and numeric min/max on the primary metric."
    )
    if isinstance(rules, list) and len(rules) >= 2:
        good = True
        for r in rules:
            if not isinstance(r, dict) or not _nonempty_str(r.get("verdict")):
                good = False
                break
            has_bound = is_number(r.get("min")) or is_number(r.get("max"))
            if not has_bound:
                good = False
                break
        rules_ok = good
        if good:
            verdicts = ", ".join(str(r.get("verdict")) for r in rules)
            rule_msg = f"decision_rule closes the loop over {len(rules)} bands ({verdicts})"
    gates.append(Gate(
        id="killer.decision_rule",
        ok=rules_ok,
        level=BLOCKER,
        killer=True,
        message=rule_msg,
    ))

    # ---- WARN A: expected must beat baseline in the metric's direction ----
    if is_number(baseline) and is_number(expected) and direction in VALID_DIRECTIONS:
        if direction == "higher_is_better":
            beat = expected > baseline
        else:
            beat = expected < baseline
        gates.append(Gate(
            id="consistency.expected_beats_baseline",
            ok=beat,
            level=WARN,
            message="expected improves on baseline in the stated direction"
            if beat else
            f"expected ({expected}) does not beat baseline ({baseline}) for {direction}.",
        ))

    # ---- WARN B: kill line sits between baseline and expected -------------
    if is_number(baseline) and is_number(expected) and is_number(fc_thr) and direction in VALID_DIRECTIONS:
        lo, hi = min(baseline, expected), max(baseline, expected)
        between = lo <= fc_thr <= hi
        gates.append(Gate(
            id="consistency.kill_line_placement",
            ok=between,
            level=WARN,
            message="failure threshold is a real kill line (inside [baseline, expected])"
            if between else
            f"failure threshold {fc_thr} is outside [{lo}, {hi}] -> the experiment "
            "can 'fail' without ever contradicting the hypothesis.",
        ))

    # ---- WARN C: decision_rule discard band aligns with failure line ------
    if rules_ok and is_number(fc_thr) and direction in VALID_DIRECTIONS:
        discard_bands = [r for r in rules if "discard" in str(r.get("verdict", "")).lower()
                         or "reject" in str(r.get("verdict", "")).lower()]
        aligned = False
        for r in discard_bands:
            rmin = r.get("min", float("-inf"))
            rmax = r.get("max", float("inf"))
            rmin = rmin if is_number(rmin) else float("-inf")
            rmax = rmax if is_number(rmax) else float("inf")
            # the failure threshold should touch the discard band edge
            if rmin <= fc_thr <= rmax:
                aligned = True
                break
        gates.append(Gate(
            id="consistency.decision_vs_failure",
            ok=aligned,
            level=WARN,
            message="decision_rule DISCARD band is consistent with failure_condition"
            if aligned else
            "decision_rule DISCARD band does not line up with failure_condition.threshold.",
        ))

    ok = all(g.ok for g in gates if g.level == BLOCKER)
    return Report(ok=ok, gates=gates)


def format_report(report: Report, title: str = "") -> str:
    """Human-readable, colour-free report for terminals/CI."""
    lines: List[str] = []
    head = "PASS" if report.ok else "FAIL"
    lines.append(f"[{head}] {title}  (blocker gates {report.score})")
    lines.append("-" * 68)
    for g in report.gates:
        mark = "OK " if g.ok else "XX "
        tag = "KILLER" if g.killer else ("BLOCK" if g.level == BLOCKER else "warn ")
        lines.append(f" {mark}{tag}  {g.id}")
        if not g.ok or g.killer:
            lines.append(f"        -> {g.message}")
    lines.append("-" * 68)
    if report.ok:
        lines.append("Result: spec is executable (all killers satisfied).")
    else:
        failed = [g.id for g in report.blockers if not g.ok]
        lines.append(f"Result: blocked by -> {', '.join(failed)}")
    return "\n".join(lines)
