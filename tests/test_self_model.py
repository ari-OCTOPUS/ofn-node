"""Kernel-level behaviour of the self-model grammar.

The ten scenarios mandated for Lane LA, exercised against the pure kernel:
classification, absence/zero honesty, determinism, fail-closed probe
verdicts, and status rollup. No I/O here — every timestamp is injected.
"""

from __future__ import annotations

import unittest

from ofn.kernel import self_model
from ofn.kernel.self_model import Reading


def healthy(sensor_id: str, value=1, observed_epoch: float = 1000.0) -> Reading:
    return Reading(sensor_id, "test", self_model.HEALTHY, value,
                   "test:source", observed_epoch)


class Scenario1AllProducersPresent(unittest.TestCase):
    def test_scenario_1_all_producers_present_is_ok(self):
        sensors = [
            healthy("code_identity", "sha"),
            self_model.process_reading("process_organism", "tcp",
                                       True, 1000.0, "tcp:127.0.0.1:8771"),
            self_model.capability_reading("capability_self_model", "ast",
                                          True, "ast:ofn/kernel/self_model.py"),
        ]
        probe = self_model.brain_probe_verdict(
            990.0, "fs:receipt.json", 1000.0, 3600)
        model = self_model.build_model(
            code_identity={"commit_sha": "sha", "branch": "main"},
            sensors=[sensors[0]],
            processes=[sensors[1]],
            capabilities=[sensors[2]],
            events=[{"sha": "a", "at": "t", "subject": "s",
                     "source": "git:log"}],
            brain_probe=probe,
        )
        self.assertEqual(model["status"], "ok")
        counts = model["counts"]
        self.assertEqual(counts["sensors"], 1)
        self.assertEqual(counts["processes"], 1)
        self.assertEqual(counts["capabilities"], 1)
        # house rule: the counts must add up
        self.assertEqual(
            counts["healthy"],
            counts["sensors"] + counts["processes"] + counts["capabilities"],
        )


class Scenario2OneProducerAbsent(unittest.TestCase):
    def test_scenario_2_absent_is_explicit_and_measured(self):
        absent = self_model.process_reading(
            "process_center", "tcp", False, 1000.0, "tcp:127.0.0.1:8776",
            "connection refused")
        model = self_model.build_model(
            code_identity={"commit_sha": "sha"},
            sensors=[healthy("code_identity", "sha")],
            processes=[absent],
            capabilities=[],
            events=[],
            brain_probe=self_model.brain_probe_verdict(
                990.0, "fs:receipt.json", 1000.0, 3600),
        )
        row = model["processes"][0]
        self.assertEqual(row["status"], "absent")
        self.assertIs(row["value"], False)
        self.assertEqual(row["detail"], "connection refused")
        # absence is a verified negative: the model is still coherent
        self.assertEqual(model["status"], "ok")
        self.assertEqual(model["counts"]["absent"], 1)


class Scenario3SeveralProducersAbsent(unittest.TestCase):
    def test_scenario_3_every_absence_is_listed(self):
        processes = [
            self_model.process_reading(f"process_{name}", "tcp", False,
                                       1000.0, "tcp:x")
            for name in ("organism", "live", "center")
        ]
        model = self_model.build_model(
            code_identity={"commit_sha": "sha"},
            sensors=[healthy("code_identity", "sha")],
            processes=processes,
            capabilities=[self_model.capability_reading(
                "capability_remote_brain", "ast", False, "ast:x")],
            events=[],
            brain_probe=self_model.brain_probe_verdict(
                990.0, "fs:receipt.json", 1000.0, 3600),
        )
        absent_ids = {
            row["sensor_id"]
            for row in model["processes"] + model["capabilities"]
            if row["status"] == "absent"
        }
        self.assertEqual(
            absent_ids,
            {"process_organism", "process_live", "process_center",
             "capability_remote_brain"},
        )
        self.assertEqual(model["counts"]["absent"], 4)


