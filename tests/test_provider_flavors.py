"""Provider failure flavors: weather retries, billing walls park."""

from __future__ import annotations
import unittest

from ofn.adapters.router import provider_note_is_transient


class TestProviderNoteClassification(unittest.TestCase):
    def test_rate_limit_and_outages_are_transient(self):
        for note in ("fugu:http-429", "fugu:http-503", "fugu:unreachable",
                     "fugu:error"):
            self.assertTrue(provider_note_is_transient(note), note)

    def test_config_and_billing_failures_are_not_transient(self):
        for note in ("fugu:not-armed", "fugu:http-401", "fugu:no-choice",
                     "fugu:usage-limit", "", "fugu"):
            self.assertFalse(provider_note_is_transient(note), note)
