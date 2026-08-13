# _ops/conversation_hub/service.py — Conversation Hub service entry point
# ADR-040: Hub is a façade/orchestrator — NOT a replacement for collaborator.
# It rides on top of existing modules (ask_vault, ask_brain, collaborator, etc.).
#
# Phase 1: stub adapters return placeholder text.
# Phase 2: real adapters wire to vault/brain/collab/MCP/runtime/memory/epistemic.
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .router import classify_intent
from .schemas import (
    ChatReply,
    ChatRequest,
    ProvenanceEvent,
    RouteDecision,
    SourceRef,
)

FLAG = "OCTOPUS_UNIFIED_CHAT"


def _enabled() -> bool:
    """Feature flag gate — default OFF for safety."""
    return os.environ.get(FLAG, "0") == "1"


def _now_iso() -> str:
    """Current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _make_provenance(
    *,
    message_id: str = "",
    conversation_id: str = "owner-main",
    idempotency_key: str = "",
) -> ProvenanceEvent:
    """Create a provenance event before any processing."""
    event_id = f"evt-{uuid.uuid4().hex[:12]}"
    return ProvenanceEvent(
        event_id=event_id,
        trigger_source="owner",
        initiator="telegram-miniapp",
        human_prompt_id=message_id or None,
        conversation_id=conversation_id,
        ts=_now_iso(),
    )


# ---------------------------------------------------------------------------
# Stub adapters (Phase 1 — replaced in Phase 2)
# ---------------------------------------------------------------------------

def _stub_ask(text: str, route: str) -> Dict[str, Any]:
    """Stub for ask/vault/brain/collab routes."""
    return {
        "answer": f"[stub:{route}] {text[:80]}",
        "sources": [],
    }


def _stub_runtime() -> Dict[str, Any]:
    """Stub for runtime snapshot."""
    return {
        "answer": "[stub:runtime] system status placeholder — cortex read-model not wired",
        "sources": [],
    }


def _stub_mcp(text: str) -> Dict[str, Any]:
    """Stub for MCP broker."""
    return {
        "answer": f"[stub:mcp] file search placeholder — MCP server not wired",
        "sources": [],
    }


def _stub_memory(text: str) -> Dict[str, Any]:
    """Stub for memory retrieval."""
    return {
        "answer": f"[stub:memory] recall placeholder — memory adapter not wired",
        "sources": [],
    }


def _stub_epistemic(text: str) -> Dict[str, Any]:
    """Stub for epistemic projection."""
    return {
        "answer": "[stub:epistemic] hypothesis projection not wired",
        "sources": [],
    }


def _stub_guide(text: str) -> Dict[str, Any]:
    """Stub for owner guidance."""
    return {
        "answer": f"[stub:guide] guidance placeholder — owner guidance not wired",
        "sources": [],
    }


def _stub_propose(text: str) -> Dict[str, Any]:
    """Stub for proposal queue."""
    return {
        "answer": "[stub:propose] proposal queued — queue adapter not wired",
        "sources": [],
        "proposals": [],
    }


# ---------------------------------------------------------------------------
# Phase 2-lite adapters (2026-08-13 — connected to the now-healthy central path)
# All fail-soft: any exception → fall back to the stub + honest limitation.
# None of these can execute anything: observe + propose only (ADR-040 §hard).
# ---------------------------------------------------------------------------

def _ensure_paths() -> None:
    ops = _ops_path()
    for p in (ops, str(Path(ops) / "owner_console"),
              str(Path(ops) / "cortex"), str(Path(ops) / "memory")):
        if p not in sys.path:
            sys.path.insert(0, p)


def _ops_path() -> str:
    return str(Path(__file__).resolve().parent.parent)


def _real_collab(text: str, _rd: RouteDecision) -> Dict[str, Any]:
    """ask/collab → collaborator.handle — the central chat path (vault→brain→
    collab escalation internally, DeepSeek-backed via the 2026-08-13
    model_router fix). Draft-only, read-only, never executes."""
    try:
        _ensure_paths()
        from owner_console import collaborator
        reply = collaborator.handle(text)
        return {
            "answer": str(reply.get("text") or ""),
            "sources": [],
            "_kind": reply.get("kind"),
            "_model_source": reply.get("model_source"),
        }
    except Exception as exc:  # noqa: BLE001 — fail-soft
        return {"answer": _stub_ask(text, "ask")["answer"], "sources": [],
                "_error": type(exc).__name__}


def _real_runtime(_text: str, _rd: RouteDecision) -> Dict[str, Any]:
    """runtime → status.runtime_truth() — read-only snapshot of live state."""
    try:
        _ensure_paths()
        from owner_console import status
        return {"answer": status.runtime_truth(), "sources": []}
    except Exception as exc:  # noqa: BLE001 — fail-soft
        return {"answer": _stub_runtime()["answer"], "sources": [],
                "_error": type(exc).__name__}


def _real_memory(text: str, _rd: RouteDecision) -> Dict[str, Any]:
    """memory → owner_recall.recall_for_owner_ask — cite-only retrieval."""
    try:
        _ensure_paths()
        import owner_recall
        facts = owner_recall.recall_for_owner_ask(text, limit=4) or []
        if not facts:
            return {"answer": "چیزی برای این سؤال در حافظه نیافتم (خالی صادق).",
                    "sources": []}
        lines = []
        for f in facts[:4]:
            prev = str(f.get("content_preview") or f.get("mkey") or "")[:160]
            src = str(f.get("source_path") or f.get("provenance") or "?")
            lines.append(f"· {prev}  [{src}]")
        return {
            "answer": "حافظه cite-only است (may_authorize=false):\n" + "\n".join(lines),
            "sources": [{"path": str(f.get("source_path") or f.get("provenance") or "?")}
                        for f in facts[:4] if f.get("source_path") or f.get("provenance")],
        }
    except Exception as exc:  # noqa: BLE001 — fail-soft
        return {"answer": _stub_memory(text)["answer"], "sources": [],
                "_error": type(exc).__name__}


def _real_guide(text: str, _rd: RouteDecision) -> Dict[str, Any]:
    """guide → owner_guidance.effective() — read-only last-wins fold of the
    owner's standing guidance (focus/think_every_n/paused)."""
    try:
        _ensure_paths()
        import owner_guidance
        eff = owner_guidance.effective() or {}
        if not eff:
            return {
                "answer": "دستورِ ایستاده‌ای در owner-guidance ثبت نشده — راهنماییِ فعلی خالی است.",
                "sources": [],
            }
        parts = [f"· focus: {eff['focus']}" if eff.get("focus") else None,
                 f"· think_every_n: {eff['think_every_n']}" if eff.get("think_every_n") else None,
                 f"· paused: {eff['paused']}" if eff.get("paused") else None]
        return {
            "answer": "دستورِ ایستادهٔ مالک (owner-guidance):\n"
                      + "\n".join(p for p in parts if p),
            "sources": [{"path": "cortex/owner_guidance.py"}],
        }
    except Exception as exc:  # noqa: BLE001 — fail-soft
        return {"answer": _stub_guide(text)["answer"], "sources": [],
                "_error": type(exc).__name__}


