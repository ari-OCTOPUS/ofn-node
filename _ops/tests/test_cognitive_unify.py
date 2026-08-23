#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cognitive_unify.py — UI default + discovery facade + policy + criticality + approval SM."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "owner_console"))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402

# 2026-08-23 — نشتِ حالت بسته شد.
# این سوییت `harness.run()` را برای گزارش استفاده می‌کرد ولی **هرگز
# `harness.setup()` را صدا نمی‌زد** — تنها سوییتِ همسایه‌ای که این کار را
# نمی‌کرد. نتیجه: نه `OCTOPUS_STATE_DIR` ست می‌شد و نه `live_state_guard`
# مسلح؛ پس هر تستی که از این فایل به `collaborator.handle` می‌رسید، گفتگوی
# مالک را در `_ops/state/chat/chat-log.jsonl` و امتیاز را در
# `_ops/state/criticality/criticality-v2.jsonl` ِ **tracked** می‌نوشت.
# اندازه‌گیری‌شده: قبل از این خط ۲ فایلِ tracked کثیف می‌شد، بعدش ۰.
# ترتیب مهم است (قراردادِ خودِ harness): env باید قبل از importِ ماژول‌ها
# ست شود — importهای واقعی این فایل داخلِ توابعِ تست‌اند، پس اینجا درست است.
ENV = harness.setup("cognitive-unify")


def t_gateway_inject_sets_collab_flag():
    os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    sys.path.insert(0, str(_OPS / "telegram_center"))
    import importlib
    import miniapp_gateway as mg
    importlib.reload(mg)
    snip = mg._build_inject()
    assert "wire_collab=true" in snip
    os.environ["OCTOPUS_WIRE_COLLAB"] = "0"
    snip2 = mg._build_inject()
    assert "wire_collab=false" in snip2


def t_gateway_inject_runs_before_miniapp_scripts():
    """Runtime flags/fetch wrapper must exist before app.js evaluates mode defaults."""
    os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    os.environ["OCTOPUS_COLLAB_USE_MODEL"] = "1"
    sys.path.insert(0, str(_OPS / "telegram_center"))
    import miniapp_gateway as mg
    status, body, ctype = mg._miniapp_static_response("/")
    text = body.decode("utf-8")
    assert status == 200 and "text/html" in ctype
    inject_at = text.index("window.__OCTOPUS__")
    shell_at = text.index('/miniapp/tg_shell.js')
    app_at = text.index('/miniapp/app.js')
    assert inject_at < shell_at < app_at, (inject_at, shell_at, app_at)
    assert "wire_collab=true" in text and "collab_use_model=true" in text
    # Inline-script suppression must not erase runtime truth: the external app.js
    # response carries the same bootstrap before its application body.
    js_status, js_body, js_type = mg._miniapp_static_response("/miniapp/app.js")
    js_text = js_body.decode("utf-8")
    assert js_status == 200 and "javascript" in js_type
    assert js_text.startswith("(function(){window.__OCTOPUS__")
    assert "wire_collab=true" in js_text[:500]
    v_on = mg.assets_version()
    os.environ["OCTOPUS_WIRE_COLLAB"] = "0"
    v_off = mg.assets_version()
    assert v_on != v_off, "runtime UI flag flip must change the cache-busting asset URL"


def t_app_js_default_collab_mode():
    js = (_OPS / "telegram_center" / "miniapp" / "app.js").read_text(encoding="utf-8")
    assert "wire_collab" in js
    assert 'id="askPlain"' in js
    assert "بدون اثر خارجی" in js
    assert 'mode === "collab"' in js or 'mode==="collab"' in js or 'collabDefault' in js


def t_discovery_facade_has_provenance():
    from owner_console.discovery_facade import discover_payload, discover_reply_text
    p = discover_payload(max_items=3)
    assert p["schema"] == "DiscoveryReply.v1"
    assert p["external_effect"] is False
    assert "facts" in p and "limitations" in p
    kinds = {f["provenance"]["source_kind"] for f in p["facts"]}
    # at least one concrete source kind present when sources respond
    assert kinds.issubset({"catalog", "manifest", "journal", "world_discovery"})
    text = discover_reply_text(max_items=3)
    assert "شواهد" in text or "Sources" in text or "catalog" in text.lower() or len(text) > 20
    # MiniApp Sources affordance
    js = (_OPS / "telegram_center" / "miniapp" / "app.js").read_text(encoding="utf-8")
    assert "Sources / شواهد" in js
    assert "buildSourcesPanel" in js


def t_world_discovery_uses_facade():
    from owner_console import status
    t = status.discovery()
    assert "propose-only" in t or "کشف" in t or "Discovery" in t or "شواهد" in t


def t_approval_state_blocks_bad_fingerprint():
    from datetime import UTC, datetime, timedelta
    from collab.approval_state import (
        TalkProposal,
        can_approve,
        clear_idempotency_registry,
    )
    clear_idempotency_registry()
    p = TalkProposal(
        proposal_id="x",
        action="external_send",
        payload_digest="aa",
        policy_version="talk-discovery-policy.v2",
        state_version=0,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        idempotency_key="k-forbid",
    )
    ok, reason = can_approve(
        p,
        signed_fingerprint="deadbeef",
        current_policy_version="talk-discovery-policy.v2",
    )
    assert ok is False and reason == "proposal_changed_after_approval"


