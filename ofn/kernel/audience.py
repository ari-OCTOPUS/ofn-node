"""Subscribers, money, and how much of the audience is actually hers.

Three questions this answers, none of which needs a model and none of which
any dashboard asks:

    how many of the people who have HAD a first week bought in it
    who has gone quiet
    is the share of the audience she owns going up or down

The first has a trap in it worth naming, because getting it wrong produces a
number that looks like failing performance and is really just growth: a
subscriber who joined yesterday has not *failed* to convert in seven days,
they have not had seven days. Counting them in the denominator makes the rate
fall every time somebody new arrives. So conversion is measured over the
cohort that is old enough to be measured, and the rest are reported
separately as "too early to say".

Money is integer minor units everywhere. `0.1 + 0.2 != 0.3`, and money is the
one place that error is eventually visible — not in one row, but in a year's
total.

Kernel purity: no clock, no I/O, no platform names. Channels are opaque
strings from the store.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

DAY = 86_400

# The window the 2026 figures are about: whether a new subscriber buys
# anything in their first week is the strongest single predictor there is.
FIRST_WINDOW_DAYS = 7

# Longer than this without a message is the "12 people are on day five and
# nobody has written to them" case — the one with the highest value and no
# risk at all, because a person sends it.
DEFAULT_QUIET_DAYS = 3


class Ownership(enum.Enum):
    """How much of the audience survives losing a platform account.

    The order matters and is the whole point: a follower count is not a
    smaller version of a mailing list, it is a different kind of thing.
    """

    OWNED = "owned"            # a way to reach them that nobody can revoke
    SEMI_OWNED = "semi_owned"  # somebody else's platform, but exportable
    RENTED = "rented"          # gone the day the account is


class RevenueKind(enum.Enum):
    SUBSCRIPTION = "subscription"
    PPV = "ppv"
    TIP = "tip"
    CUSTOM = "custom"


@dataclass(frozen=True)
class Subscriber:
    sub_id: str
    first_seen_at: int
    channel_source: str
    status: str = "active"
    last_contact_at: int | None = None
    first_purchase_at: int | None = None
    lifetime_minor: int = 0

    def days_alive(self, now_epoch_s: int) -> int:
        return max(0, (now_epoch_s - self.first_seen_at) // DAY)

    def days_since_contact(self, now_epoch_s: int) -> int | None:
        """None means nobody has ever written to them.

        Deliberately not "a very large number": never-contacted and
        contacted-long-ago are different situations, and collapsing them
        hides the one that is easiest to fix.
        """
        if self.last_contact_at is None:
            return None
        return max(0, (now_epoch_s - self.last_contact_at) // DAY)

    def had_first_window(self, now_epoch_s: int,
                         window_days: int = FIRST_WINDOW_DAYS) -> bool:
        return self.days_alive(now_epoch_s) >= window_days

    def converted_in_window(self,
                            window_days: int = FIRST_WINDOW_DAYS) -> bool:
        if self.first_purchase_at is None:
            return False
        return (self.first_purchase_at - self.first_seen_at) <= window_days * DAY


@dataclass(frozen=True)
class Conversion:
    """First-window conversion, with the part that cannot be judged kept
    separate rather than folded in."""

    channel: str
    matured: int          # old enough to be measured
    converted: int
    too_early: int        # joined recently; not a failure, just not yet

    @property
    def rate(self) -> float | None:
        """None when nothing has matured yet — not zero.

        Zero is a measurement. None is the absence of one, and the whole
        project's rule is that an absent fact does not become a number.
        """
        return None if self.matured == 0 else self.converted / self.matured


def first_window_conversion(
        subscribers: Iterable[Subscriber], *, now_epoch_s: int,
        window_days: int = FIRST_WINDOW_DAYS) -> Mapping[str, Conversion]:
    """Per acquisition channel, because that is the decision it feeds.

    A blended rate cannot tell her to stop spending on the channel that
    brings people who never buy.
    """
    buckets: dict[str, list[Subscriber]] = {}
    for sub in subscribers:
        buckets.setdefault(sub.channel_source, []).append(sub)

    out: dict[str, Conversion] = {}
    for channel, subs in buckets.items():
        matured = [s for s in subs if s.had_first_window(now_epoch_s, window_days)]
        out[channel] = Conversion(
            channel=channel,
            matured=len(matured),
            converted=sum(1 for s in matured if s.converted_in_window(window_days)),
            too_early=len(subs) - len(matured))
    return out


@dataclass(frozen=True)
class Quiet:
    sub_id: str
    days_alive: int
    days_since_contact: int | None      # None = never contacted


def gone_quiet(subscribers: Iterable[Subscriber], *, now_epoch_s: int,
               quiet_days: int = DEFAULT_QUIET_DAYS) -> Sequence[Quiet]:
    """Who is inside their first window and has not been written to.

    Sorted by how long they have been waiting, longest first, because that is
    the order somebody with ten minutes should work through.
    """
    out = []
    for sub in subscribers:
        if sub.status != "active":
            continue
        since = sub.days_since_contact(now_epoch_s)
        if since is None or since >= quiet_days:
            out.append(Quiet(sub.sub_id, sub.days_alive(now_epoch_s), since))
    # Never-contacted first, then longest silence.
    return sorted(out, key=lambda q: (q.days_since_contact is not None,
                                      -(q.days_since_contact or 0)))


@dataclass(frozen=True)
class Snapshot:
    taken_at: int
    channel: str
    kind: Ownership
    count: int


def ownership_ratio(snapshots: Iterable[Snapshot]) -> float | None:
    """(owned + semi_owned) / everything, at one moment.

    None when there is nobody at all — a business with no audience does not
    have a bad ownership ratio, it has no ratio.
    """
    owned = total = 0
    for snap in snapshots:
        total += snap.count
        if snap.kind in (Ownership.OWNED, Ownership.SEMI_OWNED):
            owned += snap.count
    return None if total == 0 else owned / total


@dataclass(frozen=True)
class Trend:
    earlier: float | None
    later: float | None

    @property
    def direction(self) -> str:
        """`up`, `down`, `flat`, or `unknown`.

        `unknown` is a real answer here. Two points, one of which does not
        exist, is not a trend — and reporting it as flat would be inventing
        the missing one.
        """
        if self.earlier is None or self.later is None:
            return "unknown"
        if abs(self.later - self.earlier) < 1e-9:
            return "flat"
        return "up" if self.later > self.earlier else "down"

    @property
    def worth_saying(self) -> bool:
        """Growth on rented ground is the failure that looks like success:
        every count rises while the share she owns falls."""
        return self.direction == "down"


def ownership_trend(series: Sequence[Snapshot], *, split_at: int) -> Trend:
    """The ratio before and after a moment.

    A trend rather than a reading, because the number on its own says almost
    nothing: 20% owned and rising is a business getting sturdier, and 40% and
    falling is one getting more fragile.
    """
    before = [s for s in series if s.taken_at < split_at]
    after = [s for s in series if s.taken_at >= split_at]
    return Trend(ownership_ratio(before), ownership_ratio(after))


@dataclass(frozen=True)
class ChannelValue:
    channel: str
    subscribers: int
    lifetime_minor: int
    acquisition_cost_minor: int | None

    @property
    def average_lifetime_minor(self) -> int | None:
        if self.subscribers == 0:
            return None
        return self.lifetime_minor // self.subscribers

    @property
    def ratio(self) -> float | None:
        """Lifetime value against what it cost to acquire.

        None when nobody has said what acquisition cost — which is the normal
        case, and must stay visibly absent rather than defaulting to zero. A
        zero cost makes every channel look infinitely profitable, and it is
        the most tempting default in this whole file.
        """
        cost = self.acquisition_cost_minor
        avg = self.average_lifetime_minor
        if cost is None or not cost or avg is None:
            return None
        return avg / cost


def value_by_channel(
        subscribers: Iterable[Subscriber], *,
        acquisition_cost_minor: Mapping[str, int] | None = None
        ) -> Mapping[str, ChannelValue]:
    costs = dict(acquisition_cost_minor or {})
    buckets: dict[str, list[Subscriber]] = {}
    for sub in subscribers:
        buckets.setdefault(sub.channel_source, []).append(sub)
    return {
        channel: ChannelValue(
            channel=channel,
            subscribers=len(subs),
            lifetime_minor=sum(s.lifetime_minor for s in subs),
            acquisition_cost_minor=costs.get(channel))
        for channel, subs in buckets.items()
    }


@dataclass(frozen=True)
class Concentration:
    """How much of the money comes from how few people.

    An average hides this completely, and for this business the distribution
    is the whole story: a handful of people are most of the income. "Average
    subscriber value is $40" describes nobody when three people are half the
    month — and it is the number that gets used to decide what a subscriber
    is worth, and therefore what one is worth acquiring.

    Same shape as the cohort trap, moved onto money: a figure computed over
    everybody, reported as if it described anybody.
    """

    total_minor: int
    payers: int
    silent: int                 # counted, never averaged away
    top_share: float | None     # what the biggest few are, of everything
    top_n: int

    @property
    def is_skewed(self) -> bool:
        """Whether the average is safe to say out loud.

        The threshold is deliberate rather than tuned: when a minority is
        more than half the money, the mean is describing a person who does
        not exist.
        """
        return self.top_share is not None and self.top_share > 0.5

    @property
    def mean_minor(self) -> int | None:
        """Only offered when it is not misleading.

        Refusing to compute it when the distribution is skewed is the point.
        A number that is available gets used, and a caller who has to reach
        for `top_share` instead has been told something true.
        """
        if self.payers == 0 or self.is_skewed:
            return None
        return self.total_minor // self.payers


def concentration(subscribers: Iterable[Subscriber], *,
                  top_n: int = 3) -> Concentration:
    """The distribution, as the shape that actually drives a decision.

    People who have never paid are counted separately rather than folded in
    as zeroes. Both facts matter and they are different facts: "forty people
    have never bought anything" is an action, and averaging them into the
    value of a subscriber is how that action disappears.
    """
    amounts = sorted((s.lifetime_minor for s in subscribers), reverse=True)
    paying = [a for a in amounts if a > 0]
    total = sum(paying)
    top = sum(paying[:top_n])
    return Concentration(
        total_minor=total,
        payers=len(paying),
        silent=len(amounts) - len(paying),
        top_share=None if total == 0 else top / total,
        top_n=min(top_n, len(paying)))


def revenue_mix(totals: Mapping[RevenueKind, int]) -> Mapping[str, float] | None:
    """What share each kind of income is, once there is any.

    None while everything is zero. The 2026 figures say PPV is 50-70% of a
    working creator's income and subscriptions 15-30% — but those are
    somebody else's numbers, and this returns hers or nothing.
    """
    total = sum(totals.values())
    if total <= 0:
        return None
    return {kind.value: amount / total for kind, amount in totals.items()}
