#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scorer — OutcomeScorer: rank an action chain by ECONOMIC evidence strength.

Evidence ladder (strongest first):
  verified payment > quote > response > contact > nothing.
No-response is an INFORMATIONAL failure about OUR data/action, never a final
verdict about the market. The scorer is structurally incapable of producing
send-authorization or replacing consent — those names raise on sight.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .receipts import PaymentReceipt, VERIFIED

__all__ = ["OutcomeScore", "OutcomeScorer", "FORBIDDEN_OUTPUT_NAMES"]

# mirror of ofn.kernel.events.FORBIDDEN_EFFECT_KINDS (read-only constant —
# the kernel vocabulary itself is untouched on this lane)
FORBIDDEN_OUTPUT_NAMES = frozenset({
    "send_authorized", "quote_sent", "campaign_envelope_ready",
})

LEVELS = ("VERIFIED_REVENUE", "QUOTE_SIGNAL", "RESPONSE_SIGNAL",
          "NO_SIGNAL", "INFO_FAILURE")


@dataclass
class OutcomeScore:
    campaign_id: str
    lead_id: str
    level: str
    reasons: list = field(default_factory=list)
    payment_received_verified: bool = False

    def as_dict(self) -> dict:
        return {"campaign_id": self.campaign_id, "lead_id": self.lead_id,
                "level": self.level, "reasons": self.reasons,
                "payment_received_verified": self.payment_received_verified}


class OutcomeScorer:
    def score(self, chain, payment: PaymentReceipt | None = None) -> OutcomeScore:
        out = OutcomeScore(campaign_id=chain.campaign_id, lead_id=chain.lead_id,
                           level="NO_SIGNAL")
        if payment is not None and payment.verification_status == VERIFIED:
            if payment.verification_status == VERIFIED:
                out.payment_received_verified = True
                out.level = "VERIFIED_REVENUE"
                out.reasons.append("independent-receipt-verified payment linked to chain")
                return out
        if payment is not None and payment.verification_status == "DISCONNECTED":
            out.reasons.append("payment receipt exists but not provably linked to this lead")
        known = {k: chain.links[k].status == "known" for k in chain.links}
        if known.get("quote"):
            out.level = "QUOTE_SIGNAL"
            out.reasons.append("quote present without verified payment")
        elif known.get("response"):
            out.level = "RESPONSE_SIGNAL"
            out.reasons.append("response present without quote")
        elif known.get("contact"):
            out.level = "INFO_FAILURE" if not known.get("response") else out.level
            out.reasons.append("contact sent, no response observed (informational, not a market verdict)")
        out.payment_received_verified = False
        return out

    # ------------------------------------------------------------- hard rule
    def authorize(self, *_args, **_kwargs):
        """The scorer can never produce authorization. Calling this is a bug."""
        raise RuntimeError(
            "OutcomeScorer cannot produce authorization or consent substitutes — "
            "economic evidence never yields send_authorized")
