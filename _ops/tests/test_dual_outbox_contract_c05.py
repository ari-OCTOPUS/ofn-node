# -*- coding: utf-8 -*-
from __future__ import annotations
import sys
from pathlib import Path

TC = Path(__file__).resolve().parents[1] / "telegram_center"
if str(TC) not in sys.path:
    sys.path.insert(0, str(TC))

import dual_outbox_contract as doc


def test_sot_outbox_class():
    r = doc.classify(doc.SOT_OUTBOX)
    assert r["class"] == "SOT_DURABLE_OUTBOX"
    assert r["merge_with_canary"] is False


def test_canary_sqlite_non_sot():
    r = doc.classify(doc.CANARY_DIR / "a18-owner-canary-rate-limit.sqlite3")
    assert r["class"] == "NON_SOT_CANARY_SQLITE"
    assert r["merge_with_canary"] is False


def test_policy_assert():
    assert doc.assert_not_merged_policy()["ok"] is True

def test_event_bridge_non_sot():
    r = doc.classify_surface(doc.CANARY_DIR / "event-bridge" / "x.json")
    assert r["class"] == "NON_SOT_EVENT_BRIDGE"
    assert r.get("merge_into_durable_sot") is False


def test_urgent_non_sot():
    r = doc.classify_surface(doc.CANARY_DIR / "urgent" / "y.json")
    assert "NON_SOT" in r["class"]
