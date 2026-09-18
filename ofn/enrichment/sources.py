"""Where to look for a contact, and how to read what comes back.

The spec is emphatic that a fixed path list is a starting hypothesis, not a
ceiling, and that matters concretely here: real Australian strata and
property sites put their people behind wording nobody can enumerate in
advance ("Meet the Team", "Our Crew", "Who We Are", "Strata Managers").  So
this module works in two layers:

  1. a seeded list of conventional paths, tried first because they are cheap
     and frequently right; and
  2. link discovery from whatever HTML actually comes back, which is what
     finds the pages the seed list could never have guessed.

Layer 2 is the one that makes this an investigator rather than a scraper,
and its results feed the lessons file so the seed list can be improved from
evidence rather than from imagination.

PDF reading is optional by design. This repository ships no dependency
manifest and every module in it is stdlib-only (the target board has 4GB of
RAM), so a hard dependency on a PDF parser would be a real change to the
project's shape. If a parser is importable it is used; if not, a PDF is
recorded as an unexplored source rather than being silently treated as
"nothing found there".
"""
from __future__ import annotations

import io
import re
from urllib.parse import urljoin, urlparse

# Seeded conventional paths. Ordered by observed hit-rate for this segment:
# a dedicated contact page carries a switchboard almost always, while the
# people pages are where the direct/mobile numbers live when they exist at
# all - so people pages are worth trying even though they hit less often,
# because their payoff is higher.
CONTACT_PATH_CANDIDATES = (
    "/contact", "/contact-us", "/contact-us/", "/contactus",
    "/our-team", "/team", "/our-people", "/people", "/staff",
    "/about", "/about-us", "/meet-the-team", "/our-staff",
    "/leadership", "/management", "/our-management-team", "/directors",
    "/locations", "/branches", "/offices", "/our-offices",
)

# Link text / href fragments that suggest a page worth following. Used on
# real fetched HTML, so it catches the wordings the seed list cannot.
_LINK_HINTS = (
    "contact", "team", "people", "staff", "leadership", "management",
    "director", "about", "our crew", "who we are", "meet the",
    "office", "branch", "location", "strata manager", "property manager",
)

