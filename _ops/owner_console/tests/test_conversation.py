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


def t_pain_question_is_shadow_proposal_not_control():
    r=conversation.handle("درد و حفاظت چه می‌گوید؟")
    assert r["kind"]=="protective-status"
    assert r["data"]["status"]=="SHADOW_PROPOSAL_ONLY"
    assert r["data"]["control_authority"] is False
    assert "halt مستقیم نیست" in r["text"]
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

if __name__=="__main__":
    ts=[v for k,v in sorted(globals().items()) if k.startswith("t_")]
    [f() for f in ts]; print(f"OK {len(ts)}")
