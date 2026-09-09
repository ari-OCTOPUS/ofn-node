"""B2B lead discovery/harvest agent — multi-source, collection-only.

Discovers NEW potential B2B accounts (strata managers, facility managers,
property managers, commercial builders, etc.) from many public sources,
normalizes them, resolves identity against the existing painting_b2b_accounts
table, and creates/updates records through LeadStore.create_account — the
SAME store, SAME schema and SAME upsert mechanism every other agent in this
pack uses. There is no second database and no second lead store here.

This is deliberately NOT a single-source collector like seek_harvest.py or
h3_strata.py. Those two shapes are still the model this module follows —
pure parse/normalize functions, one injectable I/O boundary, a `cycle`-style
orchestrator that returns an honest accounting dict and never crashes the
loop on one bad input (ingest_batch's contract) — but the *source* layer is
a plural, extensible list of `SourceCollector`s rather than one URL. Adding
a new source means adding one more `SourceCollector` (see
ofn/agents/source_registry.py's SOURCES list for the registry this pulls
from) — never rewriting this module.

Architecture decisions (see HANDOFF/report for the full rationale):

  * Identity resolution is tiered, not a single slug comparison:
      Tier A — matching official website domain            -> same company
      Tier B — matching name after stripping ONLY a legal-  -> same company
                entity suffix (Pty Ltd/Ltd/Inc/...)
      Tier C — fuzzy name similarity with no corroborating   -> POSSIBLE
                signal (e.g. one is the other + a generic       duplicate;
                trailing word like "management"/"group")        both are
                                                                  preserved,
                                                                  never
                                                                  auto-merged
      Tier D — nothing matches                              -> genuinely new
    This exists because `LeadStore.create_account`'s default id is a bare
    slug of business_name (`{tenant}:acct:{slug}`), which "McCormacks
    Strata" vs "McCormacks Strata Management" would silently defeat.

  * `create_account`'s UPSERT overwrites every column unconditionally
    (`ON CONFLICT ... SET col=excluded.col` for all columns) — correct for
    a single authoritative writer, but a second, weaker source could blank
    out a good website/suburb. This module never calls `create_account`
    with a blank that would clobber a known-good value: `merge_account`
    reads the existing row first and only ever adds, never erases.

  * painting_b2b_accounts has no dedicated phone/email columns (unlike
    painting_leads). Discovered contact details are folded into the
    existing `contact_channel` (short) and `notes` (full provenance) fields
    rather than inventing new columns — "use the existing project schema".

  * Retry/backoff on fetch follows the two sibling patterns already in this
    package: seek_harvest.py's "retry then park, never crash" contract for
    the overall shape, and demand_harvest.py's fetch_json 403-vs-429
    distinction (403 = a policy answer, never retried; 429/5xx = transient,
    retried with capped exponential backoff) for the actual HTTP handling,
    since the plain linear retry in seek_harvest.py does not itself
    distinguish those two codes and the spec calls both out explicitly.

Collection-only boundary: every network call in this module is a GET. There
is no outbox import, no email/SMS/webhook client, no form submission. This
agent stops at persisting a lead record — enrichment/scoring/outreach are
later, separate stages exactly as the existing pack already models them
(painting_b2b_accounts.stage starts at 'discovered').
"""
from __future__ import annotations

import re
import time
import urllib.error
import urllib.request
import urllib.robotparser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Iterable, Mapping, Sequence
from urllib.parse import urljoin, urlparse

TENANT = "lead"
USER_AGENT = "octopus-b2b-harvester/1.0 (Ari; painting-b2b-discovery; contact via repo owner)"

# Stamped once, at creation only, into the notes of every account THIS module
# creates (see merge_account) — never on a row it merely matches/enriches.
# This is the "separate marking" the spec asks for: a real, greppable notes
# tag using the SAME "TAG: value" convention tools/owner_digest.py already
# parses (RELEVANCE:/APPROACH:), not a new schema column and not a change to
# `stage` (a live check of the real DB during this fix found every existing
# row - the 74 hand-researched accounts included - already sitting at
# stage='discovered'; tools/update_verified_leads.py's stage='researched'
# has apparently never actually been applied to this file, so `stage` does
# NOT currently separate verified from unverified and cannot be reused for
# that here).
AUTO_DISCOVERY_TAG = "SOURCE: auto_discovery UNVERIFIED"
TIMEOUT_S = 20
MAX_RETRIES = 3
BACKOFF_BASE_S = 3.0
BACKOFF_MAX_S = 30.0

# Per-host politeness: concurrency=1 is structural (this harvester is
# sequential by construction — nothing here spawns threads/async fan-out
# across hosts), and this is the enforced MINIMUM SPACING between two
# requests to the same host, with jitter so a run does not look like a
# metronome. Operational, not architectural: raise/lower per environment.
DEFAULT_MIN_HOST_INTERVAL_S = 3.0
DEFAULT_JITTER_S = 2.0

# `LeadStore.accounts()` clamps to MAX_PAGE=100 (see lead_store.py). This
# mirrors the same bounded-scan convention h1_buysw_dom.py already uses for
# its own dedup scan (`_STORE_SCAN_LIMIT = 500`) — a bounded, not literally
# unbounded, existing-row scan is the established pattern here, not a
# shortcut invented for this module.
STORE_SCAN_LIMIT = 100

MAX_TEXT = 1200
MAX_SHORT = 220

# ── Geographic + industry query matrix (extensible, not a fixed handful) ────
# Broad Australian coverage: every state/territory plus major metro and a
# sample of regional centres, so the query strategy is not silently
# Sydney-only. Callers may pass their own `regions`/`industries` to
# build_search_queries to extend this further without touching this module.
AU_STATES = ("NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT")

AU_REGIONS = (
    # Every city carries its state (a live run proved this matters: bare
    # "Newcastle" pulled in Newcastle-upon-Tyne, UK results — .co.uk
    # domains, "Tyne and Wear" addresses — because nothing in the query
    # said which Newcastle; "Perth" [Scotland], "Sydney" [Nova Scotia,
    # Canada] and generic "Melbourne"/"Brisbane" spellings carry the same
    # risk). "Australia" and the bare state/territory abbreviations are the
    # only unqualified entries — those genuinely have no overseas homonym
    # collision at this specificity.
    "Australia", "NSW", "Sydney NSW", "Newcastle NSW", "Wollongong NSW",
    "Central Coast NSW",
    "VIC", "Melbourne VIC", "Geelong VIC", "Ballarat VIC",
    "QLD", "Brisbane QLD", "Gold Coast QLD", "Sunshine Coast QLD",
    "Townsville QLD", "Cairns QLD",
    "WA", "Perth WA", "Fremantle WA",
    "SA", "Adelaide SA",
    "TAS", "Hobart TAS", "Launceston TAS",
    "ACT", "Canberra ACT",
    "NT", "Darwin NT",
)

# Deliberately broad and easy to extend — the spec calls out commercial
# property, facilities management, strata, construction, property
# management, government/public property, aged care, education,
# retail/property groups, industrial property, real estate and building
# maintenance by name; all are represented here as independent, addable
# entries rather than baked into one hard-coded query string.
INDUSTRY_TERMS = (
    # NOTE: deliberately no "commercial painting companies" term. This table
    # is a CUSTOMER-prospect list (every one of the real existing rows is a
    # strata/facility/property/government company; none is a painting
    # business) - searching for painting companies surfaces competitors, not
    # prospects. A live run caught this exact mistake; see HANDOFF/report.
    "facilities management companies",
    "facility management",
    "strata management companies",
    "strata management",
    "property management companies",
    "commercial property managers",
    "building management",
    "commercial construction companies",
    "property maintenance companies",
    "building maintenance contractors",
    "government property services",
    "public housing property management",
    "aged care facilities management",
    "education facilities management",
    "retail property group",
    "shopping centre management",
    "industrial property management",
    "real estate asset management",
    "body corporate management",
)

