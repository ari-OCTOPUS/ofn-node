"""Redact identifying data before it leaves the node.

This is a choke point, not a filter you can opt out of: every prompt bound for
a third-party model passes through `scrub()` first. The provider on the other
end is an orchestrator that fans requests out to models it rents from other
vendors, so anything sent is disclosed to an unknown number of parties.

Design bias: over-redact. A partner's phone number reaching a third party is
unrecoverable; a slightly less specific prompt is merely worse output. So
every rule here is tuned to catch rather than to preserve, and the caller is
told exactly what was removed so a human can judge whether the request still
makes sense.

What this cannot do, stated plainly so nobody relies on it:
  * It cannot detect a name. "Sarah" is a name and a word.
  * It cannot detect a street address reliably across formats.
  * It cannot detect facts that identify someone only in combination.

So it is one layer, not the answer. The real protection is that RED actions —
which is what anything touching personal data is classified as — never reach
an external model without a human decision in the first place.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Pattern

# Ordered: the most specific patterns run first so a credit card is not
# partially eaten by the generic long-number rule.
_RULES: tuple[tuple[str, Pattern[str], str], ...] = (
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
     "[EMAIL]"),
    # Provider-style secrets. Caught early because a leaked key is the worst
    # single item on this list.
    ("secret", re.compile(r"\b(?:sk|pk|rk|api|key|token)[-_][A-Za-z0-9_\-]{16,}\b",
                          re.IGNORECASE), "[SECRET]"),
    ("bearer", re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}\b", re.IGNORECASE),
     "[SECRET]"),
    # 13-19 digits with optional separators — card-shaped.
    ("card", re.compile(r"\b(?:\d[ -]?){13,19}\b"), "[CARD]"),
    # Australian mobile / landline and generic international.
    ("phone", re.compile(
        r"(?<![\w.])(?:\+?61|0)[ -]?[２2-9](?:[ -]?\d){7,9}(?![\w.])"), "[PHONE]"),
    ("phone_intl", re.compile(r"(?<![\w.])\+\d{1,3}[ -]?(?:\d[ -]?){7,13}(?![\w.])"),
     "[PHONE]"),
    # AU business/tax numbers: 11 and 9 digits, commonly space-grouped.
    ("abn", re.compile(r"\b\d{2} ?\d{3} ?\d{3} ?\d{3}\b"), "[ABN]"),
    ("tfn", re.compile(r"\b\d{3} ?\d{3} ?\d{3}\b"), "[TFN]"),
    ("ip", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[IP]"),
    ("url_userinfo", re.compile(r"://[^/\s:@]+:[^/\s@]+@"), "://[REDACTED]@"),
)


@dataclass(frozen=True)
class ScrubResult:
    text: str
    findings: Mapping[str, int]

    @property
    def clean(self) -> bool:
        return not self.findings

    @property
    def summary(self) -> str:
        if self.clean:
            return "no identifying data found"
        parts = ", ".join(f"{n}x {k}" for k, n in sorted(self.findings.items()))
        return f"redacted: {parts}"


def scrub(text: str) -> ScrubResult:
    """Redact identifying data. Returns the cleaned text and what was removed.

    The count is per rule, not per unique value: two occurrences of the same
    email count as two, because the question being answered is "how much
    identifying material was in this prompt", not "how many people".
    """
    if not text:
        return ScrubResult("", {})
    out = text
    found: dict[str, int] = {}
    for name, pattern, replacement in _RULES:
        out, n = pattern.subn(replacement, out)
        if n:
            found[name] = found.get(name, 0) + n
    return ScrubResult(out, found)


def has_identifying_data(text: str) -> bool:
    """Cheap predicate for gates that only need a yes/no."""
    return not scrub(text).clean


def assert_clean(text: str) -> None:
    """Raise if anything identifying survived. For use immediately before an
    external call, as a belt-and-braces check on a caller that may have built
    its prompt after scrubbing."""
    result = scrub(text)
    if not result.clean:
        raise ValueError(
            f"refusing to transmit: prompt still contains {result.summary}")
