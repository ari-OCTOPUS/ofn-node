# -*- coding: utf-8 -*-
"""OCTOPUS v3.0 P0 overlay — additive, default-OFF, stdlib-only.

This package does **not** replace NBB-CP, budget_gate, genome ledger, or
STOP-ORGANISM. It is a fail-closed INTENT gate for a future choke point.

WIRED is False until the owner votes to compose it into organism/wiring.
Never import this package from those WORKLOCK files without that vote.
"""
from __future__ import annotations

WIRED = False
VERSION = "3.0.0-p0"
P0_DATE = "2026-08-16"

from .exceptions import (
    BudgetExceeded,
    DualBeatDenied,
    KillEngaged,
    LedgerClosed,
    LedgerIntegrityError,
    LeaseError,
    PolicyDenied,
    TaintNetworkDenied,
)
from .gate import Action, P0ExecutionGate, Verdict
from .kill import KillState, KillSwitch
from .ledger import IntentLedger
from .lease import CapabilityLease, LeaseStore
from .taint import TaskTaintLatch
from .beat_lease import BeatOwnership, beat_allowed

__all__ = [
    "WIRED",
    "VERSION",
    "P0_DATE",
    "Action",
    "BeatOwnership",
    "BudgetExceeded",
    "DualBeatDenied",
    "beat_allowed",
    "CapabilityLease",
    "IntentLedger",
    "KillEngaged",
    "KillState",
    "KillSwitch",
    "LeaseError",
    "LeaseStore",
    "LedgerClosed",
    "LedgerIntegrityError",
    "P0ExecutionGate",
    "PolicyDenied",
    "TaskTaintLatch",
    "TaintNetworkDenied",
    "Verdict",
]
