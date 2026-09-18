"""airtasker_alert_parser.py — AIRTASKER-WATCH lane (2026-09-08), staged deliverable.

Parses Airtasker task-alert EMAILS into structured task references so the
octopus sees new Sydney painting tasks within minutes of the owner's alert
email arriving. Proposals stay MANUAL (registry: `manual_monitor`,
"manual proposal only") — this module is read-only, zero network, zero side
effects. Integration point (documented in PIPELINE-DESIGN.md, NOT wired):
`imap_listener.classify()` currently drops unknown senders into `noise`;
an airtasker-sender branch would call `parse_alert_message()` here.

Design rules (mirror lane red lines):
  - NEVER fabricate: a field that is not literally present in the email is
    None. Truncated/garbled input yields partial results + recorded errors,
    never invented values (ACD-07F-dev-10 contract: schema_drift →
    missing/None, NEVER a fabricated value).
  - NEVER raises on malformed input (same never-die contract as
    imap_listener).
  - Sender gate: only parses mail whose From domain matches the airtasker
    allowlist (suffix match). Defence against misfiling owner's other mail.
  - Direction gate: a task whose text looks supply-side (someone OFFERING
    painting work, not buying) is flagged `supply_risk=True` so the pipeline
    never turns it into a lead card (PAINT-L5-001 wrong_recipient kill
    metric).
  - No LLM, no scoring here — deterministic parsing only. Scoring happens
    downstream with the existing direction-gate pipeline.

E-grade: E2 on DESIGNED input (fixtures below are MODELLED on the documented
alert concept; the exact email format has not yet been observed —
status: unverified until the owner saves one real alert email as .eml into
this lane folder, which is the E2-real gate).
"""
from __future__ import annotations

import email
import email.policy
import re
from dataclasses import dataclass, field
from typing import List, Optional

# Sender allowlist: suffix match on the From address domain.
# NOTE: exact alert From domain unverified until a real sample arrives —
# extend this list from the real sample, never guess domains into it.
AIRTASKER_SENDER_SUFFIXES = ("airtasker.com",)

# Task links look like https://www.airtasker.com/tasks/<slug-or-id>
# Tolerant to slug/none and query strings; id = trailing digit run in path.
TASK_URL_RE = re.compile(
    r"https?://(?:[a-z0-9-]+\.)*airtasker\.com/tasks/[^\"'\s<>]+", re.IGNORECASE)
TASK_ID_RE = re.compile(r"/tasks/(?:[^/?#]*?)(\d{4,})(?:[/?#]|$)")

BUDGET_RE = re.compile(
    r"\$\s?\d[\d,]*(?:\.\d{2})?(?:\s?[-–]\s?\$\s?\d[\d,]*(?:\.\d{2})?)?")

# Supply-side signals adapted from ofn/agents/demand_harvest.py SUPPLY_KEYWORDS
# (same wrong_recipient kill-metric philosophy, email-alert edition).
SUPPLY_KEYWORDS = (
    "looking for work", "available for work", "painter available",
    "my rates", "i offer", "contact me for", "hire me",
    "years of experience", "portfolio", "abn holder",
)


@dataclass
class TaskRef:
    """One task seen in an alert email. Absent facts are None, never invented."""
    url: str
    task_id: Optional[str] = None
    title: Optional[str] = None
    budget_text: Optional[str] = None
    location_text: Optional[str] = None
    posted_at: Optional[str] = None      # only if literally present in email
    supply_risk: bool = False            # direction-gate flag

    def to_card(self) -> str:
        """Telegram-card one-liner. Missing fields render as '—', not guesses."""
        title = self.title or "—"
        budget = self.budget_text or "—"
        loc = self.location_text or "—"
        return f"{title} | {budget} | {loc} | {self.url}"


@dataclass
class AlertEmail:
    received_at: Optional[str] = None    # email Date header, verbatim
    subject: Optional[str] = None
    tasks: List[TaskRef] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)   # what failed, transparently


def is_airtasker_sender(sender: str) -> bool:
    addr = (sender or "").strip().lower()
    if "@" not in addr:
        return False
    domain = addr.rsplit("@", 1)[1]
    return any(domain == s or domain.endswith("." + s)
               for s in AIRTASKER_SENDER_SUFFIXES)


