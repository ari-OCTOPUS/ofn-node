#!/usr/bin/env python3
"""test_ziman_branding.py — برندینگِ خودکارِ زیمان از مغزِ مشترک (model_router → Fugu).

قرارداد که این تست‌ها قفلش می‌کنند:
  * use_llm=False → byte-identical با رفتارِ امروز (صفر فراخوانِ مغز).
  * use_llm=True با مغزِ در دسترس → بدنه از LLM، body_source=llm:<tier>، propose-only.
  * مغز خاموش/خطا/جوابِ پوچ → fail-soft به همان قالبِ قطعی (هرگز crash).
  * publish/send همچنان hard-gated حتی با use_llm.
  * ziman_beat: پرچمِ خاموش → branding=None و صفر proposal (byte-identical)؛
    پرچمِ روشن + fire → دقیقاً یک draft proposal.
هیچ شبکه، هیچ پول — model_router با fake مونکی‌پچ می‌شود.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_LEGS = _OPS / "legs"
for p in (str(_OPS), str(_LEGS), str(_OPS / "budget")):
    if p not in sys.path:
        sys.path.insert(0, p)

from leg import Proposal  # noqa: E402
from ziman_leg import ZimanLeg  # noqa: E402


# ─── fake model_router (تزریق در sys.modules) ────────────────────────────────
class _FakeRouter:
    def __init__(self, result):
        self._result = result
        self.calls = []

    def ask(self, task, prompt, system="", max_tokens=400, **kw):
        self.calls.append({"task": task, "prompt": prompt, "system": system})
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def _install_router(result):
    fake = _FakeRouter(result)
    sys.modules["model_router"] = fake
    return fake


def _uninstall_router():
    sys.modules.pop("model_router", None)


def _leg():
    return ZimanLeg(organ_table={"ZIMAN": {"floor": 1}}, capacity_ceiling=6)


# ─── use_llm=False → byte-identical (صفر مغز) ────────────────────────────────
def test_default_is_template_no_llm_call():
    fake = _install_router({"ok": True, "text": "نباید صدا شود", "tier": "primary"})
    try:
        p = _leg().draft_content(kind="caption", product_family="C3", occasion="هدیه")
        assert isinstance(p, Proposal)
        assert p.payload["body_source"] == "template"
        assert fake.calls == []          # مغز اصلاً صدا نشد
        assert "پیش‌نویس است" in p.payload["body"]
    finally:
        _uninstall_router()


def test_template_body_identical_when_llm_fails():
    # مغزِ شکست‌خورده: use_llm=True باید byte-identical همان بدنهٔ قالبیِ use_llm=False بدهد.
    # (نکته: مغزِ محلیِ واقعی در این محیط در دسترس است، پس باید fakeِ شکست تزریق کرد،
    # نه به «نبودِ مغز» تکیه کرد — وگرنه تست qwenِ واقعی را صدا می‌زند و غیرقطعی می‌شود.)
    fake = _install_router({"ok": False, "reason": "down"})
    try:
        base = _leg().draft_content(product_family="C3", occasion="هدیه")   # use_llm=False
        llm = _leg().draft_content(product_family="C3", occasion="هدیه", use_llm=True)
        assert base.payload["body"] == llm.payload["body"]
        assert llm.payload["body_source"] == "template"
    finally:
        _uninstall_router()


# ─── use_llm=True با مغزِ در دسترس ────────────────────────────────────────────
def test_llm_body_used_when_router_ok():
    fake = _install_router({"ok": True, "text": "کپشنِ گرمِ برند 🌸 دست‌ساز و محدود. DM بده.",
                            "tier": "primary"})
    try:
        p = _leg().draft_content(product_family="C3", occasion="سالگرد", use_llm=True)
        assert p.payload["body_source"] == "llm:primary"     # Fugu رده primary
        assert "کپشنِ گرمِ برند" in p.payload["body"]
        assert p.payload["publish"] is False                 # propose-only دست‌نخورده
        assert p.payload["draft_only"] is True
        assert len(fake.calls) == 1
        assert "Ziman" in fake.calls[0]["system"]            # قواعدِ برند تزریق شد
    finally:
        _uninstall_router()


def test_llm_failure_falls_back_to_template():
    for bad in ({"ok": False, "reason": "kill-switch"},
                {"ok": True, "text": "کوتاه"},               # <24 char → پوچ
                RuntimeError("boom")):
        fake = _install_router(bad)
        try:
            p = _leg().draft_content(product_family="C3", occasion="هدیه", use_llm=True)
            assert p.payload["body_source"] == "template", bad
            assert "پیش‌نویس است" in p.payload["body"]
        finally:
            _uninstall_router()


def test_price_leak_flags_warning_not_block():
    fake = _install_router({"ok": True, "tier": "primary",
                            "text": "کپشنِ عالی و طولانیِ برند برای فروش، قیمت ۴۵ دلار تخفیف ویژه."})
    try:
        p = _leg().draft_content(product_family="C3", occasion="هدیه", use_llm=True)
        assert p.payload["body_source"] == "llm:primary"     # بلاک نشد (draft است)
        assert "brand_rule_warning" in p.payload             # ولی پرچمِ بازبینی خورد
    finally:
        _uninstall_router()


def test_perishable_warning_survives_llm_body():
    # هشدارِ فاسدشدنی/الکل باید حتی روی بدنهٔ LLM ضمیمه بماند
    leg = _leg()
    # C4 در fallback = فاسدشدنی هاردکد
    fake = _install_router({"ok": True, "tier": "secondary",
                            "text": "کپشنِ برندِ خوب و به‌اندازهٔ کافی طولانی برای عبور از گیت."})
    try:
        p = leg.draft_content(product_family="C4", occasion="هدیه", use_llm=True)
        assert p.payload["body_source"].startswith("llm:")
        assert "فاسدشدنی" in p.payload["body"]
    finally:
        _uninstall_router()


def test_hard_gate_still_blocks_publish_even_with_llm():
    fake = _install_router({"ok": True, "text": "هرچی", "tier": "primary"})
    try:
        r = _leg().draft_content(kind="publish", use_llm=True)
        assert isinstance(r, dict) and r["ok"] is False
        assert fake.calls == []          # حتی مغز هم صدا نشد
    finally:
        _uninstall_router()


# ─── ziman_beat wiring ───────────────────────────────────────────────────────
def _wiring():
    import importlib
    w = importlib.import_module("wiring")
    return w


_SAVED = {}


def _fresh_beat_env(monkeypatch_env, tmp_state, *, branding_on):
    import os
    import opslib
    w = _wiring()
    w._EPOCH_STATE.clear()                       # اپکِ تازه هر تست
    os.environ["OCTOPUS_WIRE_ZIMAN"] = "1"
    os.environ["CHRONO_ZIMAN_EVERY_N_BEATS"] = "1"
    os.environ["CHRONO_ZIMAN_BRANDING_EVERY_N_BEATS"] = "1"
    os.environ["OCTOPUS_ZIMAN_BRANDING"] = "1" if branding_on else "0"
    w._ZIMAN_STATE["state_path"] = tmp_state
    # گوچای worktree: opslib.STOP_ORGANISM به درختِ live اشاره می‌کند و ممکن است
    # kill-switchِ عمدیِ مالک آنجا باشد — هرگز پاکش نمی‌کنیم، فقط برای این تست به
    # مسیرِ ناموجود stub می‌کنیم (memory: stub via cleanup, never delete).
    _SAVED["stop"] = opslib.STOP_ORGANISM
    opslib.STOP_ORGANISM = tmp_state.parent / "no-such-stop"
    return w


def test_beat_branding_off_is_none_and_zero_proposals(tmp_path):
    w = _fresh_beat_env(None, tmp_path / "s.ziman", branding_on=False)
    leg = _leg()
    out = w.ziman_beat(leg=leg, beat=5)
    assert out is not None
    assert out["branding"] is None
    assert len(leg.proposals) == 0               # صفر proposal وقتی خاموش
    _cleanup_beat_env()


def test_beat_branding_on_emits_one_draft(tmp_path):
    w = _fresh_beat_env(None, tmp_path / "s.ziman", branding_on=True)
    fake = _install_router({"ok": True, "tier": "primary",
                            "text": "کپشنِ برندِ روزانه، دست‌ساز و محدود، برای مناسبتِ خاص. DM بده 🌸"})
    try:
        leg = _leg()
        out = w.ziman_beat(leg=leg, beat=1)
        assert out is not None
        assert out["branding"] is not None
        assert out["branding"]["emitted"] is True
        assert out["branding"]["body_source"] == "llm:primary"
        assert len(leg.proposals) == 1           # دقیقاً یک draft proposal
        assert leg.proposals[0].kind == "draft_content"
        assert leg.proposals[0].payload["publish"] is False
    finally:
        _uninstall_router()
        _cleanup_beat_env()


def test_beat_branding_llm_down_still_emits_template_draft(tmp_path):
    # پرچم روشن ولی مغز خراب → همچنان یک draftِ قالبی emit می‌شود (fail-soft).
    # fakeِ شکست تزریق می‌شود (نه uninstall) تا قطعی بماند — مغزِ محلیِ واقعی موجود است.
    w = _fresh_beat_env(None, tmp_path / "s.ziman", branding_on=True)
    _install_router({"ok": False, "reason": "down"})
    try:
        leg = _leg()
        out = w.ziman_beat(leg=leg, beat=1)
        assert out["branding"]["body_source"] == "template"
        assert len(leg.proposals) == 1
    finally:
        _uninstall_router()
        _cleanup_beat_env()


def _cleanup_beat_env():
    import os
    import opslib
    for k in ("OCTOPUS_WIRE_ZIMAN", "OCTOPUS_ZIMAN_BRANDING",
              "CHRONO_ZIMAN_EVERY_N_BEATS", "CHRONO_ZIMAN_BRANDING_EVERY_N_BEATS"):
        os.environ.pop(k, None)
    if "stop" in _SAVED:
        opslib.STOP_ORGANISM = _SAVED.pop("stop")   # مسیرِ زندهٔ STOP را برگردان
    w = _wiring()
    w._EPOCH_STATE.clear()
    w._ZIMAN_STATE.pop("state_path", None)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
