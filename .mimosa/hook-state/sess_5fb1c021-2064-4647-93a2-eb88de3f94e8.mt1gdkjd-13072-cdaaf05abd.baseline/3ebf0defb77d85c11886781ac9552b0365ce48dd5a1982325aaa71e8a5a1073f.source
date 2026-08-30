"""Whether an image may leave this board at all.

Separate from `consent.py` on purpose. Consent answers *may this be
published* — a question about the people in it. This answers *may these bytes
be handed to a third party's model* — a question about the content, and one
that consent cannot make true.

    a restricted collection never leaves, whatever anybody agreed to

That is structural rather than a policy. There is no setting that opens it,
no consent that overrides it, and no flag that turns it off. The gate has no
parameter that could say yes, because a parameter that could say yes is a
parameter that will one day be set.

Two reasons, and either alone is sufficient: nearly every model provider's
terms forbid it, and leaving it to somebody's memory means one day somebody
forgets.

`sensitivity` defaults to restricted everywhere it appears. Becoming general
is an explicit act. With a fact absent, stay in the most cautious state — the
same rule as every other gap in this project.

Kernel purity: no clock, no I/O, no provider names.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from .errors import FailClosedError


class Sensitivity(enum.Enum):
    """Deliberately two values.

    A third — "ask me" — would be a setting, and a setting is the thing this
    module exists to not have.
    """

    RESTRICTED = "restricted"    # the default, always
    GENERAL = "general"

    @classmethod
    def of(cls, raw: object) -> "Sensitivity":
        """Read a stored value, treating anything unrecognised as restricted.

        `None` included, and that matters: a column added later as nullable
        leaves existing rows NULL, and NULL is neither value. Anything that
        is not exactly "general" is restricted — so a typo, a migration gap
        or a future third value all fail towards not sending.
        """
        return cls.GENERAL if raw == "general" else cls.RESTRICTED


@dataclass(frozen=True)
class Collection:
    collection_id: str
    label: str
    genre: str
    sensitivity: Sensitivity


@dataclass(frozen=True)
class Verdict:
    allowed: bool
    rule: str

    def __bool__(self) -> bool:
        return self.allowed


# Named so a refusal in a log says which rule refused, not merely that
# something did.
RULE_RESTRICTED = "advisor:restricted-never-leaves"
RULE_NO_COLLECTION = "advisor:no-collection-declared"
RULE_ALLOWED = "advisor:general-collection"


def may_send_image(collection: Collection | None) -> Verdict:
    """May the pixels of this collection be sent to an outside model?

    Takes no consent argument, and that absence is the design. Consent is
    about people agreeing to be published; it says nothing about handing
    bytes to a third party, and accepting it here would let a caller believe
    one had bought the other.
    """
    if collection is None:
        # "Nobody said which collection this is" is not "it is a safe one".
        return Verdict(False, RULE_NO_COLLECTION)
    if collection.sensitivity is not Sensitivity.GENERAL:
        return Verdict(False, RULE_RESTRICTED)
    return Verdict(True, RULE_ALLOWED)


def assert_no_pixels(payload: object) -> None:
    """Refuse anything that looks like image bytes on the tier-0 path.

    Tier 0 sends numbers and labels. This is the structural half of that
    promise: the extraction layer cannot pass an image because this refuses
    the shapes an image arrives in, rather than because the code happens not
    to put one there today.
    """
    if isinstance(payload, (bytes, bytearray, memoryview)):
        raise FailClosedError("tier-0 advisor input may not contain bytes")
    if isinstance(payload, str) and payload.startswith("data:"):
        raise FailClosedError("tier-0 advisor input may not contain a data URL")
    if isinstance(payload, dict):
        for key, value in payload.items():
            assert_no_pixels(key)
            assert_no_pixels(value)
    elif isinstance(payload, (list, tuple, set, frozenset)):
        for item in payload:
            assert_no_pixels(item)
