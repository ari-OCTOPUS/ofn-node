#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_sync_agent.py — LEG-SYNC orchestration + mutation-style checks.

Stdlib-only, deterministic, no real sends. Existing lead logic is exercised through the
adapter only when needed; happy path uses injected fakes so the absent studio_pf API does not
force a fabricated module_id. The real studio_pf adapter is separately asserted to block.
"""
from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent), str(_HERE.parent / "budget"),
           str(_HERE.parent / "legs"), str(_HERE.parent / "action_bridge")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402
ENV = harness.setup("sync-agent")

# Keep tests deterministic; sync(... deps={force: True}) bypasses this when needed.
os.environ.pop("OCTOPUS_WIRE_SYNC_AGENT", None)

import opslib  # noqa: E402
importlib.reload(opslib)
import sync_agent  # noqa: E402
importlib.reload(sync_agent)
import sync_cartographer  # noqa: E402
importlib.reload(sync_cartographer)
from sync_studio_pf_adapter import StudioPFAdapter  # noqa: E402


class FakeStudioReady:
    def __init__(self):
        self.calls = 0

    def buildModule(self, spec, trace_id, idempotency_key):  # noqa: N802
        self.calls += 1
        return {"ok": True, "state": "ready", "build_id": "build-1", "module_id": "module-1"}

    def getBuildStatus(self, build_id, trace_id):  # noqa: N802
        return {"ok": True, "state": "ready", "build_id": build_id, "module_id": "module-1"}


class FakeLeadMachine:
    def __init__(self):
        self.counts = {"AUTHORIZE": 0, "DRAFT": 0, "FIRST_REPLY": 0}

    def transition(self, run, event, key=None):
        typ = event.get("type")
        self.counts[typ] = self.counts.get(typ, 0) + 1
        state = run.get("lead", {}).get("state")
        if typ == "AUTHORIZE":
            if not event.get("approved"):
                return {"ok": False, "state": "rejected", "error": "AUTHORIZATION_REJECTED"}
            if not event.get("actor_id"):
                return {"ok": False, "state": "awaiting_authorization", "error": "ACTOR_ID_REQUIRED"}
            return {"ok": True, "state": "authorized", "authorization_id": "auth-1"}
        if typ == "DRAFT":
            if state != "authorized":
                return {"ok": False, "state": state, "error": "DRAFT_REQUIRES_AUTHORIZED"}
            if not event.get("module_id"):
                return {"ok": False, "state": state, "error": "MODULE_ID_REQUIRED"}
            return {"ok": True, "state": "draft_ready", "draft_id": "draft-1"}
        if typ == "FIRST_REPLY":
            if state != "draft_ready":
                return {"ok": False, "state": state, "error": "FIRST_REPLY_REQUIRES_DRAFT_READY"}
            if not event.get("draft_id"):
                return {"ok": False, "state": state, "error": "DRAFT_ID_REQUIRED"}
            return {"ok": True, "state": "first_reply_ready", "first_reply_id": "reply-1"}
        return {"ok": False, "state": state, "error": "UNKNOWN"}


def _run(coro):
    return asyncio.run(coro)


def _base_run():
    return {
        "input": {
            "request_id": "REQ-1",
            "user_goal": "Paint hallway and prepare first reply",
            "module_spec": {"name": "lead-sync-demo", "purpose": "sync test"},
            "lead_context": {"name": "Sarah", "expected_aud": 1200, "description": "Interior hallway painting"},
        }
    }


def _deps(studio=None, lead=None):
    return {"force": True, "studio": studio or FakeStudioReady(), "lead": lead or FakeLeadMachine()}


def t_a_flag_off_blocks_inert():
    r = _run(sync_agent.sync(_base_run()))
    assert r["status"]["state"] == "blocked", r["status"]
    assert r["status"].get("next_action", {}).get("type") in ("wait", "fix_input"), r["status"]
    assert any(e.get("code") == "SYNC_AGENT_FLAG_OFF" for e in r.get("errors", [])), r.get("errors")


def t_b_real_studio_pf_adapter_blocks_honestly():
    run = _base_run()
    r = _run(sync_agent.sync(run, deps={"force": True, "studio": StudioPFAdapter(), "lead": FakeLeadMachine()}))
    assert r["studio_pf"]["state"] == "blocked", r
    assert r["studio_pf"].get("error") == "STUDIO_NO_BUILD_API", r["studio_pf"]
    st = sync_cartographer.status(r)
    assert st["state"] == "blocked" and st["phase"] == "module_build", st
    assert st["next_action"]["type"] == "human_authorization", st
    assert not r["studio_pf"].get("module_id"), "honest adapter must not fabricate module_id"


def t_c_blocked_on_authorization_after_module_ready():
    r = _run(sync_agent.sync(_base_run(), deps=_deps()))
    assert r["studio_pf"]["state"] == "ready", r
    assert r["lead"]["state"] == "awaiting_authorization", r
    assert r["status"]["state"] == "blocked", r["status"]
    assert r["status"]["next_action"]["type"] == "human_authorization", r["status"]


def t_d_full_happy_path_resume_after_authorize_done():
    run = _run(sync_agent.sync(_base_run(), deps=_deps()))
    assert run["lead"]["state"] == "awaiting_authorization", run
    run = _run(sync_agent.sync(run, incoming={"type": "AUTHORIZE", "approved": True, "actor_id": "owner"},
                               deps=_deps()))
    assert run["lead"]["state"] == "first_reply_ready", run["lead"]
    assert run["lead"]["draft_id"] == "draft-1", run["lead"]
    assert run["lead"]["first_reply_id"] == "reply-1", run["lead"]
    assert run["status"]["state"] == "done", run["status"]
    assert run["status"]["progress"] == 100, run["status"]


def t_e_retry_without_duplicate_after_done():
    studio = FakeStudioReady()
    lead = FakeLeadMachine()
    run = _run(sync_agent.sync(_base_run(), deps=_deps(studio, lead)))
    run = _run(sync_agent.sync(run, incoming={"type": "AUTHORIZE", "approved": True, "actor_id": "owner"},
                               deps=_deps(studio, lead)))
    again = _run(sync_agent.sync(run, deps=_deps(studio, lead)))
    assert again["status"]["state"] == "done", again["status"]
    assert studio.calls == 1, studio.calls
    assert lead.counts["DRAFT"] == 1, lead.counts
    assert lead.counts["FIRST_REPLY"] == 1, lead.counts


def t_f_rejected_authorization_blocks_draft():
    run = _run(sync_agent.sync(_base_run(), deps=_deps()))
    run = _run(sync_agent.sync(run, incoming={"type": "AUTHORIZE", "approved": False, "actor_id": "owner"},
                               deps=_deps()))
    assert run["lead"]["state"] == "rejected", run["lead"]
    assert run["status"]["state"] == "blocked", run["status"]
    assert not run["lead"].get("draft_id"), run["lead"]


def _mutations():
    return [
        ("drop module_id", {"studio_pf": {"state": "ready"}, "lead": {"state": "authorized"}}, "blocked"),
        ("ok true plus error", {"errors": [{"phase": "module_build", "code": "STUDIO_OK_WITH_ERROR", "message": "bad", "recoverable": False}]}, "failed"),
        ("unknown lead state", {"lead": {"state": "complete"}}, "blocked"),
        ("done without first_reply_id", {"status": {"phase": "done", "progress": 100}, "lead": {"state": "draft_ready", "draft_id": "d"}}, "blocked"),
        ("progress 140", {"status": {"phase": "draft", "progress": 140}, "lead": {"state": "drafting"}}, "blocked"),
        ("draft before authorize", {"studio_pf": {"state": "ready", "module_id": "m"}, "lead": {"state": "draft_ready", "draft_id": "d"}}, "blocked"),
        ("first_reply before draft", {"studio_pf": {"state": "ready", "module_id": "m"}, "lead": {"state": "first_reply_ready", "first_reply_id": "r"}}, "blocked"),
        ("first_reply without module", {"studio_pf": {"state": "ready"}, "lead": {"state": "first_reply_ready", "authorization_id": "a", "draft_id": "d", "first_reply_id": "r"}}, "blocked"),
        ("first_reply without authorization", {"studio_pf": {"state": "ready", "module_id": "m"}, "lead": {"state": "first_reply_ready", "draft_id": "d", "first_reply_id": "r"}}, "blocked"),
        ("duplicate/invalid first_reply", {"lead": {"state": "first_reply_ready", "draft_id": "d"}}, "blocked"),
    ]


def t_g_mutation_harness_rejects_bad_states():
    failed = []
    for name, patch, expected in _mutations():
        run = sync_agent.ensure_ids(_base_run())
        # shallow recursive patch is enough for these SyncRun mutations.
        for k, v in patch.items():
            if isinstance(v, dict) and isinstance(run.get(k), dict):
                run[k].update(v)
            else:
                run[k] = v
        st = sync_cartographer.status(run)
        if st["state"] != expected:
            failed.append((name, expected, st))
    assert not failed, failed


def t_h_lead_machine_guards_order_before_delegating():
    lead = FakeLeadMachine()
    run = sync_agent.ensure_ids(_base_run())
    run["studio_pf"] = {"state": "ready", "module_id": "m"}
    run["lead"] = {"state": "not_started"}
    res = lead.transition(run, {"type": "DRAFT", "module_id": "m"}, "k")
    assert res["ok"] is False and res["error"] == "DRAFT_REQUIRES_AUTHORIZED", res
    run["lead"] = {"state": "authorized"}
    res2 = lead.transition(run, {"type": "FIRST_REPLY", "draft_id": "d"}, "k2")
    assert res2["ok"] is False and res2["error"] == "FIRST_REPLY_REQUIRES_DRAFT_READY", res2


def t_i_real_lead_machine_rejects_conflicting_authorize():
    from sync_lead_machine import LeadMachine
    run = sync_agent.ensure_ids(_base_run())
    run["lead"] = {"state": "authorized", "authorization_id": "auth-existing"}
    r = LeadMachine(lead_effect_gate=object()).transition(
        run, {"type": "AUTHORIZE", "approved": False, "actor_id": "owner"}, "k-conflict")
    assert r["ok"] is False and r["state"] == "authorized", r
    assert r["error"] == "AUTHORIZE_CONFLICT_AFTER_AUTHORIZED", r


def t_j_real_lead_machine_rejects_authorize_after_rejected():
    from sync_lead_machine import LeadMachine
    run = sync_agent.ensure_ids(_base_run())
    run["lead"] = {"state": "rejected"}
    r = LeadMachine(lead_effect_gate=object()).transition(
        run, {"type": "AUTHORIZE", "approved": True, "actor_id": "owner"}, "k-after-reject")
    assert r["ok"] is False and r["state"] == "rejected", r
    assert r["error"] == "LEAD_TERMINAL:rejected", r


CHECKS = [
    ("flag off blocks inert", t_a_flag_off_blocks_inert),
    ("real studio_pf adapter blocks honestly", t_b_real_studio_pf_adapter_blocks_honestly),
    ("blocked on authorization", t_c_blocked_on_authorization_after_module_ready),
    ("resume after authorize to done", t_d_full_happy_path_resume_after_authorize_done),
    ("retry without duplicate", t_e_retry_without_duplicate_after_done),
    ("rejected authorization blocks draft", t_f_rejected_authorization_blocks_draft),
    ("mutation harness rejects bad states", t_g_mutation_harness_rejects_bad_states),
    ("lead order guards", t_h_lead_machine_guards_order_before_delegating),
    ("real lead rejects conflicting authorize", t_i_real_lead_machine_rejects_conflicting_authorize),
    ("real lead rejects authorize after rejected", t_j_real_lead_machine_rejects_authorize_after_rejected),
]


if __name__ == "__main__":
    failed = harness.run(CHECKS)
    print(f"\n{'✅' if not failed else '❌'} test_sync_agent: {len(CHECKS) - failed}/{len(CHECKS)} passed")
    sys.exit(1 if failed else 0)
