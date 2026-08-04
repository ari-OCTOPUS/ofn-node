"""Tenant isolation: the promise that one business cannot reach another's data.

The exit gate for this phase is a single sentence: a write performed as tenant
A must never be visible to tenant B. Everything below is an attempt to break
that in the ways it would actually break in production — a string threaded
through the wrong call, a path traversal in a key, a route rebound by a typo.
"""

from __future__ import annotations

import unittest

from ofn.kernel.domain import Confidence, PackSpec, RiskTier, TenantId
from ofn.kernel.errors import TenantIsolationError, UnknownTenantError
from ofn.kernel.tenancy import TenantRegistry, TenantScope


def pack(name: str, share: float = 0.3) -> PackSpec:
    return PackSpec(tenant=TenantId(name), capacity_units_per_week=6,
                    quota_share=share)


class FakeStore:
    """Minimal StatePort stand-in that enforces scope ownership, as a real
    adapter is required to."""

    def __init__(self) -> None:
        self.data: dict[str, bytes] = {}

    def put(self, scope: TenantScope, key: str, value: bytes) -> None:
        scope.assert_owns(key)
        self.data[key] = value

    def get(self, scope: TenantScope, key: str) -> bytes | None:
        scope.assert_owns(key)
        return self.data.get(key)


class TestTenantId(unittest.TestCase):
    def test_rejects_empty_and_overlong(self):
        with self.assertRaises(ValueError):
            TenantId("")
        with self.assertRaises(ValueError):
            TenantId("x" * 33)

    def test_rejects_path_traversal_and_separators(self):
        for bad in ["../etc", "a/b", "a\\b", "a.b", "UPPER", "a b"]:
            with self.subTest(value=bad), self.assertRaises(ValueError):
                TenantId(bad)

    def test_rejects_leading_or_trailing_punctuation(self):
        for bad in ["-a", "a-", "_a", "a_"]:
            with self.subTest(value=bad), self.assertRaises(ValueError):
                TenantId(bad)

    def test_accepts_normal_ids(self):
        for good in ["a", "alpha", "alpha-two", "leg_3", "x9"]:
            with self.subTest(value=good):
                self.assertEqual(TenantId(good).value, good)


class TestScopeKeys(unittest.TestCase):
    def setUp(self):
        self.a = TenantScope(TenantId("alpha"))
        self.b = TenantScope(TenantId("bravo"))

    def test_keys_are_namespaced(self):
        self.assertEqual(self.a.key("facts", "capacity"), "alpha/facts/capacity")

    def test_key_refuses_traversal(self):
        for bad in ["..", "../bravo", "a/b", "a\\b"]:
            with self.subTest(part=bad), self.assertRaises(TenantIsolationError):
                self.a.key(bad)

    def test_key_requires_parts(self):
        with self.assertRaises(ValueError):
            self.a.key()
        with self.assertRaises(ValueError):
            self.a.key("")

    def test_owns_is_exact_not_prefix_confusable(self):
        """`alpha` must not appear to own `alphabet/...`."""
        other = TenantScope(TenantId("alphabet"))
        k = other.key("facts")
        self.assertFalse(self.a.owns(k))
        with self.assertRaises(TenantIsolationError):
            self.a.assert_owns(k)

    def test_state_dirs_are_disjoint(self):
        self.assertNotEqual(self.a.state_dir("/opt/ofn"), self.b.state_dir("/opt/ofn"))
        self.assertTrue(self.a.state_dir("/opt/ofn").endswith("/tenants/alpha/state"))


class TestNoCrossTenantLeak(unittest.TestCase):
    """The headline guarantee."""

    def setUp(self):
        self.reg = TenantRegistry({
            "alpha": pack("alpha"), "bravo": pack("bravo"), "charlie": pack("charlie"),
        })
        self.store = FakeStore()

    def test_write_in_a_is_invisible_to_b(self):
        a, b = self.reg.scope("alpha"), self.reg.scope("bravo")
        self.store.put(a, a.key("secret"), b"alpha-only")

        # B cannot read A's key: it does not own it.
        with self.assertRaises(TenantIsolationError):
            self.store.get(b, a.key("secret"))

        # B asking for the same logical name gets its own namespace, and nothing.
        self.assertIsNone(self.store.get(b, b.key("secret")))

    def test_every_tenant_pair_is_isolated(self):
        for x in self.reg:
            sx = self.reg.scope(x)
            self.store.put(sx, sx.key("blob"), x.value.encode())
        for x in self.reg:
            for y in self.reg:
                if x == y:
                    continue
                with self.subTest(reader=y.value, target=x.value):
                    sy, sx = self.reg.scope(y), self.reg.scope(x)
                    with self.assertRaises(TenantIsolationError):
                        self.store.get(sy, sx.key("blob"))

    def test_each_tenant_reads_only_its_own_value(self):
        for x in self.reg:
            s = self.reg.scope(x)
            self.store.put(s, s.key("blob"), x.value.encode())
        for x in self.reg:
            s = self.reg.scope(x)
            self.assertEqual(self.store.get(s, s.key("blob")), x.value.encode())


class TestRegistry(unittest.TestCase):
    def test_unknown_tenant_fails_closed(self):
        reg = TenantRegistry({"alpha": pack("alpha")})
        with self.assertRaises(UnknownTenantError):
            reg.scope("nope")
        with self.assertRaises(UnknownTenantError):
            reg.pack("nope")

    def test_key_must_match_pack_tenant(self):
        with self.assertRaises(ValueError):
            TenantRegistry({"alpha": pack("bravo")})

    def test_shares_may_not_exceed_one(self):
        with self.assertRaises(ValueError):
            TenantRegistry({"alpha": pack("alpha", 0.7), "bravo": pack("bravo", 0.7)})

    def test_membership_and_iteration(self):
        reg = TenantRegistry({"bravo": pack("bravo"), "alpha": pack("alpha")})
        self.assertIn("alpha", reg)
        self.assertIn(TenantId("bravo"), reg)
        self.assertNotIn("zulu", reg)
        self.assertEqual(len(reg), 2)
        self.assertEqual([t.value for t in reg], ["alpha", "bravo"])  # sorted


class TestRouting(unittest.TestCase):
    def setUp(self):
        self.reg = TenantRegistry({"alpha": pack("alpha"), "bravo": pack("bravo")})

    def test_unrouted_identifier_fails_closed(self):
        with self.assertRaises(UnknownTenantError):
            self.reg.route("chat:12345")

    def test_routes_resolve_to_the_right_scope(self):
        self.reg.bind_route("chat:1", "alpha")
        self.reg.bind_route("chat:2", "bravo")
        self.assertEqual(self.reg.route("chat:1").tenant.value, "alpha")
        self.assertEqual(self.reg.route("chat:2").tenant.value, "bravo")

    def test_rebinding_to_a_different_tenant_is_refused(self):
        """A partner's channel must not be silently reassigned."""
        self.reg.bind_route("chat:1", "alpha")
        with self.assertRaises(TenantIsolationError):
            self.reg.bind_route("chat:1", "bravo")

    def test_rebinding_to_the_same_tenant_is_idempotent(self):
        self.reg.bind_route("chat:1", "alpha")
        self.reg.bind_route("chat:1", "alpha")
        self.assertEqual(self.reg.route("chat:1").tenant.value, "alpha")

    def test_cannot_route_to_unknown_tenant(self):
        with self.assertRaises(UnknownTenantError):
            self.reg.bind_route("chat:9", "zulu")


if __name__ == "__main__":
    unittest.main()
