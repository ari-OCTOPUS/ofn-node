#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""discover_facade.py — read-only Discovery reply with explicit provenance.

Three sources behind one reply: catalog/manifest, hidden (journal/dark),
world_discovery. Never arms. Never external effect. UI must expose Sources.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Literal, Protocol

Trust = Literal["verified", "derived", "stale", "unknown"]

SCHEMA = "DiscoveryReply.v1"
POLICY_VERSION = "discover-facade.v2"


@dataclass(frozen=True)
class Provenance:
    source_id: str
    source_kind: Literal["catalog", "manifest", "journal", "world_discovery"]
    path: str
    captured_at: str
    trust: Trust
    content_digest: str
    stale_after_hours: int | None = None


@dataclass(frozen=True)
class DiscoveryFact:
    title: str
    text: str
    confidence: float
    provenance: Provenance


@dataclass(frozen=True)
class DiscoveryReply:
    text: str
    facts: tuple[DiscoveryFact, ...]
    generated_at: str
    evidence_level: Literal["STRUCTURAL", "TESTED", "SHADOW"]
    limitations: tuple[str, ...]
    schema: str = SCHEMA
    policy_version: str = POLICY_VERSION
    external_effect: bool = False

    def as_dict(self) -> dict:
        return {
            "schema": self.schema,
            "policy_version": self.policy_version,
            "text": self.text,
            "generated_at": self.generated_at,
            "evidence_level": self.evidence_level,
            "external_effect": self.external_effect,
            "limitations": list(self.limitations),
            "facts": [
                {
                    "title": f.title,
                    "text": f.text,
                    "confidence": f.confidence,
                    "provenance": asdict(f.provenance),
                }
                for f in self.facts
            ],
        }

    def sources_text(self) -> str:
        """Owner-facing «Sources / شواهد» panel — never omit provenance."""
        if not self.facts:
            return "شواهد: هیچ factی با provenance ثبت نشد.\n" + "\n".join(
                self.limitations or ()
            )
        lines = ["شواهد / Sources (provenance):"]
        for item in self.facts:
            p = item.provenance
            lines.append(
                f"· {item.title}\n"
                f"  kind={p.source_kind} trust={p.trust} conf={item.confidence:.2f}\n"
                f"  path={p.path} digest={p.content_digest}\n"
                f"  captured_at={p.captured_at}"
                + (f" stale_after_h={p.stale_after_hours}" if p.stale_after_hours else "")
            )
        if self.limitations:
            lines.append("")
            lines.append("محدودیت‌ها:")
            lines.extend(f"· {x}" for x in self.limitations)
        return "\n".join(lines)


class DiscoverySource(Protocol):
    def search(self, query: str) -> list[DiscoveryFact]: ...


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:16]


def _is_stale(p: Provenance, now: datetime) -> bool:
    if p.stale_after_hours is None:
        return False
    captured = datetime.fromisoformat(p.captured_at.replace("Z", "+00:00"))
    if captured.tzinfo is None:
        captured = captured.replace(tzinfo=UTC)
    return (now - captured).total_seconds() > p.stale_after_hours * 3600


def discover_reply_text(
    query: str,
    *,
    catalog: DiscoverySource,
    hidden_capabilities: DiscoverySource,
    world_discovery: DiscoverySource,
    now: datetime | None = None,
) -> DiscoveryReply:
    now = now or datetime.now(UTC)
    gathered = (
        list(catalog.search(query))
        + list(hidden_capabilities.search(query))
        + list(world_discovery.search(query))
    )

    deduped: dict[str, DiscoveryFact] = {}
    for fact in gathered:
        key = _digest(f"{fact.title}|{fact.text}")
        prior = deduped.get(key)
        if prior is None or fact.confidence > prior.confidence:
            trust: Trust = "stale" if _is_stale(fact.provenance, now) else fact.provenance.trust
            deduped[key] = DiscoveryFact(
                title=fact.title,
                text=fact.text,
                confidence=fact.confidence,
                provenance=Provenance(**{**asdict(fact.provenance), "trust": trust}),
            )

    trust_rank = {"verified": 3, "derived": 2, "stale": 1, "unknown": 0}

    def _sort_key(item: DiscoveryFact):
        return (trust_rank.get(item.provenance.trust, 0), item.confidence)

    # Diversity: at least one best fact per source_kind when present, then fill to 8.
    by_kind: dict[str, list[DiscoveryFact]] = {}
    for fact in deduped.values():
        by_kind.setdefault(fact.provenance.source_kind, []).append(fact)

    selected: list[DiscoveryFact] = []
    seen_keys: set[str] = set()
    for kind in ("catalog", "manifest", "journal", "world_discovery"):
        pool = sorted(by_kind.get(kind, []), key=_sort_key, reverse=True)
        if not pool:
            continue
        top = pool[0]
        key = _digest(f"{top.title}|{top.text}")
        selected.append(top)
        seen_keys.add(key)

    remainder = sorted(
        (f for f in deduped.values() if _digest(f"{f.title}|{f.text}") not in seen_keys),
        key=_sort_key,
        reverse=True,
    )
    for fact in remainder:
        if len(selected) >= 8:
            break
        selected.append(fact)

    facts = tuple(sorted(selected, key=_sort_key, reverse=True)[:8])

    if not facts:
        return DiscoveryReply(
            text="برای این پرسش، شاهد قابل‌اتکا در منابع Discovery پیدا نشد.",
            facts=(),
            generated_at=now.isoformat(),
            evidence_level="STRUCTURAL",
            limitations=("UNKNOWN: no evidence-backed discovery fact",),
        )

    lines = ["آنچه اختاپوس با شواهد فعلی می‌شناسد:"]
    for item in facts:
        lines.append(
            f"- {item.title}: {item.text} "
            f"[{item.provenance.source_kind}; {item.provenance.trust}; "
            f"confidence={item.confidence:.2f}]"
        )
    lines.append("")
    lines.append("برای جزئیات شواهد، «Sources / شواهد» را باز کن.")

    limitations = tuple(
        f"{item.title}: source={item.provenance.path}, "
        f"trust={item.provenance.trust}, digest={item.provenance.content_digest}"
        for item in facts
    )

    return DiscoveryReply(
        text="\n".join(lines),
        facts=facts,
        generated_at=now.isoformat(),
        evidence_level="SHADOW",
        limitations=limitations,
    )
