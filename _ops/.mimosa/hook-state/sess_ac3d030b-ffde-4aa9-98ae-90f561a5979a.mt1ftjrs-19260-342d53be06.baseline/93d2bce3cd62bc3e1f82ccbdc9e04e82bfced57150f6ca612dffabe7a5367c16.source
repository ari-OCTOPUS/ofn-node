#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""smoke_live_path.py — $0 offline smoke for LIVE path (no network, no telegram send).

Run:
  python -X utf8 F:\\backup\\_ops\\smoke_live_path.py
Exit 0 = all critical imports + pure functions OK.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "budget"))
sys.path.insert(0, str(_OPS / "telegram_center"))

fails: list[str] = []


def check(cond: bool, label: str) -> None:
    if not cond:
        fails.append(label)
    else:
        print("ok", label)


def main() -> int:
    # 1) identity equations
    import identity_equations as ie
    r = ie.evaluate({
        "delta": 0.01, "n_delta": 10, "phi_max": 5.0, "phi_saturated": 0,
        "sigma": 0.3, "money_confirmed": 0, "c6_done": 1, "c6_pending": 0,
        "c6_seed_ratio": 0.0, "probe_count": 4, "romajan_verified": 2,
        "budget_frac": 0.5, "approvals_pending": 0, "honest_flags": 3,
        "alive": 1.0, "coherence_ok": 0.8, "lead_drafts": 0, "lead_total": 0,
        "missing": [],
    })
    check("identities" in r and "organism" in r["identities"], "identity.evaluate")
    check(0.0 <= r["identities"]["organism"]["value"] <= 1.0, "organism clamp")
    check("kill" in r["identities"]["learner"], "learner kill present")
    card = ie.card(r)
    check(len(card) > 40, "identity.card")

    # 2) blackbox map
    import blackbox_map as bm
    s = bm.survey()
    check(s.get("n", 0) >= 4, "blackbox.survey n>=4")
    check("c6_live_loop" in {i["id"] for i in s["items"]}, "c6 in catalog")
    check(len(bm.card()) > 20, "blackbox.card")

    # 3) collab coding (temp queue)
    tmp = tempfile.mkdtemp(prefix="smoke-collab-")
    os.environ["OCTOPUS_WIRE_COLLAB_CODING"] = "1"
    import collab_coding as cc
    cc.STATE = Path(tmp) / "collab"
    cc.QUEUE = cc.STATE / "proposals.jsonl"
    pr = cc.propose("بهبود scorer برای لید strata")
    check(pr.get("ok") is True, "collab.propose")
    check("FORBIDDEN" in str(pr.get("proposal", {}).get("apply", "")), "collab no-apply")
    ban = cc.propose("set OCTOPUS_CB_SECRET=x")
    check(ban.get("ok") is False, "collab bans secret")

    # 4) live_commands router
    import live_commands as lc
    check(lc.handles("/live"), "lc.handles /live")
    check(lc.handles("/id"), "lc.handles /id")
    check(lc.handles("/box"), "lc.handles /box")
    check(lc.handles("/code status"), "lc.handles /code")
    out = lc.dispatch("/code status")
    check(isinstance(out, str) and len(out) > 10, "lc.dispatch code status")

    # 5) intent
    import intent as im
    check(im.classify("/live")["intent"] == "live_summary", "intent live")
    check(im.classify("/id")["intent"] == "identity", "intent id")
    check(im.classify("/box")["intent"] == "blackbox", "intent box")
    check(im.classify("/code")["intent"] == "collab_code", "intent code")

    # 6) c6 probes shape + romajan seen helpers
    import c6_probes as cp
    check(len(cp.PROBES) >= 5, "probes >=5")
    for k, spec in cp.PROBES.items():
        for f in ("measure", "floor", "subject", "question", "hypothesis", "falsification"):
            check(f in spec, f"probe {k} has {f}")
        check(callable(spec["measure"]), f"probe {k} measure callable")
    # seen set roundtrip in temp — monkeypatch STATE via opslib if needed
    # just call mark with empty = ok
    check(cp.mark_romajan_seen([])["ok"] is True, "romajan seen empty ok")
    # flag-off romajan probes return -1
    os.environ.pop("OCTOPUS_WIRE_ROMAJAN_PROBES", None)
    m = cp.PROBES["romajan_new_claims"]["measure"]()
    check(int(m.get("count", 0)) == -1, "romajan probe dark when flag off")

    # 7) lead scorer option A (flag off = skip residential cheap)
    sys.path.insert(0, str(_OPS / "legs"))
    import lead_scorer as ls
    os.environ.pop("OCTOPUS_LEAD_DIRECT_RESIDENTIAL", None)
    cheap = {
        "description": "Repaint of existing dwelling house interior.",
        "cost_of_development": 8000,
        "address": "1 Test St Sydney",
        "lat": -33.87, "lng": 151.21,
    }
    sc0 = ls.score_lead(cheap)
    check(sc0.action == "skip", "scorer flag-off skip")
    os.environ["OCTOPUS_LEAD_DIRECT_RESIDENTIAL"] = "1"
    sc1 = ls.score_lead(cheap)
    check(sc1.category == "residential_repaint_direct", "scorer flag-on category")
    check(sc1.action in ("draft", "save"), "scorer flag-on not skip")
    os.environ.pop("OCTOPUS_LEAD_DIRECT_RESIDENTIAL", None)

    # 8) c6 producer flag-off no-op
    import c6_producer as prod
    os.environ["OCTOPUS_WIRE_C6_PRODUCER"] = "0"
    q = Path(tmp) / "q.jsonl"
    res = prod.produce(q)
    check(res.get("reason") == "flag-off" or res.get("produced") in (False, 0), "producer flag-off")

    print()
    if fails:
        print("FAIL smoke_live_path")
        for f in fails:
            print("  -", f)
        return 1
    print("PASS smoke_live_path —", len(fails), "fails")
    return 0


if __name__ == "__main__":
    sys.exit(main())
