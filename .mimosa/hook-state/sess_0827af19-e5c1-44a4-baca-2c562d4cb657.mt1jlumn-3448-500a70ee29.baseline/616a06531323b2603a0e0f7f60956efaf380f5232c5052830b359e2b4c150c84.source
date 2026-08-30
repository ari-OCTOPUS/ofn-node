"""test_lead_wiring.py — همگرایی و سیم‌کشیِ بخشِ نقاشی/لید (2026-07-21).

اثبات می‌کند: (الف) گاردِ تصادمِ دو inbox در lead_sense (LD-*/_* skip، نه reject-move) ·
(ب) مسیرِ canonicalِ owner_menu → submit_candidate پشتِ OCTOPUS_WIRE_LEAD_CANDIDATES ·
(ج) source-guardها که فیکسِ EffectorGate(db=None)، launcherِ boundary، و freezeِ inboxِ
قدیمی واقعاً در کد نشسته‌اند. همه flag-off = parity؛ صفر ارسال. center/wiring از همین worktree
(نه REAL_VAULT که به درختِ زنده resolve می‌شود) خوانده می‌شوند.
"""
import importlib
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
sys.path.insert(0, str(_HERE))
import harness
ENV = harness.setup("lead-wiring")
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget"), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                     # noqa: E402
importlib.reload(opslib)
import lead_sense                 # noqa: E402
importlib.reload(lead_sense)
import owner_menu                 # noqa: E402
importlib.reload(owner_menu)

WIRING_SRC = (_OPS / "wiring.py").read_text("utf-8")
ORGANISM_SRC = (_OPS / "organism.py").read_text("utf-8")
LLI_SRC = (_OPS / "legs" / "lead_leg_inbox.py").read_text("utf-8")


def _inbox():
    box = opslib.STATE_DIR / "legs" / "lead-inbox"
    box.mkdir(parents=True, exist_ok=True)
    return box


def t_a_collision_guard_skips_reserved():
    """LD-* (inboxِ قدیمیِ frozen) و _* (داخلی) skip می‌شوند — نه خوانده، نه reject-move.
    فقط فایلِ description-دار خوانده می‌شود."""
    import json
    box = _inbox()
    (box / "LD-abc123.json").write_text(json.dumps({"lead_id": "LD-abc123", "raw_text": "x"}), "utf-8")
    (box / "_control.json").write_text(json.dumps({"internal": True}), "utf-8")
    (box / "good.json").write_text(json.dumps({"lead_id": "g1", "description": "interior repaint"}), "utf-8")
    out = lead_sense.read_inbox()
    names = [p.name for p, _ in out]
    assert names == ["good.json"], names
    # LD-* هرگز به rejected/ منتقل نشد (حفظ شد)
    assert (box / "LD-abc123.json").exists()
    assert not (box / "rejected").exists() or not any(
        p.name.startswith("LD-") for p in (box / "rejected").glob("*.json"))


def t_b_canonical_route_flag_on_writes_via_submit():
    """OCTOPUS_WIRE_LEAD_CANDIDATES روشن → owner_menu متنِ آزادِ مالک را از submit_candidate
    می‌برد (consented_inbound explicit) و فایلِ description-دار می‌نویسد."""
    os.environ["OCTOPUS_WIRE_LEAD_CANDIDATES"] = "1"
    try:
        rec = owner_menu._register_lead_canonical("نقاشی داخلی ۳ خوابه موزمن قیمت می‌خوام")
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_CANDIDATES", None)
    assert isinstance(rec, dict) and rec.get("ok") and rec.get("status") == "accepted", rec
    assert rec.get("candidate_type") == "consented_inbound"
    # فایلِ top-levelِ خوانا توسطِ lead_sense نوشته شد
    seen = lead_sense.read_inbox()
    assert any(d.get("lead_id") == rec["lead_id"] and d.get("description") for _, d in seen), seen


def t_c_canonical_route_flag_off_is_none():
    """flag خاموش → None (تا caller به مسیرِ frozenِ قدیمی fallback کند) — parity."""
    os.environ.pop("OCTOPUS_WIRE_LEAD_CANDIDATES", None)
    assert owner_menu._register_lead_canonical("هر متنی") is None


def t_d_effectorgate_db_fixed_in_source():
    """کرشِ نهفته بسته شد: دیگر EffectorGate(db=None) نیست؛ ChronoDBِ واقعی تزریق می‌شود."""
    assert "EffectorGate(db=None)" not in WIRING_SRC
    assert "EffectorGate(db=_gate_db)" in WIRING_SRC
    assert "ChronoDB(str(opslib.STATE_DIR / \"chrono.db\"))" in WIRING_SRC


def t_e_boundary_launcher_wired_and_flag_gated():
    """launcherِ boundary در wiring هست، flag-gated، و organism صدایش می‌زند."""
    assert "def maybe_start_lead_boundary" in WIRING_SRC
    fn = WIRING_SRC.split("def maybe_start_lead_boundary")[1].split("\ndef ")[0]
    assert 'os.environ.get("OCTOPUS_WIRE_LEAD_BOUNDARY") != "1"' in fn
    assert "return None" in fn                       # flag-off → None (parity)
    assert "127.0.0.1" in fn or "loopback" in fn     # loopback-only
    assert "_w.maybe_start_lead_boundary()" in ORGANISM_SRC


def t_f_old_inbox_frozen():
    """lead_leg_inbox هدرِ FROZEN + منسوخ‌سازیِ فلگ دارد."""
    assert "FROZEN" in LLI_SRC and "lead_candidate_inbox" in LLI_SRC
    assert "DEPRECATED" in LLI_SRC


def t_g_owner_menu_prefers_canonical_over_frozen():
    """ساختاری: handle_new_mission اول canonical را صدا می‌زند، بعد fallback به frozen."""
    src = Path(owner_menu.__file__).read_text("utf-8")
    i_can = src.find("_register_lead_canonical(intent)")
    i_old = src.find('_lazy("legs.lead_leg_inbox")')
    assert 0 < i_can < i_old, (i_can, i_old)   # canonical قبل از fallback


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_wiring: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
