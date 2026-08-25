import tempfile
import unittest
from pathlib import Path

from ofn.benchmarks.vllm_block_size import (
    BlockSizePlan,
    CanaryLaunchAuthorization,
    PlanningError,
    SafetyObservation,
    SafetyValidationError,
    backend_plan,
    build_candidate_run_plans,
    collect_local_preflight,
    cuda_plan,
    evaluate_abort_conditions,
    randomized_run_values,
    validate_canary_endpoint,
    validate_canary_launch_authorization,
    validate_only_block_size_varies,
)


class VllmBlockSizePlanningTests(unittest.TestCase):
    def test_preflight_collects_only_bounded_availability_facts(self):
        preflight = collect_local_preflight(
            observed_at_utc="2026-08-25T00:00:00Z"
        )
        self.assertEqual(
            preflight["observed_at_utc"], "2026-08-25T00:00:00Z"
        )
        self.assertTrue(preflight["offline_preflight"])
        self.assertFalse(preflight["network_calls_performed"])
        self.assertFalse(preflight["process_environment_collected"])
        self.assertFalse(preflight["process_command_lines_collected"])
        self.assertIsNone(preflight["resolved_cache_config"])
        self.assertIsNone(preflight["owner_thermal_limit_c"])
        for available in preflight["command_availability"].values():
            self.assertIsInstance(available, bool)

    def test_cuda_plan_filters_unpreferred_and_large_sizes(self):
        plan = cuda_plan({1, 8, 16, 32, 64, 128, 256})
        self.assertTrue(plan.baseline_auto)
        self.assertEqual(plan.represented_block_sizes, (None, 8, 16, 32))
        self.assertEqual(plan.candidates, (8, 16, 32))
        self.assertEqual(plan.diagnostic_candidates, ())
        self.assertTrue(all(value <= 32 for value in plan.candidates))

    def test_size_one_requires_explicit_diagnostic_opt_in(self):
        default = cuda_plan({1, 8})
        diagnostic = cuda_plan(
            {1, 8}, enable_diagnostic_size_one=True
        )
        self.assertNotIn(1, default.candidates)
        self.assertEqual(default.diagnostic_candidates, ())
        self.assertNotIn(1, diagnostic.candidates)
        self.assertEqual(diagnostic.diagnostic_candidates, (1,))

    def test_cuda_requires_a_supported_production_candidate(self):
        with self.assertRaises(PlanningError):
            cuda_plan({1, 64})

    def test_non_cuda_never_guesses_capabilities(self):
        for supported, version, source in (
            (None, "0.11.0", "same-version-help"),
            ({16}, None, "same-version-help"),
            ({16}, "0.11.0", None),
        ):
            with self.subTest(
                supported=supported, version=version, source=source
            ):
                with self.assertRaises(PlanningError):
                    backend_plan(
                        backend="ROCm",
                        supported=supported,
                        vllm_version=version,
                        capability_source=source,
                    )

    def test_non_cuda_preserves_supplied_versioned_values(self):
        plan = backend_plan(
            backend="ROCm",
            supported={1, 16, 64},
            vllm_version="0.11.0",
            capability_source="same-version-help",
            enable_diagnostic_size_one=True,
        )
        self.assertEqual(plan.candidates, (16, 64))
        self.assertEqual(plan.diagnostic_candidates, (1,))

    def test_candidate_order_is_randomized_deterministically(self):
        plan = BlockSizePlan(True, (8, 16, 32), backend="CUDA")
        first = randomized_run_values(plan, seed=7)
        second = randomized_run_values(plan, seed=7)
        self.assertEqual(first, second)
        self.assertCountEqual(
            first, ((None, False), (8, False), (16, False), (32, False))
        )

    def test_run_plans_use_fresh_ports_paths_and_immutable_block_size(self):
        plan = BlockSizePlan(True, (8, 16), backend="CUDA")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runs = build_candidate_run_plans(
                plan,
                baseline_server_configuration={
                    "model_revision": "public-revision",
                    "dtype": "bfloat16",
                },
                seed=11,
                canary_host="127.0.0.1",
                first_canary_port=18080,
                cache_root=root / "cache",
                data_root=root / "data",
            )
        self.assertEqual(len(runs), 3)
        self.assertEqual(len({item.canary_port for item in runs}), 3)
        self.assertEqual(len({item.cache_path for item in runs}), 3)
        self.assertEqual(len({item.data_path for item in runs}), 3)
        self.assertTrue(all(item.fresh_process_required for item in runs))
        self.assertTrue(
            all(not item.dynamic_block_size_mutation_allowed for item in runs)
        )
        self.assertEqual(sum(item.baseline_auto for item in runs), 1)

    def test_only_block_size_may_vary(self):
        baseline = {"block_size": None, "dtype": "bfloat16", "seed": 7}
        validate_only_block_size_varies(
            baseline, {"block_size": 16, "dtype": "bfloat16", "seed": 7}
        )
        with self.assertRaises(SafetyValidationError):
            validate_only_block_size_varies(
                baseline, {"block_size": 16, "dtype": "float16", "seed": 7}
            )

    def test_production_endpoint_is_rejected(self):
        with self.assertRaises(SafetyValidationError):
            validate_canary_endpoint(
                "http://127.0.0.1:8000",
                ("http://127.0.0.1:8000",),
            )
        with self.assertRaises(SafetyValidationError):
            validate_canary_endpoint(
                "https://prod.example.invalid",
                (),
            )
        validate_canary_endpoint(
            "http://127.0.0.1:18080",
            ("http://127.0.0.1:8000",),
        )

    def test_launch_requires_owner_thermal_and_metrics_gates(self):
        base = dict(
            owner_approval_reference="approval-001",
            owner_thermal_limit_c=75.0,
            metrics_available=True,
            candidate_endpoint="http://127.0.0.1:18080",
        )
        with self.assertRaises(SafetyValidationError):
            validate_canary_launch_authorization(
                CanaryLaunchAuthorization(owner_approved=False, **base)
            )
        with self.assertRaises(SafetyValidationError):
            validate_canary_launch_authorization(
                CanaryLaunchAuthorization(
                    owner_approved=True,
                    **{**base, "owner_thermal_limit_c": None},
                )
            )
        with self.assertRaises(SafetyValidationError):
            validate_canary_launch_authorization(
                CanaryLaunchAuthorization(
                    owner_approved=True,
                    **{**base, "metrics_available": False},
                )
            )
        validate_canary_launch_authorization(
            CanaryLaunchAuthorization(owner_approved=True, **base)
        )

    def test_abort_conditions_use_owner_limit(self):
        observation = SafetyObservation(
            request_count=100,
            error_count=2,
            oom_count=1,
            gpu_temperature_peak_c=71.0,
            consecutive_metrics_unavailable=2,
        )
        reasons = evaluate_abort_conditions(
            observation, owner_thermal_limit_c=70.0
        )
        self.assertIn("gpu_oom", reasons)
        self.assertIn("error_rate_above_one_percent", reasons)
        self.assertIn("owner_thermal_limit_exceeded", reasons)
        self.assertIn("metrics_unavailable_two_consecutive_runs", reasons)


if __name__ == "__main__":
    unittest.main()