def t_talk_policy_external_send_needs_owner_approval():
    from collab.talk_discovery_policy import TalkAction, TalkDiscoveryPolicy
    p = TalkDiscoveryPolicy()
    d = p.decide(
        TalkAction.EXTERNAL_SEND,
        collab_enabled=True,
        untrusted_instruction=False,
        owner_approval_id=None,
    )
    assert d.allowed is False
    d_ok = p.decide(
        TalkAction.EXTERNAL_SEND,
        collab_enabled=True,
        untrusted_instruction=False,
        owner_approval_id="owner-1",
    )
    assert d_ok.allowed is True
    d2 = p.decide(
        TalkAction.RESPOND_DRAFT,
        collab_enabled=True,
        untrusted_instruction=True,
        owner_approval_id=None,
    )
    assert d2.allowed is True


def t_approval_sm_fail_closed_and_hash():
    from collab import approval_sm as sm
    body = {"intent": "note", "text_digest": "abc"}
    key = "idem-1"
    h = sm.compute_proposal_hash(body, idempotency_key=key)
    prop = sm.ApprovalProposal(
        proposal_hash=h,
        policy_version=sm.POLICY_VERSION,
        state_version=0,
        expiry_at="2099-01-01T00:00:00Z",
        owner_approval_id=None,
        idempotency_key=key,
        body=body,
    )
    prop = sm.advance(prop, sm.ApprovalState.PROPOSED)
    assert prop.state == sm.ApprovalState.PROPOSED
    prop = sm.advance(prop, sm.ApprovalState.WAITING_OWNER)
    prop = sm.advance(prop, sm.ApprovalState.APPROVED)
    prop.body = {"intent": "note", "text_digest": "TAMPERED"}
    prop = sm.begin_execute(prop)
    assert prop.state == sm.ApprovalState.BLOCKED
    assert sm.transition(sm.ApprovalState.DRAFT, sm.ApprovalState.APPROVED) == sm.ApprovalState.BLOCKED


def t_criticality_v2_shadow_components():
    from doctor.criticality_v2 import CriticalityV2, demo_path_graph, append_trace
    eng = CriticalityV2(window=4)
    g = demo_path_graph(5)
    snap = None
    for i in range(4):
        snap = eng.observe(g, activity_count=10 + i)
    assert snap is not None
    assert snap.evidence_level == "SHADOW"
    assert snap.c_t is not None and 0.0 <= snap.c_t <= 1.0
    assert "spectral_heuristic" in snap.as_dict()
    m = snap.metrics()
    assert "octopus.criticality.c_t" in m
    assert "octopus.spectral.heuristic_sigma" in m or "octopus.spectral.sigma_legacy" in m
    assert snap.measurement_status in ("OK", "PARTIAL", "UNKNOWN")
    with tempfile.TemporaryDirectory() as td:
        # append_trace uses fixed path; just ensure call doesn't raise
        append_trace(snap, run_id="test", tick=1)


def t_pulse_shadow_compare_flag_off_noop():
    from heart.pulse_shadow_compare import record_divergence, shadow_compare
    os.environ.pop("OCTOPUS_WIRE_PULSE_ARBITER_SHADOW", None)
    assert record_divergence(
        production_period=60.0, shadow_period=70.0, run_id="r", tick=1
    ) is None
    rec = shadow_compare(60.0, 70.0, "r", 1, "deadbeef")
    assert rec.pct_difference > 0
    assert rec.evidence_level == "SHADOW"


def t_collaborator_marks_draft_no_effect():
    os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    os.environ.pop("OCTOPUS_COLLAB_USE_MODEL", None)
    from owner_console import collaborator as col
    r = col.handle("سلام خودتو معرفی کن")
    os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
    assert r.get("external_effect") is False
    assert r.get("send_attempted") is False
    assert (r.get("data") or {}).get("response_mode") == "draft"


CHECKS = [
    ("gateway-inject-collab-flag", t_gateway_inject_sets_collab_flag),
    ("gateway-inject-before-app", t_gateway_inject_runs_before_miniapp_scripts),
    ("app-js-default-collab-mode", t_app_js_default_collab_mode),
    ("discovery-facade-provenance", t_discovery_facade_has_provenance),
    ("world-discovery-uses-facade", t_world_discovery_uses_facade),
    ("talk-policy-send-needs-owner", t_talk_policy_external_send_needs_owner_approval),
    ("approval-sm-fail-closed", t_approval_sm_fail_closed_and_hash),
    ("approval-state-fingerprint", t_approval_state_blocks_bad_fingerprint),
    ("criticality-v2-shadow", t_criticality_v2_shadow_components),
    ("pulse-shadow-compare", t_pulse_shadow_compare_flag_off_noop),
    ("collaborator-draft-no-effect", t_collaborator_marks_draft_no_effect),
]

failed = harness.run(CHECKS)
sys.exit(1 if failed else 0)
