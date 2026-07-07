"""Outreach draft generation — DRAFT ONLY, the human always sends manually.

INV-1: the bot never contacts a prospect. It produces a draft the operator
reviews, edits, and sends from their own email client. Spam Act 2003 requires
sender identification and an opt-out path in commercial messages — the
template bakes both in.
"""
from __future__ import annotations

import logging

from config import settings
from db import Lead

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    """Lazy Anthropic client — importing this module must not need the SDK."""
    global _client
    if _client is None:
        from anthropic import Anthropic

        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


def build_draft_prompt(lead: Lead) -> str:
    """Pure prompt builder — unit-tested without the SDK."""
    return f"""Write a short, professional first-contact email (max 150 words) \
from a Sydney building painting contractor ({settings.operator_business}) \
about this opportunity:

Title: {lead.title}
Details: {(lead.description or "")[:500]}
Location: {lead.suburb or "Sydney"}
Source: {lead.source}
URL: {lead.url}

Rules:
- B2B tone, specific to THIS opportunity (reference the actual project/tender)
- Australian English; no hype words, no emojis
- Ask exactly one clear question (site visit, tender docs, or quote invitation)
- Sign off with [YOUR NAME], {settings.operator_business}, [PHONE]
- Final line: offer to be removed from future contact (Spam Act courtesy)
- Output ONLY the email: subject line first ("Subject: ..."), then the body."""


def generate_draft(lead: Lead) -> str:
    """Blocking call — from async code use `await asyncio.to_thread(generate_draft, lead)`."""
    resp = _get_client().messages.create(
        model=settings.llm_model,
        max_tokens=700,
        messages=[{"role": "user", "content": build_draft_prompt(lead)}],
    )
    parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
    return "\n".join(parts).strip() or "(empty draft — try again)"
