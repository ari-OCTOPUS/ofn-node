# -*- coding: utf-8 -*-
"""Bridge: evolutionary doctor RFC -> self-upgrade lab cycle -> Telegram outbox.

Additive. Propose-only merge still requires human-append [merge]/[reject].
Never calls the live Bot API. Fake transport / durable outbox only.
"""
from __future__ import annotations

import hashlib
import json
import re
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



def _owner_id(owner=None):
    """Owner chat id for RFC callback tokens. Env fallback. Never network."""
    if owner is not None and str(owner).strip() != "":
        try:
            return int(owner)
        except (TypeError, ValueError):
            return owner
    raw = str(os.environ.get("TELEGRAM_OWNER_CHAT_ID", "") or "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return raw


def attach_outbox_callback_token(rec: dict, *, rfc_id: str, summary: str = "",
                                 owner=None, state_dir=None) -> dict:
    """Smallest additive callback token on a QUEUED evo outbox card.

    Uses outcomes.pending_card_recovery.prepare_rfc_card (nonce+hash durable;
    bearer token only on the card payload). Fail-soft when secret/owner missing:
    marks callback_token_missing=True and leaves merge/deny callback_data empty.
    Never live-sends. Never opens a network socket.
    """
    out = dict(rec or {})
    oid = _owner_id(owner)
    sd = Path(state_dir) if state_dir is not None else _state_root()
    rid = str(rfc_id or out.get("rfc_id") or "unknown")
    made = None
    why = "no-owner"
    if oid is not None:
        try:
            import outcomes.pending_card_recovery as _pcr  # noqa: WPS433
            made = _pcr.prepare_rfc_card(
                state_dir=sd, rfc_id=rid,
                summary=summary or ("evo-lab " + rid),
                owner=oid)
            why = "prepare-failed" if not made else "ok"
        except Exception as exc:  # noqa: BLE001 — fail-soft
            made = None
            why = "prepare-error:" + type(exc).__name__
    else:
        why = "no-owner"
    if not made or not made.get("token"):
        out["callback_token"] = ""
        out["callback_merge"] = ""
        out["callback_deny"] = ""
        out["callback_token_missing"] = True
        out["callback_token_why"] = why
        return out
    token = str(made["token"])
    out["callback_token"] = token
    out["callback_merge"] = "rfc:merge:%s:%s" % (rid, token)
    out["callback_deny"] = "rfc:deny:%s:%s" % (rid, token)
    out["callback_token_missing"] = False
    out["callback_token_why"] = "ok"
    out["callback_owner"] = oid
    return out


def parse_outbox_callback(payload) -> dict[str, Any] | None:
    """Parse callback token fields back from an outbox card (path/dict/json).

    Returns {"rfc_id", "token", "callback_merge", "callback_deny",
             "callback_token_missing"} or None if not an evo outbox card.
    Fixture / recovery helper. Never network.
    """
    data = payload
    if isinstance(payload, (str, Path)):
        path = Path(payload)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
    if not isinstance(data, dict):
        return None
    if data.get("kind") not in (None, "evo-lab-rfc-card") and not data.get("rfc_id"):
        if "callback_token" not in data and "callback_merge" not in data:
            return None
    rfc_id = data.get("rfc_id")
    token = data.get("callback_token") or ""
    merge = data.get("callback_merge") or ""
    deny = data.get("callback_deny") or ""
    if not token and merge.startswith("rfc:merge:"):
        parts = merge.split(":")
        if len(parts) >= 4:
            rfc_id = rfc_id or parts[2]
            token = parts[3]
    return {
        "rfc_id": rfc_id,
        "token": token,
        "callback_merge": merge or (
            ("rfc:merge:%s:%s" % (rfc_id, token)) if rfc_id and token else ""),
        "callback_deny": deny or (
            ("rfc:deny:%s:%s" % (rfc_id, token)) if rfc_id and token else ""),
        "callback_token_missing": bool(data.get("callback_token_missing")) or not bool(token),
        "live_send": bool(data.get("live_send")),
    }


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
    # Additive callback token for owner [merge]/[reject] buttons (no live send).
    rec = attach_outbox_callback_token(
        rec, rfc_id=rfc_id,
        summary=str((result.get("telegram_card") or {}).get("bottleneck")
                    or result.get("bottleneck") or rfc_id),
        owner=result.get("callback_owner") or result.get("owner"))
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



def parse_owner_verdict_text(text: str) -> dict[str, Any] | None:
    """Smallest free-text parser for owner Telegram [merge]/[reject].

    Callbacks already work via rfc:merge|deny. This catches literal replies that
    include bracket tags (card footer) and an optional RFC id. Persian bracket
    aliases [ادغام]/[رد] map to the same verbs (رد is the deny button label).
    Returns {"verb": "merge"|"reject", "rfc_id": str|None, "raw_tag": str} or None.
    Never opens a network socket / never live-sends.
    """
    raw = str(text or "")
    if not raw.strip():
        return None
    m = re.search(r"\[\s*(merge|reject|deny|ادغام|رد)\s*\]", raw, flags=re.IGNORECASE)
    if not m:
        return None
    tag = m.group(1)
    low = tag.lower()
    if low == "merge" or tag == "ادغام":
        verb = "merge"
    elif low in ("reject", "deny") or tag == "رد":
        verb = "reject"
    else:
        return None
    rfc_id = None
    rm = re.search(
        r"\b(RFC[-_:]?[A-Za-z0-9][A-Za-z0-9._:-]{0,80})\b",
        raw, flags=re.IGNORECASE)
    if rm:
        rfc_id = rm.group(1)
    return {"verb": verb, "rfc_id": rfc_id, "raw_tag": m.group(0)}


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



# ── EveLab ↔ Doctor reversible wire (propose-only / dry-run default) ──────────
# Not RFC-only: doctor can propose one lab experiment ticket into durable outbox;
# lab can call a dry doctor check and parse the ticket back. Never live-sends.


def _experiment_ticket_text(ticket: dict) -> str:
    tid = ticket.get("experiment_id") or "?"
    q = ticket.get("question") or ticket.get("hypothesis") or ""
    organ = ticket.get("organ") or "unknown"
    mode = ticket.get("execution_mode") or "FIXTURE_ONLY"
    lines = [
        "LAB EXPERIMENT TICKET " + str(tid),
        "question: " + str(q)[:240],
        "organ: " + str(organ),
        "execution_mode: " + str(mode),
        "propose_only: yes",
        "live_send: no",
        "",
        "[merge]  [reject]",
    ]
    return "\n".join(lines)


def _write_experiment_ticket_outbox(ticket: dict, text: str) -> Path:
    """Persist a QUEUED lab-experiment ticket. Never calls Bot API."""
    root = _state_root() / "telegram" / "loop" / "outbox"
    root.mkdir(parents=True, exist_ok=True)
    eid = str(ticket.get("experiment_id") or "unknown")
    key = "labexp-" + _hash({"eid": eid, "text": text})[:16]
    path = root / (key + ".json")
    rec = {
        "schema": "telegram-outbox/1",
        "message_key": key,
        "kind": "evo-lab-experiment-ticket",
        "stream": "evo-lab",
        "state": "QUEUED",
        "delivery_truth": "QUEUED",
        "live_send": False,
        "payload_text": text,
        "payload_hash": _hash(text),
        "experiment_id": eid,
        "ticket": {
            "experiment_id": eid,
            "question": ticket.get("question"),
            "hypothesis": ticket.get("hypothesis"),
            "organ": ticket.get("organ"),
            "execution_mode": ticket.get("execution_mode") or "FIXTURE_ONLY",
            "rfc_id": ticket.get("rfc_id"),
        },
        "attempts": 0,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
        "dry_run": True,
        "propose_only": True,
    }
    # Optional callback token when owner/rfc present (fail-soft).
    if ticket.get("rfc_id"):
        rec = attach_outbox_callback_token(
            rec, rfc_id=str(ticket.get("rfc_id")),
            summary=str(ticket.get("question") or eid),
            owner=ticket.get("owner"))
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    try:
        ebox = _state_root() / "telegram" / "event-bridge-outbox.jsonl"
        ebox.parent.mkdir(parents=True, exist_ok=True)
        with ebox.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "key": key, "state": "QUEUED",
                "event": "evo-lab-experiment-ticket",
                "experiment_id": eid, "live_send": False,
                "ts": time.time(),
            }, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return path


