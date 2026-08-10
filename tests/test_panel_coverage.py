"""The owner panel must render what the node already answers.

Eleven owner read endpoints existed on this node and appeared nowhere in
`web/panel.html` — including the outbox queue, which CLAUDE.md §1.4 calls the
only way anything leaves this device, and the ledger hash-chain verification,
which is the only reading on the panel able to contradict the others. Nothing
was broken; the backend had simply moved ahead of the surface, and no test
could see the gap because each half was correct on its own.

So the gap itself is the thing asserted here. Every owner GET route is either
drawn by the panel or listed below with the reason it is not — a decision that
has to be written down rather than a silence that looks like coverage.
"""

from __future__ import annotations

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.path.join(ROOT, "ofn", "adapters", "http_api.py")
PANEL = os.path.join(ROOT, "web", "panel.html")

# Owner GET routes the panel deliberately does not call, each because the same
# data already reaches the screen by another route. A route may only be added
# here with a reason that names where the data is drawn instead.
NOT_CALLED = {
    "/api/v1/owner/businesses":
        "same per-leg figures as owner/status.legs, drawn by drawLegs",
    "/api/v1/owner/businesses/":
        "per-business detail; the panel shows all legs at once",
    "/api/v1/owner/core/snapshot":
        "boot, gates and quota already come from owner/status",
    "/api/v1/owner/painting/sources":
        "the painting dashboard payload carries sources; drawPaintSources",
    # O7 consent administration is owner API surface; the panel's consent
    # section is a planned owner-tools card, not yet drawn (partner sees
    # gaps through studio.html). Excused until the owner UI lands.
    "/api/v1/owner/consent/subjects":
        "consent admin is API-first (O7); owner UI card planned",
    "/api/v1/owner/consent/gaps":
        "consent admin is API-first (O7); owner UI card planned",
    "/api/v1/owner/consent/releases/":
        "consent admin is API-first (O7); owner UI card planned",
    "/api/v1/owner/growth-workbench":
        "manual-first growth workbench is API-first (O8); the owner card "
        "is planned next to 'امروز'",
}


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def owner_get_routes() -> set[str]:
    """Owner routes the API answers to GET, read from the dispatcher itself."""
    api = read(API)
    routes = set()
    for match in re.finditer(
            r'method == "GET" and path(?: ==| \.startswith\()\s*'
            r'"(/api/v1/owner/[a-z0-9/_-]+)"', api):
        routes.add(match.group(1))
    # `prefix = "..."` then `path.startswith(prefix)` — the businesses detail
    # route, which the regex above cannot see.
    for match in re.finditer(r'prefix = "(/api/v1/owner/[a-z0-9/_-]+)"', api):
        routes.add(match.group(1))
    # `path in {...}` — several painting reads share one handler, and a regex
    # that only understood `path ==` reported them as non-existent while they
    # were answering requests.
    for match in re.finditer(r'method == "GET" and path in \{(.*?)\}', api,
                             re.DOTALL):
        routes.update(re.findall(r'"(/api/v1/owner/[a-z0-9/_-]+)"',
                                 match.group(1)))
    return routes


class TestPanelCoverage(unittest.TestCase):
    def setUp(self):
        self.panel = read(PANEL)
        self.routes = owner_get_routes()

    def test_dispatcher_was_parsed(self):
        """A regex that silently matches nothing would make this file pass."""
        self.assertGreaterEqual(len(self.routes), 10,
                                f"only found {sorted(self.routes)}")

    def test_every_owner_read_is_drawn_or_excused(self):
        missing = sorted(r for r in self.routes
                         if r not in self.panel and r not in NOT_CALLED)
        self.assertEqual(missing, [], "owner endpoints the panel never calls "
                                      "and never explains: " + str(missing))

    def test_exclusions_are_still_real_routes(self):
        """An excuse for a route that no longer exists is stale, not safe."""
        stale = sorted(r for r in NOT_CALLED if r not in self.routes)
        self.assertEqual(stale, [], f"excused routes that are gone: {stale}")

    def test_exclusions_carry_a_reason(self):
        for route, reason in NOT_CALLED.items():
            self.assertTrue(reason and len(reason) > 20,
                            f"{route} is excused without a real reason")


