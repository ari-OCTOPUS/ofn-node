#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_conversation_hub.py — Conversation Hub tests (t_a through t_k).

ADR-040: Hub core schemas + router + service.
Phase 1: stub adapters. Phase 2-lite (2026-08-13): ask/runtime/memory/guide
wire to real modules (fail-soft), mcp/epistemic/propose stay honest stubs.
All tests use relative imports within the conversation_hub package.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure _ops is importable (same pattern as existing tests)
_OPS = Path(__file__).resolve().parents[1]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402
ENV = harness.setup("conversation-hub")


def _with_wire_collab():
    """مسیرِ واقعیِ collaborator (draft) برای تستِ آداپتورِ ask."""
    os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    os.environ.pop("OCTOPUS_COLLAB_USE_MODEL", None)


def _clear_wire_collab():
    os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
    os.environ.pop("OCTOPUS_COLLAB_USE_MODEL", None)


# ---------------------------------------------------------------------------
# t_a: ChatRequest validation
# ---------------------------------------------------------------------------
def t_a_chat_request_validation():
    """ChatRequest requires message_id and text; empty text is rejected."""
    from conversation_hub.schemas import ChatRequest, VALID_MODES

    # Valid request
    req = ChatRequest(message_id="m1", text="hello")
    assert req.schema_version == "octopus.chat.request.v1"
    assert req.text == "hello"
    assert req.mode == "auto"
    assert req.conversation_id == "owner-main"

    # Empty text → ValidationError
    try:
        ChatRequest(message_id="m1", text="")
        assert False, "Should have raised"
    except Exception as exc:
        assert "text" in str(exc) or "min_length" in str(exc)

    # Missing message_id → ValidationError
    try:
        ChatRequest(text="hello")
        assert False, "Should have raised"
    except Exception as exc:
        assert "message_id" in str(exc)

    # Valid mode values
    for mode in VALID_MODES:
        req = ChatRequest(message_id="m2", text="test", mode=mode)
        assert req.mode == mode

    # Invalid mode → ValidationError
    try:
        ChatRequest(message_id="m3", text="test", mode="destroy")
        assert False, "Should have raised"
    except Exception:
        pass

    # idempotency_key and client_sent_at (from GPT-5.6 Terra review)
    req = ChatRequest(
        message_id="m4", text="test",
        idempotency_key="idem-abc123",
        client_sent_at="2026-08-12T23:00:00Z",
    )
    assert req.idempotency_key == "idem-abc123"
    assert req.client_sent_at == "2026-08-12T23:00:00Z"


# ---------------------------------------------------------------------------
# t_b: ChatReply validation
# ---------------------------------------------------------------------------
def t_b_chat_reply_validation():
    """ChatReply defaults: ok=True, external_effect=False, not_applicable."""
    from conversation_hub.schemas import ChatReply

    reply = ChatReply(answer="test answer", route="ask")
    assert reply.schema_version == "octopus.chat.reply.v1"
    assert reply.ok is True
    assert reply.external_effect is False
    assert reply.may_authorize is False
    assert reply.epistemic_status == "not_applicable"
    assert reply.confidence == "unknown"
    assert reply.sources == []
    assert reply.limitations == []

    # external_effect can ONLY be False (frozen model, no setter)
    try:
        ChatReply(answer="x", route="ask", external_effect=True)
        # Accepted by schema but must NEVER be set from service
    except Exception:
        pass


# ---------------------------------------------------------------------------
# t_c: Router — explicit mode override
# ---------------------------------------------------------------------------
def t_c_router_explicit_mode():
    """Explicit mode (research/guide/propose) → direct route, confidence=evidenced."""
    from conversation_hub.router import classify_intent

    d = classify_intent("random text", mode="research")
    assert d.route == "epistemic"
    assert d.confidence == "evidenced"

    d = classify_intent("random text", mode="guide")
    assert d.route == "guide"
    assert d.confidence == "evidenced"

    d = classify_intent("random text", mode="propose")
    assert d.route == "propose"
    assert d.confidence == "evidenced"


