"""GOV-V6 retain-condition debt — the three unresolved Bugbot findings on PR #66.

Each test pins one finding on octopus_survival/economy.py:
  1. HIGH  promotion streak must be consumed by the grant that used it
  2. MED   an approval stored on the episode satisfies a later execution apply
  3. MED   repeated applies of the same episode burn the daily caps once
"""

from __future__ import annotations

import pytest

from octopus_survival.economy import Economy, EconomyError
from tests.tmpdir import temp_dir  # noqa: F401  (same tmp convention as other suites)


def _decide_clean(school: Economy, name: str) -> None:
    school.open(name)
    school.apply(name, "selling", {"decision": "quote"})


def test_grant_consumes_promotion_streak(tmp_path):
    school = Economy(tmp_path, clock=lambda: 1, granted_level="A1", wire_open=True)
    for n in ("e1", "e2", "e3"):
        _decide_clean(school, n)
    assert school.grant("A2") == "A2"
    # same three episodes must NOT re-propose the next rung immediately
    assert school.propose_promotion() is None
    with pytest.raises(EconomyError, match="not proposed"):
        school.grant("A3")
    # three NEW decided episodes unlock the next proposal again
    for n in ("e4", "e5", "e6"):
        _decide_clean(school, n)
    assert school.propose_promotion() == "A3"
    assert school.grant("A3") == "A3"


def test_stored_episode_approval_counts_for_later_execution(tmp_path):
    school = Economy(tmp_path, clock=lambda: 1, granted_level="A2", wire_open=False)
    school.open("e1")
    school.apply("e1", "execution", {"approval": {"by": "owner"}})
    # receipt arrives in a LATER apply without repeating the approval field;
    # non-send receipt so the closed WIRE is not the thing under test
    school.apply("e1", "execution", {"execution_receipt": {"kind": "quote_card"}})
    assert school.get("e1").execution_receipt == {"kind": "quote_card"}


def test_caps_burn_once_per_episode_per_day(tmp_path):
    school = Economy(tmp_path, clock=lambda: 1, granted_level="A3", wire_open=True)
    school.open("e1")
    send = {"kind": "send", "to": "x"}
    school.apply("e1", "execution", {"execution_receipt": send})
    assert school.metrics()["sends_today"] == 1
    # re-applying / correcting the same slot must not burn another unit
    school.apply("e1", "execution", {"execution_receipt": dict(send, ref="v2")})
    assert school.metrics()["sends_today"] == 1

    school.apply("e1", "finance", {"cost": {"amount_cents": 1000}})
    school.apply("e1", "finance", {"cost": {"amount_cents": 1000}})
    assert school.metrics()["spend_today_cents"] == 1000

    # a different episode still counts separately
    school.open("e2")
    school.apply("e2", "execution", {"execution_receipt": {"kind": "send"}})
    assert school.metrics()["sends_today"] == 2
