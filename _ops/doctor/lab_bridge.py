# -*- coding: utf-8 -*-
"""Bridge: evolutionary doctor RFC -> self-upgrade lab cycle -> Telegram outbox.

Additive. Propose-only merge still requires human-append [merge]/[reject].
Never calls the live Bot API. Fake transport / durable outbox only.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
_TG = _OPS / "telegram_center"
if str(_TG) not in sys.path:
    sys.path.insert(0, str(_TG))


def _state_root() -> Path:
    configured = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
    if configured:
        return Path(configured)
    return _OPS / "state"


def _card_text(result: dict) -> str:
    card = result.get("telegram_card") if isinstance(result, dict) else {}
    card = card if isinstance(card, dict) else {}
    rfc_id = card.get("rfc_id") or result.get("rfc_id") or "?"
    bn = card.get("bottleneck") or result.get("bottleneck") or ""
    organ = card.get("organ") or result.get("organ") or "unknown"
    test_s = result.get("test_outcome") or (
        "pass" if card.get("test_ok") else "fail")
    ver = result.get("verify") if isinstance(result.get("verify"), dict) else {}
    v_ok = card.get("verify")
    if v_ok is None:
        v_ok = ver.get("confirmed")
    reasons = card.get("verify_reasons") or ver.get("reasons") or []
    wt = card.get("worktree") or result.get("worktree") or ""
    exp = card.get("experiment_id") or result.get("experiment_id") or ""
    promo = card.get("proposed_promote")
    if promo is None:
        promo = result.get("proposed_promote")
    lines = [
        "RFC " + str(rfc_id),
        "bottleneck: " + str(bn)[:200],
        "organ: " + str(organ),
        "lab test: " + str(test_s),
        "verify: " + ("ok" if v_ok else "no") + (
            (" " + ",".join(str(x) for x in reasons[:4])) if reasons else ""),
        "worktree: " + str(wt),
        "experiment: " + str(exp),
        "proposed_promote: " + ("yes" if promo else "no"),
        "",
        "[merge]  [reject]",
    ]
    return "\n".join(lines)


def _hash(value: object) -> str:
    blob = json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8", "replace")).hexdigest()


def _write_queued_outbox(text: str, result: dict) -> Path:
    """Persist a QUEUED card with payload_text so a later center restart can send it.

    Does not call the live Bot API. live_send stays false.
    """
    root = _state_root() / "telegram" / "loop" / "outbox"
    root.mkdir(parents=True, exist_ok=True)
    rfc_id = str((result.get("telegram_card") or {}).get("rfc_id")
                 or result.get("rfc_id") or "unknown")
    key = "evo-" + _hash({"rfc": rfc_id, "text": text})[:16]
    path = root / (key + ".json")
    rec = {
        "schema": "telegram-outbox/1",
        "message_key": key,
        "kind": "evo-lab-rfc-card",
        "stream": "evo-lab",
        "state": "QUEUED",
        "delivery_truth": "QUEUED",
        "live_send": False,
        "payload_text": text,
        "payload_hash": _hash(text),
        "rfc_id": rfc_id,
        "experiment_id": result.get("experiment_id"),
        "worktree": result.get("worktree"),
        "attempts": 0,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    # Mirror into event-bridge outbox (QUEUED, no transport).
    try:
        ebox = _state_root() / "telegram" / "event-bridge-outbox.jsonl"
        ebox.parent.mkdir(parents=True, exist_ok=True)
        with ebox.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"key": key, "state": "QUEUED",
                                 "event": "evo-lab-rfc-card",
                                 "rfc_id": rfc_id, "live_send": False,
                                 "ts": time.time()}, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return path


def enqueue_rfc_card(result: dict, *, send_fn: Callable[[], dict | None] | None = None,
                     chat_id: int = 0, topic_id=None,
                     stream: str = "evo-lab") -> dict[str, Any]:
    """Enqueue the [merge]/[reject] card via durable_loop + durable outbox.

    send_fn is injected. This function never opens a network socket.
    When send_fn is None the card is written QUEUED for a later center restart.
    """
    text = _card_text(result)
    delivered: dict | None = None
    if send_fn is not None:
        try:
            import durable_loop as dl  # noqa: WPS433
            if dl.enabled() and dl.current_context() is not None:
                delivered = dl.ack_local_result(
                    {"text": text}, chat_id=chat_id, topic_id=topic_id,
                    stream=stream, send_fn=send_fn)
        except Exception:
            delivered = None
    queued = _write_queued_outbox(text, result)
    return {
        "card_text": text,
        "outbox_path": str(queued),
        "deliver": delivered,
        "live_send": False,
    }


def _already(state_dir: Path, rfc_id: str) -> dict | None:
    p = state_dir / ("bridged-" + rfc_id.replace(":", "_") + ".json")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _mark(state_dir: Path, rfc_id: str, rec: dict) -> None:
    p = state_dir / ("bridged-" + rfc_id.replace(":", "_") + ".json")
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def run_rfc_through_lab(rfc: dict, *, worktree=None, state_dir=None,
                        send_fn: Callable[[], dict | None] | None = None,
                        chat_id: int = 0, topic_id=None) -> dict[str, Any]:
    """RFC dict in -> lab cycle (isolated worktree code) -> durable Telegram card."""
    from self_upgrade_lab.rfc_cycle import run_rfc_cycle  # noqa: WPS433

    rfc = dict(rfc or {})
    rfc_id = str(rfc.get("rfc_id") or "RFC-unknown")
    sd = Path(state_dir) if state_dir is not None else (
        Path(os.environ.get("OCTOPUS_SUL_STATE_DIR") or "")
        if str(os.environ.get("OCTOPUS_SUL_STATE_DIR") or "").strip()
        else _state_root() / "evo-lab-bridge")
    cached = _already(sd, rfc_id)
    if cached and cached.get("experiment_id"):
        cached.setdefault("cached", True)
        if send_fn is not None or not cached.get("outbox_path"):
            enq = enqueue_rfc_card(cached, send_fn=send_fn,
                                   chat_id=chat_id, topic_id=topic_id)
            cached["outbox"] = enq
            cached["outbox_path"] = enq.get("outbox_path")
        return cached

    lab = run_rfc_cycle(rfc, worktree=worktree, state_dir=sd)
    enq = enqueue_rfc_card(lab, send_fn=send_fn, chat_id=chat_id, topic_id=topic_id)
    lab["outbox"] = enq
    lab["outbox_path"] = enq.get("outbox_path")
    _mark(sd, rfc_id, {
        "rfc_id": rfc_id,
        "experiment_id": lab.get("experiment_id"),
        "worktree": lab.get("worktree"),
        "test_outcome": lab.get("test_outcome"),
        "verify": (lab.get("verify") or {}).get("confirmed"),
        "proposed_promote": lab.get("proposed_promote"),
        "telegram_card": lab.get("telegram_card"),
        "outbox_path": lab.get("outbox_path"),
        "live_send": False,
    })
    return lab


def on_rfc_ready(rfc: dict, **kwargs) -> dict[str, Any]:
    """Additive hook after an RFC is mined / submitted. Fail-soft at caller."""
    return run_rfc_through_lab(rfc, **kwargs)


def evolution_propose(rfc: dict, **kwargs) -> dict[str, Any]:
    """action_graph evolution.propose handler: mine RFC -> lab cycle -> outbox card."""
    return run_rfc_through_lab(rfc, **kwargs)


def propose(rfc: dict, **kwargs) -> dict[str, Any]:
    return evolution_propose(rfc, **kwargs)


def gate_merge(*, test_ok: bool = False, evidence_path=None,
               rollback_plan=None) -> dict[str, Any]:
    """Refuse [merge]/promote without test pass + evidence path + rollback plan."""
    from self_upgrade_lab.promoter import gate_promote  # noqa: WPS433
    return gate_promote(test_ok=test_ok, evidence_path=evidence_path,
                        rollback_plan=rollback_plan)


def refuse_merge_without_proofs(*, test_ok: bool = False, evidence_path=None,
                                rollback_plan=None) -> dict[str, Any]:
    """Alias used by merge path callers. Never auto-promotes."""
    g = gate_merge(test_ok=test_ok, evidence_path=evidence_path,
                   rollback_plan=rollback_plan)
    return {"allowed": bool(g.get("ok")), "gate": g, "live_promote": False}


def proofs_from_rfc(rfc) -> dict:
    """Extract lab/gate proofs from an RFC (sandbox_result or attributes). Additive."""
    sr = getattr(rfc, "sandbox_result", None)
    if not isinstance(sr, dict):
        sr = {}
    test_ok = sr.get("test_ok")
    if test_ok is None:
        test_ok = (sr.get("test_outcome") == "pass")
    evidence_path = sr.get("evidence_path") or getattr(rfc, "evidence_path", None)
    rollback_plan = (
        sr.get("rollback_plan")
        or getattr(rfc, "rollback", None)
        or sr.get("rollback")
    )
    # Lab / evo cards always enforce gate_promote (even when proofs are incomplete).
    labby = bool(
        sr.get("experiment_id")
        or sr.get("lab_proofs")
        or sr.get("proposed_promote") is not None
        or sr.get("worktree")
    )
    return {
        "test_ok": bool(test_ok),
        "evidence_path": evidence_path,
        "rollback_plan": rollback_plan,
        "require_gate": labby,
    }


def apply_owner_verdict(*, verb: str,
                        apply_merge_fn: Callable[..., bool] | None = None,
                        rfc=None,
                        test_ok: bool = False,
                        evidence_path=None,
                        rollback_plan=None,
                        require_gate: bool | None = None) -> dict[str, Any]:
    """Owner human-append [merge]/[reject] -> real effect.

    [merge]: gate_promote (test+evidence+rollback) then apply_merge_fn.
    [reject]/deny: never promote / never apply_merge.
    No live Telegram. No auto-merge without an explicit merge verb.
    """
    v = str(verb or "").strip().lower()
    if v in ("reject", "denied", "deny", "[reject]"):
        if rfc is not None and hasattr(rfc, "status"):
            try:
                rfc.status = "human-rejected"
            except Exception:
                pass
        return {
            "verb": "reject",
            "applied": False,
            "promoted": False,
            "live_promote": False,
            "gate": None,
        }
    if v in ("merge", "merge-approved", "approved", "[merge]"):
        has_proof_intent = bool(
            test_ok or (evidence_path is not None and str(evidence_path).strip())
            or (rollback_plan is not None and str(rollback_plan).strip())
        )
        enforce = bool(require_gate) if require_gate is not None else has_proof_intent
        if enforce:
            gate = gate_merge(test_ok=test_ok, evidence_path=evidence_path,
                              rollback_plan=rollback_plan)
            if not gate.get("ok"):
                return {
                    "verb": "merge",
                    "applied": False,
                    "promoted": False,
                    "live_promote": False,
                    "refused": True,
                    "gate": gate,
                }
        else:
            gate = None
        if apply_merge_fn is None:
            return {
                "verb": "merge",
                "applied": False,
                "promoted": False,
                "live_promote": False,
                "error": "missing-apply_merge_fn",
                "gate": gate,
            }
        applied = bool(apply_merge_fn(rfc))
        return {
            "verb": "merge",
            "applied": applied,
            "promoted": applied,
            "live_promote": False,
            "gate": gate,
            "legacy": gate is None,
        }
    return {
        "verb": v,
        "applied": False,
        "promoted": False,
        "live_promote": False,
        "error": "unknown-verb",
    }