def parse_alert_message(msg: email.message.Message) -> AlertEmail:
    """Parse an email.message.Message (policy=default). Never raises."""
    out = AlertEmail(
        received_at=msg.get("Date"),
        subject=(msg.get("Subject") or "").strip() or None,
    )
    html, text = _bodies(msg, out.errors)
    if not html and not text:
        out.errors.append("no_text_or_html_body")
        return out

    anchors = _anchors(html) if html else []
    seen_urls: set[str] = set()
    for url, link_text in anchors:
        if url in seen_urls:
            continue
        if not TASK_URL_RE.match(url):
            continue
        seen_urls.add(url)
        out.tasks.append(_build_task(url, link_text, html or "", text, out.errors))

    # text-only fallback (plain-text alert variant, unverified existence)
    if not out.tasks and text:
        for url in TASK_URL_RE.findall(text):
            if url in seen_urls:
                continue
            seen_urls.add(url)
            out.tasks.append(_build_task(url, None, "", text, out.errors))

    if not out.tasks:
        out.errors.append("no_task_links_found")
    return out


def parse_raw_bytes(raw: bytes) -> AlertEmail:
    msg = email.message_from_bytes(raw, policy=email.policy.default)
    return parse_alert_message(msg)


def _build_task(url: str, link_text: Optional[str], html: str,
                text: str, errors: List[str]) -> TaskRef:
    task = TaskRef(url=url)
    m = TASK_ID_RE.search(url)
    if m:
        task.task_id = m.group(1)
    else:
        errors.append(f"task_id_not_found:{url[:80]}")

    title = (link_text or "").strip() or None
    if not title:
        m = re.search(
            re.escape(url) + r"\"[^>]*>([^<]{3,200})<", html)
        if m:
            title = m.group(1).strip()
    task.title = title or None

    # budget/location: search a window of context around the link text only.
    window = _context_window(title or url, html, text)
    mb = BUDGET_RE.search(window)
    task.budget_text = mb.group(0) if mb else None
    ml = re.search(r"\b(Sydney|NSW)\b", window)
    task.location_text = ml.group(0) if ml else None

    low = f"{title or ''} {window}".lower()
    task.supply_risk = any(k in low for k in SUPPLY_KEYWORDS)
    return task


def _context_window(anchor: str, html: str, text: str, span: int = 120) -> str:
    """Text around the anchor, for budget/location. Budget must be plausibly
    attached to THIS task, so prefer the smallest enclosing <li>/<p>/<div>
    block; fallback is a narrow window. (Caught by test: a wide window let
    task 1's budget bleed into task 2.)"""
    if not anchor:
        return ""
    for body in (html, text):
        idx = body.find(anchor)
        if idx < 0:
            continue
        block = _enclosing_block(body, idx, idx + len(anchor))
        if block:
            return block
        return body[max(0, idx - span): idx + len(anchor) + span]
    return ""


def _enclosing_block(body: str, start: int, end: int) -> str:
    for tag in ("li", "p", "div"):
        open_re = re.compile(rf"<{tag}[\s>]", re.IGNORECASE)
        opens = [m.start() for m in open_re.finditer(body) if m.start() < start]
        if not opens:
            continue
        open_at = opens[-1]
        close = body.find(f"</{tag}>", end)
        if close >= 0:
            candidate = body[open_at:close]
            # the block must not swallow another task link
            if len(candidate) < 1500 and candidate.count("/tasks/") <= 1:
                return candidate
    return ""


def _anchors(html: str) -> List[tuple]:
    out = []
    for m in re.finditer(r"<a\s[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>",
                         html, re.IGNORECASE | re.DOTALL):
        href, inner = m.group(1), m.group(2)
        text = re.sub(r"<[^>]+>", " ", inner)
        text = re.sub(r"\s+", " ", text).strip()
        out.append((href, text))
    return out


def _bodies(msg: email.message.Message,
            errors: List[str]) -> tuple[Optional[str], Optional[str]]:
    html = text = None
    try:
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == "text/html" and html is None:
                    html = part.get_content()
                elif ct == "text/plain" and text is None:
                    text = part.get_content()
        else:
            ct = msg.get_content_type()
            if ct == "text/html":
                html = msg.get_content()
            else:
                text = msg.get_content()
    except Exception as exc:  # noqa: BLE001 — never die on malformed mail
        errors.append(f"body_extract_error:{type(exc).__name__}")
    return html, text
