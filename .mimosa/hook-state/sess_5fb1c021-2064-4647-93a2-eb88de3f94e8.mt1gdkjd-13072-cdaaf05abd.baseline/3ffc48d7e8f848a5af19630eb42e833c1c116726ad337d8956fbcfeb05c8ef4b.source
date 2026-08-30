"""test_content.py — رگرسیونِ CF-01: عددِ ظرفیتِ تأییدنشده هرگز در متنِ عمومی/پرامپت نیاید.

سقفِ خامِ yaml (فعلاً ۳۰/هفته) طبقِ CONFLICT-REGISTER «تأییدنشده» است و تا revalidation
مالک هرگز نباید در draft عمومی، DM، پست یا پرامپتِ مدل ظاهر شود؛ فقط روایتِ کیفیِ
کمیابی («ظرفیتِ محدودِ دست‌ساز») مجاز است.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))  # ziman-agent/ → importِ پکیج برای relative-importها

from ziman import content

CANARY = 37  # سقفِ کاناری: عددی که در هیچ قالب/تاریخی خودبه‌خود ظاهر نمی‌شود


def _cfg(canary=CANARY):
    return {
        "business": {"name": "Ziman Gift",
                     "products": ["گل‌آراییِ مصنوعی", "شادوباکسِ گلِ قاب‌شده"]},
        "capacity": {"units_per_week_ceiling": canary, "current_inventory": 20},
        "occasions": ["تولد", "نامزدی"],
        "audience": {"segments": ["آشنایان"]},
        "generation": {"max_tokens": 700},
    }


# عبارت‌های نشانهٔ نشتِ عددِ ظرفیت (مستقل از مقدار)
_CAPACITY_PHRASES = ("عدد در هفته", "در هفته است", "هفته‌ای ~", "واحد در هفته")
_NUMBERED_WEEK = re.compile(r"\d+\s*(عدد|تا|واحد)\s*در هفته")


def _assert_no_leak(text, canary=CANARY):
    assert str(canary) not in text, "عددِ خامِ سقفِ ظرفیت نشت کرد"
    for phrase in _CAPACITY_PHRASES:
        assert phrase not in text, f"نشتِ ظرفیت: «{phrase}»"
    assert not _NUMBERED_WEEK.search(text), "عددِ هفتگی در متنِ عمومی"


def test_offline_draft_no_capacity_leak():
    text = content._offline_draft(_cfg(), "تولد", "گل‌آراییِ مصنوعی")
    _assert_no_leak(text)


def test_dm_variants_no_capacity_leak():
    for _title, msg in content._dm_variants(_cfg()):
        _assert_no_leak(msg)


def test_post_variants_no_capacity_leak():
    for _title, msg in content._post_variants(_cfg()):
        _assert_no_leak(msg)


def test_prompts_no_capacity_leak():
    cfg = _cfg()
    system, user = content._draft_prompt(cfg, "تولد", "شادوباکس", "زمینه")
    _assert_no_leak(system + user)
    system, user = content._batch_prompt(cfg, "dm", 5, "زمینه")
    _assert_no_leak(system + user)


def test_prompts_forbid_capacity_numbers():
    """مدلِ زنده هم صراحتاً از ذکرِ عددِ ظرفیت منع می‌شود (زمینهٔ vault ممکن است ۳۰ داشته باشد)."""
    cfg = _cfg()
    system, _ = content._draft_prompt(cfg, "تولد", "شادوباکس", "")
    assert "عددِ مشخصِ ظرفیت" in system
    system, _ = content._batch_prompt(cfg, "posts", 3, "")
    assert "عددِ مشخصِ ظرفیت" in system


def test_generate_paths_offline_no_leak(monkeypatch):
    """هر سه ژنراتور در مسیرِ افتِ امنِ offline هم عدد نشت نمی‌دهند."""
    def _boom(*a, **k):
        raise RuntimeError("no live route in test")
    monkeypatch.setattr(content.llm_router, "generate", _boom)
    cfg = _cfg()
    text, mode = content.generate_draft(cfg, context="")
    assert mode == "offline"
    _assert_no_leak(text)
    dms, mode = content.generate_dms(cfg, n=6, context="")
    assert mode == "offline"
    _assert_no_leak(dms)
    posts, mode = content.generate_posts(cfg, n=3, context="")
    assert mode == "offline"
    _assert_no_leak(posts)


def test_real_yaml_ceiling_not_leaked(monkeypatch):
    """سناریوی واقعیِ CF-01: با yamlِ واقعی (سقفِ ۳۰ تأییدنشده) متنِ عمومی عدد ندارد."""
    def _boom(*a, **k):
        raise RuntimeError("offline")
    monkeypatch.setattr(content.llm_router, "generate", _boom)
    from ziman.config import load_config
    cfg = load_config(ROOT.parent / "ziman.yaml")
    assert cfg["capacity"]["units_per_week_ceiling"] == 30  # پیش‌شرطِ سناریوی CF-01
    for text, _mode in (content.generate_draft(cfg, context=""),
                        content.generate_dms(cfg, n=6, context=""),
                        content.generate_posts(cfg, n=3, context="")):
        for phrase in _CAPACITY_PHRASES:
            assert phrase not in text
        assert not _NUMBERED_WEEK.search(text)
        assert not re.search(r"\b30\s*(عدد|تا)", text)
