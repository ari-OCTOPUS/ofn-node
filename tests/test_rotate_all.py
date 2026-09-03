"""Tests for deploy/rotate_all.ps1 — the names-only rotation checklist.

The test that matters most plants a canary VALUE in a fake env file and
asserts the tool's output never contains it: a rotation tool that leaks the
old secret while checking for it would be worse than no tool.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import unittest

from tests.tmpdir import temp_dir

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "deploy", "rotate_all.ps1")
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")

CANARY_VALUE = "CANARY-VALUE-a51f3c-must-never-appear"


def _run(args):
    completed = subprocess.run(
        [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", SCRIPT, *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=60, check=False, cwd=ROOT)
    return completed


def _write_manifest(tmp, env_name, confirm="ROTATE"):
    manifest = {
        "schema": "octopus.rotation.manifest.v1",
        "confirm_word": confirm,
        "secrets": [
            {
                "name": "FAKE_SECRET_ONE",
                "service": "test service",
                "locations": [env_name],
                "rotation_ref": "test console",
            },
            {
                "name": "FAKE_SECRET_ABSENT",
                "service": "test service",
                "locations": [env_name],
                "rotation_ref": "test console",
            },
        ],
    }
    path = os.path.join(tmp, "manifest.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle)
    return path


@unittest.skipIf(
    platform.system() != "Windows" or POWERSHELL is None,
    "powershell tool — windows runners only",
)
class RotateAllDryRun(unittest.TestCase):
    def test_dry_run_locates_names_and_never_prints_values(self):
        tmp = temp_dir(self)
        env_path = os.path.join(tmp, "env")
        with open(env_path, "w", encoding="utf-8") as handle:
            handle.write(f"FAKE_SECRET_ONE={CANARY_VALUE}\nOTHER=x\n")
        manifest = _write_manifest(tmp, env_path)

        completed = _run(["-Manifest", manifest])
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("FAKE_SECRET_ONE", completed.stdout)
        self.assertIn("located", completed.stdout)
        self.assertIn("FAKE_SECRET_ABSENT", completed.stdout)
        self.assertIn("name-absent", completed.stdout)
        # the canary value must never reach the output
        self.assertNotIn(CANARY_VALUE, completed.stdout)
        self.assertNotIn(CANARY_VALUE, completed.stderr)
        # dry-run writes no receipts (scoped to the tool's receipt dir —
        # state/ may legitimately hold other runtime artifacts)
        self.assertFalse(
            os.path.exists(os.path.join(ROOT, "state", "rotation-receipts")))

    def test_missing_manifest_is_exit_2(self):
        completed = _run(["-Manifest", os.path.join("definitely", "missing")])
        self.assertEqual(completed.returncode, 2)

    def test_apply_without_confirm_word_is_refused(self):
        tmp = temp_dir(self)
        env_path = os.path.join(tmp, "env")
        with open(env_path, "w", encoding="utf-8") as handle:
            handle.write("FAKE_SECRET_ONE=whatever\n")
        manifest = _write_manifest(tmp, env_path)
        completed = _run(["-Manifest", manifest, "-Apply",
                          "-ConfirmWord", "WRONG",
                          "-ReceiptDir", os.path.join(tmp, "receipts")])
        self.assertEqual(completed.returncode, 3)
        self.assertIn("refused", completed.stdout)


if __name__ == "__main__":
    unittest.main()
