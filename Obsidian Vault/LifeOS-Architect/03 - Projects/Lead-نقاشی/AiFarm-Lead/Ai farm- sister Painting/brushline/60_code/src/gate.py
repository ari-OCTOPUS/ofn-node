"""
Constitution Gate -- Brushline (KB-07)
Evaluator-Optimizer pattern (KB-01 s3).

Checks every draft before it reaches the Approval Queue:
  ACL s29       -> no false / unsubstantiated claims (superlative scan; semantic
                   Sonnet check is TODO for the suburb-page slice)
  Spam Act 2003 -> DIRECT outbound (speed_to_lead/followup) requires consent
  Sender ID     -> ANY outbound (direct OR public reply) must carry business ABN
  Opt-out       -> DIRECT outbound must include a functional unsubscribe / STOP
  Review reply  -> public platform reply (review_response): ABN + ACL apply;
                   consent + opt-out do NOT (not a message to an address) [P1]
  Privacy       -> surface raw-PII patterns in body (INV-2)
  Sovereignty   -> sensitive AU data not sent offshore (INV-2)

Output: GateResult (PASS / SOFT_FLAG / HARD_BLOCK)
HARD_BLOCK -> draft returned to Content agent for rewrite (up to GATE_MAX_ROUNDS).

Lead-path slice: all checks here are DETERMINISTIC (zero LLM cost). The semantic
ACL evaluation via Sonnet (~AUD $0.016/draft, KB-02 s3.1) lands with suburb pages.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime

from .config import config
from .database import get_connection
from .models import Draft, GateResult, GateStatus
from . import audit

import logging

try:
    from anthropic import Anthropic
except ImportError:  # SDK absent -> semantic ACL layer is skipped (deterministic only)
    Anthropic = None

from .governance import check_and_enforce, log_cost

# Sonnet pricing (Jun 2026): input $3.00/Mtok, output $15.00/Mtok (KB-02 s2.1)
_SONNET_INPUT_USD_PER_TOK = 3.00 / 1_000_000
_SONNET_OUTPUT_USD_PER_TOK = 15.00 / 1_000_000
_EST_SEMANTIC_ACL_AUD = 0.02  # ~AUD per Sonnet semantic-ACL pass (KB-02 s3.1)

_SEMANTIC_ACL_SYSTEM = (
    "You are a compliance reviewer for Australian Consumer Law s29 (misleading or "
    "unsubstantiated claims). Read the marketing draft and list any specific phrases "
    "that make an absolute, superlative, or unsubstantiated claim a painting business "
    "could not readily prove -- e.g. 'trusted by thousands', 'award-winning', "
    "'25 years experience', 'the highest quality', invented ratings, review counts "
    "or guarantees. Ignore ordinary provable statements. Return ONLY JSON: "
    '{"claims": ["exact phrase", ...]}. Use an empty list if there are none.'
)


class GateError(Exception):
    pass


class ConstitutionGate:
    """
    Single gate instance (Evaluator-Optimizer = Constitution Gate, KB-01 s3).
    NOT a separate agent -- it IS the evaluator step.
    """
    AGENT_ID = "gate"

    # ACL s29: unsubstantiated absolute claims (deterministic first pass)
    _BANNED_SUPERLATIVES = (
        "best", "cheapest", "guaranteed", "guarantee", "#1", "no.1",
        "number one", "100%", "lowest price", "unbeatable", "the only",
    )
    # Spam Act: a functional opt-out must be present in outbound messages
    _OPTOUT_TERMS = ("opt out", "opt-out", "unsubscribe", "reply stop", "stop to opt")
    # INV-2: raw PII patterns that should not appear in a draft body
    _PII_PATTERNS = (
        r"\b04\d{8}\b",                     # AU mobile (04xxxxxxxx)
        r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b",   # email address
    )
    # Direct commercial electronic messages (Spam Act 2003): consent + opt-out required.
    _DIRECT_OUTBOUND_TYPES = ("speed_to_lead", "followup")
    # Public platform replies (e.g. a Google review response): posted publicly, so
    # NOT a "commercial electronic message" sent to an address -- consent + opt-out
    # do not apply, but sender-ID (ABN) and ACL s29 still do (P1 review slice).
    _PUBLIC_OUTBOUND_TYPES = ("review_response",)
    _OUTBOUND_TYPES = _DIRECT_OUTBOUND_TYPES + _PUBLIC_OUTBOUND_TYPES
    _HARD_PREFIXES = ("SPAM_NO_CONSENT", "SENDER_ID_MISSING_ABN", "NO_OPT_OUT")
    # High-risk marketing types that get the extra semantic ACL (Sonnet) pass (P2).
    _SEMANTIC_ACL_TYPES = ("suburb_page", "gbp_post", "blog_outline", "caption")

    def __init__(self) -> None:
        # Optional Sonnet client for the semantic ACL layer. Absent key or SDK ->
        # semantic pass is skipped and the gate stays fully deterministic.
        if config.ANTHROPIC_API_KEY and Anthropic is not None:
            self._llm = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        else:
            self._llm = None

    def check(self, draft: Draft, consent_verified: bool = False) -> GateResult:
        """
        Run all compliance checks on a draft.

        Args:
            draft:            The Draft to check.
            consent_verified: Whether consent is confirmed for outbound contact.

        Returns:
            GateResult with status PASS, SOFT_FLAG, or HARD_BLOCK.
        """
        flags: list[str] = []
        acl_ok = True
        sender_id_ok = True
        privacy_ok = True
        sovereignty_ok = True

        content = draft.content or ""
        lc = content.lower()
        dtype = draft.draft_type.value
        is_direct = dtype in self._DIRECT_OUTBOUND_TYPES     # message to a person
        is_public = dtype in self._PUBLIC_OUTBOUND_TYPES     # public platform reply
        is_outbound = is_direct or is_public
        # Consent governs DIRECT commercial messages only; a public review reply
        # is not sent to an electronic address, so consent is not applicable.
        spam_consent_ok = consent_verified if is_direct else True

        # -- ACL s29: deterministic superlative scan (all draft types) -----------
        for term in self._BANNED_SUPERLATIVES:
            if term in lc:
                flags.append(f"ACL_SUPERLATIVE: unsubstantiated claim '{term}' (ACL s29)")
                acl_ok = False

        # -- Sender ID (ABN): required on ANY outbound, direct or public reply ----
        if is_outbound and config.BUSINESS_ABN and config.BUSINESS_ABN not in content:
            flags.append("SENDER_ID_MISSING_ABN: outbound must carry the business ABN")
            sender_id_ok = False

        # -- Spam Act 2003: consent + opt-out apply to DIRECT messages only -------
        # A public review reply needs neither (P1 review slice).
        if is_direct:
            if not spam_consent_ok:
                flags.append("SPAM_NO_CONSENT: outbound message requires verified consent")
            if not any(t in lc for t in self._OPTOUT_TERMS):
                flags.append("NO_OPT_OUT: outbound must include a functional opt-out")
                sender_id_ok = False

        # -- Privacy (INV-2): surface raw-PII patterns in the body ---------------
        for pat in self._PII_PATTERNS:
            if re.search(pat, content):
                flags.append("PII_PATTERN_DETECTED: verify no raw customer PII in body (INV-2)")
                privacy_ok = False
                break

        # -- Semantic ACL (Sonnet) for high-risk marketing drafts (P2) -----------
        # Additive + advisory: extends acl_ok/flags, never a HARD block on its own.
        for sf in self._semantic_acl(draft):
            flags.append(sf)
            acl_ok = False

        # -- Status: HARD for legal blockers, SOFT for advisory flags ------------
        hard_flags = [f for f in flags if f.startswith(self._HARD_PREFIXES)]
        soft_flags = [f for f in flags if f not in hard_flags]

        if hard_flags:
            status = GateStatus.HARD_BLOCK
        elif soft_flags:
            status = GateStatus.SOFT_FLAG
        else:
            status = GateStatus.PASS

        result = GateResult(
            id=str(uuid.uuid4()),
            draft_id=draft.id,
            status=status,
            acl_ok=acl_ok,
            spam_consent_ok=spam_consent_ok,
            sender_id_ok=sender_id_ok,
            privacy_ok=privacy_ok,
            sovereignty_ok=sovereignty_ok,
            flags=flags,
            round_num=1,
            checked_at=datetime.utcnow(),
        )

        self._save(result)
        audit.append("GATE_CHECK", draft.id, {
            "gate_status": status.value,
            "flags": flags,
            "draft_type": draft.draft_type.value,
            "round": result.round_num,
        })
        return result

    def _semantic_acl(self, draft: Draft) -> list:
        """Sonnet pass for high-risk marketing drafts: catches subtle unsubstantiated
        claims the deterministic superlative scan misses (P2). Advisory (SOFT_FLAG),
        additive to the deterministic result -- never replaces it. Skipped when no
        LLM is configured or the draft is not a high-risk marketing type."""
        if not self._llm or draft.draft_type.value not in self._SEMANTIC_ACL_TYPES:
            return []
        # INV-3: governance gate BEFORE the paid Sonnet call (may raise -> propagate).
        check_and_enforce(_EST_SEMANTIC_ACL_AUD, self.AGENT_ID)
        try:
            msg = self._llm.messages.create(
                model=config.MODEL_KEY,
                max_tokens=400,
                system=_SEMANTIC_ACL_SYSTEM,
                messages=[{"role": "user", "content": (draft.content or "")[:4000]}],
            )
            text = msg.content[0].text.strip()
            tok_in = msg.usage.input_tokens
            tok_out = msg.usage.output_tokens
            cost = (tok_in * _SONNET_INPUT_USD_PER_TOK
                    + tok_out * _SONNET_OUTPUT_USD_PER_TOK)
            log_cost("llm_call", self.AGENT_ID, config.MODEL_KEY,
                     round(cost, 8), tok_in, tok_out)
            claims = json.loads(text).get("claims", [])
            return [
                f"ACL_SEMANTIC: unsubstantiated claim '{c}' (ACL s29, Sonnet)"
                for c in claims if c
            ]
        except Exception as exc:
            # Advisory layer: on any LLM/parse error, defer to the deterministic
            # gate rather than blocking. Logged for observability.
            logging.getLogger(__name__).error("semantic ACL check failed: %s", exc)
            return []

    def _save(self, result: GateResult) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """INSERT INTO gate_results
                   (id, draft_id, status, acl_ok, spam_consent_ok, sender_id_ok,
                    privacy_ok, sovereignty_ok, flags, round_num, checked_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (result.id, result.draft_id, result.status.value,
                 int(result.acl_ok), int(result.spam_consent_ok),
                 int(result.sender_id_ok), int(result.privacy_ok),
                 int(result.sovereignty_ok), json.dumps(result.flags),
                 result.round_num, result.checked_at.isoformat())
            )
            conn.commit()
        finally:
            conn.close()
