"""Owner-absent chaos — split-view composition (independent of #82 chaos).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These scenarios
lock the same seven rules at the contradiction layer: no store, no
run_id mint, no fabricated witness. HALT is not a mint parameter.
One arm's timeout cannot close another arm's open row. Recording a
split is still not a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.split_view import (
    grants_send,
    halt_blocks_row,
    mint_row,
    pick_a,
    ready_is_authorized,
    resolve,
    timeout_proves_concurrent_write,
    unknown_is_false,
)


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_missing_side_is_unknown_not_false(self):
        row = mint_row(
            claim="loopback_api",
            value_a=None,
            source_a="lan_ports",
            value_b="present",
            source_b="loopback_probe",
        )
        self.assertEqual(row.status, "unknown")
        self.assertFalse(unknown_is_false())
        self.assertFalse(row.grants_send)

    def test_unknown_claim_name_is_still_a_name(self):
        # An unseen claim is recordable. A sealed name is not "unknown".
        row = mint_row(
            claim="unseen_claim",
            value_a="a",
            source_a="body_a",
            value_b="b",
            source_b="body_b",
        )
        self.assertEqual(row.status, "open")
        self.assertFalse(row.grants_send)


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_close_siblings(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("arm A fetch timed out")
        sibling = mint_row(
            claim="origin_main",
            value_a="aaa",
            source_a="git_fetch",
            value_b="bbb",
            source_b="memory",
        )
        self.assertEqual(sibling.status, "open")
        self.assertFalse(sibling.grants_send)
        self.assertFalse(timeout_proves_concurrent_write())

    def test_timeout_does_not_prove_concurrent_write(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("lock wait timed out")
        row = mint_row(
            claim="worktree_writer",
            value_a="unknown",
            source_a="timeout",
            value_b="clean",
            source_b="status_after",
        )
        self.assertEqual(row.status, "open")
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertFalse(row.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_mint_independent_rows(self):
        rows = [
            mint_row(
                claim=f"arm_{arm}_head",
                value_a="local",
                source_a=f"arm_{arm}",
                value_b="origin",
                source_b=f"origin_{arm}",
            )
            for arm in ("a", "b", "c")
        ]
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row.status, "open")
            self.assertFalse(row.grants_send)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_mint_is_not_a_send(self):
        kwargs = dict(
            claim="incidents_pr",
            value_a="73",
            source_a="pull_73",
            value_b="120",
            source_b="pull_120",
        )
        first = mint_row(**kwargs)
        second = mint_row(**kwargs)
        self.assertEqual(first, second)
        self.assertEqual(first.status, "open")
        self.assertFalse(first.grants_send)
        self.assertFalse(grants_send())


class Scenario5SealedNameStopsThatRowOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_row_continues(self):
        with self.assertRaises(FailClosedError):
            mint_row(
                claim="send_authorized",
                value_a="held",
                source_a="flag",
                value_b="held",
                source_b="later_hold",
            )
        sibling = mint_row(
            claim="origin_main",
            value_a="aaa",
            source_a="git_fetch",
            value_b="bbb",
            source_b="memory",
        )
        self.assertEqual(sibling.status, "open")
        self.assertFalse(sibling.grants_send)


class Scenario6GlobalHaltIsNotAMintParameter(unittest.TestCase):
    def test_halt_does_not_block_classification(self):
        self.assertFalse(halt_blocks_row())
        for arm in ("a", "b", "c"):
            row = mint_row(
                claim=f"arm_{arm}_view",
                value_a="held",
                source_a=f"arm_{arm}",
                value_b="held",
                source_b=f"witness_{arm}",
            )
            self.assertEqual(row.status, "match")
            self.assertFalse(row.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        self.assertNotIn("halt", inspect.signature(mint_row).parameters)
        self.assertNotIn("halt_raw", inspect.signature(mint_row).parameters)
        self.assertNotIn("send_authorized", inspect.signature(mint_row).parameters)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_new_row_and_not_a_send(self):
        blocked = mint_row(
            claim="revenue_phase",
            value_a="campaign_envelope_struct",
            source_a="kernel",
            value_b="held",
            source_b="later_hold",
        )
        self.assertEqual(blocked.status, "open")
        self.assertFalse(blocked.grants_send)
        with self.assertRaises(FailClosedError):
            resolve(blocked, "send_authorized")
        with self.assertRaises(FailClosedError):
            pick_a(blocked)
        resumed = mint_row(
            claim="revenue_phase",
            value_a="campaign_envelope_struct",
            source_a="kernel",
            value_b="held",
            source_b="later_hold",
        )
        self.assertEqual(resumed, blocked)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(grants_send())
        self.assertFalse(ready_is_authorized())


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        for name in ("campaign_envelope_ready", "send_authorized", "quote_sent"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    mint_row(
                        claim=name,
                        value_a="held",
                        source_a="flag",
                        value_b="held",
                        source_b="later_hold",
                    )


if __name__ == "__main__":
    unittest.main()
