"""True cost of a handmade item, and the verdict that follows from it.

This is a business rule, not kernel: the kernel decides *whether* something
may be said, this decides *what the number is*. It lives beside the pack that
parameterises it, and it holds no business names beyond this module's own.

The one idea worth stating plainly, because the whole industry gets it wrong:

    A maker's own hours are a cost. Leaving them out does not make an item
    cheaper to produce, it makes the loss invisible. The most common way to
    lose money on handmade work is to price against materials alone and call
    the difference profit.

So `hourly_floor` is an input here, not an optional refinement, and there is
no code path that computes a margin without it.

Nothing in this module estimates. Every function either returns a number with
the fact keys that produced it, or refuses and names what is missing —
because a margin built from an absent fact is the one lie that gets acted on:
somebody changes a price because of it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..kernel.domain import Locale

# Facts required before any number may be produced. Ordered the way they are
# worth asking: cost first, because it is the one nobody has computed.
REQUIRED_FACTS: tuple[str, ...] = (
    "materials.cost_per_batch",
    "production.batch_size",
    "time.hours_per_item",
    "time.hourly_floor",
    "offer.price_current",
)
# Only needed for the runway half of the answer. Missing these costs you the
# "you will run out on Thursday" line, not the margin verdict.
RUNWAY_FACTS: tuple[str, ...] = ("stock.units_left", "sales.units_last_7d")

HEALTHY = "healthy"
BELOW_FLOOR = "below_floor"
LOSS_MAKING = "loss_making"


@dataclass(frozen=True)
class NotReady:
    """No numbers, on purpose. Just what is still unknown."""

    missing: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return False


@dataclass(frozen=True)
class Costing:
    """What one item actually costs, and what that means."""

    cogs: float                 # materials + the maker's own time, per item
    materials_per_item: float
    labour_per_item: float
    net_price: float            # what the business keeps, after sales tax
    margin: float
    margin_pct: float
    verdict: str
    runway_days: float | None   # None when it cannot be known, never inf
    low_stock: bool
    # Every fact key that fed a number above. A number whose ancestry cannot
    # be printed is a number that cannot be argued with, and every one of
    # these will eventually be argued with.
    provenance: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return True

    @property
    def loses_money(self) -> bool:
        return self.verdict == LOSS_MAKING


def _missing(facts: Mapping[str, float], keys: tuple[str, ...]) -> tuple[str, ...]:
    out = []
    for k in keys:
        v = facts.get(k)
        if v is None or not isinstance(v, (int, float)) or isinstance(v, bool):
            out.append(k)
    return tuple(out)


def assess(
    facts: Mapping[str, float],
    locale: Locale,
    *,
    margin_floor: float,
    runway_warn_days: float,
) -> Costing | NotReady:
    """Cost one item and judge the price, or refuse and say why.

    Raises `LocaleError` if the market's tax treatment is unresolved: a
    margin depends on whether the price includes tax, so an unanswered tax
    question is not something to work around.
    """
    missing = _missing(facts, REQUIRED_FACTS)
    if missing:
        return NotReady(missing)

    batch = float(facts["production.batch_size"])
    if batch <= 0:
        # Not a missing fact — a wrong one. Saying "batch size is missing"
        # would send her to answer a question she has already answered.
        return NotReady(("production.batch_size",))

    price = float(facts["offer.price_current"])
    if price <= 0:
        return NotReady(("offer.price_current",))

    rate, pricing = locale.require_tax()   # refuses while unresolved
    # Tax collected on a sale was never the business's money. Counting it as
    # revenue overstates every margin by the rate.
    net_price = price / (1.0 + rate) if (pricing == "inclusive" and rate) else price

    materials = float(facts["materials.cost_per_batch"]) / batch
    labour = float(facts["time.hours_per_item"]) * float(facts["time.hourly_floor"])
    cogs = materials + labour
    margin = net_price - cogs
    margin_pct = margin / net_price

    if margin < 0:
        verdict = LOSS_MAKING
    elif margin_pct < margin_floor:
        verdict = BELOW_FLOOR
    else:
        verdict = HEALTHY

    prov = list(REQUIRED_FACTS)
    runway: float | None = None
    low_stock = False
    if not _missing(facts, RUNWAY_FACTS):
        sold = float(facts["sales.units_last_7d"])
        left = float(facts["stock.units_left"])
        if sold > 0:
            # Sold nothing this week is not "stock lasts forever" — it is a
            # different question, and answering it here would be a guess.
            runway = left / (sold / 7.0)
            low_stock = runway < runway_warn_days
        prov += list(RUNWAY_FACTS)

    return Costing(
        cogs=cogs,
        materials_per_item=materials,
        labour_per_item=labour,
        net_price=net_price,
        margin=margin,
        margin_pct=margin_pct,
        verdict=verdict,
        runway_days=runway,
        low_stock=low_stock,
        provenance=tuple(prov),
    )


def price_for_margin(cogs: float, target_margin: float, locale: Locale) -> float:
    """The shelf price that would actually hit `target_margin`.

    Grossed back up by sales tax where prices are tax-inclusive, so the answer
    is the number that goes on the label rather than one an accountant has to
    correct afterwards.
    """
    if not 0.0 <= target_margin < 1.0:
        raise ValueError("target margin must be within 0..1")
    rate, pricing = locale.require_tax()
    net = cogs / (1.0 - target_margin)
    return net * (1.0 + rate) if (pricing == "inclusive" and rate) else net
