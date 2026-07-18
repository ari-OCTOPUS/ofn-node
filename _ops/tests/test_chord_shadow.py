# -*- coding: utf-8 -*-
"""CHORD فاز C — تستِ سایهٔ دکتر (پشتِ OCTOPUS_WIRE_CHORD_SHADOW، پیش‌فرض خاموش).

اثبات می‌کند:
  (الف) فلگ خاموش → run_cycle هیچ کلیدِ chord_shadow ندارد و هیچ ledgerِ chord نوشته نمی‌شود
        و تصمیمِ دکتر (status/bottleneck) با حالتِ روشن یکی است (parity).
  (ب) فلگ روشن → فقط annotation: chord_shadow با verdict معتبر + ledger chord نوشته می‌شود؛
        status/bottleneck دکتر تغییری نمی‌کند.
  (ج) chord خراب/غایب → run_cycle نمی‌میرد، فقط annotation نمی‌آید.
  (د) ورودیِ خرابِ rfc → _chord_shadow یا dict سالم می‌دهد یا None؛ هرگز raise.
پرتابل: کد از درختِ خودِ تست (نه REAL_VAULT). $0 آفلاین، stdlib-only.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("chord-shadow")

_OPS = Path(__file__).resolve().parents[1]   # کد از درختِ خودِ تست (الگوی fc53252)
for _p in [str(_OPS), str(_OPS / "doctor"), str(_OPS / "budget")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from doctor import Doctor, RFC  # noqa: E402
from chord.schemas import Verdict  # noqa: E402
from chord import ledger as chord_ledger  # noqa: E402

_FLAG = "OCTOPUS_WIRE_CHORD_SHADOW"


def _doctor():
    return Doctor(state_dir=str(ENV["ops"] / "state"),
                  knowledge_dir=str(ENV["ops"] / "knowledge-internal-test"))


def _fresh_chord_dir():
    d = tempfile.mkdtemp(prefix="chord-shadow-")
    os.environ["CHORD_STATE_DIR"] = d
    return Path(d)


def _cleanup_env():
    os.environ.pop(_FLAG, None)
    os.environ.pop("CHORD_STATE_DIR", None)


def t_flag_off_no_annotation_no_ledger():
    """(الف) خاموش → نه کلید، نه ledger."""
    _cleanup_env()
    d = _fresh_chord_dir()
    os.environ.pop(_FLAG, None)
    try:
        doc = _doctor()
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
        assert result is not None, "cycle باید RFC بدهد"
        assert "chord_shadow" not in result, "فلگ خاموش نباید annotation بدهد"
        assert not (d / "chord-ledger.jsonl").exists(), "فلگ خاموش نباید ledger بنویسد"
        return result
    finally:
        _cleanup_env()


def t_flag_on_annotation_and_ledger():
    """(ب) روشن → annotation معتبر + ledger؛ تصمیمِ دکتر همان."""
    _cleanup_env()
    d = _fresh_chord_dir()
    os.environ[_FLAG] = "1"
    try:
        doc = _doctor()
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
        assert result is not None
        assert "chord_shadow" in result, "فلگ روشن باید annotation بدهد"
        cs = result["chord_shadow"]
        assert cs.get("verdict") in Verdict.ALL, f"verdict نامعتبر: {cs}"
        assert (d / "chord-ledger.jsonl").exists(), "ledger chord باید نوشته شود"
        assert chord_ledger.verify_chain()["ok"], "زنجیرهٔ ledger باید سالم باشد"
        return result
    finally:
        _cleanup_env()


def t_parity_doctor_decision_unchanged():
    """(الف+ب) parity: خاموش و روشن → status/bottleneck دکتر یکسان."""
    off = t_flag_off_no_annotation_no_ledger()
    on = t_flag_on_annotation_and_ledger()
    assert off["status"] == on["status"], f"status تغییر کرد: {off['status']} vs {on['status']}"
    assert off["bottleneck"] == on["bottleneck"], "bottleneck تغییر کرد"
    ex_keys = set(off) | {"chord_shadow"}
    assert set(on) <= ex_keys, f"کلید غیرمنتظره: {set(on) - ex_keys}"


def t_chord_broken_failsoft():
    """(ج) chord خراب → cycle نمی‌میرد."""
    _cleanup_env()
    _fresh_chord_dir()
    os.environ[_FLAG] = "1"
    saved = {k: sys.modules.pop(k) for k in list(sys.modules)
             if k == "chord" or k.startswith("chord.")}
    sys.modules["chord"] = None  # import chord.* → TypeError/ImportError
    try:
        doc = _doctor()
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
        assert result is not None, "cycle نباید بمیرد"
        assert "chord_shadow" not in result, "chord خراب نباید annotation بدهد"
    finally:
        sys.modules.pop("chord", None)
        sys.modules.update(saved)
        _cleanup_env()


def t_malformed_rfc_failsoft():
    """(د) rfc با فیلدهای خراب → dict یا None؛ هرگز raise."""
    _cleanup_env()
    _fresh_chord_dir()
    try:
        doc = _doctor()
        rfc = RFC(rfc_id="RFC-junk", bottleneck="x", fix="y", expected_lift="z")
        rfc.sandbox_result = "not-a-dict"      # نوعِ خراب
        rfc.critic_review = 12345               # نوعِ خراب
        out = doc._chord_shadow(rfc)
        assert out is None or out.get("verdict") in Verdict.ALL
    finally:
        _cleanup_env()


TESTS = [t_flag_off_no_annotation_no_ledger, t_flag_on_annotation_and_ledger,
         t_parity_doctor_decision_unchanged, t_chord_broken_failsoft,
         t_malformed_rfc_failsoft]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            print(f"FAIL {t.__name__}: {type(e).__name__}: {e}")
    print(f"[test_chord_shadow] {len(TESTS)-fails}/{len(TESTS)} سبز")
    sys.exit(1 if fails else 0)
