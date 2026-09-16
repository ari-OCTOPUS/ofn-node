"""test_cockpit_golive_honesty.py — برنامه ۹ (2026-07-16): صداقتِ کابین پس از GO-LIVE.
چهار دروغِ سطحِ تصمیمِ مالک قفل می‌شوند:
  (۱) bundleِ exportِ کهنه هرگز بر stateِ زندهٔ تازه‌تر برنده نمی‌شود (mtime-guard)؛
  (۲) قفل‌های hardcodeِ «🔴 قفل تا 2026-07-21» → وضعیتِ زنده از فایلِ ACTIVATION + live_gate_open؛
  (۳) کورتکسِ مرده (cortex-state.json کهنه‌تر از ۲h) هرگز «در حالِ فکر» رندر نمی‌شود؛
  (۴) /health گیت‌های ACTIVATIONِ مسلح را از فایل می‌شمارد و نام می‌برد.
"""
import datetime as _dt
import json
import os
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("cockpit_golive_honesty")

import opslib  # noqa: E402
import cockpit_readmodel as crm  # noqa: E402
from approval_channel import TelegramApprovalChannel  # noqa: E402

OPS = Path(ENV["ops"])


def _chan(state_dir):
    return TelegramApprovalChannel(state_dir=str(state_dir))


def _cleanup_flags():
    for f in OPS.glob("ACTIVATION-*.flag"):
        f.unlink()


def _mk_state(td: Path, bundle_age_s=None, live_age_s=None):
    """fixture: bundle (halted=True) + live (halted=False) با mtimeهای کنترل‌شده —
    اختلافِ عمدی تا معلوم شود کدام منبع رندر شده."""
    now = time.time()
    if bundle_age_s is not None:
        exp = td / "export"
        exp.mkdir(parents=True, exist_ok=True)
        bp = exp / "octopus-status-bundle.json"
        bp.write_text(json.dumps({
            "organism_state": {"halted": True, "ts": "2026-07-10T09:00:00"},
            "genome_ledger": {"records": 5}}), "utf-8")
        os.utime(bp, (now - bundle_age_s, now - bundle_age_s))
    if live_age_s is not None:
        lp = td / "ORGANISM-STATE.json"
        lp.write_text(json.dumps({"halted": False,
                                  "ts": "2026-07-16T09:00:00"}), "utf-8")
        os.utime(lp, (now - live_age_s, now - live_age_s))


# ── (۱) mtime-guardِ bundle ─────────────────────────────────────────────────────
def t_stale_bundle_loses_to_fresh_live():
    """bundleِ ۵روزه + liveِ ۱دقیقه‌ای → bundle کنار می‌رود، rules از live می‌خواند."""
    with tempfile.TemporaryDirectory() as td:
        st = Path(td)
        _mk_state(st, bundle_age_s=5 * 24 * 3600, live_age_s=60)
        rm = crm.CockpitReadModel(state_dir=st, ops_dir=st)
        assert rm.read_bundle() == {}, "bundleِ کهنه‌تر از live نباید برگردد"
        r2 = next(r for r in rm.rules() if r["id"] == "R2")
        assert r2["status"] == "🟢", f"halted باید از liveِ تازه (False) بیاید: {r2}"


def t_fresh_bundle_wins():
    """bundleِ ۱دقیقه‌ای + liveِ ۵روزه → bundle همچنان منبعِ اول است."""
    with tempfile.TemporaryDirectory() as td:
        st = Path(td)
        _mk_state(st, bundle_age_s=60, live_age_s=5 * 24 * 3600)
        rm = crm.CockpitReadModel(state_dir=st, ops_dir=st)
        assert (rm.read_bundle().get("genome_ledger") or {}).get("records") == 5
        r2 = next(r for r in rm.rules() if r["id"] == "R2")
        assert r2["status"] == "🔴", "bundleِ تازه‌تر منبع است (halted=True)"


def t_bundle_without_live_sources_still_failsoft():
    """هیچ فایلِ زنده‌ای نیست → bundle (حتی کهنه) همان fail-softِ قبلی می‌ماند."""
    with tempfile.TemporaryDirectory() as td:
        st = Path(td)
        _mk_state(st, bundle_age_s=5 * 24 * 3600, live_age_s=None)
        rm = crm.CockpitReadModel(state_dir=st, ops_dir=st)
        assert rm.read_bundle() != {}, "بدونِ منبعِ زنده، bundle نباید دور ریخته شود"


# ── (۲) قفل‌های ACTIVATION از فایل، نه hardcode ─────────────────────────────────
def t_activation_absent_renders_locked():
    _cleanup_flags()
    with tempfile.TemporaryDirectory() as td:
        ch = _chan(td)
        money = ch._tab_text("money")
        assert "گاورنرِ LLM: 🔴 قفل تا 2026-07-21" in money, money
        assert "مسلح (فلگ + سپرِ تاریخ باز)" not in money
        gov = ch._render_card("money", "governor")
        assert "🔴 قفل تا 2026-07-21" in gov and "غایب" in gov, gov


