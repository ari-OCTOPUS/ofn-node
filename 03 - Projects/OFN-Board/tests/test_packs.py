"""Pack loading: the YAML subset parser, validation, and the three real packs."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from ofn.adapters.packloader import (
    load_dir, load_pack, parse_yaml_subset, spec_from_mapping,
)
from ofn.kernel.domain import Confidence, RiskTier
from ofn.kernel.errors import PackError
from ofn.kernel.quota import NodeQuota
from ofn.kernel.tenancy import TenantRegistry

PACKS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "packs")


class TestYamlSubset(unittest.TestCase):
    def test_scalars(self):
        d = parse_yaml_subset("a: 1\nb: 2.5\nc: true\nd: false\ne: hello\nf: 'q'\n")
        self.assertEqual(d, {"a": 1, "b": 2.5, "c": True, "d": False,
                             "e": "hello", "f": "q"})

    def test_comments_stripped(self):
        d = parse_yaml_subset("# header\na: 1  # trailing\n")
        self.assertEqual(d, {"a": 1})

    def test_hash_inside_quotes_survives(self):
        d = parse_yaml_subset('a: "not # a comment"\n')
        self.assertEqual(d["a"], "not # a comment")

    def test_nested_mapping(self):
        d = parse_yaml_subset("outer:\n  inner: 5\n  other: x\n")
        self.assertEqual(d, {"outer": {"inner": 5, "other": "x"}})

    def test_block_sequence(self):
        d = parse_yaml_subset("items:\n  - a\n  - b\n")
        self.assertEqual(d, {"items": ["a", "b"]})

    def test_inline_sequence(self):
        self.assertEqual(parse_yaml_subset("items: [a, b, c]\n"),
                         {"items": ["a", "b", "c"]})
        self.assertEqual(parse_yaml_subset("items: []\n"), {"items": []})

    def test_tabs_rejected(self):
        with self.assertRaises(PackError):
            parse_yaml_subset("a:\n\tb: 1\n")

    def test_odd_indentation_rejected(self):
        with self.assertRaises(PackError):
            parse_yaml_subset("a:\n   b: 1\n")

    def test_line_without_colon_rejected(self):
        with self.assertRaises(PackError):
            parse_yaml_subset("just a line\n")

    def test_empty_document(self):
        self.assertEqual(parse_yaml_subset(""), {})


class TestValidation(unittest.TestCase):
    def base(self, **kw):
        d = {"tenant": "alpha", "capacity_units_per_week": 6, "quota_share": 0.5}
        d.update(kw)
        return d

    def test_minimal_pack(self):
        spec = spec_from_mapping(self.base())
        self.assertEqual(spec.tenant.value, "alpha")
        self.assertEqual(spec.capacity_units_per_week, 6)

    def test_missing_tenant(self):
        with self.assertRaises(PackError):
            spec_from_mapping({"capacity_units_per_week": 6})

    def test_bad_tenant_id(self):
        with self.assertRaises(PackError):
            spec_from_mapping(self.base(tenant="../evil"))

    def test_non_integer_capacity(self):
        with self.assertRaises(PackError):
            spec_from_mapping(self.base(capacity_units_per_week="six"))

    def test_bool_is_not_an_integer_capacity(self):
        with self.assertRaises(PackError):
            spec_from_mapping(self.base(capacity_units_per_week=True))

    def test_unknown_confidence_is_rejected_with_a_useful_message(self):
        with self.assertRaises(PackError) as cm:
            spec_from_mapping(self.base(required_facts={"x": "sort_of_sure"}))
        self.assertIn("owner_confirmed", str(cm.exception))

    def test_unknown_tier_is_rejected(self):
        with self.assertRaises(PackError):
            spec_from_mapping(self.base(risk_overrides={"a": "puce"}))

    def test_share_out_of_range(self):
        with self.assertRaises(PackError):
            spec_from_mapping(self.base(quota_share=1.5))

    def test_gates_must_be_a_list(self):
        with self.assertRaises(PackError):
            spec_from_mapping(self.base(gates="capacity"))

    def test_confidences_and_tiers_parse(self):
        spec = spec_from_mapping(self.base(
            required_facts={"a": "measured", "b": "owner_confirmed"},
            risk_overrides={"go": "red", "look": "green"},
            gates=["budget", "consent"]))
        self.assertIs(spec.required_facts["a"], Confidence.MEASURED)
        self.assertIs(spec.risk_overrides["go"], RiskTier.RED)
        self.assertEqual(spec.gates, ("budget", "consent"))


class TestFileLoading(unittest.TestCase):
    def test_json_and_yaml_agree(self):
        data = {"tenant": "alpha", "capacity_units_per_week": 4,
                "quota_share": 0.5, "gates": ["budget"],
                "required_facts": {"x": "measured"},
                "risk_overrides": {"go": "red"}}
        with tempfile.TemporaryDirectory() as d:
            jp = os.path.join(d, "a.json")
            with open(jp, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
            yp = os.path.join(d, "a.yaml")
            with open(yp, "w", encoding="utf-8") as fh:
                fh.write("tenant: alpha\ncapacity_units_per_week: 4\n"
                         "quota_share: 0.5\ngates: [budget]\n"
                         "required_facts:\n  x: measured\n"
                         "risk_overrides:\n  go: red\n")
            self.assertEqual(load_pack(jp), load_pack(yp))

    def test_invalid_json_message(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.json")
            open(p, "w", encoding="utf-8").write("{nope")
            with self.assertRaises(PackError):
                load_pack(p)

    def test_duplicate_tenant_in_dir_is_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            for n in ("a.yaml", "b.yaml"):
                open(os.path.join(d, n), "w", encoding="utf-8").write(
                    "tenant: alpha\ncapacity_units_per_week: 1\n")
            with self.assertRaises(PackError):
                load_dir(d)

    def test_empty_dir_is_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(PackError):
                load_dir(d)


class TestRealPacks(unittest.TestCase):
    """The packs that ship with this node: three partner legs + hypno."""

    def setUp(self):
        self.packs = load_dir(PACKS_DIR)

    def test_all_four_load(self):
        self.assertEqual(sorted(self.packs),
                         ["hypno", "lead", "studio", "ziman"])

    def test_shares_sum_to_one(self):
        total = sum(p.quota_share for p in self.packs.values())
        self.assertAlmostEqual(total, 1.0, places=6)

    def test_registry_accepts_them(self):
        reg = TenantRegistry(self.packs)
        self.assertEqual(len(reg), 4)

    def test_quota_built_from_packs_matches_the_agreed_split(self):
        """40% utilisation of the derived weekly capacity, split 35/35/20/10."""
        capacity = 180_000_000
        q = NodeQuota(
            estimated_capacity_tokens=capacity, utilisation=0.40,
            shares={k: v.quota_share for k, v in self.packs.items()})
        self.assertEqual(q.node_ceiling, 72_000_000)
        self.assertEqual(q.tenant_ceiling("ziman"), 25_200_000)
        self.assertEqual(q.tenant_ceiling("lead"), 25_200_000)
        self.assertEqual(q.tenant_ceiling("studio"), 14_400_000)
        self.assertEqual(q.tenant_ceiling("hypno"), 7_200_000)
        self.assertTrue(q.capacity_is_estimate)

    def test_every_pack_declares_capacity_and_gates(self):
        for name, p in self.packs.items():
            with self.subTest(pack=name):
                self.assertGreater(p.capacity_units_per_week, 0)
                self.assertTrue(p.gates)

    def test_every_required_fact_key_is_subject_dot_predicate(self):
        """Regression: the packs once used bare keys while the fact store is
        subject/predicate shaped, so every answer was silently rejected. Unit
        tests passed because they used their own dotted fixtures; only an
        end-to-end run against the real packs caught it."""
        for name, p in self.packs.items():
            for key in p.required_facts:
                with self.subTest(pack=name, key=key):
                    subject, sep, predicate = key.partition(".")
                    self.assertTrue(sep, f"{key!r} has no '.' separator")
                    self.assertTrue(subject and predicate,
                                    f"{key!r} has an empty half")
                    self.assertNotIn(".", predicate,
                                     f"{key!r} has more than one separator")

    def test_every_pack_is_subject_to_secret_rotation(self):
        """The node-wide closed gate must reach all three, or one leg escapes it."""
        for name, p in self.packs.items():
            with self.subTest(pack=name):
                self.assertIn("secret_rotation", p.gates)

    def test_no_pack_downgrades_a_publish_action(self):
        for name, p in self.packs.items():
            for action, tier in p.risk_overrides.items():
                if action.startswith(("publish", "send", "confirm")):
                    with self.subTest(pack=name, action=action):
                        self.assertTrue(tier.at_least(RiskTier.YELLOW))


if __name__ == "__main__":
    unittest.main()
