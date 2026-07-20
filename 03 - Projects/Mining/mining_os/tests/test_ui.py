"""UI تلگرام: منوی دقیقاً ۶-گزینه، namespaceِ mo:، بدونِ نشتِ token."""
import unittest

from mining_os.core import mining_beat
from mining_os.ui.telegram import render_topic, MENU


class TestTelegramUI(unittest.TestCase):
    def test_menu_has_six_options(self):
        self.assertEqual(len(MENU), 6)

    def test_menu_namespace_is_mo(self):
        for item in MENU:
            self.assertTrue(item["cb"].startswith("mo:"))

    def test_render_topic_shape(self):
        card = render_topic(mining_beat(None))
        self.assertIn("pinned", card)
        self.assertEqual(len(card["menu"]), 6)
        self.assertIn("halt_alert", card)

    def test_verdict_cards_from_open_ids(self):
        state = {"fleet": {"nodes": [{"id": "n1", "status": "running"}],
                           "electricity_price_kwh": 0.03},
                 "verdicts": [{"id": "MIN-V1", "status": "open"},
                              {"id": "MIN-V2", "status": "closed"}]}
        card = render_topic(mining_beat(state))
        ids = [c["id"] for c in card["verdict_cards"]]
        self.assertEqual(ids, ["MIN-V1"])
        self.assertTrue(card["verdict_cards"][0]["cb_yes"].startswith("mo:vok:"))

    def test_no_token_leak(self):
        blob = str(render_topic(mining_beat(None))).lower()
        for bad in ["token", "seed", "bot_token", "wallet:"]:
            self.assertNotIn(bad, blob)


if __name__ == "__main__":
    unittest.main()