_A_HREF_RE = re.compile(
    r'<a\b[^>]*?href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")

# Roles worth attributing a number to, longest-first so "Managing Director"
# wins over "Director" and "General Manager" over "Manager".
DECISION_ROLES = (
    "Managing Director", "Business Development Manager", "General Manager",
    "Client Services Manager", "Portfolio Manager", "Facilities Manager",
    "Building Manager", "Property Manager", "Strata Manager",
    "Operations Manager", "Asset Manager", "National Manager",
    "Branch Manager", "Office Manager", "Licensee", "Principal",
    "Director", "Owner", "Partner", "Founder", "CEO", "Head of",
)
# Seniority prefixes must be part of the ROLE, not the name. Without this
# the leftmost match on "Debbie Stanojevic Senior Property Manager" returns
# the name as "Debbie Stanojevic Senior" - observed on a live Civium page,
# and a wrong name is worse than no name because it tells the owner to ask
# for somebody who does not exist.
_ROLE_PREFIXES = ("Senior", "Junior", "Assistant", "Associate", "Head",
                  "Lead", "Principal", "National", "Regional", "Executive",
                  "Chief", "Deputy", "Group", "State", "Client")
_ROLE_ALT = ("(?:(?:" + "|".join(_ROLE_PREFIXES) + r")\s+)?(?:"
             + "|".join(re.escape(r) for r in DECISION_ROLES) + ")")

# "Jane Smith - Managing Director" / "Jane Smith, Director" / "Jane Smith\nDirector"
# The name quantifier is LAZY ({1,2}?) so a two-word name is preferred and
# the role pattern gets first refusal on the next word. Greedy matching made
# "Debbie Stanojevic Senior Property Manager" parse as a three-word name
# plus "Property Manager", swallowing the seniority prefix into the name.
_PERSON_THEN_ROLE = re.compile(
    r"\b([A-Z][a-z'’\-]{1,15}(?:\s+[A-Z][a-z'’\-]{1,15}){1,2}?)\s*"
    r"(?:[-–—,:|]|\s)\s*(" + _ROLE_ALT + r")\b")
# "Director: Jane Smith" / "Managing Director - Jane Smith"
_ROLE_THEN_PERSON = re.compile(
    r"\b(" + _ROLE_ALT + r")\s*[-–—,:|]\s*"
    r"([A-Z][a-z'’\-]{1,15}(?:\s+[A-Z][a-z'’\-]{1,15}){1,2})\b")

# Words that look like a capitalised name but are page furniture.
_NOT_A_NAME = frozenset({
    "Our Team", "The Team", "Meet The", "Contact Us", "About Us", "Read More",
    "Privacy Policy", "Terms Of", "Site Map", "Get In", "Find Out", "Learn More",
    "New South", "South Wales", "Strata Management", "Property Management",
})

# Flattening HTML to text runs a nav/link label straight into the first
# person's name, so a leftmost regex match happily returns "Statement Murray
# Cox" for a page whose menu ends "...Capability Statement". These are the
# capitalised words that show up immediately before a name in that way; they
# are stripped off the FRONT of a match rather than rejecting it, because
# the name itself is still correct once the furniture is removed.
_NAME_LEAD_NOISE = frozenset({
    "statement", "capability", "download", "downloads", "brochure", "profile",
    "home", "contact", "team", "about", "more", "read", "our", "the", "meet",
    "view", "email", "phone", "mobile", "office", "menu", "close", "search",
    "services", "service", "news", "blog", "welcome", "back", "next", "skip",
})

# A number labelled as the company's own line is NOT a person's direct
# contact, even when a person's name happens to sit nearby on the page - the
# switchboard in a footer is the classic case. Attribution is refused for
# these rather than guessed.
_COMPANY_LINE_LABELS = (
    "office", "reception", "switchboard", "head office", "general enquiries",
    "enquiries", "admin", "administration", "after hours", "emergency",
    "freecall", "toll free", "main line", "fax",
)

# Australian state markers, for detecting that a contact belongs to a
# DIFFERENT branch than the lead. A live run attributed three genuine
# Civium mobiles to the lead "Civium Strata NSW" - every one of them from
# the company's /act/ page, i.e. Canberra staff. The numbers were real and
# the people were real; they were simply the wrong office for a Sydney
# painting business, which is the "different branch" false positive the
# brief calls out. Detected and flagged rather than discarded: the contact
# is still true, and a human should decide whether it is useful.
_STATE_MARKERS = {
    "nsw": ("nsw", "new south wales", "sydney"),
    "vic": ("vic", "victoria", "melbourne"),
    "qld": ("qld", "queensland", "brisbane"),
    "wa": ("wa", "western australia", "perth"),
    "sa": ("sa", "south australia", "adelaide"),
    "tas": ("tas", "tasmania", "hobart"),
    "act": ("act", "canberra"),
    "nt": ("nt", "northern territory", "darwin"),
}


def detect_state(text: str) -> str:
    """Best-guess Australian state from a URL path or short text, or "".

    Word-boundary matched so "act" does not fire on "contact" and "sa" does
    not fire on "same" - a naive substring test makes this check worse than
    useless by flagging almost everything.
    """
    blob = (text or "").lower()
    for state, markers in _STATE_MARKERS.items():
        for m in markers:
            if re.search(r"(?<![a-z])" + re.escape(m) + r"(?![a-z])", blob):
                return state
    return ""


def branch_mismatch_note(*, source_url: str, context: str,
                         expected_state: str) -> str:
    """Flag a contact that looks like it belongs to another state's office."""
    if not expected_state:
        return ""
    found = detect_state(urlparse(source_url).path) or detect_state(context[-120:])
    if found and found != expected_state.lower():
        return (f"BRANCH CAUTION: contact appears to be {found.upper()} office "
                f"while the lead is recorded as {expected_state.upper()} - "
                f"verify the office before calling")
    return ""


_GOV_SUFFIXES = (".gov.au", ".gov", ".nsw.au")
_ASSOC_HINTS = ("association", "institute", "council", "society", "chamber",
                "conference", "summit", "awards", "membership", "strata.community")
_NEWS_HINTS = ("news", "media", "press", "magazine", "journal", "review",
               "afr.com", "smh.com.au", "realestate.com.au/news")
_LISTING_HINTS = ("yellowpages", "truelocal", "hotfrog", "localsearch",
                  "yelp", "startlocal", "aussieweb", "dlook", "cylex")


def clean_text(html: str) -> str:
    """Visible text only.

    Markup is stripped rather than parsed for attributes on purpose: an
    earlier live run on this repo pulled a web developer's email out of a
    <meta name="twitter:data1"> tag and a fake number out of a form's
    placeholder= attribute. Neither is visible to a human on the page, and
    "publicly displayed" has to mean displayed.
    """
    text = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", html or "")
    text = _TAG_RE.sub(" ", text)
    for ent, ch in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"),
                    ("&gt;", ">"), ("&#39;", "'"), ("&quot;", '"'),
                    ("&#8217;", "'"), ("&rsquo;", "'")):
        text = text.replace(ent, ch)
    return re.sub(r"\s+", " ", text).strip()