def t_activation_armed_renders_green():
    """فلگ + GO-LIVE → گیت باز → 🟢 مسلح (در money-tab، کارتِ governor و کارتِ debate)."""
    _cleanup_flags()
    for f in ("ACTIVATION-GO-LIVE.flag", "ACTIVATION-GOVERNOR-LLM.flag",
              "ACTIVATION-DEBATE.flag"):
        (OPS / f).write_text("owner", "utf-8")
    try:
        with tempfile.TemporaryDirectory() as td:
            ch = _chan(td)
            money = ch._tab_text("money")
            assert "گاورنرِ LLM: 🟢 مسلح (فلگ + سپرِ تاریخ باز)" in money, money
            gov = ch._render_card("money", "governor")
            assert "🟢 مسلح" in gov and "قفل تا 2026-07-21 —" not in gov, gov
            llm = ch._render_card("safety", "llm")
            assert "مناظره: 🟢 مسلح" in llm, llm
    finally:
        _cleanup_flags()


def t_activation_armed_but_date_blocked_is_partial():
    """فلگ هست ولی GO-LIVE نیست و سپرِ تاریخ بسته → 🟡 صادقانه (نه سبز، نه قفلِ کور)."""
    _cleanup_flags()
    (OPS / "ACTIVATION-GOVERNOR-LLM.flag").write_text("owner", "utf-8")
    real_date = opslib.LIVE_GATE_DATE
    opslib.LIVE_GATE_DATE = _dt.date(2099, 1, 1)   # سپرِ تاریخ قطعاً بسته
    try:
        with tempfile.TemporaryDirectory() as td:
            gov = _chan(td)._render_card("money", "governor")
            assert "🟡 فلگ مسلح ولی سپرِ تاریخ بسته" in gov, gov
            assert "🟢" not in gov and "2099-01-01" in gov
    finally:
        opslib.LIVE_GATE_DATE = real_date
        _cleanup_flags()


# ── (۳) کورتکسِ کهنه هرگز «در حالِ فکر» نیست ────────────────────────────────────
def _write_cortex(st: Path, age_s: float):
    cx = st / "cortex"
    cx.mkdir(parents=True, exist_ok=True)
    p = cx / "cortex-state.json"
    p.write_text(json.dumps({"schema": "cortex-state.v1", "coherence": 0.9,
                             "thought": "فکرِ قدیمی", "brains": {}, "rhythm": {}}),
                 "utf-8")
    old = time.time() - age_s
    os.utime(p, (old, old))


def t_cortex_stale_renders_dead():
    with tempfile.TemporaryDirectory() as td:
        st = Path(td)
        _write_cortex(st, age_s=6 * 24 * 3600)      # فریزشده از ۶ روز پیش
        out = _chan(st)._tab_text("cortex")
        assert "⚫ کورتکس خاموش/کهنه" in out and "سن:" in out, out
        assert "d)" in out, f"سنِ چندروزه باید بر حسبِ روز باشد: {out}"
        assert "coherence" not in out, "stateِ کهنه نباید «الان» رندر شود"
        assert "کهنه" in out and "فکرِ قدیمی" in out   # محتوا با برچسبِ صادق، نه پنهان


def t_cortex_fresh_renders_normal():
    with tempfile.TemporaryDirectory() as td:
        st = Path(td)
        _write_cortex(st, age_s=60)                  # یک دقیقه پیش
        out = _chan(st)._tab_text("cortex")
        assert "⚫" not in out and "coherence" in out, out


# ── (۴) /health: گیت‌های مسلح از فایل ───────────────────────────────────────────
def t_health_lists_armed_gates():
    _cleanup_flags()
    (OPS / "ACTIVATION-GO-LIVE.flag").write_text("owner", "utf-8")
    (OPS / "ACTIVATION-PULSE.flag").write_text("owner", "utf-8")
    try:
        with tempfile.TemporaryDirectory() as td:
            out = _chan(td)._cmd_health()
            assert "گیت‌های مسلح: 2" in out, out
            assert "GO-LIVE" in out and "PULSE" in out, out
    finally:
        _cleanup_flags()


def t_health_zero_gates_honest():
    _cleanup_flags()
    with tempfile.TemporaryDirectory() as td:
        out = _chan(td)._cmd_health()
        assert "گیت‌های مسلح: 0" in out, out


if __name__ == "__main__":
    failed = harness.run([
        ("bundleِ کهنه ← liveِ تازه برنده", t_stale_bundle_loses_to_fresh_live),
        ("bundleِ تازه برنده می‌ماند", t_fresh_bundle_wins),
        ("bundle بدونِ منبعِ زنده fail-soft", t_bundle_without_live_sources_still_failsoft),
        ("ACTIVATION غایب → قفل با تاریخِ واقعی", t_activation_absent_renders_locked),
        ("ACTIVATION+GO-LIVE → 🟢 مسلح", t_activation_armed_renders_green),
        ("فلگ بدونِ GO-LIVE → 🟡 صادق", t_activation_armed_but_date_blocked_is_partial),
        ("کورتکسِ کهنه → ⚫ نه «در حالِ فکر»", t_cortex_stale_renders_dead),
        ("کورتکسِ تازه → رندرِ عادی", t_cortex_fresh_renders_normal),
        ("/health گیت‌های مسلح را می‌شمارد", t_health_lists_armed_gates),
        ("/health صفرِ صادق", t_health_zero_gates_honest),
    ])
    print(f"\n{'✅ PASS' if not failed else '❌ FAIL'} test_cockpit_golive_honesty "
          f"({10 - failed}/10)")
    sys.exit(1 if failed else 0)
