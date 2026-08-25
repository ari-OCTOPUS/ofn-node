import sys
import unittest

sys.path.insert(0, "/opt/octopus/lab")

from ofn.adapters import vllm_prefix_cache


class VllmPrefixCacheHashTests(unittest.TestCase):
    def test_sha256_cache_salt_changes_hash(self):
        block_tokens = (100, 200, 300, 400)
        shared_extra = {
            "model_id": "model-a",
            "tokenizer_id": "tok-a",
            "model_revision": "rev-a",
            "lora_id": "base",
        }
        hash_a, _ = vllm_prefix_cache.compute_block_hash(
            algorithm="sha256",
            parent_hash=None,
            block_tokens=block_tokens,
            extra_hashes={**shared_extra, "cache_salt": "tenant-a"},
        )
        hash_b, _ = vllm_prefix_cache.compute_block_hash(
            algorithm="sha256",
            parent_hash=None,
            block_tokens=block_tokens,
            extra_hashes={**shared_extra, "cache_salt": "tenant-b"},
        )
        self.assertNotEqual(hash_a, hash_b)

    def test_overlap_ratio_reduces_when_cache_salt_enabled(self):
        config = vllm_prefix_cache.WorkloadConfig(
            tenant_count=4,
            prompts_per_tenant=6,
            blocks_per_prompt=3,
            block_size=8,
            iterations=20,
            collision_samples=200,
        )
        no_salt = vllm_prefix_cache.tenant_overlap_metrics(
            algorithm="sha256",
            config=config,
            include_cache_salt=False,
        )
        with_salt = vllm_prefix_cache.tenant_overlap_metrics(
            algorithm="sha256",
            config=config,
            include_cache_salt=True,
        )
        self.assertGreater(no_salt["overlap_ratio"], 0.0)
        self.assertEqual(with_salt["overlap_ratio"], 0.0)

    def test_run_suite_includes_sha256_result(self):
        config = vllm_prefix_cache.WorkloadConfig(
            tenant_count=2,
            prompts_per_tenant=2,
            blocks_per_prompt=2,
            block_size=4,
            iterations=8,
            collision_samples=100,
        )
        result = vllm_prefix_cache.run_suite(config, ["sha256"])
        self.assertEqual(result["suite"], "vllm_apc_hash_benchmark")
        self.assertEqual(result["algorithms"][0]["algorithm"], "sha256")
        self.assertEqual(result["algorithms"][0]["status"], "OK")

    @unittest.skipUnless(vllm_prefix_cache.cbor2 is not None, "cbor2 not installed")
    def test_sha256_cbor_has_stable_bytes_for_reordered_keys(self):
        probe = vllm_prefix_cache.reproducibility_probe("sha256_cbor")
        self.assertTrue(probe["same_bytes_after_key_reordering"])


if __name__ == "__main__":
    unittest.main()