def propose_lab_experiment_ticket(
        ticket: dict | None = None, *,
        experiment_id: str | None = None,
        question: str = "",
        hypothesis: str = "",
        organ: str = "doctor",
        execution_mode: str = "FIXTURE_ONLY",
        rfc_id: str | None = None,
        dry_run: bool = True,
        state_dir=None) -> dict[str, Any]:
    """Doctor → lab: propose one experiment ticket into durable outbox.

    Propose-only / dry-run default. Does not run the RFC cycle. Never live-sends.
    Never opens a network socket.
    """
    if state_dir is not None:
        os.environ["OCTOPUS_STATE_DIR"] = str(state_dir)
    t = dict(ticket or {})
    if experiment_id:
        t["experiment_id"] = experiment_id
    t.setdefault("experiment_id", "labexp-" + _hash({
        "q": question or t.get("question"), "t": time.time(),
    })[:12])
    if question:
        t["question"] = question
    if hypothesis:
        t["hypothesis"] = hypothesis
    t.setdefault("question", t.get("hypothesis") or "fixture lab experiment")
    t.setdefault("hypothesis", t.get("question"))
    t.setdefault("organ", organ)
    t.setdefault("execution_mode", execution_mode)
    if rfc_id:
        t["rfc_id"] = rfc_id
    if not dry_run:
        # Hard default: still no live send; dry_run only skips optional side marks.
        pass
    text = _experiment_ticket_text(t)
    path = _write_experiment_ticket_outbox(t, text)
    return {
        "ok": True,
        "experiment_id": t["experiment_id"],
        "ticket": t,
        "card_text": text,
        "outbox_path": str(path),
        "kind": "evo-lab-experiment-ticket",
        "state": "QUEUED",
        "live_send": False,
        "dry_run": True,
        "propose_only": True,
        "live_promote": False,
    }