def _real_epistemic(text: str, _rd: RouteDecision) -> Dict[str, Any]:
    """epistemic → projection فقط‌خواندنی از کابینِ epistemics (ADR-039).

    parallel advisory (نه inline به چت): هیچ claimی ساخته/اجرا نمی‌کند؛ فقط یک
    read-only view از receipt-chain + invariants + labelها می‌دهد. هرگز may_execute.
    fail-soft → stub با limitation صادق."""
    try:
        _ensure_paths()
        import epistemics.invariants as _inv
        import epistemics.policy as _pol
        from epistemics.receipt_store import ReceiptStore
        cfg = _pol.load_policy()
        chain = ReceiptStore().verify()
        structural = _inv.structural_invariants()
        lines = [
            f"کابینِ epistemic (ADR-039، {cfg.max_authority}-only، sandbox={cfg.sandbox_profile}):",
            f"· receipt-chain: {'ok' if chain.ok else 'BROKEN @'+str(chain.broken_at)} "
            f"({chain.n_records} records)",
            f"· invariants: {_inv.count()} ({len(structural)} structural-enforced)",
            f"· world_mode labels در تمامِ claim/receipt حفظ می‌شود (invariant #4)",
            f"· may_execute همیشه False — آزمون واقعی فقط در sandbox_runner، نه چت",
            f"· status: {'ACCEPTED' if not cfg.default_off else 'default-OFF'} "
            f"(EPISTEMIC_TESTS={os.environ.get('EPISTEMIC_TESTS', '0')})",
        ]
        return {
            "answer": "\n".join(lines),
            "sources": [{"path": "epistemics/schemas.py"},
                        {"path": "epistemics/invariants.py"}],
        }
    except Exception as exc:  # noqa: BLE001 — fail-soft
        return {"answer": _stub_epistemic(text)["answer"], "sources": [],
                "_error": type(exc).__name__}


