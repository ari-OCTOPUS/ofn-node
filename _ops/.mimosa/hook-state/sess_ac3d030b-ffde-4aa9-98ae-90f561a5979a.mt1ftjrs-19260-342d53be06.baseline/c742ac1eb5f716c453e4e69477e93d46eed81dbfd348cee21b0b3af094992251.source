#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Beat Ownership Lease — unique test file (WORKLOCK: not registered in run_all.py).

Run:
  python _ops/tests/test_beat_ownership_lease_20260816.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

OPS = Path(__file__).resolve().parents[1]
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

from octopus_v3.beat_lease import (  # noqa: E402
    TTL_S,
    BeatOwnership,
    beat_allowed,
)
from octopus_v3.exceptions import DualBeatDenied  # noqa: E402


class BeatLeaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.path = Path(self._td.name) / "beat-ownership-lease.json"
        self.key = b"unit-test-beat-lease-hmac"
        self.own = BeatOwnership(self.path, self.key)
        self._env = {k: os.environ.get(k) for k in (
            "OCTOPUS_BEAT_LEASE", "OCTOPUS_BEAT_HOLDER",
            "OCTOPUS_BEAT_ROLE", "OCTOPUS_BEAT_LEASE_HMAC",
            "OCTOPUS_BEAT_LEASE_PATH",
        )}

    def tearDown(self) -> None:
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self._td.cleanup()

    def test_flag_off_allows_beat_without_file(self) -> None:
        os.environ["OCTOPUS_BEAT_LEASE"] = "0"
        self.assertTrue(beat_allowed(path=self.path, hmac_key=self.key, holder_id="laptop-a"))
        self.assertFalse(self.path.exists())

    def test_flag_on_without_hmac_denies(self) -> None:
        os.environ["OCTOPUS_BEAT_LEASE"] = "1"
        os.environ["OCTOPUS_BEAT_HOLDER"] = "laptop-a"
        os.environ.pop("OCTOPUS_BEAT_LEASE_HMAC", None)
        self.assertFalse(beat_allowed(path=self.path, hmac_key=b"", holder_id="laptop-a", role="laptop"))

    def test_flag_on_without_lease_denies(self) -> None:
        os.environ["OCTOPUS_BEAT_LEASE"] = "1"
        os.environ["OCTOPUS_BEAT_HOLDER"] = "laptop-a"
        os.environ["OCTOPUS_BEAT_ROLE"] = "laptop"
        os.environ["OCTOPUS_BEAT_LEASE_HMAC"] = self.key.decode("ascii")
        os.environ["OCTOPUS_BEAT_LEASE_PATH"] = str(self.path)
        self.assertFalse(beat_allowed())

    def test_holder_beats_other_denied(self) -> None:
        t0 = 1_000_000.0
        self.own.acquire("laptop-a", "laptop", now=t0)
        self.assertTrue(self.own.may_beat("laptop-a", now=t0 + 1))
        self.assertFalse(self.own.may_beat("arm1-b", now=t0 + 1))
        with self.assertRaises(DualBeatDenied) as ctx:
            self.own.acquire("arm1-b", "arm1", now=t0 + 1)
        self.assertIn("beat held by", str(ctx.exception))

    def test_expired_lease_can_be_stolen_once(self) -> None:
        t0 = 1_000_000.0
        first = self.own.acquire("laptop-a", "laptop", now=t0)
        stolen = self.own.acquire("arm1-b", "arm1", now=t0 + TTL_S + 0.01)
        self.assertEqual(stolen.generation, first.generation + 1)
        self.assertTrue(self.own.may_beat("arm1-b", now=t0 + TTL_S + 1))
        self.assertFalse(self.own.may_beat("laptop-a", now=t0 + TTL_S + 1))

    def test_shadow_must_not_acquire(self) -> None:
        with self.assertRaises(DualBeatDenied):
            self.own.acquire("arm1-shadow", "shadow", now=1.0)
        os.environ["OCTOPUS_BEAT_LEASE"] = "1"
        os.environ["OCTOPUS_BEAT_ROLE"] = "shadow"
        os.environ["OCTOPUS_BEAT_HOLDER"] = "arm1-shadow"
        os.environ["OCTOPUS_BEAT_LEASE_HMAC"] = "x"
        self.assertFalse(beat_allowed(path=self.path, hmac_key=self.key, holder_id="arm1-shadow", role="shadow"))

    def test_renew_extends_ttl_same_generation(self) -> None:
        t0 = 1_000_000.0
        a = self.own.acquire("laptop-a", "laptop", now=t0)
        b = self.own.renew("laptop-a", now=t0 + 30)
        self.assertEqual(a.generation, b.generation)
        self.assertGreater(b.expires_unix, a.expires_unix)
        self.assertTrue(self.own.may_beat("laptop-a", now=t0 + 30 + 50))

    def test_release_lets_the_other_side_take_over(self) -> None:
        t0 = 1_000_000.0
        self.own.acquire("laptop-a", "laptop", now=t0)
        self.own.release("laptop-a", now=t0 + 5)
        self.assertFalse(self.own.may_beat("laptop-a", now=t0 + 5.1))
        other = self.own.acquire("arm1-b", "arm1", now=t0 + 5.1)
        self.assertTrue(other.generation >= 0)
        self.assertTrue(self.own.may_beat("arm1-b", now=t0 + 6))

    def test_tamper_is_not_a_steal_opportunity(self) -> None:
        t0 = 1_000_000.0
        self.own.acquire("laptop-a", "laptop", now=t0)
        raw = self.path.read_text("utf-8")
        self.path.write_text(raw.replace("laptop-a", "arm1-evil", 1), encoding="utf-8")
        with self.assertRaises(DualBeatDenied):
            self.own.acquire("arm1-b", "arm1", now=t0 + 1)

    def test_ttl_is_sixty_seconds(self) -> None:
        self.assertEqual(TTL_S, 60.0)


if __name__ == "__main__":
    raise SystemExit(unittest.main(verbosity=2))