def parse_lab_experiment_ticket(payload) -> dict[str, Any] | None:
    """Reverse parse of an evo-lab-experiment-ticket outbox card (path/dict/json).

    Returns ticket fields + live_send flag, or None if not a lab experiment ticket.
    Never network.
    """
    data = payload
    if isinstance(payload, (str, Path)):
        path = Path(payload)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
    if not isinstance(data, dict):
        return None
    if data.get("kind") not in (None, "evo-lab-experiment-ticket"):
        if not data.get("experiment_id") or data.get("kind") == "evo-lab-rfc-card":
            return None
    ticket = data.get("ticket") if isinstance(data.get("ticket"), dict) else {}
    eid = data.get("experiment_id") or ticket.get("experiment_id")
    if not eid:
        return None
    return {
        "experiment_id": eid,
        "question": ticket.get("question") or data.get("question"),
        "hypothesis": ticket.get("hypothesis"),
        "organ": ticket.get("organ"),
        "execution_mode": ticket.get("execution_mode") or "FIXTURE_ONLY",
        "rfc_id": ticket.get("rfc_id") or data.get("rfc_id"),
        "outbox_state": data.get("state"),
        "live_send": bool(data.get("live_send")),
        "kind": data.get("kind") or "evo-lab-experiment-ticket",
        "payload_text": data.get("payload_text") or "",
        "outbox_path": str(payload) if isinstance(payload, (str, Path)) else None,
    }


