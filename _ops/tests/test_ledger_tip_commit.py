#!/usr/bin/env python3
"""test_ledger_tip_commit — حذفِ انتهای زنجیرهٔ ژنوم را sidecar می‌گیرد.

verify() روی کپیِ زنده با آخرین خطِ حذف‌شده همچنان ok می‌دهد (همان کلاس
epistemics E3-tail، 2026-08-16). tip-commit این درز را می‌بندد — بدون تغییر
رفتار verify()."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
ROOT = _OPS.parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("ledger-tip-commit")


def _Ledger():
    py = ROOT / "07 - Knowledge" / "genome-system" / "ledger" / "ledger.py"
    spec = importlib.util.spec_from_file_location("_lg_tip_test", str(py))
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m.Ledger


def t_verify_still_ok_after_tail_drop_negative_control():
    """کنترل منفیِ درز: verify() دم را نمی‌بیند — اگر این قرمز شود، درز عوض شده."""
    td = Path(tempfile.mkdtemp(prefix="tip-neg-"))
    p = td / "ledger.jsonl"
    lg = _Ledger()(p)
    for i in range(4):
        lg.append("NOTE", {"i": i}, actor="test")
    ok, _ = lg.verify()
    assert ok is True
    lines = p.read_text("utf-8").splitlines()
    p.write_text("\n".join(lines[:-1]) + "\n", "utf-8")
    lg2 = _Ledger()(p)
    ok2, msg = lg2.verify()
    assert ok2 is True, msg


def t_verify_tip_catches_the_same_tail_drop():
    td = Path(tempfile.mkdtemp(prefix="tip-pos-"))
    p = td / "ledger.jsonl"
    lg = _Ledger()(p)
    for i in range(4):
        lg.append("NOTE", {"i": i}, actor="test")
    ok, reason = lg.verify_tip()
    assert ok is True and reason == "ok", (ok, reason)
    tip = json.loads(lg.tip_path().read_text("utf-8"))
    assert tip["n"] == 4 and tip["tip_hash"]
    lines = p.read_text("utf-8").splitlines()
    p.write_text("\n".join(lines[:-1]) + "\n", "utf-8")
    lg2 = _Ledger()(p)
    ok_v, _ = lg2.verify()
    ok_t, msg = lg2.verify_tip()
    assert ok_v is True, "verify must stay LAW-unchanged"
    assert ok_t is False and "length mismatch" in msg, msg


def t_unsealed_is_not_a_failure():
    td = Path(tempfile.mkdtemp(prefix="tip-unsealed-"))
    p = td / "ledger.jsonl"
    lg = _Ledger()(p)
    lg.append("NOTE", {"i": 0}, actor="test")
    lg.tip_path().unlink()
    ok, reason = lg.verify_tip()
    assert ok is True and reason == "unsealed", (ok, reason)
    sealed = lg.seal_tip()
    assert sealed["n"] == 1 and sealed["sealed"] is True
    ok2, reason2 = lg.verify_tip()
    assert ok2 is True and reason2 == "ok", (ok2, reason2)


def t_seal_repairs_a_stale_count_not_just_increments_it():
    """۲۰۲۶-۰۸-۲۵ (شاهد زندهٔ G4): sidecar با count کهنه (offset ثابت) و hashِ درست.
    seal قبلاً فقط prev_n+1 می‌نوشت و mismatch را هرگز ترمیم نمی‌کرد؛ حالا باید
    شمارش واقعی را بنویسد و verify_tip سبز شود — append همچنان prev_n+1 می‌ماند."""
    td = Path(tempfile.mkdtemp(prefix="tip-stale-"))
    p = td / "ledger.jsonl"
    lg = _Ledger()(p)
    for i in range(6):
        lg.append("NOTE", {"i": i}, actor="test")
    # شبیه‌سازی همان وضعیت زنده: bulk بیرونی ۳ رکیف اضافه کرد بدون عبور از append
    extra = [lg.append("NOTE", {"bulk": k}, actor="bulk") for k in range(3)]
    good = json.loads(lg.tip_path().read_text("utf-8"))
    good["n"] = good["n"] - 3          # count کهنه؛ hash همین head فعلی می‌ماند
    lg.tip_path().write_text(json.dumps(good), "utf-8")
    ok_v, _ = lg.verify()
    ok_t, msg = lg.verify_tip()
    assert ok_v is True, "verify باید LAW بماند"
    assert ok_t is False and "length mismatch" in msg, msg
    lg2 = _Ledger()(p)
    sealed = lg2.seal_tip()
    assert sealed["sealed"] is True
    ok_t2, msg2 = lg2.verify_tip()
    assert ok_t2 is True and msg2 == "ok", msg2
    tip2 = json.loads(lg2.tip_path().read_text("utf-8"))
    assert tip2["n"] == sealed["n"] == 9, tip2          # شمارش واقعی، نه ۷
    # append بعدی هنوز فقط +1 می‌کند و سازگاری می‌ماند
    lg2.append("NOTE", {"after": 1}, actor="test")
    ok_t3, msg3 = lg2.verify_tip()
    assert ok_t3 is True and msg3 == "ok", msg3
    assert json.loads(lg2.tip_path().read_text("utf-8"))["n"] == 10


def t_organism_daily_calls_verify_tip():
    src = (_OPS / "organism.py").read_text("utf-8")
    assert "verify_tip()" in src
    assert "seal_tip()" in src


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_ledger_tip_commit: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
