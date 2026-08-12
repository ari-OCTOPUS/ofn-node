#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collaborator.py — collaborator engine (WP-E3 + Talk Discovery Phase A).

Wraps/extends conversation.py, does NOT replace it.
Default deterministic stub ($0, no network).
Real model behind OCTOPUS_COLLAB_USE_MODEL → collab_model_adapter → model_router.

Contract:
  schema: owner-console.reply.v1
  external_effect = false
  send_attempted = false
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent

import sys
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from owner_console import conversation, collab_memory  # noqa: E402
from owner_console import collab_model_adapter as _model  # noqa: E402


def _is_enabled() -> bool:
    return os.environ.get("OCTOPUS_WIRE_COLLAB", "0") == "1"


def _use_model() -> bool:
    return os.environ.get("OCTOPUS_COLLAB_USE_MODEL", "0") == "1"


def _turn_id(owner_text: str) -> str:
    """Deterministic turn ID from owner text for replay-safe idempotency."""
    return hashlib.sha256(str(owner_text).encode("utf-8")).hexdigest()[:16]


def _stub_enhance(base_reply: dict, owner_text: str) -> dict:
    """Deterministic stub enhancement — rationale + model_source stub."""
    enhanced = dict(base_reply)
    data = dict(enhanced.get("data") or {})
    kind = enhanced.get("kind", "")
    if kind == "clarify":
        data["rationale"] = "stub: input ambiguous — needs narrower intent specification"
    elif kind == "intro":
        data["rationale"] = "stub: structural owner intro"
    elif kind == "capabilities":
        data["rationale"] = "stub: catalog lookup from capability manifest"
    elif kind == "runtime":
        data["rationale"] = "stub: live_snapshot read-only truth"
    elif kind == "blockers":
        data["rationale"] = "stub: health snapshot blockers"
    else:
        data["rationale"] = f"stub: deterministic reply for kind={kind}"
    enhanced["data"] = data
    enhanced["model_source"] = "deterministic-stub"
    return enhanced


# LLM may enrich talk turns; discover stays deterministic (journal/pulse evidence).
# 2026-08-12 fix: intro از _LLM_KINDS خارج شد — _live_intro_witness شاهد زندهٔ فوری دارد
# (beat/pain/brains)؛ فرستادنِ «سلام» به DeepSeek باعث client_timeout 60s می‌شد.
_LLM_KINDS = frozenset({"clarify", "chat"})


def _model_enhance(base_reply: dict, owner_text: str) -> dict:
    """Call model_router via adapter; on failure fall back to stub honestly."""
    kind = str(base_reply.get("kind") or "")
    if kind not in _LLM_KINDS:
        return _stub_enhance(base_reply, owner_text)

    result = _model.complete(owner_text, kind_hint=kind)
    if not result.get("ok"):
        enhanced = _stub_enhance(base_reply, owner_text)
        enhanced["model_source"] = "model-fallback-stub"
        data = dict(enhanced.get("data") or {})
        reason = result.get("reason") or "unknown"
        data["warning"] = f"model_call_failed:{reason}"
        # 2026-08-12 fix: قبلاً دلیلِ واقعیِ شکست (مثلاً سهمیهٔ روزانه تمام
        # شده) فقط در data.warning می‌رفت — فیلدی که app.js هیچ‌جا نمی‌خواند
        # (بررسی شد: صفر ارجاع به .warning در buildSourcesPanel). کاربر متنِ
        # عمومیِ stub را می‌دید انگار یک شکستِ گذرا بود، نه یک محدودیتِ
        # ساعت‌ها-طولانی. اینجا مستقیم از fugu_quota.status() (فقط‌خواندنی،
        # بدون تماسِ پولی) چک می‌شود — مستقل از اینکه reason چه رشته‌ای بود،
        # چون model_router در برخی مسیرها (quota denial) به‌جای reason
        # مشخص فقط None برمی‌گرداند و اینجا به "no-answer" عمومی می‌رسد.
        try:
            import sys as _qsys
            _cortex_dir = str(HERE.parent / "cortex")
            if _cortex_dir not in _qsys.path:
                _qsys.path.insert(0, _cortex_dir)
            import fugu_quota as _fq  # noqa: WPS433
            qs = _fq.status()
            if qs.get("remaining", 1) <= 0:
                enhanced["text"] = (
                    f"سهمیهٔ روزانهٔ مدل پولی تمام شده ({qs.get('used_total')}/"
                    f"{qs.get('cap')}) — تا نیمه‌شب UTC ریست می‌شود. "
                    "این یک شکستِ گذرا نیست؛ دوباره‌فرستادن الان کمکی نمی‌کند.\n\n"
                    + str(enhanced.get("text") or "")
                )
        except Exception:  # noqa: BLE001 — چک اختیاری؛ شکستش نباید جوابِ stub را ببرد
            pass
        enhanced["data"] = data
        return enhanced

    enhanced = dict(base_reply)
    data = dict(enhanced.get("data") or {})
    data["rationale"] = "model: model_router via collab_model_adapter"
    data["tier"] = result.get("tier")
    enhanced["data"] = data
    enhanced["text"] = result["text"]
    if kind == "clarify":
        enhanced["kind"] = "chat"
    enhanced["model_source"] = result.get("model_source") or "model"
    enhanced["estimated_cost"] = float(result.get("cost_usd") or 0.0)
    return enhanced


