import csv
import tempfile
import unittest
from pathlib import Path

from ofn.benchmarks.result_store import (
    RESULT_COLUMNS,
    BenchmarkResult,
    CandidateSummary,
    ResultStore,
    SelectionPolicy,
    redact_mapping,
    select_candidate,
)


def summary(
    candidate_id,
    *,
    baseline=False,
    block_size=16,
    profile="batch",
    **overrides,
):
    values = {
        "candidate_id": candidate_id,
        "block_size": None if baseline else block_size,
        "baseline_auto": baseline,
        "profile": profile,
        "repeat_count": 3,
        "ttft_p95_ms": 100.0,
        "e2e_p95_ms": 200.0,
        "throughput_rps": 10.0,
        "prefix_cache_hit_ratio": 0.50,
        "preemption_total": 10.0,
        "fragmentation_ratio": 0.20,
        "queue_p95_ms": 20.0,
        "gpu_memory_peak_bytes": 1000.0,
        "ttft_p95_ci": (99.0, 101.0),
        "e2e_p95_ci": (198.0, 202.0),
        "throughput_ci": (9.9, 10.1),
        "prefix_cache_hit_ci": (0.49, 0.51),
        "preemption_ci": (9.8, 10.2),
        "fragmentation_ci": (0.19, 0.21),
        "queue_p95_ci": (19.5, 20.5),
        "gpu_memory_ci": (990.0, 1010.0),
        "request_count": 100,
    }
    values.update(overrides)
    return CandidateSummary(**values)


def clear_winner(candidate_id="block-16", **overrides):
    values = {
        "ttft_p95_ms": 85.0,
        "e2e_p95_ms": 170.0,
        "throughput_rps": 12.0,
        "prefix_cache_hit_ratio": 0.65,
        "preemption_total": 5.0,
        "fragmentation_ratio": 0.12,
        "queue_p95_ms": 15.0,
        "gpu_memory_peak_bytes": 850.0,
        "ttft_p95_ci": (84.0, 86.0),
        "e2e_p95_ci": (168.0, 172.0),
        "throughput_ci": (11.8, 12.2),
        "prefix_cache_hit_ci": (0.64, 0.66),
        "preemption_ci": (4.8, 5.2),
        "fragmentation_ci": (0.11, 0.13),
        "queue_p95_ci": (14.5, 15.5),
        "gpu_memory_ci": (840.0, 860.0),
    }
    values.update(overrides)
    return summary(candidate_id, **values)


