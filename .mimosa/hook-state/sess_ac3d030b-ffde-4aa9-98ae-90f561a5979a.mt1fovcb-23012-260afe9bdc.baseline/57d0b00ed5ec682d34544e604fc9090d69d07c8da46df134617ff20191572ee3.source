"""گیت‌های fail-closed: اقدام‌های ممنوع رد شوند؛ برق درست HALT کند؛ wallet هرگز مجاز نیست."""
import unittest

from mining_os.organs.governance import (
    assert_action_allowed, is_action_allowed, electricity_gate,
    wallet_access_allowed, ActionForbidden,
)


class TestGovernance(unittest.TestCase):
    def test_forbidden_actions_rejected(self):
        for a in ["ssh", "deploy", "wallet", "trade", "buy", "sell",
                  "withdraw", "spawn", "miner_control", "code.apply"]:
            with self.assertRaises(ActionForbidden):
                assert_action_allowed(a)
            self.assertFalse(is_action_allowed(a))

    def test_case_insensitive(self):
        with self.assertRaises(ActionForbidden):
            assert_action_allowed("  SSH ")

    def test_electricity_halt_when_expensive(self):
        self.assertEqual(electricity_gate(0.09, False)[0], "HALT")

    def test_electricity_halt_when_unknown(self):
        self.assertEqual(electricity_gate(None, False)[0], "HALT")

    def test_electricity_ok_when_cheap(self):
        self.assertEqual(electricity_gate(0.03, False)[0], "OK")

    def test_electricity_ok_when_solar(self):
        self.assertEqual(electricity_gate(None, True)[0], "OK")

    def test_wallet_never_allowed(self):
        self.assertFalse(wallet_access_allowed())


if __name__ == "__main__":
    unittest.main()
