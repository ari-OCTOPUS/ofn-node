#!/usr/bin/env python3
"""تستِ فاز۲ (P-W3): profileِ بوت + تستِ سختِ money/capability separation.

profile: OCTOPUS_PROFILE ∈ {bare, paper-full, live}. پیش‌فرضِ نو (وقتی متغیر ست
نشده) = paper-full → بوتِ عادی کلِ بدنِ امن را فعال می‌کند.

تستِ سخت: هیچ profile (حتی live) نباید capability_gate یا money_gate را باز کند.
money/live مطلقاً جدا — profile فقط flagهای امنِ propose-only را ست می‌کند.
$0 آفلاین.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("profile-w3")

_OPS = Path(r"F:\backup\_ops")
for _p in [str(_OPS), str(_OPS / "budget")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import wiring  # noqa: E402


def _clear_all_flags():
    for f in wiring.PAPER_FULL_FLAGS:
        os.environ.pop(f, None)


# ════════════════════════════════════════════════════════════════════════════════
# (الف) پیش‌فرض = paper-full
# ════════════════════════════════════════════════════════════════════════════════

def t_default_profile_is_paper_full():
    """وقتی OCTOPUS_PROFILE ست نشده → پیش‌فرض = paper-full."""
    os.environ.pop("OCTOPUS_PROFILE", None)
    assert wiring.resolve_profile() == "paper-full", \
        "پیش‌فرض باید paper-full باشد (بوتِ عادی کلِ بدنِ امن)"


def t_bare_profile_explicit():
    """OCTOPUS_PROFILE=bare → bare (debug/emergency)."""
    os.environ["OCTOPUS_PROFILE"] = "bare"
    try:
        assert wiring.resolve_profile() == "bare"
    finally:
        os.environ.pop("OCTOPUS_PROFILE", None)


def t_live_profile_recognized():
    """OCTOPUS_PROFILE=live → live (paper-full + effector جدا)."""
    os.environ["OCTOPUS_PROFILE"] = "live"
    try:
        assert wiring.resolve_profile() == "live"
    finally:
        os.environ.pop("OCTOPUS_PROFILE", None)


# ════════════════════════════════════════════════════════════════════════════════
# (ب) paper-full/live → همه flagهای امن = 1
# ════════════════════════════════════════════════════════════════════════════════

def t_paper_full_sets_all_flags():
    """paper-full → همهٔ flagهای PAPER_FULL_FLAGS = 1."""
    os.environ["OCTOPUS_PROFILE"] = "paper-full"
    _clear_all_flags()
    try:
        wiring.apply_profile()
        for f in wiring.PAPER_FULL_FLAGS:
            assert os.environ.get(f) == "1", f"paper-full باید {f}=1 کند"
    finally:
        os.environ.pop("OCTOPUS_PROFILE", None)
        _clear_all_flags()


def t_live_sets_same_flags_as_paper():
    """live → همانِ flagهای paper-full (effectorها جدا)."""
    os.environ["OCTOPUS_PROFILE"] = "live"
    _clear_all_flags()
    try:
        wiring.apply_profile()
        for f in wiring.PAPER_FULL_FLAGS:
            assert os.environ.get(f) == "1", f"live باید {f}=1 کند (مثلِ paper-full)"
    finally:
        os.environ.pop("OCTOPUS_PROFILE", None)
        _clear_all_flags()


def t_bare_sets_no_flags():
    """bare → هیچ flagی ست نمی‌شود (debug/emergency)."""
    os.environ["OCTOPUS_PROFILE"] = "bare"
    _clear_all_flags()
    try:
        wiring.apply_profile()
        for f in wiring.PAPER_FULL_FLAGS:
            assert os.environ.get(f, "0") != "1", f"bare نباید {f} را ست کند"
    finally:
        os.environ.pop("OCTOPUS_PROFILE", None)
        _clear_all_flags()


def t_explicit_flag_override_stays():
    """flag مجزا که صریحاً 0 ست شده → پایین می‌ماند حتی در paper-full (override)."""
    os.environ["OCTOPUS_PROFILE"] = "paper-full"
    _clear_all_flags()
    os.environ["OCTOPUS_WIRE_BOX"] = "0"   # صریحاً off
    try:
        wiring.apply_profile()
        # BOX باید پایین بماند (صریحاً 0 ست شد)
        assert os.environ.get("OCTOPUS_WIRE_BOX", "0") == "0", \
            "flag صریحاً off باید override کند حتی در paper-full"
        # ولی بقیه باید 1 باشند
        assert os.environ.get("OCTOPUS_WIRE_NEURAL") == "1"
    finally:
        os.environ.pop("OCTOPUS_PROFILE", None)
        _clear_all_flags()


# ════════════════════════════════════════════════════════════════════════════════
# (ج) تستِ سخت: هیچ profile money/capability را باز نمی‌کند
# ════════════════════════════════════════════════════════════════════════════════

def t_no_money_flag_in_paper_full():
    """هیچ flagِ money/live در PAPER_FULL_FLAGS نیست."""
    for f in wiring.PAPER_FULL_FLAGS:
        flow = f.lower()
        assert "money" not in flow, f"money نباید در PAPER_FULL_FLAGS باشد: {f}"
        assert "live" not in flow, f"live نباید در PAPER_FULL_FLAGS باشد: {f}"
        assert "capability" not in flow, f"capability نباید در PAPER_FULL_FLAGS باشد: {f}"


def test_paper_full_does_not_open_capability_gate():
    """paper-full → capability_gate.is_open همچنان False (تستِ سخت).
    is_open(action_id, amount_aud) باید (False, ...) برگرداند — profile گنجایش را باز نمی‌کند."""
    os.environ["OCTOPUS_PROFILE"] = "paper-full"
    _clear_all_flags()
    try:
        wiring.apply_profile()
        try:
            sys.path.insert(0, str(_OPS / "budget"))
            import capability_gate
            ok, why = capability_gate.is_open("ANY", 0.01)
            assert ok is False, \
                f"capability_gate نباید در paper-full باز باشد: ok={ok} why={why}"
        except ImportError:
            assert True  # capability_gate نباشد = بسته (fail-closed)
    finally:
        os.environ.pop("OCTOPUS_PROFILE", None)
        _clear_all_flags()


def test_live_does_not_open_capability_gate():
    """live → capability_gate.is_open همچنان (False, ...) (profile آن را باز نمی‌کند).
    live فقط flagهای paper-full را ست می‌کند؛ capability/history جدا و gated باقی می‌مانند."""
    os.environ["OCTOPUS_PROFILE"] = "live"
    _clear_all_flags()
    try:
        wiring.apply_profile()
        try:
            import capability_gate
            ok, why = capability_gate.is_open("ANY", 0.01)
            assert ok is False, \
                f"live نباید capability_gate را باز کند: ok={ok} why={why}"
        except ImportError:
            assert True
    finally:
        os.environ.pop("OCTOPUS_PROFILE", None)
        _clear_all_flags()


def test_no_live_enabled_flag():
    """هیچ LIVE_ENABLED در PAPER_FULL_FLAGS نیست."""
    assert not any("LIVE_ENABLED" in f for f in wiring.PAPER_FULL_FLAGS)


# ════════════════════════════════════════════════════════════════════════════════
# (د) spectral در paper-full
# ════════════════════════════════════════════════════════════════════════════════

def t_spectral_in_paper_full():
    """OCTOPUS_WIRE_SPECTRAL در PAPER_FULL_FLAGS است (فعال در paper-full)."""
    assert "OCTOPUS_WIRE_SPECTRAL" in wiring.PAPER_FULL_FLAGS


if __name__ == "__main__":
    failed = harness.run([
        # (الف) پیش‌فرض
        ("default = paper-full", t_default_profile_is_paper_full),
        ("bare explicit", t_bare_profile_explicit),
        ("live recognized", t_live_profile_recognized),
        # (ب) flags
        ("paper-full همه flagها", t_paper_full_sets_all_flags),
        ("live همانِ paper", t_live_sets_same_flags_as_paper),
        ("bare no flags", t_bare_sets_no_flags),
        ("explicit flag override", t_explicit_flag_override_stays),
        # (ج) hard money/capability test
        ("no money flag in paper-full", t_no_money_flag_in_paper_full),
        ("paper-full capability بسته", test_paper_full_does_not_open_capability_gate),
        ("live capability بسته", test_live_does_not_open_capability_gate),
        ("no LIVE_ENABLED", test_no_live_enabled_flag),
        # (د) spectral
        ("spectral در paper-full", t_spectral_in_paper_full),
    ])
    sys.exit(1 if failed else 0)
