"""test_tg_intent.py — طبقه‌بندِ نیتِ مرکزِ تلگرام (telegram_center/intent.py).

خالص و بدونِ شبکه/نوشتن: نیتِ هر نمونهٔ متنی قطعی است، danger درست gating می‌شود،
تشخیصِ پا در ابهام None برمی‌گردد، و ورودیِ خراب هرگز crash نمی‌کند.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("tg-intent")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))
import intent  # noqa: E402


# ─── نیت‌های پایه ────────────────────────────────────────────────────────────────
def t_a_status_intent():
    for q in ("وضعیت الان چطوره؟", "الان چی شده", "status now", "how are things"):
        r = intent.classify(q)
        assert r["intent"] == "status", (q, r)
        assert r["danger"] == "read"
        assert r["confidence"] >= 0.85


def t_b_revenue_intent():
    for q in ("درآمد چقدره؟", "پول چطوره", "مالی", "revenue", "money"):
        r = intent.classify(q)
        assert r["intent"] == "revenue", (q, r)
        assert r["danger"] == "read"


def t_c_budget_intent():
    for q in ("بودجه", "تخصیص بده", "budget"):
        r = intent.classify(q)
        assert r["intent"] == "budget", (q, r)
        assert r["danger"] == "read"


def t_d_help_menu_intent():
    for q in ("کمک", "راهنما", "منو", "help", "menu"):
        r = intent.classify(q)
        assert r["intent"] == "help", (q, r)


def t_e_pause_intent_with_leg():
    r = intent.classify("لید رو مکث کن")
    assert r["intent"] == "pause_leg" and r["leg"] == "lead", r
    assert r["danger"] == "low"          # برگشت‌پذیر ولی state عوض می‌شود
    assert r["confidence"] == 1.00


def t_f_resume_intent_with_leg():
    r = intent.classify("ziman رو ادامه بده")
    assert r["intent"] == "resume_leg" and r["leg"] == "ziman", r
    assert r["danger"] == "low"


def t_g_pause_without_leg_returns_none_leg():
    r = intent.classify("مکثش کن")
    assert r["intent"] == "pause_leg", r
    assert r["leg"] is None, ("بدونِ پا → None تا center کارتِ انتخاب بسازد", r)


def t_h_scan_metadata_intent():
    for q in ("نقشه بکش", "اسکن کن", "manifest بساز", "metadata", "چی توشه"):
        r = intent.classify(q)
        assert r["intent"] == "scan_metadata", (q, r)
        assert r["danger"] == "read"      # فقط metadata، کارت پیشنهاد — نه اجرا


def t_i_approvals_intent():
    for q in ("تأییدها", "صف تصمیم", "approvals", "چی منتظره"):
        r = intent.classify(q)
        assert r["intent"] == "approvals", (q, r)
        assert r["danger"] == "read"


def t_j_unknown_intent_with_card():
    r = intent.classify("یه چیز کاملاً عجیب")
    assert r["intent"] == "unknown", r
    assert r["confidence"] < 0.85, ("unknown باید confidence پایین داشته باشد", r)
    assert r["danger"] == "read"


# ─── تشخیصِ پا ─────────────────────────────────────────────────────────────────
def t_k_detect_leg_single_hit():
    assert intent.detect_leg("لید") == "lead"
    assert intent.detect_leg("ziman") == "ziman"
    assert intent.detect_leg("استودیو") == "studio_pf"
    assert intent.detect_leg("نقشه‌بردار") == "cartographer"


def t_l_detect_leg_ambiguous_returns_none():
    # دو پا در یک متن → None (center باید کارتِ انتخاب بسازد)
    assert intent.detect_leg("لید و ziman") is None
    assert intent.detect_leg("استودیو و ماینینگ") is None


def t_m_detect_leg_no_hit_returns_none():
    assert intent.detect_leg("چیزی شبیه هیچ‌کدوم") is None
    assert intent.detect_leg("") is None


# ─── ناوردی‌ها ───────────────────────────────────────────────────────────────────
def t_n_broken_input_safe():
    for bad in (None, "", "   ", 12345, {"not": "string"}):
        r = intent.classify(bad)   # type: ignore[arg-type]
        assert isinstance(r, dict)
        assert set(r.keys()) == {"intent", "leg", "confidence", "danger"}
        assert r["intent"] in ("unknown",) or isinstance(r["intent"], str)


def t_o_output_shape_contract():
    r = intent.classify("وضعیت")
    assert set(r.keys()) == {"intent", "leg", "confidence", "danger"}
    assert isinstance(r["confidence"], float)
    assert 0.0 <= r["confidence"] <= 1.0
    assert r["danger"] in ("read", "low", "medium", "high")


def t_p_is_read_only_helper():
    assert intent.is_read_only("status") is True
    assert intent.is_read_only("scan_metadata") is True
    assert intent.is_read_only("pause_leg") is False
    assert intent.is_read_only("resume_leg") is False
    assert intent.is_read_only("nonsense") is True     # fail-safe به read


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_intent: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
