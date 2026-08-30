#!/usr/bin/env python3
"""تست T3: epoch آلوستاتیک (نه clock) + گاورنر سایه dry ($0) + H1."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("epoch")
import opslib          # noqa: E402
import governor_epoch  # noqa: E402
import telemetry       # noqa: E402


def t_allostatic_not_clock():
    base = 60.0
    calm = governor_epoch.epoch_length_minutes(0.0, base)
    tense = governor_epoch.epoch_length_minutes(1.0, base)
    mid = governor_epoch.epoch_length_minutes(0.5, base)
    assert calm == 60.0, calm
    assert tense == 15.0, tense           # clamp به base/4 — «تندتر تپیدن» زیر فشار
    assert 15.0 < mid < 60.0, mid
    assert calm > mid > tense, "طول epoch باید تابع نزولی فشار باشد"


def t_deadline_pressure():
    snap = telemetry.snapshot(write=False)
    p = governor_epoch.pressure_state(snap)
    # PROJECT_F با deadline 2026-07-20 (۱۴ روز مانده از 07-06) → فشار ددلاین > صفر
    assert p["deadline_proximity"] > 0.0, p
    assert "PROJECT_F" in p["deadline_ref"], p


def t_dry_epoch_shadow():
    rec = governor_epoch.run_epoch()
    assert "allostatic" in rec["epoch_mode"]
    assert rec.get("allocation_dry"), rec.keys()
    a = rec["allocation_dry"]
    assert a["h1_check"]["ok"], a["h1_check"]       # H1: جمع grantها ≤ cap
    for organ in ("PROJECT_F", "ARCHITECT_SYS", "GENOME_SYS", "ZIMAN"):
        g = a["grants"][organ]
        assert g["total_month_aud"] >= g["floor_aud"], f"{organ}: floor نقض شد (H2)"
    assert a["explore_reserve_aud"] == 3.0, a["explore_reserve_aud"]   # 10% از 30
    files = list((opslib.BUDGET_DIR / "epochs").glob("epoch-*.json"))
    assert files, "فایل epoch باید نوشته می‌شد"


def t_epoch_logged_to_ledger():
    lg = opslib.genome_ledger()
    notes = [r for r in lg.iter_events()
             if r.get("type") == "NOTE"
             and (r.get("payload") or {}).get("subtype") == "ALLOCATION_SHADOW"]
    assert notes, "ALLOCATION_SHADOW باید در ledger ثبت می‌شد"
    ok, msg = lg.verify()
    assert ok, f"زنجیرهٔ hash شکست: {msg}"


def t_second_epoch_and_state():
    rec = governor_epoch.run_epoch()   # epoch دوم (DoD پک: دو epoch در shadow)
    assert rec.get("allocation_dry")
    files = list((opslib.BUDGET_DIR / "epochs").glob("epoch-*.json"))
    assert len(files) >= 2, len(files)


if __name__ == "__main__":
    failed = harness.run([
        ("epoch آلوستاتیک: تابع نزولی فشار با clamp", t_allostatic_not_clock),
        ("فشار ددلاین PROJECT_F دیده می‌شود (H5)", t_deadline_pressure),
        ("epoch سایه dry: H1/H2/explore + فایل epoch", t_dry_epoch_shadow),
        ("ALLOCATION_SHADOW در ledger + زنجیره سالم", t_epoch_logged_to_ledger),
        ("epoch دوم (DoD: دو epoch سایه)", t_second_epoch_and_state),
    ])
    sys.exit(1 if failed else 0)
