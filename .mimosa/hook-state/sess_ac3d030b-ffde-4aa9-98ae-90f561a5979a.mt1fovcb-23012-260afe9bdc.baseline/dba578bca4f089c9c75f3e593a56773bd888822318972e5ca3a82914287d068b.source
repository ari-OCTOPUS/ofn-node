"""UIِ تلگرامِ Mining: منو/paneها/verdict، و نامتغیرِ callback_data (ASCII ≤64B)."""
import unittest

from mining_os.ui import tg_mining


class TestTgMining(unittest.TestCase):
    def test_menu_text_and_kb(self):
        txt, kb = tg_mining.render_menu()
        self.assertIn("Mining", txt)
        flat = [b for row in kb for b in row]
        self.assertTrue(any(b["callback_data"] == "mo:fleet" for b in flat))
        self.assertEqual(sum(1 for b in flat if b["callback_data"].startswith("mo:")
                             and b["callback_data"] in
                             {"mo:fleet", "mo:coins", "mo:power", "mo:dec", "mo:risk", "mo:report"}), 6)

    def test_all_panes_render_with_back(self):
        for p in ["fleet", "coins", "power", "dec", "risk", "report"]:
            txt, kb = tg_mining.render_pane(p)
            self.assertTrue(txt)
            self.assertEqual(kb, [[{"text": "🔙 منو", "callback_data": "mo:menu"}]])

    def test_callback_routes_pane(self):
        txt, kb, toast = tg_mining.handle_callback("mo:fleet")
        self.assertIn("ناوگان", txt)

    def test_callback_menu(self):
        txt, kb, toast = tg_mining.handle_callback("mo:menu")
        self.assertIn("Mining", txt)

    def test_verdict_records_and_toasts(self):
        txt, kb, toast = tg_mining.handle_callback("mo:vok:MIN-V1")
        self.assertIn("MIN-V1", toast)

    def test_callback_data_ascii_and_bounded(self):
        _, kb = tg_mining.render_menu()
        for row in kb:
            for b in row:
                cd = b["callback_data"]
                self.assertTrue(cd.isascii(), cd)
                self.assertLessEqual(len(cd.encode()), 64)


if __name__ == "__main__":
    unittest.main()
