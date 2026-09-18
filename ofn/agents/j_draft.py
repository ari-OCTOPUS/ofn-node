"""J1/J2 — strata email drafts, built from Offer v0.3 and queued for a human.

This module writes emails. It does not send them, and it cannot: the only way
a draft reaches the queue is `enqueue_draft`, which takes the caller's gate
function as an argument and has no queue of its own to write to.

That split is deliberate and was the one correction to the original design.
An earlier shape had the generator holding the outbox directly, which meant a
draft could be admitted while the node was killed — the kill switch lives in
`Node._gate_enqueue`, so anything that reaches around it is unswitchable. Now:

    draft_email_from_offer(lead, offer)   pure — no clock, no store, no queue
    enqueue_draft(gate, scope, ...)       admission, through the caller's gate

`tests/test_j_draft.py::TestKillSwitchIsNotBypassed` asserts both halves,
including a source-level check that this file never names the queue adapter.
If a later edit "simplifies" the indirection away, that test goes red before
anything ships.

On content, one rule with no exceptions: a sentence may appear in a draft only
if an item of Offer v0.3 puts it there. Every sentence carries the offer key
it came from, `offer_refs` reports them, and a field the offer lacks becomes a
visible `[OWNER INPUT REQUIRED: field]` rather than a plausible guess. The two
numbers Ari approved but withheld from customer-facing text — the $400 floor
and the photo count — are refused in prose by `_assert_fact_only`, which reads
them out of `QUALIFICATION_ONLY` rather than hard-coding them here.

Nothing in this module has a side effect except the gate call in
`enqueue_draft`, and that one ends at `status=pending`.
"""

from __future__ import annotations

import hashlib
import re
from typing import Callable, Mapping, Sequence

from ..kernel.domain import RiskTier
from ..offer_v0_3 import FORBIDDEN_CLAIMS, QUALIFICATION_ONLY
from .lead_email_writer import FORBIDDEN

# Same namespace as the lead traffic node.py already queues (`lead:reply`,
# `lead:quote`). A draft is a third member of that family, not a new word.
KIND = "lead:draft"

# Email carries the customer's name and leaves the device. That is RED for the
# same reason send_lead_reply is RED — the tier is a property of the action,
# not a judgement about this particular message.
TIER = RiskTier.RED

PLACEHOLDER = "[OWNER INPUT REQUIRED: {field}]"

MAX_BODY_WORDS = 130

# The body, as sentences bound to the offer items that authorise them. The
# wording is the approved `pitch_en` paragraph, split so a missing field
# degrades one clause instead of silently deleting a claim or, worse, keeping
# a claim whose evidence has gone away.
_SENTENCES: Sequence[tuple[str, tuple[str, ...]]] = (
    ("Master Painting is a {insurance_status} painting contractor serving "
     "{target_customer} across the {service_area}.",
     ("insurance_status", "target_customer", "service_area")),

    ("We offer a {primary_cta} — we come to your building, inspect the "
     "paintwork, and provide an honest written report at no cost.",
     ("primary_cta",)),

    ("We have {verified_proof}.",
     ("verified_proof",)),

    ("If you'd like to schedule an assessment, we can arrange a time that "
     "suits your building's needs.",
     ()),
)

_SUBJECT = "{primary_cta} for your building"

_GREETING = "Hello {contact_name},"

_SIGNOFF = "Kind regards,\n{sender_name}\n{sender_city}"

# Shapes that only ever appear in a fabricated claim, given an offer that
# contains none of these facts. The generator runs this over its own output
# before returning: a future edit to the offer that smuggles in a figure fails
# here rather than in a customer's inbox.
_FABRICATION = (
    (r"\$\s*\d", "a price"),
    (r"\b\d+\s*(?:%|per\s?cent)", "a percentage"),
    (r"\b\d{2}\s?\d{3}\s?\d{3}\s?\d{3}\b", "an ABN-shaped number"),
    (r"\b\d+\s*(?:year|yr)s?\b", "a duration"),
    (r"\b\d+\s*(?:building|propert)", "a portfolio count"),
    (r"\bmillion\b", "an insurance figure"),
)