def same_site(url: str, official_domain: str) -> bool:
    """Never wander off the company's own domain while "checking its site".
    Subdomains count as the same site; a link to a partner or a CDN does not.
    """
    host = (urlparse(url).hostname or "").lower().lstrip("www.")
    dom = (official_domain or "").lower().lstrip("www.")
    return bool(dom) and (host == dom or host.endswith("." + dom))


def seeded_urls(base_url: str) -> list[str]:
    base = base_url if base_url.endswith("/") else base_url + "/"
    return [urljoin(base, p.lstrip("/")) for p in CONTACT_PATH_CANDIDATES]


def discover_links(html: str, base_url: str, official_domain: str,
                   *, limit: int = 12) -> list[str]:
    """Internal links whose text or href suggests contact/people content.

    This is layer 2 - the part that finds "Meet Our Strata Managers" when the
    seed list only knew about /our-team. Ranked so that link TEXT matching a
    hint outranks a mere href match, because navigation labels describe the
    destination more reliably than a slug does.
    """
    scored: list[tuple[int, str]] = []
    seen: set[str] = set()
    for m in _A_HREF_RE.finditer(html or ""):
        href, label_html = m.group(1), m.group(2)
        url = urljoin(base_url, href.strip())
        if not url.lower().startswith(("http://", "https://")):
            continue
        if not same_site(url, official_domain):
            continue
        if url.lower().endswith((".jpg", ".png", ".gif", ".svg", ".css", ".js",
                                 ".zip", ".mp4", ".webp", ".ico")):
            continue
        if url in seen:
            continue
        label = clean_text(label_html).lower()
        path = urlparse(url).path.lower()
        score = 0
        for hint in _LINK_HINTS:
            if hint in label:
                score = max(score, 3)
            elif hint in path:
                score = max(score, 2)
        if score:
            seen.add(url)
            scored.append((score, url))
    scored.sort(key=lambda t: (-t[0], len(t[1])))
    return [u for _, u in scored[:limit]]


def discover_pdfs(html: str, base_url: str, official_domain: str,
                  *, limit: int = 4) -> list[str]:
    """PDFs hosted on the company's own domain - capability statements,
    brochures and strata documents, which the spec correctly identifies as
    carrying better direct contacts than the HTML sometimes does."""
    out: list[str] = []
    seen: set[str] = set()
    for m in _A_HREF_RE.finditer(html or ""):
        url = urljoin(base_url, m.group(1).strip())
        if not url.lower().split("?")[0].endswith(".pdf"):
            continue
        if not same_site(url, official_domain) or url in seen:
            continue
        seen.add(url)
        out.append(url)
        if len(out) >= limit:
            break
    return out


def pdf_parser_available() -> bool:
    try:
        import pypdf  # noqa: F401
        return True
    except Exception:
        return False


