#!/usr/bin/env python3
"""Seed the scorer with REAL funnel decisions (phase 3, C-1).

9 matured (EXPLORATORY — registered post-hoc, labeled honestly per the
plan's own rule) + 10 preregistered CONFIRMATORY (today's sends, outcomes
unknown, horizon 24h). One warm reply exists: QP-3991 followup (Absolute
Strata, 2026-09-16T00:22:06Z).
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tools import decision_scorer as ds  # noqa: E402

STORE = REPO / "rca" / "scorer" / "decisions.jsonl"

# --- matured, EXPLORATORY (post-hoc registration, outcomes already known) ---
matured = [
    # 2026-09-13 batch: 3 original quotes (no direct replies from these sends)
    ("QP-20260913-3991-original", 0.12, 0), ("QP-5195-original", 0.12, 0),
    ("QP-951-original", 0.12, 0),
    # 2026-09-15 11:32-11:40Z: 3 warm followups (24h horizon matured)
    ("QP-3991-followup1", 0.25, 1),   # Absolute Strata replied 00:22:06Z
    ("QP-5195-followup1", 0.25, 0), ("QP-951-followup1", 0.25, 0),
    # 2026-09-15 12:02Z: 3 fresh quotes (24h horizon matured)
    ("QP-1049-quote", 0.12, 0), ("QP-1225-quote", 0.12, 0),
    ("QP-1279-quote", 0.12, 0),
]
for action, p, y in matured:
    rec = ds.preregister(action, p, 0.10, 24, domain="painting-quote-email",
                         expected_cash_delta_cents=150000,
                         runway_impact_days=0.5, exploratory=True,
                         store=STORE)
    ds.resolve(rec["decision_id"], y, store=STORE)

# --- CONFIRMATORY: today's 10 sends (2026-09-16T00:01:22Z), outcomes unknown ---
todays = ["QP-128", "QP-1391", "QP-2042", "QP-3420", "QP-3661",
          "QP-4121", "QP-4129", "QP-4421", "QP-4737", "QP-4982"]
for qp in todays:
    ds.preregister(f"{qp}-quote-20260916", 0.12, 0.10, 24,
                   domain="painting-quote-email",
                   expected_cash_delta_cents=150000,
                   runway_impact_days=0.5, store=STORE)

print(json.dumps({"registered": 9 + 10,
                  "matured_scored": 9,
                  "confirmatory_pending": 10,
                  "dashboard": ds.dashboard(STORE)}, indent=1))
