import sys
import unittest

sys.path.insert(0, "/opt/octopus/lab")

from ofn.benchmarks.vllm_block_size import (
    apc_unreused_suffix_tokens,
    divisible_block_tail_waste_property,
    estimate_fragmentation,
    estimate_full_attention_kv_bytes,
    tail_waste_tokens,
)


class VllmBlockSizeEstimatorTests(unittest.TestCase):
    def test_exact_block_has_zero_waste(self):
        result = estimate_fragmentation([16], 16)
        self.assertEqual(result.allocated_tokens, 16)
        self.assertEqual(result.wasted_tokens, 0)
        self.assertEqual(result.fragmentation_ratio, 0.0)
        self.assertEqual(result.mean_waste_per_request, 0)

    def test_one_token_over_block_allocates_two_blocks(self):
        result = estimate_fragmentation([17], 16)
        self.assertEqual(result.logical_tokens, 17)
        self.assertEqual(result.allocated_tokens, 32)
        self.assertEqual(result.wasted_tokens, 15)
        self.assertAlmostEqual(result.fragmentation_ratio, 15 / 32)
        self.assertEqual(result.mean_waste_per_request, 15)

    def test_zero_lengths_have_zero_ratio(self):
        result = estimate_fragmentation([0, 0], 8)
        self.assertEqual(result.allocated_tokens, 0)
        self.assertEqual(result.wasted_tokens, 0)
        self.assertEqual(result.fragmentation_ratio, 0.0)

    def test_allocation_is_exact_for_large_integer_lengths(self):
        length = 10**100 + 1
        result = estimate_fragmentation([length], 16)
        self.assertEqual(result.allocated_tokens % 16, 0)
        self.assertEqual(
            result.wasted_tokens,
            (16 - (length % 16)) % 16,
        )

    def test_invalid_inputs_are_rejected(self):
        for block_size in (0, -1, 1.5, True):
            with self.subTest(block_size=block_size):
                with self.assertRaises(ValueError):
                    estimate_fragmentation([1], block_size)
        with self.assertRaises(ValueError):
            estimate_fragmentation([], 16)
        with self.assertRaises(ValueError):
            estimate_fragmentation([1, -1], 16)
        with self.assertRaises(ValueError):
            estimate_fragmentation([1.5], 16)

    def test_divisible_sizes_have_scoped_monotonic_tail_waste(self):
        for smaller, larger in ((1, 8), (2, 8), (4, 16), (8, 16), (8, 32)):
            for length in range(0, 257):
                with self.subTest(
                    smaller=smaller, larger=larger, length=length
                ):
                    self.assertTrue(
                        divisible_block_tail_waste_property(
                            length, smaller, larger
                        )
                    )

    def test_numeric_size_order_alone_is_not_monotonic(self):
        self.assertLess(6, 8)
        self.assertGreater(tail_waste_tokens(7, 6), tail_waste_tokens(7, 8))
        with self.assertRaises(ValueError):
            divisible_block_tail_waste_property(7, 6, 8)

    def test_apc_unreused_suffix_is_bounded(self):
        for block_size in (8, 16, 32):
            for length in range(0, 100):
                suffix = apc_unreused_suffix_tokens(length, block_size)
                self.assertEqual(suffix, length % block_size)
                self.assertLessEqual(suffix, block_size - 1)

    def test_full_attention_memory_estimate_is_explicitly_theoretical(self):
        result = estimate_full_attention_kv_bytes(
            num_layers=2,
            num_kv_heads=4,
            head_dim=8,
            bytes_per_element=2,
            tensor_parallel_sharding=2,
            block_size=16,
        )
        self.assertEqual(result.bytes_per_token, 128)
        self.assertEqual(result.bytes_per_block, 2048)
        self.assertTrue(any("authoritative" in item for item in result.limitations))


if __name__ == "__main__":
    unittest.main()
