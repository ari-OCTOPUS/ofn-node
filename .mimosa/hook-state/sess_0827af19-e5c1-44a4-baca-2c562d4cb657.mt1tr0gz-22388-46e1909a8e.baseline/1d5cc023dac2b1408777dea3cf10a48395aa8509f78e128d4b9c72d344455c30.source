#!/usr/bin/env python3
"""
Tests for manifest_generator.py

Run with unittest:
    python -m unittest body_bridge.tests.test_manifest_generator
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure kernel root is on path
KERNEL_ROOT = Path("F:/backup/03 - Projects/research-spec-compiler")
if str(KERNEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KERNEL_ROOT))

from body_bridge import manifest_generator as mg


class TestManifestGenerator(unittest.TestCase):
    """Unit tests for the manifest_generator module."""

    def setUp(self):
        """Create a temporary fake kernel tree."""
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "fake_kernel"
        self.root.mkdir()
        (self.root / "adr").mkdir()
        (self.root / "experiments").mkdir()
        (self.root / "specs").mkdir()
        (self.root / "body_bridge" / "output").mkdir(parents=True)

        # Integrity files
        (self.root / "rsc.py").write_text("print('hello')", encoding="utf-8")
        (self.root / "SENSITIVITY-LADDER.md").write_text(
            "### 🟢 LOW\nRead-only.\n\n### 🟡 MEDIUM\nEdits.\n\n### 🔴 HIGH\n1. **body write**\n2. **daemon**\n",
            encoding="utf-8",
        )
        (self.root / "GEOMETRY.md").write_text("# Geometry\n", encoding="utf-8")
        (self.root / "CLAIMS_LEDGER.csv").write_text(
            "claim_id,claim,c_level,verdict,primary_metric,primary_value,evidence_tag,source,spec,seed_family,caveats\n"
            "ADR-001,Fake claim,C0,INTEGRATE,acc,0.9,FACT,adr/ADR-001.md,specs/fake.yaml,100000,none\n",
            encoding="utf-8",
        )

        # Fake ADR
        (self.root / "adr" / "ADR-001-fake.md").write_text(
            "# ADR-001 — Fake ADR for testing\n"
            "- **Status:** Closed — machine verdict INTEGRATE\n"
            "- **Date:** 2026-07-14\n"
            "- **Spec:** `specs/fake.yaml`\n"
            "- **Decision rule (GO/NO-GO):** < 0.5 → DISCARD · ≥ 0.5 → INTEGRATE\n",
            encoding="utf-8",
        )

        # Fake spec + experiment module
        (self.root / "specs" / "fake.yaml").write_text("name: fake\n", encoding="utf-8")
        (self.root / "experiments" / "fake.py").write_text("# experiment\n", encoding="utf-8")

        # Patch module paths for this test
        self._orig_kernel_root = mg.KERNEL_ROOT
        self._orig_output_dir = mg.OUTPUT_DIR
        self._orig_manifest_json = mg.MANIFEST_JSON
        self._orig_integrity_files = mg.INTEGRITY_FILES
        mg.KERNEL_ROOT = self.root
        mg.OUTPUT_DIR = self.root / "body_bridge" / "output"
        mg.MANIFEST_JSON = mg.OUTPUT_DIR / "manifest.json"
        mg.INTEGRITY_FILES = [
            self.root / "rsc.py",
            self.root / "SENSITIVITY-LADDER.md",
            self.root / "GEOMETRY.md",
            self.root / "CLAIMS_LEDGER.csv",
        ]

    def tearDown(self):
        """Restore original paths."""
        mg.KERNEL_ROOT = self._orig_kernel_root
        mg.OUTPUT_DIR = self._orig_output_dir
        mg.MANIFEST_JSON = self._orig_manifest_json
        mg.INTEGRITY_FILES = self._orig_integrity_files
        self.tmp.cleanup()

    def test_generate_required_keys(self):
        """generate() must emit a JSON manifest containing all mandatory top-level keys."""
        manifest = mg.generate()

        required = {
            "kernel_name", "ring", "status", "autonomy", "risk_tier",
            "capabilities", "experiments", "adrs", "sensitivity_ladder",
            "commands", "interfaces", "last_updated", "integrity",
        }
        self.assertTrue(required.issubset(manifest.keys()))

        self.assertEqual(manifest["kernel_name"], "Cognitive Kernel 0.1")
        self.assertEqual(manifest["ring"], 2)
        self.assertEqual(manifest["status"], "shadow-attached")
        self.assertEqual(manifest["autonomy"], "L1-propose-only")
        self.assertEqual(manifest["risk_tier"], "green")
        self.assertIsInstance(manifest["capabilities"], list)
        self.assertIsInstance(manifest["experiments"], list)
        self.assertIsInstance(manifest["adrs"], list)
        self.assertIsInstance(manifest["integrity"], dict)
        self.assertIsInstance(manifest["sensitivity_ladder"], dict)

        on_disk = self.root / "body_bridge" / "output" / "manifest.json"
        self.assertTrue(on_disk.exists())
        with open(on_disk, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["kernel_name"], manifest["kernel_name"])

    def test_validate_integrity_no_manifest(self):
        """validate_integrity() must report valid=False when manifest does not exist."""
        result = mg.validate_integrity()
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "manifest_missing")
        self.assertFalse(result["manifest_exists"])

    def test_validate_integrity_tampering_detected(self):
        """validate_integrity() must detect when a tracked file has changed."""
        mg.generate()
        result = mg.validate_integrity()
        self.assertTrue(result["valid"])
        self.assertTrue(result["manifest_exists"])
        self.assertEqual(result["reason"], "ok")

        # Tamper with rsc.py
        (self.root / "rsc.py").write_text("# tampered\n", encoding="utf-8")
        result_after = mg.validate_integrity()
        self.assertFalse(result_after["valid"])
        self.assertIn("rsc.py", result_after["details"])
        self.assertFalse(result_after["details"]["rsc.py"]["ok"])

    def test_parse_adr_frontmatter(self):
        """_parse_adr_frontmatter must extract number, title, verdict, date, spec, decision rule."""
        text = (
            "# ADR-042 — Example Decision Record\n"
            "- **Status:** Closed — machine verdict OPTIMIZE\n"
            "- **Date:** 2026-07-10\n"
            "- **Spec:** `specs/example.yaml`\n"
            "- **Decision rule (GO/NO-GO):** < 0.3 → DISCARD · [0.3, 0.7) → OPTIMIZE · ≥ 0.7 → INTEGRATE\n"
        )
        parsed = mg._parse_adr_frontmatter(text)
        self.assertEqual(parsed["number"], "ADR-042")
        self.assertEqual(parsed["title"], "Example Decision Record")
        self.assertEqual(parsed["verdict"], "OPTIMIZE")
        self.assertEqual(parsed["date"], "2026-07-10")
        self.assertEqual(parsed["spec"], "specs/example.yaml")
        self.assertIn("DISCARD", parsed["decision_rule"])

    def test_parse_adr_accepted(self):
        """ADRs with 'Accepted' must map to ACCEPTED verdict."""
        text = (
            "# ADR-007 — Governance Layer\n"
            "- **Status:** Accepted (governance; not an experiment)\n"
        )
        parsed = mg._parse_adr_frontmatter(text)
        self.assertEqual(parsed["number"], "ADR-007")
        self.assertEqual(parsed["verdict"], "ACCEPTED")

    def test_parse_adr_bold_verdict(self):
        """ADRs with markdown-bold around the verdict word must be parsed."""
        text = (
            "# ADR-009 — Social Mirror\n"
            "- **Status:** Closed — machine verdict **INTEGRATE** (see §Verdict)\n"
        )
        parsed = mg._parse_adr_frontmatter(text)
        self.assertEqual(parsed["verdict"], "INTEGRATE")

    def test_parse_adr_no_false_applies(self):
        """Phrases like 'no machine verdict applies' must not yield a false verdict."""
        text = (
            "# ADR-007 — Central Law\n"
            "- **Status:** Accepted (governance; not an experiment — no machine verdict applies)\n"
        )
        parsed = mg._parse_adr_frontmatter(text)
        self.assertEqual(parsed["verdict"], "ACCEPTED")

    def test_parse_adr_empty(self):
        """Empty input must degrade gracefully."""
        parsed = mg._parse_adr_frontmatter("")
        self.assertIsNone(parsed["number"])
        self.assertEqual(parsed["verdict"], "UNKNOWN")

    def test_scan_experiments_deterministic(self):
        """_scan_experiments must return a deterministic sorted list."""
        exps = mg._scan_experiments()
        names = [e["name"] for e in exps]
        self.assertIn("fake", names)
        self.assertEqual(names, sorted(names))

    def test_read_sensitivity_ladder_missing_file(self):
        """When SENSITIVITY-LADDER.md is missing, return default summaries."""
        orig_root = mg.KERNEL_ROOT
        try:
            mg.KERNEL_ROOT = Path(tempfile.mkdtemp())
            ladder = mg._read_sensitivity_ladder()
            self.assertIn("LOW", ladder)
            self.assertIn("MEDIUM", ladder)
            self.assertIn("HIGH", ladder)
        finally:
            mg.KERNEL_ROOT = orig_root

    def test_sha256_changes(self):
        """_sha256_of_file must produce different digests for different contents."""
        path = self.root / "rsc.py"
        h1 = mg._sha256_of_file(path)
        path.write_text("# modified\n", encoding="utf-8")
        h2 = mg._sha256_of_file(path)
        self.assertNotEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_commands_dict(self):
        """The commands dict must map core commands to sensitivity grades."""
        manifest = mg.generate()
        cmds = manifest["commands"]
        self.assertIn("validate", cmds)
        self.assertIn("run", cmds)
        self.assertEqual(cmds["validate"], "LOW")
        self.assertEqual(cmds["body.write"], "HIGH")


if __name__ == "__main__":
    unittest.main()
