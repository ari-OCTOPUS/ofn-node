"""STAGE-01 gap scan: the registry is a claim, the tree is the measurement.

These tests exist because STAGE-00 and the 10-aspect report stated counts
and absences as prose. A number that is worth writing is worth deriving,
and an absence on this host is body_not_on_this_host, not body_missing.
"""

from __future__ import annotations

import ast
import json
import os
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN_DIR = os.path.join(
    ROOT, "docs", "octopus-surgery", "stage-01-lineage-scan", "2026-09-01"
)
REPORT = os.path.join(SCAN_DIR, "STAGE-01-REPORT.md")
CONTRADICTIONS = os.path.join(SCAN_DIR, "CONTRADICTIONS.md")
REGISTRY = os.path.join(SCAN_DIR, "CONCEPT-REGISTRY.json")
TOOL = os.path.join(ROOT, "tools", "gap_scan.py")

FORBIDDEN_IMPORT_ROOTS = {
    "socket",
    "ssl",
    "http",
    "urllib.request",
    "requests",
    "httpx",
    "aiohttp",
}
SECRET_FRAGMENTS = (
    ".config/ofn",
    "/etc/cloudflared",
    "board-cp-ca.pem",
)


def _import_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class TestSourceHashIsCheckoutStable(unittest.TestCase):
    def test_text_hash_ignores_crlf(self):
        from tools.gap_scan import _sha256_file
        with tempfile.TemporaryDirectory(prefix="gap-scan-nl-") as tmp:
            lf = os.path.join(tmp, "lf.md")
            crlf = os.path.join(tmp, "crlf.md")
            payload = "مرحله ۰\nline two\n"
            with open(lf, "wb") as fh:
                fh.write(payload.encode("utf-8"))
            with open(crlf, "wb") as fh:
                fh.write(payload.replace("\n", "\r\n").encode("utf-8"))
            self.assertEqual(
                _sha256_file(lf, normalize_newlines=True),
                _sha256_file(crlf, normalize_newlines=True),
            )
            self.assertNotEqual(
                _sha256_file(lf, normalize_newlines=False),
                _sha256_file(crlf, normalize_newlines=False),
            )

    def test_binary_hash_does_not_strip_cr(self):
        from tools.gap_scan import _sha256_file
        with tempfile.TemporaryDirectory(prefix="gap-scan-bin-") as tmp:
            path = os.path.join(tmp, "x.png")
            raw = b"\x89PNG\r\n\x1a\n" + b"\x00\x01"
            with open(path, "wb") as fh:
                fh.write(raw)
            self.assertEqual(
                _sha256_file(path, normalize_newlines=False),
                __import__("hashlib").sha256(raw).hexdigest(),
            )


class TestGapScanPurity(unittest.TestCase):
    def test_tool_does_not_import_network(self):
        with open(TOOL, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=TOOL)
        imported = _import_names(tree)
        offenders = []
        for name in imported:
            if name in FORBIDDEN_IMPORT_ROOTS or name.split(".")[0] in {
                "socket", "ssl", "http", "requests", "httpx", "aiohttp",
            }:
                offenders.append(name)
            if name == "urllib" or name.startswith("urllib.request"):
                offenders.append(name)
        self.assertEqual(offenders, [], f"gap_scan imported network code: {offenders}")

    def test_tool_does_not_name_secret_paths_as_inputs(self):
        with open(TOOL, encoding="utf-8") as fh:
            body = fh.read()
        self.assertIn("FORBIDDEN_READ_PREFIXES", body)
        self.assertIn("~/.config/ofn", body)
        self.assertNotIn("os.environ[", body)


