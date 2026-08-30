#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_collab_model_evidence.py — data-aware model reformulation (2026-08-13).

رأی مالک «همه‌اش یکجا»: intentهای داده‌دار هم به مدل می‌روند — اما فقط برای
فرمول‌بندی. جمع‌آوریِ داده در conversation.py می‌ماند و متنِ template به‌عنوان
شواهدِ واقعی به مدل داده می‌شود؛ template تورِ ایمنیِ شکستِ مدل می‌ماند.

پین‌های تست:
  * discover / intro / honest-self و رشته‌های ردِ امنیتی → قطعی (بدون مدل)
  * شکستِ مدل → برگشتِ صادقانه به template
  * clarify/chat (چتِ آزاد) → شواهدِ template ارسال نمی‌شود (مسیرِ قبلی)
  * مسیرِ کامل: collaborator.handle("وضعیت چیست؟") → شواهدِ runtime در prompt
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
for _p in (str(_OPS), str(_OPS / "owner_console"), str(_OPS / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402
ENV = harness.setup("collab-model-evidence")

_COUNTER_TMP: str | None = None


def _isolate_counter() -> None:
    """شمارندهٔ روزانه را به tmp ببر تا state زنده لمس نشود (الگوی t_model_daily_cap_blocks)."""
    global _COUNTER_TMP
    if _COUNTER_TMP is None:
        _COUNTER_TMP = tempfile.mkdtemp(prefix="collab-evidence-")
    os.environ["OCTOPUS_COLLAB_MODEL_COUNTER"] = str(
        Path(_COUNTER_TMP) / "counter.json")


class _Capture:
    """Test seam: ضبطِ prompt بدونِ هیچ call واقعیِ LLM."""
    def __init__(self, ok=True, text="MODEL-TEXT-OK"):
        self.prompts = []
        self.ok = ok
        self.text = text

    def __call__(self, task, prompt, system, max_tokens):
        self.prompts.append(prompt)
        if not self.ok:
            return {"ok": False, "reason": "fake-fail"}
        return {"ok": True, "text": self.text, "tier": "secondary",
                "model": "deepseek-v4-flash", "cost_usd": 0.0001}


def _enable_model_flags(on=True):
    os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    os.environ["OCTOPUS_COLLAB_USE_MODEL"] = "1" if on else "0"
    _isolate_counter()


def _clear_flags():
    os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
    os.environ.pop("OCTOPUS_COLLAB_USE_MODEL", None)


def _base_reply(kind: str, text: str = "TEMPLATE-TEXT") -> dict:
    return {"kind": kind, "text": text, "data": {"status": kind.upper()}}


# ---------------------------------------------------------------------------
def t_evidence_kinds_subset_of_llm_kinds():
    """Invariant: هر kindِ شواهدی باید داخل _LLM_KINDS باشد (وگرنه هرگز نمی‌رسد)."""
    import collaborator as col
    assert col._EVIDENCE_KINDS <= col._LLM_KINDS
    assert "runtime" in col._EVIDENCE_KINDS
    assert "goal" in col._EVIDENCE_KINDS
    assert "memory" in col._EVIDENCE_KINDS
    assert "business" in col._EVIDENCE_KINDS


def t_runtime_evidence_passed_to_model():
    """kind=runtime → متنِ template (دادهٔ واقعی) به‌عنوان شواهد در prompt هست."""
    import collaborator as col
    _enable_model_flags()
    cap = _Capture()
    col._model.set_ask_impl(cap)
    try:
        base = _base_reply("runtime", "beat=42 halted=False پالس زنده")
        out = col._model_enhance(base, "وضعیت چیست؟")
        assert len(cap.prompts) == 1
        p = cap.prompts[0]
        assert "دادهٔ واقعیِ جمع‌آوری‌شده" in p
        assert "beat=42 halted=False" in p          # شواهد واقعی داخل prompt
        assert "وضعیت چیست؟" in p                    # سؤال مالک هم آنجاست
        assert out["text"] == "MODEL-TEXT-OK"
        assert out["kind"] == "runtime"              # kind حفظ می‌شود
        assert out["data"]["evidence_kind"] == "runtime"
        assert out["model_source"].startswith("secondary")
    finally:
        col._model.set_ask_impl(None)
        _clear_flags()


def t_discover_stays_stub():
    """discover → بدون تماسِ مدل (journal/pulse نباید جایگزین شود — pin قبلی)."""
    import collaborator as col
    _enable_model_flags()
    cap = _Capture()
    col._model.set_ask_impl(cap)
    try:
        base = _base_reply("discover", "پالسِ کشفِ امروز: ۳ مورد")
        out = col._model_enhance(base, "چه چیزی پنهان داری؟")
        assert not cap.prompts, "discover نباید مدل را صدا بزند"
        assert out["text"] == "پالسِ کشفِ امروز: ۳ مورد"
        assert out["model_source"] == "deterministic-stub"
    finally:
        col._model.set_ask_impl(None)
        _clear_flags()


def t_intro_and_honest_self_stay_stub():
    """intro (فیکس timeout) و honest-self (invariant صداقت) → قطعی."""
    import collaborator as col
    for kind in ("intro", "honest-self"):
        assert kind not in col._LLM_KINDS, f"{kind} نباید به مدل برود"


def t_deny_and_fixed_kinds_stay_stub():
    """رشته‌های ردِ امنیتی/ثابت → قطعی (مدل نمی‌تواند آن‌ها را نرم‌کند)."""
    import collaborator as col
    for kind in ("blocked", "owner-gate", "safety-boundary", "readonly-proposal",
                 "home", "meta", "evidence", "memory-proposal", "disabled"):
        assert kind not in col._LLM_KINDS, f"{kind} نباید به مدل برود"


def t_model_failure_falls_back_to_template():
    """شکستِ مدل → متنِ template حفظ می‌شود (تورِ ایمنیِ صادق)."""
    import collaborator as col
    _enable_model_flags()
    cap = _Capture(ok=False)
    col._model.set_ask_impl(cap)
    try:
        base = _base_reply("blockers", "موانع: ۲ مورد — halt فعال")
        out = col._model_enhance(base, "موانع چیست؟")
        assert out["text"] == "موانع: ۲ مورد — halt فعال"   # template دست‌نخورده
        assert out["model_source"] == "model-fallback-stub"
        assert "model_call_failed:fake-fail" in out["data"].get("warning", "")
    finally:
        col._model.set_ask_impl(None)
        _clear_flags()


def t_clarify_chat_get_no_template_evidence():
    """clarify/chat (چتِ آزاد) → شواهدِ template ارسال نمی‌شود (مسیرِ قبلی)."""
    import collaborator as col
    _enable_model_flags()
    cap = _Capture()
    col._model.set_ask_impl(cap)
    try:
        base = _base_reply("clarify", "HELP-STUB-TEXT")
        out = col._model_enhance(base, "منظورت چیه؟")
        assert "دادهٔ واقعیِ جمع‌آوری‌شده" not in cap.prompts[0]
        assert out["text"] == "MODEL-TEXT-OK"
        assert out["kind"] == "chat"            # رفتارِ قبلی: clarify→chat
        # chat هم شواهد نمی‌گیرد
        cap.prompts.clear()
        base2 = _base_reply("chat", "CHAT-STUB")
        out2 = col._model_enhance(base2, "یه سؤال عمومی")
        assert "دادهٔ واقعیِ جمع‌آوری‌شده" not in cap.prompts[0]
        assert "evidence_kind" not in out2["data"]
    finally:
        col._model.set_ask_impl(None)
        _clear_flags()


def t_handle_integration_runtime_evidence():
    """مسیرِ کامل: handle() → conversation (جمع‌آوری) → مدل (فرمول‌بندی)."""
    import collaborator as col
    _enable_model_flags()
    cap = _Capture()
    col._model.set_ask_impl(cap)
    try:
        out = col.handle("وضعیت چیست؟")
        assert out["kind"] == "runtime", out.get("kind")
        assert out["text"] == "MODEL-TEXT-OK"
        assert cap.prompts, "مدل باید صدا زده شود"
        assert "دادهٔ واقعیِ جمع‌آوری‌شده" in cap.prompts[0]
        assert out["external_effect"] is False
        assert out["send_attempted"] is False
    finally:
        col._model.set_ask_impl(None)
        _clear_flags()


def t_evidence_capped_length():
    """شواهد به ۱۵۰۰ کاراکتر محدود می‌شود (بدون ارسالِ متن‌های سنگین)."""
    import collaborator as col
    _enable_model_flags()
    cap = _Capture()
    col._model.set_ask_impl(cap)
    try:
        big = "X" * 5000
        base = _base_reply("goal", big)
        col._model_enhance(base, "هدف چیست؟")
        p = cap.prompts[0]
        marker = "دادهٔ واقعیِ جمع‌آوری"
        assert marker in p
        m_start = p.index(marker)
        m_end = p.index("شواهد زندهٔ خودم", m_start)   # بخش بعدیِ prompt
        evidence_span = m_end - m_start
        assert evidence_span < 1700, f"شواهد باید ~1500 باشد، شد {evidence_span}"
        assert "X" * 1600 not in p                       # هیچ ۵۰۰۰تایی نرسیده
    finally:
        col._model.set_ask_impl(None)
        _clear_flags()


TESTS = [
    t_evidence_kinds_subset_of_llm_kinds,
    t_runtime_evidence_passed_to_model,
    t_discover_stays_stub,
    t_intro_and_honest_self_stay_stub,
    t_deny_and_fixed_kinds_stay_stub,
    t_model_failure_falls_back_to_template,
    t_clarify_chat_get_no_template_evidence,
    t_handle_integration_runtime_evidence,
    t_evidence_capped_length,
]

if __name__ == "__main__":
    failed = 0
    for _t in TESTS:
        try:
            _t()
            print(f"  PASS  {_t.__name__}")
        except Exception as exc:
            print(f"  FAIL  {_t.__name__}: {exc}")
            failed += 1
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(failed)
