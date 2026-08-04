"""Who to write to, and what a message to them would say.

Two deliberate absences shape this file.

**Nothing is stored.** A draft is computed when a screen asks for it and
exists nowhere afterwards. That is what makes automatic sending impossible by
construction rather than merely switched off: there is no table for a sender
to drain, no row to mark as pending, and no queue that a future flag could
point at. D-13 deleted that feature rather than deferring it, and a deferred
feature leaves a shape behind — this one leaves none.

**No model is involved.** The valuable part is not the prose, it is knowing
that twelve people are on day five and nobody has written to them. That is
arithmetic, it is free, and it is available the day the first subscriber
arrives. A model can improve wording later; it cannot supply the fact.

What comes out is text for a person to read, adjust and send. The tone is
hers — a template that sounds like the tool is a template she will rewrite
every time, which costs more than writing it herself.

Kernel purity: no clock, no I/O, no platform names.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Iterable, Sequence

from .audience import DAY, FIRST_WINDOW_DAYS, Subscriber, gone_quiet


class Moment(enum.Enum):
    """Why this person is on the list. The reason changes what to say."""

    NEVER_GREETED = "never_greeted"      # arrived, nobody has said anything
    INSIDE_FIRST_WEEK = "inside_first_week"   # the window that decides churn
    GONE_QUIET = "gone_quiet"            # was talked to, then stopped
    NO_PURCHASE_YET = "no_purchase_yet"  # past the window, never bought


@dataclass(frozen=True)
class Draft:
    """One suggested message. Text, and why it is being suggested."""

    sub_id: str
    moment: Moment
    days_alive: int
    text: str

    @property
    def is_editable_by_a_person(self) -> bool:
        """Always true, and stated as a property so the answer is in the
        type rather than in a habit: nothing here sends anything."""
        return True


# Written plainly, in the second person, with nothing in them that only a
# tool would say. Each leaves the specific part to her — a template that
# fills in every blank is one that sounds filled in.
_TEXT = {
    Moment.NEVER_GREETED: (
        "سلام! ممنون که اومدی 🙏\n"
        "اگه چیز خاصی دوست داری ببینی بگو — همین اول کار راحت‌تره."
    ),
    Moment.INSIDE_FIRST_WEEK: (
        "سلام، چند روزه اومدی و نپرسیدم اوضاع چطوره.\n"
        "چیزی هست که دنبالش بودی و پیدا نکردی؟"
    ),
    Moment.GONE_QUIET: (
        "سلام، مدتی بی‌خبر بودیم.\n"
        "چیز تازه‌ای گذاشتم — اگه دوست داشتی نگاه کن."
    ),
    Moment.NO_PURCHASE_YET: (
        "سلام! دیدم مدتیه هستی.\n"
        "اگه چیزی خواستی که ندیدی، بگو — شاید بتونم درستش کنم."
    ),
}


def moment_for(sub: Subscriber, *, now_epoch_s: int,
               window_days: int = FIRST_WINDOW_DAYS) -> Moment | None:
    """Why this person needs a message, or None if they do not.

    Order matters and is not arbitrary: somebody nobody has ever greeted is
    a different situation from somebody who has gone quiet, and the first
    is both more urgent and easier to fix. Checking "quiet" first would
    label every new arrival as quiet and bury the ones who were never
    spoken to at all.
    """
    if sub.status != "active":
        return None
    days = sub.days_alive(now_epoch_s)
    if sub.last_contact_at is None:
        return Moment.NEVER_GREETED
    if days <= window_days:
        return Moment.INSIDE_FIRST_WEEK
    since = sub.days_since_contact(now_epoch_s)
    if since is not None and since >= 14:
        return Moment.GONE_QUIET
    if sub.first_purchase_at is None and days > window_days:
        return Moment.NO_PURCHASE_YET
    return None


def drafts_for(subscribers: Iterable[Subscriber], *, now_epoch_s: int,
               quiet_days: int = 3, limit: int = 10) -> Sequence[Draft]:
    """The list, in the order somebody with ten minutes should work through.

    `limit` is a kindness rather than a performance measure. A list of two
    hundred is a list nobody starts, and the first ten are where nearly all
    of the value is — the people inside their first week.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")

    waiting = {q.sub_id for q in gone_quiet(subscribers, now_epoch_s=now_epoch_s,
                                            quiet_days=quiet_days)}
    out: list[Draft] = []
    for sub in subscribers:
        if sub.sub_id not in waiting:
            continue
        moment = moment_for(sub, now_epoch_s=now_epoch_s)
        if moment is None:
            continue
        out.append(Draft(sub_id=sub.sub_id, moment=moment,
                         days_alive=sub.days_alive(now_epoch_s),
                         text=_TEXT[moment]))

    # Never-greeted first, then whoever has been waiting longest. Somebody
    # who has never had a word is the cheapest thing on this list to fix.
    order = {Moment.NEVER_GREETED: 0, Moment.INSIDE_FIRST_WEEK: 1,
             Moment.NO_PURCHASE_YET: 2, Moment.GONE_QUIET: 3}
    out.sort(key=lambda d: (order[d.moment], -d.days_alive))
    return tuple(out[:limit])


def summary(drafts: Sequence[Draft]) -> str:
    """One sentence for the top of a screen.

    Says the number and the reason, because "you have 12 drafts" is a chore
    and "12 people are inside their first week and nobody has written" is a
    reason to open it.
    """
    if not drafts:
        return "کسی منتظر پیام نیست."
    first = drafts[0].moment
    count = sum(1 for d in drafts if d.moment is first)
    said = {
        Moment.NEVER_GREETED: "هنوز هیچ پیامی نگرفته‌اند",
        Moment.INSIDE_FIRST_WEEK: "در هفتهٔ اولشان‌اند",
        Moment.GONE_QUIET: "مدتی است بی‌خبرند",
        Moment.NO_PURCHASE_YET: "هستند و هنوز چیزی نخریده‌اند",
    }[first]
    return f"{count} نفر {said}."