class FabricatedClaimError(ValueError):
    """Raised when a draft would state something Offer v0.3 does not support.

    A subclass of ValueError so a caller that only knows "bad offer" still
    catches it, and a caller that wants to page a human can tell the two
    apart: a wrong version is a mistake, a fabricated claim is an incident.
    """


def contact_digest(value: object) -> str:
    """Stable 16-hex digest of a contact address.

    Short on purpose: this is a correlation handle for the owner's queue, not
    a password hash. The address itself never leaves LeadStore, so the digest
    only has to survive being looked at, and a full 64 characters in every
    queue row would make the payload harder to read for no gain.
    """
    text = str(value or "").strip().lower()
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _require_v0_3(offer: Mapping[str, object]) -> None:
    """Content rules are version-specific; v0.4 may permit different claims.

    Rendering a later offer with this module's assumptions would be the
    quietest possible way to start lying, so it is refused outright.
    """
    version = str(offer.get("version") or "")
    if version != "0.3":
        raise ValueError(
            f"j_draft renders Offer v0.3 only, got {version!r}")


def _fill(template: str, offer: Mapping[str, object],
          extra: Mapping[str, object], missing: set[str]) -> str:
    """Substitute `{field}` from the offer, or mark it as owner input.

    Marking is inline rather than dropping the sentence: the owner needs to
    see *where* the gap is, and a deleted sentence looks like a finished
    email. Records every gap in `missing` so the caller can report it.
    """
    def one(match: re.Match) -> str:
        field = match.group(1)
        if field in extra:
            value = extra[field]
        elif field in offer:
            value = offer[field]
        else:
            value = None
        if value is None or str(value).strip() == "":
            missing.add(field)
            return PLACEHOLDER.format(field=field)
        return str(value)

    return re.sub(r"\{(\w+)\}", one, template)


def _assert_fact_only(text: str, offer: Mapping[str, object]) -> None:
    """Refuse to emit a claim the offer does not support.

    Runs over offer-derived prose only. The greeting is excluded deliberately:
    a building legitimately named "Unit 8" must not be mistaken for a photo
    count, and rejecting a customer's own name would be a guard doing harm.
    """
    lowered = text.lower()
    for pattern, what in _FABRICATION:
        if re.search(pattern, text, re.IGNORECASE):
            raise FabricatedClaimError(
                f"draft states {what}, which Offer v0.3 does not supply")
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            raise FabricatedClaimError(
                f"draft makes a {claim!r} claim, absent from Offer v0.3")
    # Ari's ruling: these are facts we qualify on, never facts we say. Read
    # from the offer so the list stays true if the offer changes.
    for field in QUALIFICATION_ONLY:
        value = offer.get(field)
        if isinstance(value, (int, float)) and str(value) in text:
            raise FabricatedClaimError(
                f"draft names {field}, which is qualification-only")


def check(draft: Mapping[str, object]) -> list[str]:
    """House style gate — errors, empty means pass.

    `FORBIDDEN` is imported from lead_email_writer rather than copied, so the
    anti-boilerplate list has one owner. Its sibling rule is inverted here on
    purpose: that module *requires* a dollar figure (its leads come with real
    NSW contract totals), and this one forbids every figure, because a strata
    lead comes with none and Ari is the only person who prices work.
    """
    errs: list[str] = []
    text = (str(draft.get("subject") or "") + "\n" +
            str(draft.get("body") or "")).lower()
    for bad in FORBIDDEN:
        if bad in text:
            errs.append(f"forbidden-phrase:{bad}")
    words = len(str(draft.get("body") or "").split())
    if words > MAX_BODY_WORDS:
        errs.append(f"body-too-long:{words}")
    return errs


