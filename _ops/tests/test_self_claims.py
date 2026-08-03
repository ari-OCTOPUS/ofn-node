#!/usr/bin/env python3
"""test_self_claims.py — تولیدکنندهٔ ادعاهای خود (رفعِ ORPH-SELF-CLAIMS، 2026-07-14).

مسئله: calibration_probe به‌صورتِ LIVE از state/cortex/self-claims.jsonl می‌خوانَد
ولی هیچ‌کس آن را نمی‌نوشت → probe همیشه کور (n_claims=0). این تست اثبات می‌کند
self_model.emit_self_claims حالا آن لِجِر را تولید می‌کند و calibration_probe
می‌تواند ورودیِ ناخالی بخواند.

اثبات می‌کند:
  * فلگ خاموش (پیش‌فرض) → صفر نوشتن (byte-identical؛ فایل حتی ساخته نمی‌شود).
  * فلگ روشن → رکوردی با شِمای موردِ انتظارِ probe ({key, confidence∈[0,1]}) الحاق می‌شود.
  * calibration_probe._load_claims همان لِجِر را ناخالی می‌خواند.
  * fail-soft: خطا در نوشتن حلقهٔ فراخوان را نمی‌کشد.

صفر نوشتن روی مسیرهای زنده: همهٔ pathها به یک tmp dir مونکی‌پچ می‌شوند.
اجرا: python -X utf8 test_self_claims.py
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
for _p in (_HERE.parent / "budget", _HERE.parent / "cortex", _HERE.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# ایزوله قبل از اولین import — وگرنه `opslib.alert()` (از راهِ self_model) روی
# `state/alert-signatures.json` ِ زنده می‌نوشت و `self-model.write-failure.json` ِ
# زنده را unlink می‌کرد.
import harness  # noqa: E402
ENV = harness.setup("self-claims")

import self_model  # noqa: E402
import calibration_probe  # noqa: E402


def _tmp() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp(prefix="selfclaims-test-"))


def _isolate(d: pathlib.Path) -> None:
    """لِجِرِ ادعا + خروجیِ نقشه را به tmp ببر — هیچ فایلِ زنده لمس نمی‌شود."""
    self_model.SELF_CLAIMS_PATH = d / "cortex" / "self-claims.jsonl"
    self_model.MODEL_PATH = d / "cortex" / "self-model.json"
    # probe از همان مسیر بخواند
    calibration_probe.CLAIMS = self_model.SELF_CLAIMS_PATH


def _flag(on: bool) -> None:
    if on:
        os.environ["CORTEX_SELF_MONITOR"] = "1"
    else:
        os.environ.pop("CORTEX_SELF_MONITOR", None)


def test_flag_off_writes_nothing() -> None:
    d = _tmp()
    _isolate(d)
    _flag(False)
    model = self_model.build_model()
    written = self_model.emit_self_claims(model)
    assert written == 0, written
    # byte-identical: فایل حتی ساخته نشده
    assert not self_model.SELF_CLAIMS_PATH.exists()


def test_flag_on_appends_probe_schema() -> None:
    d = _tmp()
    _isolate(d)
    _flag(True)
    try:
        model = self_model.build_model()
        written = self_model.emit_self_claims(model)
        assert written >= 1, written
        assert self_model.SELF_CLAIMS_PATH.exists()

        # رکورد باید key + confidence∈[0,1] داشته باشد (شِمای موردِ انتظارِ probe)
        import json
        rows = [json.loads(ln) for ln in
                self_model.SELF_CLAIMS_PATH.read_text("utf-8").splitlines() if ln.strip()]
        assert rows, "لِجِر خالی است"
        rec = rows[0]
        assert "key" in rec and str(rec["key"]).strip()
        assert "confidence" in rec
        c = float(rec["confidence"])
        assert 0.0 <= c <= 1.0, c

        # calibration_probe حالا ورودیِ ناخالی می‌خواند (کورِ سابق دیگر بینا است)
        claims = calibration_probe._load_claims(calibration_probe.DEFAULT_WINDOW_H)
        assert len(claims) >= 1, "probe هنوز کور است"
        assert claims[0]["key"] == rec["key"]
        assert 0.0 <= claims[0]["confidence"] <= 1.0
    finally:
        _flag(False)


def test_flag_on_is_append_not_truncate() -> None:
    """صدور مکرر = append (idempotent-ish رشد)، نه بازنویسیِ مخرب."""
    d = _tmp()
    _isolate(d)
    _flag(True)
    try:
        model = self_model.build_model()
        self_model.emit_self_claims(model)
        self_model.emit_self_claims(model)
        n = len([ln for ln in
                 self_model.SELF_CLAIMS_PATH.read_text("utf-8").splitlines() if ln.strip()])
        assert n >= 2, n
    finally:
        _flag(False)


def test_emit_is_fail_soft() -> None:
    """نوشتنِ ناممکن (مسیرِ نامعتبر) → صفر، بدونِ استثناء (حلقهٔ فراخوان زنده می‌ماند)."""
    d = _tmp()
    _isolate(d)
    _flag(True)
    try:
        # مسیر را به یک هدفِ ناممکن ببر: یک فایل را به‌عنوانِ دایرکتوریِ والد جا بزن
        bad_parent = d / "afile"
        bad_parent.write_text("x", "utf-8")
        self_model.SELF_CLAIMS_PATH = bad_parent / "sub" / "self-claims.jsonl"
        # alert را هم به tmp ببر تا لِجِرِ زنده لمس نشود
        opsalert = d / "alerts.md"
        import opslib
        opslib.ALERTS_MD = opsalert
        written = self_model.emit_self_claims(self_model.build_model())
        assert written == 0, written
    finally:
        _flag(False)


def test_run_and_persist_reports_claims_and_flag_off_default() -> None:
    """run_and_persist خروجیِ self_claims_written می‌دهد؛ خاموش → 0 و بدونِ لِجِر."""
    d = _tmp()
    _isolate(d)
    _flag(False)
    out = self_model.run_and_persist()
    assert out.get("ok") is True, out
    assert out.get("self_claims_written") == 0, out
    assert not self_model.SELF_CLAIMS_PATH.exists()


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for _t in _tests:
        _t()
        print(f"  ✓ {_t.__name__}")
    print(f"✅ test_self_claims: {len(_tests)}/{len(_tests)} سبز")
