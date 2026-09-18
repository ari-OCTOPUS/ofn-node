#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chain — ActionChainLinker: lead → contact → response → quote → payment.

A missing link is recorded as UNKNOWN and never invented. Completeness is a
property of evidence, not of wishfulness.
"""
from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["ChainLink", "ActionChain", "ActionChainLinker", "LINK_KINDS"]

LINK_KINDS = ("lead", "contact", "response", "quote", "payment")


@dataclass
class ChainLink:
    kind: str
    ref: str | None = None
    at: str | None = None
    status: str = "unknown"      # known | unknown — never fabricated
    evidence: str = ""


@dataclass
class ActionChain:
    campaign_id: str
    lead_id: str
    links: dict = field(default_factory=dict)

    @property
    def complete(self) -> bool:
        return all(self.links.get(k) and self.links[k].status == "known"
                   for k in LINK_KINDS)

    def unknown_links(self) -> list[str]:
        return [k for k in LINK_KINDS
                if not self.links.get(k) or self.links[k].status != "known"]


class ActionChainLinker:
    def build(self, campaign_id: str, lead_id: str, events: list[dict]) -> ActionChain:
        """events: normalized dicts {kind, ref, at, evidence} from runtime receipts."""
        chain = ActionChain(campaign_id=campaign_id, lead_id=lead_id)
        for kind in LINK_KINDS:
            chain.links[kind] = ChainLink(kind=kind, status="unknown")
        for ev in events:
            kind = ev.get("kind")
            if kind not in LINK_KINDS:
                continue
            if kind == "lead":
                link = chain.links["lead"]
                link.ref, link.at = ev.get("ref", lead_id), ev.get("at")
                link.status, link.evidence = "known", ev.get("evidence", "")
                continue
            # keep the FIRST known link of each kind (earliest evidence wins;
            # later duplicates are already handled by ledger idempotency)
            if chain.links[kind].status != "known":
                chain.links[kind] = ChainLink(
                    kind=kind, ref=ev.get("ref"), at=ev.get("at"),
                    status="known", evidence=ev.get("evidence", ""))
        return chain