def handle(text: str, *, state_dir: Path | None = None) -> dict:
    """Handle owner input with collaborator enhancement.

    Default: deterministic stub ($0, no network).
    If OCTOPUS_COLLAB_USE_MODEL=1: collab_model_adapter → model_router.

    Policy: draft responses only — never external_effect / send.
    Content-free episodic digests (sha256 markers) are not WRITE_EPISODIC_MEMORY.
    """
    if not _is_enabled():
        return {
            "schema": "owner-console.reply.v1",
            "kind": "disabled",
            "text": "🚫 Collaborator غیرفعال است (OCTOPUS_WIRE_COLLAB=0).",
            "keyboard": [],
            "data": {"status": "DISABLED"},
            "external_effect": False,
            "estimated_cost": 0,
            "send_attempted": False,
            "authorization": None,
        }

    # ADR-033 Evidence-Control Plane: quarantine + PolicyGate (fail-closed).
    # Allowed path only: retrieve → reason → draft → display.
    auth_meta: dict = {}
    try:
        from evidence_plane.quarantine import admit, may_draft_reply
        from policy.talk_gate import guard_talk_discovery_draft

        envelope = admit(
            text=text,
            source_kind="user",
            trust_level="untrusted",
            injection_signals=False,
        )
        if not may_draft_reply(envelope):
            return {
                "schema": "owner-console.reply.v1",
                "kind": "blocked",
                "text": "🔐 ContextQuarantine: ورودی قابل مصرف عملیاتی نیست.",
                "keyboard": [],
                "data": {
                    "status": "QUARANTINED",
                    "provenance_id": envelope.provenance_id,
                },
                "external_effect": False,
                "estimated_cost": 0,
                "send_attempted": False,
                "authorization": None,
            }

        gate = guard_talk_discovery_draft(text)
        draft = gate["draft"]
        auth_meta = {
            "policy_version": gate["policy_version"],
            "gate_decision": draft.decision,
            "gate_reason": draft.reason,
            "event_id": draft.event_id,
            "provenance_id": envelope.provenance_id,
            "context_status": envelope.status.value,
            "external_send_denied": gate["external_send_denied"],
        }
        if not draft.allowed:
            return {
                "schema": "owner-console.reply.v1",
                "kind": "blocked",
                "text": f"🔐 PolicyGate: {draft.reason}",
                "keyboard": [],
                "data": {"status": "POLICY_BLOCKED", **auth_meta},
                "external_effect": False,
                "estimated_cost": 0,
                "send_attempted": False,
                "authorization": None,
            }
        assert gate["external_send_denied"] is True
    except Exception:  # noqa: BLE001 — import miss must not open effects
        # Fail closed on side-effects; still allow draft via legacy policy if present.
        try:
            from collab.talk_discovery_policy import TalkAction, TalkDiscoveryPolicy
            decision = TalkDiscoveryPolicy().decide(
                TalkAction.RESPOND_DRAFT,
                collab_enabled=True,
                untrusted_instruction=True,
                owner_approval_id=None,
            )
            if not decision.allowed:
                return {
                    "schema": "owner-console.reply.v1",
                    "kind": "blocked",
                    "text": f"🔐 PolicyGate: {decision.reason}",
                    "keyboard": [],
                    "data": {"status": "POLICY_BLOCKED", "reason": decision.reason},
                    "external_effect": False,
                    "estimated_cost": 0,
                    "send_attempted": False,
                    "authorization": None,
                }
        except Exception:
            pass

    base_reply = conversation.handle(text)

    # ── Cognitive Runtime: Typed Event instrumentation (additive, fail-soft) ──
    _run_info = None
    try:
        import sys as _csys
        _cog = str(Path(__file__).resolve().parent.parent / "cognitive")
        if _cog not in _csys.path:
            _csys.path.insert(0, _cog)
        import event_stream as _es  # noqa: WPS433
        _run_info = _es.start_run(text)
        _es.emit(_run_info["run_id"], "INTENT_DETECTED",
                 trace_id=_run_info["trace_id"], producer="conversation",
                 intent=str(base_reply.get("kind", "unknown")),
                 payload={"kind": base_reply.get("kind")})
    except Exception:  # noqa: BLE001 — instrumentation هرگز collab را نمی‌کشد
        _run_info = None

    if _use_model():
        enhanced = _model_enhance(base_reply, text)
        if _run_info:
            try:
                _es.emit(_run_info["run_id"], "MODEL_FINISHED",
                         trace_id=_run_info["trace_id"], producer="adapter",
                         payload={"model_source": enhanced.get("model_source", "?")})
            except Exception:  # noqa: BLE001
                pass
    else:
        enhanced = _stub_enhance(base_reply, text)
        if _run_info:
            try:
                _es.emit(_run_info["run_id"], "MODEL_FINISHED",
                         trace_id=_run_info["trace_id"], producer="stub",
                         status="SKIPPED",
                         payload={"model_source": "deterministic-stub"})
            except Exception:  # noqa: BLE001
                pass

    turn_id = _turn_id(text)
    # Content-free digest only (sha256) — not semantic episodic write.
    mem_result = collab_memory.append(
        turn_id=turn_id,
        role="owner",
        intent=enhanced.get("kind", "unknown"),
        summary=(f"owner_input_sha256={hashlib.sha256(str(text).encode('utf-8')).hexdigest()};"
                 f"reply_kind={enhanced.get('kind', '?')}"),
        state_dir=state_dir,
    )
    if mem_result.get("ok"):
        data = dict(enhanced.get("data") or {})
        data["memory_turn_id"] = turn_id
        data["memory_kind"] = "content_free_digest"
        enhanced["data"] = data
    # فاز S — session memory (موقت؛ فقط preview؛ may_authorize=false)
    try:
        import sys
        from pathlib import Path as _Ps
        mem_dir_s = str(_Ps(__file__).resolve().parent.parent / "memory")
        if mem_dir_s not in sys.path:
            sys.path.insert(0, mem_dir_s)
        import session_memory as _sm  # noqa: WPS433
        _sm.remember(turn_id, "owner", str(enhanced.get("kind") or "chat"), text)
        _sm.remember(turn_id + ":r", "collaborator",
                     str(enhanced.get("kind") or "chat"),
                     str(enhanced.get("text") or "")[:200])
        data = dict(enhanced.get("data") or {})
        data["session_turn"] = turn_id
        enhanced["data"] = data
    except Exception:  # noqa: BLE001 — session هرگز collab را نمی‌کشد
        pass
    # فاز V (2026-08-12 owner request) — Chat Log سرور-ساید:
    # گفتگو را در وب‌اپ سیو کن (قبلاً فقط localStorage مرورگر بود).
    # fail-soft + redact + run_id → به Cognitive Runtime وصل است.
    try:
        import sys as _cv
        from pathlib import Path as _Pv
        _own_dir = str(_Pv(__file__).resolve().parent)
        if _own_dir not in _cv.path:
            _cv.path.insert(0, _own_dir)
        import chat_log as _clog  # noqa: WPS433
        _run_id_v = (_run_info or {}).get("run_id") or ""
        _clog.append(role="owner", kind=str(enhanced.get("kind") or "chat"),
                     text=text, run_id=_run_id_v, turn_id=turn_id)
        _clog.append(role="collaborator", kind=str(enhanced.get("kind") or "chat"),
                     text=str(enhanced.get("text") or ""), run_id=_run_id_v,
                     model_source=str(enhanced.get("model_source") or ""),
                     turn_id=turn_id + ":r")
    except Exception:  # noqa: BLE001 — chat log هرگز collab را نمی‌کشد
        pass
    # فاز X (2026-08-12) — پیشنهاد حافظه از حرف مالک:
    # فقط CANDIDATE (may_authorize=false)؛ commit با رأی مالک. حلقهٔ چت→حافظه.
    try:
        import sys as _cx
        from pathlib import Path as _Px
        _cog_x = str(_Px(__file__).resolve().parent.parent / "cognitive")
        if _cog_x not in _cx.path:
            _cx.path.insert(0, _cog_x)
        import memory_formation as _mf  # noqa: WPS433
        _kind_x = str(enhanced.get("kind") or "chat")
        if _kind_x not in ("greeting", "intro", "timeout", "blocked", "disabled"):
            _prop = _mf.propose_memory(text, intent=_kind_x,
                                       run_id=(_run_info or {}).get("run_id"))
            if (_prop.get("ok")
                    and _prop.get("importance") in
                    (_mf.IMPORTANCE_HIGH, _mf.IMPORTANCE_MEDIUM)):
                data = dict(enhanced.get("data") or {})
                data["memory_candidate_id"] = _prop.get("candidate_id")
                data["memory_candidate_importance"] = _prop.get("importance")
                data["memory_candidate_status"] = _prop.get("status")
                enhanced["data"] = data
    except Exception:  # noqa: BLE001 — پیشنهاد هرگز collab را نمی‌کشد
        pass

    enhanced["external_effect"] = False
    if "estimated_cost" not in enhanced:
        enhanced["estimated_cost"] = 0
    enhanced["send_attempted"] = False
    data = dict(enhanced.get("data") or {})
    data["policy_version"] = auth_meta.get("policy_version") or "ADR-033-v1"
    data["response_mode"] = "draft"
    data["evidence_plane"] = "ADR-033"
    if auth_meta:
        data["authorization_truth"] = auth_meta
    # Awareness megaprompt: cite-only Memory/self-loop facts for Sources panel
    try:
        import sys
        from pathlib import Path as _P
        mem_dir = str(_P(__file__).resolve().parent.parent / "memory")
        if mem_dir not in sys.path:
            sys.path.insert(0, mem_dir)
        import owner_recall as _or  # noqa: WPS433
        if _or.topic_wants_recall(text):
            facts = _or.recall_for_owner_ask(text, limit=3)
            data["facts"] = facts
            data["facts_rationale"] = (
                "recall cite-only" if facts else "recall خالی"
            )
            data["may_authorize"] = False
            if facts and "شاهد:" not in str(enhanced.get("text") or ""):
                cite_lines = []
                for f in facts[:3]:
                    cite_lines.append(
                        f"· {f.get('source_path')} / {f.get('mkey')}"
                    )
                enhanced["text"] = (
                    str(enhanced.get("text") or "").rstrip()
                    + "\n\nشاهد:\n" + "\n".join(cite_lines)
                )
        else:
            data.setdefault("facts", [])
    except Exception:  # noqa: BLE001 — recall هرگز collab را نمی‌کشد
        data.setdefault("facts", [])
        data["facts_rationale"] = "recall unavailable (fail-soft)"
    # Phase J: equation advice — observe-only, advice_only, never decides.
    try:
        import sys
        from pathlib import Path as _P2
        mem_dir2 = str(_P2(__file__).resolve().parent.parent / "memory")
        if mem_dir2 not in sys.path:
            sys.path.insert(0, mem_dir2)
        import equation_advice as _ea  # noqa: WPS433
        adv = _ea.equation_advice_snapshot()
        data["equation_advice"] = {
            "schema": adv.get("schema"),
            "equation_advice_only": adv.get("equation_advice_only"),
            "decision_effect": adv.get("decision_effect"),
            "apply_effect": adv.get("apply_effect"),
            "equations_consulted": adv.get("equations_consulted"),
            "aggregate_advice": adv.get("aggregate_advice"),
        }
        if adv.get("aggregate_advice") == "slow_down":
            data["equation_advice"]["note"] = (
                "معادلات فقط توصیه می‌کنند؛ هیچ تصمیمی تغییر نکرده."
            )
    except Exception:  # noqa: BLE001 — advice هرگز collab را نمی‌کشد
        data.setdefault("equation_advice", {
            "equation_advice_only": True,
            "decision_effect": False,
            "apply_effect": False,
            "error": "advice unavailable (fail-soft)",
        })
    # Phase P/T: unified context (shadow/effects/architecture) — read-only visibility.
    try:
        import sys
        from pathlib import Path as _P3
        mem_dir3 = str(_P3(__file__).resolve().parent.parent / "memory")
        if mem_dir3 not in sys.path:
            sys.path.insert(0, mem_dir3)
        import unified_context as _uc  # noqa: WPS433
        uctx = _uc.assemble(text)
        data["unified_context"] = {
            "intent": uctx.get("intent"),
            "self_context": uctx.get("self_context"),
            "shadow": uctx.get("shadow"),
            "effects": uctx.get("effects"),
            "architecture": uctx.get("architecture"),
            "trace_id": uctx.get("trace_id"),
            "may_authorize": False,
        }
        if uctx.get("facts") and not data.get("facts"):
            data["facts"] = uctx["facts"]
    except Exception:  # noqa: BLE001 — unified هرگز collab را نمی‌کشد
        data.setdefault("unified_context", {"may_authorize": False,
                                            "error": "unified unavailable (fail-soft)"})
    enhanced["data"] = data
    # ── Cognitive Runtime: complete run + run_id in response ──
    if _run_info:
        try:
            import hashlib as _h2
            _resp_digest = _h2.sha256(str(enhanced.get("text") or "").encode("utf-8")).hexdigest()[:16]
            _es.complete_run(_run_info["run_id"], trace_id=_run_info["trace_id"],
                             response_digest=_resp_digest)
            data = dict(enhanced.get("data") or {})
            data["run_id"] = _run_info["run_id"]
            data["trace_id"] = _run_info["trace_id"]
            enhanced["data"] = data
        except Exception:  # noqa: BLE001
            pass
    return enhanced
    """Handle callback data (button presses) through collaborator."""
    if not _is_enabled():
        return {
            "schema": "owner-console.reply.v1",
            "kind": "disabled",
            "text": "🚫 Collaborator غیرفعال است.",
            "data": {"status": "DISABLED"},
            "external_effect": False, "estimated_cost": 0,
            "send_attempted": False, "authorization": None,
        }
    base_reply = conversation.callback(data)
    enhanced = _stub_enhance(base_reply, data)
    enhanced["external_effect"] = False
    enhanced["estimated_cost"] = 0
    enhanced["send_attempted"] = False
    return enhanced
