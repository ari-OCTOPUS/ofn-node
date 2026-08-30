#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""identity_equations — pure/offline tests ($0, no network)."""
import os
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))

import identity_equations as ie  # noqa: E402

fails = []


def check(cond, label):
    if not cond:
        fails.append(label)


# synthetic signals: strong learner/guardian, weak earner
sig = {
    "delta": 0.05,
    "n_delta": 50,
    "phi_max": 10.0,
    "phi_saturated": 0,
    "sigma": 0.3,
    "money_confirmed": 0,
    "c6_done": 3,
    "c6_pending": 1,
    "c6_seed_ratio": 0.0,
    "probe_count": 6,
    "romajan_verified": 10,
    "budget_frac": 0.8,
    "approvals_pending": 0,
    "honest_flags": 5,
    "alive": 1.0,
    "coherence_ok": 0.9,
    "lead_drafts": 0,
    "lead_total": 0,
    "missing": [],
}
r = ie.evaluate(sig)
ids = r["identities"]
check(0.0 <= ids["learner"]["value"] <= 1.0, "learner in [0,1]")
check(0.0 <= ids["earner"]["value"] <= 1.0, "earner in [0,1]")
check(0.0 <= ids["organism"]["value"] <= 1.0, "organism in [0,1]")
check(ids["learner"]["value"] > ids["earner"]["value"], "learner > earner on this fixture")
check("kill" in ids["organism"] and len(ids["organism"]["kill"]) > 20, "organism has kill")
check(all("equation" in ids[k] for k in ids), "every identity has equation")

card = ie.card(r)
check("مگا-معادلات" in card or "organism" in card.lower() or "ارگانیسم" in card, "card renders")
d = ie.detail_card("learner")
check("یادگیرنده" in d or "learner" in d.lower(), "detail learner")
check("آگاهی" not in d, "no phenomenal claim in detail")

# clamp / nan safety
bad = dict(sig, delta=float("nan"), budget_frac=2.5)
r2 = ie.evaluate(bad)
check(0.0 <= r2["identities"]["organism"]["value"] <= 1.0, "nan-safe organism")

print("FAIL" if fails else "PASS", "— test_identity_equations")
for f in fails:
    print("  -", f)
sys.exit(1 if fails else 0)
