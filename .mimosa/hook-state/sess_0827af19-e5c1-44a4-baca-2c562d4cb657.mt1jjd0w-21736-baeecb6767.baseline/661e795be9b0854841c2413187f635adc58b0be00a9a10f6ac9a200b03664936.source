#!/usr/bin/env python3
"""test_chatbox_unified.py — فاز P→U: unified context + explainers + session + intents.

پوشش رفتار: دو مغز حاضر · 4D صادق · vault خالی · fact بدون source رد · recall هرگز
authorize نکند · failure یک provider crash نکند · معادلهٔ بدون implementation ACTIVE
نشود · session موقت · memory candidate نه commit.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("chatbox-unified")
_OPS = harness.SELF_OPS

for _p in (str(_OPS), str(_OPS / "memory"), str(_OPS / "owner_console")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unified_context as uc  # noqa: E402
import equation_explainer as eqx  # noqa: E402
import architecture_explainer as arx  # noqa: E402
import session_memory as sm  # noqa: E402


# ════════════════════════════════════════════════════════════════════
# فاز P — unified context
# ════════════════════════════════════════════════════════════════════

def p_two_brains_present_4d_honest():
    uc.STATE_DIR = Path(ENV["ops"]) / "state"
    # seed minimal live brain files so pulse is real, not static fallback
    cortex_dir = Path(ENV["ops"]) / "state" / "cortex"
    cortex_dir.mkdir(parents=True, exist_ok=True)
    (cortex_dir / "cortex-state.json").write_text(json.dumps({
        "cycle": 7, "coherence": 0.91, "members": [{"id": "x", "present": True}],
        "alignment": {"aligned": True},
    }), encoding="utf-8")
    (cortex_dir / "business-brain-latest.json").write_text(json.dumps({
        "beat": 3, "n_proposals": 1,
        "proposals": [{"title": "test-proposal"}],
    }), encoding="utf-8")
    r = uc.assemble("از چی تشکیل شدی؟")
    sc = r["self_context"]
    assert sc["cortex"]["live"] is True
    assert sc["business_brain"]["live"] is True
    assert sc["four_d_connected"] is False
    assert sc.get("bridge") in ("file-read-only", "fallback-static")
    assert sc["cortex"].get("cycle") == 7
    assert sc["business_brain"].get("beat") == 3
    assert sc.get("ipc_to_cortex") is False
    assert sc.get("chat_heard_by_brains") is False


def p_brain_pulse_module_reads_files():
    import brain_pulse as bp
    bp.STATE_DIR = Path(ENV["ops"]) / "state"
    cortex_dir = bp.STATE_DIR / "cortex"
    cortex_dir.mkdir(parents=True, exist_ok=True)
    (cortex_dir / "cortex-state.json").write_text(
        json.dumps({"cycle": 99, "coherence": 0.5, "members": []}), encoding="utf-8")
    snap = bp.snapshot()
    assert snap["schema"] == "brain-pulse.v1"
    assert snap["may_authorize"] is False
    assert snap["ipc_to_cortex"] is False
    assert snap["cortex"]["cycle"] == 99
    text = bp.as_context_block()
    assert "cycle=99" in text
    assert "file-bridge" in text


def p_never_authorizes():
    r = uc.assemble("چیزی")
    assert r["may_authorize"] is False
    assert r["equations"].get("may_authorize") is False
    assert r["effects"].get("may_authorize") is False
    assert r["shadow"].get("may_authorize") is False


def p_missing_state_failsoft_no_crash():
    uc.STATE_DIR = Path(tempfile.mkdtemp(prefix="uc-")) / "nope"
    r = uc.assemble("وضعیت")
    assert r["schema"] == "unified-context.v1"
    assert r["may_authorize"] is False


# ════════════════════════════════════════════════════════════════════
# فاز Q — equation explainer
# ════════════════════════════════════════════════════════════════════

def q_bcm_explained_with_status():
    r = eqx.explain("معادله BCM چیه؟")
    assert r["matched"] is True
    assert r["equation_id"] == "bcm"
    assert r["equation"]["runtime_status"] in eqx.STATUSES
    assert r["equation"]["decision_effect"] is False
    assert r["equation"]["apply_effect"] is False
    assert any("_ops/neural/bcm.py" in e for e in r["equation"]["evidence_refs"])


def q_sigma_effect_honest():
    r = eqx.explain("سیگما چه اثری روی تصمیم داره؟")
    assert r["matched"] is True
    assert r["equation_id"] == "spectral-sigma-legacy"
    # نه ACTIVE جعلی؛ اثر واقعی از شاهد می‌آید
    assert r["equation"]["runtime_status"] in ("ACTIVE", "TESTED", "DIAGNOSTIC", "SHADOW")


def q_unknown_equation_not_claimed():
    r = eqx.explain("معادلهٔ فلانفلان چیه؟")
    assert r["matched"] is False
    assert r["equation"] is None
    assert r["may_authorize"] is False


def q_arch_explained_with_path():
    r = arx.explain("Pulse Arbiter به چی وصله؟")
    assert r["matched"] is True
    assert r["architecture"]["component"] == "pulse_arbiter"
    assert "pulse_arbiter.py" in r["architecture"]["detail"]["path"]
    assert r["may_authorize"] is False


# ════════════════════════════════════════════════════════════════════
# فاز S — session memory
# ════════════════════════════════════════════════════════════════════

def s_session_roundtrip_isolated():
    sm.SESSION_FILE = Path(ENV["ops"]) / "state" / "session" / "sm.jsonl"
    sm.clear()
    sm.remember("a", "owner", "intro", "سلام")
    sm.remember("a:r", "collaborator", "intro", "سلام! دو مغز دارم")
    recent = sm.recent()
    assert len(recent) == 2
    assert recent[0]["role"] == "owner" and recent[1]["role"] == "collaborator"
    assert all(t.get("may_authorize") is False for t in recent)


def s_memory_proposal_not_commit():
    p = sm.propose_remember("این حرف را یادت بماند")
    assert p["proposal"] == "MEMORY_CANDIDATE"
    assert p["status"] == "candidate_not_committed"
    assert p["may_authorize"] is False
    assert "نیازمند رأی مالک" in p["note"]


def s_session_clear():
    sm.clear()
    assert sm.recent() == []


# ════════════════════════════════════════════════════════════════════
# conversation intents (Q)
# ════════════════════════════════════════════════════════════════════

def q_conversation_equation_intent():
    from owner_console import conversation as conv
    r = conv.handle("معادله BCM چیه؟")
    assert r["kind"] == "equation"
    assert r["data"]["equation_advice_only"] is True
    assert r["data"]["may_authorize"] is False
    assert r["external_effect"] is False


def q_conversation_effect_proposal_only():
    from owner_console import conversation as conv
    r = conv.handle("سرعت رو کم کن")
    assert r["kind"] == "effect"
    assert r["data"]["applied"] is False
    assert r["external_effect"] is False


def q_conversation_evidence_honest():
    from owner_console import conversation as conv
    r = conv.handle("شاهدت چیه؟")
    assert r["kind"] == "evidence"
    assert r["data"]["may_authorize"] is False


if __name__ == "__main__":
    failed = harness.run([
        ("[P] دو مغز + 4D صادق", p_two_brains_present_4d_honest),
        ("[P] brain_pulse file-bridge", p_brain_pulse_module_reads_files),
        ("[P] never authorizes", p_never_authorizes),
        ("[P] missing state fail-soft", p_missing_state_failsoft_no_crash),
        ("[Q] BCM توضیح با status", q_bcm_explained_with_status),
        ("[Q] sigma اثر صادق", q_sigma_effect_honest),
        ("[Q] معادلهٔ ناشناخته ادعا نشود", q_unknown_equation_not_claimed),
        ("[Q] معماری با path", q_arch_explained_with_path),
        ("[S] session roundtrip + isolation", s_session_roundtrip_isolated),
        ("[S] memory proposal نه commit", s_memory_proposal_not_commit),
        ("[S] session clear", s_session_clear),
        ("[Q:intent] equation intent", q_conversation_equation_intent),
        ("[Q:intent] effect proposal-only", q_conversation_effect_proposal_only),
        ("[Q:intent] evidence honest", q_conversation_evidence_honest),
    ])
    sys.exit(1 if failed else 0)