def read_pdf_text(data: bytes, *, max_pages: int = 8) -> str:
    """Extract text from PDF bytes, or "" when no parser is installed.

    Returning "" for "cannot parse" is intentionally indistinguishable at the
    call site from "parsed, contained nothing" - so the CALLER must check
    pdf_parser_available() first if it wants to record the difference, and
    the researcher does exactly that. Silently conflating the two would turn
    a missing dependency into a false "this company publishes nothing".
    """
    try:
        import pypdf
    except Exception:
        return ""
    try:
        reader = pypdf.PdfReader(io.BytesIO(data))
        parts = []
        for page in reader.pages[:max_pages]:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                continue
        return re.sub(r"\s+", " ", " ".join(parts)).strip()
    except Exception:
        return ""


def classify_source_type(url: str, official_domain: str) -> str:
    """Which evidence class a URL belongs to. Drives the confidence model,
    so it errs toward the LOWER class when a page could be read two ways."""
    from .evidence import (SRC_ASSOCIATION, SRC_GOV, SRC_LISTING, SRC_NEWS,
                           SRC_OFFICIAL_PDF, SRC_OFFICIAL_SITE)
    host = (urlparse(url).hostname or "").lower()
    is_pdf = url.lower().split("?")[0].endswith(".pdf")
    if same_site(url, official_domain):
        return SRC_OFFICIAL_PDF if is_pdf else SRC_OFFICIAL_SITE
    if any(host.endswith(s) for s in _GOV_SUFFIXES):
        return SRC_GOV
    blob = host + urlparse(url).path.lower()
    if any(h in blob for h in _LISTING_HINTS):
        return SRC_LISTING
    if any(h in blob for h in _ASSOC_HINTS):
        return SRC_ASSOCIATION
    if any(h in blob for h in _NEWS_HINTS):
        return SRC_NEWS
    return SRC_LISTING


def extract_people(text: str, *, limit: int = 12) -> list[tuple[str, str]]:
    """(name, role) pairs from visible page text.

    Attribution is what separates a P0 contact from a P1 one, so this is
    deliberately strict: two or three capitalised words next to a role title
    from DECISION_ROLES, with page furniture filtered out. A wrong name
    attached to a right number is worse than no name, because it tells the
    owner to ask for somebody who does not work there.
    """
    found: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(name: str, role: str) -> None:
        words = name.split()
        # Drop leading page-furniture words (see _NAME_LEAD_NOISE) so
        # "Statement Murray Cox" becomes "Murray Cox" instead of being
        # thrown away or stored wrong.
        while words and words[0].lower() in _NAME_LEAD_NOISE:
            words = words[1:]
        name = " ".join(words)
        if not name or name in _NOT_A_NAME or name.lower() in seen:
            return
        if len(words) < 2:
            return
        seen.add(name.lower())
        found.append((name, role.strip()))

    for m in _PERSON_THEN_ROLE.finditer(text or ""):
        add(m.group(1), m.group(2))
    for m in _ROLE_THEN_PERSON.finditer(text or ""):
        add(m.group(2), m.group(1))
    return found[:limit]


def nearest_person(text: str, number_raw: str,
                   people: list[tuple[str, str]]) -> tuple[str, str]:
    """Attribute a number to the person named closest before it.

    Team pages are laid out as repeated person blocks, so proximity is a
    real signal - but only within a tight window. Beyond that the "nearest"
    name is just whoever happened to appear earlier on the page, which is how
    a number gets confidently attached to the wrong human.
    """
    if not people or not number_raw:
        return ("", "")
    idx = text.find(number_raw)
    if idx < 0:
        return ("", "")

    # A number the page itself labels as the company line is never a
    # person's direct contact, however close a name happens to sit. Without
    # this, a footer switchboard gets attributed to whoever appears last in
    # the team list above it - observed on the first realistic page tested.
    label = text[max(0, idx - 40):idx].lower()
    if any(w in label for w in _COMPANY_LINE_LABELS):
        return ("", "")

    best: tuple[int, str, str] = (-1, "", "")
    for name, role in people:
        pos = text.rfind(name, 0, idx)
        if pos > best[0]:
            best = (pos, name, role)
    # One person "card" (name + role + number) is well under 160 characters
    # of flattened text. A wider window mostly reaches past the card into
    # unrelated page content and starts inventing attributions.
    if best[0] < 0 or (idx - best[0]) > 160:
        return ("", "")
    return (best[1], best[2])
