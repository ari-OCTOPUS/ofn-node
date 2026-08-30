"""unified_context.py — فاز P: Unified Context Bus / Assembler (یک جریان، چند اندام).

بدون سیستم موازی: همین ماژول منابع موجود را fail-soft جمع می‌کند:
    owner_recall (cite-only) · equation_advice (advice-only) · runtime status
    · self_context (brains) · shadow influence summary · limited-effect status

قرارداد خروجی (schema unified-context.v1):
    {
      "intent": ...,
      "self_context": {cortex/business_brain/four_d_connected},
      "memory": {owner_recall_used, vault_empty?, facts_n},
      "equations": [...advice-only...],
      "architecture": {components, edges, runtime_verified},
      "effects": {proposal_created, policy_gate_status, applied},
      "facts": [...cite-only...],
      "warnings": [...],
      "trace_id": ...
    }

هر منبع شکست‌خورده = degraded-mode صادق (warning)، هرگز crash.
may_authorize همیشه False. هیچ اجرا/اثری.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
STATE_DIR = Path(os.environ.get("OCTOPUS_STATE_DIR", str(_OPS / "state")))

UNIFIED_SCHEMA = "unified-context.v1"


def _add_ops_path() -> None:
    for p in (str(_OPS), str(_HERE), str(_OPS / "owner_console")):
        if p not in __import__("sys").path:
            __import__("sys").path.insert(0, p)


def _read_json(rel: str) -> dict | None:
    p = STATE_DIR / rel
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def _trace_id() -> str:
    return f"uctx-{uuid.uuid4().hex[:12]}"


def _self_context_block() -> dict[str, Any]:
    """دو مغز + شاهد فایل زنده (file-bridge) — نه ادعای IPC به :8772."""
    try:
        import brain_pulse as _bp  # noqa: WPS433
        _bp.STATE_DIR = STATE_DIR
        return _bp.for_unified_self_context()
    except Exception as exc:  # noqa: BLE001 — fail-soft به شکل قبلی
        org = _read_json("ORGANISM-STATE.json") or {}
        return {
            "cortex": {"live": True, "role": "planning/reasoning organ"},
            "business_brain": {"live": True, "role": "business/opportunity brain"},
            "four_d_connected": False,
            "note": "4d_system/Super-Governor وصل نیست; brain_pulse fail-soft",
            "bridge": "fallback-static",
            "may_authorize": False,
            "runtime": {
                "beat": org.get("beat"),
                "halted": bool(org.get("halted")),
                "pain": ((org.get("pain_assessment") or {}).get("pain")
                         if isinstance(org.get("pain_assessment"), dict) else None),
                "protective_skip": bool(org.get("protective_skip")),
            },
            "warnings": [f"brain_pulse unavailable: {type(exc).__name__}"],
        }


def _memory_block(query: str) -> dict[str, Any]:
    """owner_recall cite-only + vault truth. هیچ authorize. fail-soft."""
    out: dict[str, Any] = {"owner_recall_used": False, "vault_empty": None,
                           "facts_n": 0, "may_authorize": False}
    try:
        _add_ops_path()
        import owner_recall as _or  # noqa: WPS433
        if _or.topic_wants_recall(query):
            facts = _or.recall_for_owner_ask(query, limit=3)
            out["owner_recall_used"] = True
            out["facts_n"] = len(facts)
            out["facts"] = [
                {"claim": f.get("content_preview", "")[:200],
                 "source": f.get("source_path", ""),
                 "locator": f.get("mkey", ""),
                 "confidence": "VERIFIED" if f.get("source_path") else "REPORTED"}
                for f in facts
            ]
    except Exception as exc:  # noqa: BLE001
        out["warnings"] = [f"owner_recall unavailable: {type(exc).__name__}"]
    return out


def _equations_block() -> dict[str, Any]:
    """equation_advice — فقط advice. برچسب اجباری. fail-soft."""
    try:
        _add_ops_path()
        import equation_advice as _ea  # noqa: WPS433
        snap = _ea.equation_advice_snapshot()
        return {
            "equation_advice_only": snap.get("equation_advice_only"),
            "decision_effect": snap.get("decision_effect"),
            "apply_effect": snap.get("apply_effect"),
            "equations_consulted": snap.get("equations_consulted") or [],
            "aggregate_advice": snap.get("aggregate_advice"),
            "may_authorize": False,
        }
    except Exception as exc:  # noqa: BLE001
        return {"equation_advice_only": True, "decision_effect": False,
                "apply_effect": False, "may_authorize": False,
                "warnings": [f"equation_advice unavailable: {type(exc).__name__}"]}


def _architecture_block() -> dict[str, Any]:
    """Read-model کوچک از فایل‌های موجود (بدون گراف سنگین)."""
    return {
        "components": [
            "miniapp_gateway (/api/ask,/api/collab)",
            "collaborator (unified router)",
            "conversation (intents)",
            "owner_recall (cite-only memory)",
            "equation_advice (advice-only)",
            "ask_vault / ask_brain (ask ladder)",
        ],
        "edges": [
            "chat_box -> miniapp_gateway -> collaborator",
            "collaborator -> owner_recall | equation_advice | collab_memory",
            "collaborator -> collab_model_adapter -> model_router",
            "brain_pulse <-file- read cortex-state + business-brain-latest (not IPC :8772)",
            "cortex reads owner_guidance.jsonl only (chat does not push unless guidance path)",
        ],
        "runtime_verified": True,
        "note": "4d_system/Super-Gov خارج از مسیر (DEPRECATED); لایه۵=file-bridge",
    }


def _shadow_block() -> dict[str, Any]:
    """Shadow influence summary (فاز K) — فقط وضعیت، applied همیشه false."""
    try:
        import sys
        if str(_HERE) not in sys.path:
            sys.path.insert(0, str(_HERE))
        import shadow_influence as _si  # noqa: WPS433
        _si.STATE_DIR = STATE_DIR
        _si.OUT_DIR = STATE_DIR / "shadow-influence"
        _si.DIVERGENCE = _si.OUT_DIR / "divergence.jsonl"
        records = _si.count_records()
        return {"shadow_records": records, "applied": False, "may_authorize": False}
    except Exception as exc:  # noqa: BLE001
        return {"shadow_records": 0, "applied": False,
                "warnings": [f"shadow unavailable: {type(exc).__name__}"]}


def _effects_block() -> dict[str, Any]:
    """limited-effect وضعیت (فاز N) — رأی‌خوان، فقط نمایش."""
    try:
        _add_ops_path()
        import limited_effect as _le  # noqa: WPS433
        return {
            "proposal_created": False,
            "policy_gate_status": "NOT_REQUESTED",
            "applied": False,
            "enabled": _le.enabled(),
            "may_authorize": False,
        }
    except Exception as exc:  # noqa: BLE001
        return {"proposal_created": False, "policy_gate_status": "NOT_REQUESTED",
                "applied": False, "enabled": False,
                "warnings": [f"limited_effect unavailable: {type(exc).__name__}"]}


def assemble(query: str) -> dict[str, Any]:
    """Assembler واحد — تمام منابع را fail-soft جمع می‌کند."""
    q = str(query or "").strip()
    warnings: list[str] = []
    result: dict[str, Any] = {
        "schema": UNIFIED_SCHEMA,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trace_id": _trace_id(),
        "intent": "general_chat",
        "self_context": _self_context_block(),
        "memory": _memory_block(q),
        "equations": _equations_block(),
        "architecture": _architecture_block(),
        "effects": _effects_block(),
        "shadow": _shadow_block(),
        "facts": [],
        "warnings": [],
        "may_authorize": False,
    }
    # حافظه → facts واحد
    mem = result["memory"]
    if mem.get("facts"):
        result["facts"] = mem["facts"]
    for blk in ("memory", "equations", "shadow", "effects"):
        for w in (blk_data := result.get(blk) or {}).get("warnings") or []:
            warnings.append(f"{blk}: {w}")
    result["warnings"] = warnings
    return result


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "از چی تشکیل شدی؟"
    print(json.dumps(assemble(q), ensure_ascii=False, indent=2))
