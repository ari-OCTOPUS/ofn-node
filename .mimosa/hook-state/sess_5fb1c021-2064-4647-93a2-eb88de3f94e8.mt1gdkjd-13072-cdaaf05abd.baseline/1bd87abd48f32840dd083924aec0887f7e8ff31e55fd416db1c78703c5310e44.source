"""test_world_discovery_action_boundary.py — مرز عمل، owner gate، telegram draft."""
import sys
from pathlib import Path

import pytest

_OPS = Path(__file__).resolve().parent.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from world_discovery import action_boundary as AB
from world_discovery.contracts import OwnerActionCard


def test_all_levels_defined():
    assert AB.ALL_LEVELS == {"L0", "L1", "L2", "L3", "L4"}


def test_always_forbidden_set():
    assert "spend" in AB.ALWAYS_FORBIDDEN
    assert "deploy" in AB.ALWAYS_FORBIDDEN
    assert "fake-revenue" in AB.ALWAYS_FORBIDDEN
    assert "edit-runtime-state" in AB.ALWAYS_FORBIDDEN


def test_level_matrix():
    # L0: no sends, no artifacts
    assert AB.action_allowed("read-public-data", "L0") is True
    assert AB.action_allowed("build-artifact", "L0") is False
    assert AB.action_allowed("send-telegram", "L0", owner_voted=True) is False
    # L1: artifacts ok, no send
    assert AB.action_allowed("build-artifact", "L1") is True
    assert AB.action_allowed("send-telegram", "L1", owner_voted=True) is False
    # L3: send with vote
    assert AB.action_allowed("send-telegram", "L3", owner_voted=True) is True
    assert AB.action_allowed("send-telegram", "L3", owner_voted=False) is False


def test_assert_action_raises():
    with pytest.raises(AB.PermissionDenied):
        AB.assert_action("send-telegram", "L3", owner_voted=False)
    with pytest.raises(AB.PermissionDenied):
        AB.assert_action("spend", "L4", owner_voted=True)


def test_make_card_defaults():
    card = AB.make_owner_action_card(
        discovery_id="d1", exact_action="send-telegram: brief",
        why_needed="owner needs to decide",
        draft_message="hello owner",
    )
    assert card.status == "BLOCKED_BY_OWNER"
    assert card.default_without_approval == "do-not-execute"
    assert card.external_effect is True
    assert card.channel == "telegram"
    assert card.draft_message == "hello owner"
    assert card.expires_at  # has TTL


def test_compose_telegram_brief_structure():
    brief = AB.compose_telegram_brief(
        discovery={"claim": "test claim about agents", "why_it_matters": "matters"},
        opportunity={"type": "competitor-weakness", "claim": "opp", "confidence": 0.6},
        experiment={"level": "E0", "observable_metric": "metric X"},
        metrics={"external_effect_count": 0, "spend_amount": 0.0, "privacy_violation_count": 0},
    )
    assert "WORLD-DISCOVERY" in brief
    assert "BLOCKED_BY_OWNER" in brief
    assert "test claim" in brief
    assert len(brief) <= 3500


def test_card_expired_logic():
    from datetime import datetime, timedelta, timezone
    card = AB.make_owner_action_card(
        discovery_id="d", exact_action="x", why_needed="y", ttl_hours=1,
    )
    assert AB.card_expired(card) is False
    assert AB.card_expired(card, now=datetime.now(timezone.utc) + timedelta(hours=5)) is True


def test_noop_gate_safe_default():
    gate = AB.NoOpOwnerGate()
    card = AB.make_owner_action_card(
        discovery_id="d", exact_action="send-telegram", why_needed="y"
    )
    res = gate.request(card)
    assert res["approved"] is False
    # critical: nothing was actually sent; only a BLOCKED status returned
    assert res["status"] == "BLOCKED_BY_OWNER"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
