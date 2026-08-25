import unittest
from pathlib import Path
import tempfile

from ofn.organism.cognition.voice import compose_utterance, match_intent
from ofn.organism.tools.discover import (
    _hex_ipv4_le,
    discover_neighbors,
    discover_place,
    run_tools,
)


class DiscoverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "proc/sys/kernel").mkdir(parents=True)
        (self.root / "proc/sys/kernel/hostname").write_text(
            "octopus-continuity-180\n", encoding="utf-8"
        )
        (self.root / "proc/sys/kernel/random").mkdir(parents=True)
        (self.root / "proc/sys/kernel/random/boot_id").write_text(
            "boot-test\n", encoding="utf-8"
        )
        (self.root / "proc/device-tree").mkdir(parents=True)
        (self.root / "proc/device-tree/model").write_bytes(b"Orange Pi 5 Pro\x00")
        (self.root / "proc/uptime").write_text("12.5 80.0\n", encoding="utf-8")
        (self.root / "proc/net").mkdir(parents=True)
        (self.root / "proc/net/route").write_text(
            "Iface\tDestination\tGateway\tFlags\tRefCnt\tUse\tMetric\tMask\tMTU\tWindow\tIRTT\n"
            "eth0\t00000000\t0100A8C0\t0003\t0\t0\t0\t00000000\t0\t0\t0\n",
            encoding="utf-8",
        )
        (self.root / "proc/net/fib_trie").write_text(
            "     +-- 192.168.0.0/24 2 0 1\n"
            "        |-- 192.168.0.180\n"
            "           /32 host LOCAL\n",
            encoding="utf-8",
        )
        (self.root / "proc/net/arp").write_text(
            "IP address       HW type     Flags       HW address            Mask     Device\n"
            "192.168.0.138    0x1         0x2         c0:74:2b:f9:72:d5     *        eth0\n"
            "192.168.0.1      0x1         0x2         08:40:f3:eb:ba:a0     *        eth0\n",
            encoding="utf-8",
        )
        eth = self.root / "sys/class/net/eth0"
        eth.mkdir(parents=True)
        (eth / "address").write_text("c0:74:2b:f9:72:90\n", encoding="utf-8")
        (eth / "operstate").write_text("up\n", encoding="utf-8")
        wlan = self.root / "sys/class/net/wlan0"
        wlan.mkdir()
        (wlan / "address").write_text("aa:aa:aa:aa:aa:aa\n", encoding="utf-8")
        (wlan / "operstate").write_text("down\n", encoding="utf-8")
        zone = self.root / "sys/class/thermal/thermal_zone0"
        zone.mkdir(parents=True)
        (zone / "type").write_text("soc-thermal\n", encoding="utf-8")
        (zone / "temp").write_text("29615\n", encoding="utf-8")
        (self.root / "proc/meminfo").write_text(
            "MemTotal:        4000000 kB\nMemAvailable:    2700000 kB\n",
            encoding="utf-8",
        )
        (self.root / "sys/devices/system/cpu").mkdir(parents=True)
        (self.root / "sys/devices/system/cpu/present").write_text("0-7\n", encoding="utf-8")
        (self.root / "etc").mkdir()
        (self.root / "etc/timezone").write_text("UTC\n", encoding="utf-8")

    def test_gateway_bytes(self):
        self.assertEqual(_hex_ipv4_le("0100A8C0"), "192.168.0.1")

    def test_place_and_neighbor_family(self):
        place = discover_place(self.root)
        self.assertEqual(place["hostname"], "octopus-continuity-180")
        self.assertEqual(place["board_model"], "Orange Pi 5 Pro")
        self.assertEqual(place["ipv4"], "192.168.0.180")
        self.assertEqual(place["gateway_ipv4"], "192.168.0.1")
        self.assertEqual(place["wlan0_operstate"], "down")
        self.assertEqual(place["gps"], "ABSENT")
        neighbors = discover_neighbors(self.root)
        family = {
            item["ip"]: item["same_mac_family_as_self"] for item in neighbors["arp"]
        }
        self.assertTrue(family["192.168.0.138"])
        self.assertFalse(family["192.168.0.1"])

    def test_place_speech_uses_measured_facts(self):
        self.assertEqual(match_intent("کجایی"), "place")
        discovery = run_tools(self.root, force=True)
        text = compose_utterance(
            "place",
            {"discovery": discovery, "organism_id": "board-life-001"},
        )
        self.assertIn("192.168.0.180", text)
        self.assertIn("Orange Pi 5 Pro", text)
        self.assertIn("UNMEASURED_NO_GPS_NO_GEOIP", text)
        self.assertNotIn("تهران", text)

    def test_microphone_absent_without_pcm(self):
        discovery = run_tools(self.root, force=True)
        self.assertEqual(discovery["senses"]["microphone"], "NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
