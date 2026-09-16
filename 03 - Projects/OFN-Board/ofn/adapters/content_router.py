"""Content router — one draft, many platform-shaped variants.

A draft is what the partner made: a caption seed, a sensitivity, a style,
some media. A *variant* is that draft shaped for one platform: caption
trimmed or reframed, hashtags chosen, an idempotency key minted, and —
critically — a platform screen verdict attached. The router never
publishes. It produces candidates for the outbox, and the outbox is the
only door out.

The router is deliberately dumb about caption *craft*. It does not write
copy; it applies mechanical safety (trim to the platform's limit, refuse
what the platform forbids) and leaves the actual words to the partner and
the model. A `caption_seed` is expected to already be a finished caption;
the router only adapts it. This keeps the router testable without a model
and keeps the model out of the safety-critical path.

Idempotency keys are derived from (draft, platform, caption) so a retry of
the *same* variant collides with itself in the outbox and is refused, while
a genuinely different variant (different caption after a rewrite) gets a
new key and may proceed. This is the structural defence against the most
common 2026 agent failure: a network timeout that was actually a success,
retried into a double post.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable

from ofn.kernel.platform_matrix import PlatformMatrix, ScreenVerdict


@dataclass(frozen=True)
class DraftForRouting:
    """What the partner made, in routing shape.

    `caption_seed` is the partner's caption as written. `sensitivity` is
    advisor_gate's verdict as a string ("general" | "restricted"). The
    router does not re-derive either.
    """

    draft_id: str
    caption_seed: str
    sensitivity: str          # "general" | "restricted"
    style_id: str
    media_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class RoutedVariant:
    """One draft, shaped for one platform, with its screen verdict.

    A variant whose `screen.ok` is False is still returned — the caller
    (the outbox intake) needs to see *why* it was refused, and the owner
    needs to see that nine platforms were tried and seven refused. A
    router that silently dropped refusals would look like a router that
    found three places to post.
    """

    draft_id: str
    platform: str
    caption: str
    hashtags: tuple[str, ...]
    framing: str
    adult_label: bool
    screen: ScreenVerdict
    idempotency_key: str


def idempotency_key(draft_id: str, platform: str, caption: str) -> str:
    """Stable key for (draft, platform, caption).

    Same triple → same key → a retry collides with itself. Different
    caption (after a rewrite) → different key → may proceed. This is what
    makes retries safe rather than duplicating.
    """
    return sha256(f"{draft_id}|{platform}|{caption}".encode("utf-8")).hexdigest()


def safe_caption(seed: str, platform: str, matrix: PlatformMatrix) -> str:
    """Trim a caption to its platform's limit, never inventing content.

    The router does not write copy. If a seed is longer than a platform
    allows, it is truncated to the limit — *not* rewritten, because a
    rewrite is a model decision and the safety path stays model-free.
    Truncation can produce a worse caption; it cannot produce a less safe
    one, which is the property that matters here.
    """
    rule = matrix.rules.get(platform)
    base = seed.strip()
    if rule is not None and rule.caption_max is not None:
        return base[:rule.caption_max]
    return base


def default_hashtags(framing: str) -> tuple[str, ...]:
    """A minimal, wellness-framed default hashtag set.

    These are deliberately bland and platform-safe. The real hashtag
    strategy is a model/partner concern and lives elsewhere; this exists
    so a variant is never empty of hashtags when none were provided.
    """
    if framing == "adult_labeled":
        return ("#adult", "#consensual")
    return ("#footcare", "#beautyroutine", "#softlight")


class ContentRouter:
    """Turns one draft into N variants, one per requested platform."""

    def __init__(self, matrix: PlatformMatrix):
        self.matrix = matrix

    def route(
        self,
        draft: DraftForRouting,
        platforms: Iterable[str],
        *,
        framing: str,
        hashtags: tuple[str, ...] | None = None,
        adult_label: bool = False,
        targets_minors: bool = False,
    ) -> list[RoutedVariant]:
        variants: list[RoutedVariant] = []
        tags = hashtags if hashtags is not None else default_hashtags(framing)
        for platform in platforms:
            caption = safe_caption(draft.caption_seed, platform, self.matrix)
            verdict = self.matrix.screen(
                platform=platform,
                caption=caption,
                framing=framing,
                sensitivity=draft.sensitivity,
                adult_label=adult_label,
                targets_minors=targets_minors,
            )
            variants.append(RoutedVariant(
                draft_id=draft.draft_id,
                platform=platform,
                caption=caption,
                hashtags=tags,
                framing=framing,
                adult_label=adult_label,
                screen=verdict,
                idempotency_key=idempotency_key(
                    draft.draft_id, platform, caption),
            ))
        return variants
