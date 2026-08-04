"""What somebody with no credentials learns.

Every other test in this repository is an authenticated user. That is not a
gap that more tests fill — it is a missing *role*. A suite only finds bugs in
states it can imagine itself into, and "a stranger loaded the URL" was a
state nothing here had a name for.

It was found by opening the real address in an ordinary browser. This file is
that person, kept.

The tunnel is public. Every one of these four addresses answers to anyone on
the internet, before the node knows whether they are anybody at all.
"""

from __future__ import annotations

import os
import re
import threading
import time
import unittest
import urllib.error
import urllib.request

from ofn.adapters.http_api import ApiApp, HostMap, serve
from ofn.kernel.domain import TenantId
from ofn.kernel.tenancy import PackSpec, TenantRegistry

WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "web")
SHELLS = ("ziman.html", "lead.html", "studio.html", "panel.html")

# The real people this node is for. None may appear in anything served before
# somebody has proved who they are. Surnames included: a family name is the
# part that identifies a person outside their own circle.
FORBIDDEN_TERMS = ("ملیحه", "عباس", "اسدی", "سبا", "سبولی")

# Things that are not names but still say more than a stranger should learn.
FORBIDDEN_SECRETS = ("OFN_BOT_TOKEN", "OFN_SESSION_SECRET", "api.telegram.org/bot")


def static(name: str) -> bytes:
    with open(os.path.join(WEB, name), "rb") as fh:
        return fh.read()


class TestAStrangerLearnsNoOnesName(unittest.TestCase):
    """The file on disk, which is exactly what the tunnel serves."""

    def test_no_shell_names_a_person(self):
        for name in SHELLS:
            src = static(name).decode("utf-8")
            # Comments are allowed to name what they warn against; everything
            # a browser renders or runs is not.
            live = re.sub(r"<!--.*?-->|/\*.*?\*/", "", src, flags=re.S)
            with self.subTest(shell=name):
                for person in FORBIDDEN_TERMS:
                    self.assertNotIn(person, live,
                                     f"{name} serves {person} to anyone")

    def test_no_title_names_a_person(self):
        """The first thing served and the last thing anybody checks. This is
        exactly where the leak was found."""
        for name in SHELLS:
            src = static(name).decode("utf-8")
            title = re.search(r"<title>(.*?)</title>", src, re.S)
            with self.subTest(shell=name):
                self.assertIsNotNone(title)
                for person in FORBIDDEN_TERMS:
                    self.assertNotIn(person, title.group(1))

    def test_no_shell_carries_a_secret(self):
        for name in SHELLS:
            src = static(name).decode("utf-8")
            with self.subTest(shell=name):
                for secret in FORBIDDEN_SECRETS:
                    self.assertNotIn(secret, src)

    def test_no_shell_carries_a_telegram_user_id(self):
        """A numeric id is not a name, and it is still a person. Nine or ten
        digits standing alone in served markup has no innocent reason.

        `[0-9]`, not `\\d`: Python's `\\d` matches Unicode digits, so it read
        the Persian digit-translation table `۰۱۲۳۴۵۶۷۸۹` as a user id. That
        was this test being wrong, not the shell — and a test that cries wolf
        on its first run is one somebody deletes on its second.
        """
        for name in SHELLS:
            live = re.sub(r"<!--.*?-->|/\*.*?\*/", "",
                          static(name).decode("utf-8"), flags=re.S)
            with self.subTest(shell=name):
                for hit in re.findall(r"(?<![0-9])[0-9]{9,12}(?![0-9])", live):
                    self.fail(f"{name} contains a bare long number: {hit}")


class TestOverTheWire(unittest.TestCase):
    """The same question asked of a running server, because what is served
    and what is on disk are two facts, not one."""

    PORT = 8883

    @classmethod
    def setUpClass(cls):
        packs = {"ziman": PackSpec(tenant=TenantId("ziman"),
                                   capacity_units_per_week=6, quota_share=1.0)}
        app = ApiApp(TenantRegistry(packs),
                     HostMap(tenants={"z.test": "ziman"}, owner_host="p.test"),
                     bot_tokens={"ziman": "t"}, session_secret="s",
                     now=lambda: 1_785_000_000)
        cls.server = serve(app, cls.PORT, static={
            "/index.html": static("studio.html"),
            "/sabaapp": static("studio.html"),
        })
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def get(self, path, host="z.test"):
        req = urllib.request.Request(f"http://127.0.0.1:{self.PORT}{path}",
                                     headers={"Host": host})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()

    def test_the_page_is_served_to_anyone(self):
        """Stated rather than assumed: this is why the rest of the file
        matters."""
        status, _ = self.get("/")
        self.assertEqual(status, 200)

    def test_and_it_names_nobody(self):
        for path in ("/", "/sabaapp"):
            _, body = self.get(path)
            with self.subTest(path=path):
                for person in FORBIDDEN_TERMS:
                    self.assertNotIn(person.encode(), body)

    def test_every_api_route_refuses_without_a_session(self):
        for path in ("/api/v1/me", "/api/v1/status", "/api/v1/questions",
                     "/api/v1/products", "/api/v1/studio/board"):
            with self.subTest(path=path):
                status, _ = self.get(path)
                self.assertEqual(status, 401)

    def test_a_refusal_says_nothing_about_who_would_be_allowed(self):
        """Signature first, identity second — so an unsigned request never
        learns whether an id it guessed is on a list."""
        _, body = self.get("/api/v1/me")
        for word in (b"allow", b"partner", b"list", b"user_id"):
            self.assertNotIn(word, body.lower())

    def test_an_unknown_host_gets_nothing(self):
        status, _ = self.get("/api/v1/me", host="evil.test")
        self.assertIn(status, (401, 403, 404))

    def test_the_health_check_reveals_nothing(self):
        status, body = self.get("/healthz")
        self.assertEqual(status, 200)
        for person in FORBIDDEN_TERMS:
            self.assertNotIn(person.encode(), body)
        for word in (b"token", b"secret", b"user"):
            self.assertNotIn(word, body.lower())


if __name__ == "__main__":
    unittest.main()
