#!/usr/bin/env python3
"""Deterministic goal candidate -> canonical mission envelope + action-request.v1.

Classification comes from the candidate key and a reviewed table, never from free method text.
The text is retained only as intent/evidence. Unknown candidate = blocked.
"""
from __future__ import annotations

import sys
from pathlib import Path

from . import contracts

OPS = Path(__file__).resolve().parents[1]
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

# Reviewed semantic mapping. No LLM participates.
MAP = {
    "money-claimed": {
        "action_type": "owner_action_card",
        "target": "owner:qualified-lead-review",
        "expected_effect": "مالک یک لید واقعیِ واجد شرایط را برای claim بررسی می‌کند؛ هیچ claim خودکار ساخته نمی‌شود",
        "allowed_scope": ["owner-cards"],
        "external_effect": False,
        "estimated_cost": 0,
        "rollback": "کارت منقضی/رد می‌شود؛ metric و attribution خودکار تغییر نمی‌کنند",
        "falsifier": "هیچ لید تحویل‌شده با مبلغ مثبت و شاهد مستقل وجود نداشته باشد",
        "risk": "medium",
        "target_leg": "lead",
        "mission_action": "request_qualified_lead_review",
    },
    "recall-events": {
        "action_type": "observe_metric",
        "target": "state/neural/recall-trend.jsonl",
        "expected_effect": "روند بازیابی فقط‌خواندنی مشاهده و برای ارزیاب ثبت می‌شود",
        "allowed_scope": ["state/neural"],
        "external_effect": False,
        "estimated_cost": 0,
        "rollback": "read-only؛ rollback لازم نیست",
        "falsifier": "رخداد بازیابی یا بهبود روند مشاهده نشود",
        "risk": "low",
        "target_leg": "knowledge",
        "mission_action": "observe_recall_trend",
    },
    "tool-precision": {
        "action_type": "observe_metric",
        "target": "state/telegram/tool-requests.jsonl",
        "expected_effect": "دقت درخواست ابزار از دفتر موجود اندازه‌گیری می‌شود",
        "allowed_scope": ["state/telegram"],
        "external_effect": False,
        "estimated_cost": 0,
        "rollback": "read-only؛ rollback لازم نیست",
        "falsifier": "نسبت precise افزایش نیابد یا دفتر ناخوانا باشد",
        "risk": "low",
        "target_leg": "knowledge",
        "mission_action": "observe_tool_request_precision",
    },
}


def translate(compass: dict) -> dict:
    candidate = str(compass.get("candidate_key") or "")
    cfg = MAP.get(candidate)
    if cfg is None:
        return {"ok": False, "reason": f"unmapped-candidate:{candidate or '<empty>'}"}
    prereg_id = str(compass.get("prereg_id") or "")
    goal_key = str(compass.get("goal_key") or "")
    if not prereg_id or not goal_key:
        return {"ok": False, "reason": "missing-frozen-goal-identity"}
    action_id = contracts.stable_id("act", prereg_id, candidate, cfg["mission_action"])
    req = {
        "schema": contracts.ACTION_REQUEST_SCHEMA,
        "action_id": action_id,
        "goal_id": goal_key,
        "prereg_id": prereg_id,
        "source_component": "unified_control.method_translator",
        "intent": str(compass.get("method") or "")[:400],
        "action_type": cfg["action_type"],
        "target": cfg["target"],
        "expected_effect": cfg["expected_effect"],
        "metric": dict(compass.get("metric") or {}),
        "allowed_scope": list(cfg["allowed_scope"]),
        "forbidden_actions": ["fabricate_claim", "external_send", "spend", "merge",
                              "deploy", "restart", "arm_flag", "edit_evaluator"],
        "required_capabilities": [],
        "external_effect": cfg["external_effect"],
        "estimated_cost": cfg["estimated_cost"],
        "privacy_class": "internal",
        "deadline": "from-prereg",
        "rollback": cfg["rollback"],
        "falsifier": cfg["falsifier"],
        "classification_hint": None,
    }
    v = contracts.validate_action_request(req)
    if not v["ok"]:
        return {"ok": False, "reason": "invalid-action-request", "errors": v["errors"]}
    return {"ok": True, "request": req, "mission": {
        "source": "self-goal",
        "target_leg": cfg["target_leg"],
        "owner": "octopus_core",
        "action": cfg["mission_action"],
        "risk": cfg["risk"],
        "intent": str(compass.get("goal") or "")[:400],
        "payload": {"prereg_id": prereg_id, "action_id": action_id},
        "trace_id": contracts.stable_id("trace", prereg_id, action_id),
    }}
