"""test_self_improve.py — جلسه ۴۶: حلقهٔ خودارتقایی (self_audit + improve).

ماتریسِ ممیزی از واقعیت، پیشنهادهای دسته‌بندی‌شده، مرزِ اتومات (propose-only مگر پرچم)،
یادگیری از verdict، مغزِ محلیِ اختیاری، و ساختاری (فقط‌خواندنی، بدونِ importِ پول).
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("self-improve")

import importlib       # noqa: E402
import self_audit      # noqa: E402
import improve         # noqa: E402
importlib.reload(self_audit)
importlib.reload(improve)
import opslib          # noqa: E402

STATE = Path(ENV["ops"]) / "state"


def t_a_audit_matrix_from_reality():
    """ممیزی: هر probe یک item با status/evidence/priority؛ tally + maturity؛ گاف‌ها مرتب."""
    m = self_audit.run_audit(write=True)
    assert m["schema"] == "audit-matrix.v1"
    assert m["n"] == len(self_audit.PROBES)
    for it in m["items"]:
        assert it["status"] in ("Done", "Partial", "Missing", "Unknown")
        assert set(it) >= {"item", "status", "evidence", "priority", "gap_type"}
    assert 0 <= m["maturity_pct"] <= 100
    # گاف‌ها فقط Missing/Partial و مرتب بر اساسِ اولویت
    assert all(g["status"] in ("Missing", "Partial") for g in m["gaps"])
    assert self_audit.MATRIX_PATH.exists()


def t_b_audit_honest_not_fake_green():
    """صداقت: در vault موقتِ خالی، کلِ چیز Done نیست — گاف‌های واقعی گزارش می‌شوند."""
    m = self_audit.run_audit(write=False)
    assert m["tally"]["Missing"] + m["tally"]["Partial"] > 0
    # kill-switch باید Done باشد (opslib همیشه هست)
    ks = next(i for i in m["items"] if "kill switch" in i["item"])
    assert ks["status"] == "Done"


def t_c_proposals_categorized_and_ranked():
    """پیشنهادها دسته‌بندی‌شده (رأی مالک) + P0 اول + هرکدام suggested_action دارد."""
    d = improve.run(write=True, use_local_brain=False)
    assert d["schema"] == "upgrades-digest.v1"
    assert d["n_proposals"] > 0
    assert isinstance(d["by_category"], dict) and len(d["by_category"]) >= 2
    # top فقط P0/P1 و مرتب
    assert all(t["priority"] in ("P0", "P1") for t in d["top"])
    for cat, items in d["by_category"].items():
        for it in items:
            assert it["suggested_action"] and it["change_level"] in (
                "tune", "reconfig", "rewrite", "code")
    assert improve.DIGEST_PATH.exists()


def t_d_auto_boundary_propose_only_without_flag():
    """بدونِ پرچمِ ACTIVATION-SELF-IMPROVE-AUTO هیچ‌چیز auto نیست (propose-only)."""
    if improve.ACT_AUTO.exists():
        improve.ACT_AUTO.unlink()
    d = improve.run(write=True, use_local_brain=False)
    assert d["auto_enabled"] is False
    assert d["auto_eligible"] == []
    for items in d["by_category"].values():
        for it in items:
            assert it["status"] == "proposed"


def t_e_auto_flag_enables_only_whitelisted_tune():
    """با پرچم: فقط knobهای tuneِ whitelist auto-eligible می‌شوند، نه code/reconfig."""
    improve.ACT_AUTO.parent.mkdir(parents=True, exist_ok=True)
    improve.ACT_AUTO.write_text("owner", "utf-8")
    try:
        props = improve.generate_proposals(improve.gather_signals())
        for p in props:
            if p["auto_applicable"]:
                assert p["change_level"] == "tune"
                assert any(k.lower() in p["title"].lower() for k in improve.AUTO_KNOBS)
        # code-levelها هرگز auto نیستند
        codes = [p for p in props if p["change_level"] == "code"]
        assert all(not p["auto_applicable"] for p in codes)
    finally:
        improve.ACT_AUTO.unlink()


def t_f_learning_deprioritizes_rejected_category():
    """یادگیری: رد‌کردنِ یک دسته توسطِ مالک → جریمهٔ اولویتِ آن دسته."""
    improve.record_verdict("up-x", "governance", "reject")
    improve.record_verdict("up-y", "governance", "reject")
    pen = improve._load_verdict_penalty()
    assert pen.get("governance", 0) >= 2
    assert improve.VERDICTS_PATH.exists()


def t_g_local_brain_optional_failsoft():
    """مغزِ محلیِ غایب → digest بدونِ brain_note، هرگز کرش."""
    d = improve.run(write=False, use_local_brain=True)
    assert "maturity_pct" in d          # حتی اگر ollama نباشد، digest ساخته می‌شود


def t_h_structural_readonly_no_money_import():
    """ساختاری: self_audit/improve فقط state خودشان را می‌نویسند؛ هیچ importِ گیتِ پول."""
    for mod in (self_audit, improve):
        src = Path(mod.__file__).read_text("utf-8")
        head = src.split("def ")[0]
        for bad in ("import organ_gate", "import money_gate", "import budget_gate",
                    "from organ_gate", "from money_gate"):
            assert bad not in head, f"{mod.__name__}: {bad}"
    # improve فقط digest/verdicts/audit-matrix خودش را می‌نویسد + ledger_note (مشاهده)
    isrc = Path(improve.__file__).read_text("utf-8")
    assert "LockedJson(DIGEST_PATH)" in isrc


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_self_improve: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
