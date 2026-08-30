#!/usr/bin/env python3
"""test_cortex_shadow_wiring.py — WP-A: سیم‌کشیِ SHADOWِ قفسهٔ مردهٔ cortex در run_cycle.

اثبات می‌کند (رأی مالک: هر رفتار پشتِ flagِ موجودِ خودش، پیش‌فرض خاموش، byte-identical):
  * با همهٔ flagها خاموش، run_cycle هیچ‌کدام از ماژول‌های سایه را صدا نمی‌زند و state
    هیچ‌یک از کلیدهای ignition/calibration/consolidate/softwta را ندارد (رفتارِ دست‌نخورده).
  * با روشن‌کردنِ *دقیقاً یک* flag، فقط entrypointِ همان ماژول یک‌بار صدا زده می‌شود و
    فقط کلیدِ متناظر به state اضافه می‌شود.

جدایی کامل: ماژول‌های سنگین (registry/model_router/stress/innervation/align/heart) و خودِ
ماژول‌های مردهٔ cortex همه به spy مونکی‌پچ می‌شوند؛ هیچ فایلِ زنده لمس نمی‌شود (state به tmp).
اجرا: python -X utf8 test_cortex_shadow_wiring.py
"""
from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import tempfile
import types

_HERE = pathlib.Path(__file__).resolve().parent
# _ops/cortex هم پکیج است هم شاملِ cortex.py؛ برای اطمینان از تستِ همین worktree،
# فایلِ cortex.py را مستقیم load می‌کنیم (cortex.py خودش path/opslib را bootstrap می‌کند).
for _p in (_HERE.parent / "budget", _HERE.parent / "cortex"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
_CORTEX_PY = _HERE.parent / "cortex" / "cortex.py"
_spec = importlib.util.spec_from_file_location("cortex_wp_a", _CORTEX_PY)
cortex = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cortex)

_FLAGS = ("CORTEX_IGNITION", "CORTEX_SELF_MONITOR",
          "CORTEX_CONSOLIDATE", "IGNITION_SOFT_WTA_SHADOW")


def _tmp() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp(prefix="cortex-shadow-"))


def _clear_flags() -> None:
    for f in _FLAGS:
        os.environ.pop(f, None)


class _Spy:
    """ماژولِ جعلی با یک entrypointِ شمارنده — به sys.modules تزریق می‌شود."""

    def __init__(self, ret: dict):
        self.calls = 0
        self._ret = ret

    def __call__(self, *a, **k):
        self.calls += 1
        return dict(self._ret)


def _install_spies() -> dict:
    """چهار ماژولِ مرده را با spy جایگزین کن (cortex آن‌ها را lazy import می‌کند)."""
    spies = {
        "ignition": _Spy({"ignited": True, "winner": {"source": "money"},
                          "broadcast_width": 3, "n_candidates": 4}),
        "calibration_probe": _Spy({"n": 2, "brier": 0.1, "aurc": 0.0, "ungraded": 1}),
        "consolidate": _Spy({"flag": True, "n_in": 5, "n_semantic": 2, "archived": 5}),
        "ignition_softwta": _Spy({"winner_current": "money", "winner_soft_wta_shadow": "heart",
                                  "disagreement": True, "n_candidates": 4}),
    }
    entry = {"ignition": "persist", "calibration_probe": "probe",
             "consolidate": "consolidate_once", "ignition_softwta": "shadow_compare"}
    for modname, fn in entry.items():
        m = types.ModuleType(modname)
        setattr(m, fn, spies[modname])
        sys.modules[modname] = m
    return spies


def _isolate_run_cycle(d: pathlib.Path) -> None:
    """cortex را کاملاً به tmp/spy ببر تا run_cycle سبک و بی‌عارضه بماند."""
    cortex.CORTEX_DIR = d
    cortex.STATE_PATH = d / "cortex-state.json"
    cortex.JOURNAL_PATH = d / "journal.jsonl"
    cortex.registry = types.SimpleNamespace(
        sweep=lambda: {"coherence": 1.0, "stale_members": [], "members": [], "n": 0})
    cortex.model_router = types.SimpleNamespace(
        keys_present=lambda: [], paid_gate=lambda: (False, "no-key"))
    cortex.align_work_plan = lambda sweep: {"changed": False, "reason": "test"}
    cortex.stress_tick = lambda cycle: None
    cortex.innervation_tick = lambda cycle: None
    cortex.heart_rhythm_period = lambda: (120.0, "test")