class Scenario4StaleData(unittest.TestCase):
    def test_scenario_4_old_observation_is_stale_not_healthy(self):
        status, age = self_model.classify_freshness(100.0, 1000.0, 300)
        self.assertEqual(status, self_model.STALE)
        self.assertEqual(age, 900)

    def test_scenario_4_stale_evidence_degrades_the_probe(self):
        verdict = self_model.brain_probe_verdict(
            0.0, "fs:receipt.json", 100_000.0, 3600)
        self.assertEqual(verdict["status"], self_model.STALE)
        self.assertEqual(verdict["verdict"], "probe-evidence-stale")


class Scenario5MalformedPayload(unittest.TestCase):
    def test_scenario_5_undatable_payload_is_unknown_never_healthy(self):
        for garbage in (None, "not-a-number", float("nan"),
                        float("inf"), "1000.0", True, [], {}):
            status, _ = self_model.classify_freshness(
                garbage, 1000.0, 300)  # type: ignore[arg-type]
            self.assertEqual(status, self_model.UNKNOWN, repr(garbage))

    def test_scenario_5_future_dated_payload_fails_closed(self):
        status, _ = self_model.classify_freshness(5000.0, 1000.0, 300)
        self.assertEqual(status, self_model.UNKNOWN)

    def test_scenario_5_invalid_status_cannot_hide_in_rollup(self):
        self.assertEqual(self_model.overall_status(["healthy", "bogus"]),
                         "unverifiable")

    def test_scenario_5_fallback_healthy_without_time_is_unknown(self):
        status, _ = self_model.freshness_with_fallback(
            None, 1000.0, 300, self_model.HEALTHY)
        self.assertEqual(status, self_model.UNKNOWN)


class Scenario6RealZeroValue(unittest.TestCase):
    def test_scenario_6_zero_is_a_measurement_and_survives(self):
        zero = Reading("queue_depth", "test", self_model.HEALTHY, 0,
                       "test:source", 1000.0)
        model = self_model.build_model(
            code_identity={},
            sensors=[healthy("code_identity", "sha"), zero],
            processes=[], capabilities=[], events=[],
            brain_probe=self_model.brain_probe_verdict(
                990.0, "fs:receipt.json", 1000.0, 3600),
        )
        row = next(item for item in model["sensors"]
                   if item["sensor_id"] == "queue_depth")
        self.assertEqual(row["status"], "healthy")
        self.assertIs(row["value"], 0)


class Scenario7AbsentIsNotZero(unittest.TestCase):
    def test_scenario_7_absent_carries_no_numeric_value(self):
        unknown = Reading("queue_depth", "test", self_model.UNKNOWN, None,
                          "test:source", None)
        absent = self_model.capability_reading(
            "capability_x", "ast", False, "ast:x")
        model = self_model.build_model(
            code_identity={}, sensors=[unknown], processes=[],
            capabilities=[absent], events=[],
            brain_probe=self_model.brain_probe_verdict(
                None, None, 1000.0, 3600),
        )
        unknown_row = model["sensors"][0]
        absent_row = model["capabilities"][0]
        self.assertIsNone(unknown_row["value"])
        self.assertIsNot(unknown_row["value"], 0)
        self.assertIs(absent_row["value"], False)
        self.assertIsNot(absent_row["value"], 0)


