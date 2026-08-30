#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sync_agent.py — LEG-SYNC orchestration layer.

Additive, stdlib-only, fail-soft sync layer that wires three black-box surfaces:
  * studio_pf       → honest adapter; no build API exists, so it blocks visibly.
  * cartographer    → pure SyncRun → SyncStatus mapper in legs/sync_cartographer.py.
  * lead            → thin adapter over existing lead modules; no second state machine.

SyncRun shape (plain dict by convention):
  run_id, trace_id, created_at, updated_at, input{},
  studio_pf{state, build_id?, module_id?, error?},
  lead{state, authorization_id?, draft_id?, first_reply_id?, error?},
  status{phase, progress, message}, events[], errors[].

The orchestrator is a resumable step function: each call advances until the first wait,
blocked state, failure, or done. Every side-effect operation uses the megaprompt's exact
idempotency keys:
  ${run_id}:studio_build, ${run_id}:authorize, ${run_id}:draft, ${run_id}:first_reply.

Flag: OCTOPUS_WIRE_SYNC_AGENT (default OFF). Halt checks precede the flag. No live module
is rewritten and no studio_pf module_id is fabricated.
"""
from __future__ import annotations

import inspect
import json
import os
import secrets
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "legs"), str(_HERE / "action_bridge")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import opslib  # noqa: E402
except Exception:  # noqa: BLE001
    opslib = None  # type: ignore

try:
    import idempotency as _idem  # noqa: E402
except Exception:  # noqa: BLE001
    _idem = None  # type: ignore

from sync_cartographer import status as _status  # noqa: E402
from sync_studio_pf_adapter import StudioPFAdapter  # noqa: E402
from sync_lead_machine import LeadMachine  # noqa: E402

FLAG = "OCTOPUS_WIRE_SYNC_AGENT"

_STUDIO_STATES = {"not_started", "queued", "building", "ready", "failed", "blocked"}
_LEAD_STATES = {
    "not_started", "awaiting_authorization", "authorized", "drafting", "draft_ready",
    "awaiting_first_reply", "first_reply_ready", "rejected", "failed", "blocked",
}


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def _now_iso() -> str:
    try:
        return opslib.now_iso() if opslib is not None else ""
    except Exception:  # noqa: BLE001
        return ""


def _ledger_path() -> Path:
    base = opslib.STATE_DIR if opslib is not None else (_HERE / "state")
    return Path(base) / "sync-agent" / "ledger.json"


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text("utf-8")) if path.exists() else {}
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _write_json(path: Path, data: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if opslib is not None and hasattr(opslib, "LockedJson"):
            with opslib.LockedJson(path) as lj:
                lj.write(data)
            return
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True), "utf-8")
        os.replace(tmp, path)
    except Exception:  # noqa: BLE001 — fail-soft; next retry may redo but adapters still fail-closed.
        pass


def _halt_reason() -> str | None:
    try:
        if opslib is None:
            return None
        if hasattr(opslib, "master_halted"):
            r = opslib.master_halted()
            if r:
                return str(r)
        if hasattr(opslib, "halted"):
            r = opslib.halted()
            if r:
                return str(r)
        if getattr(opslib, "STOP_ORGANISM", None) and opslib.STOP_ORGANISM.exists():
            return "STOP-ORGANISM"
        if hasattr(opslib, "frozen") and opslib.frozen():
            return "FREEZE"
    except Exception as exc:  # noqa: BLE001
        return f"halt_probe_error:{type(exc).__name__}"
    return None


def ensure_ids(run: dict | None) -> dict:
    if not isinstance(run, dict):
        run = {}
    now = _now_iso()
    run.setdefault("run_id", "sync-" + secrets.token_hex(8))
    run.setdefault("trace_id", "trace-" + secrets.token_hex(8))
    run.setdefault("created_at", now)
    run["updated_at"] = now
    run.setdefault("input", {})
    run.setdefault("studio_pf", {})
    run["studio_pf"].setdefault("state", "not_started")
    run.setdefault("lead", {})
    run["lead"].setdefault("state", "not_started")
    run.setdefault("status", {"phase": "init", "progress": 0, "message": "initialized"})
    run.setdefault("events", [])
    run.setdefault("errors", [])
    return run


def emit(run: dict, source: str, event_type: str, payload: dict | None = None) -> None:
    try:
        run.setdefault("events", []).append({
            "at": _now_iso(),
            "source": str(source),
            "type": str(event_type),
            "payload": dict(payload or {}),
        })
    except Exception:  # noqa: BLE001
        pass


def _add_error(run: dict, phase: str, code: str, message: str, recoverable: bool = True) -> None:
    try:
        errors = run.setdefault("errors", [])
        sig = (phase, code, message)
        for e in errors:
            if isinstance(e, dict) and (e.get("phase"), e.get("code"), e.get("message")) == sig:
                return
        errors.append({
            "at": _now_iso(),
            "phase": phase,
            "code": code,
            "message": message,
            "recoverable": bool(recoverable),
        })
    except Exception:  # noqa: BLE001
        pass


def mark_failed(run: dict, phase: str, code: str, message: str | None = None) -> None:
    _add_error(run, phase, code, message or code, False)
    run["status"] = {"phase": "failed", "progress": min(int(run.get("status", {}).get("progress", 0) or 0), 95),
                     "message": message or code}


def mark_blocked(run: dict, phase: str, code: str, message: str | None = None) -> None:
    _add_error(run, phase, code, message or code, True)
    run["status"] = {"phase": phase if phase else "blocked",
                     "progress": min(int(run.get("status", {}).get("progress", 0) or 0), 95),
                     "message": message or code}


def mark_done(run: dict) -> None:
    run["status"] = {"phase": "done", "progress": 100, "message": "done"}


def update_status(run: dict, status: dict | None = None) -> dict:
    try:
        st = status if isinstance(status, dict) else _status(run)
        run["status"] = {
            "phase": st.get("phase"),
            "progress": st.get("progress"),
            "message": st.get("message"),
            "state": st.get("state"),
            "next_action": st.get("next_action"),
            "artifacts": st.get("artifacts", {}),
        }
        if st.get("errors"):
            # Keep public errors visible in status; run.errors remains append-only above.
            run["status"]["errors"] = st.get("errors")
        run["updated_at"] = _now_iso()
        return st
    except Exception as exc:  # noqa: BLE001
        run["status"] = {"phase": "blocked", "progress": 0,
                         "message": f"status update failed: {type(exc).__name__}",
                         "state": "blocked"}
        return run["status"]


def _module_spec(run: dict) -> dict:
    inp = run.get("input") if isinstance(run.get("input"), dict) else {}
    spec = inp.get("module_spec") if isinstance(inp.get("module_spec"), dict) else {}
    return {
        "name": str(spec.get("name") or inp.get("request_id") or run.get("run_id") or "sync-module"),
        "purpose": str(spec.get("purpose") or inp.get("user_goal") or "LEG-SYNC module"),
        **spec,
    }


def _action_request(action_id: str, action_type: str, target: str, payload: dict) -> dict:
    return {
        "action_id": action_id,
        "action_type": action_type,
        "target": target,
        "allowed_scope": ["sync_agent", target],
        "external_effect": False,
        "estimated_cost": 0.0,
        "prereg_id": "LEG-SYNC-2026-08-02",
        "payload": payload,
    }


def _idempotent(action_id: str, action_type: str, target: str, payload: dict, fn):
    ledger_path = _ledger_path()
    ledger = _read_json(ledger_path)
    req = _action_request(action_id, action_type, target, payload)
    if _idem is None:
        # Local conservative fallback: exact action_id duplicate only.
        key = action_id + ":fallback"
        if key in ledger:
            return ledger[key].get("result")
        result = fn()
        ledger[key] = {"at": _now_iso(), "result": result}
        _write_json(ledger_path, ledger)
        return result
    chk = _idem.check(req, ledger)
    if chk.get("state") == "DUPLICATE":
        prev = chk.get("previous") if isinstance(chk.get("previous"), dict) else {}
        return prev.get("result", {"ok": False, "state": "blocked", "error": "IDEMPOTENCY_PREVIOUS_MISSING"})
    if chk.get("state") == "CONFLICT":
        return {"ok": False, "state": "failed", "error": "IDEMPOTENCY_CONFLICT", "reason": chk.get("reason")}
    result = fn()
    _idem.remember(chk.get("key"), {"at": _now_iso(), "result": result}, ledger)
    _write_json(ledger_path, ledger)
    return result


async def _maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value


def apply_studio_build_result(run: dict, result: dict) -> None:
    studio = run.setdefault("studio_pf", {})
    if not isinstance(result, dict):
        studio["state"] = "failed"
        studio["error"] = "STUDIO_EMPTY_RESPONSE"
        mark_failed(run, "module_build", "STUDIO_EMPTY_RESPONSE")
        return
    if result.get("ok") is True and result.get("error"):
        studio["state"] = "failed"
        studio["error"] = "STUDIO_OK_WITH_ERROR"
        mark_failed(run, "module_build", "STUDIO_OK_WITH_ERROR")
        return
    state = str(result.get("state") or ("ready" if result.get("ok") else "failed"))
    if state not in _STUDIO_STATES:
        studio["state"] = "failed"
        studio["error"] = "UNKNOWN_STUDIO_STATE"
        mark_failed(run, "module_build", "UNKNOWN_STUDIO_STATE", f"Unknown studio_pf state: {state}")
        return
    if state == "queued":
        state = "building"
    studio["state"] = state
    for k in ("build_id", "module_id", "error", "message", "next_action"):
        if k in result and result.get(k) is not None:
            studio[k] = result.get(k)
    if state == "blocked":
        mark_blocked(run, "module_build", str(result.get("error") or "STUDIO_BLOCKED"),
                     str(result.get("message") or result.get("error") or "studio_pf blocked"))
    elif state == "failed":
        mark_failed(run, "module_build", str(result.get("error") or "STUDIO_BUILD_FAILED"))
    elif state == "building":
        run["status"] = {"phase": "module_build", "progress": 20,
                         "message": "studio_pf build is in progress"}
    elif state == "ready":
        run["status"] = {"phase": "module_build", "progress": 35,
                         "message": "studio_pf module is ready"}


def apply_lead_result(run: dict, result: dict) -> None:
    lead = run.setdefault("lead", {})
    if not isinstance(result, dict):
        lead["state"] = "failed"
        lead["error"] = "LEAD_EMPTY_RESPONSE"
        mark_failed(run, "lead", "LEAD_EMPTY_RESPONSE")
        return
    state = str(result.get("state") or lead.get("state") or "failed")
    if state not in _LEAD_STATES:
        lead["state"] = "failed"
        lead["error"] = "UNKNOWN_LEAD_STATE"
        mark_failed(run, "lead", "UNKNOWN_LEAD_STATE", f"Unknown lead state: {state}")
        return
    lead["state"] = state
    for k in ("authorization_id", "effect_id", "draft_id", "first_reply_id", "error", "first_reply", "quote"):
        if k in result and result.get(k) is not None:
            lead[k] = result.get(k)
    if not result.get("ok"):
        code = str(result.get("error") or "LEAD_TRANSITION_FAILED")
        if state in ("failed",):
            mark_failed(run, "lead", code)
        else:
            mark_blocked(run, "lead", code)
    elif state == "authorized":
        run["status"] = {"phase": "authorization", "progress": 50, "message": "lead authorized"}
    elif state == "draft_ready":
        run["status"] = {"phase": "draft", "progress": 75, "message": "draft ready"}
    elif state == "first_reply_ready":
        run["status"] = {"phase": "first_reply", "progress": 95, "message": "first reply ready"}


def _incoming_key(run: dict, incoming: dict) -> str:
    typ = str((incoming or {}).get("type") or "").upper()
    if typ == "AUTHORIZE":
        return f"{run['run_id']}:authorize"
    if typ == "DRAFT":
        return f"{run['run_id']}:draft"
    return f"{run['run_id']}:first_reply"


def _default_deps(run: dict) -> dict:
    return {
        "studio": StudioPFAdapter(event_sink=lambda e: run.setdefault("events", []).append(e)),
        "lead": LeadMachine(),
        "cartographer": _status,
        "force": False,
    }


async def sync(run, incoming=None, deps: dict | None = None) -> dict:
    """Advance a SyncRun until wait/block/fail/done. Never raises across the boundary."""
    run = ensure_ids(run)
    deps2 = _default_deps(run)
    if isinstance(deps, dict):
        deps2.update(deps)
    cartographer = deps2.get("cartographer") or _status
    try:
        emit(run, "sync_agent", "SYNC_STARTED")
        halt = _halt_reason()
        if halt:
            mark_blocked(run, "init", "HALTED", f"sync halted: {halt}")
            update_status(run, cartographer(run))
            return run
        if not enabled() and not deps2.get("force"):
            mark_blocked(run, "init", "SYNC_AGENT_FLAG_OFF", f"{FLAG}=0")
            update_status(run, cartographer(run))
            return run

        lead_machine = deps2["lead"]
        studio = deps2["studio"]

        # 0. External human event, usually AUTHORIZE.
        if incoming:
            key = _incoming_key(run, incoming)
            async def _transition():  # not used as coroutine; local wrapper documents boundary.
                return lead_machine.transition(run, incoming, key)
            lead_result = _idempotent(
                key, "lead_transition", "lead",
                {"event": incoming, "lead_state": run.get("lead", {}).get("state")},
                lambda: lead_machine.transition(run, incoming, key),
            )
            lead_result = await _maybe_await(lead_result)
            apply_lead_result(run, lead_result)
            if not lead_result.get("ok"):
                update_status(run, cartographer(run))
                return run

        # 1. Build / track studio module.
        studio_state = run.get("studio_pf", {}).get("state")
        if studio_state == "not_started":
            key = f"{run['run_id']}:studio_build"
            spec = _module_spec(run)
            build = _idempotent(
                key, "studio_build", "studio_pf",
                {"spec": spec},
                lambda: studio.buildModule(spec, run["trace_id"], key),
            )
            build = await _maybe_await(build)
            apply_studio_build_result(run, build)
            studio_state = run.get("studio_pf", {}).get("state")

        if studio_state == "building" and run.get("studio_pf", {}).get("build_id"):
            build = await _maybe_await(studio.getBuildStatus(run["studio_pf"]["build_id"], run["trace_id"]))
            apply_studio_build_result(run, build)
            studio_state = run.get("studio_pf", {}).get("state")

        if studio_state == "failed":
            mark_failed(run, "module_build", "STUDIO_BUILD_FAILED", run.get("studio_pf", {}).get("error"))
            update_status(run, cartographer(run))
            return run
        if studio_state == "blocked":
            update_status(run, cartographer(run))
            return run
        if studio_state != "ready":
            update_status(run, cartographer(run))
            return run
        if not run.get("studio_pf", {}).get("module_id"):
            mark_blocked(run, "module_build", "MODULE_READY_WITHOUT_MODULE_ID")
            update_status(run, cartographer(run))
            return run

        # 2. Authorization gate.
        lead_state = run.get("lead", {}).get("state")
        if lead_state == "not_started":
            run["lead"]["state"] = "awaiting_authorization"
            emit(run, "lead", "AUTHORIZATION_REQUIRED", {"module_id": run["studio_pf"].get("module_id")})
            update_status(run, cartographer(run))
            return run
        if lead_state == "awaiting_authorization":
            update_status(run, cartographer(run))
            return run
        if lead_state == "rejected":
            mark_blocked(run, "authorization", "AUTHORIZATION_REJECTED")
            update_status(run, cartographer(run))
            return run
        if lead_state == "failed":
            mark_failed(run, "lead", "LEAD_FAILED", run.get("lead", {}).get("error"))
            update_status(run, cartographer(run))
            return run

        # 3. Draft.
        if run["lead"].get("state") == "authorized":
            key = f"{run['run_id']}:draft"
            event = {
                "type": "DRAFT",
                "module_id": run["studio_pf"]["module_id"],
                "context": run.get("input", {}).get("lead_context", {}),
            }
            draft = _idempotent(
                key, "lead_draft", "lead",
                {"event": event, "authorization_id": run["lead"].get("authorization_id")},
                lambda: lead_machine.transition(run, event, key),
            )
            draft = await _maybe_await(draft)
            apply_lead_result(run, draft)

        if run["lead"].get("state") in ("failed", "blocked"):
            update_status(run, cartographer(run))
            return run
        if run["lead"].get("state") != "draft_ready":
            update_status(run, cartographer(run))
            return run
        if not run["lead"].get("draft_id"):
            mark_blocked(run, "draft", "DRAFT_READY_WITHOUT_DRAFT_ID")
            update_status(run, cartographer(run))
            return run

        # 4. First reply.
        if run["lead"].get("state") == "draft_ready":
            key = f"{run['run_id']}:first_reply"
            event = {"type": "FIRST_REPLY", "draft_id": run["lead"]["draft_id"], "channel": "default"}
            first_reply = _idempotent(
                key, "lead_first_reply", "lead",
                {"event": event, "draft_id": run["lead"].get("draft_id")},
                lambda: lead_machine.transition(run, event, key),
            )
            first_reply = await _maybe_await(first_reply)
            apply_lead_result(run, first_reply)

        if run["lead"].get("state") == "first_reply_ready":
            if not run["lead"].get("first_reply_id"):
                mark_blocked(run, "first_reply", "FIRST_REPLY_READY_WITHOUT_ID")
            else:
                mark_done(run)
        update_status(run, cartographer(run))
        return run
    except Exception as exc:  # noqa: BLE001
        mark_failed(run, "sync", "SYNC_EXCEPTION", f"sync exception: {type(exc).__name__}")
        update_status(run, cartographer(run))
        return run


def sync_agent_status() -> dict:
    """Zero-arg heartbeat for capability_registry auto-discovery."""
    return {
        "ok": True,
        "component": "sync_agent",
        "flag": FLAG,
        "enabled": enabled(),
        "default_mode": "inert-until-flag-on",
        "contracts": ["studio_pf.blocked_adapter", "cartographer.status", "lead.thin_adapter"],
        "ledger": str(_ledger_path()),
    }


def card() -> str:
    st = sync_agent_status()
    return ("LEG-SYNC sync_agent — "
            f"enabled={st['enabled']} · studio_pf=honest-blocked · "
            "lead=thin-adapter · cartographer=pure-status")


if __name__ == "__main__":
    import asyncio
    print(json.dumps(sync_agent_status(), ensure_ascii=False, indent=2))
    demo = {"input": {"user_goal": "demo sync"}}
    print(json.dumps(asyncio.run(sync(demo, deps={"force": True})), ensure_ascii=False, indent=2))
