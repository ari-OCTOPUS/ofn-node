"""test_indicator_scorecard.py — بک‌لاگِ ۲۰۲۷ #۸: اسکورکاردِ نشانگرهای access-only.

اثبات‌ها: بدونِ فلگ = no-op ِ مطلق؛ هر نشانگر وضعیتِ معتبر (ABSENT/WEAK/PRESENT) از
واقعیتِ کد می‌گیرد؛ گِیتِ خاموش → WEAK و روشن‌شدنِ فلگ → PRESENT (خودراستایی)؛ بنرِ
access-only همیشه هست و هیچ «عددِ آگاهی» تولید نمی‌شود؛ گاردِ ضدِ اغراق ادعای مثبتِ
phenomenal را raise می‌کند ولی سلبِ مشروع را نه.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))
sys.path.insert(0, str(_HERE.parent / "epistemics"))

import harness
ENV = harness.setup("indicator-scorecard")

import indicator_scorecard as isc   # noqa: E402

_ROOT = harness.SELF_OPS          # درختِ تحتِ تست (worktree)
_VALID = {isc.ABSENT, isc.WEAK, isc.PRESENT}


def _clean():
    os.environ.pop(isc.FLAG, None)
    for ind in isc._INDICATORS:
        if ind.get("gate"):
            os.environ.pop(ind["gate"], None)


def t_shadow_off_is_total_noop():
    _clean()
    out = Path(ENV["OPS_DIR"]) / "state" / "cortex" / "isc-noop.jsonl"   # سینکِ اختصاصی
    card = isc.run(_ROOT, out_path=out)
    assert not out.exists()                       # بدونِ فلگ هیچ نوشتنی
    assert "_persisted" not in card


def t_every_indicator_has_valid_status():
    _clean()
    card = isc.score(_ROOT)
    assert card["n_indicators"] == len(isc._INDICATORS) >= 8
    for r in card["indicators"]:
        assert r["status"] in _VALID, r
    assert card["present"] + card["weak"] + card["absent"] == card["n_indicators"]


def t_no_consciousness_number_and_banner_present():
    _clean()
    card = isc.score(_ROOT)
    assert card["is_proof"] is False and card["epistemic"] == "access-only"
    assert "evidence NOT proof" in card["banner"]
    # هیچ کلیدِ عددیِ «درصد/score آگاهی» نباید وجود داشته باشد
    assert not any(k for k in card if "score" in k.lower() or "pct" in k.lower()
                   or "awareness" in k.lower())


def t_gated_signal_is_weak_then_promotes_when_flag_on():
    """PP-1 پشتِ OCTOPUS_WIRE_HEART: خاموش → WEAK؛ روشن → PRESENT (خودراستایی)."""
    _clean()
    pp = next(r for r in isc.score(_ROOT)["indicators"] if r["id"] == "PP-1")
    assert pp["status"] == isc.WEAK, pp        # فلگ خاموش → صادقانه WEAK
    os.environ["OCTOPUS_WIRE_HEART"] = "1"
    try:
        pp2 = next(r for r in isc.score(_ROOT)["indicators"] if r["id"] == "PP-1")
        assert pp2["status"] == isc.PRESENT, pp2   # فلگ روشن → ارتقا
    finally:
        _clean()


def t_absent_when_module_missing(tmp_path=None):
    """ریشهٔ خالی → همهٔ نشانگرها ABSENT (فایلِ ماژول نیست)."""
    _clean()
    empty = Path(ENV["OPS_DIR"]) / "state" / "empty-root"
    empty.mkdir(parents=True, exist_ok=True)
    card = isc.score(empty)
    assert card["absent"] == card["n_indicators"] and card["present"] == 0


def t_guard_raises_on_phenomenal_but_not_disclaimer():
    _clean()
    # ادعای مثبت → raise
    try:
        isc._assert_access_only("this module has qualia and phenomenal feels")
        raised = False
    except Exception:
        raised = True
    assert raised
    # سلبِ مشروع → مجاز (نباید raise کند)
    isc._assert_access_only("access routing only — not a phenomenal-consciousness claim")


def t_flag_on_writes_only_own_sink():
    _clean()
    os.environ[isc.FLAG] = "1"
    try:
        out = Path(ENV["OPS_DIR"]) / "state" / "cortex" / "isc-write.jsonl"
        card = isc.run(_ROOT, out_path=out)
        assert out.exists() and card.get("_persisted")
        line = json.loads(out.read_text("utf-8").splitlines()[-1])
        assert line["schema"] == isc.SCHEMA and line["epistemic"] == "access-only"
    finally:
        _clean()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_indicator_scorecard: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
