# -*- coding: utf-8 -*-
"""T72 — sense → record → assess → propose → owner feedback → learn."""
from __future__ import annotations

import json
from pathlib import Path

from .paths import ORGANS_STATE, assert_not_telegram

STAGES = ("sense", "record", "assess", "propose", "owner_feedback", "learn")
DEAD = "DEAD_FEEDBACK_LOOP"


def assess_loop(organ_id: str, *, proposals: int, votes: int, effects: int,
                has_acceptance_criteria: bool) -> dict:
    stages_ok = {
        "sense": True,
        "record": True,
        "assess": True,
        "propose": proposals > 0,
        "owner_feedback": votes > 0,
        "learn": effects > 0 or votes > 0,
    }
    dead = proposals > 0 and votes == 0 and effects == 0
    label = DEAD if dead else "CLOSED_OR_WAITING"
    action = None
    if dead and not has_acceptance_criteria:
        action = "disable_via_flag"
    elif dead:
        action = "keep_with_acceptance_criteria"
    return {
        "organ_id": organ_id,
        "stages": stages_ok,
        "proposals": proposals,
        "votes": votes,
        "effects": effects,
        "label": label,
        "action": action,
        "executable": False,
    }


def write_loops(rows: list[dict], *, root: Path | None = None) -> Path:
    root = Path(root) if root is not None else ORGANS_STATE
    p = root / "feedback-loops.json"
    assert_not_telegram(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"loops": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    return p
