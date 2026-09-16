# -*- coding: utf-8 -*-
"""Typed contracts for one self-upgrade cycle. No secrets. No production writes."""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from . import LAB_DIR, OPS_DIR, ROOT, STATE_DIR

Layer = Literal["heart", "brain", "memory"]
Risk = Literal["LOW", "MEDIUM", "HIGH"]
Decision = Literal["PROMOTE", "REJECT", "RETRY_ONCE"]
PromoLevel = Literal["NONE", "LAB_PASS", "SHADOW_PASS", "CANARY_PASS", "PRODUCTION_VERIFIED"]

MAX_PROD_FILES = 5
MAX_DIFF_LINES = 500
MAX_CYCLE_MINUTES = 30
PAID_CALLS = "FORBIDDEN"

OWNER_TARGETS: list[dict[str, Any]] = [
    {"id": "P0-MEMORY-GATE", "layer": "memory", "priority": "P0",
     "problem": "memory gate suite vs F3 + two-phase admission (t_h NoneType, stale tests)",
     "severity": 9, "user_impact": 9, "evidence_confidence": 0.95,
     "repairability": 0.9, "dependency_value": 9, "estimated_risk": 1.2,
     "estimated_runtime": 1.0,
     "files_allowed": ["_ops/tests/test_memory_gate.py"],
     "tests_required": ["_ops/tests/test_memory_gate.py"]},
    {"id": "P0-MEMORY-TIMEOUTS", "layer": "memory", "priority": "P0",
     "problem": "test_memory_read_loop + test_memory_admission_p2 timeout in full suite",
     "severity": 7, "user_impact": 6, "evidence_confidence": 0.85,
     "repairability": 0.8, "dependency_value": 6, "estimated_risk": 1.3,
     "estimated_runtime": 1.5,
     "files_allowed": ["_ops/tests/test_memory_read_loop.py",
                       "_ops/tests/test_memory_admission_p2.py"],
     "tests_required": ["_ops/tests/test_memory_read_loop.py",
                        "_ops/tests/test_memory_admission_p2.py"]},
    {"id": "P1-BRAIN-CALIBRATION", "layer": "brain", "priority": "P1",
     "problem": "calibration-latest is DEAD-OUTPUT for improve.py (S-A03)",
     "severity": 7, "user_impact": 7, "evidence_confidence": 0.9,
     "repairability": 0.95, "dependency_value": 8, "estimated_risk": 1.1,
     "estimated_runtime": 0.8,
     "files_allowed": ["_ops/cortex/improve.py",
                       "_ops/tests/test_improve_reads_calibration.py"],
     "tests_required": ["_ops/tests/test_improve_reads_calibration.py"]},
    {"id": "P1-HEART-ORPHAN", "layer": "heart", "priority": "P1",
     "problem": "orphan watchdog exists but is not wired observe-only into organism tick",
     "severity": 7, "user_impact": 8, "evidence_confidence": 0.88,
     "repairability": 0.85, "dependency_value": 7, "estimated_risk": 1.4,
     "estimated_runtime": 1.0,
     "files_allowed": ["_ops/orphan_watchdog.py", "_ops/organism.py",
                       "_ops/tests/test_orphan_watchdog.py"],
     "tests_required": ["_ops/tests/test_orphan_watchdog.py"]},
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha16(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()[:16]


def sha256_file(path: Path, cap: int = 256_000) -> str:
    try:
        data = path.read_bytes()[:cap]
    except OSError:
        return ""
    return hashlib.sha256(data).hexdigest()


def priority_score(*, severity: float, user_impact: float, evidence_confidence: float,
                   repairability: float, dependency_value: float,
                   estimated_risk: float, estimated_runtime: float) -> float:
    den = max(0.01, float(estimated_risk)) * max(0.01, float(estimated_runtime))
    return (severity * user_impact * evidence_confidence * repairability
            * dependency_value) / den


def append_jsonl(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def write_json(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


@dataclass
class Hypothesis:
    hypothesis_id: str
    target_layer: Layer
    problem: str
    evidence_refs: list[str]
    root_cause_candidate: str
    predicted_result: str
    files_allowed: list[str]
    tests_required: list[str]
    risk: Risk
    rollback: str
    time_budget_minutes: int = 30
    target_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Experiment:
    experiment_id: str
    hypothesis_id: str
    worktree: str
    before_metrics: dict = field(default_factory=dict)
    patch_hash: str = ""
    tests: dict = field(default_factory=dict)
    after_metrics: dict = field(default_factory=dict)
    verifier: dict = field(default_factory=dict)
    decision: Decision | str = "REJECT"
    learning_id: str | None = None
    promotion_level: PromoLevel = "NONE"

    def to_dict(self) -> dict:
        return asdict(self)


def new_ids(layer: str) -> tuple[str, str, str]:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    nonce = sha16(f"{layer}|{ts}|{os.getpid()}|{time.time_ns()}".encode())[:8]
    cycle = f"CYC-{ts}-{layer[:3].upper()}-{nonce}"
    hyp = f"HYP-{ts}-{layer[:3].upper()}-{nonce}"
    exp = f"EXP-{ts}-{layer[:3].upper()}-{nonce}"
    return cycle, hyp, exp


def ensure_state_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (LAB_DIR / "worktrees").mkdir(parents=True, exist_ok=True)
    for name in ("heart", "brain", "memory"):
        (LAB_DIR / "worktrees" / name).mkdir(parents=True, exist_ok=True)
    (LAB_DIR / "patches").mkdir(parents=True, exist_ok=True)


def secret_scan(text: str) -> list[str]:
    """Name-only hits. Never echo matched secret values."""
    keys = ("api_key", "secret", "token", "password", "BEGIN PRIVATE", "sk-")
    hits = []
    low = text.lower()
    for k in keys:
        if k.lower() in low:
            hits.append(k)
    return hits
