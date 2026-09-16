"""
Worker C -- Content / Copy (KB-01, namespace: content_*)
draft-only. No auto-publish. All drafts go through Gate -> Queue.

Phase 2 (lead-path slice): speed-to-lead + follow-up are REAL Haiku drafts.
  - draft_speed_to_lead: first reply to a new enquiry, target < 15 min
    (SLA_LEAD_MINUTES). Inferred-consent path (KB-09); still human-approved (INV-1).
  - draft_followup:      B3 template -- day 2 (question), day 5 (adjust scope),
                         day 10 (close). Polite, no pressure (KB-10 B3).

Every DIRECT outbound message carries a sender-ID footer (BUSINESS_NAME + ABN +
opt-out) so it satisfies the Gate (Spam Act 2003: sender ID + functional opt-out).

Phase 2 (review slice, P1): draft_review_response is a REAL Haiku draft (public
footer: name + ABN, NO opt-out).
Phase 2 (suburb slice, P2): draft_suburb_page is a REAL Sonnet draft (website copy,
no footer). capital_works (Phase 5) remains a stub.

Model: Haiku (cheap-first, KB-02 s2.1). Cost ~AUD $0.004 per message (KB-02 s3.1).
Falls back to a compliant template if the LLM is unavailable (zero spend).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

try:
    from anthropic import Anthropic
except ImportError:  # SDK absent -> Worker C falls back to compliant templates
    Anthropic = None

from ..config import config
from ..database import get_connection
from ..models import Draft, DraftType
from .. import audit
from ..governance import check_and_enforce, log_cost
from ..resilience import call_with_retry, new_idempotency_key
from .base_agent import (
    BaseAgent, AgentCapability, RiskLevel, QualificationStatus, register_agent,
)

logger = logging.getLogger(__name__)

# Haiku pricing (Jun 2026): input $0.80/Mtok, output $4.00/Mtok (KB-02 s2.1)
_HAIKU_INPUT_USD_PER_TOK = 0.80 / 1_000_000
_HAIKU_OUTPUT_USD_PER_TOK = 4.00 / 1_000_000

# Estimated AUD cost for the per-action governance pre-check (KB-02 s3.1)
_EST_SPEED_TO_LEAD_AUD = 0.004
_EST_FOLLOWUP_AUD = 0.004
_EST_REVIEW_RESPONSE_AUD = 0.004
# Sonnet pricing (Jun 2026): input $3.00/Mtok, output $15.00/Mtok (KB-02 s2.1)
_SONNET_INPUT_USD_PER_TOK = 3.00 / 1_000_000
_SONNET_OUTPUT_USD_PER_TOK = 15.00 / 1_000_000
_EST_SUBURB_PAGE_AUD = 0.08

# P7 cost optimisation (KB-02 s2.2, Anthropic pricing Jun 2026):
#   prompt cache WRITE = 1.25x input price; cache READ = 0.10x input price
#   (=90% saving on every repeated system token once the block is cached).
#   Message Batches API = 50% off both input and output.
# NOTE (honesty): the API only caches blocks above a minimum size (order of
# 1-2k tokens depending on model). Worker C system prompts are currently a
# few hundred tokens, so cache_control is wired and harmless but the read
# discount only materialises once stable blocks grow past the minimum
# (e.g. suburb-page system + fixed KB template). Cost accounting below is
# correct either way because it reads the usage fields the API returns.
_CACHE_WRITE_MULT = 1.25
_CACHE_READ_MULT = 0.10
_BATCH_DISCOUNT = 0.50

_SPEED_TO_LEAD_SYSTEM = (
    "You write the FIRST reply to a new painting enquiry for a Sydney house-painting "
    "business. Goals: acknowledge fast, sound human and local, ask one clarifying "
    "question, and invite a free no-obligation quote. Hard rules: no unsubstantiated "
    "claims (no 'best', 'cheapest', 'guaranteed', 'number one') -- Australian Consumer "
    "Law s29. Under 90 words. Plain, warm, no emoji. Do NOT add a signature, ABN or "
    "opt-out footer (it is appended automatically). Return ONLY the message body."
)

_FOLLOWUP_SYSTEM = (
    "You write a SHORT, polite follow-up to someone who enquired about house painting "
    "in Sydney but has not replied. No pressure, no guilt-tripping. Offer one clear, "
    "easy next step. Hard rules: no unsubstantiated claims (ACL s29). Under 70 words. "
    "Plain, warm, no emoji. Do NOT add a signature, ABN or opt-out footer (appended "
    "automatically). Return ONLY the message body."
)

# KB-10 B3: day 2 = question, day 5 = adjust scope, day 10 = close
_FOLLOWUP_INTENT = {
    2: "Day 2: gentle check-in. Ask if they have any questions about the quote or scope.",
    5: "Day 5: offer to adjust the scope or budget to suit them; ask what would help.",
    10: "Day 10: final friendly close. Leave the door open with zero pressure.",
}

# -- Review response (P1 review slice) ---------------------------------------
# A review reply is posted PUBLICLY on the platform, so it must never echo the
# reviewer's contact details, and it carries NO opt-out (Spam Act direct-message
# rules do not apply to a public reply). ACL s29 + ABN sender-ID still apply.
_REVIEW_RESPONSE_SYSTEM = (
    "You write a PUBLIC reply to a customer review for a Sydney house-painting "
    "business. It is posted publicly, so never include the reviewer's phone, email "
    "or address. Sound human and specific; thank them by first name if given. Hard "
    "rules: no unsubstantiated claims (no 'best', 'cheapest', 'guaranteed', 'number "
    "one', '100%') -- Australian Consumer Law s29. Never admit legal liability. "
    "Under 80 words. Plain, warm, no emoji. Do NOT add a signature or ABN (it is "
    "appended automatically). Return ONLY the reply body."
)
_REVIEW_TONE = {
    "positive": ("Sentiment: positive. Warmly thank them and reinforce one "
                 "specific thing they praised. Invite them back."),
    "negative": ("Sentiment: negative. Acknowledge their experience with genuine "
                 "empathy, apologise that it fell short (WITHOUT admitting legal "
                 "fault), and invite them to continue offline so you can make it "
                 "right. Do not be defensive."),
    "neutral":  ("Sentiment: neutral. Thank them, acknowledge the feedback, and "
                 "offer to help further."),
}

# -- Suburb landing page (P2 suburb slice) -----------------------------------
# A suburb page is website copy (local SEO), NOT a message to a person -- no
# footer/opt-out. Sonnet (MODEL_KEY) for quality; Gate then runs its semantic
# ACL pass (Sonnet) on this high-risk marketing type (KB-07).
_SUBURB_PAGE_SYSTEM = (
    "You write a UNIQUE, locally-relevant landing page for a Sydney house-painting "
    "business targeting one suburb, for local SEO. Structure: a short intro naming "
    "the suburb, the services offered, why a local painter helps, and a clear call "
    "to action to request a free no-obligation quote. Hard rules (Australian "
    "Consumer Law s29): make NO unsubstantiated or absolute claims -- do NOT invent "
    "review counts, star ratings, years in business, awards, testimonials or "
    "statistics; do not claim to be 'best', 'cheapest', 'number one' or "
    "'guaranteed'. State only what is plainly true of any competent local painter. "
    "Use the suburb name naturally a few times. Under 350 words. Plain, warm, no "
    "emoji. Return ONLY the page text."
)


@register_agent
class ContentAgent(BaseAgent):
    """Worker C: all content drafted here, never published directly (INV-1)."""

    AGENT_ID = "C_content"
    ALLOWED_ACTIONS = frozenset({"read", "analyse", "draft", "propose"})
    FORBIDDEN_ACTIONS = frozenset({
        "publish", "send", "spend", "alter_policy", "expose_pii",
        "write_canonical_memory", "access_secrets",
    })

    @property
    def role_name(self) -> str:
        return "Worker C — Content / Copy"

    @property
    def qualification_status(self) -> QualificationStatus:
        return QualificationStatus.TRAINEE

    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.GREEN  # drafts only; publishing is Worker E + INV-1 gate

    @property
    def required_inputs(self) -> frozenset[str]:
        return frozenset({"lead", "research"})

    @property
    def capabilities(self) -> tuple[AgentCapability, ...]:
        return (
            AgentCapability("draft_speed_to_lead", "Draft", pii_handling="local-only"),
            AgentCapability("draft_followup", "Draft", pii_handling="local-only"),
            AgentCapability("draft_review_response", "Draft", pii_handling="local-only"),
            AgentCapability("draft_suburb_page", "Draft"),
            AgentCapability("draft_capital_works_assessment", "Draft"),
            AgentCapability("submit_followup_batch", "batch_id"),
            AgentCapability("collect_followup_batch", "list[Draft]"),
        )

    def health(self) -> dict:
        ready = bool(getattr(self, "_llm", None))
        return {
            "ready": True,  # always ready — falls back to compliant templates
            "detail": "Anthropic live" if ready
                      else "ANTHROPIC_API_KEY missing — using template fallback",
        }

    def __init__(self) -> None:
        if config.ANTHROPIC_API_KEY and Anthropic is not None:
            self._llm = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        else:
            self._llm = None
            logger.warning(
                "ANTHROPIC_API_KEY not set -- Worker C uses compliant template fallback."
            )

    # -- sender-ID footers --------------------------------------------------------

    def _sender_footer(self) -> str:
        """Direct message footer: name + ABN + opt-out (Spam Act 2003)."""
        name = config.BUSINESS_NAME or "Our team"
        abn = config.BUSINESS_ABN
        abn_part = f"ABN {abn} | " if abn else ""
        return f"\n\n--\n{name} | {abn_part}Reply STOP to opt out."

    def _public_reply_footer(self) -> str:
        """Public review reply footer: identify the business (name + ABN) but NO
        opt-out. A public platform reply is not a direct commercial message, so a
        STOP/unsubscribe line would be meaningless here (P1 review slice)."""
        name = config.BUSINESS_NAME or "Our team"
        abn = config.BUSINESS_ABN
        abn_part = f" ABN {abn}" if abn else ""
        return f"\n\n-- {name}{abn_part}"

    # -- P7 helpers: prompt caching + cache/batch-aware real cost -----------------

    @staticmethod
    def _system_param(system: str):
        """CACHE_ENABLED -> mark the stable system block for prompt caching."""
        if config.CACHE_ENABLED:
            return [{
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }]
        return system

    @staticmethod
    def _cost_from_usage(usage, in_per_tok: float, out_per_tok: float,
                         batch: bool = False):
        """
        REAL cost after cache/batch discounts, from the usage the API returned:
          normal input           x1.00 * input price
          cache_creation tokens  x1.25 * input price (cache write)
          cache_read tokens      x0.10 * input price (the actual saving)
          batch                  x0.50 on the whole call
        Returns (tok_in_total, tok_out, cost_usd). This is what flows into
        log_cost -> cost_events, so INV-3 accounting reflects the discount.
        """
        tok_in = getattr(usage, "input_tokens", 0) or 0
        tok_out = getattr(usage, "output_tokens", 0) or 0
        cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
        cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
        cost = (tok_in * in_per_tok
                + cache_write * in_per_tok * _CACHE_WRITE_MULT
                + cache_read * in_per_tok * _CACHE_READ_MULT
                + tok_out * out_per_tok)
        if batch:
            cost *= _BATCH_DISCOUNT
        return tok_in + cache_write + cache_read, tok_out, round(cost, 8)

    # -- Haiku helper: returns (text, tok_in, tok_out, cost_usd) or None ----------

    def _haiku(self, system: str, user: str, max_tokens: int = 320,
               est_cost_aud: float = _EST_SPEED_TO_LEAD_AUD):
        if not self._llm:
            return None
        idem = new_idempotency_key()
        try:
            msg = call_with_retry(
                lambda: self._llm.messages.create(
                    model=config.MODEL_CHEAP,
                    max_tokens=max_tokens,
                    system=self._system_param(system),
                    messages=[{"role": "user", "content": user}],
                    extra_headers={"Idempotency-Key": idem},
                ),
                agent_id=self.AGENT_ID,
                before_attempt=lambda: check_and_enforce(est_cost_aud, self.AGENT_ID),
                max_attempts=config.RETRY_MAX_ATTEMPTS,
                base_delay=config.RETRY_BASE_DELAY_SEC,
                max_delay=config.RETRY_MAX_DELAY_SEC,
            )
            text = msg.content[0].text.strip()
            tok_in, tok_out, cost = self._cost_from_usage(
                msg.usage, _HAIKU_INPUT_USD_PER_TOK, _HAIKU_OUTPUT_USD_PER_TOK)
            return text, tok_in, tok_out, cost
        except Exception as exc:
            logger.error("Worker C Haiku call failed: %s", exc)
            return None

    def _sonnet(self, system: str, user: str, max_tokens: int = 900,
                est_cost_aud: float = _EST_SUBURB_PAGE_AUD):
        """Sonnet (MODEL_KEY) call for high-value copy. Same shape as _haiku."""
        if not self._llm:
            return None
        idem = new_idempotency_key()
        try:
            msg = call_with_retry(
                lambda: self._llm.messages.create(
                    model=config.MODEL_KEY,
                    max_tokens=max_tokens,
                    system=self._system_param(system),
                    messages=[{"role": "user", "content": user}],
                    extra_headers={"Idempotency-Key": idem},
                ),
                agent_id=self.AGENT_ID,
                before_attempt=lambda: check_and_enforce(est_cost_aud, self.AGENT_ID),
                max_attempts=config.RETRY_MAX_ATTEMPTS,
                base_delay=config.RETRY_BASE_DELAY_SEC,
                max_delay=config.RETRY_MAX_DELAY_SEC,
            )
            text = msg.content[0].text.strip()
            tok_in, tok_out, cost = self._cost_from_usage(
                msg.usage, _SONNET_INPUT_USD_PER_TOK, _SONNET_OUTPUT_USD_PER_TOK)
            return text, tok_in, tok_out, cost
        except Exception as exc:
            logger.error("Worker C Sonnet call failed: %s", exc)
            return None

    # -- speed-to-lead (first reply to a new enquiry) ----------------------------

    def draft_speed_to_lead(self, lead: dict, research: Optional[dict] = None) -> Draft:
        """Draft the first response to a new enquiry. Target < 15 min. Haiku."""
        check_and_enforce(_EST_SPEED_TO_LEAD_AUD, self.AGENT_ID)

        suburb = lead.get("suburb", "")
        service = lead.get("service_type", "")
        name = lead.get("name", "")
        notes = lead.get("notes", "")
        context = (
            f"Customer first name: {name or 'unknown'}\n"
            f"Suburb: {suburb or 'unknown'}\n"
            f"Service requested: {service or 'general house painting'}\n"
            f"Their note: {notes or '(none)'}"
        )

        result = self._haiku(_SPEED_TO_LEAD_SYSTEM, context, max_tokens=320)
        if result:
            body, tok_in, tok_out, cost_usd = result
            model = config.MODEL_CHEAP
            log_cost("llm_call", self.AGENT_ID, model, cost_usd, tok_in, tok_out)
        else:
            body = self._fallback_speed_to_lead(name, suburb, service)
            tok_in = tok_out = 0
            cost_usd = 0.0
            model = config.MODEL_CHEAP + "+fallback"

        draft = Draft(
            id=str(uuid.uuid4()),
            lead_id=lead.get("id"),
            draft_type=DraftType.SPEED_TO_LEAD,
            content=body + self._sender_footer(),
            agent_id=self.AGENT_ID,
            model_used=model,
            tokens_in=tok_in,
            tokens_out=tok_out,
            cost_usd=cost_usd,
            created_at=datetime.utcnow(),
        )
        self._save(draft)
        audit.append("DRAFT_CREATED", draft.id, {
            "draft_type": draft.draft_type.value,
            "lead_suburb": suburb,            # suburb is NOT PII (INV-2 safe)
            "cost_usd": cost_usd,
        })
        return draft

    def _fallback_speed_to_lead(self, name: str, suburb: str, service: str) -> str:
        greet = f"Hi {name}," if name else "Hi there,"
        where = f" in {suburb}" if suburb else ""
        svc = service or "your painting project"
        return (
            f"{greet} thanks for reaching out about {svc}{where}. We'd love to help. "
            f"Could you tell us a little more about the rooms or areas involved and "
            f"your rough timing? We'll arrange a free, no-obligation quote at a time "
            f"that suits you."
        )

    # -- follow-up (KB-10 B3: day 2 / 5 / 10) ------------------------------------

    def draft_followup(self, lead_id: str, day: int) -> Draft:
        """Follow-up message for day 2, 5, or 10 after enquiry. Haiku."""
        check_and_enforce(_EST_FOLLOWUP_AUD, self.AGENT_ID)

        lead = self._load_lead(lead_id) or {}
        name = lead.get("name", "")
        suburb = lead.get("suburb", "")
        service = lead.get("service_type", "")
        intent = _FOLLOWUP_INTENT.get(day, _FOLLOWUP_INTENT[2])
        context = (
            f"Customer first name: {name or 'unknown'}\n"
            f"Suburb: {suburb or 'unknown'}\n"
            f"Service: {service or 'house painting'}\n"
            f"Follow-up stage -- {intent}"
        )

        result = self._haiku(_FOLLOWUP_SYSTEM, context, max_tokens=240)
        if result:
            body, tok_in, tok_out, cost_usd = result
            model = config.MODEL_CHEAP
            log_cost("llm_call", self.AGENT_ID, model, cost_usd, tok_in, tok_out)
        else:
            body = self._fallback_followup(name, day)
            tok_in = tok_out = 0
            cost_usd = 0.0
            model = config.MODEL_CHEAP + "+fallback"

        draft = Draft(
            id=str(uuid.uuid4()),
            lead_id=lead_id,
            draft_type=DraftType.FOLLOWUP,
            content=body + self._sender_footer(),
            agent_id=self.AGENT_ID,
            model_used=model,
            tokens_in=tok_in,
            tokens_out=tok_out,
            cost_usd=cost_usd,
            created_at=datetime.utcnow(),
        )
        self._save(draft)
        audit.append("DRAFT_CREATED", draft.id, {
            "draft_type": "followup",
            "day": day,
            "lead_id": lead_id,                # opaque uuid, not PII
            "cost_usd": cost_usd,
        })
        return draft

    # -- P7 batch path: day 2/5/10 follow-ups are not time-sensitive --------------
    # Message Batches API = 50% off. Async by nature (minutes to hours), so the
    # flow is submit -> (later, e.g. next cron tick) collect. Collected drafts
    # still go through Gate -> Queue via the orchestrator (INV-1 unchanged).

    def _followup_context(self, lead_id: str, day: int) -> str:
        lead = self._load_lead(lead_id) or {}
        name = lead.get("name", "")
        suburb = lead.get("suburb", "")
        service = lead.get("service_type", "")
        intent = _FOLLOWUP_INTENT.get(day, _FOLLOWUP_INTENT[2])
        return (
            f"Customer first name: {name or 'unknown'}\n"
            f"Suburb: {suburb or 'unknown'}\n"
            f"Service: {service or 'house painting'}\n"
            f"Follow-up stage -- {intent}"
        )

    def submit_followup_batch(self, jobs: list) -> Optional[str]:
        """
        Submit day-2/5/10 follow-ups as ONE Message Batch (50% discount).
        jobs: [{"lead_id": ..., "day": ...}, ...]
        Returns batch_id, or None when offline / BATCH_ENABLED=false (caller
        falls back to per-draft draft_followup).
        """
        check_and_enforce(
            len(jobs) * _EST_FOLLOWUP_AUD * _BATCH_DISCOUNT, self.AGENT_ID)
        if not (self._llm and config.BATCH_ENABLED and jobs):
            return None
        requests = [{
            "custom_id": f"{j['lead_id']}::{j['day']}",
            "params": {
                "model": config.MODEL_CHEAP,
                "max_tokens": 240,
                "system": self._system_param(_FOLLOWUP_SYSTEM),
                "messages": [{
                    "role": "user",
                    "content": self._followup_context(j["lead_id"], j["day"]),
                }],
            },
        } for j in jobs]
        try:
            batch = call_with_retry(
                lambda: self._llm.messages.batches.create(requests=requests),
                agent_id=self.AGENT_ID,
                before_attempt=lambda: check_and_enforce(
                    len(jobs) * _EST_FOLLOWUP_AUD * _BATCH_DISCOUNT, self.AGENT_ID),
                max_attempts=config.RETRY_MAX_ATTEMPTS,
                base_delay=config.RETRY_BASE_DELAY_SEC,
                max_delay=config.RETRY_MAX_DELAY_SEC,
            )
        except Exception as exc:
            logger.error("Worker C batch submit failed: %s", exc)
            return None
        audit.append("BATCH_SUBMITTED", batch.id, {
            "n_requests": len(requests),
            "task_type": "followup",
        })
        return batch.id

    def collect_followup_batch(self, batch_id: str) -> Optional[list]:
        """
        Collect a finished follow-up batch into Draft rows (NOT sent -- the
        orchestrator must still run each through Gate -> Queue, INV-1).
        Returns list of Drafts, or None if the batch is still processing.
        Cost per draft = API usage at 50% batch discount -> cost_events.
        """
        check_and_enforce(0.0, self.AGENT_ID)
        if not self._llm:
            return None
        batch = self._llm.messages.batches.retrieve(batch_id)
        if getattr(batch, "processing_status", "") != "ended":
            return None  # not ready -- caller retries on the next tick
        drafts = []
        for entry in self._llm.messages.batches.results(batch_id):
            lead_id, _, day_s = entry.custom_id.partition("::")
            day = int(day_s or 2)
            if getattr(entry.result, "type", "") != "succeeded":
                audit.append("BATCH_ITEM_FAILED", batch_id, {
                    "lead_id": lead_id, "day": day,
                    "result_type": getattr(entry.result, "type", "unknown"),
                })
                # compliant fallback so the follow-up still happens
                lead = self._load_lead(lead_id) or {}
                body = self._fallback_followup(lead.get("name", ""), day)
                drafts.append(self._build_followup_draft(
                    lead_id, day, body, 0, 0, 0.0,
                    config.MODEL_CHEAP + "+fallback"))
                continue
            msg = entry.result.message
            body = msg.content[0].text.strip()
            tok_in, tok_out, cost = self._cost_from_usage(
                msg.usage, _HAIKU_INPUT_USD_PER_TOK, _HAIKU_OUTPUT_USD_PER_TOK,
                batch=True)
            log_cost("llm_call_batch", self.AGENT_ID, config.MODEL_CHEAP,
                     cost, tok_in, tok_out)
            drafts.append(self._build_followup_draft(
                lead_id, day, body, tok_in, tok_out, cost,
                config.MODEL_CHEAP + "+batch"))
        audit.append("BATCH_COLLECTED", batch_id, {
            "n_drafts": len(drafts),
        })
        return drafts

    def _build_followup_draft(self, lead_id: str, day: int, body: str,
                              tok_in: int, tok_out: int, cost_usd: float,
                              model: str) -> Draft:
        draft = Draft(
            id=str(uuid.uuid4()),
            lead_id=lead_id,
            draft_type=DraftType.FOLLOWUP,
            content=body + self._sender_footer(),
            agent_id=self.AGENT_ID,
            model_used=model,
            tokens_in=tok_in,
            tokens_out=tok_out,
            cost_usd=cost_usd,
            created_at=datetime.utcnow(),
        )
        self._save(draft)
        audit.append("DRAFT_CREATED", draft.id, {
            "draft_type": "followup",
            "day": day,
            "lead_id": lead_id,
            "cost_usd": cost_usd,
        })
        return draft

    def _fallback_followup(self, name: str, day: int) -> str:
        greet = f"Hi {name}," if name else "Hi there,"
        if day <= 2:
            return (f"{greet} just checking in on the painting quote -- "
                    f"any questions we can answer for you?")
        if day <= 5:
            return (f"{greet} happy to adjust the scope or budget to suit you. "
                    f"What would help most?")
        return (f"{greet} we'll leave this with you for now -- reach out any time "
                f"and we'll be glad to help.")

    def _load_lead(self, lead_id: str) -> Optional[dict]:
        """Read lead row for personalisation. PII stays local, never logged (INV-2)."""
        if not lead_id:
            return None
        try:
            conn = get_connection()
        except Exception:
            return None
        try:
            row = conn.execute(
                "SELECT id, name, suburb, service_type FROM leads WHERE id = ?",
                (lead_id,),
            ).fetchone()
            return dict(row) if row else None
        except Exception:
            return None
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # -- Review response (P1 review slice -- REAL). suburb_page (P2) and -----------
    #    capital_works (Phase 5) below remain stubs until their slice lands.

    def draft_review_response(self, review_text: str, sentiment: str,
                              platform: str, reviewer_name: str = "",
                              key_themes: Optional[list] = None) -> Draft:
        """
        Draft a PUBLIC reply to a customer review (Haiku, tone by sentiment).

        Public reply => no opt-out footer and no consent requirement, but ABN
        sender-ID + ACL s29 still apply (enforced by the Gate). The reviewer's
        text and name are NEVER written to the audit trail (INV-2). Falls back to
        a compliant template if the LLM is unavailable (zero spend).
        """
        check_and_enforce(_EST_REVIEW_RESPONSE_AUD, self.AGENT_ID)

        norm_sent = (sentiment or "neutral").lower()
        tone = _REVIEW_TONE.get(norm_sent, _REVIEW_TONE["neutral"])
        themes = ", ".join(key_themes or []) or "(none extracted)"
        context = (
            f"Platform: {platform or 'unknown'}\n"
            f"Reviewer first name: {reviewer_name or 'unknown'}\n"
            f"{tone}\n"
            f"Key themes: {themes}\n"
            f"Their review:\n<review>\n{(review_text or '')[:1500]}\n</review>"
        )

        result = self._haiku(_REVIEW_RESPONSE_SYSTEM, context, max_tokens=260)
        if result:
            body, tok_in, tok_out, cost_usd = result
            model = config.MODEL_CHEAP
            log_cost("llm_call", self.AGENT_ID, model, cost_usd, tok_in, tok_out)
        else:
            body = self._fallback_review_response(reviewer_name, norm_sent)
            tok_in = tok_out = 0
            cost_usd = 0.0
            model = config.MODEL_CHEAP + "+fallback"

        draft = Draft(
            id=str(uuid.uuid4()),
            draft_type=DraftType.REVIEW_RESPONSE,
            content=body + self._public_reply_footer(),
            agent_id=self.AGENT_ID,
            model_used=model,
            tokens_in=tok_in,
            tokens_out=tok_out,
            cost_usd=cost_usd,
            created_at=datetime.utcnow(),
        )
        self._save(draft)
        # INV-2: log platform + sentiment + cost ONLY. Never the review text or
        # the reviewer's name (both may contain PII).
        audit.append("DRAFT_CREATED", draft.id, {
            "draft_type": "review_response",
            "platform": platform,
            "sentiment": norm_sent,
            "cost_usd": cost_usd,
        })
        return draft

    def _fallback_review_response(self, reviewer_name: str, sentiment: str) -> str:
        greet = f"Hi {reviewer_name}," if reviewer_name else "Hi there,"
        if sentiment == "positive":
            return (f"{greet} thank you so much for the kind words -- it means a lot "
                    f"to our team. We really enjoyed working on your project and would "
                    f"be glad to help again.")
        if sentiment == "negative":
            return (f"{greet} thank you for the feedback, and we're sorry your "
                    f"experience fell short of what we aim for. We'd like to put this "
                    f"right -- please reach out so we can help directly.")
        return (f"{greet} thanks for taking the time to share your feedback. We "
                f"appreciate it and would be happy to help with anything further.")

    # -- Remaining later-slice stubs ---------------------------------------------

    def draft_suburb_page(self, suburb: str, research: Optional[dict] = None,
                          demand: Optional[dict] = None) -> Draft:
        """
        Draft a unique suburb landing page for local SEO (Sonnet, P2 suburb slice).

        Website copy, so no opt-out footer. The Gate runs a semantic ACL pass
        (Sonnet) on this draft_type to catch subtle unsubstantiated claims beyond
        the deterministic superlative scan. Falls back to a compliant template if
        the LLM is unavailable (zero spend).
        """
        check_and_enforce(_EST_SUBURB_PAGE_AUD, self.AGENT_ID)

        context = self._summarise_research(suburb, research or {}, demand)
        result = self._sonnet(_SUBURB_PAGE_SYSTEM, context, max_tokens=900)
        if result:
            body, tok_in, tok_out, cost_usd = result
            model = config.MODEL_KEY
            log_cost("llm_call", self.AGENT_ID, model, cost_usd, tok_in, tok_out)
        else:
            body = self._fallback_suburb_page(suburb)
            tok_in = tok_out = 0
            cost_usd = 0.0
            model = config.MODEL_KEY + "+fallback"

        draft = Draft(
            id=str(uuid.uuid4()),
            draft_type=DraftType.SUBURB_PAGE,
            content=body,
            agent_id=self.AGENT_ID,
            model_used=model,
            tokens_in=tok_in,
            tokens_out=tok_out,
            cost_usd=cost_usd,
            created_at=datetime.utcnow(),
        )
        self._save(draft)
        audit.append("DRAFT_CREATED", draft.id, {
            "draft_type": "suburb_page",
            "suburb": suburb,                 # suburb is NOT PII (INV-2 safe)
            "cost_usd": cost_usd,
        })
        return draft

    def _summarise_research(self, suburb: str, research: dict,
                            demand: Optional[dict]) -> str:
        """Compact, safe brief for the model. Search snippets are BACKGROUND only --
        the model is told not to copy competitor wording or repeat their numbers."""
        lines = [f"Suburb: {suburb} (Sydney, NSW)"]
        if demand:
            lines.append(
                f"Seasonal demand index: {demand.get('demand_index')} "
                f"({demand.get('season')})"
            )
        for key in ("keywords", "competitor", "pricing", "pre_intent", "suburb"):
            items = research.get(key) or []
            if items:
                snippet = "; ".join((i.get("content", "")[:120]) for i in items[:3])
                lines.append(f"{key} signals: {snippet}")
        lines.append(
            "NOTE: the above are raw search snippets for background only. Do NOT "
            "copy competitor wording or repeat any numbers/claims from them."
        )
        return "\n".join(lines)

    def _fallback_suburb_page(self, suburb: str) -> str:
        s = suburb or "your suburb"
        return (
            f"House Painting in {s}\n\n"
            f"Looking for a reliable local painter in {s}? We provide interior and "
            f"exterior house painting for homes across {s} and the surrounding "
            f"Sydney area. From a single room to a full repaint, we focus on careful "
            f"preparation, tidy work, and clear communication from quote to "
            f"clean-up.\n\n"
            f"Our services in {s} include interior walls and ceilings, exterior "
            f"weatherproofing, doors and trim, and minor repairs before painting. We "
            f"are happy to talk through colours, timing, and budget to suit your "
            f"home.\n\n"
            f"As a local painting team, we can arrange a visit in {s} at a time that "
            f"works for you. Get in touch for a free, no-obligation quote and we will "
            f"walk you through the options."
        )

    def draft_capital_works_assessment(self, strata_info: dict) -> Draft:
        """Draft a Capital Works paint assessment (strata segment). (Phase 0 stub.)"""
        check_and_enforce(0.08, self.AGENT_ID)
        # TODO Phase 5: Sonnet with strata/property context
        draft = Draft(
            id=str(uuid.uuid4()),
            draft_type=DraftType.CAPITAL_WORKS_ASSESSMENT,
            content="[stub -- capital works assessment not yet implemented]",
            agent_id=self.AGENT_ID,
            model_used=config.MODEL_KEY,
        )
        self._save(draft)
        audit.append("DRAFT_CREATED", draft.id, {
            "draft_type": "capital_works_assessment",
            "strata_id": strata_info.get("id"),
        })
        return draft

    # -- persistence --------------------------------------------------------------

    def _save(self, draft: Draft) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """INSERT INTO drafts
                   (id, lead_id, draft_type, content, agent_id, model_used,
                    tokens_in, tokens_out, cost_usd, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (draft.id, draft.lead_id, draft.draft_type.value, draft.content,
                 draft.agent_id, draft.model_used, draft.tokens_in, draft.tokens_out,
                 draft.cost_usd, draft.created_at.isoformat())
            )
            conn.commit()
        finally:
            conn.close()
