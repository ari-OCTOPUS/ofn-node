#!/usr/bin/env python3
# heart/state_machine.py - life FSM (fail-closed, no threat->capability edge).
# Persian doc: map-e halat-e hayat. All string literals below are pure ASCII;
# a self-check at import asserts key purity (invisible-char contamination guard).

STATES = ("GENESIS", "BOOTING", "WARMUP", "RUNNING", "DEGRADED", "SAFE",
          "COMA", "DORMANT")

RECOVERY_STREAK = 3

_EDGES = {
    "GENESIS": {"BOOTING"},
    "BOOTING": {"WARMUP", "RUNNING"},
    "WARMUP": {"RUNNING", "SAFE", "COMA", "DORMANT"},
    "RUNNING": {"DEGRADED", "SAFE", "COMA", "DORMANT"},
    "DEGRADED": {"RUNNING", "SAFE", "COMA", "DORMANT"},
    "SAFE": {"RUNNING", "COMA", "DORMANT"},
    "COMA": {"WARMUP", "DORMANT"},
    "DORMANT": set(),
}


def _assert_purity() -> None:
    """Guard: every state name must be built from exactly these ASCII bytes.

    Rationale (2026-08-25): a prior revision of this file carried an invisible
    Unicode mark inside one state key; cross-source comparisons silently failed
    while same-source comparisons passed. This check makes that class of bug
    loud at import time.
    """
    expected = {
        "GENESIS": (71, 69, 78, 69, 83, 73, 83),
        "BOOTING": (66, 79, 79, 84, 73, 78, 71),
        "WARMUP": (87, 65, 82, 77, 85, 80),
        "RUNNING": (82, 85, 78, 78, 73, 78, 71),
        "DEGRADED": (68, 69, 71, 82, 65, 68, 69, 68),
        "SAFE": (83, 65, 70, 69),
        "COMA": (67, 79, 77, 65),
        "DORMANT": (68, 79, 82, 77, 65, 78, 84),
    }
    for name in STATES:
        want = bytes(expected[name])
        got = name.encode("utf-8")
        if got != want:
            raise ValueError(
                f"state literal contaminated: {name!r} bytes={got.hex()} "
                f"expected={want.hex()}")
    for key, targets in _EDGES.items():
        if key not in expected:
            raise ValueError(f"unknown edge key {key!r}")
        for t in targets:
            if t not in expected:
                raise ValueError(f"unknown edge target {t!r} from {key!r}")


_assert_purity()


def can_transition(current: str, target: str) -> bool:
    return target in _EDGES.get(current, set())


def assess_transition(current: str, *, kill: bool = False,
                      journal_failure: bool = False,
                      red: bool = False, degraded_inputs: bool = False,
                      green_streak: int = 0, warmup_ready: bool = False,
                      coma_recovered: bool = False) -> tuple[str, list[str]]:
    """(new_state, reasons). Kill is supreme; fail-closed throughout.

    Legal: BOOTING->WARMUP/RUNNING, WARMUP->RUNNING(needs ready),
    RUNNING->DEGRADED/SAFE, DEGRADED->RUNNING(needs streak),
    SAFE->RUNNING(needs streak), any(journal)->COMA, COMA->WARMUP(recovery),
    any(kill)->DORMANT(terminal). No edge raises capability from a threat
    state without recovery evidence (anti-threat->capability invariant)."""
    reasons: list[str] = []
    if kill:
        return "DORMANT", ["kill-switch supreme"]
    if journal_failure:
        reasons.append("journal commit failure sustained")
        if can_transition(current, "COMA"):
            return "COMA", reasons
        return current, reasons + [f"illegal COMA from {current} (held)"]
    if red:
        if can_transition(current, "SAFE"):
            return "SAFE", ["RED vitals / integrity conflict"]
        reasons.append(f"RED held in {current}")
        return current, reasons
    if current == "SAFE" or current == "DEGRADED" or (
            current == "WARMUP" and not warmup_ready):
        if green_streak >= RECOVERY_STREAK:
            target = "RUNNING"
            if can_transition(current, target):
                return target, [
                    f"recovery streak {green_streak}/{RECOVERY_STREAK}"]
        return current, [
            f"awaiting recovery streak {green_streak}/{RECOVERY_STREAK}"]
    if current == "WARMUP" and warmup_ready:
        return "RUNNING", ["sensor windows ready"]
    if current == "BOOTING":
        return ("WARMUP", ["booting to warmup"]) if not warmup_ready else \
               ("RUNNING", ["booting ready"])
    if current == "COMA" and coma_recovered and green_streak >= RECOVERY_STREAK:
        return "WARMUP", ["coma recovery evidence + streak"]
    if degraded_inputs:
        if can_transition(current, "DEGRADED"):
            return "DEGRADED", ["non-vital sensor/provider degraded"]
        return current, reasons + [f"degraded held in {current}"]
    return current, ["no change"]