def draft_email_from_offer(lead: Mapping[str, object],
                           offer: Mapping[str, object]) -> dict:
    """Compose a draft. Pure: no clock, no store, no queue, no randomness.

    Returns subject, body, the offer keys every sentence came from, and the
    fields an owner still has to supply. Same inputs give the same output
    forever, which is what makes the idempotency key downstream meaningful.
    """
    _require_v0_3(offer)

    missing: set[str] = set()
    refs: list[str] = []

    paragraphs: list[str] = []
    for template, keys in _SENTENCES:
        paragraphs.append(_fill(template, offer, {}, missing))
        # A key that resolved is a claim we are standing behind; a key that
        # turned into a placeholder is a question, so it is not cited.
        refs.extend(k for k in keys if k not in missing and k in offer)

    # The offer stores its items in the lower case they are quoted in mid-
    # sentence ("we offer a no-obligation condition assessment"). A subject
    # line starts one, so it gets a capital here rather than a second, almost
    # identical copy of the phrase living in the offer.
    subject = _fill(_SUBJECT, offer, {}, missing)
    subject = subject[:1].upper() + subject[1:]
    offer_text = subject + "\n" + "\n".join(paragraphs)
    _assert_fact_only(offer_text, offer)

    greeting = _fill(_GREETING, offer,
                     {"contact_name": lead.get("customer_name")}, missing)
    signoff = _fill(_SIGNOFF, offer, {}, missing)

    body = "\n\n".join((greeting,
                        " ".join(paragraphs[:2]),
                        " ".join(paragraphs[2:]),
                        signoff))

    draft = {
        "subject": subject,
        "body": body,
        "lead_id": str(lead.get("lead_id") or ""),
        "tenant": str(lead.get("tenant_id") or "lead"),
        "to_digest": contact_digest(lead.get("email")),
        "offer_version": str(offer.get("version")),
        "offer_refs": sorted(set(refs)),
        "placeholders": sorted(missing),
        "channel": "email",
    }

    errs = check(draft)
    if errs:
        raise FabricatedClaimError("draft failed house style: " + ", ".join(errs))
    return draft


def draft_idem_key(lead: Mapping[str, object],
                   offer: Mapping[str, object]) -> str:
    """Stable key for one lead's draft of one offer version.

    The content digest is part of the key so that editing the offer produces a
    *new* draft rather than being silently swallowed as a duplicate — the
    failure mode where a corrected email never reaches the owner because an
    older one already holds the key.
    """
    draft = draft_email_from_offer(lead, offer)
    digest = hashlib.sha256(
        (draft["subject"] + "\n" + draft["body"]).encode("utf-8")
    ).hexdigest()[:12]
    tenant = draft["tenant"]
    return f"lead-draft:{tenant}:{draft['lead_id']}:v{draft['offer_version']}:{digest}"


def enqueue_draft(gate: Callable[..., Mapping[str, object]],
                  scope, lead: Mapping[str, object],
                  offer: Mapping[str, object], now_iso: str) -> dict:
    """Build a draft and offer it to `gate` for admission.

    `gate` must have the signature of `Node._gate_enqueue`:

        gate(scope, idem_key, kind, payload, tier, now_iso) -> {"ok", ...}

    Pass the node's own bound method. This module deliberately has no other
    route to the queue — it never imports the adapter and never holds one, so
    the kill switch inside that method is the single door, and there is no
    second door to forget about.

    The payload carries `to_digest`, not the address: the queue row is durable
    and read by the owner panel, while the address itself stays in LeadStore
    and is resolved by `lead_id` at the moment a human is ready to send.

    On success the item sits at `status=pending`. Nothing here approves it,
    claims it, or sends it.
    """
    draft = draft_email_from_offer(lead, offer)
    idem_key = draft_idem_key(lead, offer)
    payload = dict(draft)
    payload["tenant"] = scope.tenant.value

    result = gate(scope, idem_key, KIND, payload, TIER, now_iso)
    out = dict(result)
    out["idem_key"] = idem_key
    out["draft"] = draft
    return out