def _real_mcp(text: str, _rd: RouteDecision) -> Dict[str, Any]:
    """mcp → MCP broker (۳ ابزارِ read-only: search_hybrid/read_file_slice/list_tree).

    کد/فایلِ پرسیده‌شده را در repo جستجو می‌کند و نتایج را به‌عنوان SourceRef برمی‌گرداند.
    read-only — هیچ فایلی نمی‌نویسد. مرورگر هرگز MCP/stdio را نمی‌بیند (پشت gateway)."""
    try:
        ops = _ops_path()
        mcp_dir = str(Path(ops).parent / "_ops" / "octopus_mcp")
        # server.py در _ops/octopus_mcp/ است
        mcp_dir = str(Path(ops) / "octopus_mcp")
        if mcp_dir not in sys.path:
            sys.path.insert(0, mcp_dir)
        import server as _mcp  # noqa: WPS433
        # query را از متن استخراج کن (بعد از کلیدواژه‌های فایل/کد)
        q = str(text or "").strip()
        res = _mcp.t_search_hybrid(query=q[:80], path=".", max_results=6)
        hits = res.get("results") or []
        if not hits:
            return {"answer": f"برای «{q[:60]}» چیزی در repo نیافتم (خالی صادق).",
                    "sources": []}
        lines = [f"در repo {len(hits)} مورد یافتم:"]
        srcs = []
        for h in hits[:6]:
            p = str(h.get("path") or h.get("file") or "?")
            snip = str(h.get("preview") or h.get("line") or "")[:120]
            lines.append(f"· {p}" + (f"\n  {snip}" if snip else ""))
            srcs.append({"path": p})
        return {"answer": "\n".join(lines), "sources": srcs}
    except Exception as exc:  # noqa: BLE001 — fail-soft
        return {"answer": _stub_mcp(text)["answer"], "sources": [],
                "_error": type(exc).__name__}


# انواعِ proposal مجاز از چت (محرمانه/پول/ارسال ممنوع — autonomy_grant هم‌راستا).
_SAFE_PROPOSE_KINDS = frozenset({"report", "modify_file", "deduplicate", "archive"})
_DENY_RE = None  # lazy


def _real_propose(text: str, _rd: RouteDecision) -> Dict[str, Any]:
    """propose → queue-only: پیشنهاد را در صفِ تأییدِ مالک می‌نویسد (هرگز اجرا نمی‌کند).

    autonomy: فقط انواعِ امن (report/modify_file/deduplicate/archive)؛ متنِ حاوی
    pay/send/commit/secret/PII رد می‌شود. external_effect=False (نوشتن در صفِ محلی،
    نه اثرِ بیرونی). may_authorize=False (تأییدِ جداگانه لازم)."""
    global _DENY_RE
    try:
        import re
        if _DENY_RE is None:
            _DENY_RE = re.compile(
                r"pay|payment|invoice|money|send|publish|apply|merge|commit|"
                r"secret|token|password|PII|flag|delete|remove", re.IGNORECASE)
        q = str(text or "").strip()
        if not q or _DENY_RE.search(q):
            return {
                "answer": ("این پیشنهاد شامل کلیدواژهٔ محرمانه/خطرناک است یا خالی است — "
                           "در صف ننوشتم. فقط انواعِ امن (report/modify_file/deduplicate/"
                           "archive) بدون pay/send/secret/PII."),
                "sources": [], "proposals": [],
            }
        ops = _ops_path()
        mcp_dir = str(Path(ops) / "octopus_mcp")
        if mcp_dir not in sys.path:
            sys.path.insert(0, mcp_dir)
        import server as _mcp  # noqa: WPS433
        # نوعِ پیش‌فرض report (امن‌ترین)؛ summary از متن
        result = _mcp.t_propose_action(
            kind="report", summary=q[:48], detail=q[:400])
        return {
            "answer": ("پیشنهاد در صفِ تأییدِ مالک نوشته شد (queue-only؛ اجرا نشد).\n"
                       f"· صف: {result.get('queued')}\n"
                       "· تأیید نهایی با مالک طبق _octopus/config/policy.yaml"),
            "sources": [{"path": "_octopus/queue/pending"}],
            "proposals": [{"queued": result.get("queued"), "kind": "report",
                           "status": "pending"}],
        }
    except Exception as exc:  # noqa: BLE001 — fail-soft
        return {"answer": _stub_propose(text)["answer"], "sources": [],
                "_error": type(exc).__name__}


