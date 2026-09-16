# -*- coding: utf-8 -*-
"""Fail-closed errors for the v3 P0 overlay. None of these are retried."""
from __future__ import annotations


class OctopusV3Error(Exception):
    """Base. Callers must treat any subclass as deny, not retry."""


class LedgerClosed(OctopusV3Error):
    """Disk/I/O failure or torn ledger — no action may start (INV-5)."""


class LedgerIntegrityError(OctopusV3Error):
    """Hash chain or HMAC break. History is untrusted until human repair."""


class KillEngaged(OctopusV3Error):
    """Kill switch or composed STOP file is active (INV-3)."""


class BudgetExceeded(OctopusV3Error):
    """Per-action, daily, or monthly overlay cap would be breached (INV-1)."""


class PolicyDenied(OctopusV3Error):
    """hard_no_go or L3 human-approval missing (INV-2 / INV-11)."""


class LeaseError(OctopusV3Error):
    """Capability lease expired, exhausted, replayed, or params tampered."""


class TaintNetworkDenied(OctopusV3Error):
    """G4 latch: tainted task requested network after latch fired."""


class DualBeatDenied(OctopusV3Error):
    """Another living holder owns the beat, or the lease file is untrusted."""
