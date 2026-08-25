import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts import benchmark_vllm_block_size


COMPLETE_METRICS = """
vllm:request_success_total 1
vllm:prompt_tokens_total 1
vllm:generation_tokens_total 1
vllm:time_to_first_token_seconds 0.1
vllm:time_per_output_token_seconds 0.02
vllm:inter_token_latency_seconds 0.02
vllm:e2e_request_latency_seconds 0.2
vllm:request_queue_time_seconds 0.01
vllm:request_prefill_time_seconds 0.08
vllm:request_decode_time_seconds 0.12
vllm:kv_cache_usage_perc 0.5
vllm:num_preemptions_total 0
vllm:num_requests_waiting 0
vllm:prefix_cache_queries_total 1
vllm:prefix_cache_hits_total 1
"""


def invoke(arguments):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        status = benchmark_vllm_block_size.main(arguments)
    return status, stdout.getvalue(), stderr.getvalue()


class VllmBlockSizeCliTests(unittest.TestCase):
    def test_default_invocation_is_offline_plan_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "artifacts"
            status, stdout, _ = invoke(["--output-dir", str(output)])
            self.assertEqual(status, 0)
            self.assertIn("canary_launched=false", stdout)
            preflight = json.loads(
                (output / "preflight.json").read_text(encoding="utf-8")
            )
            self.assertTrue(preflight["offline_preflight"])
            self.assertFalse(preflight["network_calls_performed"])
            self.assertFalse(preflight["service_actions_performed"])
            self.assertEqual(preflight["status"], "BLOCKED_NO_GPU")
            results_lines = (
                (output / "results.csv")
                .read_text(encoding="utf-8")
                .splitlines()
            )
            self.assertEqual(len(results_lines), 1)
            recommendation = (output / "recommendation.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("final_status: `BLOCKED_NO_GPU`", recommendation)
            self.assertIn("no GPU measurements", recommendation)

    def test_canary_validation_has_hard_owner_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            status, _, stderr = invoke(
                [
                    "--mode",
                    "validate-canary",
                    "--output-dir",
                    temporary,
                ]
            )
        self.assertEqual(status, 2)
        self.assertIn("BLOCKED_SAFETY", stderr)

    def test_metrics_and_owner_gate_still_reject_production_origin(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metrics = root / "metrics.txt"
            metrics.write_text(COMPLETE_METRICS, encoding="utf-8")
            status, _, _ = invoke(
                [
                    "--mode",
                    "validate-canary",
                    "--output-dir",
                    str(root / "output"),
                    "--owner-approved",
                    "--owner-approval-reference",
                    "approval-001",
                    "--owner-thermal-limit-c",
                    "70",
                    "--metrics-file",
                    str(metrics),
                    "--vllm-version",
                    "0.11.0",
                    "--canary-endpoint",
                    "http://127.0.0.1:18080",
                    "--production-endpoint",
                    "http://127.0.0.1:18080",
                ]
            )
        self.assertEqual(status, 2)

    def test_wave0_refuses_execute_even_after_all_validation_gates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metrics = root / "metrics.txt"
            metrics.write_text(COMPLETE_METRICS, encoding="utf-8")
            status, _, stderr = invoke(
                [
                    "--mode",
                    "validate-canary",
                    "--output-dir",
                    str(root / "output"),
                    "--owner-approved",
                    "--owner-approval-reference",
                    "approval-001",
                    "--owner-thermal-limit-c",
                    "70",
                    "--metrics-file",
                    str(metrics),
                    "--vllm-version",
                    "0.11.0",
                    "--backend",
                    "CUDA",
                    "--supported-block-sizes",
                    "8,16,32",
                    "--capability-source",
                    "same-version-help",
                    "--canary-endpoint",
                    "http://127.0.0.1:18080",
                    "--execute-canary",
                ]
            )
        self.assertEqual(status, 2)
        self.assertIn("BLOCKED_SAFETY", stderr)


if __name__ == "__main__":
    unittest.main()