# Route → adapter dispatch (Phase 2-lite + Phase 2 complete: all routes real)
_ADAPTERS = {
    "ask": _real_collab,
    "vault": _real_collab,
    "brain": _real_collab,
    "collab": _real_collab,
    "runtime": _real_runtime,
    "memory": _real_memory,
    "guide": _real_guide,
    "epistemic": _real_epistemic,
    "mcp": _real_mcp,
    "propose": _real_propose,
}


def _call_adapter(route: str, text: str, decision: RouteDecision) -> Dict[str, Any]:
    """Dispatch to the appropriate adapter (real Phase 2-lite / honest stub)."""
    adapter = _ADAPTERS.get(route)
    if adapter is None:
        return _stub_ask(text, route)
    try:
        return adapter(text, decision)
    except Exception:
        return {"answer": f"[error:{route}] adapter raised an exception", "sources": []}


def handle(
    req: ChatRequest | dict,
    *,
    state_dir: Optional[str] = None,
) -> ChatReply:
    """Main entry point for the Conversation Hub.

    Accepts a ChatRequest (or raw dict that validates as one).
    Returns a ChatReply with unified schema.

    Steps:
      1. Validate request schema
      2. Create provenance event (before any processing)
      3. Route intent via deterministic router
      4. Call adapter (Phase 2-lite: real for ask/runtime/memory/guide,
         honest stub for mcp/epistemic/propose)
      5. Compose unified reply
      6. Attach provenance + limitations
      7. Return ChatReply
    """
    # 1. Validate / coerce request
    if not isinstance(req, ChatRequest):
        req = ChatRequest(**req)  # may raise ValidationError

    # 2. Provenance event (created BEFORE processing — cannot retroactively
    #    claim a chat was self-initiated)
    prov = _make_provenance(
        message_id=req.message_id,
        conversation_id=req.conversation_id,
        idempotency_key=req.idempotency_key,
    )

    # 3. Route intent
    decision = classify_intent(req.text, mode=req.mode)

    # 4. Call adapter
    result = _call_adapter(decision.route, req.text, decision)

    # 5. Compose unified reply
    sources = [
        SourceRef(path=s) if isinstance(s, str) else s
        for s in result.get("sources", [])
    ]

    # Epistemic status: only meaningful when a Claim+Plan+Receipt is evaluated.
    # The Hub's epistemic route is a READ-ONLY projection (not a claim evaluation),
    # so it is honestly "not_applicable" — never fake "supported/inconclusive".
    epistemic = "not_applicable"

    # Honest limitations: stubs say "not wired"; real adapters note the
    # fail-soft boundary; every reply carries at least one limitation.
    if result.get("_error"):
        limitations = [
            f"adapter failed ({result['_error']}) → deterministic fallback used",
        ]
    elif decision.route in ("mcp", "propose"):
        limitations = ["Phase 2 adapter — read-only (mcp) / queue-only (propose), no execution (ADR-040)"]
    else:
        limitations = ["observe-only adapter — draft reply, no execution (ADR-040)"]

    reply = ChatReply(
        ok=True,
        answer=result.get("answer", ""),
        route=decision.route,
        epistemic_status=epistemic,
        confidence=decision.confidence,
        sources=sources,
        provenance_event_id=prov.event_id,
        may_authorize=False,
        external_effect=False,
        limitations=limitations,
    )

    return reply