class TestRegistryIsARealClaim(unittest.TestCase):
    def setUp(self):
        with open(REGISTRY, encoding="utf-8") as fh:
            self.reg = json.load(fh)

    def test_schema_and_unique_ids(self):
        self.assertEqual(self.reg["schema"], "octopus.gap_scan.registry.v1")
        ids = [row["id"] for row in self.reg["concepts"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 30)

    def test_every_concept_has_an_independent_record(self):
        for row in self.reg["concepts"]:
            self.assertIn(row["expected_status"], self.reg["status_vocabulary"])
            self.assertTrue(row.get("sources"), row["id"])
            has_paths = bool(row.get("must_exist") or row.get("must_not_exist"))
            self.assertTrue(has_paths, f"{row['id']} has no path record")

    def test_two_h1_concepts_are_not_the_same_thing(self):
        ids = {row["id"] for row in self.reg["concepts"]}
        self.assertIn("C-H1-HARVEST", ids)
        self.assertIn("C-H1-IDEM", ids)
        harvest = next(r for r in self.reg["concepts"] if r["id"] == "C-H1-HARVEST")
        idem = next(r for r in self.reg["concepts"] if r["id"] == "C-H1-IDEM")
        self.assertEqual(harvest["expected_status"], "present_in_this_lineage")
        self.assertEqual(idem["expected_status"], "body_not_on_this_host")
        self.assertNotEqual(harvest["must_exist"], idem["must_exist"])

    def test_stage00_fifty_concepts_are_marked_incomplete(self):
        row = next(r for r in self.reg["concepts"] if r["id"] == "STAGE00-C50")
        self.assertEqual(row["expected_status"], "incomplete_enumeration")

    def test_vault_bodies_are_not_called_missing(self):
        vault = {
            "C-OBS-RUNTIME",
            "C-HYP-ENGINE",
            "C-NBB-CP",
            "C-CHECKLIST-200",
            "C-OPS",
            "C-H1-IDEM",
        }
        for row in self.reg["concepts"]:
            if row["id"] in vault:
                self.assertEqual(row["expected_status"], "body_not_on_this_host",
                                 row["id"])

    def test_eight_coverage_domains_are_registered(self):
        domains = [r["id"] for r in self.reg["concepts"] if r["id"].startswith("DOM-")]
        self.assertEqual(
            sorted(domains),
            [
                "DOM-BACKUP",
                "DOM-CONSENT",
                "DOM-KERNEL",
                "DOM-OUTBOX",
                "DOM-PERMISSION",
                "DOM-RELEASE",
                "DOM-SECURITY",
                "DOM-TENANCY",
            ],
        )

    def test_registry_does_not_point_at_secret_files_to_read(self):
        for row in self.reg["concepts"]:
            for path in (row.get("must_exist") or []):
                for fragment in SECRET_FRAGMENTS:
                    self.assertNotIn(fragment, path, f"{row['id']} must_exist {path}")


class TestScanAgreesWithTheTree(unittest.TestCase):
    def test_live_scan_matches_registry(self):
        from tools.gap_scan import scan
        receipt = scan(root=ROOT, with_tests=False)
        self.assertTrue(receipt["sources"]["match"], receipt["sources"]["mismatches"])
        mismatches = [row for row in receipt["concepts"] if not row["match"]]
        self.assertEqual(mismatches, [], mismatches)
        self.assertTrue(receipt["ok"])
        self.assertEqual(receipt["baseline"]["tenants"],
                         sorted(receipt["baseline"]["tenants"]))
        self.assertIn("hypno", receipt["baseline"]["tenants"])

    def test_broken_expectation_is_visible(self):
        from tools.gap_scan import _classify
        fake = {
            "id": "FAKE-PRESENT",
            "expected_status": "present_in_this_lineage",
            "derive": "present_if_all_exist",
            "must_exist": ["this-file-does-not-exist-on-purpose.py"],
            "must_not_exist": [],
        }
        row = _classify(fake, ROOT)
        self.assertFalse(row["match"])
        self.assertEqual(row["derived_status"], "contradicted")

    def test_receipt_can_be_written_to_a_temp_dir(self):
        from tools.gap_scan import main
        with tempfile.TemporaryDirectory(prefix="gap-scan-") as tmp:
            dest = os.path.join(tmp, "receipt.json")
            rc = main(["--write-receipt", dest])
            self.assertEqual(rc, 0)
            with open(dest, encoding="utf-8") as fh:
                receipt = json.load(fh)
            self.assertEqual(receipt["schema"], "octopus.gap_scan.receipt.v1")
            self.assertTrue(receipt["ok"])
            self.assertTrue(receipt["propose_only"])


class TestReportDoesNotFreezeCounts(unittest.TestCase):
    def test_report_points_at_the_tool(self):
        with open(REPORT, encoding="utf-8") as fh:
            body = fh.read()
        self.assertIn("tools/gap_scan.py", body)
        self.assertIn("tools/repo_baseline.py", body)
        self.assertIn("this_host_only", body)
        self.assertIn("body_not_on_this_host", body)

    def test_report_does_not_hard_code_a_live_test_total(self):
        with open(REPORT, encoding="utf-8") as fh:
            body = fh.read()
        import re
        stale = re.findall(r"\d{3,4}\s*(?:تست|tests?|passed)", body)
        self.assertEqual(stale, [], f"STAGE-01 report froze a test count: {stale}")

    def test_contradictions_keep_both_values(self):
        with open(CONTRADICTIONS, encoding="utf-8") as fh:
            body = fh.read()
        self.assertIn("resolution: null", body)
        self.assertIn("414", body)
        self.assertIn("408", body)
        self.assertIn("207", body)
        self.assertIn("171", body)
        self.assertIn("C-H1-HARVEST", body)
        self.assertIn("C-H1-IDEM", body)


if __name__ == "__main__":
    unittest.main()
