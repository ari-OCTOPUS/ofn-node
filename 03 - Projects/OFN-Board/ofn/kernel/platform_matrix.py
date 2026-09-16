"""Platform policy matrix — what each platform will accept, as a screen.

This is the structural half of "is this caption allowed on this platform?".
It runs *before* the outbox: a variant that fails the screen never becomes
a candidate for publishing, so the outbox never has to refuse it and the
owner never sees a publish attempt that was doomed.

The rules and the marker vocabularies are data, not code. The kernel must
not know which brands exist (the kernel purity test enforces this), and a
brand name like a subscription platform is exactly the kind of name that
rule exists to keep out. So this module ships an *empty* default matrix
and exposes `screen` + `load_matrix_from_rules`; the actual platform keys,
framing vocabularies, and adult-link markers are supplied by the adapter
layer from data files. The kernel decides the *shape* of a screen; the
data supplies the *content*.

What `screen` refuses, and why each refusal is structural rather than
advisory:

  - unknown platform → refuse. "We have no policy" is not "anything goes".
  - targets minors → refuse, unconditionally and first.
  - sensitivity != general → refuse. Restricted never leaves, full stop;
    this duplicates advisor_gate on purpose. Defence in depth.
  - caption empty → refuse. A silent post is a bug.
  - blocked framing → refuse, by exact match.
  - framing not in allowlist → refuse, when the platform has one.
  - direct adult link on a platform that forbids it → refuse.
  - sexual-solicitation markers on a wellness-only platform → refuse.

The marker lists (when supplied) are meant to be conservative and
over-broad. A caption refused here costs a rewrite; a caption that leaks
costs an account. The asymmetry is the whole point.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class ScreenVerdict:
    ok: bool
    rule: str
    reasons: tuple[str, ...] = ()
    risk: str = "RED"


@dataclass(frozen=True)
class PlatformRule:
    """One platform's policy, as data.

    `direct_adult_link_allowed` may be a bool or a sentinel string like
    "private_opt_in_only" / "subreddit_specific" — the screen treats any
    non-False value as "allowed, subject to other checks", because the
    nuance lives in `adult_policy` and the framing allowlist.

    `adult_link_markers` and `solicitation_markers` are per-rule so a
    platform with no adult policy does not need to carry a vocabulary it
    never uses. Empty tuples are the default and mean "no sniffing".
    """

    name: str
    layer: str
    risk: str
    adult_policy: str
    direct_adult_link_allowed: bool | str
    caption_max: int | None = None
    allowed_framing: tuple[str, ...] = ()
    blocked_framing: tuple[str, ...] = ()
    adult_link_markers: tuple[str, ...] = ()
    solicitation_markers: tuple[str, ...] = ()


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    if not markers:
        return False
    low = text.lower()
    return any(m in low for m in markers)


class PlatformMatrix:
    """Holds the rules and applies them. Stateless beyond the rules dict."""

    def __init__(self, rules: Mapping[str, PlatformRule]):
        self.rules = dict(rules)

    def screen(
        self,
        *,
        platform: str,
        caption: str,
        framing: str,
        sensitivity: str,
        adult_label: bool = False,
        targets_minors: bool = False,
        has_direct_adult_link: bool | None = None,
    ) -> ScreenVerdict:
        rule = self.rules.get(platform)
        if rule is None:
            return ScreenVerdict(False, "platform:unknown", (platform,))

        # Minor targeting is refused first, unconditionally, regardless of
        # anything else in the context. This is the one rule that cannot be
        # argued with.
        if targets_minors:
            return ScreenVerdict(False, "safety:minor-targeting-denied",
                                 risk=rule.risk)

        # Restricted never leaves. This is advisor_gate's rule, restated here
        # so the screen is self-contained and the refusal names the right
        # module if it ever fires.
        if sensitivity != "general":
            return ScreenVerdict(False, "advisor:restricted-never-leaves",
                                 risk=rule.risk)

        if not caption.strip():
            return ScreenVerdict(False, "content:caption-empty", risk=rule.risk)

        if rule.caption_max is not None and len(caption) > rule.caption_max:
            return ScreenVerdict(
                False, "platform:caption-too-long",
                (str(len(caption)), str(rule.caption_max)), rule.risk,
            )

        if framing in rule.blocked_framing:
            return ScreenVerdict(False, "platform:blocked-framing",
                                 (framing,), rule.risk)

        if rule.allowed_framing and framing not in rule.allowed_framing:
            return ScreenVerdict(False, "platform:framing-not-allowed",
                                 (framing,), rule.risk)

        # Adult-link detection: caller may pass it explicitly (they know the
        # bio link), otherwise we sniff the caption using *this rule's*
        # markers — never a global list, because the kernel must not carry
        # brand names.
        if has_direct_adult_link is None:
            has_direct_adult_link = _contains_any(caption,
                                                  rule.adult_link_markers)
        if has_direct_adult_link and rule.direct_adult_link_allowed is False:
            return ScreenVerdict(False, "platform:direct-adult-link-blocked",
                                 risk=rule.risk)

        # Platforms that allow labeled adult still require the label.
        if rule.adult_policy == "allowed_labeled" and (
                framing == "adult_labeled" or has_direct_adult_link):
            if not adult_label:
                return ScreenVerdict(False, "platform:adult-label-required",
                                     risk=rule.risk)

        # Wellness-only platforms refuse any whiff of solicitation, using
        # their own per-rule vocabulary.
        if rule.adult_policy in {
                "wellness_only", "wellness_only_high_risk",
                "sexual_content_prohibited"}:
            if _contains_any(caption, rule.solicitation_markers) \
                    or framing == "adult_labeled":
                return ScreenVerdict(
                    False, "platform:sexual-solicitation-blocked",
                    risk=rule.risk)

        return ScreenVerdict(True, "platform:ok", risk=rule.risk)


def empty_matrix() -> PlatformMatrix:
    """An empty matrix, which refuses every platform as unknown.

    The real matrix is built by the adapter layer from data files
    (`data/platform_matrix.json`), which is where brand names and marker
    vocabularies are allowed to live. The kernel ships empty on purpose:
    it decides the shape of a screen, not the content.
    """
    return PlatformMatrix({})
