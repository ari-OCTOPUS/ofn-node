#!/usr/bin/env python3
"""test_leg_feed.py — خوراکِ حسّی پاها (2026-08-12). $0 · harness ایزوله."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("leg-feed")
_OPS = harness.SELF_OPS
for _p in [str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import leg_feed  # noqa: E402
import leg_cultivate  # noqa: E402
import wiring  # noqa: E402


def t_ensure_food_drops_all_legs():
    r = leg_feed.ensure_food(force=True)
    assert not r["errors"], r
    assert {x["leg"] for x in r["fed"]} == set(leg_cultivate.CULTIVATED_LEGS)
    assert set(r["pulses"]) == {"mining", "ziman"}
    for leg in leg_cultivate.CULTIVATED_LEGS:
        box = opslib.STATE_DIR / "legs" / f"{leg}-inbox"
        assert list(box.glob("sense-*.json")), leg


def t_ensure_food_idempotent_same_day():
    leg_feed.ensure_food(force=True)
    r2 = leg_feed.ensure_food(force=False)
    assert r2["fed"] == []
    assert set(r2["skipped"]) == set(leg_cultivate.CULTIVATED_LEGS)


def t_feed_then_cultivate_clears_starved_and_stale():
    leg_feed.ensure_food(force=True)
    cult = leg_cultivate.cultivate_all(write_report=True)
    assert cult["starved_legs"] == [], cult["starved_legs"]
    assert cult["stale_legs"] == [], cult["stale_legs"]
    for leg, d in cult["legs"].items():
        assert d.get("digested", 0) >= 1, (leg, d)
        assert d.get("starved") is False, (leg, d)
        assert d.get("stale_source") is False, (leg, d)


def t_wiring_feed_flag_off_no_auto_feed():
    os.environ["OCTOPUS_WIRE_LEG_CULTIVATE"] = "1"
    os.environ.pop("OCTOPUS_WIRE_LEG_FEED", None)
    try:
        # empty inboxes → starved still possible
        wiring._EPOCH_STATE.clear()
        r = wiring.legs_cultivation_beat(beat=60)
        assert r is not None
        assert r.get("feed") is None
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEG_CULTIVATE", None)


def t_wiring_feed_flag_on_feeds():
    os.environ["OCTOPUS_WIRE_LEG_CULTIVATE"] = "1"
    os.environ["OCTOPUS_WIRE_LEG_FEED"] = "1"
    try:
        # fresh day marker so ensure_food drops again in this sandbox
        last = opslib.STATE_DIR / "legs" / "cultivation-last.json"
        if last.exists():
            last.unlink()
        for leg in leg_cultivate.CULTIVATED_LEGS:
            box = opslib.STATE_DIR / "legs" / f"{leg}-inbox"
            if box.is_dir():
                for p in box.rglob("sense-*.json"):
                    try:
                        p.unlink()
                    except OSError:
                        pass
                seen = box / "processed" / "_seen.json"
                if seen.exists():
                    seen.unlink()
        wiring._EPOCH_STATE.clear()
        r = wiring.legs_cultivation_beat(beat=60)
        assert r is not None
        assert r.get("feed") is not None
        assert r["feed"]["fed"], r["feed"]
        assert r["starved_legs"] == [], r
        assert r["stale_legs"] == [], r
        assert r["digested_total"] >= 5, r
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEG_CULTIVATE", None)
        os.environ.pop("OCTOPUS_WIRE_LEG_FEED", None)


if __name__ == "__main__":
    failed = harness.run([
        ("ensure_food drops all legs", t_ensure_food_drops_all_legs),
        ("idempotent same day", t_ensure_food_idempotent_same_day),
        ("cultivate clears starved+stale", t_feed_then_cultivate_clears_starved_and_stale),
        ("wiring feed off", t_wiring_feed_flag_off_no_auto_feed),
        ("wiring feed on", t_wiring_feed_flag_on_feeds),
    ])
    sys.exit(1 if failed else 0)
