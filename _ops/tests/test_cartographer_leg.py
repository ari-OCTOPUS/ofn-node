#!/usr/bin/env python3
"""test_cartographer_leg.py — تست‌های pure/offline پای نقشه‌بردار (صفر شبکه، صفر ledgerِ واقعی)."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_LEGS = _OPS / "legs"
for p in (str(_OPS), str(_LEGS), str(_OPS / "budget")):
    if p not in sys.path:
        sys.path.insert(0, p)

from cartographer_leg import (  # noqa: E402
    CARTO_ANCHORS, CartographerLeg, default_packet)

_NOW = datetime(2026, 7, 12, 12, 0, tzinfo=timezone.utc)


def _capturing_leg():
    """leg با emitterِ ضبط‌کننده — هرگز در state/events.jsonl واقعی نمی‌نویسد."""
    captured = []

    def fake_emit(event_name, agent_id, **kw):
        captured.append({"event": event_name, "agent": agent_id, **kw})
        return {"ok": True}

    leg = CartographerLeg(organ_table={}, emitter=fake_emit)
    return leg, captured


def test_default_packet_isolation():
    pkt = default_packet()
    assert pkt.leg_id == "vault-cartographer"
    assert pkt.organ == "CARTOGRAPHER"
    assert pkt.spawn == 0
    assert pkt.secrets == ()
    assert pkt.budget_aud == 0.0
    assert "*" not in pkt.read_allowlist and all(pkt.read_allowlist)


def test_no_outward_methods():
    leg = CartographerLeg(organ_table={})
    for m in ("send", "publish", "pay", "trade", "dm", "spend"):
        assert not hasattr(leg, m), f"propose-only violated: {m}"


def test_money_link_incubating_without_organ():
    # CARTOGRAPHER در budgets نیست → incubating (هرگز بودجه رزرو نمی‌کند)
    leg = CartographerLeg(organ_table={})
    assert leg.money_link == "incubating"


def test_status_is_read_only_contained():
    leg = CartographerLeg(organ_table={})
    s = leg.status_snapshot()
    assert s["autonomy_floor"] == "read-only"
    assert s["autonomy_ceiling"] == "propose-only"
    assert s["read_only"] is True
    assert s["mutates"] is False
    assert s["external_action"] is False
    assert s["spend_aud"] == 0


def test_staleness_fresh_vs_stale():
    leg = CartographerLeg(organ_table={})
    assert leg.map_staleness_check("2026-07-10", _now=_NOW)["stale"] is False   # 2 روز
    assert leg.map_staleness_check("2026-05-01", _now=_NOW)["stale"] is True    # >14 روز
    # تاریخِ نامعلوم/غیرقابل‌parse → fail-closed (stale=True)
    assert leg.map_staleness_check(None, _now=_NOW)["stale"] is True
    assert leg.map_staleness_check("banana", _now=_NOW)["stale"] is True
    # آینده → نادیده (تازه فرض)
    assert leg.map_staleness_check("2099-01-01", _now=_NOW)["stale"] is False


def test_propose_refresh_is_proposal_only():
    leg, captured = _capturing_leg()
    p = leg.propose_refresh("map looks stale", map_updated_iso="2026-05-01")
    assert p.kind == "cartography_refresh"
    assert p.payload["publish"] is False
    assert p.payload["draft_only"] is True
    assert p.payload["no_mutation"] is True
    assert p.payload["external_action"] is False
    assert len(leg.proposals) == 1


def test_propose_refresh_logs_content_free_ledger():
    leg, captured = _capturing_leg()
    leg.propose_refresh("refresh", map_updated_iso="2026-05-01", trace_id="t-1")
    assert len(captured) == 1
    ev = captured[0]
    assert ev["event"] == "task.completed"
    assert ev["agent"] == "vault-cartographer"
    assert ev["approval_state"] == "none"          # پیشنهاد، نه اکشنِ گیت‌دار
    assert ev.get("enrich") is True
    # content-free: هیچ رشتهٔ ممنوع در summary/next_action
    blob = (ev.get("summary", "") + " " + ev.get("next_action", "")).lower()
    for banned in ("اونلی", "onlyfans", "صبا", "sk-", "api_key", "token"):
        assert banned not in blob


def test_emit_is_fail_soft_without_emitter():
    # بدونِ emitterِ تزریقی و بدونِ ledgerِ واقعیِ در دسترس، نباید crash کند
    leg = CartographerLeg(organ_table={}, emitter=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    # نباید استثنا بیرون بدهد (fail-soft)
    p = leg.propose_refresh("x", map_updated_iso="2026-05-01")
    assert p.kind == "cartography_refresh"


def test_read_allowlist_enforced():
    leg = CartographerLeg(organ_table={})
    assert leg.read_brief("secret/other.md") is None       # خارجِ allowlist
    assert leg.packet.can_read(CARTO_ANCHORS[0]) is True    # anchorِ مجاز


def test_tick_ok_no_side_effect():
    leg, captured = _capturing_leg()
    r = leg.tick()
    assert r["ok"] is True
    assert r["read_only"] is True
    assert captured == []          # tick هیچ چیز emit نمی‌کند
