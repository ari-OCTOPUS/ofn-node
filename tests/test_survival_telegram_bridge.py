"""survival→telegram bridge: cockpit routing, rate cap, idempotency."""
from __future__ import annotations

import os, tempfile
from ofn.adapters.outbox import Outbox
from ofn.kernel.domain import RiskTier, TenantId
from ofn.kernel.tenancy import TenantScope
from octopus_survival.telegram_bridge import SurvivalTelegramBridge

NOW_S = 1_800_100_000
SCOPE = TenantScope(TenantId("lead"))


def bridge(tmp, max_per_day=20):
    ob = Outbox(os.path.join(tmp, "o.sqlite"))
    b = SurvivalTelegramBridge(ob, SCOPE, now_epoch_s=lambda: NOW_S,
                               now_iso=lambda: "2026-09-01T00:00:00Z",
                               max_per_day=max_per_day)
    return ob, b


def test_event_lands_in_owner_queue_as_green_manual(tmp_path):
    ob, b = bridge(str(tmp_path))
    assert b.notify("R1", "RUN_REGISTERED",
                    {"exp_id": "EXP-1", "authority": 2}) is True
    item = ob.pending(SCOPE)[0]
    assert item.kind == "survival_loop_event"
    assert item.tier == RiskTier.GREEN
    assert "EXP-1" in item.payload["message"]


def test_rate_cap_blocks_flood(tmp_path):
    ob, b = bridge(str(tmp_path), max_per_day=2)
    assert b.notify("R1", "RUN_REGISTERED", {}) is True
    assert b.notify("R1", "PAYMENT_RECEIVED", {"amount_aud": 5}) is True
    assert b.notify("R1", "RUN_HALTED", {}) is False      # capped
    assert ob.counts(SCOPE)["pending"] == 2


def test_cap_resets_next_day(tmp_path):
    ob, b = bridge(str(tmp_path), max_per_day=1)
    assert b.notify("R1", "RUN_REGISTERED", {}) is True
    assert b.notify("R1", "RUN_HALTED", {}) is False
    b._now_s = lambda: NOW_S + 86_400                      # next day
    assert b.notify("R1", "RUN_HALTED", {}) is True


def test_duplicate_tick_is_idempotent(tmp_path):
    ob, b = bridge(str(tmp_path))
    assert b.notify("R1", "RUN_REGISTERED", {}) is True
    assert b.notify("R1", "RUN_REGISTERED", {}) is False   # same tick+key
    assert ob.counts(SCOPE)["pending"] == 1
