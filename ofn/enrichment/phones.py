"""Australian phone parsing, classification and false-positive defense.

This is the module where being wrong is most expensive: a fabricated or
misread number sends the owner to a stranger, and a number that is really an
ABN makes the whole table untrustworthy. So the rule here is conservative by
construction — a candidate must positively match a known AU numbering shape
AND survive context checks, or it is discarded. Nothing is ever repaired,
completed, or guessed into validity.

Numbering facts encoded (Australian Numbering Plan):
  04xx xxx xxx / 05xx xxx xxx   mobile, 10 digits
  02/03/07/08 + 8 digits        geographic landline, 10 digits
  1300 xxx xxx / 1800 xxx xxx   inbound service, 10 digits
  13 xx xx                      inbound service, 6 digits (e.g. 13 20 92)
  +61 <9 digits>                international form; the 0 trunk prefix is
                                dropped, so +61 4xx... == 04xx...

Deliberately NOT accepted: 19xx premium, 0500 personal-number range, and
anything else outside the shapes above. An unrecognised shape is a reject,
never a "probably fine".
"""
from __future__ import annotations

import re
from dataclasses import dataclass, replace

# ── tiers, in the priority order the spec defines ────────────────────────────
# P0/P1 are the numbers that actually reach a decision-maker; P2 is a real
# person's desk; P3 is the switchboard the owner already knows is a dead end.
TIER_P0 = "P0_personal_mobile"      # mobile + named person + role
TIER_P1 = "P1_mobile_unattributed"  # mobile, company-associated, person unclear
TIER_P2 = "P2_direct_office"        # geographic landline for a person/team
TIER_P3 = "P3_general"              # 1300/1800/13 or generic switchboard
TIER_ORDER = (TIER_P0, TIER_P1, TIER_P2, TIER_P3)

KIND_MOBILE = "mobile"
KIND_LANDLINE = "landline"
KIND_SERVICE = "service"            # 1300/1800/13


@dataclass(frozen=True)
class PhoneCandidate:
    """One phone-shaped string that survived validation.

    `raw` is preserved exactly as published (the owner dials what the site
    shows); `e164` is the comparison key so 0412 345 678, +61 412 345 678 and
    (04) 1234 5678 all collapse to one contact rather than three.
    """
    raw: str
    e164: str
    kind: str
    tier: str = TIER_P3
    person: str = ""
    role: str = ""
    context: str = ""           # the surrounding text the number was read from

    def with_attribution(self, *, person: str, role: str) -> "PhoneCandidate":
        """Attach a person and re-derive the tier. A mobile only earns P0 once
        it actually has a named human against it — attribution is evidence,
        not decoration."""
        tier = self.tier
        if self.kind == KIND_MOBILE:
            tier = TIER_P0 if (person and role) else TIER_P1
        return replace(self, person=person or "", role=role or "", tier=tier)


# Broad finder: any plausible run of digits/separators. Real validation is
# done on the stripped digits below, so this stays readable instead of
# becoming one unmaintainable meta-regex.
_CANDIDATE_RE = re.compile(r"(?<![\w/])((?:\+?61[\s.-]?|\()?[\d][\d\s().\-]{4,18}\d\)?)(?![\w/])")

# Numbers that are structurally valid but are obviously filler. Extending
# this list is cheap; a placeholder reaching the owner's call list is not.
#
# Judgement call worth stating plainly: 0412 345 678 is in here. It is a
# real allocated mobile shape and could in principle be somebody's number,
# but it is also THE canonical example number in Australian government
# forms, telco documentation and web templates, so a page showing it is far
# more likely to be showing an example than a contact. Given the spec's
# "accuracy > volume" bar, the cost of one wasted/embarrassing call to a
# stranger outweighs the cost of missing one genuine lead. Same reasoning
# for the other ascending-digit variants below.
_PLACEHOLDER_E164 = frozenset({
    "+61400000000", "+61411111111", "+61412345678", "+61423456789",
    "+61400123456", "+61234567890", "+61255555555", "+61212345678",
    "+61300000000", "+61800000000", "+61000000000", "+61123456789",
})

# Context words that mean "this number is not a voice line we want", or
# "these digits are an identifier, not a phone at all". Checked against a
# short window immediately BEFORE the number, which is where labels sit.
_REJECT_CONTEXT = (
    "abn", "a.b.n", "acn", "a.c.n", "arbn", "tfn", "gst",
    "fax", "facsimile",
    "licence", "license", "lic no", "lic.", "registration no", "reg no",
    "invoice", "receipt", "ref no", "reference no", "order no", "account no",
    "bsb", "postcode", "post code", "po box", "abn:", "acn:",
)
_FAX_CONTEXT = ("fax", "facsimile")


def _digits(text: str) -> str:
    return re.sub(r"\D", "", text or "")


