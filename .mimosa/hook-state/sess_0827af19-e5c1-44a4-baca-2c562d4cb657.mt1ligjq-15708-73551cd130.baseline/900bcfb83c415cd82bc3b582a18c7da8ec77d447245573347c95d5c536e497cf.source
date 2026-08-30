#!/usr/bin/env python3
"""test_mining_leg.py — پای Mining (دو مغز)، propose-only، read-only، offline.

اثبات می‌کند: دو مغز (hardware control + coin discovery) کار می‌کنند، propose-only
مطلق (هیچ send/publish/pay/trade/ssh/deploy)، secrets خالی (D-11)، گیت برق ساختاری،
death-watch فقط D2 (نه payback). هیچ اثر بیرونی، هیچ شبکه، $0.
"""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
for p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")):
    if p not in sys.path:
        sys.path.insert(0, p)

from mining_leg import (  # noqa: E402
    MiningLeg, HardwareControlBrain, CoinDiscoveryBrain, default_packet,
    HARD_GATED, ELECTRICITY_CEILING_USD_KWH,
)


# ─── TaskPacket / isolation ──────────────────────────────────────────────────
def test_default_packet_is_contained():
    pkt = default_packet()
    assert pkt.leg_id == "mining-fleet"
    assert pkt.organ == "MINING"
    assert pkt.spawn == 0                       # INV-17
    assert pkt.secrets == ()                    # D-11: هیچ دسترسی wallet
    assert pkt.budget_aud == 0.0               # $0
    assert "*" not in pkt.read_allowlist        # بدون wildcard (IsolationModel)
    assert all(n.startswith("03 - Projects/Mining") for n in pkt.read_allowlist)


def test_leg_is_incubating_without_organ():
    leg = MiningLeg(default_packet(), organ_table={})   # MINING در budgets نیست
    assert leg.money_link == "incubating"


def test_leg_has_no_outward_methods():
    leg = MiningLeg(default_packet(), organ_table={})
    for m in ("send", "publish", "pay", "trade", "ssh", "deploy", "withdraw"):
        assert not hasattr(leg, m), f"leg نباید متدِ {m} داشته باشد (propose-only)"


def test_two_brains_present():
    leg = MiningLeg(default_packet(), organ_table={})
    assert isinstance(leg.hw, HardwareControlBrain)
    assert isinstance(leg.coins, CoinDiscoveryBrain)
    st = leg.status_snapshot()
    assert st["brains"] == ["hardware_control", "coin_discovery"]


# ─── hard-gated actions (D-10/D-11/D-20) ─────────────────────────────────────
def test_hard_gated_actions_recognized():
    leg = MiningLeg(default_packet(), organ_table={})
    for action in ("ssh_to_node", "deploy", "access_wallet", "execute_trade",
                   "buy", "sell", "withdraw", "start_mining"):
        assert leg.is_hard_gated(action) is True
    assert leg.is_hard_gated("read_status") is False


# ─── 🛠 مغز ۱: hardware control / electricity gate ───────────────────────────
def test_electricity_gate_solar_is_safe():
    r = HardwareControlBrain.electricity_check(
        [{"node_id": "OPI-1", "power_source": "solar"}])
    assert r["safe"] is True and r["mood"] == "🟢"


def test_electricity_gate_expensive_grid_halts():
    r = HardwareControlBrain.electricity_check(
        [{"node_id": "OPI-1", "power_source": "grid",
          "electricity_cost_usd_kwh": 0.25}])
    assert r["safe"] is False and r["mood"] == "🔴"
    assert any("OPI-1" in u for u in r["unsafe"])


def test_electricity_gate_cheap_grid_is_safe():
    r = HardwareControlBrain.electricity_check(
        [{"node_id": "OPI-1", "power_source": "grid",
          "electricity_cost_usd_kwh": 0.04}])
    assert r["safe"] is True and r["mood"] == "🟢"


def test_electricity_gate_unknown_is_failclosed():
    r = HardwareControlBrain.electricity_check(
        [{"node_id": "OPI-1", "power_source": "unknown"}])
    assert r["safe"] is False and r["mood"] == "🟡"
    assert "OPI-1" in r["unknown"]


def test_electricity_gate_no_nodes_failclosed():
    r = HardwareControlBrain.electricity_check([])
    assert r["safe"] is False and r["mood"] == "🟡"


def test_ceiling_is_the_manifest_value():
    assert ELECTRICITY_CEILING_USD_KWH == 0.05


def test_fleet_summary_thermal_warn():
    summ = HardwareControlBrain.fleet_summary([
        {"node_id": "OPI-1", "status": "running", "temp_c": 80},
        {"node_id": "OPI-2", "status": "running", "temp_c": 55},
    ])
    assert summ["nodes_total"] == 2
    assert summ["nodes_running"] == 2
    assert "OPI-1" in summ["thermal_warn"]
    assert summ["measured"] is True


