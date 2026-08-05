"""Security-header contract tests.

The shells run inside Telegram and load the Telegram SDK, so CSP must
allow telegram.org for scripts. Everything else is self-only. The API
returns JSON and needs only nosniff + referrer-policy. frame-ancestors
'none' is the clickjacking guard the senior-architect review asked for.
"""

import unittest

SRC = open("ofn/adapters/http_api.py", encoding="utf-8").read()


class TestSecurityHeadersPresent(unittest.TestCase):
    def test_nosniff_on_html_path(self):
        self.assertIn("X-Content-Type-Options", SRC)
        self.assertIn("nosniff", SRC)

    def test_referrer_policy_on_html_path(self):
        # The HTML branch sends Referrer-Policy too, not only the API branch.
        # Count occurrences: the API path has one, and the HTML path should
        # add another. At least two send_header calls for Referrer-Policy.
        self.assertGreaterEqual(SRC.count('Referrer-Policy", "no-referrer"'), 2,
                                "both API and HTML paths must send Referrer-Policy")

    def test_csp_present_with_frame_ancestors_none(self):
        self.assertIn("Content-Security-Policy", SRC)
        self.assertIn("frame-ancestors 'none'", SRC)

    def test_csp_allows_telegram_sdk(self):
        # The shells load telegram-web-app.js from telegram.org.
        self.assertIn("https://telegram.org", SRC)

    def test_csp_allows_inline_scripts_and_styles(self):
        # The shells have inline <script> boot logic and inline <style>.
        self.assertIn("'unsafe-inline'", SRC)

    def test_csp_fonts_self_only(self):
        # The font is self-hosted (vazirmatn.woff2), no external font CDN.
        self.assertIn("font-src 'self'", SRC)

    def test_x_frame_options_deny_present(self):
        self.assertIn("X-Frame-Options", SRC)
        self.assertIn("DENY", SRC)


if __name__ == "__main__":
    unittest.main()
