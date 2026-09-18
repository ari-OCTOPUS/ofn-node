"""Offer v0.3 — the only source of things we are allowed to say.

Ari approved eight items on 2026-08-29. This module is those items in a form
code can read, and nothing else: no marketing copy invented here, no field
that the signed document does not contain.

Two of the eight are deliberately *not* customer-facing, and that is the whole
reason they are annotated rather than merely stored:

  * `min_project_value_aud` — Ari sets prices. A generator that writes "$400"
    into an email has quoted on his behalf.
  * `proof_photo_count` — eight today, possibly twelve next month. An email
    that names the number becomes false later without anyone editing it, which
    is the worst kind of false: nobody is watching the file that broke.

Both live in `QUALIFICATION_ONLY` and the draft generator refuses to put them
in prose. They are here so the I3 qualifier can use them as facts, which is
what a minimum project value is actually for.

What the document does NOT contain is as load-bearing as what it does. There
is no ABN, no licence number, no warranty, no insurance figure, no client
reference. Anything absent here may not appear in customer-facing text —
`FORBIDDEN_CLAIMS` names the tempting ones so the refusal is explicit rather
than incidental.

Source: Offer_v0_3_clean.docx — "OFFER — Master Painting — v0.3".
"""

from __future__ import annotations

import copy
from typing import Mapping

VERSION = "0.3"

# The eight approved items. Keys are stable identifiers: a draft cites them to
# prove every sentence it wrote came from here.
OFFER_V0_3: Mapping[str, object] = {
    "version": VERSION,
    "approved_on": "2026-08-29",

    # 1 — target customer
    "target_customer": "strata properties",

    # 2 — primary CTA, the single action every message asks for
    "primary_cta": "no-obligation condition assessment",

    # 3 — verified proof. The prose form, not the count; see QUALIFICATION_ONLY.
    "verified_proof": "documented before-and-after results from previous "
                      "strata projects",
    "proof_photo_count": 8,

    # 4 — service scope. Ari accepts everything; the pilot only talks about
    # strata painting, so the pilot line is what the generator may use.
    "service_scope": "painting, renovation and building work",
    "pilot_scope": "strata painting",

    # 5 — service area. 50–100 km is guidance for qualification, not a cutoff,
    # and not a sentence we put in an email.
    "service_area": "Sydney metro area",
    "service_radius_km": (50, 100),
    "service_area_is_hard_cutoff": False,

    # 6 — minimum project value. Hard floor, no exceptions. Never in prose.
    "min_project_value_aud": 400,

    # 7 — insurance. The claim is approved; the figure is not. Ari holds the
    # certificate and answers any request for evidence himself.
    "insurance_status": "fully insured",

    # 8 — the approved paragraph, verbatim. The generator composes its body
    # from the same wording, sentence by sentence, so each line can name the
    # item it came from. This stays here as the canonical text to check against.
    "pitch_en": (
        "Master Painting is a fully insured painting contractor serving "
        "strata properties across the Sydney metro area. We offer a "
        "no-obligation condition assessment — we come to your building, "
        "inspect the paintwork, and provide an honest written report at no "
        "cost. We have documented before-and-after results from previous "
        "strata projects. If you'd like to schedule an assessment, we can "
        "arrange a time that suits your building's needs."
    ),

    # Sender identity — the same one lead_email_writer signs with.
    "sender_name": "Master Painting",
    "sender_city": "Sydney NSW",
}

# Facts we hold and may act on, but may not say. Qualification, not copy.
QUALIFICATION_ONLY = ("min_project_value_aud", "proof_photo_count",
                      "service_radius_km", "service_area_is_hard_cutoff")

# Claims Offer v0.3 does not support. Absence from the document is the reason;
# this tuple only makes the absence checkable.
FORBIDDEN_CLAIMS = ("abn", "licence", "license", "warranty", "guarantee",
                    "certified", "accredited", "award", "testimonial")


def load_offer() -> dict:
    """A mutable copy, so a caller cannot edit the approved offer in place.

    Deep, because `service_radius_km` is the kind of nested value that a
    shallow copy would share and some future caller would sort.
    """
    return copy.deepcopy(dict(OFFER_V0_3))