# ─── ⛏ مغز ۲: coin discovery / algo classification ──────────────────────────
def test_algo_yespower_is_arm_viable():
    a = CoinDiscoveryBrain.classify_algo("yespower")
    assert a["arm_viable"] is True and a["category"] == "cpu_arm_preferred"


def test_algo_sha256_is_rejected():
    a = CoinDiscoveryBrain.classify_algo("sha256")
    assert a["arm_viable"] is False and a["category"] == "gpu_or_asic_dominated"


def test_algo_unknown_needs_review():
    a = CoinDiscoveryBrain.classify_algo("frobnicate9000")
    assert a["arm_viable"] is False and a["category"] == "needs_manual_review"


def test_score_candidate_arm_coin():
    scored = CoinDiscoveryBrain.score_candidate({
        "symbol": "NEW", "name": "Newborn", "algorithm": "yespower",
        "launch_age_days": 30, "dev_activity_notes": "active repo",
        "community_notes": "small discord", "network_hashrate_hs": 1000.0,
        "block_reward": 50, "blocks_per_day": 720,
    })
    assert scored["arm_viable"] is True
    assert scored["score"] >= 70 and scored["mood"] == "🟢"


def test_score_candidate_gpu_coin_is_red():
    scored = CoinDiscoveryBrain.score_candidate({
        "symbol": "GPU", "name": "GpuCoin", "algorithm": "kawpow",
        "launch_age_days": 10})
    assert scored["arm_viable"] is False and scored["mood"] == "🔴"


# ─── ⛏ مغز ۲: death-watch (D2 only) ──────────────────────────────────────────
def test_death_watch_dev_dead_abandons():
    v = CoinDiscoveryBrain.death_watch({"coin": "X", "dev_dead_weeks": 10})
    assert v["abandon"] is True and v["mood"] == "🔴"


def test_death_watch_payback_never_kills():
    # payback بد نباید abandon بسازد — فقط D2. اینجا هیچ معیار D2 نیست.
    v = CoinDiscoveryBrain.death_watch({
        "coin": "X", "dev_dead_weeks": 1, "chain_stalled": False,
        "community_dead": False})
    assert v["abandon"] is False and v["mood"] == "🟢"


def test_death_watch_incomplete_is_amber():
    v = CoinDiscoveryBrain.death_watch({"coin": "X"})
    assert v["abandon"] is False and v["mood"] == "🟡"


# ─── proposals (propose-only) ────────────────────────────────────────────────
def test_fleet_health_emits_proposal():
    leg = MiningLeg(default_packet(), organ_table={})
    p = leg.fleet_health([{"node_id": "OPI-1", "power_source": "solar"}])
    assert p.kind == "fleet_health"
    assert p.payload["draft_only"] is True
    assert p.payload["external_action"] is False
    assert len(leg.proposals) == 1


def test_coin_scout_emits_sorted_proposal():
    leg = MiningLeg(default_packet(), organ_table={})
    p = leg.coin_scout([
        {"symbol": "A", "algorithm": "kawpow"},
        {"symbol": "B", "algorithm": "yespower", "launch_age_days": 20,
         "dev_activity_notes": "x", "network_hashrate_hs": 1.0},
    ])
    assert p.kind == "coin_scout"
    # مرتب‌شده نزولی: کاندید ARM باید بالاتر باشد
    assert p.payload["candidates"][0]["symbol"] == "B"


def test_death_watch_emits_proposal():
    leg = MiningLeg(default_packet(), organ_table={})
    p = leg.death_watch({"coin": "X", "chain_stalled": True})
    assert p.kind == "death_watch"
    assert p.payload["death_watch"]["abandon"] is True


# ─── tick / telegram digest ──────────────────────────────────────────────────
def test_tick_is_status_only():
    leg = MiningLeg(default_packet(), organ_table={})
    r = leg.tick()
    assert r["ok"] is True
    assert r["status"]["external_action"] is False
    assert r["status"]["read_only"] is True
    assert r["proposals_total"] == 0            # tick چیزی emit نمی‌کند


def test_telegram_digest_three_lines():
    leg = MiningLeg(default_packet(), organ_table={})
    d = leg.telegram_digest([{"node_id": "OPI-1", "power_source": "solar",
                              "status": "running"}])
    lines = d.splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("⛏ Mining")
    assert "propose-only" in d


def test_hard_gated_covers_domain_rules():
    # D-10/D-11/D-20 همه در HARD_GATED
    for a in ("ssh_to_node", "deploy", "access_wallet", "execute_trade",
              "buy", "sell", "withdraw"):
        assert a in HARD_GATED