class VllmResultStoreTests(unittest.TestCase):
    def test_header_only_store_is_valid_when_no_gpu_results_exist(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "results.csv"
            store = ResultStore(path)
            store.ensure_header()
            self.assertEqual(store.row_count(), 0)
            with path.open("r", encoding="utf-8", newline="") as handle:
                self.assertEqual(tuple(next(csv.reader(handle))), RESULT_COLUMNS)

    def test_store_accepts_only_fixed_redacted_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "results.csv"
            store = ResultStore(path)
            store.append(
                BenchmarkResult(
                    run_id="run-001",
                    candidate_id="baseline-auto",
                    workload_id="W1",
                    profile="interactive",
                    cache_phase="cold",
                    repetition=1,
                    baseline_auto=True,
                    request_count=1,
                    success_count=1,
                    metrics_available=True,
                )
            )
            self.assertEqual(store.row_count(), 1)
        with self.assertRaises(ValueError):
            BenchmarkResult(
                run_id="run contains raw prompt words",
                candidate_id="baseline-auto",
                workload_id="W1",
                profile="interactive",
                cache_phase="cold",
                repetition=1,
            )

    def test_oom_and_error_candidates_are_never_selected(self):
        baseline = summary("baseline-auto", baseline=True)
        unsafe = clear_winner("unsafe", oom_count=1, error_count=1)
        decision = select_candidate(
            [baseline, unsafe],
            baseline_candidate_id="baseline-auto",
        )
        self.assertEqual(decision.final_status, "KEEP_PLATFORM_DEFAULT")
        self.assertEqual(decision.selected_candidate_id, "baseline-auto")
        rejected = dict(decision.rejected)
        self.assertIn("oom", rejected["unsafe"])
        self.assertIn("errors", rejected["unsafe"])

    def test_less_than_five_percent_preserves_platform_default(self):
        baseline = summary("baseline-auto", baseline=True)
        candidate = summary(
            "block-16",
            ttft_p95_ms=96.0,
            e2e_p95_ms=192.0,
            throughput_rps=10.4,
            prefix_cache_hit_ratio=0.52,
            preemption_total=9.6,
            fragmentation_ratio=0.192,
            queue_p95_ms=19.2,
            gpu_memory_peak_bytes=960.0,
        )
        decision = select_candidate(
            [baseline, candidate],
            baseline_candidate_id="baseline-auto",
        )
        self.assertEqual(decision.final_status, "KEEP_PLATFORM_DEFAULT")
        self.assertEqual(decision.selected_candidate_id, "baseline-auto")

    def test_theoretical_fragmentation_alone_cannot_choose_winner(self):
        baseline = summary("baseline-auto", baseline=True)
        candidate = summary(
            "block-16",
            fragmentation_ratio=0.10,
            fragmentation_ci=(0.09, 0.11),
        )
        decision = select_candidate(
            [baseline, candidate],
            baseline_candidate_id="baseline-auto",
        )
        self.assertEqual(decision.final_status, "KEEP_PLATFORM_DEFAULT")
        self.assertEqual(decision.selected_candidate_id, "baseline-auto")
        self.assertIn("theoretical fragmentation", decision.reason)

    def test_diagnostic_size_one_cannot_be_selected_for_production(self):
        baseline = summary("baseline-auto", baseline=True)
        diagnostic = clear_winner(
            "diagnostic-block-1",
            block_size=1,
            diagnostic_only=True,
        )
        decision = select_candidate(
            [baseline, diagnostic],
            baseline_candidate_id="baseline-auto",
        )
        self.assertEqual(decision.final_status, "KEEP_PLATFORM_DEFAULT")
        self.assertIn(
            "diagnostic_only",
            dict(decision.rejected)["diagnostic-block-1"],
        )

    def test_interactive_candidate_over_service_limit_is_rejected(self):
        baseline = summary(
            "baseline-auto", baseline=True, profile="interactive"
        )
        candidate = clear_winner(
            profile="interactive",
            ttft_p95_ms=120.0,
            ttft_p95_ci=(119.0, 121.0),
        )
        decision = select_candidate(
            [baseline, candidate],
            baseline_candidate_id="baseline-auto",
            policy=SelectionPolicy(service_ttft_p95_limit_ms=110.0),
        )
        self.assertNotEqual(decision.selected_candidate_id, "block-16")
        self.assertEqual(decision.selected_candidate_id, "baseline-auto")
        self.assertIn(
            "service_ttft_limit_violated",
            dict(decision.rejected)["block-16"],
        )

    def test_incomplete_candidate_data_returns_no_clear_winner(self):
        baseline = summary("baseline-auto", baseline=True)
        candidate = clear_winner(throughput_rps=None)
        decision = select_candidate(
            [baseline, candidate],
            baseline_candidate_id="baseline-auto",
        )
        self.assertEqual(
            decision.final_status, "BLOCKED_NO_CLEAR_WINNER"
        )
        self.assertIsNone(decision.selected_candidate_id)

    def test_overlapping_confidence_interval_returns_no_clear_winner(self):
        baseline = summary("baseline-auto", baseline=True)
        candidate = clear_winner(
            throughput_ci=(10.0, 12.2)
        )
        decision = select_candidate(
            [baseline, candidate],
            baseline_candidate_id="baseline-auto",
        )
        self.assertEqual(
            decision.final_status, "BLOCKED_NO_CLEAR_WINNER"
        )
        self.assertIn("overlap", decision.reason)

    def test_complete_nonoverlapping_pareto_winner_needs_owner_canary(self):
        baseline = summary("baseline-auto", baseline=True)
        candidate = clear_winner()
        decision = select_candidate(
            [baseline, candidate],
            baseline_candidate_id="baseline-auto",
        )
        self.assertEqual(
            decision.final_status, "READY_FOR_OWNER_APPROVED_CANARY"
        )
        self.assertEqual(decision.selected_candidate_id, "block-16")
        self.assertEqual(decision.selected_block_size, 16)

    def test_arbitrary_diagnostics_are_redacted(self):
        safe = redact_mapping(
            {
                "raw_prompt": "private words",
                "nested": {
                    "api_key": "sk-private-value",
                    "endpoint": "https://prod.example.invalid",
                },
                "events": ["https://private.example.invalid"],
                "status": "Bearer private-value",
            }
        )
        serialized = repr(safe)
        self.assertNotIn("private words", serialized)
        self.assertNotIn("sk-private-value", serialized)
        self.assertNotIn("prod.example", serialized)
        self.assertNotIn("private.example", serialized)
        self.assertNotIn("Bearer private-value", serialized)


if __name__ == "__main__":
    unittest.main()
