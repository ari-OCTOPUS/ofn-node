import json
import unittest

from ofn.benchmarks.workload_manifest import (
    AnonymizedHistogramBin,
    build_workload_manifest,
    validate_workload_manifest,
)


def phase(manifest, workload_id, cache_phase):
    return next(
        item
        for item in manifest["phase_manifests"]
        if item["workload_id"] == workload_id and item["phase"] == cache_phase
    )


class VllmWorkloadManifestTests(unittest.TestCase):
    def test_manifest_contains_w1_through_w5(self):
        manifest = build_workload_manifest(seed=7)
        self.assertEqual(
            [item["workload_id"] for item in manifest["definitions"]],
            ["W1", "W2", "W3", "W4", "W5"],
        )
        self.assertEqual(len(manifest["phase_manifests"]), 10)

    def test_generation_is_deterministic(self):
        self.assertEqual(
            build_workload_manifest(seed=123),
            build_workload_manifest(seed=123),
        )
        self.assertNotEqual(
            build_workload_manifest(seed=123),
            build_workload_manifest(seed=124),
        )

    def test_cold_and_warm_phases_are_separate_but_shape_paired(self):
        manifest = build_workload_manifest(seed=9)
        for workload_id in ("W1", "W2", "W3", "W4", "W5"):
            cold = phase(manifest, workload_id, "cold")
            warm = phase(manifest, workload_id, "warm")
            self.assertTrue(
                all(item["phase"] == "cold" for item in cold["requests"])
            )
            self.assertTrue(
                all(item["phase"] == "warm" for item in warm["requests"])
            )
            cold_shapes = [
                (
                    item["prompt_tokens"],
                    item["generation_tokens"],
                    item["concurrency"],
                    item["shared_prefix_tokens"],
                    item["synthetic_prefix_pattern"],
                )
                for item in cold["requests"]
            ]
            warm_shapes = [
                (
                    item["prompt_tokens"],
                    item["generation_tokens"],
                    item["concurrency"],
                    item["shared_prefix_tokens"],
                    item["synthetic_prefix_pattern"],
                )
                for item in warm["requests"]
            ]
            self.assertEqual(cold_shapes, warm_shapes)

    def test_workload_ranges_match_specification(self):
        manifest = build_workload_manifest(seed=11)
        for request in phase(manifest, "W1", "cold")["requests"]:
            self.assertIn(request["prompt_tokens"], range(128, 513))
            self.assertIn(request["generation_tokens"], range(32, 129))
            self.assertIn(request["concurrency"], (1, 4, 16))
        for request in phase(manifest, "W2", "cold")["requests"]:
            self.assertIn(request["prompt_tokens"], range(1_024, 8_193))
            self.assertIn(request["generation_tokens"], range(64, 257))
            self.assertIn(request["concurrency"], (1, 8, 32))
        for request in phase(manifest, "W3", "cold")["requests"]:
            query_tail = (
                request["prompt_tokens"] - request["shared_prefix_tokens"]
            )
            self.assertIn(
                request["shared_prefix_tokens"], range(8_192, 32_769)
            )
            self.assertIn(query_tail, range(32, 257))
        for request in phase(manifest, "W5", "cold")["requests"]:
            self.assertIn(request["prompt_tokens"], range(512, 2_049))
            self.assertIn(request["generation_tokens"], range(512, 2_049))

    def test_w4_does_not_guess_a_production_distribution(self):
        manifest = build_workload_manifest()
        definition = manifest["definitions"][3]
        self.assertEqual(
            definition["status"],
            "BLOCKED_MISSING_ANONYMIZED_HISTOGRAM",
        )
        self.assertEqual(phase(manifest, "W4", "cold")["requests"], [])
        self.assertEqual(phase(manifest, "W4", "warm")["requests"], [])

    def test_w4_expands_owner_supplied_anonymized_histogram(self):
        histogram = (
            AnonymizedHistogramBin(
                prompt_tokens=256,
                generation_tokens=64,
                count=2,
                concurrency=4,
                shared_prefix_fraction=0.5,
            ),
            AnonymizedHistogramBin(
                prompt_tokens=1024,
                generation_tokens=128,
                count=1,
                concurrency=8,
                shared_prefix_fraction=0.75,
            ),
        )
        manifest = build_workload_manifest(
            anonymized_histogram=histogram
        )
        definition = manifest["definitions"][3]
        self.assertEqual(definition["status"], "READY")
        requests = phase(manifest, "W4", "cold")["requests"]
        self.assertEqual(len(requests), 3)
        self.assertEqual(requests[0]["shared_prefix_tokens"], 128)
        self.assertEqual(requests[-1]["shared_prefix_tokens"], 768)

    def test_manifest_contains_no_raw_content_or_sensitive_values(self):
        manifest = build_workload_manifest(seed=7)
        validate_workload_manifest(manifest)
        serialized = json.dumps(manifest).lower()
        for forbidden in (
            '"raw_prompt"',
            '"prompt_text"',
            '"token_ids"',
            '"api_key"',
            '"endpoint"',
            '"cache_salt"',
            '"tenant_id"',
        ):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
