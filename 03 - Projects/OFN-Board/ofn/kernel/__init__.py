"""Kernel: pure decision logic.

Hard rules, enforced by tests/test_kernel_purity.py:
  * stdlib only — no third-party imports, ever
  * no I/O, no clock, no environment, no filesystem
  * no business, partner, or product name appears anywhere in this package
"""

from .domain import (
    Action, Confidence, Decision, PackSpec, RiskTier, TenantId, TokenSpend, max_tier,
)
from .errors import (
    FailClosedError, KernelError, PackError, QuotaExceededError,
    TenantIsolationError, UnknownTenantError,
)
from .gates import admit, executable
from .quota import DEFAULT_ORCHESTRATION_MULTIPLIER, NodeQuota, week_index
from .risk import RiskAssessment, assess, base_tier, explain
from .routing import (
    INTERACTIVE_BUDGET_MS, RouteDecision, RouteRequest, Rung, fits_interactive,
    may_escalate, start_rung, token_estimate,
)
from .scrub import ScrubResult, assert_clean, has_identifying_data, scrub
from .tenancy import TenantRegistry, TenantScope

__all__ = [
    "Action", "Confidence", "Decision", "PackSpec", "RiskTier", "TenantId",
    "TokenSpend", "max_tier", "FailClosedError", "KernelError", "PackError",
    "QuotaExceededError", "TenantIsolationError", "UnknownTenantError",
    "admit", "executable", "NodeQuota", "week_index",
    "DEFAULT_ORCHESTRATION_MULTIPLIER", "RiskAssessment", "assess",
    "base_tier", "explain", "TenantRegistry", "TenantScope",
    "Rung", "RouteRequest", "RouteDecision", "start_rung", "may_escalate",
    "token_estimate", "fits_interactive", "INTERACTIVE_BUDGET_MS",
    "scrub", "ScrubResult", "has_identifying_data", "assert_clean",
]
