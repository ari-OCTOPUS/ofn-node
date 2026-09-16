"""تستِ عدمِ نشتِ توکنِ تلگرام به لاگ (فیکسِ notify)."""
from tests import _bootstrap  # noqa: F401

import os
import unittest
from unittest import mock

import brain.notify as notify

_FAKE_TOKEN = "123456:FAKESECRETTOKENXYZ"


class TestTelegramTokenNoLeak(unittest.TestCase):
    def setUp(self):
        self._old = {k: os.environ.get(k)
                     for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")}
        os.environ["TELEGRAM_BOT_TOKEN"] = _FAKE_TOKEN
        os.environ["TELEGRAM_CHAT_ID"] = "42"
        self._old_last_send = notify._last_send[0]
        notify._last_send[0] = 0.0  # دورزدنِ throttle

    def tearDown(self):
        for k, v in self._old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        notify._last_send[0] = self._old_last_send

    def test_transport_error_does_not_log_token(self):
        """خطای شبکه‌ای که URL کامل (با توکن) در پیامش است نباید وارد لاگ شود."""
        err = Exception(
            f"Max retries exceeded with url: /bot{_FAKE_TOKEN}/sendMessage")
        with mock.patch("requests.post", side_effect=err):
            with self.assertLogs("brain.notify", level="WARNING") as cm:
                ok, detail = notify._send_telegram("hello")
        self.assertFalse(ok)
        self.assertTrue(detail.startswith("error:"))
        logged = "\n".join(cm.output)
        self.assertNotIn(_FAKE_TOKEN, logged)      # هیچ نشتی
        self.assertIn("Exception", logged)          # ولی نوعِ خطا ثبت شده


if __name__ == "__main__":
    unittest.main()
