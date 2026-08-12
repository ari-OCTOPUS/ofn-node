#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
OPS=Path(__file__).resolve().parents[2]
if str(OPS) not in sys.path: sys.path.insert(0,str(OPS))
from owner_console import conversation


def t_home_is_human_and_has_navigation():
    r=conversation.handle("خانه")
    assert r["kind"]=="home" and r["keyboard"]
    assert "مرکز مالک" in r["text"]

def t_sensitive_send_is_blocked_not_executed():
    r=conversation.handle("این پیام را برای مشتری بفرست")
    assert r["kind"]=="owner-gate"
    assert r["data"]["status"]=="BLOCKED_BY_OWNER"
    assert r["send_attempted"] is False and r["external_effect"] is False

def t_goal_in_owner_language_reads_goal_state():
    r=conversation.handle("هدف چیست؟")
    assert r["kind"]=="goal"
    assert r["external_effect"] is False and r["send_attempted"] is False


def t_status_in_owner_language_reads_runtime():
    r=conversation.handle("وضعیت چیست؟")
    assert r["kind"]=="runtime"
    assert "runtime" in r["text"]
    assert r["external_effect"] is False and r["send_attempted"] is False


def t_blockers_phrase_that_stub_itself_suggests():
    """Regression 2026-08-12: clarify suggested «موانع چیست؟» then missed it."""
    for q in ("موانع چیست", "موانع چیست؟", "موانع", "مانع چیه", "⛔ موانع"):
        r = conversation.handle(q)
        assert r["kind"] == "blockers", (q, r["kind"], r["text"][:80])
        assert r["external_effect"] is False and r["send_attempted"] is False


def t_greeting_typo_is_intro_not_clarify():
    for q in ("سلام", "سلان", "hi", "hello"):
        r = conversation.handle(q)
        assert r["kind"] == "intro", (q, r["kind"])


def t_meta_why_dont_you_understand_is_not_blockers():
    r = conversation.handle("چرا نمیفهمی")
    assert r["kind"] == "meta", r
    assert r["data"].get("status") == "META_INTENT_FIXED"


def t_pain_question_is_shadow_proposal_not_control():
    r=conversation.handle("درد و حفاظت چه می‌گوید؟")
    assert r["kind"]=="protective-status"
    assert r["data"]["status"]=="SHADOW_PROPOSAL_ONLY"
    assert r["data"]["control_authority"] is False
    assert "halt صریحِ کنترل" in r["text"] or "SHADOW" in str(r.get("data"))
    assert r["external_effect"] is False and r["send_attempted"] is False


def t_unknown_clarifies():
    r=conversation.handle("یک چیز عجیب که معلوم نیست")
    assert r["kind"]=="clarify" and r["data"]["status"]=="CLARIFY"

def t_unknown_callback_blocks():
    r=conversation.callback("oc:evil:send")
    assert r["kind"]=="blocked"
    assert r["data"]["status"]=="BLOCKED_UNKNOWN_CALLBACK"

def t_every_reply_has_zero_cost_and_no_send():
    for q in ("خانه","همه قابلیت‌ها","هدفت چیه","شاهد runtime","موانع","کشف تازه"):
        r=conversation.handle(q)
        assert r["estimated_cost"]==0 and r["send_attempted"] is False
        assert r["authorization"] is None

def t_readonly_mission_is_proposal_only():
    r=conversation.handle("یک مأموریت فقط خواندنی بساز")
    assert r["kind"]=="readonly-proposal"
    assert r["data"]["status"]=="PROPOSED_NOT_SUBMITTED"


def t_collab_chat_not_stolen_by_local_first():
    """B4 regression: collab_chat must NOT be stolen by CORTEX_LOCAL_FIRST.

    When CORTEX_LOCAL_FIRST=1 and task=collab_chat, model_router must skip
    the local-first quality gate and go directly to secondary (DeepSeek).
    """
    import os
    old = os.environ.get("CORTEX_LOCAL_FIRST")
    os.environ["CORTEX_LOCAL_FIRST"] = "1"
    try:
        src = (OPS / "cortex" / "model_router.py").read_text("utf-8")
        assert "collab_chat" in src and "_skip_local" in src, \
            "collab_chat LOCAL_FIRST skip not found in model_router.py"
        assert 'TASK_TIERS' in src and '"collab_chat": "secondary"' in src
    finally:
        if old is None:
            os.environ.pop("CORTEX_LOCAL_FIRST", None)
        else:
            os.environ["CORTEX_LOCAL_FIRST"] = old


def t_self_aware_intents_match():
    """Phase E + INT-04: هویت/ترکیب → intro؛ ادعای خودآگاهی → honest-self (مسیرِ صادق)."""
    # هویت و ترکیب: intro (اسطوره‌ای نیستند، ادعای consciousness هم نیستند).
    for q in ("خودت کی ای", "از چی تشکیل شدی"):
        r = conversation.handle(q)
        assert r["kind"] == "intro", f"{q!r} → kind={r['kind']} (expected intro)"
    # ادعای خودآگاهی/قلب (INT-04، commit 6f4f3a1): مسیرِ صادق → honest-self، نه intro اسطوره‌ای.
    r = conversation.handle("خودآگاه هستی")
    assert r["kind"] == "honest-self", f"'خودآگاه هستی' → kind={r['kind']} (expected honest-self, INT-04)"


if __name__ == "__main__":
    ts = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    [f() for f in ts]
    print(f"OK {len(ts)}")