def lab_call_doctor_check(*, state_dir=None, dry_run: bool = True,
                          roundtrip: bool = True) -> dict[str, Any]:
    """Lab → doctor: lightweight dry-run check of the reversible wire.

    Verifies doctor bridge surface + optional propose/parse roundtrip.
    Never live-sends. Never restarts center. Never mutates live vault code.
    """
    if state_dir is not None:
        os.environ["OCTOPUS_STATE_DIR"] = str(state_dir)
    checks: list[dict[str, Any]] = []
    ok = True

    # 1) lab_bridge propose surface present
    has_propose = callable(globals().get("propose_lab_experiment_ticket"))
    has_parse = callable(globals().get("parse_lab_experiment_ticket"))
    checks.append({"name": "lab_bridge_ticket_api", "ok": has_propose and has_parse})
    ok = ok and has_propose and has_parse

    # 2) doctor._bridge_to_lab present (RFC path still wired)
    bridge_ok = False
    try:
        import doctor as _doc_mod  # noqa: WPS433
        Doctor = getattr(_doc_mod, "Doctor", None)
        bridge_ok = Doctor is not None and callable(
            getattr(Doctor, "_bridge_to_lab", None))
        # Prefer instance method presence on class
        if not bridge_ok and Doctor is not None:
            bridge_ok = "_bridge_to_lab" in getattr(Doctor, "__dict__", {})
    except Exception as exc:  # noqa: BLE001
        checks.append({"name": "doctor_import", "ok": False,
                       "error": type(exc).__name__})
        ok = False
    else:
        checks.append({"name": "doctor_bridge_to_lab", "ok": bridge_ok})
        ok = ok and bridge_ok

    # 3) optional roundtrip under fixture state_dir
    if roundtrip and dry_run:
        sd = Path(state_dir) if state_dir is not None else (
            _state_root() / "evelab-doctor-wire-fixture")
        sd.mkdir(parents=True, exist_ok=True)
        prev = os.environ.get("OCTOPUS_STATE_DIR")
        os.environ["OCTOPUS_STATE_DIR"] = str(sd)
        try:
            prop = propose_lab_experiment_ticket(
                experiment_id="labexp-wire-check",
                question="lab can call doctor check",
                organ="doctor",
                dry_run=True,
                state_dir=sd)
            parsed = parse_lab_experiment_ticket(prop.get("outbox_path"))
            rt_ok = bool(prop.get("ok") and parsed
                         and parsed.get("experiment_id") == "labexp-wire-check"
                         and parsed.get("live_send") is False)
            checks.append({
                "name": "propose_parse_roundtrip",
                "ok": rt_ok,
                "outbox_path": prop.get("outbox_path"),
            })
            ok = ok and rt_ok
        finally:
            if prev is None:
                os.environ.pop("OCTOPUS_STATE_DIR", None)
            else:
                os.environ["OCTOPUS_STATE_DIR"] = prev
    else:
        checks.append({"name": "propose_parse_roundtrip", "ok": True, "skipped": True})

    # 4) fail-closed poller uniqueness (dry-run fixture under state_dir)
    uniq_summary: dict[str, Any]
    try:
        import poller_uniqueness as _pu  # noqa: WPS433
        if dry_run:
            sd = Path(state_dir) if state_dir is not None else (
                _state_root() / "evelab-doctor-wire-fixture")
            sd.mkdir(parents=True, exist_ok=True)
            fixture_pid = 424242
            _pu.seed_uniqueness_fixture(sd, center_pid=fixture_pid)
            uniq = _pu.check_poller_uniqueness(
                state_dir=sd,
                center_pids=[fixture_pid],
                require_lock_pid_alive=False,
                scan_live_pids=False,
            )
            uniq_ok = bool(uniq.get("ok"))
            uniq_summary = {
                "name": "poller_uniqueness",
                "ok": uniq_ok,
                "fixture": True,
                "center_pid_count": uniq.get("center_pid_count"),
                "active_lease_count": uniq.get("active_lease_count"),
                "tg_poller_lock_count": uniq.get("tg_poller_lock_count"),
                "checks": uniq.get("checks"),
                "reasons": uniq.get("reasons") or [],
            }
            ok = ok and uniq_ok
        else:
            # Non-dry path still fail-closed on live probe (read-only).
            uniq = _pu.check_poller_uniqueness(state_dir=state_dir)
            uniq_ok = bool(uniq.get("ok"))
            uniq_summary = {
                "name": "poller_uniqueness",
                "ok": uniq_ok,
                "fixture": False,
                "center_pid_count": uniq.get("center_pid_count"),
                "active_lease_count": uniq.get("active_lease_count"),
                "tg_poller_lock_count": uniq.get("tg_poller_lock_count"),
                "checks": uniq.get("checks"),
                "reasons": uniq.get("reasons") or [],
            }
            ok = ok and uniq_ok
    except Exception as exc:  # noqa: BLE001 — fail-closed
        uniq_summary = {
            "name": "poller_uniqueness",
            "ok": False,
            "error": type(exc).__name__,
            "error_msg": str(exc)[:200],
        }
        ok = False
    checks.append(uniq_summary)

    return {
        "ok": ok,
        "dry_run": True,
        "live_send": False,
        "propose_only": True,
        "checks": checks,
        "wire": "evelab-doctor-reversible/1",
    }
