"""Whether the people in a piece of content have agreed to it being published.

This module exists because a boolean called `consent_confirmed` has the shape
of a control without being one. It cannot be audited six months later, it
cannot answer "which posts is this person in", and — worst — it makes
everybody feel the question has been handled.

So consent here is about a **person**, not about a post. A release is a
document somebody signed, covering named platforms, with a date it was signed
and possibly a date it stops counting. A post is publishable when every person
in it is covered right now.

Kernel purity: no clock, no I/O, no platform names, no business names. `now`
arrives as an argument and platforms arrive as opaque validated strings from a
pack, so adding a platform is a data change.

Two rules that are the whole point:

    nobody declared        →  refuse
    consent withdrawn      →  refuse, and no older document undoes it

The first is the `fleet.judge` pattern: *no baseline → UNKNOWN, never
healthy*. Here, "nobody said there is a person in this" is indistinguishable
from "nobody looked", and those must not be treated as agreement. An empty
list is the most common way for a check like this to pass by accident.

What this module deliberately does NOT do: it does not gate on *what kind* of
content something is. A release's scope is a set of platforms and nothing
more. Content-kind gating would need its own field, its own wording on the
signed document, and its own argument here — and a control that is claimed but
not implemented is worse than one that is absent, because people rely on it.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from .errors import FailClosedError

# A platform id, or a subject id, or a release id. Deliberately narrow: these
# end up in file paths, ledger payloads and URLs.
_ID = re.compile(r"^[a-z0-9]([a-z0-9_-]{0,62}[a-z0-9])?$")

# A signature dated in the future is not yet in force. On a board with no
# battery-backed clock the clock is as likely to be wrong as the document, so
# this is a small tolerance rather than a hard zero.
FUTURE_TOLERANCE_S = 60


class Refusal(enum.Enum):
    """Why publication is refused. One value per distinct human situation.

    These are for the operator and for the partner's screen. They never carry
    a person's real name — `Block` carries the subject id, and the label a
    person chose for themselves lives in the store, not here.
    """

    NO_SUBJECT_DECLARED = "no_subject_declared"
    NO_RELEASE = "no_release"
    NOT_YET_IN_FORCE = "not_yet_in_force"
    EXPIRED = "expired"
    REVOKED = "revoked"
    OUT_OF_SCOPE = "out_of_scope"


@dataclass(frozen=True)
class Subject:
    """Somebody who may appear in content.

    `display_label` is a label, not necessarily a legal name. The system never
    needs to know who somebody really is in order to honour their decision.
    """

    subject_id: str
    display_label: str

    def __post_init__(self) -> None:
        if not _ID.match(self.subject_id):
            raise FailClosedError(f"invalid subject id: {self.subject_id!r}")


@dataclass(frozen=True)
class Release:
    """A signed document, reduced to the facts a decision needs.

    The document itself is not here and is not in any database — only a
    reference to where it is kept and a hash of it, so that "the document we
    checked" and "the document on disk today" can be shown to be the same one.
    """

    release_id: str
    subject_id: str
    scope: frozenset[str]        # platform ids this document covers
    signed_at: int
    expires_at: int | None = None      # None = no expiry
    revoked_at: int | None = None      # withdrawal, and it does not come back

    def __post_init__(self) -> None:
        if not _ID.match(self.release_id):
            raise FailClosedError(f"invalid release id: {self.release_id!r}")
        if not _ID.match(self.subject_id):
            raise FailClosedError(f"invalid subject id: {self.subject_id!r}")


@dataclass(frozen=True)
class Block:
    """One person, and the reason they stop this from going out."""

    subject_id: str
    reason: Refusal


@dataclass(frozen=True)
class Verdict:
    allowed: bool
    blocks: tuple[Block, ...]
    why: str

    def __bool__(self) -> bool:
        return self.allowed


def parse_scope(text: str) -> frozenset[str]:
    """Turn the scope column of a signed document into a set of platforms.

    Separated by commas or whitespace. Anything that is not a well-formed
    platform id is dropped rather than raising, and dropping is safe here
    because an unrecognised token can then never match a platform and the
    release simply does not cover it.

    There is no wildcard, and adding one would be a mistake worth naming: a
    document that says "everywhere" is a document whose author could not have
    known where "everywhere" would be a year later.
    """
    out = set()
    for token in re.split(r"[,\s]+", (text or "").strip().lower()):
        if token and _ID.match(token):
            out.add(token)
    return frozenset(out)


def _latest_revocation(releases: Sequence[Release]) -> int | None:
    """When this person most recently withdrew, across all their documents."""
    stamps = [r.revoked_at for r in releases if r.revoked_at is not None]
    return max(stamps) if stamps else None


def _judge_one(subject_id: str, releases: Sequence[Release], *,
               platform: str, now_epoch_s: int) -> Refusal | None:
    """The reason this person blocks publication, or None if they do not.

    Withdrawal is handled by time rather than by flag. A revocation
    invalidates every document signed at or before it, and only a document
    signed strictly afterwards can count again. That is what makes withdrawal
    irreversible in the sense that matters: no older piece of paper can be
    produced later to undo it, but a person who changes their mind and signs
    again is not locked out for ever.
    """
    mine = [r for r in releases if r.subject_id == subject_id]
    if not mine:
        return Refusal.NO_RELEASE

    withdrew = _latest_revocation(mine)

    # Reasons are collected rather than returned on the first failure, so the
    # message names the nearest miss instead of whichever document happened to
    # be first in the list.
    seen: set[Refusal] = set()
    for r in mine:
        if r.revoked_at is not None:
            seen.add(Refusal.REVOKED)
            continue
        if withdrew is not None and r.signed_at <= withdrew:
            seen.add(Refusal.REVOKED)
            continue
        if r.signed_at > now_epoch_s + FUTURE_TOLERANCE_S:
            seen.add(Refusal.NOT_YET_IN_FORCE)
            continue
        if r.expires_at is not None and r.expires_at <= now_epoch_s:
            seen.add(Refusal.EXPIRED)
            continue
        if platform not in r.scope:
            seen.add(Refusal.OUT_OF_SCOPE)
            continue
        return None                      # this document covers it

    # Most specific first: a withdrawal is a decision, an expiry is a lapse,
    # and being out of scope is merely the wrong paperwork.
    for reason in (Refusal.REVOKED, Refusal.EXPIRED,
                   Refusal.NOT_YET_IN_FORCE, Refusal.OUT_OF_SCOPE):
        if reason in seen:
            return reason
    return Refusal.NO_RELEASE


def may_publish(subjects: Iterable[Subject], releases: Iterable[Release], *,
                platform: str, now_epoch_s: int) -> Verdict:
    """May this content go out to this platform, right now?

    Every person named in the content must be covered by a live release for
    this platform. The rules, in order:

        nobody declared              →  refuse
        a person with no release     →  refuse
        signed in the future         →  refuse
        expired                      →  refuse
        withdrawn                    →  refuse, and no older document undoes it
        scope does not name this platform →  refuse

    The verdict names every blocking person, not just the first. Fixing
    consent one refusal at a time, with a new publish attempt between each,
    is how a person gets missed.
    """
    if not _ID.match(platform or ""):
        raise FailClosedError(f"invalid platform id: {platform!r}")

    people = list(subjects)
    if not people:
        # The rule this module exists for. "Nobody said there is a person in
        # this" and "nobody looked" are the same bytes.
        return Verdict(False, (), "no subject has been declared for this "
                                  "content — that is not the same as there "
                                  "being nobody in it")

    docs = list(releases)
    blocks = []
    for person in people:
        reason = _judge_one(person.subject_id, docs,
                            platform=platform, now_epoch_s=now_epoch_s)
        if reason is not None:
            blocks.append(Block(person.subject_id, reason))

    if blocks:
        return Verdict(False, tuple(blocks),
                       f"{len(blocks)} of {len(people)} people are not "
                       f"cleared for {platform}")
    return Verdict(True, (), f"all {len(people)} cleared for {platform}")


def subjects_needing_attention(
        subjects: Iterable[Subject], releases: Iterable[Release], *,
        platform: str, now_epoch_s: int) -> Mapping[str, Refusal]:
    """The same judgement, as a map, for a screen that lists what is missing.

    Separate from `may_publish` on purpose: a caller that wants to *show* the
    gaps must not be tempted to rebuild the decision out of them.
    """
    docs = list(releases)
    return {s.subject_id: reason for s in subjects
            if (reason := _judge_one(s.subject_id, docs, platform=platform,
                                     now_epoch_s=now_epoch_s)) is not None}
