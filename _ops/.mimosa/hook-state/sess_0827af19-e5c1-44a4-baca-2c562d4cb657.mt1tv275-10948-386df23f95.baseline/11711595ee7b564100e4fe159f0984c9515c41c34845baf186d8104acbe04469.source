#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sync_lead_machine.py — thin adapter over existing lead logic for LEG-SYNC.

This is intentionally not a second authorization state machine. It reads the current
SyncRun lead state, enforces the sync-layer order (AUTHORIZE → DRAFT → FIRST_REPLY), then
delegates to existing lead modules where available:
  * AUTHORIZE → lead_effect_gate.authorize(effect_id, lead_id, token)
  * DRAFT     → LeadLeg.intake(...) + lead_quote.create_quote(...)
  * FIRST_REPLY → lead_first_reply.compose_first_reply(record)

Tests can inject fake deps; production remains fail-soft/std-lib only. No customer send is
performed: existing lead_first_reply composes only, and quote creation is propose-only.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_BUDGET = _OPS / "budget"
for _p in (str(_OPS), str(_BUDGET), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import opslib  # noqa: E402
except Exception:  # noqa: BLE001
    opslib = None  # type: ignore


_LEAD_STATES_TERMINAL_DENY = {"rejected", "failed"}


def _now_iso() -> str:
    try:
        return opslib.now_iso() if opslib is not None else ""
    except Exception:  # noqa: BLE001
        return ""


def _s(v, default=""):
    return v if isinstance(v, str) else default


def _d(v):
    return v if isinstance(v, dict) else {}


def _consented_candidate(run: dict) -> dict:
    inp = _d(run.get("input"))
    lead_context = _d(inp.get("lead_context"))
    candidate = lead_context.get("candidate")
    if isinstance(candidate, dict):
        return candidate
    user_goal = _s(inp.get("user_goal"), "painting enquiry")
    return {
        "schema_version": "1.1",
        "source": {"channel": "website_form", "source_id": "sync_agent"},
        "candidate_type": "consented_inbound",
        "consent": {"basis": "explicit", "evidence": "sync_agent_test_or_owner_input"},
        "contact": {"name": _s(lead_context.get("name"), "Customer")},
        "property": {"suburb": _s(lead_context.get("suburb"), "")},
        "request": {"scope_text": user_goal},
        "description": user_goal,
        "lead_id": _s(inp.get("request_id"), _s(run.get("run_id"), "sync-lead")),
    }


def _make_default_lead_leg():
    try:
        from lead_leg import LeadLeg  # noqa: WPS433
        from leg import TaskPacket  # noqa: WPS433
        packet = TaskPacket(
            leg_id="lead",
            organ="PROJECT_F",
            read_allowlist=(),
            tools=("intake", "draft_quote"),
            budget_aud=0.0,
            spawn=0,
            secrets=(),
        )
        return LeadLeg(packet, organ_table={})
    except Exception:  # noqa: BLE001
        return None


class LeadMachine:
    """Dispatcher adapter; order is enforced by reading run['lead']['state']."""

    def __init__(self, *, lead_effect_gate=None, lead_leg=None, lead_quote=None,
                 lead_first_reply=None, config=None):
        self._gate = lead_effect_gate
        self._lead_leg = lead_leg
        self._lead_quote = lead_quote
        self._first_reply = lead_first_reply
        self._config = config or {
            "phone": "0400 000 111",
            "business_name": "Sync Test Painting Co",
            "owner_name": "Owner",
            "abn": "11 222 333 444",
        }

    def _leg_gate(self):
        if self._gate is not None:
            return self._gate
        import lead_effect_gate as leg_gate  # noqa: WPS433
        return leg_gate

    def _leg_quote(self):
        if self._lead_quote is not None:
            return self._lead_quote
        import lead_quote  # noqa: WPS433
        return lead_quote

    def _leg_first_reply(self):
        if self._first_reply is not None:
            return self._first_reply
        import lead_first_reply  # noqa: WPS433
        return lead_first_reply

    def _leg(self):
        return self._lead_leg if self._lead_leg is not None else _make_default_lead_leg()

    def transition(self, run: dict, event: dict, idempotency_key: str | None = None) -> dict:
        try:
            if not isinstance(run, dict) or not isinstance(event, dict):
                return {"ok": False, "state": "failed", "error": "BAD_RUN_OR_EVENT"}
            typ = _s(event.get("type")).upper()
            lead = _d(run.get("lead"))
            current = _s(lead.get("state"), "not_started")
            if current in _LEAD_STATES_TERMINAL_DENY:
                if typ == "AUTHORIZE" and current == "rejected" and event.get("approved") is False:
                    return {"ok": False, "state": "rejected", "error": _s(event.get("reason"), "AUTHORIZATION_REJECTED")}
                return {"ok": False, "state": current, "error": f"LEAD_TERMINAL:{current}"}
            if typ == "AUTHORIZE":
                return self._authorize(run, event, idempotency_key)
            if typ == "DRAFT":
                return self._draft(run, event, idempotency_key)
            if typ == "FIRST_REPLY":
                return self._first_reply_transition(run, event, idempotency_key)
            return {"ok": False, "state": current or "failed", "error": "UNKNOWN_LEAD_EVENT"}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "state": "failed", "error": f"exception:{type(exc).__name__}"}

    def _authorize(self, run: dict, event: dict, key: str | None) -> dict:
        lead = _d(run.get("lead"))
        current = _s(lead.get("state"), "not_started")
        actor = _s(event.get("actor_id"))
        if not actor:
            return {"ok": False, "state": "awaiting_authorization", "error": "ACTOR_ID_REQUIRED"}
        if current == "authorized" and lead.get("authorization_id"):
            if event.get("approved") is True:
                return {"ok": True, "state": "authorized", "authorization_id": lead.get("authorization_id")}
            return {"ok": False, "state": "authorized", "error": "AUTHORIZE_CONFLICT_AFTER_AUTHORIZED"}
        if event.get("approved") is not True:
            return {"ok": False, "state": "rejected", "error": _s(event.get("reason"), "AUTHORIZATION_REJECTED")}
        effect_id = _s(event.get("effect_id"), f"sync-effect-{_s(run.get('run_id'), 'run')}")
        lead_id = _s(event.get("lead_id"), _s(_d(run.get("input")).get("request_id"), _s(run.get("run_id"), "sync-lead")))
        token = _s(event.get("decision_token"), str(key or f"{_s(run.get('run_id'), 'run')}:authorize"))
        try:
            res = self._leg_gate().authorize(effect_id, lead_id, token)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "state": "failed", "error": f"AUTHORIZE_EXCEPTION:{type(exc).__name__}"}
        if not res.get("ok"):
            return {"ok": False, "state": "awaiting_authorization", "error": _s(res.get("reason"), "AUTHORIZE_FAILED")}
        return {
            "ok": True,
            "state": "authorized",
            "authorization_id": _s(res.get("effect_id"), effect_id),
            "effect_id": _s(res.get("effect_id"), effect_id),
        }

    def _draft(self, run: dict, event: dict, key: str | None) -> dict:
        lead = _d(run.get("lead"))
        current = _s(lead.get("state"), "not_started")
        if current != "authorized":
            return {"ok": False, "state": current, "error": "DRAFT_REQUIRES_AUTHORIZED"}
        module_id = _s(event.get("module_id"))
        if not module_id:
            return {"ok": False, "state": current, "error": "MODULE_ID_REQUIRED"}
        if lead.get("draft_id"):
            return {"ok": True, "state": "draft_ready", "draft_id": lead.get("draft_id")}
        leg = self._leg()
        if leg is None:
            return {"ok": False, "state": "failed", "error": "LEAD_LEG_UNAVAILABLE"}
        inp = _d(run.get("input"))
        ctx = _d(inp.get("lead_context"))
        name = _s(ctx.get("name"), _s(inp.get("request_id"), _s(run.get("run_id"), "sync lead")))
        description = _s(ctx.get("description"), _s(inp.get("user_goal"), "sync lead draft"))
        expected = ctx.get("expected_aud", 0.0)
        try:
            intake_res = leg.intake(name, expected, cell=_s(ctx.get("cell"), "lead.doer"), description=description)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "state": "failed", "error": f"LEAD_INTAKE_EXCEPTION:{type(exc).__name__}"}
        if not intake_res.get("ok") or not intake_res.get("attribution_id"):
            return {"ok": False, "state": "failed", "error": _s(intake_res.get("error"), "LEAD_INTAKE_FAILED")}
        candidate = _consented_candidate(run)
        candidate.setdefault("description", description)
        try:
            lq = self._leg_quote()
            quote_res = lq.create_quote(leg, intake_res["attribution_id"], lq.lead_to_intake(candidate, {}))
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "state": "failed", "error": f"LEAD_QUOTE_EXCEPTION:{type(exc).__name__}"}
        if not quote_res.get("ok"):
            return {"ok": False, "state": "failed", "error": _s(quote_res.get("error"), "LEAD_QUOTE_FAILED")}
        draft_id = _s(quote_res.get("proposal_id"), _s(quote_res.get("qt_number"), _s(intake_res.get("attribution_id"))))
        if not draft_id:
            return {"ok": False, "state": "failed", "error": "DRAFT_OK_WITHOUT_DRAFT_ID"}
        return {
            "ok": True,
            "state": "draft_ready",
            "draft_id": draft_id,
            "quote": quote_res,
            "module_id": module_id,
        }

    def _first_reply_transition(self, run: dict, event: dict, key: str | None) -> dict:
        lead = _d(run.get("lead"))
        current = _s(lead.get("state"), "not_started")
        if current != "draft_ready":
            return {"ok": False, "state": current, "error": "FIRST_REPLY_REQUIRES_DRAFT_READY"}
        draft_id = _s(event.get("draft_id"), _s(lead.get("draft_id")))
        if not draft_id:
            return {"ok": False, "state": current, "error": "DRAFT_ID_REQUIRED"}
        if lead.get("first_reply_id"):
            return {"ok": True, "state": "first_reply_ready", "first_reply_id": lead.get("first_reply_id")}
        candidate = _consented_candidate(run)
        candidate["lead_id"] = _s(candidate.get("lead_id"), _s(run.get("run_id"), "sync-lead"))
        prev_flag = os.environ.get("OCTOPUS_WIRE_LEAD_FIRST_REPLY")
        os.environ["OCTOPUS_WIRE_LEAD_FIRST_REPLY"] = "1"
        try:
            res = self._leg_first_reply().compose_first_reply(candidate, config=self._config)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "state": "failed", "error": f"FIRST_REPLY_EXCEPTION:{type(exc).__name__}"}
        finally:
            if prev_flag is None:
                os.environ.pop("OCTOPUS_WIRE_LEAD_FIRST_REPLY", None)
            else:
                os.environ["OCTOPUS_WIRE_LEAD_FIRST_REPLY"] = prev_flag
        if not res.get("ok"):
            return {"ok": False, "state": "blocked", "error": _s(res.get("reason"), "FIRST_REPLY_BLOCKED")}
        first_reply_id = f"first-reply:{draft_id}"
        return {
            "ok": True,
            "state": "first_reply_ready",
            "first_reply_id": first_reply_id,
            "first_reply": res,
        }


if __name__ == "__main__":
    import json
    print(json.dumps({"ok": True, "adapter": "LeadMachine", "now": _now_iso()}, ensure_ascii=False))
