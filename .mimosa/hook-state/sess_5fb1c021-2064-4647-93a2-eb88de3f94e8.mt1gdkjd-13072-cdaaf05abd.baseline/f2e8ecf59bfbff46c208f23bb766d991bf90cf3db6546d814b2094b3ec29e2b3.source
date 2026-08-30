"""Unit tests for ofn.adapters.sysmetrics — using mocked sysfs/proc files.

No real hardware needed; all source files are created in temp directories.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from ofn.adapters import sysmetrics


class TestReadThermal(unittest.TestCase):
    """_read_thermal() with mocked /sys/class/thermal."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.thermal_base = os.path.join(self.tmpdir.name, "thermal")

    def tearDown(self):
        self.tmpdir.cleanup()

    def _make_zone(self, zone_name: str, zone_type: str, temp_mc: int) -> None:
        """Create a fake thermal_zone{N} with type and temp files."""
        zone_path = os.path.join(self.thermal_base, zone_name)
        os.makedirs(zone_path, exist_ok=True)
        with open(os.path.join(zone_path, "type"), "w") as f:
            f.write(zone_type)
        with open(os.path.join(zone_path, "temp"), "w") as f:
            f.write(f"{temp_mc}\n")

    def test_single_zone_converts_millidegrees(self):
        """29615 millidegrees should become 29.6 C."""
        self._make_zone("thermal_zone0", "soc-thermal", 29615)
        with mock.patch.object(sysmetrics, "_THERMAL_BASE", self.thermal_base):
            result = sysmetrics._read_thermal()
        self.assertEqual(result["soc-thermal"], 29.6)

    def test_missing_zone_returns_none(self):
        """A zone that doesn't exist should be None."""
        with mock.patch.object(sysmetrics, "_THERMAL_BASE", self.thermal_base):
            result = sysmetrics._read_thermal()
        self.assertIsNone(result["soc-thermal"])

    def test_multiple_zones(self):
        """Multiple zones are read independently."""
        self._make_zone("thermal_zone0", "soc-thermal", 45000)
        self._make_zone("thermal_zone1", "gpu-thermal", 55000)
        with mock.patch.object(sysmetrics, "_THERMAL_BASE", self.thermal_base):
            result = sysmetrics._read_thermal()
        self.assertEqual(result["soc-thermal"], 45.0)
        self.assertEqual(result["gpu-thermal"], 55.0)

    def test_unknown_zone_type_ignored(self):
        """A zone whose type is not in _THERMAL_TYPES should be ignored."""
        self._make_zone("thermal_zone0", "unknown-type", 30000)
        self._make_zone("thermal_zone1", "bigcore0-thermal", 40000)
        with mock.patch.object(sysmetrics, "_THERMAL_BASE", self.thermal_base):
            result = sysmetrics._read_thermal()
        # unknown-type is not in the dict (no key for it)
        self.assertNotIn("unknown-type", result)
        self.assertEqual(result["bigcore0-thermal"], 40.0)

    def test_corrupt_temp_file_returns_none_for_zone(self):
        """A zone with an unreadable temp should be None."""
        zone_path = os.path.join(self.thermal_base, "thermal_zone0")
        os.makedirs(zone_path, exist_ok=True)
        with open(os.path.join(zone_path, "type"), "w") as f:
            f.write("soc-thermal")
        # Write a non-integer temp
        with open(os.path.join(zone_path, "temp"), "w") as f:
            f.write("not-a-number\n")
        with mock.patch.object(sysmetrics, "_THERMAL_BASE", self.thermal_base):
            result = sysmetrics._read_thermal()
        self.assertIsNone(result["soc-thermal"])

    def test_missing_thermal_base_returns_all_none(self):
        """If _THERMAL_BASE doesn't exist, all values should be None."""
        nonexistent = os.path.join(self.tmpdir.name, "nonexistent")
        with mock.patch.object(sysmetrics, "_THERMAL_BASE", nonexistent):
            result = sysmetrics._read_thermal()
        for key in sysmetrics._THERMAL_TYPES:
            self.assertIsNone(result[key])


