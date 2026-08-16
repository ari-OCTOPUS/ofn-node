#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""identity_store.py -- Lightweight identity registry for Octopus agents/services.

Registers identity types (user, agent, service, tool) and maps them to roles.
This is NOT a full IAM system. It is the minimum structure needed to answer:
  - "Is this agent_id known?"
  - "What type and role does this agent have?"
  - "On whose behalf is this agent acting?"

No SPIFFE, no Keycloak, no mTLS. Local stack justification:
  Octopus runs on a single laptop with one human owner. Service identity is
  internal process-to-process. Adding SPIRE/Keycloak would be disproportionate
  for a single-node deployment.

Design:
  - Typed identity: user, agent, service, tool
  - Roles: observer, worker, coordinator, owner
  - Delegation: agent can act "on_behalf_of" a user/owner (e.g., owner's CLI)
  - deny-by-default: unknown agent_id = denied

$0 | stdlib-only | no network | no external writes.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

SCHEMA = "identity-store.v1"

# Valid identity types
IDENTITY_TYPES = ("user", "agent", "service", "tool")

# Valid roles (ordered by privilege: observer < worker < coordinator < owner)
ROLES = ("observer", "worker", "coordinator", "owner")
_ROLE_RANK = {r: i for i, r in enumerate(ROLES)}


@dataclass(frozen=True)
class Identity:
    """Immutable identity record.

    Fields:
        agent_id: Unique identifier (e.g., "octopus-cortex", "owner-cli")
        identity_type: One of IDENTITY_TYPES
        role: One of ROLES
        on_behalf_of: Optional agent_id this identity represents (delegation)
        metadata: Additional attributes (immutable dict)
        created_at: Unix timestamp
    """
    agent_id: str
    identity_type: str
    role: str
    on_behalf_of: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        # Validate at construction time
        if not self.agent_id or not isinstance(self.agent_id, str):
            raise ValueError("agent_id must be non-empty string")
        if self.identity_type not in IDENTITY_TYPES:
            raise ValueError(f"identity_type must be one of {IDENTITY_TYPES}")
        if self.role not in ROLES:
            raise ValueError(f"role must be one of {ROLES}")


class IdentityStore:
    """In-memory identity registry. deny-by-default for unknown agents.

    Usage:
        store = IdentityStore()
        store.register(Identity("worker-1", "agent", "worker"))
        identity = store.lookup("worker-1")
        if identity is None:
            # denied -- unknown agent
        if store.has_privilege("worker-1", "observer"):
            # worker role >= observer role
    """

    def __init__(self) -> None:
        self._identities: dict[str, Identity] = {}

    def register(self, identity: Identity) -> None:
        """Register an identity. Overwrites if already exists (idempotent)."""
        if not isinstance(identity, Identity):
            raise TypeError("identity must be Identity instance")
        self._identities[identity.agent_id] = identity

    def lookup(self, agent_id: str) -> Identity | None:
        """Look up an identity by agent_id. Returns None if unknown (deny)."""
        return self._identities.get(str(agent_id))

    def is_known(self, agent_id: str) -> bool:
        """Check if agent_id is registered. Unknown = denied."""
        return str(agent_id) in self._identities

    def has_privilege(self, agent_id: str, required_role: str) -> bool:
        """Check if agent has at least the required role level.

        Uses role hierarchy: owner > coordinator > worker > observer.
        Unknown agent = False (deny-by-default).
        """
        identity = self.lookup(agent_id)
        if identity is None:
            return False  # deny-by-default
        if required_role not in _ROLE_RANK:
            return False
        return _ROLE_RANK.get(identity.role, -1) >= _ROLE_RANK[required_role]

    def check_delegation(self, agent_id: str, claimed_principal: str) -> bool:
        """Verify that agent_id is allowed to act on behalf of claimed_principal.

        True if:
          - agent_id IS the principal (direct access)
          - agent has on_behalf_of == claimed_principal
          - agent is an owner (owner can act on behalf of anyone)

        This is the confused-deputy defense: an agent claiming to act on behalf
        of X must have X in their on_behalf_of field.
        """
        if str(agent_id) == str(claimed_principal):
            return True
        identity = self.lookup(agent_id)
        if identity is None:
            return False  # unknown agent, deny
        if identity.on_behalf_of == str(claimed_principal):
            return True
        if identity.role == "owner":
            return True  # owner can delegate to anyone
        return False

    def list_identities(self) -> list[dict[str, Any]]:
        """Return all registered identities as dicts (for audit)."""
        return [
            {
                "agent_id": ident.agent_id,
                "identity_type": ident.identity_type,
                "role": ident.role,
                "on_behalf_of": ident.on_behalf_of,
                "created_at": ident.created_at,
            }
            for ident in self._identities.values()
        ]

    def revoke(self, agent_id: str) -> bool:
        """Remove an identity. Returns True if it existed."""
        return bool(self._identities.pop(str(agent_id), None))


# -- Seed identities for the Octopus system --
def default_store() -> IdentityStore:
    """Create an IdentityStore pre-populated with known Octopus identities.

    These are derived from bots.yaml and the known architecture:
      - owner: human operator (highest privilege)
      - octopus: commander agent (coordinator)
      - telbot: telegram assistant (worker, read-only)
      - mcp-vault: MCP vault server (service, read-only)
      - worker-*: dynamic workers (registered at task start, revoked at end)
    """
    store = IdentityStore()
    store.register(Identity("owner", "user", "owner"))
    store.register(Identity("octopus", "agent", "coordinator"))
    store.register(Identity("telbot", "service", "worker",
                            on_behalf_of="octopus"))
    store.register(Identity("mcp-vault", "service", "observer"))
    return store
