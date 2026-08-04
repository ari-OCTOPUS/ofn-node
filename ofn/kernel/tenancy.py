"""Tenancy: three businesses on one board, unable to see each other.

The isolation guarantee this module makes is narrow and therefore keepable:

  A caller holding a scope for tenant A cannot name, read, or write any
  state belonging to tenant B — not by path, not by key, not by accident.

It is enforced structurally, not by convention. `TenantScope` is the only way
to build a state key, and it refuses to build one for a tenant other than its
own. There is no "just this once" parameter.

Note what this does *not* claim: it is not a security boundary against
hostile code running in-process. It is a correctness boundary against the
far likelier failure — a leg reaching into a sibling's data because a string
got threaded through the wrong call.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Mapping

from .domain import PackSpec, TenantId
from .errors import TenantIsolationError, UnknownTenantError


@dataclass(frozen=True)
class TenantScope:
    """A capability object: proof that the holder may act as exactly one tenant.

    Pass this instead of a tenant string. A function that takes a `TenantScope`
    cannot be tricked into touching a neighbour, because the scope itself
    refuses to produce a foreign key.
    """

    tenant: TenantId

    def key(self, *parts: str) -> str:
        """Namespace a state key under this tenant.

        Every storage adapter must route through here. Parts are validated so
        a caller cannot climb out with `..` or inject a separator.
        """
        if not parts:
            raise ValueError("key requires at least one part")
        for p in parts:
            if not p:
                raise ValueError("key parts must be non-empty")
            if "/" in p or "\\" in p or ".." in p:
                raise TenantIsolationError(
                    f"illegal key part {p!r}: separators and traversal are refused"
                )
        return "/".join((self.tenant.value, *parts))

    def owns(self, key: str) -> bool:
        """True iff `key` was minted by this scope."""
        return key.startswith(self.tenant.value + "/")

    def assert_owns(self, key: str) -> None:
        """Guard for the read path. Storage adapters call this before returning
        a value, so a key smuggled in from elsewhere cannot be dereferenced."""
        if not self.owns(key):
            raise TenantIsolationError(
                f"tenant {self.tenant.value!r} may not touch key {key!r}"
            )

    def state_dir(self, root: str) -> str:
        """Filesystem location for this tenant. Pure string arithmetic — this
        module never creates or opens anything."""
        base = root.rstrip("/\\")
        return f"{base}/tenants/{self.tenant.value}/state"


class TenantRegistry:
    """The set of legs this node runs, and the only place scopes are minted.

    Routing lives here too: an inbound chat, webhook, or hostname maps to
    exactly one tenant, and an unmapped identifier fails closed rather than
    landing on a default. Silently defaulting is how one partner ends up
    reading another's queue.
    """

    def __init__(self, packs: Mapping[str, PackSpec]) -> None:
        self._packs: dict[str, PackSpec] = {}
        for key, spec in packs.items():
            if key != spec.tenant.value:
                raise ValueError(
                    f"registry key {key!r} does not match pack tenant {spec.tenant.value!r}"
                )
            self._packs[key] = spec
        total = sum(p.quota_share for p in self._packs.values())
        if total > 1.0 + 1e-9:
            raise ValueError(f"quota shares sum to {total:.3f}, which exceeds 1.0")
        self._routes: dict[str, str] = {}

    # ── membership ────────────────────────────────────────────────────────
    def __contains__(self, tenant: object) -> bool:
        if isinstance(tenant, TenantId):
            return tenant.value in self._packs
        if isinstance(tenant, str):
            return tenant in self._packs
        return False

    def __iter__(self) -> Iterator[TenantId]:
        return (TenantId(k) for k in sorted(self._packs))

    def __len__(self) -> int:
        return len(self._packs)

    @property
    def tenants(self) -> tuple[TenantId, ...]:
        return tuple(TenantId(k) for k in sorted(self._packs))

    # ── scopes and packs ──────────────────────────────────────────────────
    def scope(self, tenant: TenantId | str) -> TenantScope:
        """Mint a scope. This is the only constructor callers should use."""
        name = tenant.value if isinstance(tenant, TenantId) else tenant
        if name not in self._packs:
            raise UnknownTenantError(f"no such tenant: {name!r}")
        return TenantScope(TenantId(name))

    def pack(self, tenant: TenantId | str) -> PackSpec:
        name = tenant.value if isinstance(tenant, TenantId) else tenant
        try:
            return self._packs[name]
        except KeyError:
            raise UnknownTenantError(f"no such tenant: {name!r}") from None

    # ── routing ───────────────────────────────────────────────────────────
    def bind_route(self, identifier: str, tenant: TenantId | str) -> None:
        """Map an external identifier (chat id, hostname, bot token id) to a leg.

        Rebinding an identifier to a *different* tenant is refused: that is
        either a config mistake or an attempt to hijack a partner's channel,
        and neither should succeed quietly.
        """
        name = tenant.value if isinstance(tenant, TenantId) else tenant
        if name not in self._packs:
            raise UnknownTenantError(f"cannot route to unknown tenant {name!r}")
        if not identifier:
            raise ValueError("route identifier must be non-empty")
        existing = self._routes.get(identifier)
        if existing is not None and existing != name:
            raise TenantIsolationError(
                f"identifier {identifier!r} already routes to {existing!r}; "
                f"refusing to rebind to {name!r}"
            )
        self._routes[identifier] = name

    def route(self, identifier: str) -> TenantScope:
        """Resolve an external identifier to a scope, or fail closed."""
        name = self._routes.get(identifier)
        if name is None:
            raise UnknownTenantError(
                f"identifier {identifier!r} is not routed to any tenant"
            )
        return TenantScope(TenantId(name))