def test_all_flags_off_is_byte_identical_noop() -> None:
    d = _tmp()
    _isolate_run_cycle(d)
    spies = _install_spies()
    _clear_flags()
    state = cortex.run_cycle(1)                        # cycle=1 → think/improve هم skip
    for name, spy in spies.items():
        assert spy.calls == 0, f"{name} با flag خاموش صدا زده شد ({spy.calls})"
    for key in ("ignition", "calibration", "consolidate", "softwta"):
        assert key not in state, f"کلیدِ {key} با flag خاموش نباید در state باشد"


def test_ignition_flag_on_invokes_only_ignition() -> None:
    d = _tmp()
    _isolate_run_cycle(d)
    spies = _install_spies()
    _clear_flags()
    os.environ["CORTEX_IGNITION"] = "1"
    try:
        state = cortex.run_cycle(1)
    finally:
        _clear_flags()
    assert spies["ignition"].calls == 1, spies["ignition"].calls
    assert spies["calibration_probe"].calls == 0
    assert spies["consolidate"].calls == 0
    assert spies["ignition_softwta"].calls == 0
    assert state.get("ignition", {}).get("winner") == "money"
    for key in ("calibration", "consolidate", "softwta"):
        assert key not in state


def test_calibration_flag_on_invokes_only_calibration() -> None:
    d = _tmp()
    _isolate_run_cycle(d)
    spies = _install_spies()
    _clear_flags()
    os.environ["CORTEX_SELF_MONITOR"] = "1"
    try:
        state = cortex.run_cycle(1)
    finally:
        _clear_flags()
    assert spies["calibration_probe"].calls == 1
    assert spies["ignition"].calls == 0
    assert spies["consolidate"].calls == 0
    assert spies["ignition_softwta"].calls == 0
    assert state.get("calibration", {}).get("n") == 2
    for key in ("ignition", "consolidate", "softwta"):
        assert key not in state


def test_consolidate_flag_on_invokes_only_consolidate() -> None:
    d = _tmp()
    _isolate_run_cycle(d)
    spies = _install_spies()
    _clear_flags()
    os.environ["CORTEX_CONSOLIDATE"] = "1"
    try:
        state = cortex.run_cycle(1)
    finally:
        _clear_flags()
    assert spies["consolidate"].calls == 1
    assert spies["ignition"].calls == 0
    assert spies["calibration_probe"].calls == 0
    assert spies["ignition_softwta"].calls == 0
    assert state.get("consolidate", {}).get("n_semantic") == 2
    for key in ("ignition", "calibration", "softwta"):
        assert key not in state


def test_softwta_flag_on_invokes_only_softwta() -> None:
    d = _tmp()
    _isolate_run_cycle(d)
    spies = _install_spies()
    _clear_flags()
    os.environ["IGNITION_SOFT_WTA_SHADOW"] = "1"
    try:
        state = cortex.run_cycle(1)
    finally:
        _clear_flags()
    assert spies["ignition_softwta"].calls == 1
    assert spies["ignition"].calls == 0
    assert spies["calibration_probe"].calls == 0
    assert spies["consolidate"].calls == 0
    assert state.get("softwta", {}).get("disagreement") is True
    for key in ("ignition", "calibration", "consolidate"):
        assert key not in state


def test_calibration_lenient_flag_truthy_values() -> None:
    """CORTEX_SELF_MONITOR باید با هر truthy (نه فقط '1') روشن شود — قراردادِ خودِ ماژول."""
    d = _tmp()
    _isolate_run_cycle(d)
    spies = _install_spies()
    _clear_flags()
    os.environ["CORTEX_SELF_MONITOR"] = "yes"
    try:
        cortex.run_cycle(1)
    finally:
        _clear_flags()
    assert spies["calibration_probe"].calls == 1


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items())
              if k.startswith("test_") and callable(v)]
    for _t in _tests:
        _t()
        print(f"  ✓ {_t.__name__}")
    print(f"✅ test_cortex_shadow_wiring: {len(_tests)}/{len(_tests)} سبز")
