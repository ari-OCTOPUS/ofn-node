import unittest

from ofn.adapters.vllm_metrics import (
    REDACTED,
    PrometheusParseError,
    discover_vllm_metrics,
    parse_prometheus_text,
)


COMPLETE_CURRENT_METRICS = """
# TYPE vllm:request_success_total counter
vllm:request_success_total{status="ok"} 12
# TYPE vllm:prompt_tokens_total counter
vllm:prompt_tokens_total 1200
# TYPE vllm:generation_tokens_total counter
vllm:generation_tokens_total 300
# TYPE vllm:time_to_first_token_seconds histogram
vllm:time_to_first_token_seconds_bucket{le="0.1"} 4
vllm:time_to_first_token_seconds_bucket{le="+Inf"} 12
vllm:time_to_first_token_seconds_count 12
vllm:time_per_output_token_seconds 0.02
vllm:inter_token_latency_seconds 0.02
# TYPE vllm:e2e_request_latency_seconds histogram
vllm:e2e_request_latency_seconds_bucket{le="1.0"} 12
vllm:e2e_request_latency_seconds_count 12
# TYPE vllm:request_queue_time_seconds histogram
vllm:request_queue_time_seconds_bucket{le="0.1"} 12
vllm:request_queue_time_seconds_count 12
vllm:request_prefill_time_seconds 0.08
vllm:request_decode_time_seconds 0.12
vllm:kv_cache_usage_perc 0.5
vllm:num_preemptions_total 0
vllm:num_requests_waiting 0
vllm:prefix_cache_queries_total 10
vllm:prefix_cache_hits_total 8
"""


class VllmMetricsTests(unittest.TestCase):
    def test_parses_metric_families_and_samples(self):
        parsed = parse_prometheus_text(COMPLETE_CURRENT_METRICS)
        families = {item.name: item for item in parsed.families}
        self.assertEqual(
            families["vllm:time_to_first_token_seconds"].metric_type,
            "histogram",
        )
        self.assertEqual(
            len(families["vllm:time_to_first_token_seconds"].samples),
            3,
        )
        self.assertEqual(parsed.issues, ())

    def test_current_version_mapping_is_complete(self):
        discovery = discover_vllm_metrics(
            COMPLETE_CURRENT_METRICS,
            vllm_version="0.11.2",
        )
        self.assertEqual(discovery.profile, "vllm_0_11_plus")
        self.assertTrue(discovery.required_metrics_available)
        self.assertEqual(discovery.missing_required, ())
        self.assertEqual(
            discovery.mapping_dict()["prefix_cache_hits"],
            "vllm:prefix_cache_hits_total",
        )

    def test_legacy_version_uses_legacy_alias_profile(self):
        legacy = COMPLETE_CURRENT_METRICS.replace(
            "vllm:kv_cache_usage_perc", "vllm:gpu_cache_usage_perc"
        ).replace(
            "vllm:prefix_cache_queries_total", "vllm:prefix_cache_queries"
        ).replace(
            "vllm:prefix_cache_hits_total", "vllm:prefix_cache_hits"
        )
        discovery = discover_vllm_metrics(
            legacy,
            vllm_version="0.10.1",
        )
        self.assertEqual(discovery.profile, "vllm_pre_0_11")
        self.assertTrue(discovery.required_metrics_available)

    def test_unknown_version_discovers_but_does_not_claim_one_profile(self):
        discovery = discover_vllm_metrics(
            COMPLETE_CURRENT_METRICS,
            vllm_version=None,
        )
        self.assertEqual(
            discovery.profile, "unknown_version_discovery_only"
        )
        self.assertTrue(discovery.warnings)
        self.assertTrue(discovery.required_metrics_available)

    def test_missing_required_metrics_are_exposed(self):
        discovery = discover_vllm_metrics(
            "vllm:num_requests_waiting 0\n",
            vllm_version="0.11.0",
        )
        self.assertFalse(discovery.required_metrics_available)
        self.assertIn("ttft_seconds", discovery.missing_required)
        self.assertIn("prefix_cache_hits", discovery.missing_required)

    def test_non_finite_only_metric_is_not_considered_available(self):
        discovery = discover_vllm_metrics(
            "vllm:num_requests_waiting NaN\n",
            vllm_version="0.11.0",
        )
        self.assertIn("requests_waiting", discovery.missing_required)

    def test_sensitive_and_unapproved_labels_are_redacted(self):
        parsed = parse_prometheus_text(
            'vllm:request_success_total{'
            'status="ok",tenant_id="private-tenant",'
            'prompt="raw private words",api_key="sk-private-value",'
            'model_name="internal/model",'
            'reason="https://private.example.invalid"} 1\n'
        )
        labels = parsed.samples[0].label_dict()
        self.assertEqual(labels["status"], "ok")
        self.assertEqual(labels["tenant_id"], REDACTED)
        self.assertEqual(labels["prompt"], REDACTED)
        self.assertEqual(labels["api_key"], REDACTED)
        self.assertEqual(labels["model_name"], REDACTED)
        self.assertEqual(labels["reason"], REDACTED)
        self.assertNotIn("private-tenant", repr(parsed))
        self.assertNotIn("raw private words", repr(parsed))
        self.assertEqual(parsed.redacted_label_count, 5)

    def test_malformed_lines_fail_strict_and_are_reported_non_strict(self):
        with self.assertRaises(PrometheusParseError):
            parse_prometheus_text("not valid metrics\n")
        with self.assertRaises(PrometheusParseError):
            parse_prometheus_text('metric{status="ok",} 1\n')
        parsed = parse_prometheus_text(
            "not valid metrics\nvllm:num_requests_waiting 0\n",
            strict=False,
        )
        self.assertEqual(len(parsed.issues), 1)
        self.assertEqual(len(parsed.samples), 1)


if __name__ == "__main__":
    unittest.main()