class TestReadMeminfo(unittest.TestCase):
    """_read_meminfo() with mocked /proc/meminfo."""

    def test_parses_meminfo(self):
        content = (
            "MemTotal:       3910156 kB\n"
            "MemFree:         220712 kB\n"
            "MemAvailable:   2207456 kB\n"
            "Buffers:          63456 kB\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".meminfo",
                                         delete=False, encoding="utf-8") as f:
            f.write(content)
            f.flush()
            path = f.name
        try:
            with mock.patch.object(sysmetrics, "_PROC_MEMINFO", path):
                result = sysmetrics._read_meminfo()
        finally:
            os.unlink(path)

        self.assertEqual(result["total_b"], 3910156 * 1024)
        self.assertEqual(result["available_b"], 2207456 * 1024)
        self.assertEqual(result["free_b"], 220712 * 1024)

    def test_missing_file_returns_zeros(self):
        with mock.patch.object(sysmetrics, "_PROC_MEMINFO",
                               "/nonexistent/meminfo"):
            result = sysmetrics._read_meminfo()
        self.assertEqual(result, {"total_b": 0, "available_b": 0, "free_b": 0})


class TestReadLoadavg(unittest.TestCase):
    """_read_loadavg() with mocked /proc/loadavg."""

    def test_parses_loadavg(self):
        content = "0.47 0.68 0.62 2/742 12345\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".loadavg",
                                         delete=False, encoding="utf-8") as f:
            f.write(content)
            f.flush()
            path = f.name
        try:
            with mock.patch.object(sysmetrics, "_PROC_LOADAVG", path):
                result = sysmetrics._read_loadavg()
        finally:
            os.unlink(path)

        self.assertIsNotNone(result)
        self.assertAlmostEqual(result[0], 0.47)
        self.assertAlmostEqual(result[1], 0.68)
        self.assertAlmostEqual(result[2], 0.62)

    def test_missing_file_returns_none(self):
        with mock.patch.object(sysmetrics, "_PROC_LOADAVG",
                               "/nonexistent/loadavg"):
            result = sysmetrics._read_loadavg()
        self.assertIsNone(result)

    def test_corrupt_file_returns_none(self):
        content = "not numbers at all\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".loadavg",
                                         delete=False, encoding="utf-8") as f:
            f.write(content)
            f.flush()
            path = f.name
        try:
            with mock.patch.object(sysmetrics, "_PROC_LOADAVG", path):
                result = sysmetrics._read_loadavg()
        finally:
            os.unlink(path)
        self.assertIsNone(result)


class TestReadUptime(unittest.TestCase):
    """_read_uptime_s() with mocked /proc/uptime."""

    def test_parses_uptime(self):
        content = "12345.67 23456.78\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".uptime",
                                         delete=False, encoding="utf-8") as f:
            f.write(content)
            f.flush()
            path = f.name
        try:
            with mock.patch.object(sysmetrics, "_PROC_UPTIME", path):
                result = sysmetrics._read_uptime_s()
        finally:
            os.unlink(path)

        self.assertIsNotNone(result)
        self.assertAlmostEqual(result, 12345.67)

    def test_missing_file_returns_none(self):
        with mock.patch.object(sysmetrics, "_PROC_UPTIME",
                               "/nonexistent/uptime"):
            result = sysmetrics._read_uptime_s()
        self.assertIsNone(result)


