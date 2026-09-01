"""Preflight: state directory permission checks.

The state directory holds SQLite databases with tenant data. If it is
world-readable or group-readable, a local user without authorisation can
copy the databases and read everything. The preflight check surfaces this
without auto-correcting — chmod is a deliberate operator action.
"""

from __future__ import annotations

import os
import stat
import tempfile
import unittest

from ofn.preflight import _check_state_dir_mode


class TestStateDirModeCheck(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = self._dir.name

    # POSIX permission bits have no Windows equivalent (chmod there only
    # toggles the read-only flag), so the mode-bit assertions are Linux-only.
    @unittest.skipIf(os.name == "nt", "POSIX permission-bit semantics")
    def test_0700_passes_silently(self):
        os.chmod(self.path, 0o700)
        warnings = _check_state_dir_mode(self.path)
        self.assertEqual(warnings, [])

    @unittest.skipIf(os.name == "nt", "POSIX permission-bit semantics")
    def test_0755_warns(self):
        os.chmod(self.path, 0o755)
        warnings = _check_state_dir_mode(self.path)
        self.assertEqual(len(warnings), 1)
        self.assertIn("0700", warnings[0])
        self.assertIn("chmod", warnings[0])

    @unittest.skipIf(os.name == "nt", "POSIX permission-bit semantics")
    def test_0750_warns(self):
        """Group-readable is still too permissive."""
        os.chmod(self.path, 0o750)
        warnings = _check_state_dir_mode(self.path)
        self.assertEqual(len(warnings), 1)

    def test_missing_dir_returns_no_warnings(self):
        """A non-existent directory is not a warning here — makedirs handles it."""
        warnings = _check_state_dir_mode("/nonexistent/path/that/does/not/exist")
        self.assertEqual(warnings, [])

    def test_warning_names_the_path(self):
        os.chmod(self.path, 0o777)
        warnings = _check_state_dir_mode(self.path)
        self.assertIn(self.path, warnings[0])