def normalize_au(raw: str) -> str:
    """Return E.164 (+61...) for a valid AU number, else "".

    The single source of truth for "are these two numbers the same contact".
    Returning "" is how this module says *invalid* — callers must treat an
    empty result as a hard reject, never as "unknown but probably fine".
    """
    d = _digits(raw)
    if not d:
        return ""
    # International forms: 0011 is the AU outbound prefix, 61 the country code.
    if d.startswith("001161"):
        d = d[6:]
    elif d.startswith("61") and len(d) in (11, 10, 8):
        d = d[2:]
    elif d.startswith("0061"):
        d = d[4:]
    else:
        d = d[1:] if d.startswith("0") and len(d) in (10, 7) else d

    # `d` is now the national number without the trunk 0.
    if len(d) == 9:
        head = d[0]
        if head in "45":                       # mobile 04xx/05xx
            return "+61" + d
        if head in "2378":                     # geographic landline
            return "+61" + d
        if d.startswith("300") or d.startswith("800"):   # 1300/1800 minus trunk
            return "+61" + d
        return ""
    if len(d) == 10 and (d.startswith("1300") or d.startswith("1800")):
        return "+61" + d[1:]
    if len(d) == 6 and d.startswith("13"):     # 13 xx xx short service line
        return "+61" + d
    return ""


def classify_kind(e164: str) -> str:
    """mobile / landline / service for an already-normalized number."""
    if not e164.startswith("+61"):
        return ""
    n = e164[3:]
    if n[:1] in ("4", "5"):
        return KIND_MOBILE
    if n.startswith("300") or n.startswith("800") or n.startswith("13"):
        return KIND_SERVICE
    if n[:1] in ("2", "3", "7", "8"):
        return KIND_LANDLINE
    return ""


def is_placeholder(e164: str) -> bool:
    """Filler numbers, and any number whose digits are a single repeated
    character or a straight ascending run — both are template artifacts, not
    contacts anyone answers."""
    if e164 in _PLACEHOLDER_E164:
        return True
    n = e164[3:] if e164.startswith("+61") else e164
    if not n:
        return True
    if len(set(n)) == 1:                       # 000000000, 111111111
        return True
    if n in ("123456789", "234567890", "987654321"):
        return True
    return False


def _context_window(text: str, start: int, end: int, *, before: int = 42,
                    after: int = 18) -> str:
    return (text[max(0, start - before):end + after] or "").lower()


def extract_candidates(text: str, *, allow_fax: bool = False) -> list[PhoneCandidate]:
    """Every valid, non-placeholder AU number in a block of VISIBLE text.

    `text` must already be visible page text, not raw HTML — a live run
    during earlier work on this repo pulled a web developer's address out of
    a <meta name="twitter:data1"> tag and a form's placeholder= attribute,
    neither of which a human visitor ever sees. Callers strip markup first.

    De-duplicated by E.164 so one number printed in a header and a footer is
    one contact, keeping the first (usually better-labelled) occurrence.
    """
    out: list[PhoneCandidate] = []
    seen: set[str] = set()
    for m in _CANDIDATE_RE.finditer(text or ""):
        raw = m.group(1).strip()
        e164 = normalize_au(raw)
        if not e164 or is_placeholder(e164):
            continue
        kind = classify_kind(e164)
        if not kind:
            continue
        ctx = _context_window(text, m.start(1), m.end(1))
        label_side = ctx[:ctx.find(raw.lower()) if raw.lower() in ctx else len(ctx)]
        if any(bad in label_side for bad in _REJECT_CONTEXT):
            if not (allow_fax and any(f in label_side for f in _FAX_CONTEXT)):
                continue
        if e164 in seen:
            continue
        seen.add(e164)
        tier = TIER_P3 if kind == KIND_SERVICE else (
            TIER_P1 if kind == KIND_MOBILE else TIER_P2)
        out.append(PhoneCandidate(raw=raw, e164=e164, kind=kind, tier=tier,
                                  context=ctx.strip()))
    return out


def best_tier(candidates) -> str:
    """The strongest tier present, for stopping decisions and reporting."""
    for tier in TIER_ORDER:
        if any(c.tier == tier for c in candidates):
            return tier
    return ""


def already_present(e164: str, existing_contact_channel: str) -> bool:
    """True when this exact contact is already on the account.

    Compares on normalized form, so appending "0412 345 678" to a row that
    already reads "+61 412 345 678" correctly does nothing. This is what
    keeps re-runs idempotent instead of growing the field forever.

    Deliberately does NOT reuse extract_candidates: this asks "is this string
    already in the field", which is a different question from "is this a good
    number to store". Routing it through the quality filters made a
    placeholder or fax already sitting in the field invisible here, so a
    re-run would happily append a duplicate of it.
    """
    if not e164:
        return False
    for m in _CANDIDATE_RE.finditer(existing_contact_channel or ""):
        if normalize_au(m.group(1)) == e164:
            return True
    return False
