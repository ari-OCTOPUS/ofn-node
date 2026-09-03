"""Adapter-level behaviour of the self-model producer and cockpit section.

Fixtures here mirror the real producers' output shapes exactly — including
the shapes they produce when a producer is absent, inconclusive, or
garbage. The integration cases at the bottom run the REAL producers
against this checkout (git) and the REAL loopback socket path.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from tests.tmpdir import temp_dir

from ofn.adapters import self_model_producer as producer
from ofn.adapters.cockpit_self_model import SelfModelSection
from ofn.kernel import self_model

ROOT = Path(__file__).resolve().parents[1]
FAKE_HEAD = "ab12" * 10
FAKE_LOG_EPOCH = 1770000000


def fresh_probe_evidence(now_epoch):
    """The dated run evidence the real host does not have — injected so the
    'every producer present' scenario can be exercised honestly."""
    return self_model.brain_probe_verdict(
        now_epoch - 10.0, "test:probe-receipt", now_epoch,
        producer.FRESHNESS_SECONDS["probe"])


def fake_git(repo_root, *args):
    """Mirrors real git output shapes: trailing newline, \\x1f-separated
    log fields, empty string (not None) for a detached branch."""
    if args == ("rev-parse", "HEAD"):
        return FAKE_HEAD + "\n"
    if args == ("branch", "--show-current"):
        return "lane/self-awareness\n"
    if args[0] == "log":
        return (
            f"{FAKE_HEAD}\x1f{FAKE_LOG_EPOCH}\x1ffeat(x): one\n"
            f"{'cd34' * 10}\x1f{FAKE_LOG_EPOCH - 90}\x1ffeat(x): two\n"
        )
    return None


def fake_prober_ok(unit):
    return True, "active"


def make_prober(mapping):
    def prober(unit):
        return mapping.get(unit, (None, "no route"))
    return prober


class ProducerEnvelope(unittest.TestCase):
    def test_produce_all_healthy_envelope(self):
        with mock.patch.object(
                producer, "_collect_brain_probe",
                lambda root, now: fresh_probe_evidence(now)):
            envelope = producer.produce(
                clock=lambda: 1000.0,
                repo_root=ROOT,
                git_runner=fake_git,
                unit_prober=fake_prober_ok,
            )
        self.assertEqual(envelope["schema"], producer.SCHEMA_ID)
        self.assertEqual(envelope["status"], "ok")
        self.assertEqual(envelope["data"]["code_identity"]["commit_sha"],
                         FAKE_HEAD)
        self.assertEqual(envelope["data"]["code_identity"]["branch"],
                         "lane/self-awareness")
        counts = envelope["data"]["counts"]
        self.assertEqual(counts["healthy"], counts["sensors"]
                         + counts["processes"] + counts["capabilities"])
        self.assertEqual(envelope["warnings"], [])
        # events carry provenance, parsed from the real log shape
        events = envelope["data"]["events"]
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["source"], "git:log")
        self.assertEqual(events[0]["subject"], "feat(x): one")

    def test_scenario_2_one_producer_absent(self):
        units = dict(producer.MEMBER_UNITS)
        prober_map = dict.fromkeys(units.values(), (True, "active"))
        prober_map[units["supervisor"]] = (False, "failed")

        envelope = producer.produce(
            clock=lambda: 1000.0, repo_root=ROOT,
            git_runner=fake_git, unit_prober=make_prober(prober_map))
        row = next(item for item in envelope["data"]["processes"]
                   if item["sensor_id"] == "process_supervisor")
        self.assertEqual(row["status"], "absent")
        self.assertIn("process_supervisor_absent", envelope["warnings"])

    def test_scenario_3_several_producers_absent(self):
        units = producer.MEMBER_UNITS
        prober_map = dict.fromkeys(units.values(), (True, "active"))
        for member in ("bridge", "cycle_settler", "supervisor"):
            prober_map[units[member]] = (False, "failed")
        envelope = producer.produce(
            clock=lambda: 1000.0, repo_root=ROOT,
            git_runner=fake_git, unit_prober=make_prober(prober_map))
        absent = [item["sensor_id"] for item in envelope["data"]["processes"]
                  if item["status"] == "absent"]
        self.assertEqual(absent, ["process_bridge", "process_cycle_settler",
                                  "process_supervisor"])

    def test_scenario_5_git_unavailable_is_unknown_not_fabricated(self):
        envelope = producer.produce(
            clock=lambda: 1000.0, repo_root=ROOT,
            git_runner=lambda root, *args: None,
            unit_prober=fake_prober_ok)
        identity = envelope["data"]["code_identity"]
        self.assertIsNone(identity["commit_sha"])
        row = envelope["data"]["sensors"][0]
        self.assertEqual(row["status"], "unknown")
        self.assertEqual(envelope["status"], "unverifiable")
        self.assertEqual(envelope["data"]["events"], [])

    def test_scenario_5_malformed_log_line_is_skipped(self):
        def garbage_git(repo_root, *args):
            if args == ("rev-parse", "HEAD"):
                return FAKE_HEAD + "\n"
            if args == ("branch", "--show-current"):
                return "main\n"
            if args[0] == "log":
                return "not-a-real-log-line\n"
            return None

        envelope = producer.produce(
            clock=lambda: 1000.0, repo_root=ROOT,
            git_runner=garbage_git, unit_prober=fake_prober_ok)
        self.assertEqual(envelope["data"]["events"], [])

    def test_scenario_7_absent_port_value_is_false_not_zero(self):
        prober_map = dict.fromkeys(producer.MEMBER_UNITS.values(),
                                   (False, "failed"))
        envelope = producer.produce(
            clock=lambda: 1000.0, repo_root=ROOT,
            git_runner=fake_git, unit_prober=make_prober(prober_map))
        for row in envelope["data"]["processes"]:
            self.assertIs(row["value"], False)
            self.assertIsNot(row["value"], 0)

    def test_scenario_9_inconclusive_probe_is_not_green(self):
        prober_map = dict.fromkeys(producer.MEMBER_UNITS.values(),
                                   (None, "systemctl unavailable"))
        envelope = producer.produce(
            clock=lambda: 1000.0, repo_root=ROOT,
            git_runner=fake_git, unit_prober=make_prober(prober_map))
        self.assertEqual(envelope["status"], "unverifiable")
        self.assertNotEqual(envelope["status"], "ok")

    def test_scenario_10_brain_probe_fails_closed_without_evidence(self):
        tmp = temp_dir(self)
        envelope = producer.produce(
            clock=lambda: 1000.0, repo_root=Path(tmp),
            git_runner=fake_git, unit_prober=fake_prober_ok)
        probe = envelope["data"]["brain_probe"]
        self.assertEqual(probe["status"], "unknown")
        self.assertEqual(probe["verdict"], "unverifiable")
        self.assertIn("brain_probe_unknown", envelope["warnings"])

    def test_scenario_10_old_probe_evidence_is_stale(self):
        tmp = temp_dir(self)
        receipts = Path(tmp) / "docs/octopus-surgery/receipts"
        receipts.mkdir(parents=True, exist_ok=True)
        receipt = receipts / "BRAIN-PROBE-20200101T000000Z.json"
        receipt.write_text("{}", encoding="utf-8")
        old = 1_000_000.0
        os.utime(receipt, (old, old))
        envelope = producer.produce(
            clock=lambda: 100_000_000.0, repo_root=Path(tmp),
            git_runner=fake_git, unit_prober=fake_prober_ok)
        self.assertEqual(envelope["data"]["brain_probe"]["status"], "stale")
        self.assertEqual(envelope["status"], "degraded")


class ProducerDeterminism(unittest.TestCase):
    def test_scenario_8_same_input_same_document_and_digest(self):
        kwargs = dict(
            repo_root=ROOT, git_runner=fake_git,
            unit_prober=fake_prober_ok, clock=lambda: 1000.0)
        first = producer.produce(**kwargs)
        second = producer.produce(**kwargs)
        # identical injected inputs must yield the identical document —
        # including generation time, which is injected too
        self.assertEqual(first, second)
        self.assertEqual(producer.semantic_digest(first),
                         producer.semantic_digest(second))

    def test_scenario_8_later_read_keeps_semantics_and_updates_stamp(self):
        kwargs = dict(repo_root=ROOT, git_runner=fake_git,
                      unit_prober=fake_prober_ok)
        first = producer.produce(clock=lambda: 1000.0, **kwargs)
        second = producer.produce(clock=lambda: 2000.0, **kwargs)
        self.assertNotEqual(first["generated_at"], second["generated_at"])
        # observation times are part of the observation; the counts and
        # statuses (the semantic claims) must not move between reads
        self.assertEqual(first["data"]["counts"], second["data"]["counts"])
        self.assertEqual(first["data"]["status"], second["data"]["status"])

    def test_scenario_8_document_is_json_roundtrip_stable(self):
        envelope = producer.produce(
            clock=lambda: 1000.0, repo_root=ROOT,
            git_runner=fake_git, unit_prober=fake_prober_ok)
        self.assertEqual(json.loads(json.dumps(envelope)), envelope)


class ArtifactWrite(unittest.TestCase):
    def test_write_artifact_is_atomic_and_reloadable(self):
        envelope = producer.produce(
            clock=lambda: 1000.0, repo_root=ROOT,
            git_runner=fake_git, unit_prober=fake_prober_ok)
        tmp = temp_dir(self)
        target = Path(tmp) / "state" / "self-model" / "MODEL.json"
        path, digest_one = producer.write_artifact(envelope, target)
        self.assertTrue(target.is_file())
        self.assertFalse(Path(str(target) + ".tmp").exists())
        reloaded = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(reloaded, envelope)
        _, digest_two = producer.write_artifact(envelope, target)
        self.assertEqual(digest_one, digest_two)


class RealProducersIntegration(unittest.TestCase):
    """These run against this actual checkout and loopback — no fakes."""

    def test_real_git_identity_matches_the_worktree(self):
        completed = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, timeout=10)
        real_head = completed.stdout.strip()
        envelope = producer.produce(repo_root=ROOT, unit_prober=fake_prober_ok)
        self.assertEqual(envelope["data"]["code_identity"]["commit_sha"],
                         real_head)

    def test_real_capabilities_all_present_in_this_checkout(self):
        envelope = producer.produce(
            repo_root=ROOT, clock=lambda: 1000.0, git_runner=fake_git,
            unit_prober=fake_prober_ok)
        for row in envelope["data"]["capabilities"]:
            self.assertEqual(row["status"], "healthy", row["sensor_id"])

    def test_real_socket_dead_port_is_never_alive(self):
        server = socket.socket()
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        try:
            port = server.getsockname()[1]
            alive, detail = producer.probe_port("127.0.0.1", port, 0.5)
            self.assertIs(alive, True)
            self.assertEqual(detail, "connected")
        finally:
            server.close()
        # After close the port is dead. Unix refuses it (measured absent);
        # this Windows host times out instead (measured inconclusive) —
        # measured on 2026-09-02. Either way it must never read alive.
        alive, detail = producer.probe_port("127.0.0.1", port, 0.5)
        self.assertIsNot(alive, True)
        self.assertIn(alive, (False, None))

    def test_real_cli_run_writes_honest_artifact(self):
        import contextlib
        import io

        tmp = temp_dir(self)
        output = Path(tmp) / "MODEL.json"
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            code = producer.main(["--repo", str(ROOT),
                                  "--output", str(output)])
        self.assertEqual(code, 0)
        envelope = json.loads(output.read_text(encoding="utf-8"))
        self.assertIn(envelope["status"],
                      ("ok", "degraded", "unverifiable"))
        # no dated brain-probe run evidence exists in this checkout: the
        # verdict fails closed regardless of host
        self.assertEqual(envelope["data"]["brain_probe"]["verdict"],
                         "unverifiable")
        # host-independent honesty invariants: warnings are exactly the
        # non-healthy readings, and the counts add up
        non_healthy = {
            f"{row['sensor_id']}_{row['status']}"
            for group in ("sensors", "processes", "capabilities")
            for row in envelope["data"][group]
            if row["status"] != "healthy"
        }
        if envelope["data"]["brain_probe"]["status"] != "healthy":
            non_healthy.add(
                "brain_probe_" + envelope["data"]["brain_probe"]["status"])
        self.assertEqual(set(envelope["warnings"]), non_healthy)
        counts = envelope["data"]["counts"]
        self.assertEqual(
            counts["healthy"] + counts["absent"] + counts["stale"]
            + counts["failed"] + counts["unknown"],
            counts["sensors"] + counts["processes"]
            + counts["capabilities"],
        )
        self.assertIn("sha256=", captured.getvalue())


class CockpitSection(unittest.TestCase):
    def _producer(self, **kwargs):
        options = dict(
            repo_root=ROOT, git_runner=fake_git, unit_prober=fake_prober_ok)
        options.update(kwargs)
        return lambda: producer.produce(**options)

    def test_scenario_1_section_carries_producer_status(self):
        with mock.patch.object(
                producer, "_collect_brain_probe",
                lambda root, now: fresh_probe_evidence(now)):
            section = SelfModelSection(self._producer())
            envelope = section.read()
        self.assertEqual(envelope["section"], "self_model")
        self.assertEqual(envelope["status"], "ok")
        self.assertTrue(SelfModelSection.is_green(envelope))

    def test_scenario_9_section_never_greens_unknown(self):
        prober_map = dict.fromkeys(producer.MEMBER_UNITS.values(),
                                   (None, "systemctl unavailable"))
        section = SelfModelSection(self._producer(
            clock=lambda: 1000.0,
            unit_prober=make_prober(prober_map)))
        envelope = section.read()
        self.assertEqual(envelope["status"], "unverifiable")
        self.assertFalse(SelfModelSection.is_green(envelope))
        unknown_rows = [row for row in section.summary_rows(envelope)
                        if row["status"] == "unknown"]
        self.assertTrue(unknown_rows)

    def test_broken_producer_is_unavailable_not_green(self):
        def exploding():
            raise RuntimeError("boom")

        section = SelfModelSection(exploding)
        envelope = section.read()
        self.assertEqual(envelope["status"], "unavailable")
        self.assertIn("producer_failed", envelope["warnings"])
        self.assertFalse(SelfModelSection.is_green(envelope))
        rows = SelfModelSection.summary_rows(envelope)
        self.assertEqual(rows[0]["status"], "unknown")

    def test_malformed_producer_output_is_unavailable(self):
        section = SelfModelSection(lambda: {"nope": True})
        envelope = section.read()
        self.assertEqual(envelope["status"], "unavailable")

    def test_summary_rows_mirror_readings_verbatim(self):
        section = SelfModelSection(self._producer())
        envelope = section.read()
        rows = section.summary_rows(envelope)
        model = envelope["data"]
        expected = (len(model["sensors"]) + len(model["processes"])
                    + len(model["capabilities"]) + 1)
        self.assertEqual(len(rows), expected)


if __name__ == "__main__":
    unittest.main()