# A category label for each industry term, used only to give a discovered
# account a sensible, honest `segment` value (never invented data — just a
# classification of which query bucket found it). Free text on the store
# side (painting_b2b_accounts.segment has no CHECK constraint), matching
# real existing rows such as "commercial"/"government"/"strata".
_SEGMENT_BY_KEYWORD = (
    ("strata", "strata"), ("body corporate", "strata"),
    ("facilit", "facility_management"),
    ("property management", "property_management"),
    ("property manager", "property_management"),
    ("government", "government"), ("public housing", "government"),
    ("aged care", "aged_care"),
    ("education", "education"),
    ("retail", "retail_property"), ("shopping centre", "retail_property"),
    ("industrial property", "industrial_property"),
    ("real estate", "real_estate"),
    ("construction", "commercial_construction"),
    ("maintenance", "building_maintenance"),
    ("building management", "commercial"),
    ("painting", "commercial"),
)


def segment_for_industry(industry: str) -> str:
    """Classify a discovered candidate's industry text into a segment label.

    Always falls back to 'commercial' rather than guessing something more
    specific than the evidence supports.
    """
    text = (industry or "").lower()
    for needle, label in _SEGMENT_BY_KEYWORD:
        if needle in text:
            return label
    return "commercial"


def build_search_queries(
    regions: Sequence[str] = AU_REGIONS,
    industries: Sequence[str] = INDUSTRY_TERMS,
) -> tuple[str, ...]:
    """Cross-join industries x regions into search-query strings, ordered so
    that ANY prefix of the result is a broad sample across both axes.

    Pure and deterministic. Extensible by construction: passing a longer
    `regions`/`industries` sequence produces more queries, with no other
    code change required — the query count is a function of these two
    sequences, never a fixed literal list of query strings.

    Ordering matters once an operational cap (--max-queries-per-source)
    takes a prefix of this list for one run. A plain nested loop (industry
    outer, region inner) puts a small prefix entirely inside industry[0] -
    a live run against html.duckduckgo.com did exactly that: the first 12
    queries were all the same industry term in 12 different cities, and
    every other industry was never reached. Filling the (industry, region)
    grid diagonally - by increasing max(i, r) - means the earliest entries
    already span several distinct industries AND several distinct regions,
    so a capped run still samples broadly instead of exhausting one term.
    """
    n_i, n_r = len(industries), len(regions)
    if n_i == 0 or n_r == 0:
        return ()
    pairs = sorted(
        ((i, r) for i in range(n_i) for r in range(n_r)),
        key=lambda pair: (max(pair), pair),
    )
    seen: set[str] = set()
    out: list[str] = []
    for i, r in pairs:
        q = f"{industries[i]} {regions[r]}".strip()
        if q not in seen:
            seen.add(q)
            out.append(q)
    return tuple(out)


# ── AU contact extraction (extraction, not redaction) ───────────────────────
# kernel/scrub.py's phone rule exists to REDACT personal numbers and
# deliberately does not match 1300/1800 lines (those are not personally
# identifying). This agent's job is the opposite: find genuine, PUBLICLY
# published AU business phone numbers, 1300/1800 included, so the pattern
# here is intentionally a different, purpose-built one — not a reuse of
# scrub.py's redaction regex, which would silently drop the exact numbers
# this task requires (+61/02/03/04/1300/1800).
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# Broad candidate finder: any digit-ish run of plausible phone length. The
# actual AU-shape validation happens in `_valid_au_phone` on the stripped
# digits, so this stays permissive without needing an unreadable megaregex.
_PHONE_CANDIDATE_RE = re.compile(r"(?<!\w)((?:\+|\()?\d[\d\s().-]{6,17}\d\)?)(?!\w)")


def _valid_au_phone(digits: str) -> bool:
    if not digits or not digits.isdigit():
        return False
    d = digits
    if d.startswith("61") and len(d) == 11:
        d = "0" + d[2:]                       # +61 2 xxxx xxxx -> 02 xxxx xxxx
    if len(d) == 10 and d[0] == "0" and d[1] in "23478":
        return True                           # 02/03/04/07/08 landline+mobile
    if len(d) == 10 and d[:4] in ("1300", "1800", "1900"):
        return True                           # AU business/service numbers
    return False


def _phone_key(digits: str) -> str:
    """Normalize to one canonical key so +61 2 9876 5432 and 02 9876 5432
    dedupe as the SAME number — the same idea lead_store._contact_hash
    already uses for AU phone normalization, applied here for identity
    rather than hashing."""
    d = digits
    if d.startswith("61") and len(d) == 11:
        d = "0" + d[2:]
    return d


def extract_phones(text: str) -> list[str]:
    """Extract genuinely-present AU phone numbers from free text.

    Never fabricates: an empty/no-match input returns []. Two spellings of
    the same number (intl vs domestic) collapse to one entry, preserving
    the first-seen display form.
    """
    seen: set[str] = set()
    out: list[str] = []
    for m in _PHONE_CANDIDATE_RE.finditer(text or ""):
        raw = m.group(1)
        digits = re.sub(r"\D", "", raw)
        if not _valid_au_phone(digits):
            continue
        key = _phone_key(digits)
        if key in seen:
            continue
        seen.add(key)
        out.append(raw.strip())
    return out


# A live fetch during this fix found extract_emails happily returning
# "youremail@mail.com" — the placeholder attribute of a Contact Form 7
# <input placeholder="youremail@mail.com">, not any person's address. It
# genuinely IS text on the page (so this is not "fabrication" in the sense
# of inventing bytes that were never there), but presenting boilerplate
# form-field placeholder text as a real business contact is exactly the
# false-positive the spec's "never fabricate contact info" concern is
# about in practice, so known placeholder shapes are excluded here. This
# is a quality filter over the SAME real-only extraction, not a second
# fabrication path: a placeholder email that ISN'T excluded still passes
# through untouched, and nothing here invents a replacement address.
_PLACEHOLDER_EMAIL_DOMAINS = frozenset({
    "example.com", "example.org", "example.net", "test.com", "domain.com",
    "yourdomain.com", "yoursite.com", "email.com", "yourcompany.com",
})
_PLACEHOLDER_LOCAL_PREFIXES = (
    "youremail", "your-email", "your.email", "yourname", "your-name",
    "example", "test", "sample", "placeholder", "someone",
    "firstname", "john.doe", "jane.doe", "name@",
)


def _is_placeholder_email(email: str) -> bool:
    local, _, domain = email.lower().partition("@")
    if domain in _PLACEHOLDER_EMAIL_DOMAINS:
        return True
    return any(local == p.rstrip("@") or local.startswith(p.rstrip("@"))
              for p in _PLACEHOLDER_LOCAL_PREFIXES)


def extract_emails(text: str) -> list[str]:
    """Extract publicly-displayed email addresses. Never fabricates - and
    never passes through a recognized form-placeholder string either, even
    though that string is technically present in the page's own HTML (see
    _is_placeholder_email)."""
    seen: set[str] = set()
    out: list[str] = []
    for m in _EMAIL_RE.finditer(text or ""):
        e = m.group(0)
        if _is_placeholder_email(e):
            continue
        key = e.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


# ── Name / domain normalization for identity resolution ─────────────────────
# Only true legal-entity suffixes are stripped for identity comparison.
# Business-descriptor words ("strata", "management", "group", "services")
# are deliberately left alone: "McCormacks Strata" and "McCormacks Strata
# Management" must NOT collapse to the same normalized name on name alone —
# that is exactly the over-aggressive merge the spec warns against. They can
# still be recognized as the same company, but only via a corroborating
# signal (the domain) — see resolve_identity's Tier A/B/C.
_LEGAL_SUFFIXES = (
    "proprietary limited", "pty ltd", "pty. ltd.", "pty limited",
    "limited", "ltd", "incorporated", "inc", "llc",
)

