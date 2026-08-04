"""What may be shown to a model, and the shape of what it may say back.

The promise is that no pixel leaves this board. A promise kept by everybody
remembering is not kept; this file keeps it with a type.

`Evidence` can hold a number, or a label from a set the pack declared. That
is all it can hold. Bytes, data URLs, long free text and unknown labels are
refused at construction, so the extraction layer cannot carry an image — not
because the code today does not put one there, but because there is nowhere
to put one. A bug in a caller cannot invent a field.

The other half is provenance. A suggestion without one cannot be argued
with:

    «تک‌سوژه با نور پخش دو برابر بیشتر نگه می‌دارد»
        از ۳۸ پست خودت، در ۹۰ روز        ← قابل رد کردن
    «مخاطب شما از نظر روان‌شناختی به X پاسخ می‌دهد»
                                          ← نه قابل اثبات، نه قابل ابطال

Only the first shape can exist here: a `Finding` without evidence is refused.

Kernel purity: no clock, no I/O, no model, no platform names.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from .errors import FailClosedError

# A label is a short, closed-vocabulary token she or the pack chose:
# "single-subject", "soft-light". Not a sentence, and not a caption — a
# caption is content, and content is what this file exists to keep in.
_LABEL = re.compile(r"^[a-z0-9]([a-z0-9_-]{0,38}[a-z0-9])?$")

# Enough to name a thing, far too little to smuggle one. A field that could
# hold a base64 image would make every other rule here decorative.
MAX_LABEL_LEN = 40


class Disposition(enum.Enum):
    """A ratchet: opinions harden, they do not soften.

    Without it the advisor offers the same three suggestions every week and
    she stops opening it after the third.
    """

    UNSEEN = "unseen"
    OFFERED = "offered"
    ACCEPTED = "accepted"
    REJECTED_SOFT = "rejected_soft"    # not now
    REJECTED_HARD = "rejected_hard"    # never again

    def is_final(self) -> bool:
        return self is Disposition.REJECTED_HARD


@dataclass(frozen=True)
class Evidence:
    """One measured thing. A number, or a count of a label.

    Constructed only through the validating path, so the guarantee holds for
    every instance rather than for the ones somebody remembered to check.
    """

    name: str
    value: float
    unit: str = ""
    label: str = ""

    def __post_init__(self) -> None:
        for field_name, text in (("name", self.name), ("unit", self.unit),
                                 ("label", self.label)):
            if text and not _LABEL.match(text):
                raise FailClosedError(
                    f"evidence {field_name} must be a short label: {text!r}")
        if not _LABEL.match(self.name):
            raise FailClosedError("evidence needs a name")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise FailClosedError(
                f"evidence value must be a number: {self.value!r}")


@dataclass(frozen=True)
class Provenance:
    """Where a claim came from. Both numbers, both required.

    "From 38 posts over 90 days" is checkable. "Based on your data" is a
    sentence that sounds like one.
    """

    sample: int
    window_days: int

    def __post_init__(self) -> None:
        for name, n in (("sample", self.sample),
                        ("window_days", self.window_days)):
            if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
                raise FailClosedError(f"provenance {name} must be positive")

    def render(self) -> str:
        return f"از {self.sample} پست، در {self.window_days} روز"


@dataclass(frozen=True)
class Finding:
    """One thing worth saying, with what it rests on."""

    key: str
    claim: str
    evidence: Sequence[Evidence]
    provenance: Provenance

    def __post_init__(self) -> None:
        if not _LABEL.match(self.key or ""):
            raise FailClosedError(f"finding key must be a label: {self.key!r}")
        if not (self.claim or "").strip():
            raise FailClosedError("a finding must say something")
        if not self.evidence:
            # The rule this class exists for. A claim with nothing under it
            # cannot be argued with, and a suggestion that cannot be rejected
            # is not advice.
            raise FailClosedError(
                f"finding {self.key!r} has no evidence — refused")


def extract(raw: Mapping[str, object], *,
            allowed: Iterable[str]) -> tuple[Evidence, ...]:
    """Turn measurements into the only shape that may travel.

    Whitelisted by name: a field the pack did not declare does not become
    evidence, however harmless it looks. The alternative — blacklisting what
    must not travel — needs somebody to have thought of every kind of thing
    that must not travel.
    """
    permitted = set(allowed)
    out = []
    for name, value in raw.items():
        if name not in permitted:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            # Not an error: a measurement that is not a number is simply not
            # evidence. Raising here would let one odd row stop a whole
            # weekly summary.
            continue
        out.append(Evidence(name=name, value=float(value)))
    return tuple(out)


@dataclass
class Memory:
    """What has already been offered, and how it landed."""

    _notes: dict[str, Disposition] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self._notes is None:
            self._notes = {}

    def disposition(self, key: str) -> Disposition:
        return self._notes.get(key, Disposition.UNSEEN)

    def remember(self, key: str, disposition: Disposition) -> None:
        """The ratchet. A hard rejection is never overwritten.

        Softening it would mean a suggestion she has already said "never" to
        comes back — which is exactly the behaviour that makes somebody stop
        opening a tool.
        """
        if self.disposition(key).is_final():
            return
        self._notes[key] = disposition

    def may_offer(self, key: str) -> bool:
        return not self.disposition(key).is_final()

    def filter(self, findings: Iterable[Finding]) -> tuple[Finding, ...]:
        return tuple(f for f in findings if self.may_offer(f.key))
