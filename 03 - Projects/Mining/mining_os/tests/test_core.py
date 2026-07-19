"""نامتغیرِ صداقتِ mining_beat: تا دادهٔ واقعی نیست، live=False و هرگز crash."""
import unittest

from mining_os.core import mining_beat


class TestCoreHonesty(unittest.TestCase):
    def test_no_state_is_skeleton(self):
        b = mining_beat(None)
        self.assertFalse(b["live"])
        self.assertEqual(b["signal"], "skeleton")

    def test_empty_fleet_is_skeleton(self):
        b = mining_beat({"fleet": {"nodes": [], "electricity_price_kwh": None}})
        self.assertFalse(b["live"])

    def test_never_raises_on_garbage(self):
        for bad in [123, "x", [], {"fleet": "notadict"}, {"no": "fleet"}]:
            b = mining_beat(bad)  # type: ignore[arg-type]
            self.assertIn("live", b)
            self.assertFalse(b["live"])

    def test_live_requires_real_data(self):
        state = {
            "phase": "P3",
            "fleet": {
                "nodes": [{"id": "n1", "status": "running", "temp_c": 60}],
                "electricity_price_kwh": 0.03, "solar": False,
            },
            "coins": {"candidates": [{"symbol": "VRSC", "survival_score": 70}]},
        }
        b = mining_beat(state)
        self.assertTrue(b["live"])
        self.assertEqual(b["electricity"]["gate"], "OK")
        self.assertFalse(b["halt_proposal"])
        self.assertEqual(b["coins"]["count"], 1)

    def test_expensive_power_forces_halt_proposal(self):
        state = {"fleet": {"nodes": [{"id": "n1", "status": "running"}],
                           "electricity_price_kwh": 0.09, "solar": False}}
        b = mining_beat(state)
        self.assertTrue(b["halt_proposal"])
        self.assertEqual(b["electricity"]["gate"], "HALT")

    def test_wallet_access_always_false(self):
        self.assertFalse(mining_beat(None)["wallet_access"])
        self.assertFalse(mining_beat({"fleet": {"nodes": []}})["wallet_access"])


if __name__ == "__main__":
    unittest.main()