# Generic trailing words that, when they are the ONLY difference between two
# otherwise-identical names, mark a *possible* (never automatic) duplicate.
_GENERIC_TRAILING_WORDS = frozenset({
    "management", "group", "services", "holdings", "australia", "sydney",
})


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation/whitespace, strip a trailing legal
    suffix only. Conservative by design — see module docstring."""
    n = (name or "").lower().strip()
    n = re.sub(r"[^\w\s]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    for suf in sorted(_LEGAL_SUFFIXES, key=len, reverse=True):
        if n == suf:
            return ""
        if n.endswith(" " + suf):
            n = n[: -(len(suf) + 1)].strip()
            break
    return n


def _strip_generic_trailing(normalized: str) -> str:
    words = normalized.split()
    while words and words[-1] in _GENERIC_TRAILING_WORDS:
        words.pop()
    return " ".join(words)


def _is_possible_duplicate(name_a_norm: str, name_b_norm: str) -> bool:
    """True when the two names are identical once trailing generic words are
    removed, but were NOT already an exact match. Signals "maybe", never
    "definitely" — callers must treat this as a flag, not a merge."""
    if not name_a_norm or not name_b_norm or name_a_norm == name_b_norm:
        return False
    a2 = _strip_generic_trailing(name_a_norm)
    b2 = _strip_generic_trailing(name_b_norm)
    return bool(a2) and a2 == b2


def registrable_domain(url_or_host: str) -> str:
    """Normalize a URL/host to a comparable domain: strip scheme, path,
    query, userinfo, port and a leading 'www.'. Not a full public-suffix
    implementation (no new dependency) — good enough for exact-domain
    identity matching, not for anything security-sensitive."""
    s = (url_or_host or "").strip().lower()
    if not s:
        return ""
    s = re.sub(r"^[a-z][a-z0-9+.\-]*://", "", s)
    s = s.split("/", 1)[0]
    s = s.split("?", 1)[0].split("#", 1)[0]
    s = s.split("@")[-1]
    s = s.split(":")[0]
    if s.startswith("www."):
        s = s[4:]
    return s


def _looks_like_single_url(value: str) -> str:
    """Return `value` trimmed if it is exactly one plausible URL/host, else
    "". Multiple comma/space/semicolon-separated candidates are ambiguous
    and must never be guessed at — 'website not found' beats a fabricated
    pick among several possibilities."""
    v = (value or "").strip()
    if not v:
        return ""
    for sep in (",", ";", " and ", "|", "\n"):
        if sep in v:
            return ""
    if v.count("http://") + v.count("https://") > 1:
        return ""
    if " " in v.strip():
        return ""
    return v


# ── Real business-name extraction (not a search-engine <title>) ─────────────
# A search-result title is SEO copy the page's owner wrote for a search
# engine, not the business's name - a live run on the real store confirmed
# titles like "Home", "Top 20 Facility Management Companies in Australia
# 2026 Guide" and "Facilities Management Sydney |Facilities Management
# Companies Sydney" landing verbatim in business_name. The fix is a priority
# chain, each step strictly more reliable than the fallback below it:
#
#   1. og:site_name meta tag on the candidate's OWN fetched homepage - the
#      business declaring its own name, the strongest signal available.
#   2. schema.org Organization/LocalBusiness JSON-LD `name` on that same
#      fetched page - same authority as (1), different markup convention.
#   3. That page's own <title>, cleaned (see clean_title_name below) - still
#      the business's own page, just unstructured.
#   4. The ORIGINAL search-result title, cleaned the same way - used only
#      when the homepage could not be fetched at all (blocked/error), so a
#      transient 403 on enrichment does not have to cost the whole
#      candidate.
#
# If none of the four yields a reliable name, extract_business_name returns
# "" and the caller must drop the candidate - a real company with no
# verifiable name beats a fabricated one, but a page with no verifiable name
# is not a lead at all (see normalize_candidate's business_name is
# non-negotiable rule, unchanged by this).
_TITLE_TAG_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_OG_SITE_NAME_RE = re.compile(
    r'<meta\s+[^>]*?\bproperty=["\']og:site_name["\'][^>]*?\bcontent=["\']([^"\']+)["\']'
    r'|<meta\s+[^>]*?\bcontent=["\']([^"\']+)["\'][^>]*?\bproperty=["\']og:site_name["\']',
    re.IGNORECASE,
)
_LD_JSON_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
_ORG_LD_TYPES = ("organization", "localbusiness", "corporation")


def _extract_title_tag(html: str) -> str:
    m = _TITLE_TAG_RE.search(html or "")
    return _clean_html_text(m.group(1)) if m else ""


def extract_og_site_name(html: str) -> str:
    """The business's own declared name via Open Graph. Attribute order in
    the tag is not guaranteed, so both orders are matched explicitly rather
    than assumed."""
    m = _OG_SITE_NAME_RE.search(html or "")
    if not m:
        return ""
    return _clean(m.group(1) or m.group(2), 180)


def extract_schema_org_name(html: str) -> str:
    """The business's own declared name via schema.org JSON-LD. Tolerant of
    a single object, a list of objects, and a multi-typed `@type` array;
    malformed JSON-LD is skipped rather than raising - one bad script block
    on an otherwise-real page must not sink the whole candidate."""
    import json
    for m in _LD_JSON_RE.finditer(html or ""):
        try:
            data = json.loads(m.group(1).strip())
        except (ValueError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            typ = item.get("@type", "")
            typ_text = " ".join(typ) if isinstance(typ, list) else str(typ)
            if any(t in typ_text.lower() for t in _ORG_LD_TYPES):
                name = _clean(item.get("name"), 180)
                if name:
                    return name
    return ""


# Words that are true of almost every result in this table's target
# industries (place names + generic service/corporate vocabulary) and so
# carry ~zero identifying information on their own. AU_REGIONS is reused
# directly (not retyped) so the geo half of this list can never drift out of
# sync with the query matrix itself.
_GENERIC_NAME_TOKENS = frozenset({
    "home", "welcome", "index", "homepage", "site", "website", "your",
    "facilities", "facility", "management", "company", "companies",
    "services", "service", "solutions", "group", "provider", "providers",
    "commercial", "property", "properties", "maintenance",
} | {w.lower() for region in AU_REGIONS for w in region.replace(",", " ").split()})

# Split only on a separator a title actually uses between an SEO phrase and
# a brand: a pipe (loose spacing - real titles were seen both "A | B" and
# "A |B"), or a hyphen/en-dash/em-dash WITH a space on both sides. A bare
# mid-word hyphen ("Sydney-Wide") is deliberately NOT a split point.
_TITLE_SEP_RE = re.compile(r"\s*\|\s*|\s+[–—]\s+|\s+-\s+")

# The search backend itself truncates a long title with a trailing ellipsis
# (a real stored value found during this fix: "Aurora ..." - 10 characters,
# not a display artifact) - this is the search engine's own snippet limit,
# not a separator, so it is trimmed off the chosen segment rather than
# treated as part of the name.
_TRAILING_ELLIPSIS_RE = re.compile(r"[.…\s]+$")


def _segment_is_reliable(segment: str) -> bool:
    words = re.findall(r"[A-Za-z']+", segment.lower())
    return bool(words) and any(w not in _GENERIC_NAME_TOKENS for w in words)


def clean_title_name(title: str) -> str:
    """The first SEGMENT of a title that survives the generic-word test, not
    simply the first segment. A real, confirmed pattern this exists for:
    "Home - Marion Facilities Management" and "Facilities Management
    Company | Sydney, Melbourne & Brisbane | NFM" both put the real name in
    a LATER segment, after a generic lead-in - taking only segment[0] would
    have kept "Home" and thrown "Marion Facilities Management" away.
    Returns "" when every segment is exhausted without one surviving -
    callers must treat that as "no reliable name", not fall back further."""
    t = _clean(title, 200)
    if not t:
        return ""
    for raw_segment in _TITLE_SEP_RE.split(t):
        segment = _TRAILING_ELLIPSIS_RE.sub("", raw_segment.strip()).strip()
        if segment and _segment_is_reliable(segment):
            return segment
    return ""


def extract_business_name(*, original_title: str, fetched_html: str | None) -> str:
    """The priority chain described above the extractor functions. `fetched_html`
    is None when the candidate's homepage could not be retrieved at all
    (blocked/error/no website) - that case skips straight to cleaning the
    original search-result title.

    og:site_name/JSON-LD are run through clean_title_name too, not trusted
    as an atomic string - a live fetch during this fix found a real site's
    OWN og:site_name literally reading "Australis Facilities Management |
    Just another WordPress site" (the CMS's uncustomized default tagline,
    baked in by an SEO plugin). "The business declared its own name" turns
    out not to guarantee the business actually edited that field.
    """
    if fetched_html:
        raw_name = extract_og_site_name(fetched_html) or extract_schema_org_name(fetched_html)
        name = clean_title_name(raw_name) if raw_name else ""
        if name:
            return name
        page_title_name = clean_title_name(_extract_title_tag(fetched_html))
        if page_title_name:
            return page_title_name
    return clean_title_name(original_title)


# ── Article/listicle filter ──────────────────────────────────────────────────
# "Top 20 Facility Management Companies in Australia" is a ranking blog post
# ABOUT several companies, not a single company's own page - a real live run
# put exactly this (and its near-twin "...Compared") into business_name.
# Quality filter, same standing as KNOWN_AGGREGATOR_HOSTS: extend only from a
# real observed miss, never preemptively.
_ARTICLE_URL_PATTERNS = (
    "/blog/", "/top-", "/best-", "/list-", "/guide/", "-guide/",
    "/news/", "/article/",
)
_ARTICLE_TITLE_RE = re.compile(
    r"\btop\s*\d*\b.{0,40}\bcompanies\b"
    r"|\bbest\s*\d*\b.{0,40}\bcompanies\b"
    r"|\b\d+\s+(?:best|top|leading)\b"
    r"|\bleading\b.{0,40}\bcompanies\b"
    r"|\bcompar(?:ed|ison)\b",
    re.IGNORECASE,
)


def looks_like_article(*, url: str, title: str) -> bool:
    """True for a directory/listicle page found BY a search query, as
    distinct from a single company's own page. URL patterns catch the
    common blog/listicle path shapes; the title regex catches "Top N ...
    Companies", "N Best ...", "Leading ... Companies" and "... Compared"
    even when the URL itself gives no hint (a listicle hosted as a page on
    a real company's own marketing site, seen in a live run, has neither
    "/blog/" nor "/top-" in its path)."""
    path = urlparse(url).path.lower() if url else ""
    if any(p in path for p in _ARTICLE_URL_PATTERNS):
        return True
    return bool(_ARTICLE_TITLE_RE.search(title or ""))


# ── Customer-vs-provider classification ──────────────────────────────────────
# A strata/property/body-corporate manager NEEDS a painting contractor; a
# pure facilities-management company might BE one (or self-perform in
# house), so it is left uncertain rather than assumed either way; a company
# that explicitly advertises its OWN painting service is the one case with
# strong enough evidence to call it a likely competitor/provider outright.
_LIKELY_CUSTOMER_SEGMENTS = frozenset({
    "strata", "property_management", "government", "aged_care",
    "education", "retail_property", "industrial_property", "real_estate",
})
_CUSTOMER_TEXT_HINTS = (
    "strata management", "strata manager", "body corporate", "property management",
)
_PROVIDER_TEXT_HINTS = (
    "painting services", "painting service", "in-house painting",
    "our painters", "we provide painting", "painting and decorating",
)


def classify_candidate(*, segment: str, text: str) -> str:
    """One of "likely_customer" / "likely_provider" / "uncertain".
    `text` should be every honestly-available signal (industry query text,
    plus fetched page text when enrichment succeeded) - never invented."""
    t = (text or "").lower()
    if any(h in t for h in _PROVIDER_TEXT_HINTS):
        return "likely_provider"
    if segment in _LIKELY_CUSTOMER_SEGMENTS or any(h in t for h in _CUSTOMER_TEXT_HINTS):
        return "likely_customer"
    return "uncertain"


# ── Candidate shape ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Candidate:
    """One normalized discovery result — the fields the spec asks for,
    limited to what the source actually provided. Missing is empty, never
    guessed."""
    business_name: str
    website: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    suburb: str = ""
    state: str = ""
    industry: str = ""
    source: str = ""
    source_url: str = ""
    source_type: str = ""
    notes: str = ""
    classification: str = "uncertain"
    enrichment_status: str = "not_attempted"


def _clean(value: object, limit: int = MAX_TEXT) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def normalize_candidate(raw: Mapping) -> Candidate | None:
    """Raw source dict -> Candidate, or None if unusable.

    A business name is the one non-negotiable field — everything else is
    kept only when the source actually supplied it. An ambiguous/multi-URL
    website hint is dropped (empty), never guessed.
    """
    name = _clean(raw.get("business_name") or raw.get("name"), 180)
    if not name:
        return None
    website_hint = _looks_like_single_url(_clean(raw.get("website"), 300))
    return Candidate(
        business_name=name,
        website=website_hint,
        phone=_clean(raw.get("phone"), 40),
        email=_clean(raw.get("email"), 160),
        address=_clean(raw.get("address"), 220),
        suburb=_clean(raw.get("suburb"), 120),
        state=_clean(raw.get("state"), 20).upper() if raw.get("state") else "",
        industry=_clean(raw.get("industry"), 120),
        source=_clean(raw.get("source"), 80) or "unknown",
        source_url=_clean(raw.get("source_url") or raw.get("url"), 300),
        source_type=_clean(raw.get("source_type"), 40) or "unknown",
        notes=_clean(raw.get("notes"), MAX_TEXT),
        classification=_clean(raw.get("classification"), 20) or "uncertain",
        enrichment_status=_clean(raw.get("enrichment_status"), 20) or "not_attempted",
    )


# ── Identity resolution (the core anti-duplicate logic) ─────────────────────

@dataclass(frozen=True)
class IdentityMatch:
    kind: str            # "new" | "match" | "possible_duplicate"
    account_id: str | None
    reason: str


def resolve_identity(candidate: Candidate, existing: Sequence[Mapping]) -> IdentityMatch:
    """Compare one candidate against the known accounts (existing DB rows
    plus any created earlier in the same run). Tiered, conservative:

      Tier A: candidate.website's domain == an existing account's website
              domain -> match (strongest signal available in this schema).
      Tier B: normalized name (legal-suffix stripped only) is IDENTICAL to
              an existing normalized name -> match.
      Tier C: names are identical only after also stripping a generic
              trailing word ("management"/"group"/...) -> possible_duplicate.
              Never auto-merged; both candidates are preserved for review.
      Tier D: nothing matches -> new.

    Weak name-only similarity never reaches "match" on its own — only an
    exact (post conservative-normalization) name, or a real domain match,
    does. This is deliberate: "McCormacks Strata" vs "McCormacks Strata
    Management" must not merge on name alone, but WILL correctly resolve to
    the same account once a shared domain corroborates it (Tier A runs
    first).
    """
    cand_domain = registrable_domain(candidate.website) if candidate.website else ""
    cand_norm = normalize_name(candidate.business_name)

    if cand_domain:
        for row in existing:
            other_domain = registrable_domain(str(row.get("website") or ""))
            if other_domain and other_domain == cand_domain:
                return IdentityMatch("match", row.get("account_id"),
                                     f"same website domain: {cand_domain}")

    for row in existing:
        other_norm = normalize_name(str(row.get("business_name") or ""))
        if cand_norm and other_norm and cand_norm == other_norm:
            return IdentityMatch("match", row.get("account_id"),
                                 f"same normalized name: {cand_norm!r}")

    for row in existing:
        other_norm = normalize_name(str(row.get("business_name") or ""))
        if _is_possible_duplicate(cand_norm, other_norm):
            return IdentityMatch("possible_duplicate", row.get("account_id"),
                                 f"name similarity only (no domain evidence): "
                                 f"{candidate.business_name!r} vs "
                                 f"{row.get('business_name')!r}")

    return IdentityMatch("new", None, "no matching signal found")


def merge_account(candidate: Candidate, existing: Mapping | None) -> tuple[dict, bool]:
    """Build the payload to pass to LeadStore.create_account.

    Never lets an empty candidate field blank out a non-empty existing
    value — `create_account`'s UPSERT overwrites every column
    unconditionally, so the safety has to live here, at the call site.
    Returns (payload, changed) where `changed` is False only when every
    field the candidate could contribute was already present verbatim
    (a pure re-confirmation, not new information).

    AUTO_DISCOVERY_TAG plus this candidate's CLASSIFICATION/ENRICHMENT are
    stamped into notes ONLY when `existing` is None (a genuinely brand-new
    account). This check happens here, before the `existing or {}`
    normalization below, specifically so it is never confused with a real
    but merely-sparse existing row: every caller in this module only ever
    passes None for a Tier D/"new" or Tier C/"possible_duplicate" verdict,
    and a real store row (Tier A/B "match") otherwise — see
    resolve_identity — so `existing is None` here means exactly "this
    module is about to CREATE this account", never "this account happens to
    have little data". Tagging an already-existing row — including one of
    the 74 hand-researched accounts this agent must never mark unverified —
    would require `existing` to be a real dict, which this branch excludes.
    """
    is_new = existing is None
    existing = existing or {}
    changed = existing == {}

    def pick(field_name: str, cand_value: str) -> str:
        nonlocal changed
        old = _clean(existing.get(field_name), MAX_SHORT)
        new = _clean(cand_value, MAX_SHORT)
        if not new:
            return old
        if not old:
            changed = True
            return new
        if new.lower() == old.lower():
            return old
        return old  # a differing non-empty existing value wins; see notes

    business_name = existing.get("business_name") or candidate.business_name
    if not existing.get("business_name"):
        changed = True

    website = pick("website", candidate.website)
    suburb = pick("suburb", candidate.suburb)
    service_area = pick("service_area", candidate.state)

    contact_bits = []
    if candidate.phone:
        contact_bits.append(f"phone: {candidate.phone}")
    if candidate.email:
        contact_bits.append(f"email: {candidate.email}")
    new_contact = "; ".join(contact_bits)
    old_contact = _clean(existing.get("contact_channel"), MAX_SHORT)
    if new_contact and new_contact.lower() not in old_contact.lower():
        contact_channel = (old_contact + ("; " if old_contact else "") + new_contact)[:MAX_SHORT]
        changed = True
    else:
        contact_channel = old_contact

    evidence_url = existing.get("evidence_url") or candidate.source_url
    if not existing.get("evidence_url") and candidate.source_url:
        changed = True

    provenance = (
        f"Discovered via {candidate.source_type or 'unknown'} "
        f"({candidate.source or 'unknown'})"
        + (f" at {candidate.source_url}" if candidate.source_url else "")
        + (f". Address: {candidate.address}" if candidate.address else "")
        + (f". Industry: {candidate.industry}" if candidate.industry else "")
    )
    if is_new:
        provenance += (
            f" | {AUTO_DISCOVERY_TAG}"
            f" | CLASSIFICATION: {candidate.classification}"
            f" | ENRICHMENT: {candidate.enrichment_status}"
        )
    old_notes = _clean(existing.get("notes"), MAX_TEXT)
    if provenance and provenance not in old_notes:
        notes = (old_notes + (" | " if old_notes else "") + provenance)[:MAX_TEXT]
        changed = True
    else:
        notes = old_notes

    segment = existing.get("segment") or segment_for_industry(candidate.industry)

    payload = {
        "business_name": business_name,
        "segment": segment,
        "website": website,
        "suburb": suburb,
        "service_area": service_area,
        "contact_channel": contact_channel,
        "evidence_url": evidence_url,
        "notes": notes,
    }
    if existing.get("account_id"):
        payload["account_id"] = existing["account_id"]
    if existing.get("stage"):
        payload["stage"] = existing["stage"]
    return payload, changed


# ── Rate limiting (per-host, stateless verdict style like rate_limit.py) ────

@dataclass
class HostThrottle:
    """Per-host minimum spacing between requests. Concurrency=1 is
    structural (this harvester never issues two requests to any host at
    once); this class enforces the MINIMUM DELAY between consecutive
    requests to the SAME host, with jitter. Pure/testable: `now` and the
    jitter source are both injectable, no real clock required in tests.
    """
    min_interval_s: float = DEFAULT_MIN_HOST_INTERVAL_S
    jitter_s: float = DEFAULT_JITTER_S
    _jitter_fn: Callable[[], float] = field(default=lambda: 0.0, repr=False)
    _last: dict[str, float] = field(default_factory=dict, repr=False)

    def wait_seconds(self, host: str, *, now: float) -> float:
        last = self._last.get(host)
        if last is None:
            return 0.0
        elapsed = now - last
        remaining = self.min_interval_s - elapsed
        return max(0.0, remaining)

    def record(self, host: str, *, now: float) -> None:
        self._last[host] = now

    def throttle(self, host: str, *, now: Callable[[], float], sleep: Callable[[float], None]) -> None:
        current = now()
        wait = self.wait_seconds(host, now=current)
        if self.jitter_s:
            wait += self.jitter_s * self._jitter_fn()
        if wait > 0:
            sleep(wait)
            current = now()
        self.record(host, now=current)


# ── robots.txt ───────────────────────────────────────────────────────────────

def _default_fetch_robots(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return resp.read().decode("utf-8", "replace")
    except Exception:                          # noqa: BLE001 — fail-open, see RobotsGate
        return None


class RobotsGate:
    """Per-host robots.txt cache, backed by stdlib urllib.robotparser.

    `fetch` is injectable so tests never touch the network. When robots.txt
    itself cannot be fetched (missing, network error), the host is treated
    as allowed — the common convention that absence of a robots file means
    no restriction was declared. When robots.txt IS reachable, its rules
    are followed exactly; a Disallow is never bypassed.
    """

    def __init__(self, *, fetch: Callable[[str], str | None] = _default_fetch_robots,
                user_agent: str = USER_AGENT) -> None:
        self._fetch = fetch
        self._user_agent = user_agent
        self._parsers: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def _parser_for(self, url: str) -> urllib.robotparser.RobotFileParser | None:
        parsed = urlparse(url)
        host = parsed.netloc
        if host in self._parsers:
            return self._parsers[host]
        robots_url = f"{parsed.scheme}://{host}/robots.txt"
        body = self._fetch(robots_url)
        parser = None
        if body is not None:
            parser = urllib.robotparser.RobotFileParser()
            parser.parse(body.splitlines())
        self._parsers[host] = parser
        return parser

    def allowed(self, url: str) -> bool:
        parser = self._parser_for(url)
        if parser is None:
            return True             # fail-open: no robots.txt found/reachable
        try:
            return parser.can_fetch(self._user_agent, url)
        except Exception:            # noqa: BLE001 — a malformed file must not crash a run
            return True


# ── The one real I/O boundary ────────────────────────────────────────────────

class HarvestError(Exception):
    """Fetch/parse failure — park, never crash the run (seek_harvest.py's
    contract)."""


def fetch_url(
    url: str,
    *,
    opener: Callable[..., object] = urllib.request.urlopen,
    robots: RobotsGate,
    throttle: HostThrottle,
    now: Callable[[], float] = time.time,
    sleep: Callable[[float], None] = time.sleep,
    user_agent: str = USER_AGENT,
    timeout: int = TIMEOUT_S,
    data: bytes | None = None,
) -> dict:
    """One polite GET (or, with `data`, POST — some public endpoints, e.g.
    html.duckduckgo.com/html/, are the target of a <form method="post">, and
    a query-string GET to the same path is simply the wrong HTTP verb for
    it, not a restriction of any kind: robots.txt has no method concept, it
    governs the path, and the path stays exactly as declared). Returns a
    result dict, never raises.

    kind is one of: "ok", "robots_disallowed", "blocked_403", "blocked_429",
    "error". 403 is a policy answer and is never retried (demand_harvest.py's
    documented rule); 429/5xx back off exponentially up to MAX_RETRIES
    (also demand_harvest.py); anything else retries with the same backoff
    then gives up, exactly like seek_harvest.py's "retry then park".
    """
    if not robots.allowed(url):
        return {"ok": False, "kind": "robots_disallowed", "status": None,
                "body": None, "url": url}

    host = urlparse(url).netloc
    throttle.throttle(host, now=now, sleep=sleep)

    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            headers = {"User-Agent": user_agent, "Accept": "text/html,application/json"}
            if data is not None:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            req = urllib.request.Request(url, data=data, headers=headers)
            resp = opener(req, timeout=timeout)
            with resp as r:
                body = r.read()
                if isinstance(body, bytes):
                    body = body.decode("utf-8", "replace")
                code = r.getcode() if hasattr(r, "getcode") else 200
            return {"ok": True, "kind": "ok", "status": code, "body": body, "url": url}
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                return {"ok": False, "kind": "blocked_403", "status": 403,
                        "body": None, "url": url}
            if exc.code in (429, 500, 502, 503, 504):
                last_exc = exc
                sleep(min(BACKOFF_BASE_S * (2 ** attempt), BACKOFF_MAX_S))
                continue
            return {"ok": False, "kind": "error", "status": exc.code,
                    "body": None, "url": url}
        except Exception as exc:               # noqa: BLE001 — park, don't crash
            last_exc = exc
            sleep(min(BACKOFF_BASE_S * (2 ** attempt), BACKOFF_MAX_S))
    kind = "blocked_429" if isinstance(last_exc, urllib.error.HTTPError) else "error"
    return {"ok": False, "kind": kind, "status": None, "body": str(last_exc), "url": url}


# ── A real SearchSource backend: html.duckduckgo.com ────────────────────────
# html.duckduckgo.com is a DIFFERENT host from duckduckgo.com/www.duckduckgo.com
# (robots.txt is per-host, never per "domain family") and its own robots.txt
# is `Allow: /` — verified live before this was written, not assumed. Its
# /html/ endpoint is the target of a <form method="post">: a GET with a
# query string to that same path is simply the wrong HTTP verb, which is why
# fetch_url grew a `data=` (POST) option above rather than this module
# adopting a different User-Agent to "get past" anything — the honest,
# transparent USER_AGENT this module already uses everywhere else is exactly
# what is sent here too, and it works, because there was never an identity
# check to get past: the earlier hang was the verb, not who was asking.
_DDG_SEARCH_URL = "https://html.duckduckgo.com/html/"
_DDG_RESULT_RE = re.compile(
    r'<a rel="nofollow" class="result__a" href="([^"]+)">(.*?)</a>', re.DOTALL)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HTML_ENTITIES = {
    "&amp;": "&", "&#x27;": "'", "&quot;": '"', "&lt;": "<", "&gt;": ">", "&nbsp;": " ",
}

# Result pages that are themselves directories/comparison sites, not a real
# B2B prospect — a quality filter, not a correctness one: leaving one of
# these in would not fabricate anything, it would just waste a row. Short
# and extensible; unrecognized hosts are never excluded on a guess.
KNOWN_AGGREGATOR_HOSTS = frozenset({
    "comparestrata.com", "localbusinessguide.com.au", "yellowpages.com.au",
    "whitepages.com.au", "truelocal.com.au", "hotfrog.com.au", "yelp.com",
    "wikipedia.org", "facebook.com", "linkedin.com", "youtube.com",
    # Added from a real live run against html.duckduckgo.com: company
    # databases, review platforms and market-research firms that show up
    # for "X companies in Australia"-style queries but are not themselves
    # an X company - lead-gen/directory/analyst businesses, not prospects.
    "ensun.io", "companydata.com", "clutch.co", "mordorintelligence.com",
    "aeroleads.com", "productreview.com.au",
    # Job boards and Yellow-Pages-style directories: a job listing or a
    # directory search-results page is not itself a company.
    "au.seek.com", "seek.com.au", "au.jora.com", "jora.com", "australiayp.com",
})


def _clean_html_text(raw_html: str) -> str:
    text = _HTML_TAG_RE.sub("", raw_html)
    for ent, ch in _HTML_ENTITIES.items():
        text = text.replace(ent, ch)
    return re.sub(r"\s+", " ", text).strip()


# Geographic scope guard: this agent targets Australia (the spec is explicit
# about this), and a bare city name in a query can collide with a same-named
# overseas city no matter how carefully the region list is worded (see
# AU_REGIONS' comment). A live run proved this concretely: one under-
# specified "Newcastle" query returned 10 genuine Newcastle-upon-Tyne, UK
# facilities-management companies — real businesses, just the wrong country,
# which is a scope violation, not merely "incomplete data". The region-name
# fix addresses the query side; this is the defense-in-depth check on the
# result side. Extend only with evidence (a real run surfacing another
# non-AU TLD), same discipline as KNOWN_AGGREGATOR_HOSTS.
NON_AU_TLD_SUFFIXES = (".uk",)


def parse_duckduckgo_html(body: str) -> list[dict]:
    """Real-result-page parser, written against actual captured markup
    (tests/test_b2b_discovery.py embeds the verified real fixture this was
    built from) rather than a remembered/assumed structure. Returns raw
    candidate dicts with business_name/website only — phone/email still
    come only from a page actually GET-inspected later
    (probe_official_website), never invented from a search snippet.
    """
    out: list[dict] = []
    for m in _DDG_RESULT_RE.finditer(body or ""):
        href, title_html = m.group(1), m.group(2)
        if not href.startswith("http"):
            continue
        domain = registrable_domain(href)
        if not domain or domain in KNOWN_AGGREGATOR_HOSTS:
            continue
        if any(domain.endswith(suffix) for suffix in NON_AU_TLD_SUFFIXES):
            continue
        title = _clean_html_text(title_html)
        if not title:
            continue
        if looks_like_article(url=href, title=title):
            continue
        out.append({"business_name": title, "website": href})
    return out


def duckduckgo_search(
    *,
    robots: RobotsGate,
    throttle: HostThrottle,
    fetch: Callable[..., dict] = fetch_url,
    user_agent: str = USER_AGENT,
) -> Callable[[str], list[dict]]:
    """Build a `search(query) -> list[dict]` callable for
    make_query_search_collector, backed by the real html.duckduckgo.com
    endpoint. Raises HarvestError on any non-ok fetch outcome so it slots
    into the existing collector's exception handling (and circuit breaker)
    unchanged - a source that starts failing here behaves exactly like any
    other HarvestError-raising source.
    """
    def _search(query: str) -> list[dict]:
        import urllib.parse as _up
        body_bytes = _up.urlencode({"q": query}).encode("utf-8")
        result = fetch(_DDG_SEARCH_URL, robots=robots, throttle=throttle,
                       user_agent=user_agent, data=body_bytes)
        if not result.get("ok"):
            raise HarvestError(f"duckduckgo search failed: {result.get('kind')} "
                              f"(status={result.get('status')})")
        return parse_duckduckgo_html(result.get("body") or "")
    return _search


# ── Official-website enrichment paths (bounded, not unlimited crawling) ────
# A short, extensible list of useful pages to check once a candidate's
# official site is known. This is enrichment of an ALREADY-identified
# candidate, not a new discovery source, and it never leaves this fixed,
# short path list or follows an external domain.
WEBSITE_PROBE_PATHS = ("/", "/contact", "/contact-us", "/about", "/about-us")


def probe_official_website(
    base_url: str,
    *,
    fetch: Callable[[str], dict],
    paths: Sequence[str] = WEBSITE_PROBE_PATHS,
) -> dict:
    """GET a bounded set of pages on ONE already-identified official site and
    pull out any publicly displayed phone/email, plus enough of the first
    successfully-fetched page to support name extraction and classification
    downstream (make_website_enricher does that; this function stays a
    plain "what did we find" probe). Stops fetching more paths once contact
    info is found - name-quality needs page_html too, so the loop still
    keeps going a little further than a contacts-only probe would if a name
    has not yet been captured. Never follows a link to a different domain:
    `paths` is always joined against `base_url`, nothing in a fetched page's
    own content is ever used as a next URL.

    Every attempted path's outcome kind is kept in `attempts`, so a caller
    can tell "we saw real content with nothing on it" (kind="ok") apart from
    "every attempt was blocked/failed" (kind in the blocked/error set) -
    exactly the distinction enrichment_status needs and a bare phones/emails
    list cannot give it.
    """
    found_phones: list[str] = []
    found_emails: list[str] = []
    page_bodies: list[str] = []
    checked = 0
    attempts: list[str] = []
    base = base_url if base_url.endswith("/") else base_url + "/"
    for path in paths:
        url = urljoin(base, path.lstrip("/"))
        result = fetch(url)
        checked += 1
        attempts.append(result.get("kind", "error"))
        if result.get("ok") and result.get("body"):
            body = result["body"]
            page_bodies.append(body)
            # Extract from VISIBLE text only, not raw markup - a live fetch
            # during this fix found a real page's own <meta name="twitter:
            # data1" content="daniel@daodigital.com.au" /> (a "Written by"
            # author credit, not the business's contact) and a form
            # <input placeholder="youremail@mail.com"> both matching the
            # bare regex over raw HTML. _clean_html_text drops whole tags -
            # attribute content vanishes with them - while text a visitor
            # actually SEES between tags (including a script/JSON-LD
            # block's own text, which is not inside an attribute) survives
            # untouched. "Publicly displayed" means displayed, not merely
            # present somewhere in the markup.
            visible_text = _clean_html_text(body)
            found_phones.extend(extract_phones(visible_text))
            found_emails.extend(extract_emails(visible_text))
        if found_phones or found_emails:
            break
    return {
        "phones": list(dict.fromkeys(found_phones)),
        "emails": list(dict.fromkeys(found_emails)),
        "pages_checked": checked,
        # EVERY successfully-fetched page's body, in visit order - not just
        # the first. A real bug this fixed: the contact page (not "/") is
        # often where both the phone/email AND a classification-relevant
        # phrase ("we manage strata and body corporate portfolios") live,
        # while "/" alone was all a caller keeping only the first body ever
        # saw.
        "page_bodies": page_bodies,
        "any_ok": "ok" in attempts,
    }


def make_website_enricher(
    *,
    fetch: Callable[..., dict],
    robots: RobotsGate,
    throttle: HostThrottle,
    paths: Sequence[str] = WEBSITE_PROBE_PATHS,
) -> Callable[[Mapping], dict]:
    """Build the `enrich(raw) -> raw'` callable make_query_search_collector
    (and make_directory_collector) accept. One already-identified candidate
    in, the SAME dict back out with business_name corrected to the real
    extracted name (see extract_business_name), phone/email filled from the
    site if publicly published there, and classification/enrichment_status
    attached — never a second discovery pass, never a fetch of anything
    outside `paths` on the candidate's own declared domain.

    `fetch` is `fetch_url` (or a fake, in tests) so this makes exactly the
    same kind of polite, robots-checked, throttled, retried GETs as every
    other real I/O in this module — no separate network path.
    """
    def _enrich(raw: Mapping) -> dict:
        row = dict(raw)
        original_title = _clean(row.get("business_name"), 200)
        website = _looks_like_single_url(_clean(row.get("website"), 300))
        industry = _clean(row.get("industry"), 120)

        if not website:
            row["business_name"] = clean_title_name(original_title)
            row["enrichment_status"] = "no_website"
            row["classification"] = classify_candidate(
                segment=segment_for_industry(industry), text=f"{original_title} {industry}")
            return row

        probe = probe_official_website(website, fetch=lambda u: fetch(u, robots=robots, throttle=throttle),
                                       paths=paths)
        page_bodies = probe["page_bodies"]

        # Try EVERY fetched page for a name, not just the first - og:site_name
        # or JSON-LD might sit on one page and not another. Falls through to
        # cleaning the original search title (extract_business_name's own
        # fetched_html=None path) only once every fetched body has been
        # tried and none yielded anything.
        final_name = ""
        for body in page_bodies:
            candidate_name = extract_business_name(original_title=original_title, fetched_html=body)
            if candidate_name:
                final_name = candidate_name
                break
        if not final_name:
            final_name = extract_business_name(original_title=original_title, fetched_html=None)
        row["business_name"] = final_name

        if probe["phones"]:
            row["phone"] = probe["phones"][0]
        if probe["emails"]:
            row["email"] = probe["emails"][0]

        # Classification looks at EVERY fetched page's text too - the
        # "we manage strata/body corporate" sentence that decides
        # likely_customer vs uncertain is routinely on /contact or /about,
        # not on "/".
        page_text = " ".join(_clean_html_text(b)[:1000] for b in page_bodies)
        classification_text = " ".join([original_title, industry, page_text])
        row["classification"] = classify_candidate(
            segment=segment_for_industry(industry), text=classification_text)

        if probe["phones"] or probe["emails"]:
            row["enrichment_status"] = "found"
        elif probe["any_ok"]:
            row["enrichment_status"] = "no_contact_found"
        else:
            row["enrichment_status"] = "unreachable"
        return row
    return _enrich


# ── Source collectors: the plural, extensible source layer ─────────────────

@dataclass(frozen=True)
class CollectorResult:
    """Honest per-source accounting, matching ingest_batch's style: every
    number here is independently meaningful, never inferred from another."""
    candidates: tuple[dict, ...] = ()
    domains_checked: tuple[str, ...] = ()
    robots_disallowed: int = 0
    blocked: int = 0
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceCollector:
    """One discovery source. `collect` is a zero-arg callable (already bound
    to its own fetch/query configuration via closure) so the orchestrator
    never needs to know HOW a source works — only that it returns a
    CollectorResult. Adding a source means adding one more of these to the
    list passed to `run_discovery`; nothing else in this module changes."""
    source_id: str
    source_type: str
    collect: Callable[[], CollectorResult]


# A backend that fails N times in a row is proven unavailable for this run;
# trying it again for every remaining query in a matrix that can easily be
# hundreds long (AU_REGIONS x INDUSTRY_TERMS) is exactly the "hammering a
# source" this whole module tries not to do. This is an efficiency/civility
# safeguard, not a discovery cap - it only trips on repeated FAILURE, and
# resets the moment a query succeeds (see the "recovers after transient
# failures" test), so a backend that is merely flaky never loses coverage.
SEARCH_CIRCUIT_BREAKER_THRESHOLD = 3


def make_query_search_collector(
    source_id: str,
    *,
    search: Callable[[str], Iterable[Mapping]],
    regions: Sequence[str] = AU_REGIONS,
    industries: Sequence[str] = INDUSTRY_TERMS,
    max_queries: int | None = None,
    circuit_breaker_threshold: int = SEARCH_CIRCUIT_BREAKER_THRESHOLD,
    enrich: Callable[[Mapping], Mapping] | None = None,
) -> SourceCollector:
    """Build a search-based SourceCollector from an injected `search`
    backend (query string -> iterable of raw result dicts). This is the
    "SearchSource" shape from the spec, implemented as configuration over
    the generic collector contract rather than a bespoke class hierarchy.
    `search` is whatever the deployment actually has available (a search
    API, a specific engine's result-page parser, or — in tests — a fixture);
    this function does not care which, and never touches the network
    itself.

    `enrich`, when given, runs on each raw result before it is counted as a
    candidate — this is where make_website_enricher plugs in to turn a
    search-result title into a real business name plus contact/
    classification. Optional and defaulting to None (pass-through)
    specifically so every existing caller/test that does not care about
    enrichment keeps working unchanged.
    """
    def _collect() -> CollectorResult:
        queries = build_search_queries(regions=regions, industries=industries)
        if max_queries is not None:
            queries = queries[:max_queries]
        candidates: list[dict] = []
        domains: set[str] = set()
        errors: list[str] = []
        blocked = robots_dis = 0
        consecutive_failures = 0
        errors_this_streak = 0     # how many of `errors` came from the CURRENT
                                   # streak specifically (403/429/robots don't
                                   # append to `errors` at all, so this can be
                                   # less than consecutive_failures)
        last_failure = ""
        attempted = 0
        for q in queries:
            attempted += 1
            try:
                for raw in search(q):
                    row = dict(raw)
                    row.setdefault("source_type", "search")
                    row.setdefault("industry", q)
                    if enrich is not None:
                        row = dict(enrich(row))
                    candidates.append(row)
                    if row.get("website"):
                        d = registrable_domain(str(row["website"]))
                        if d:
                            domains.add(d)
                consecutive_failures = 0     # this query round-tripped without raising
                errors_this_streak = 0
            except HarvestError as exc:
                msg = str(exc)
                last_failure = msg
                consecutive_failures += 1
                if "403" in msg or "429" in msg:
                    blocked += 1
                elif "robots" in msg:
                    robots_dis += 1
                else:
                    errors.append(f"{source_id}: {msg[:200]}")
                    errors_this_streak += 1
            except Exception as exc:            # noqa: BLE001 — one query never aborts the source
                last_failure = f"{type(exc).__name__}: {exc}"
                consecutive_failures += 1
                errors.append(f"{source_id}: {last_failure[:160]}")
                errors_this_streak += 1
            if consecutive_failures >= circuit_breaker_threshold:
                if errors_this_streak:
                    del errors[len(errors) - errors_this_streak:]
                errors.append(
                    f"{source_id}: stopped after {consecutive_failures} consecutive "
                    f"failures ({attempted}/{len(queries)} queries attempted) — "
                    f"last error: {last_failure[:200]}")
                break
        return CollectorResult(
            candidates=tuple(candidates), domains_checked=tuple(sorted(domains)),
            robots_disallowed=robots_dis, blocked=blocked, errors=tuple(errors),
        )
    return SourceCollector(source_id=source_id, source_type="search", collect=_collect)


def make_directory_collector(
    source_id: str,
    *,
    list_entries: Callable[[], Iterable[Mapping]],
    source_type: str = "directory",
    enrich: Callable[[Mapping], Mapping] | None = None,
) -> SourceCollector:
    """Build a SourceCollector from any directory-shaped listing function
    (`list_entries` -> iterable of raw candidate dicts). Covers business
    directories, industry-association member lists, tender/procurement
    listings and similar "here is a page of entities" sources — they all
    reduce to the same shape once the source-specific parsing is done by
    the injected callable.
    """
    def _collect() -> CollectorResult:
        candidates: list[dict] = []
        domains: set[str] = set()
        errors: list[str] = []
        blocked = robots_dis = 0
        try:
            for raw in list_entries():
                row = dict(raw)
                row.setdefault("source_type", source_type)
                if enrich is not None:
                    row = dict(enrich(row))
                candidates.append(row)
                if row.get("website"):
                    d = registrable_domain(str(row["website"]))
                    if d:
                        domains.add(d)
        except HarvestError as exc:
            msg = str(exc)
            if "robots" in msg:
                robots_dis += 1
            elif "403" in msg or "429" in msg:
                blocked += 1
            else:
                errors.append(f"{source_id}: {msg[:200]}")
        except Exception as exc:                # noqa: BLE001 — park this source, keep the run going
            errors.append(f"{source_id}: {type(exc).__name__}: {str(exc)[:160]}")
        return CollectorResult(
            candidates=tuple(candidates), domains_checked=tuple(sorted(domains)),
            robots_disallowed=robots_dis, blocked=blocked, errors=tuple(errors),
        )
    return SourceCollector(source_id=source_id, source_type=source_type, collect=_collect)


# ── Orchestration ────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_discovery(
    store,
    collectors: Sequence[SourceCollector],
    *,
    max_candidates: int | None = None,
    dry_run: bool = False,
    now_iso: str | None = None,
    notify: Callable[[str, str, Mapping], bool] | None = None,
) -> dict:
    """One discovery run across every given source. Mirrors ingest_batch's
    honest-accounting contract and seek_harvest's cycle() shape.

    `max_candidates` and `dry_run` are OPERATIONAL controls only — neither
    is read by any discovery/identity/merge function above; removing the
    cap or turning dry_run off does not change any code path, only how much
    of it runs and whether writes are committed. Nothing here is
    architecturally limited to a small source or candidate count.

    A source that raises is recorded as an error and skipped; the run
    continues with every other source ("disable one unavailable source !=
    disable broad discovery").
    """
    stamp = now_iso or _now_iso()
    known: list[dict] = list(store.accounts(TENANT, limit=STORE_SCAN_LIMIT))

    sources_checked = 0
    candidates_discovered = 0
    new_accounts_created = 0
    existing_accounts_enriched = 0
    duplicates_prevented = 0
    possible_duplicates_flagged = 0
    websites_verified = 0
    contacts_found = 0
    not_found = 0
    robots_disallowed = 0
    blocked_403_429 = 0
    errors: list[str] = []
    domains_checked: set[str] = set()
    per_source_new: dict[str, int] = {}
    possible_duplicate_notes: list[str] = []

    for sc in collectors:
        sources_checked += 1
        try:
            result = sc.collect()
        except Exception as exc:                # noqa: BLE001 — one source never stops the run
            errors.append(f"{sc.source_id}: {type(exc).__name__}: {exc}")
            continue

        domains_checked.update(result.domains_checked)
        robots_disallowed += result.robots_disallowed
        blocked_403_429 += result.blocked
        errors.extend(result.errors)

        stop = False
        for raw in result.candidates:
            if max_candidates is not None and candidates_discovered >= max_candidates:
                stop = True
                break
            row = dict(raw)
            row.setdefault("source", sc.source_id)
            row.setdefault("source_type", sc.source_type)
            candidates_discovered += 1

            candidate = normalize_candidate(row)
            if candidate is None:
                continue

            if candidate.website:
                websites_verified += 1
                d = registrable_domain(candidate.website)
                if d:
                    domains_checked.add(d)
            if candidate.phone or candidate.email:
                contacts_found += 1
            if not candidate.website and not candidate.phone and not candidate.email:
                not_found += 1

            match = resolve_identity(candidate, known)

            if match.kind == "possible_duplicate":
                possible_duplicates_flagged += 1
                possible_duplicate_notes.append(
                    f"{candidate.business_name!r} (source={candidate.source}) "
                    f"vs existing {match.account_id!r}: {match.reason}")
                existing_row = None    # never merge on a possible-duplicate signal
            elif match.kind == "match":
                existing_row = next(
                    (r for r in known if r.get("account_id") == match.account_id), None)
            else:
                existing_row = None

            payload, changed = merge_account(candidate, existing_row)

            if dry_run:
                if match.kind == "match":
                    duplicates_prevented += 1
                    if changed:
                        existing_accounts_enriched += 1
                else:
                    new_accounts_created += 1
                    per_source_new[sc.source_id] = per_source_new.get(sc.source_id, 0) + 1
                # keep the in-run working set honest for dry-run too, so a
                # duplicate WITHIN the same simulated run is still caught.
                simulated = dict(payload)
                simulated.setdefault("account_id", f"dry-run:{candidate.business_name}")
                known.append(simulated)
                continue

            result_row = store.create_account(TENANT, payload, now_iso=stamp)
            if not result_row.get("ok"):
                errors.append(f"{sc.source_id}: create_account failed: {result_row.get('error')}")
                continue

            created_id = result_row["account"]
            if match.kind == "match":
                duplicates_prevented += 1
                if changed:
                    existing_accounts_enriched += 1
                for i, r in enumerate(known):
                    if r.get("account_id") == created_id:
                        known[i] = {**r, **payload, "account_id": created_id}
                        break
            else:
                new_accounts_created += 1
                per_source_new[sc.source_id] = per_source_new.get(sc.source_id, 0) + 1
                known.append({**payload, "account_id": created_id})
                if notify is not None:
                    try:
                        notify(created_id, "B2B_ACCOUNT_DISCOVERED", {
                            "business_name": candidate.business_name[:80],
                            "source": candidate.source,
                        })
                    except Exception:            # noqa: BLE001 — notify is best-effort
                        pass
        if stop:
            break

    top_sources = sorted(
        ({"source_id": sid, "new_accounts": n} for sid, n in per_source_new.items()),
        key=lambda r: r["new_accounts"], reverse=True,
    )

    return {
        "status": "DONE",
        "dry_run": dry_run,
        "sources_checked": sources_checked,
        "domains_checked": len(domains_checked),
        "candidates_discovered": candidates_discovered,
        "new_accounts_created": new_accounts_created,
        "existing_accounts_enriched": existing_accounts_enriched,
        "duplicates_prevented": duplicates_prevented,
        "possible_duplicates_flagged": possible_duplicates_flagged,
        "possible_duplicate_notes": possible_duplicate_notes,
        "websites_verified": websites_verified,
        "contacts_found": contacts_found,
        "not_found": not_found,
        "robots_disallowed": robots_disallowed,
        "blocked_403_429": blocked_403_429,
        "errors": errors,
        "top_sources": top_sources,
    }