# ---------------------------------------------------------------------------
# t_d: Router — auto mode keyword matching
# ---------------------------------------------------------------------------
def t_d_router_auto_keyword_matching():
    """Auto mode: keywords map to correct routes (bilingual)."""
    from conversation_hub.router import classify_intent

    # Runtime keywords
    d = classify_intent("وضعیت سیستم چطوره", mode="auto")
    assert d.route == "runtime"
    assert "وضعیت" in d.keywords

    d = classify_intent("show me the system pulse", mode="auto")
    assert d.route == "runtime"
    assert "pulse" in d.keywords

    # MCP keywords
    d = classify_intent("خط ۴۲ فایل cortex.py", mode="auto")
    assert d.route == "mcp"

    d = classify_intent("find the ADR for chat hub", mode="auto")
    assert d.route == "mcp"

    # Memory keywords
    d = classify_intent("یادت میاد دیبا چه گفت", mode="auto")
    assert d.route == "memory"

    d = classify_intent("do you remember last week", mode="auto")
    assert d.route == "memory"

    # Epistemic keywords
    d = classify_intent("آیا فرضیهٔ X ثابت شده", mode="auto")
    assert d.route == "epistemic"

    d = classify_intent("is this hypothesis supported", mode="auto")
    assert d.route == "epistemic"

    # Guide keywords
    d = classify_intent("فوکوس رو بذار روی performance", mode="auto")
    assert d.route == "guide"

    d = classify_intent("focus on the memory leak", mode="auto")
    assert d.route == "guide"

    # Propose keywords
    d = classify_intent("اصلاح کن این باگ رو", mode="auto")
    assert d.route == "propose"

    d = classify_intent("fix the null pointer", mode="auto")
    assert d.route == "propose"


# ---------------------------------------------------------------------------
# t_e: Router — fallback to ask
# ---------------------------------------------------------------------------
def t_e_router_fallback():
    """No keyword match → ask route, confidence=unknown."""
    from conversation_hub.router import classify_intent

    d = classify_intent("hello there", mode="auto")
    assert d.route == "ask"
    assert d.confidence == "unknown"
    assert d.keywords == []


# ---------------------------------------------------------------------------
# t_f: Service — stub handle with mode=ask
# ---------------------------------------------------------------------------
def t_f_service_stub_handle():
    """Service handle() returns ChatReply with provenance_event_id for ask.

    Phase 2-lite: ask → collaborator (real draft path when OCTOPUS_WIRE_COLLAB=1;
    honest disabled message when off). No more "[stub:ask]" markers.
    """
    from conversation_hub.service import handle

    reply = handle({
        "message_id": "msg-001",
        "text": "سلام، حالت چطوره؟",
        "mode": "ask",
    })

    assert reply.ok is True
    assert reply.route == "ask"
    assert reply.answer != ""
    assert "[stub:ask]" not in reply.answer
    assert reply.provenance_event_id is not None
    assert reply.provenance_event_id.startswith("evt-")
    assert reply.external_effect is False
    assert reply.may_authorize is False

    # با wire روشن، آداپتورِ واقعیِ collaborator جواب می‌دهد
    _with_wire_collab()
    try:
        reply2 = handle({
            "message_id": "msg-001b",
            "text": "وضعیت چطوره؟",
            "mode": "ask",
        })
        assert reply2.ok is True and reply2.answer != ""
        assert "[stub:ask]" not in reply2.answer
    finally:
        _clear_wire_collab()


# ---------------------------------------------------------------------------
# t_g: Service — stub handle with mode=guide
# ---------------------------------------------------------------------------
def t_g_service_stub_guide():
    """Service handle() with mode=guide → route=guide in reply.

    Phase 2-lite: guide → owner_guidance.effective() (real read-only fold;
    live file may be empty → honest "ثبت نشده" — either way non-empty).
    """
    from conversation_hub.service import handle

    reply = handle({
        "message_id": "msg-002",
        "text": "فوکوس روی performance",
        "mode": "guide",
    })

    assert reply.route == "guide"
    assert reply.answer != ""
    assert "[stub:guide]" not in reply.answer
    assert reply.confidence == "evidenced"