class Scenario8Determinism(unittest.TestCase):
    def _inputs(self):
        return dict(
            code_identity={"commit_sha": "s" * 40, "branch": "lane/x"},
            sensors=[healthy("code_identity", "s" * 40)],
            processes=[
                self_model.process_reading("process_a", "tcp", True,
                                           1000.0, "tcp:a"),
                self_model.process_reading("process_b", "tcp", False,
                                           1000.0, "tcp:b"),
            ],
            capabilities=[
                self_model.capability_reading("capability_a", "ast", True,
                                              "ast:a"),
                self_model.capability_reading("capability_b", "ast", None,
                                              "ast:b"),
            ],
            events=[{"sha": "x", "at_epoch": 1.0, "at": "t",
                     "subject": "s", "source": "git:log"}],
            brain_probe=self_model.brain_probe_verdict(
                999.0, "fs:r.json", 1000.0, 3600),
        )

    def test_scenario_8_same_input_same_document(self):
        first = self_model.build_model(**self._inputs())
        second = self_model.build_model(**self._inputs())
        self.assertEqual(first, second)

    def test_scenario_8_input_order_does_not_leak(self):
        inputs = self._inputs()
        shuffled = dict(inputs)
        shuffled["processes"] = list(reversed(inputs["processes"]))
        shuffled["capabilities"] = list(reversed(inputs["capabilities"]))
        self.assertEqual(
            self_model.build_model(**shuffled),
            self_model.build_model(**inputs),
        )


class Scenario9UnknownIsNotGreen(unittest.TestCase):
    def test_scenario_9_unknown_sensor_makes_model_unverifiable(self):
        unknown = Reading("process_x", "tcp", self_model.UNKNOWN, None,
                          "tcp:x", None, "probe timeout")
        model = self_model.build_model(
            code_identity={"commit_sha": "sha"},
            sensors=[healthy("code_identity", "sha")],
            processes=[unknown], capabilities=[], events=[],
            brain_probe=self_model.brain_probe_verdict(
                990.0, "fs:receipt.json", 1000.0, 3600),
        )
        self.assertEqual(model["status"], "unverifiable")
        self.assertNotEqual(model["status"], "ok")

    def test_scenario_9_empty_sensor_list_is_not_ok(self):
        self.assertEqual(self_model.overall_status([]), "unverifiable")


class Scenario10ProbeFailsClosed(unittest.TestCase):
    def test_scenario_10_no_evidence_is_never_healthy(self):
        for evidence in (None, (None, "fs:receipt.json")):
            epoch, source = evidence if evidence else (None, None)
            verdict = self_model.brain_probe_verdict(
                epoch, source, 1000.0, 3600)
            self.assertEqual(verdict["status"], self_model.UNKNOWN)
            self.assertEqual(verdict["verdict"], "unverifiable")
            self.assertNotEqual(verdict["status"], self_model.HEALTHY)

    def test_scenario_10_future_evidence_is_untrusted(self):
        verdict = self_model.brain_probe_verdict(
            999_999.0, "fs:receipt.json", 1000.0, 3600)
        self.assertEqual(verdict["status"], self_model.UNKNOWN)
        self.assertEqual(verdict["verdict"], "unverifiable")

    def test_scenario_10_fresh_evidence_is_deterministic(self):
        first = self_model.brain_probe_verdict(
            990.0, "fs:receipt.json", 1000.0, 3600)
        second = self_model.brain_probe_verdict(
            990.0, "fs:receipt.json", 1000.0, 3600)
        self.assertEqual(first, second)
        self.assertEqual(first["status"], self_model.HEALTHY)


class RollupRules(unittest.TestCase):
    def test_severity_order_unknown_beats_degraded(self):
        self.assertEqual(
            self_model.overall_status(
                [self_model.STALE, self_model.UNKNOWN]),
            "unverifiable",
        )

    def test_failed_is_degraded(self):
        self.assertEqual(
            self_model.overall_status([self_model.HEALTHY, self_model.FAILED]),
            "degraded",
        )

    def test_counts_reconcile(self):
        readings = [
            healthy("a"),
            self_model.process_reading("p", "tcp", False, 1.0, "tcp"),
            Reading("u", "t", self_model.UNKNOWN, None, "s", None),
        ]
        counts = self_model.status_counts(readings)
        self.assertEqual(sum(counts.values()), len(readings))


if __name__ == "__main__":
    unittest.main()
