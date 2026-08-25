import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys

sys.path.insert(0, "/opt/octopus/lab")
from ofn.organism.runtime.lan_watch import (
    next_status,
    validate_ip,
)
from ofn.organism.runtime.telegram_letter import telegram_ready


class AfferentTests(unittest.TestCase):
    def test_rejects_public_ip(self):
        with self.assertRaises(ValueError):
            validate_ip("1.1.1.1")

    def test_accepts_gateway(self):
        self.assertEqual(validate_ip("192.168.0.1"), "192.168.0.1")

    def test_fail_threshold_to_down(self):
        status, fails, recover = next_status("up", False, 2, 0, 3, 2)
        self.assertEqual(status, "down")
        self.assertEqual(fails, 3)
        self.assertEqual(recover, 0)

    def test_recover_threshold_to_up(self):
        status, fails, recover = next_status("down", True, 0, 1, 3, 2)
        self.assertEqual(status, "up")
        self.assertEqual(fails, 0)
        self.assertEqual(recover, 2)

    def test_single_fail_is_candidate_not_letter(self):
        status, fails, _recover = next_status("up", False, 0, 4, 3, 2)
        self.assertEqual(status, "down_candidate")
        self.assertEqual(fails, 1)

    def test_telegram_missing_is_not_ready(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "secrets.env"
            path.write_text("DEEPSEEK_API_KEY=not-a-telegram-key\n", encoding="utf-8")
            path.chmod(0o600)
            with patch(
                "ofn.organism.runtime.telegram_letter.SECRETS_PATH",
                path,
            ):
                self.assertEqual(telegram_ready(), "TELEGRAM_NOT_CONFIGURED")


if __name__ == "__main__":
    unittest.main()
