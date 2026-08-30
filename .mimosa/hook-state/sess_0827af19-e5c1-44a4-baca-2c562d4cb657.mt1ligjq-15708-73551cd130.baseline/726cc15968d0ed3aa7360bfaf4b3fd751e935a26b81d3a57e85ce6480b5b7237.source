"""loop.tick: بدونِ state → skeleton، هرگز crash، beat را حمل می‌کند."""
import unittest

from mining_os import loop


class TestLoop(unittest.TestCase):
    def test_tick_returns_skeleton_without_state(self):
        snap = loop.tick(42)
        self.assertEqual(snap["leg"], "mining")
        self.assertFalse(snap["live"])
        self.assertEqual(snap["beat"], 42)

    def test_tick_never_raises(self):
        for b in [0, 1, 999]:
            self.assertIn("signal", loop.tick(b))


if __name__ == "__main__":
    unittest.main()
