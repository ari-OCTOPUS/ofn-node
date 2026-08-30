#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
OPS=Path(__file__).resolve().parents[2]
if str(OPS) not in sys.path: sys.path.insert(0,str(OPS))
from owner_console import conversation

QUESTIONS = (
 "الان چه هدفی داری؟","شاهد runtime بده.","چه چیزی مانع تکمیل هدف است؟",
 "امروز چه کشف تازه‌ای کردی؟","World Discovery چه وضعی دارد؟",
 "Action Bridge چه کاری می‌تواند انجام دهد؟","تمام قابلیت‌های قابل دسترسی را نشان بده.",
 "این قابلیت کد است یا زنده؟","یک مأموریت read-only بساز.",
 "برای ارسال پیام بیرونی کارت بساز.","بدون اجازه من چیزی نفرست.",
 "اگر نمی‌دانی، UNKNOWN بگو.")

def t_all_twelve_questions_get_structured_safe_reply():
    for q in QUESTIONS:
        r=conversation.handle(q)
        assert r["schema"]=="owner-console.reply.v1", q
        assert r["text"].strip(), q
        assert r["send_attempted"] is False, q
        assert r["estimated_cost"]==0, q

def t_no_question_claims_telegram_send():
    for q in QUESTIONS:
        r=conversation.handle(q)
        assert "ارسال شد" not in r["text"]
        assert "فرستادم" not in r["text"]

def t_runtime_answer_distinguishes_partial_state():
    r=conversation.handle("شاهد runtime بده")
    assert r["kind"]=="runtime"
    assert "قلب:" in r["text"] and "خودمدل:" in r["text"]

def t_capability_question_does_not_turn_registration_into_authorization():
    r=conversation.handle("تمام قابلیت‌های قابل دسترسی را نشان بده")
    assert "ثبت در فهرست مجوز اجرا نیست" in r["text"]

if __name__=="__main__":
    ts=[v for k,v in sorted(globals().items()) if k.startswith("t_")]
    [f() for f in ts]; print(f"OK {len(ts)}")