class TestPanelSafety(unittest.TestCase):
    """The two rules that make node data safe to put on a screen."""

    def setUp(self):
        self.panel = read(PANEL)

    # `showDead` renders the connection-failure copy, which is a module-level
    # literal in REASONS and contains markup on purpose. Measuring "innerHTML
    # appears nowhere" would fail that safe line — the mechanism, not the
    # property (CLAUDE.md §8-a). The property is that no function which
    # receives node data ever assigns innerHTML.
    INNERHTML_ALLOWED = {"showDead"}

    def test_node_data_never_reaches_innerhtml(self):
        for match in re.finditer(r"\w+\.innerHTML\s*=", self.panel):
            before = self.panel[:match.start()]
            fn = re.findall(r"function\s+(\w+)\s*\(", before)
            owner = fn[-1] if fn else "<top level>"
            self.assertIn(owner, self.INNERHTML_ALLOWED,
                          f"{owner}() assigns innerHTML; it renders node data")

    def test_the_allowed_exception_renders_only_literals(self):
        """showDead may use innerHTML only while REASONS stays a literal."""
        block = re.search(r"const REASONS = \{(.*?)\n\};", self.panel, re.DOTALL)
        self.assertIsNotNone(block, "REASONS map not found")
        self.assertNotIn("${", block.group(1),
                         "REASONS interpolates a value; it must stay literal")

    def test_secrets_are_never_rendered(self):
        """The node omits tokens and identifiers; the panel must not ask.

        `owner/telegram` returns `tokens: "omitted"`. A panel that read
        `.tokens` would print the word "omitted" today and a real token the
        day someone made the endpoint more helpful.
        """
        # `init_data` and the Bearer header are the authentication path itself
        # and belong here; what must not appear is any read of a field the node
        # fills with a secret.
        for forbidden in (".tokens", ".identifiers", ".token", ".secret"):
            self.assertNotIn(forbidden, self.panel,
                             f"panel reads {forbidden!r} from node data")


class TestPanelParses(unittest.TestCase):
    """The panel's script must parse. This has been broken before.

    Commit 2533aa3 shipped a duplicate `const fa`, which is a syntax error, so
    every tab on the page died at once — a whole control surface taken out by
    something no Python test could see. `node --check` is the independent
    record that the file the browser gets is actually a program.
    """

    @staticmethod
    def _node() -> str | None:
        import shutil
        return shutil.which("node") or shutil.which("nodejs")

    @unittest.skipIf(_node.__func__() is None, "node not installed")
    def test_inline_script_parses(self):
        import subprocess
        import tempfile
        blocks = re.findall(r"<script>(.*?)</script>", read(PANEL), re.DOTALL)
        self.assertTrue(blocks, "panel has no inline script")
        for i, block in enumerate(blocks):
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                             encoding="utf-8") as fh:
                fh.write(block)
                path = fh.name
            try:
                proc = subprocess.run([self._node(), "--check", path],
                                      capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0,
                                 f"script block {i} does not parse:\n"
                                 f"{proc.stderr[:800]}")
            finally:
                os.unlink(path)


class TestEveryTenantIsLabelled(unittest.TestCase):
    """A leg with no label is a leg that quietly leaves the inventory (D-25)."""

    def test_all_packs_have_panel_labels(self):
        from ofn.adapters.packloader import load_dir
        panel = read(PANEL)
        for tenant in load_dir(os.path.join(ROOT, "packs")):
            for table in ("ORB", "NAME", "WHAT"):
                block = re.search(rf"const {table} = \{{(.*?)\}};",
                                  panel, re.DOTALL)
                self.assertIsNotNone(block, f"{table} map not found in panel")
                self.assertIn(f"{tenant}:", block.group(1),
                              f"tenant {tenant!r} has no entry in {table}")


if __name__ == "__main__":
    unittest.main()
