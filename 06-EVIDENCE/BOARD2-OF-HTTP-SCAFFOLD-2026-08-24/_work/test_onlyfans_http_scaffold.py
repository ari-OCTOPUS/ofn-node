import os
import unittest
import urllib.error
from unittest import mock

from ofn.adapters.platforms.base import PublishRequest, RULE_DRY_RUN, RULE_WIRE_CLOSED
from ofn.adapters.platforms.onlyfans import OnlyFansAdapter


def _req(**kw):
    base = dict(platform="onlyfans", idempotency_key="k", caption="hi")
    base.update(kw)
    return PublishRequest(**base)


class TestOnlyFansHttpScaffold(unittest.TestCase):
    """G1 (2026-08-24): HTTP client exists, is double-locked, and opens no
    socket unless every dry/held gate is explicitly armed by the owner."""

    OF_KEYS = (
        "OFN_ONLYFANS_LIVE",
        "OFN_ONLYFANS_HTTP_ARM",
        "OFN_ONLYFANS_SESSION_COOKIE",
        "OFN_ONLYFANS_USER_AGENT",
        "OFN_ONLYFANS_ACCOUNT_ID",
        "OFN_ONLYFANS_POST_URL",
    )

    def setUp(self):
        self._saved = {k: os.environ.pop(k, None) for k in self.OF_KEYS}

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_available_platforms_lists_onlyfans(self):
        from ofn.adapters.platforms import available_platforms
        self.assertIn("onlyfans", available_platforms())

    def test_no_network_when_dry_or_live_unset(self):
        a = OnlyFansAdapter(account_id="scaffold")
        with mock.patch("urllib.request.urlopen") as uo:
            uo.side_effect = AssertionError("no socket allowed in dry / live-unset")
            r1 = a.publish(_req())
            self.assertTrue(r1.ok)
            self.assertEqual(r1.rule, RULE_DRY_RUN)
            r2 = a.publish(_req(dry_run=False))
            self.assertFalse(r2.ok)
            self.assertEqual(r2.rule, RULE_WIRE_CLOSED)
            self.assertFalse(uo.called)

    def test_live_without_cookie_is_no_credentials(self):
        os.environ["OFN_ONLYFANS_LIVE"] = "1"
        r = OnlyFansAdapter().publish(_req(dry_run=False))
        self.assertFalse(r.ok)
        self.assertEqual(r.rule, "onlyfans:no-credentials")

    def test_live_with_cookie_holds_without_second_lock(self):
        os.environ["OFN_ONLYFANS_LIVE"] = "1"
        os.environ["OFN_ONLYFANS_SESSION_COOKIE"] = "sess=dry-hold-test"
        with mock.patch("urllib.request.urlopen") as uo:
            uo.side_effect = AssertionError("dry-hold must not touch network")
            r = OnlyFansAdapter().publish(_req(dry_run=False))
        self.assertFalse(r.ok)
        self.assertEqual(r.rule, "onlyfans:http-scaffold-dry-hold")
        self.assertFalse(uo.called)

    def test_post_create_needs_endpoint(self):
        os.environ["OFN_ONLYFANS_SESSION_COOKIE"] = "sess=ep-test"
        with mock.patch("urllib.request.urlopen") as uo:
            r = OnlyFansAdapter()._post_create(_req(dry_run=False), "sess=ep-test")
        self.assertFalse(r.ok)
        self.assertEqual(r.rule, "onlyfans:endpoint-unconfigured")
        self.assertFalse(uo.called)

    def test_post_create_mock_success(self):
        os.environ["OFN_ONLYFANS_POST_URL"] = "https://example.test/post"
        with mock.patch("urllib.request.urlopen") as uo:
            uo.return_value.__enter__.return_value.read.return_value = b'{"id": 4242}'
            r = OnlyFansAdapter()._post_create(_req(dry_run=False), "sess=ok-test")
        self.assertTrue(r.ok)
        self.assertEqual(r.rule, "adapter:ok")
        self.assertEqual(r.external_id, "4242")
        args, kwargs = uo.call_args
        self.assertEqual(kwargs.get("timeout"), 15)
        self.assertEqual(args[0].get_method(), "POST")
        self.assertEqual(args[0].get_header("Content-type"), "application/json")

    def test_post_create_mock_http_error(self):
        os.environ["OFN_ONLYFANS_POST_URL"] = "https://example.test/post"
        with mock.patch("urllib.request.urlopen") as uo:
            uo.side_effect = urllib.error.HTTPError(
                "https://example.test/post", 403, "Forbidden", None, None
            )
            r = OnlyFansAdapter()._post_create(_req(dry_run=False), "sess=forbid-test")
        self.assertFalse(r.ok)
        self.assertEqual(r.rule, "onlyfans:http-403")

    def test_post_create_mock_network_error(self):
        os.environ["OFN_ONLYFANS_POST_URL"] = "https://example.test/post"
        with mock.patch("urllib.request.urlopen") as uo:
            uo.side_effect = urllib.error.URLError("conn refused")
            r = OnlyFansAdapter()._post_create(_req(dry_run=False), "sess=net-test")
        self.assertFalse(r.ok)
        self.assertEqual(r.rule, "onlyfans:network-error")

    def test_cookie_never_leaks_into_result(self):
        os.environ["OFN_ONLYFANS_POST_URL"] = "https://example.test/post"
        secret = "sess=leak-canary-DO-NOT-ECHO"
        with mock.patch("urllib.request.urlopen") as uo:
            uo.return_value.__enter__.return_value.read.return_value = b"not json"
            r = OnlyFansAdapter()._post_create(_req(dry_run=False), secret)
        blob = " ".join(
            x for x in (r.rule, r.external_id or "", r.platform, r.idempotency_key) if x
        )
        self.assertNotIn("leak-canary", blob)
        # sanity: it did run the mocked path (bad-response, not crash)
        self.assertEqual(r.rule, "onlyfans:bad-response")


if __name__ == "__main__":
    unittest.main()
