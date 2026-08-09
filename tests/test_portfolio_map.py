"""The portfolio/tenant vocabulary, checked against the repository.

D-25 records that GiftMesh Sydney is a brand of the `ziman` tenant, not a
tenant of its own, and fixes a set of names that arrived from an outside plan
document and did not exist here. A decision like that decays the moment
someone writes the old name again, so it is asserted rather than described.

Two things are checked, and they are different:

  * the map names only tenants that packs/ actually declares, and every
    tenant packs/ declares appears on the map (an omission is how `hypno`
    disappeared from a portfolio plan while remaining a real tenant);
  * every repository path the map cites exists, and the invented names it
    replaces have not crept into the code.

The map states no countable figure. `tools/repo_baseline.py` derives those,
and this file checks that the tool agrees with the files it reads — per
CLAUDE.md §8-a, a number in prose is a number that is already stale.
"""

from __future__ import annotations

import json
import os
import re
import unittest

from ofn.adapters.packloader import load_dir

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, "docs", "architecture", "PORTFOLIO-TENANT-MAP.md")
PACKS_DIR = os.path.join(ROOT, "packs")

# Names that arrived with the plan draft and describe nothing in this tree.
# They may appear in the map (its left-hand column is exactly the list of
# terms being translated); they may not appear anywhere else.
IMPORTED_NAMES = ("MycoLedger", "EffectorGate")


def map_text() -> str:
    with open(MAP, encoding="utf-8") as fh:
        return fh.read()


# Where shipped behaviour lives. Backups and `.bak-` files are excluded because
# they are frozen history: a name retired today was legitimately there
# yesterday, and failing on that would make the test a nuisance rather than a
# guard. This file excludes itself for the obvious reason.
CODE_DIRS = ("ofn", "packs", "tools", "data", "migrations", "web")
CODE_SUFFIXES = (".py", ".yaml", ".json", ".html", ".js")
SELF = os.path.abspath(__file__)


def code_files():
    """Every shipped source file, minus caches, backups and this test."""
    for top in CODE_DIRS:
        base = os.path.join(ROOT, top)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames
                           if d not in {"__pycache__", "node_modules"}]
            for name in filenames:
                path = os.path.join(dirpath, name)
                if (name.endswith(CODE_SUFFIXES)
                        and ".bak-" not in name
                        and os.path.abspath(path) != SELF):
                    yield path


class TestTenantInventory(unittest.TestCase):
    """The map's tenant table and packs/ are the same set, both directions."""

    def setUp(self):
        self.packs = load_dir(PACKS_DIR)
        self.text = map_text()

    def test_map_names_every_real_tenant(self):
        for tenant in self.packs:
            self.assertIn(f"`{tenant}`", self.text,
                          f"tenant {tenant!r} exists in packs/ but is absent "
                          f"from the portfolio map")

    def test_map_invents_no_tenant(self):
        # Backticked lowercase identifiers in the tenant table's first column.
        table = self.text.split("## ۳)")[0]
        claimed = set(re.findall(r"^\| `([a-z_]+)` \|", table, re.MULTILINE))
        self.assertTrue(claimed, "tenant table parsed as empty — did it move?")
        self.assertEqual(claimed - set(self.packs), set(),
                         "map claims tenants that packs/ does not declare")

    def test_giftmesh_is_not_a_tenant(self):
        """D-25: the brand must not appear as a tenant id anywhere in code."""
        for path in code_files():
            with open(path, encoding="utf-8", errors="replace") as fh:
                body = fh.read()
            self.assertNotIn("giftmesh", body.lower(),
                             f"{os.path.relpath(path, ROOT)} mentions giftmesh; "
                             f"D-25 keeps it a documentation-level brand only")

    def test_brand_is_recorded_against_ziman(self):
        self.assertIn("giftmesh-sydney", self.text)
        self.assertIn("GiftMesh Sydney", self.text)
        # The brand line and the tenant it belongs to must be in the same table.
        row = [ln for ln in self.text.splitlines()
               if "GiftMesh Sydney" in ln and "`ziman`" in ln]
        self.assertTrue(row, "GiftMesh is not mapped to the ziman tenant row")


class TestVocabulary(unittest.TestCase):
    """Every path the map cites is real; the names it retires stay retired."""

    def setUp(self):
        self.text = map_text()

    def test_cited_paths_exist(self):
        cited = set(re.findall(r"`([\w./-]+\.(?:py|json|yaml))`", self.text))
        self.assertTrue(cited, "no repository paths cited — table gone?")
        for rel in sorted(cited):
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)),
                            f"map cites {rel!r}, which does not exist")

    def test_imported_names_exist_only_in_the_map(self):
        for path in code_files():
            with open(path, encoding="utf-8", errors="replace") as fh:
                body = fh.read()
            for name in IMPORTED_NAMES:
                self.assertNotIn(name, body,
                                 f"{os.path.relpath(path, ROOT)} uses {name!r}; "
                                 f"the real component is named in the map")

    def test_map_states_no_test_total(self):
        """§8-a: the map points at the baseline tool instead of a figure."""
        self.assertIn("tools/repo_baseline.py", self.text)
        stale = re.findall(r"\d{3,4}\s*(?:تست|tests?|passed)", self.text)
        self.assertEqual(stale, [],
                         f"map hard-codes a test count: {stale}")

    def test_constitution_states_no_test_total(self):
        """The rule §8-a states, applied to the document that states it.

        CLAUDE.md carried a fixed green-test figure and was 319 behind within
        days — a document describing itself instead of the tree. The number
        now comes from the tool; this keeps it from being written back in.
        """
        with open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8") as fh:
            body = fh.read()
        self.assertIn("tools/repo_baseline.py", body)
        stale = re.findall(r"\d{3,4}\s*(?:تست|tests?|passed)", body)
        self.assertEqual(stale, [],
                         f"CLAUDE.md hard-codes a test count: {stale}")


class TestBaselineIsDerived(unittest.TestCase):
    """The baseline tool reads the files rather than repeating the map."""

    def test_tool_agrees_with_packs(self):
        from tools.repo_baseline import baseline
        data = baseline()
        self.assertEqual(sorted(data["tenants"]), sorted(load_dir(PACKS_DIR)))
        self.assertEqual(data["tenant_count"], len(data["tenants"]))

    def test_tool_agrees_with_registry(self):
        from tools.repo_baseline import baseline
        path = os.path.join(ROOT, "data", "painting_source_registry.json")
        with open(path, encoding="utf-8") as fh:
            actual = len(json.load(fh)["sources"])
        self.assertEqual(baseline()["painting_registry_sources"], actual)

    def test_shut_gates_are_reported_per_tenant(self):
        """studio carries a gate the others do not; a node-wide count hides it."""
        from tools.repo_baseline import baseline
        shut = baseline()["shut_gates_by_tenant"]
        self.assertIn("partner_precondition", shut["studio"])
        self.assertNotIn("partner_precondition", shut["ziman"])


if __name__ == "__main__":
    unittest.main()
