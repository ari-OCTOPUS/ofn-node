#!/usr/bin/env python3
"""Prepare the existing self-goal as a canonical mission and Action Bridge plan.

This module does not install a caller. `prepare()` is read-only. `dry_run()` may write only under
unified_control/artifacts and never performs A2+ actions, network, spend or runtime-state writes.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

from . import compass as compass_mod
from . import contracts as uc_contracts
from . import link_graph, method_translator, snapshot

OPS = Path(__file__).resolve().parents[1]
ACTION = OPS / "action_bridge"
ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
SANDBOX = ARTIFACTS / "sandbox"
RECEIPTS = ARTIFACTS / "receipts"
LEDGER = ARTIFACTS / "action-ledger.jsonl"


def _action_modules():
    # action_bridge v1 deliberately uses sibling absolute imports.
    if str(ACTION) not in sys.path:
        sys.path.insert(0, str(ACTION))
    planner = importlib.import_module("planner")
    executor = importlib.import_module("executor")
    return planner, executor


def _mission_envelope(spec: dict, request: dict) -> dict:
    if str(OPS) not in sys.path:
        sys.path.insert(0, str(OPS))
    import mission_contract as mc
    mid = uc_contracts.stable_id("mis", spec["trace_id"], request["action_id"])
    return mc.make_envelope(
        source=spec["source"], target_leg=spec["target_leg"], owner=spec["owner"],
        action=spec["action"], risk=spec["risk"], intent=spec["intent"],
        payload=spec["payload"], mission_id=mid, trace_id=spec["trace_id"],
        task_id=request["action_id"], project_id="octopus-self-goal",
        status="needs_approval" if spec["risk"] != "low" else "queued")


def _prepare_snapshot(snap: dict, *, now: float | None = None) -> dict:
    comp = compass_mod.build(snap)
    trans = method_translator.translate(comp)
    if not trans.get("ok"):
        graph = link_graph.build(snap, comp)
        return {"ok": False, "status": "BLOCKED", "snapshot": snap,
                "compass": comp, "translation": trans, "graph": graph}
    req = trans["request"]
    mission = _mission_envelope(trans["mission"], req)
    planner, _ = _action_modules()
    prereg = (snap.get("goal_cycle") or {}).get("prereg") or {}

    def lookup(pid):
        return prereg if str(prereg.get("prereg_id")) == str(pid) else None

    plan = planner.plan(req, sandbox_root=OPS, prereg_lookup=lookup,
                        ledger={}, approval=None, used_nonces=set(),
                        now=float(now or snap.get("created_epoch") or 0.0))
    graph = link_graph.build(snap, comp, mission=mission)
    return {"ok": True, "status": "PREPARED_NOT_EXECUTED",
            "snapshot": snap, "compass": comp, "mission": mission,
            "request": req, "plan": plan, "graph": graph}


def prepare(*, now: float | None = None) -> dict:
    """Operator/offline view: read the current records from disk."""
    return _prepare_snapshot(snapshot.build(now=now), now=now)


def prepare_records(*, directions: list[str], prereg: dict, heart: dict,
                    cortex: dict | None = None, self_model_authority: str = "MISSING",
                    innervation: dict | None = None, owner_guidance: dict | None = None,
                    now: float | None = None) -> dict:
    """Runtime-safe seam: caller passes the exact frozen record; no latest-row guessing.

    This does not write. `heart` must already carry explicit authority and production_open.
    """
    snap = {
        "schema": "unified-control.snapshot.v1",
        "created_epoch": float(now or 0.0),
        "directions": list(directions or []),
        "self_model": {"authority": self_model_authority},
        "cortex": {"authority": "AUTHORITATIVE", "data": dict(cortex or {})},
        "heart": dict(heart or {}),
        "heartstate": {},
        "innervation": dict(innervation or {}),
        "work_plan": {},
        "goal_cycle": {"prereg": dict(prereg or {}), "journal": {}, "verdict": {},
                       "counts": {"prereg": 1 if prereg else 0, "cycles": 0, "verdicts": 0}},
        "owner_guidance": {"latest": dict(owner_guidance or {}) or None,
                           "count": 1 if owner_guidance else 0},
        "blockers": [], "fully_integrated": False,
    }
    return _prepare_snapshot(snap, now=now)


def dry_run(*, now: float | None = None, now_iso: str = "") -> dict:
    prepared = prepare(now=now)
    if not prepared.get("ok"):
        return prepared
    _, executor = _action_modules()
    result = executor.execute(
        prepared["request"], prepared["plan"], sandbox_root=OPS,
        receipts_dir=RECEIPTS, ledger_path=LEDGER, now_iso=now_iso,
        dry_run=True)
    receipt = result.get("receipt") or {}
    prepared["dry_run"] = result
    prepared["graph"] = link_graph.build(
        prepared["snapshot"], prepared["compass"],
        mission=prepared["mission"], action_receipt=receipt)
    prepared["status"] = "DRY_RUN_ONLY"
    return prepared
