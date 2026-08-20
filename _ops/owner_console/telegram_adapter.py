#!/usr/bin/env python3
"""Pure seam for telegram_center after input_surface_policy has authorized Outer DM.

A10: LocalCommandResult is the only local return. String coercion lives in
exactly one boundary (_as_reply_dict) and emits LEGACY_LOCAL_RESULT_COERCED.
Local exceptions never fall through to a model.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from . import conversation
from .local_commands import (
    HANDLER_SCHEMA_VERSION, LocalCommandResult, handle_local, is_local_firewall,
    stopped, try_recall,
)

CANONICAL_OWNER_BOT_ID = 7992324219
APPROVAL_BOT_ID = 8187434784
ZIMAN_BOT_ID = 8861821707
_OPS = Path(__file__).resolve().parents[1]
# Unit 4 (2026-08-21): env-override state (همان الگوی tg_api) تا تست‌های
# ایزوله به temp بنویسند، نه به درخت زنده.
_STATE_BASE = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
_COERCE_LOG = (Path(_STATE_BASE) if _STATE_BASE else (_OPS / "state")) / "telegram" / "legacy-coerce.jsonl"
LEGACY_COERCE_COUNT = 0


def _collab_armed() -> bool:
    return os.environ.get("OCTOPUS_WIRE_COLLAB", "0") == "1"


def _log_legacy_coerce(kind: str) -> None:
    global LEGACY_COERCE_COUNT
    LEGACY_COERCE_COUNT += 1
    try:
        _COERCE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _COERCE_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "LEGACY_LOCAL_RESULT_COERCED",
                                "kind": kind, "n": LEGACY_COERCE_COUNT},
                               ensure_ascii=False) + "\n")
    except OSError:
        pass


def _as_reply_dict(reply, *, kind: str = "local-command") -> dict | None:
    """Single compatibility boundary. Typed results go through as_dict()."""
    if reply is None:
        return None
    if isinstance(reply, LocalCommandResult):
        return reply.as_dict()
    if isinstance(reply, str):
        _log_legacy_coerce("str")
        return {"kind": kind, "text": reply, "keyboard": None, "executable": False,
                "model_allowed": False, "legacy_coerced": True,
                "handler_schema_version": HANDLER_SCHEMA_VERSION}
    if isinstance(reply, dict):
        out = dict(reply)
        out.setdefault("kind", kind)
        out.setdefault("keyboard", None)
        out.setdefault("executable", False)
        out.setdefault("handler_schema_version", HANDLER_SCHEMA_VERSION)
        if "text" not in out and out.get("data"):
            out["text"] = str((out.get("data") or {}).get("text") or out.get("kind") or "")
        return out
    _log_legacy_coerce(type(reply).__name__)
    return {"kind": kind, "text": str(reply), "keyboard": None, "executable": False,
            "model_allowed": False, "legacy_coerced": True}


def handle_message(text: str, *, surface_decision: dict, model_fn=None) -> dict:
    d = dict(surface_decision or {})
    if not (d.get("allow") is True and d.get("mode") == "core_conversation"):
        return {"handled": False, "reason": "not-authorized-outer-core-conversation",
                "reply": None}
    _emit_owner_inbound(d, text)
    raw = str(text or "")
    first = raw.lstrip().split()[0].split("@")[0].lower() if raw.strip() else ""
    if stopped() and first not in ("/resume", "/status", "/health", "/help", "/stop"):
        return {"handled": True, "reason": "owner-stopped",
                "reply": _ok_local("توقف فعال است. /resume یا /status.", kind="local-stop")}
    if is_local_firewall(raw):
        result = handle_local(text, model_fn=model_fn)
        return {"handled": True, "reason": "local-command" if result.kind != "LOCAL_COMMAND_ERROR"
                else "LOCAL_COMMAND_ERROR",
                "reply": result.as_dict(),
                "handler_schema_version": HANDLER_SCHEMA_VERSION}
    recalled = try_recall(text)
    if recalled:
        _hear_brains(d, text, kind="owner.recall")
        return {"handled": True, "reason": "local-recall",
                "reply": recalled.as_dict(),
                "handler_schema_version": HANDLER_SCHEMA_VERSION}
    brains = _hear_brains(d, text, kind="owner.free_text")
    hcwm = _hc_wm_effect(text)
    # A15/A16: until live attribution is proven, stay local-degraded.
    if os.environ.get("OCTOPUS_PAID_COGNITION", "0") != "1":
        extra = ""
        if hcwm.get("label") == "HC_WM_DECORATIVE_PATH":
            extra = "\n(HC/WM در این turn اثر علّی جدا نشان نداد.)"
        n = int(brains.get("brains_receive_cognition_inbox") or 0)
        return {"handled": True, "reason": "local-degraded-paid-paused",
                "reply": _ok_local(
                    f"[DEGRADED_LOCAL_ONLY] مغزها پیام را شنیدند (n={n}، advisory، "
                    "executable=false). مدل پولی تا گیت A13 خاموش است. "
                    "/status · /remember"
                    + extra,
                    kind="local-degraded"),
                "hc_wm": hcwm, "brains": brains,
                "handler_schema_version": HANDLER_SCHEMA_VERSION}
    if model_fn is not None:
        model_fn({"text": text})
    if _collab_armed():
        from . import collaborator
        return {"handled": True, "reason": "collaborator",
                "reply": _as_reply_dict(collaborator.handle(text), kind="collaborator")}
    return {"handled": True, "reason": "owner-console",
            "reply": _as_reply_dict(conversation.handle(text), kind="owner-console")}


def _ok_local(text: str, *, kind: str) -> dict:
    return LocalCommandResult(handled=True, kind=kind, text=text).as_dict()


def handle_callback(data: str, *, surface_decision: dict) -> dict:
    d = dict(surface_decision or {})
    if not (d.get("allow") is True and d.get("mode") == "core_conversation"):
        return {"handled": False, "reason": "not-authorized-outer-core-conversation",
                "reply": None}
    if not str(data or "").startswith("oc:"):
        return {"handled": False, "reason": "not-owner-console-callback", "reply": None}
    if _collab_armed():
        from . import collaborator
        return {"handled": True, "reason": "collaborator",
                "reply": _as_reply_dict(collaborator.callback(data), kind="collaborator")}
    return {"handled": True, "reason": "owner-console",
            "reply": _as_reply_dict(conversation.callback(data), kind="owner-console")}


def _bot_id() -> int:
    return CANONICAL_OWNER_BOT_ID


def _hear_brains(decision: dict, text: str, *, kind: str) -> dict:
    try:
        import hashlib
        import sys
        ops = str(_OPS)
        if ops not in sys.path:
            sys.path.insert(0, ops)
        from organs.cognition_inbox import append_event, brains_hear  # noqa: WPS433
        ev = {
            "event_id": f"tg-{decision.get('update_id') or 'na'}",
            "kind": kind,
            "input_event_id": decision.get("update_id"),
            "n_chars": len(text or ""),
            "executable": False,
        }
        append_event(ev)
        pack = brains_hear([ev])
        a5 = []
        for r in pack.get("receipts") or []:
            blob = json.dumps(r, sort_keys=True, default=str).encode("utf-8")
            st = str(r.get("status") or "")
            ok = bool(r.get("heard")) and st.lower() not in (
                "brain_degraded", "degraded", "timeout")
            a5.append({
                "brain": r.get("brain"),
                "heard": bool(r.get("heard")),
                "input_event_id": ev.get("event_id"),
                "memory_ids": list(r.get("memory_ids") or []),
                "evidence_ids": list(r.get("evidence_ids") or []),
                "output_hash": hashlib.sha256(blob).hexdigest()[:16],
                "status": "OK" if ok else (
                    "TIMEOUT" if st.lower() == "timeout" else "DEGRADED"),
                "executable": False,
            })
        pack["a5_receipts"] = a5
        pack["synthesis_has_evidence"] = any(x.get("evidence_ids") for x in a5)
        return pack
    except Exception:  # noqa: BLE001
        return {"brains_receive_cognition_inbox": 0, "status": "BRAIN_DEGRADED",
                "executable": False, "a5_receipts": []}


def _readj(path: Path) -> dict:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _plan_pipeline(text: str, *, hcwm: bool, memory_ids: list[str]) -> dict:
    """A17: two planners, zero extra model calls."""
    if not hcwm:
        return {
            "context_ids": list(memory_ids),
            "uncertainty": None,
            "gate_mode": "memory-only",
            "token_budget": 256,
            "risk_reasons": [],
            "route": "local-memory",
        }
    hc = _readj(_OPS / "state" / "pulse" / "heartstate-latest.json")
    lc = _readj(_OPS / "state" / "pulse" / "life-currency-latest.json")
    wm = _readj(_OPS / "state" / "cortex" / "business-brain-latest.json")
    gate = _readj(_OPS / "state" / "pulse" / "arbiter-latest.json")
    color = (lc.get("color") or gate.get("color") or gate.get("state")
             or hc.get("color") or "UNKNOWN")
    uncertainty = (gate.get("uncertainty") if gate.get("uncertainty") is not None
                   else hc.get("uncertainty"))
    if uncertainty is None:
        uncertainty = {"GREEN": 0.2, "AMBER": 0.55, "RED": 0.85}.get(str(color), 0.5)
    token_budget = 64 if str(color) in ("AMBER", "RED") else 192
    route = "local-degraded" if str(color) == "RED" else "signed-paused"
    risk = [f"gate:{color}"]
    if wm:
        risk.append("wm:present")
    ctx = list(memory_ids) + [f"hc:{color}", f"wm:{len(wm)}"]
    return {
        "context_ids": ctx,
        "uncertainty": uncertainty,
        "gate_mode": str(color),
        "token_budget": token_budget,
        "risk_reasons": risk,
        "route": route,
        "n_chars": len(text or ""),
    }


def _hc_wm_effect(text: str) -> dict:
    from . import local_commands as _lc
    last = _lc.last_remember()
    memory_ids = [str(last["id"])] if last and last.get("id") else []
    plan_a = _plan_pipeline(text, hcwm=True, memory_ids=memory_ids)
    plan_b = _plan_pipeline(text, hcwm=False, memory_ids=memory_ids)
    deltas = {
        "context_ids_delta": plan_a["context_ids"] != plan_b["context_ids"],
        "uncertainty_delta": plan_a["uncertainty"] != plan_b["uncertainty"],
        "gate_mode_delta": plan_a["gate_mode"] != plan_b["gate_mode"],
        "token_budget_delta": plan_a["token_budget"] != plan_b["token_budget"],
        "risk_reasons_delta": plan_a["risk_reasons"] != plan_b["risk_reasons"],
        "route_delta": plan_a["route"] != plan_b["route"],
    }
    meaningful = any(deltas.values())
    label = "HC_WM_CAUSAL" if meaningful else "HC_WM_DECORATIVE_PATH"
    return {
        "label": label,
        "plan_a": plan_a,
        "plan_b": plan_b,
        "deltas": deltas,
        "same_as_b": not meaningful,
        "executable": False,
    }


def _emit_owner_inbound(decision: dict, text: str) -> None:
    """#14A F2: bitemporal spine event. No clock fabrication. No getMe."""
    if os.environ.get("OCTOPUS_T48_EVENT_TIME", "1").strip().lower() not in ("1", "true", "yes", "on"):
        return
    try:
        import sys as _sys
        _sp = str(_OPS / "spine")
        if _sp not in _sys.path:
            _sys.path.insert(0, _sp)
        import spine_adapters as _sa
        date = decision.get("message_date")
        if not date:
            return
        from datetime import datetime, timezone as _tz
        occ = datetime.fromtimestamp(int(date), tz=_tz.utc).isoformat(timespec="seconds")
        _sa.emit_event(
            event_type="delivered", domain="telegram",
            correlation_id=f"tg-{decision.get('chat_id')}-{date}",
            subject="owner_message", producer="owner_console_seam",
            trust="DETERMINISTIC", occurred_at=occ,
            event_time_source="telegram_message_date", time_precision="1s",
            payload={"mode": decision.get("mode"), "reason": decision.get("reason"),
                     "bot_id": _bot_id(),
                     "handler_schema_version": HANDLER_SCHEMA_VERSION},
            idempotency_key=f"tg-{decision.get('chat_id')}-{date}-{decision.get('update_id')}|owner-console")
    except Exception:  # noqa: BLE001
        pass
