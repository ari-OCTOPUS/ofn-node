"""Negative API-contract probes; never observations or runtime events.

Use the existing deterministic self-model test input as the valid control.
No data collection, artifact writer, clock, network or operational state.
"""
import unittest

from ofn.kernel import self_model as model
from tests import test_self_model as existing_tests


class InputTrust(unittest.TestCase):
    def test_invalid_freshness_window_is_unknown(self):
        for window in (None, True, False, "300", [], {}, float("nan"),
                       float("inf"), float("-inf"), -1, 10 ** 400):
            with self.subTest(window_type=type(window).__name__):
                self.assertEqual(model.classify_freshness(990, 1000, window),
                                 (model.UNKNOWN, None))

    def test_unrepresentable_epochs_are_unknown(self):
        for observed, now in ((10 ** 400, 1000), (990, 10 ** 400),
                              (-1e308, 1e308)):
            with self.subTest(observed_type=type(observed).__name__):
                self.assertEqual(model.classify_freshness(observed, now, 300),
                                 (model.UNKNOWN, None))

    def test_process_requires_actual_boolean(self):
        for value in (0, 1, "false", "active", [], {}, None):
            with self.subTest(value=value):
                reading = model.process_reading("p", "contract", value,
                                                1000, "contract")
                self.assertEqual(reading.status, model.UNKNOWN)
                self.assertIsNone(reading.value)

    def test_capability_requires_actual_boolean(self):
        for value in (0, 1, "false", "present", [], {}, None):
            with self.subTest(value=value):
                reading = model.capability_reading("c", "contract", value,
                                                   "contract")
                self.assertEqual(reading.status, model.UNKNOWN)
                self.assertIsNone(reading.value)

    def test_valid_measured_booleans_are_preserved(self):
        for value, status in ((True, model.HEALTHY), (False, model.ABSENT)):
            process = model.process_reading("p", "contract", value,
                                            1000, "contract")
            capability = model.capability_reading("c", "contract", value,
                                                  "contract")
            for reading in (process, capability):
                self.assertEqual(reading.status, status)
                self.assertIs(reading.value, value)

    def test_missing_brain_verdict_cannot_be_omitted(self):
        inputs = existing_tests.Scenario8Determinism()._inputs()
        inputs["capabilities"] = inputs["capabilities"][:1]
        self.assertEqual(model.build_model(**inputs)["status"], "ok")
        inputs["brain_probe"] = {}
        self.assertEqual(model.build_model(**inputs)["status"], "unverifiable")

    def test_invalid_brain_verdict_cannot_be_omitted(self):
        for status in (None, True, 1, [], {}, "invalid"):
            with self.subTest(status=status):
                inputs = existing_tests.Scenario8Determinism()._inputs()
                inputs["capabilities"] = inputs["capabilities"][:1]
                self.assertEqual(model.build_model(**inputs)["status"], "ok")
                inputs["brain_probe"] = {"status": status}
                result = model.build_model(**inputs)
                self.assertEqual(result["status"], "unverifiable")
                self.assertEqual(result["brain_probe"], {"status": status})

    def test_valid_zero_and_age_boundary_are_preserved(self):
        self.assertEqual(model.classify_freshness(0, 0, 0), (model.HEALTHY, 0))
        self.assertEqual(model.classify_freshness(700, 1000, 300),
                         (model.HEALTHY, 300))
        self.assertEqual(model.classify_freshness(699, 1000, 300),
                         (model.STALE, 301))

    def test_existing_future_tolerance_is_unchanged(self):
        self.assertEqual(model.FUTURE_TOLERANCE_SECONDS, 5.0)
        self.assertEqual(model.classify_freshness(1005, 1000, 300),
                         (model.HEALTHY, 0))
        self.assertEqual(model.classify_freshness(1006, 1000, 300),
                         (model.UNKNOWN, None))


if __name__ == "__main__":
    unittest.main()