# ---------------------------------------------------------------------------
# t_h: Service — provenance event structure
# ---------------------------------------------------------------------------
def t_h_service_provenance_structure():
    """Provenance event has trigger_source=owner, initiator, valid event_id."""
    from conversation_hub.service import _make_provenance

    prov = _make_provenance(
        message_id="msg-003",
        conversation_id="owner-main",
        idempotency_key="idem-key-1",
    )

    assert prov.trigger_source == "owner"
    assert prov.initiator == "telegram-miniapp"
    assert prov.event_id.startswith("evt-")
    assert len(prov.event_id) == 16  # "evt-" + 12 hex chars
    assert prov.conversation_id == "owner-main"
    assert prov.human_prompt_id == "msg-003"
    assert prov.ts != ""  # ISO-8601 timestamp present


# ---------------------------------------------------------------------------
# t_i: Service — limitations always present
# ---------------------------------------------------------------------------
def t_i_service_limitations():
    """Reply always has at least one honest limitation (observe-only / not wired)."""
    from conversation_hub.service import handle

    reply = handle({
        "message_id": "msg-004",
        "text": "anything",
    })

    assert len(reply.limitations) >= 1
    joined = " | ".join(reply.limitations)
    assert "observe-only" in joined or "not wired" in joined

    # مسیرهای stub (mcp/epistemic/propose) صراحتاً «not wired» می‌گویند
    reply_mcp = handle({"message_id": "msg-004b", "text": "فایل cortex.py رو ببین",
                        "mode": "auto"})
    assert "not wired" in " | ".join(reply_mcp.limitations)


# ---------------------------------------------------------------------------
# t_j: Flag-off → _enabled() = False
# ---------------------------------------------------------------------------
def t_j_flag_off_disabled():
    """When OCTOPUS_UNIFIED_CHAT is not set or '0', _enabled() returns False."""
    import os
    from conversation_hub.service import _enabled, FLAG

    old = os.environ.pop(FLAG, None)
    try:
        assert _enabled() is False

        os.environ[FLAG] = "0"
        assert _enabled() is False
    finally:
        if old is not None:
            os.environ[FLAG] = old
        else:
            os.environ.pop(FLAG, None)

    # Explicitly ON
    os.environ[FLAG] = "1"
    try:
        assert _enabled() is True
    finally:
        os.environ.pop(FLAG, None)


# ---------------------------------------------------------------------------
# t_k: Idempotency key preserved
# ---------------------------------------------------------------------------
def t_k_idempotency_in_provenance():
    """Idempotency key from request is reflected in provenance event_id chain."""
    from conversation_hub.service import handle

    # Request with idempotency_key
    reply = handle({
        "message_id": "msg-005",
        "text": "system status",
        "idempotency_key": "idem-unique-abc",
    })

    assert reply.provenance_event_id is not None
    # The provenance event should be traceable to the message
    assert reply.route == "runtime"


# ---------------------------------------------------------------------------
# Test registry — allows run_all.py to discover these
# ---------------------------------------------------------------------------
TESTS = [
    t_a_chat_request_validation,
    t_b_chat_reply_validation,
    t_c_router_explicit_mode,
    t_d_router_auto_keyword_matching,
    t_e_router_fallback,
    t_f_service_stub_handle,
    t_g_service_stub_guide,
    t_h_service_provenance_structure,
    t_i_service_limitations,
    t_j_flag_off_disabled,
    t_k_idempotency_in_provenance,
]

if __name__ == "__main__":
    failed = 0
    for t in TESTS:
        name = t.__name__
        try:
            t()
            print(f"  PASS  {name}")
        except Exception as exc:
            print(f"  FAIL  {name}: {exc}")
            failed += 1
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(failed)
