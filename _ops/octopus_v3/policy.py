# -*- coding: utf-8 -*-
"""hard_no_go + L3 classification. Policy author is the owner (INV-11)."""
from __future__ import annotations

from .exceptions import PolicyDenied
from .profile import HARD_NO_GO

# Action names that are structurally forbidden — not a preference, a fence.
FORBIDDEN_ACTIONS = frozenset(HARD_NO_GO.keys()) | frozenset({
    "abliterate",
    "abliteration",
    "auto_transfer",
    "auto_payout",
    "edit_invariants",
    "edit_policy_weights",
    "public_companion_chatbot",
    "install_vaara",
    "install_kremis",
    "pip_install_unadmitted",
})

L3_KINDS = frozenset({"financial", "irreversible", "production", "policy"})


def deny_forbidden(action_name: str) -> None:
    key = action_name.strip().lower().replace("-", "_")
    if key in FORBIDDEN_ACTIONS or key in HARD_NO_GO:
        raise PolicyDenied(HARD_NO_GO.get(key, f"hard_no_go: {key}"))


def requires_owner(action_name: str, *, financial: bool, irreversible: bool, production: bool) -> bool:
    if financial or irreversible or production:
        return True
    key = action_name.strip().lower()
    return key in L3_KINDS or key.startswith("money_") or key.startswith("policy_")
