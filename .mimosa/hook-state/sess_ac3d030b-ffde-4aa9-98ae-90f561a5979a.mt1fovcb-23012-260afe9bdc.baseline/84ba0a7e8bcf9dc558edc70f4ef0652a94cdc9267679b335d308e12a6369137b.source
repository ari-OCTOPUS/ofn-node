#!/usr/bin/env python3
"""test_deadwrite_readers.py — WP5: سطح‌نماییِ فقط‌خواندنیِ سه آرتیفکتِ سایه.

اثبات می‌کند (ORPH-CALIB-LATEST / ORPH-WORK-HEALTH / ORPH-ROUTE-DECISIONS):
  * live/server.py::deadwrite_shadows() سه فایلِ سایه را می‌خواند:
      - نبودِ فایل → present:false (—/absent)، بدونِ کرش.
      - وجودِ فایل → مقادیرِ واقعی سطح‌نمایی می‌شوند.
      - فایلِ خراب (JSON نامعتبر) → present:false، هرگز کرش.
  * پرچمِ default-off (OCTOPUS_WIRE_DEADWRITE_CARDS): خاموش = _deadwrite_flag_on()
    False → کلیدِ deadwrites به ops_state افزوده نمی‌شود (بایت‌همسان).
  * dashboard/server.py::_deadwrite_card() همان قرارداد؛ و page_activity() فقط پشتِ
    پرچم کارت را می‌افزاید (خاموش = "" = صفحهٔ بایت‌همسان).

صفر نوشتن روی مسیرهای زنده: STATE/STATE_DIR به tmp مونکی‌پچ می‌شوند.
اجرا: python -X utf8 test_deadwrite_readers.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sys
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
_OPS = _HERE.parent


def _load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


live = _load(_OPS / "live" / "server.py", "wp5_live_server")
dash = _load(_OPS / "dashboard" / "server.py", "wp5_dash_server")


def _tmp() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp(prefix="deadwrite-test-"))


def _seed(d: pathlib.Path) -> None:
    (d / "cortex").mkdir(parents=True, exist_ok=True)
    (d / "pulse").mkdir(parents=True, exist_ok=True)
    (d / "cortex" / "calibration-latest.json").write_text(
        json.dumps({"n": 5, "brier": 0.12, "aurc": 0.2,
                    "abstain_below": 0.6, "ungraded": 3}), "utf-8")
    (d / "pulse" / "work-health.json").write_text(
        json.dumps({"sigma": 1.4, "period_shadow_s": 300,
                    "gate0": True, "wire_open": False}), "utf-8")
    (d / "cortex" / "route-decisions.jsonl").write_text(
        "\n".join(json.dumps(x) for x in
                  [{"tier": "local", "task": "classify", "est_cost": 0.0},
                   {"tier": "primary", "task": "refactor", "est_cost": 0.05}]), "utf-8")


# ── live/server.py ────────────────────────────────────────────────────────────
def test_live_absent_renders_safe_default() -> None:
    d = _tmp()
    live.STATE = d                          # پوشهٔ خالی — هیچ فایلِ سایه‌ای نیست
    r = live.deadwrite_shadows()
    assert r["calibration"]["present"] is False
    assert r["work_health"]["present"] is False
    assert r["route_decisions"]["present"] is False


def test_live_present_surfaces_values() -> None:
    d = _tmp()
    _seed(d)
    live.STATE = d
    r = live.deadwrite_shadows()
    assert r["calibration"]["present"] is True
    assert r["calibration"]["brier"] == 0.12 and r["calibration"]["n"] == 5
    assert r["work_health"]["present"] is True
    assert r["work_health"]["sigma"] == 1.4 and r["work_health"]["gate0"] is True
    assert r["route_decisions"]["present"] is True
    assert r["route_decisions"]["n"] == 2
    assert r["route_decisions"]["recent"][-1]["tier"] == "primary"


def test_live_corrupt_never_crashes() -> None:
    d = _tmp()
    (d / "cortex").mkdir(parents=True, exist_ok=True)
    (d / "cortex" / "calibration-latest.json").write_text("{not json", "utf-8")
    (d / "cortex" / "route-decisions.jsonl").write_text("garbage\n{bad", "utf-8")
    live.STATE = d
    r = live.deadwrite_shadows()             # نباید استثنا بدهد
    assert r["calibration"]["present"] is False
    assert r["route_decisions"]["present"] is False


def test_live_flag_default_off() -> None:
    os.environ.pop(live.DEADWRITE_FLAG, None)
    assert live._deadwrite_flag_on() is False        # پیش‌فرض خاموش
    os.environ[live.DEADWRITE_FLAG] = "1"
    assert live._deadwrite_flag_on() is True
    os.environ[live.DEADWRITE_FLAG] = "0"
    assert live._deadwrite_flag_on() is False        # "0" = خاموش
    os.environ.pop(live.DEADWRITE_FLAG, None)


# ── dashboard/server.py ───────────────────────────────────────────────────────
def test_dash_card_absent_shows_absent() -> None:
    d = _tmp()
    dash.STATE_DIR = d
    card = dash._deadwrite_card()             # هیچ فایلی نیست
    assert card.count("—/absent") == 3        # هر سه ردیف absent
    assert "آرتیفکت‌های سایه" in card


def test_dash_card_present_shows_values() -> None:
    d = _tmp()
    _seed(d)
    dash.STATE_DIR = d
    card = dash._deadwrite_card()
    assert "0.12" in card and "n=5" in card
    assert "1.4" in card
    assert "primary" in card or "local" in card
    assert "—/absent" not in card            # همه حاضرند


def test_dash_page_activity_gated_by_flag() -> None:
    d = _tmp()
    dash.STATE_DIR = d
    dash.ENV_FILE = d / "no-flags.cmd"        # override-file نامموجود → فقط os.environ
    os.environ.pop(dash.DEADWRITE_FLAG, None)
    body_off = dash.page_activity().decode("utf-8")
    assert "آرتیفکت‌های سایه" not in body_off  # خاموش = کارت غایب (بایت‌همسان)
    os.environ[dash.DEADWRITE_FLAG] = "1"
    body_on = dash.page_activity().decode("utf-8")
    assert "آرتیفکت‌های سایه" in body_on       # روشن = کارت حاضر
    assert "—/absent" in body_on              # فایل‌ها نیستند → absent تمیز
    os.environ.pop(dash.DEADWRITE_FLAG, None)


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for _t in _tests:
        _t()
        print(f"  ✓ {_t.__name__}")
    print(f"✅ test_deadwrite_readers: {len(_tests)}/{len(_tests)} سبز")