class TestReadDisk(unittest.TestCase):
    """_read_disk() with mocked statvfs."""

    def test_returns_disk_info(self):
        # Create a temp dir to point at (real filesystem)
        with tempfile.TemporaryDirectory() as tmpdir:
            result = sysmetrics._read_disk(tmpdir)
            # Real filesystem should return positive numbers
            self.assertGreater(result["total_b"], 0)
            self.assertGreater(result["free_b"], 0)
            self.assertGreater(result["used_b"], 0)
            # used + free should equal total
            self.assertEqual(result["used_b"] + result["free_b"],
                             result["total_b"])

    def test_nonexistent_path_returns_zeros(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = os.path.join(tmpdir, "nonexistent_mount")
            result = sysmetrics._read_disk(fake_path)
            self.assertEqual(result["total_b"], 0)
            self.assertEqual(result["free_b"], 0)
            self.assertEqual(result["used_b"], 0)


class TestSnapshot(unittest.TestCase):
    """snapshot() with all mocks in place."""

    def test_snapshot_returns_all_keys(self):
        """snapshot() must return every key the panel expects."""
        # Mock thermal
        thermal_tmp = tempfile.TemporaryDirectory()
        thermal_base = os.path.join(thermal_tmp.name, "thermal")
        os.makedirs(thermal_base)
        zone_path = os.path.join(thermal_base, "thermal_zone0")
        os.makedirs(zone_path)
        with open(os.path.join(zone_path, "type"), "w") as f:
            f.write("soc-thermal")
        with open(os.path.join(zone_path, "temp"), "w") as f:
            f.write("65000\n")  # 65.0 C

        # Mock meminfo
        meminfo_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".meminfo", delete=False, encoding="utf-8")
        meminfo_file.write("MemTotal:       3910156 kB\n"
                           "MemFree:         220712 kB\n"
                           "MemAvailable:   2207456 kB\n")
        meminfo_file.close()

        # Mock loadavg
        loadavg_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".loadavg", delete=False, encoding="utf-8")
        loadavg_file.write("0.47 0.68 0.62 2/742 12345\n")
        loadavg_file.close()

        # Mock uptime
        uptime_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".uptime", delete=False, encoding="utf-8")
        uptime_file.write("12345.67 23456.78\n")
        uptime_file.close()

        try:
            with mock.patch.object(sysmetrics, "_THERMAL_BASE", thermal_base), \
                 mock.patch.object(sysmetrics, "_PROC_MEMINFO",
                                   meminfo_file.name), \
                 mock.patch.object(sysmetrics, "_PROC_LOADAVG",
                                   loadavg_file.name), \
                 mock.patch.object(sysmetrics, "_PROC_UPTIME",
                                   uptime_file.name):
                result = sysmetrics.snapshot(state_dir=thermal_tmp.name)
        finally:
            os.unlink(meminfo_file.name)
            os.unlink(loadavg_file.name)
            os.unlink(uptime_file.name)
            thermal_tmp.cleanup()

        # Check all expected keys are present
        self.assertIn("thermal", result)
        self.assertIn("thermal_hottest_c", result)
        self.assertIn("throttling", result)
        self.assertIn("mem", result)
        self.assertIn("loadavg", result)
        self.assertIn("uptime_s", result)
        self.assertIn("disk", result)

        # Check thermal readings
        self.assertEqual(result["thermal"]["soc-thermal"], 65.0)
        self.assertEqual(result["thermal_hottest_c"], 65.0)

        # Check mem readings
        self.assertEqual(result["mem"]["total_b"], 3910156 * 1024)

        # Check loadavg
        self.assertAlmostEqual(result["loadavg"][0], 0.47)

        # Check uptime
        self.assertAlmostEqual(result["uptime_s"], 12345.67)

        # Not throttling at 65 C (threshold is 80)
        self.assertFalse(result["throttling"])

    def test_snapshot_throttling_detection(self):
        """Thermal reading >= 80 C should set throttling=True."""
        thermal_tmp = tempfile.TemporaryDirectory()
        thermal_base = os.path.join(thermal_tmp.name, "thermal")
        os.makedirs(thermal_base)
        zone_path = os.path.join(thermal_base, "thermal_zone0")
        os.makedirs(zone_path)
        with open(os.path.join(zone_path, "type"), "w") as f:
            f.write("soc-thermal")
        with open(os.path.join(zone_path, "temp"), "w") as f:
            f.write("85000\n")  # 85.0 C — above throttle threshold

        try:
            with mock.patch.object(sysmetrics, "_THERMAL_BASE", thermal_base), \
                 mock.patch.object(sysmetrics, "_PROC_MEMINFO", "/dev/null"), \
                 mock.patch.object(sysmetrics, "_PROC_LOADAVG", "/dev/null"), \
                 mock.patch.object(sysmetrics, "_PROC_UPTIME", "/dev/null"):
                result = sysmetrics.snapshot()
        finally:
            thermal_tmp.cleanup()

        self.assertEqual(result["thermal_hottest_c"], 85.0)
        self.assertTrue(result["throttling"])

    def test_snapshot_empty_state_dir(self):
        """snapshot() with no state_dir should return zero disk."""
        thermal_tmp = tempfile.TemporaryDirectory()
        thermal_base = os.path.join(thermal_tmp.name, "thermal")
        os.makedirs(thermal_base)
        # No zones created — all None
        try:
            with mock.patch.object(sysmetrics, "_THERMAL_BASE", thermal_base), \
                 mock.patch.object(sysmetrics, "_PROC_MEMINFO", "/dev/null"), \
                 mock.patch.object(sysmetrics, "_PROC_LOADAVG", "/dev/null"), \
                 mock.patch.object(sysmetrics, "_PROC_UPTIME", "/dev/null"):
                result = sysmetrics.snapshot(state_dir="")
        finally:
            thermal_tmp.cleanup()

        self.assertEqual(result["disk"],
                         {"total_b": 0, "free_b": 0, "used_b": 0})
        self.assertIsNone(result["thermal_hottest_c"])
        self.assertFalse(result["throttling"])
        # loadavg should be [] since /dev/null parse fails
        self.assertEqual(result["loadavg"], [])


if __name__ == "__main__":
    unittest.main()
