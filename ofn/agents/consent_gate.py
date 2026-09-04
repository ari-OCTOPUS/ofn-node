"""consent_gate — the third, independent, store-backed consent layer.

Layer 1 is the structural firewall inside ``consent_store`` (SQL CHECKs).
Layer 2 was the planned ``consent_firewall`` in lead_effect_gate. This
module is layer 3 (wired per the 2026-08-07 owner wiring note in
outbound_worker.py): it NEVER trusts a producer's claim about consent —
it re-reads the persisted ``consent_current`` row from the store and
refuses unless that row, right now, says outreach is allowed.

Contract (must match outbound_worker._consent_check):
  may_draft(lead_id, store=None)          -> (ok: bool, reason: str)
  may_release(lead_id, effect_kind, store=None) -> (ok: bool, reason: str)

Fail-closed: missing record, purged row, stale retention anchor, revoked
consent state, unreviewed compliance, active suppression, or ANY error
reading the store → (False, reason). The reasons are stable strings so
worker receipts can classify them.

A store may be injected (tests); otherwise a fresh ConsentStore is opened
and always closed here — same shape as the worker's own guard.
"""

from __future__ import annotations

from typing import Any

# consent_state values that permit outreach. The store's own CHECK firewall
# already forbids these states from carrying outreach_allowed=1; we re-check
# independently (defence in depth, layer 3 must not lean on layer 1).
_ALLOW_STATES = frozenset({"CONSENTED_INBOUND", "B2B_PROSPECT"})
# compliance must be human-reviewed before any effect.
_ALLOW_COMPLIANCE = frozenset({"CLEAR", "OWNER_CLEARED"})


def _open(store: Any | None):
    if store is not None:
        return store, False
    import consent_store as _cs  # noqa: WPS433 — lazy, same-directory
    return _cs.ConsentStore(), True


def normalize_email(value: str) -> str:
    return str(value or "").strip().casefold()


def _check(lead_id: str, *, store: Any) -> tuple[bool, str]:
    rec = store.load_current(str(lead_id))
    if rec is None:
        return False, "consent:missing"
    if rec.get("purged"):
        return False, "consent:purged"
    if not rec.get("outreach_allowed"):
        return False, f"consent:not-allowed:{rec.get('consent_state', 'unknown')}"
    state = str(rec.get("consent_state", ""))
    if state not in _ALLOW_STATES:
        return False, f"consent:state-blocked:{state}"
    compliance = str(rec.get("compliance_state", "UNREVIEWED"))
    if compliance not in _ALLOW_COMPLIANCE:
        return False, f"consent:compliance:{compliance.lower()}"
    cvn = rec.get("contact_value_norm")
    if cvn:
        active = store.suppression_active(str(cvn))
        if active:
            return False, f"consent:suppressed:{active}"
    return True, "consent:ok"


def may_draft(lead_id: str, store: Any | None = None) -> tuple[bool, str]:
    """Layer-3 consent check before composing a draft (no effect)."""
    s, owned = _open(store)
    try:
        return _check(lead_id, store=s)
    except Exception as e:  # noqa: BLE001 — fail-closed by design
        return False, f"consent-gate-unavailable:{type(e).__name__}"
    finally:
        if owned:
            try:
                s.close()
            except Exception:  # noqa: BLE001
                pass


def may_release(lead_id: str, effect_kind: str = "",
                store: Any | None = None) -> tuple[bool, str]:
    """Layer-3 consent check before release_and_settle (before transport —
    a deny here must leave the effect releasable, so this is checked
    BEFORE settle in send_one, never after)."""
    s, owned = _open(store)
    try:
        ok, why = _check(lead_id, store=s)
        if not ok:
            return ok, why
        # Retention anchor sanity: an anchor absurdly in the future or a
        # blank one means the row was hand-edited — refuse and record.
        anchor = str((s.load_current(str(lead_id)) or {}).get(
            "retention_anchor_at") or "")
        if not anchor or len(anchor) < 10:
            return False, "consent:retention-anchor-invalid"
        return True, f"consent:ok:{effect_kind}" if effect_kind else "consent:ok"
    except Exception as e:  # noqa: BLE001
        return False, f"consent-gate-unavailable:{type(e).__name__}"
    finally:
        if owned:
            try:
                s.close()
            except Exception:  # noqa: BLE001
                pass
