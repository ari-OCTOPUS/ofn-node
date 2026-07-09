#!/usr/bin/env python3
"""تستِ رفتاریِ P-N2: سیم‌کشیِ کلِ خوشهٔ box به Doctor.

گپِ connectivity-audit: کلِ خوشهٔ box (۱۲ فایل) shelfware بود — هیچ مسیرِ runtime
صدایشان نمی‌زد. حالا پشتِ flagِ نو OCTOPUS_WIRE_BOX در run_cycle سیم‌کشی شد:
Box.run_tick → bottlenecks adapter → b3_bridge.box_to_doctor_pipeline →
doctor.submit (propose-only، human-gate). b4_fusion.compute_phi_t = novelty.
falsif_suite = کنترلِ دوره‌ای.

این تست اثبات می‌کند:
  (الف) flag روشن → Box در چرخه step می‌کند و b3 به doctor propose می‌رسد (نه merge).
  (ب) b4 (φ_t) و falsif فعال‌اند (در گزارش).
  (ج) Warden سقفِ ۲٪ را enforce می‌کند (E_box_max = 0.02 · E_total).
  (د) flag خاموش → no-op (on-shelf، رفتارِ فعلی).
  (هـ) Warden اطاعتِ STOP (kill-switch supreme).
$0 آفلاین، stdlib-only.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("box-wiring")

_OPS = Path(r"F:\backup\_ops")
for _p in [str(_OPS), str(_OPS / "doctor"), str(_OPS / "budget")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from doctor import Doctor  # noqa: E402

# box cluster باید روی path باشد (doctor.py داخلش insert می‌کند ولی برای import مستقیم)
for _p in [str(_OPS / "doctor" / "box")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _doctor(box=None):
    return Doctor(state_dir=str(ENV["ops"] / "state"),
                  knowledge_dir=str(ENV["ops"] / "knowledge-internal-test"),
                  box=box)


# ════════════════════════════════════════════════════════════════════════════════
# (الف) flag روشن → Box steps + b3 propose (نه merge)
# ════════════════════════════════════════════════════════════════════════════════

def t_flag_on_box_in_result():
    """flag روشن → run_cycle خروجی کلیدِ 'box' دارد (fire شد)."""
    os.environ["OCTOPUS_WIRE_BOX"] = "1"
    try:
        doc = _doctor()
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
        assert result is not None
        assert "box" in result, "flag on باید box را fire کند"
        box = result["box"]
        assert box.get("stepped") is True, f"Box باید step کند، نه {box}"
    finally:
        os.environ.pop("OCTOPUS_WIRE_BOX", None)


def t_flag_on_box_steps_multiple_ticks():
    """flag روشن → بعد از چند run_cycle، Box.tick_count افزایش می‌یابد."""
    os.environ["OCTOPUS_WIRE_BOX"] = "1"
    try:
        doc = _doctor()
        doc.run_cycle(beat=1, trace={"errors_24h": 3})
        tc1 = doc._box.tick_count
        doc.run_cycle(beat=2, trace={"errors_24h": 3})
        tc2 = doc._box.tick_count
        assert tc2 > tc1, f"tick_count باید افزایش یابد: {tc1} → {tc2}"
    finally:
        os.environ.pop("OCTOPUS_WIRE_BOX", None)


def t_b3_propose_not_merge():
    """b3 از طریقِ doctor.submit می‌گذرد ولی هرگز merge (propose-only، human-gate).

    بدونِ channel → status = 'submitted-no-channel' (pending ابدی)، نه 'merged'."""
    os.environ["OCTOPUS_WIRE_BOX"] = "1"
    try:
        doc = _doctor()
        # آرشیو را پیش‌پُر کن تا bottleneck از Box بیاید (flagged/stress)
        doc.run_cycle(beat=1, trace={"errors_24h": 50})  # load بالا → stress بالا
        # RFCها نباید 'merged' باشند (هیچ channel، هیچ human-append)
        for rfc_id, rfc in doc._rfcs.items():
            assert rfc.status != "merged", \
                f"RFC نباید merge شده باشد (propose-only): {rfc_id} = {rfc.status}"
    finally:
        os.environ.pop("OCTOPUS_WIRE_BOX", None)


def t_box_propose_only_flag():
    """گزارشِ box باید propose_only=True داشته باشد."""
    os.environ["OCTOPUS_WIRE_BOX"] = "1"
    try:
        doc = _doctor()
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
        assert result["box"].get("propose_only") is True
    finally:
        os.environ.pop("OCTOPUS_WIRE_BOX", None)


# ════════════════════════════════════════════════════════════════════════════════
# (ب) b4 (φ_t) + falsif فعال
# ════════════════════════════════════════════════════════════════════════════════

def t_b4_phi_t_in_report():
    """flag روشن → گزارشِ box شاملِ phi_t است (b4_fusion فعال)."""
    os.environ["OCTOPUS_WIRE_BOX"] = "1"
    try:
        doc = _doctor()
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
        phi = result["box"].get("phi_t")
        assert phi is not None, "phi_t باید در گزارش باشد (b4 فعال)"
        assert "available" in phi, "phi_t باید ساختارِ compute_phi_t داشته باشد"
    finally:
        os.environ.pop("OCTOPUS_WIRE_BOX", None)


def test_falsif_runs_periodically():
    """falsif_suite هر N tick اجرا می‌شود (CHRONO_BOX_FALSIF_EVERY_N_TICKS)."""
    os.environ["OCTOPUS_WIRE_BOX"] = "1"
    os.environ["CHRONO_BOX_FALSIF_EVERY_N_TICKS"] = "1"  # هر tick → falsif
    try:
        doc = _doctor()
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
        falsif = result["box"].get("falsif_majority")
        assert falsif is not None, "falsif_majority باید set شده باشد (هر tick)"
        assert isinstance(falsif, bool)
    finally:
        os.environ.pop("OCTOPUS_WIRE_BOX", None)
        os.environ.pop("CHRONO_BOX_FALSIF_EVERY_N_TICKS", None)


def test_falsif_skipped_when_not_due():
    """اگر falsif نوبتش نباشد → falsif_majority=None."""
    os.environ["OCTOPUS_WIRE_BOX"] = "1"
    os.environ["CHRONO_BOX_FALSIF_EVERY_N_TICKS"] = "99999"  # هرگز نوبتش نیست
    try:
        doc = _doctor()
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
        assert result["box"].get("falsif_majority") is None, \
            "falsif نباید اجرا شود وقتی نوبتش نیست"
    finally:
        os.environ.pop("OCTOPUS_WIRE_BOX", None)
        os.environ.pop("CHRONO_BOX_FALSIF_EVERY_N_TICKS", None)


# ════════════════════════════════════════════════════════════════════════════════
# (ج) Warden سقفِ ۲٪ را enforce می‌کند
# ════════════════════════════════════════════════════════════════════════════════

def t_warden_cap_is_2pct():
    """E_box_max = 0.02 · E_total (hard cap)."""
    os.environ["OCTOPUS_WIRE_BOX"] = "1"
    try:
        doc = _doctor()
        doc.run_cycle(beat=1, trace={"errors_24h": 3})
        warden = doc._box.warden
        assert warden.E_box_max == 0.02 * warden.E_total, \
            f"E_box_max باید ۲٪ باشد: {warden.E_box_max} vs {0.02 * warden.E_total}"
        assert "warden_cap_2pct" in doc.run_cycle(beat=2, trace={"errors_24h": 3})["box"]
    finally:
        os.environ.pop("OCTOPUS_WIRE_BOX", None)


def t_warden_obeyed_on_stop():
    """STOP-ORGANISM → Warden yield می‌کند (kill-switch supreme).

    این از طریقِ _stop_file() در warden.py چک می‌شود. توجه: _stop_file() از
    parents[3] محاسبه می‌شود (F:\\backup\\STOP-ORGANISM)، نه opslib.STOP_ORGANISM
    (F:\\backup\\_ops\\STOP-ORGANISM) — پس در همان مسیرِ warden می‌نویسیم."""
    _box_dir = str(_OPS / "doctor" / "box")
    if sys.path[0] != _box_dir:
        if _box_dir in sys.path:
            sys.path.remove(_box_dir)
        sys.path.insert(0, _box_dir)
    sys.modules.pop("box", None)
    sys.modules.pop("warden", None)
    from box import Box, BoxConfig  # noqa: E402
    from warden import _stop_file  # noqa: E402
    box = Box(BoxConfig(E_total=100000))
    stop_path = _stop_file()
    stop_path.write_text("kill", "utf-8")
    try:
        can_go, reason = box.warden.can_continue(box.agents, 0.5)
        assert can_go is False, "STOP باید Warden را halt کند"
        assert "STOP" in reason
    finally:
        try:
            stop_path.unlink()
        except OSError:
            pass


def test_warden_budget_tracked():
    """گزارشِ box باید budget_used و warden_cap را نشان دهد (tracking)."""
    os.environ["OCTOPUS_WIRE_BOX"] = "1"
    try:
        doc = _doctor()
        result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
        box = result["box"]
        assert "budget_used" in box and "warden_cap_2pct" in box
        assert box["budget_used"] <= box["warden_cap_2pct"] + 1e-6, \
            "budget_used نباید از ۲٪ cap بیشتر باشد"
    finally:
        os.environ.pop("OCTOPUS_WIRE_BOX", None)


# ════════════════════════════════════════════════════════════════════════════════
# (د) flag خاموش → no-op (on-shelf، رفتارِ فعلی)
# ════════════════════════════════════════════════════════════════════════════════

def t_flag_off_no_box():
    """flag خاموش → run_cycle بدونِ کلیدِ box (on-shelf)."""
    os.environ.pop("OCTOPUS_WIRE_BOX", None)
    doc = _doctor()
    result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
    assert result is not None
    assert "box" not in result, "flag خاموز نباید box را fire کند"
    assert "rfc_id" in result   # رفتارِ فعلی حفظ شد


def t_flag_off_box_not_created():
    """flag خاموش → Box ساخته نمی‌شود (None می‌ماند)."""
    os.environ.pop("OCTOPUS_WIRE_BOX", None)
    doc = _doctor()
    doc.run_cycle(beat=1, trace={"errors_24h": 3})
    assert doc._box is None, "flag خاموز نباید Box بسازد"


def t_flag_off_legacy_shape():
    """flag خاموش → شکلِ خروجی بدونِ box (evolution ممکن است باشد اگر flagِ دیگر on)."""
    os.environ.pop("OCTOPUS_WIRE_BOX", None)
    os.environ.pop("OCTOPUS_WIRE_EVOLUTION", None)
    doc = _doctor()
    result = doc.run_cycle(beat=1, trace={"errors_24h": 3})
    assert "box" not in result
    assert "evolution" not in result


# ════════════════════════════════════════════════════════════════════════════════
# (هـ) support-libهای box reachable (با wire شدنِ box.py)
# ════════════════════════════════════════════════════════════════════════════════

def test_support_libs_reachable():
    """با wire شدنِ box.py، support-libهایش reachable می‌شوند (import test)."""
    os.environ["OCTOPUS_WIRE_BOX"] = "1"
    try:
        doc = _doctor()
        doc.run_cycle(beat=1, trace={"errors_24h": 3})
        # Box ساخته شده → supportها روی path
        from agent_state import AgentState  # noqa
        from dynamics import f_cognitive  # noqa
        from archivist import Archivist  # noqa
        from topology import build_topology  # noqa
        from sensors import rho_jacobian  # noqa
        from null_dreamer import make_null_dreamer  # noqa
        # اگر اینجا رسیدیم بدونِ ImportError → reachable
        assert doc._box is not None
    finally:
        os.environ.pop("OCTOPUS_WIRE_BOX", None)


def t_non_blocking_with_box():
    """flag روشن → run_cycle همچنان سریع است (box سبک، نه hang)."""
    import time as _t
    os.environ["OCTOPUS_WIRE_BOX"] = "1"
    try:
        doc = _doctor()
        t0 = _t.time()
        doc.run_cycle(beat=1, trace={"errors_24h": 3})
        elapsed = _t.time() - t0
        assert elapsed < 5.0, f"run_cycle با box باید سریع باشد، نه {elapsed:.1f}s"
    finally:
        os.environ.pop("OCTOPUS_WIRE_BOX", None)


if __name__ == "__main__":
    failed = harness.run([
        # (الف) flag on → Box steps + b3 propose
        ("flag on → box در result", t_flag_on_box_in_result),
        ("flag on → tick_count افزایش", t_flag_on_box_steps_multiple_ticks),
        ("b3 propose نه merge", t_b3_propose_not_merge),
        ("propose_only=True در گزارش", t_box_propose_only_flag),
        # (ب) b4 + falsif
        ("b4 phi_t در گزارش", t_b4_phi_t_in_report),
        ("falsif هر N tick", test_falsif_runs_periodically),
        ("falsif skip وقتی نوبت نیست", test_falsif_skipped_when_not_due),
        # (ج) Warden ۲٪
        ("Warden cap = ۲٪", t_warden_cap_is_2pct),
        ("Warden اطاعتِ STOP", t_warden_obeyed_on_stop),
        ("Warden budget tracked", test_warden_budget_tracked),
        # (د) flag off
        ("flag off → no box", t_flag_off_no_box),
        ("flag off → Box ساخته نمی‌شود", t_flag_off_box_not_created),
        ("flag off → legacy shape", t_flag_off_legacy_shape),
        # (هـ) support-lib + non-blocking
        ("support-libهای box reachable", test_support_libs_reachable),
        ("non-blocking با box", t_non_blocking_with_box),
    ])
    sys.exit(1 if failed else 0)
