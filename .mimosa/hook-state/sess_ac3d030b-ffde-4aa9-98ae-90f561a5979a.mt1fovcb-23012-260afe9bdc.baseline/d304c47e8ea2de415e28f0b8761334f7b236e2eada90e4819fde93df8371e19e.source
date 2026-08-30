"""
00-Orchestrator -- Brushline (KB-01 s3)

intent -> plan -> route -> collect -> gate -> approve

MVP rule: workflow-driven (fixed code paths), NOT autonomous LLM decision.
LLM only fills in the *content* of each step, not the *routing* decisions.

Phase 1: research paths (Workers A + B) live.
Phase 2 (lead-path slice): enquiry + follow-up now draft (Worker C) and Gate.
Phase 2 (review slice, P1): review response now drafts (Worker C) and Gate.
Phase 3: PASS / SOFT_FLAG drafts are submitted to the Human Approval Queue
(HARD_BLOCK drafts are NOT queued -- they must be rewritten first, KB-07).
"""
from __future__ import annotations

from typing import Optional

from .config import config
from .governance import check_and_enforce
from .models import DraftType, GateStatus
from . import audit


class OrchestratorError(Exception):
    pass


class Orchestrator:
    """
    Routes tasks to Workers A-F and enforces the governance pipeline.

    Fixed workflow paths (KB-01 s1 -- no autonomous routing in MVP):
      Enquiry path:   F -> C -> Gate -> Queue -> (Sync if lead approved)
      Content path:   A -> C -> D? -> E -> Gate -> Queue
      Follow-up path: C -> Gate -> Queue
      Review path:    B -> C -> Gate -> Queue
    """

    def __init__(self):
        from .agents.researcher import Researcher
        from .agents.audience import AudienceAgent
        from .agents.content import ContentAgent
        from .agents.asset import AssetAgent
        from .agents.channel import ChannelAgent
        from .agents.lead_capture import LeadCaptureAgent
        from .gate import ConstitutionGate
        from .queue import ApprovalQueue

        self.researcher = Researcher()
        self.audience = AudienceAgent()
        self.content = ContentAgent()
        self.asset = AssetAgent()
        self.channel = ChannelAgent()
        self.lead_capture = LeadCaptureAgent()
        self.gate = ConstitutionGate()
        self.queue = ApprovalQueue()

    def _maybe_queue(self, draft, gate_result) -> Optional[str]:
        """
        Submit to the Human Approval Queue unless the Gate HARD_BLOCKed it
        (HARD_BLOCK drafts go back for rewrite, not into the queue, KB-07).
        Returns the ApprovalAction id, or None if not queued.
        """
        if gate_result.status == GateStatus.HARD_BLOCK:
            return None
        action = self.queue.submit(draft)
        return action.id

    # -- Enquiry path (Worker C draft -> Gate -> Queue) ----------------------------

    def intake_enquiry(self, raw_enquiry: dict) -> dict:
        """
        Full front door for a NEW enquiry (arch review 2026-07-02).

        handle_enquiry() alone never persisted a Lead row, so day-2/5/10
        follow-ups (_load_lead) and CRM sync (sync_lead) could not find the
        lead. This wrapper does it properly:
          1. Worker F captures the Lead (+ ENQUIRY_RECEIVED audit, PII-safe)
          2. speed-to-lead draft -> Gate -> Queue via handle_enquiry()
        Returns handle_enquiry's dict plus lead_id.
        """
        check_and_enforce(0.01, "orchestrator")
        lead = self.lead_capture.capture(raw_enquiry)
        enquiry = dict(raw_enquiry)
        enquiry["id"] = lead.id
        result = self.handle_enquiry(enquiry)
        result["lead_id"] = lead.id
        return result

    def handle_enquiry(self, enquiry: dict) -> dict:
        """
        Main entry-point for incoming lead enquiries.
        Triggers a speed-to-lead draft (target < 15 min, SLA_LEAD_MINUTES),
        runs it through the Constitution Gate, and -- unless HARD_BLOCKed --
        submits it to the Human Approval Queue (Phase 3).

        A customer-initiated enquiry establishes an inferred business
        relationship (Spam Act s7 / KB-09), so consent_verified=True for the
        first reply. The draft is still human-approved before sending (INV-1).

        enquiry keys: id, name, phone, suburb, service_type, source_channel, notes
        """
        check_and_enforce(0.01, "orchestrator")  # governance gate first

        audit.append("ENQUIRY_RECEIVED", enquiry.get("id", "unknown"), {
            "source_channel": enquiry.get("source_channel"),
            "service_type":   enquiry.get("service_type"),
            "suburb":         enquiry.get("suburb"),
        })

        draft = self.content.draft_speed_to_lead(lead=enquiry)
        gate = self.gate.check(draft, consent_verified=True)
        action_id = self._maybe_queue(draft, gate)

        return {
            "status":      "drafted",
            "draft_id":    draft.id,
            "draft_type":  draft.draft_type.value,
            "content":     draft.content,
            "gate_status": gate.status.value,
            "gate_flags":  gate.flags,
            "cost_usd":    draft.cost_usd,
            "queued":      action_id is not None,
            "approval_action_id": action_id,
            "next": (
                "Queued for human approval (Telegram /queue)."
                if action_id else
                "HARD_BLOCK -- rewrite required before queuing."
            ),
        }

    # -- Content path (A -> C -> D? -> E -> Gate -> Queue) -------------------------

    def kickoff_suburb_page(self, suburb: str, service_type: str = "residential") -> dict:
        """
        Operator-initiated: research + draft suburb landing page.
        Phase 1: Workers A+B run real search. Worker C draft in the suburb slice.
        """
        check_and_enforce(0.05, "orchestrator")
        audit.append("CONTENT_TASK_KICKOFF", "orchestrator", {
            "task_type": "suburb_page",
            "suburb": suburb,
            "service_type": service_type,
        })

        # Phase 1 -- Worker A research bundle
        suburb_intel     = self.researcher.search_suburb(suburb)
        competitor_intel = self.researcher.search_competitor(suburb, service_type)
        pricing_intel    = self.researcher.search_market_pricing(suburb, service_type)
        keyword_intel    = self.researcher.search_keyword_intent(suburb)
        pre_intent       = self.researcher.search_pre_intent_signals(suburb)

        # Phase 1 -- Worker B seasonal demand signal
        from datetime import date
        demand = self.audience.get_seasonal_demand(suburb, date.today().month)

        total_cost_usd = (
            suburb_intel.cost_usd
            + competitor_intel.cost_usd
            + pricing_intel.cost_usd
            + keyword_intel.cost_usd
            + pre_intent.cost_usd
        )
        audit.append("RESEARCH_COMPLETE", "orchestrator", {
            "suburb": suburb,
            "result_counts": {
                "suburb":      len(suburb_intel.results),
                "competitor":  len(competitor_intel.results),
                "pricing":     len(pricing_intel.results),
                "keywords":    len(keyword_intel.results),
                "pre_intent":  len(pre_intent.results),
            },
            "demand_index":    demand["demand_index"],
            "total_cost_usd":  total_cost_usd,
        })

        # Worker C drafts the page from the research bundle -> Gate -> Queue (P2).
        research_bundle = {
            "suburb":     suburb_intel.results,
            "competitor": competitor_intel.results,
            "pricing":    pricing_intel.results,
            "keywords":   keyword_intel.results,
            "pre_intent": pre_intent.results,
        }
        draft = self.content.draft_suburb_page(suburb, research_bundle, demand)
        # Not outbound (website copy): consent/opt-out n/a. Gate runs deterministic
        # ACL + PII + the semantic ACL (Sonnet) pass for this high-risk type.
        gate = self.gate.check(draft)
        action_id = self._maybe_queue(draft, gate)

        return {
            "status":            "drafted",
            "suburb":            suburb,
            "service_type":      service_type,
            "demand":            demand,
            "draft_id":          draft.id,
            "draft_type":        draft.draft_type.value,
            "content":           draft.content,
            "gate_status":       gate.status.value,
            "gate_flags":        gate.flags,
            "cost_usd":          draft.cost_usd,
            "research_cost_usd": total_cost_usd,
            "queued":            action_id is not None,
            "approval_action_id": action_id,
            "next": (
                f"Queued (priority {config.approval_priority('suburb_page')}) "
                f"for human approval (Telegram /queue)."
                if action_id else
                "HARD_BLOCK -- rewrite required before queuing."
            ),
        }

    def kickoff_followup(self, lead_id: str, followup_day: int,
                         consent_verified: bool = True) -> dict:
        """
        Auto-triggered follow-up on day 2/5/10 after enquiry.

        Follow-up to an enquiry customer is within the inferred business
        relationship (KB-09), so consent_verified defaults True. Pass False to
        force a HARD_BLOCK (e.g. the lead opted out -> suppression list).
        """
        check_and_enforce(0.01, "orchestrator")
        audit.append("CONTENT_TASK_KICKOFF", lead_id, {
            "task_type": "followup",
            "day": followup_day,
        })

        draft = self.content.draft_followup(lead_id, followup_day)
        gate = self.gate.check(draft, consent_verified=consent_verified)
        action_id = self._maybe_queue(draft, gate)

        return {
            "status":      "drafted",
            "lead_id":     lead_id,
            "day":         followup_day,
            "draft_id":    draft.id,
            "content":     draft.content,
            "gate_status": gate.status.value,
            "gate_flags":  gate.flags,
            "cost_usd":    draft.cost_usd,
            "queued":      action_id is not None,
            "approval_action_id": action_id,
            "next": (
                "Queued for human approval (Telegram /queue)."
                if action_id else
                "HARD_BLOCK -- rewrite required before queuing."
            ),
        }

    def kickoff_review_response(self, review: dict) -> dict:
        """
        Draft a PUBLIC reply to a Google/platform review (P1 review slice).

        Path: Worker B (sentiment) -> Worker C (draft, tone by sentiment) ->
        Gate -> Queue. A review reply is public, so the Gate applies ABN + ACL
        but NOT consent/opt-out. Still human-approved before posting (INV-1).

        review keys: text, platform, reviewer_name (optional)
        """
        check_and_enforce(0.01, "orchestrator")

        sentiment_result = self.audience.analyse_review(
            review_text=review.get("text", ""),
            platform=review.get("platform", "unknown"),
        )
        audit.append("CONTENT_TASK_KICKOFF", "orchestrator", {
            "task_type": "review_response",
            "platform":  sentiment_result.source,
            "sentiment": sentiment_result.sentiment,
            "score":     sentiment_result.score,
            "themes":    sentiment_result.key_themes,
            "cost_usd":  sentiment_result.cost_usd,
        })

        draft = self.content.draft_review_response(
            review_text=review.get("text", ""),
            sentiment=sentiment_result.sentiment,
            platform=sentiment_result.source,
            reviewer_name=review.get("reviewer_name", ""),
            key_themes=sentiment_result.key_themes,
        )
        # Public reply: consent is not applicable (Gate treats review_response as
        # public outbound). consent_verified is passed True but ignored for this type.
        gate = self.gate.check(draft, consent_verified=True)
        action_id = self._maybe_queue(draft, gate)

        return {
            "status":      "drafted",
            "draft_type":  draft.draft_type.value,
            "platform":    sentiment_result.source,
            "sentiment":   sentiment_result.sentiment,
            "score":       sentiment_result.score,
            "key_themes":  sentiment_result.key_themes,
            "draft_id":    draft.id,
            "content":     draft.content,
            "gate_status": gate.status.value,
            "gate_flags":  gate.flags,
            "cost_usd":    draft.cost_usd,
            "sentiment_cost_usd": sentiment_result.cost_usd,
            "queued":      action_id is not None,
            "approval_action_id": action_id,
            "next": (
                f"Queued (priority {config.approval_priority('review_response')}, "
                f"SLA {config.approval_sla_minutes('review_response')} min) "
                f"for human approval (Telegram /queue)."
                if action_id else
                "HARD_BLOCK -- rewrite required before queuing."
            ),
        }

    def kickoff_gbp_post(self, content: str,
                         cta: str = "Get in touch for a free, no-obligation quote.") -> dict:
        """
        Operator-initiated: Worker E drafts a Google Business Profile post
        (DRAFT only) -> Gate -> Queue (P4). Nothing is posted here; publishing
        happens only via ChannelAgent.publish() AFTER a human APPROVE (INV-1).
        """
        check_and_enforce(0.01, "orchestrator")
        audit.append("CONTENT_TASK_KICKOFF", "orchestrator", {
            "task_type": "gbp_post",
        })
        draft = self.channel.draft_gbp_post(content, cta=cta)
        # Marketing copy (not a direct message): consent/opt-out n/a; Gate runs
        # deterministic ACL + PII + the semantic ACL (Sonnet) pass.
        gate = self.gate.check(draft)
        action_id = self._maybe_queue(draft, gate)
        return {
            "status":      "drafted",
            "draft_id":    draft.id,
            "draft_type":  draft.draft_type.value,
            "content":     draft.content,
            "gate_status": gate.status.value,
            "gate_flags":  gate.flags,
            "queued":      action_id is not None,
            "approval_action_id": action_id,
            "next": (
                "Queued for human approval; publish only via Channel.publish() "
                "after APPROVE (INV-1)."
                if action_id else
                "HARD_BLOCK -- rewrite required before queuing."
            ),
        }

    def kickoff_followup_batch(self, jobs: list) -> dict:
        """
        Submit day-2/5/10 follow-ups as one Message Batch (P7, 50% off).
        Not time-sensitive, so async is fine. Falls back to the normal
        per-draft path when offline or BATCH_ENABLED=false.
        """
        check_and_enforce(0.01, "orchestrator")
        audit.append("CONTENT_TASK_KICKOFF", "orchestrator", {
            "task_type": "followup_batch",
            "n_jobs": len(jobs),
        })
        batch_id = self.content.submit_followup_batch(jobs)
        if batch_id is None:
            # fallback: draft each one now at full price (still Gate+Queue)
            results = [self.kickoff_followup(j["lead_id"], j["day"])
                       for j in jobs]
            return {"status": "fallback_sync", "batch_id": None,
                    "results": results}
        return {"status": "batch_submitted", "batch_id": batch_id,
                "n_jobs": len(jobs),
                "next": "call collect_followup_batch(batch_id) on a later "
                        "tick; drafts then go Gate -> Queue (INV-1)."}

    def collect_followup_batch(self, batch_id: str,
                               consent_verified: bool = True) -> dict:
        """Collect a finished batch; every draft still goes Gate -> Queue."""
        check_and_enforce(0.01, "orchestrator")
        drafts = self.content.collect_followup_batch(batch_id)
        if drafts is None:
            return {"status": "processing", "batch_id": batch_id}
        results = []
        for draft in drafts:
            gate = self.gate.check(draft, consent_verified=consent_verified)
            action_id = self._maybe_queue(draft, gate)
            results.append({
                "draft_id": draft.id,
                "gate_status": gate.status.value,
                "queued": action_id is not None,
            })
        return {"status": "collected", "batch_id": batch_id,
                "n_drafts": len(drafts), "results": results}

    def sync_lead(self, lead_id: str, target: str,
                  operator_chat_id: int) -> dict:
        """
        Operator-initiated: push a consented lead to ServiceM8/Tradify (P5).

        INV-1: pushing PII to a third party is an external action, so this
        entry-point is human-initiated by construction -- operator_chat_id
        MUST be in ALLOWED_OPERATOR_CHAT_IDS (fail-closed: empty list = no
        sync). INV-2: consent is enforced again inside LeadCaptureAgent._sync
        (defense in depth); PII never enters audit payloads.
        """
        check_and_enforce(0.001, "orchestrator")

        if operator_chat_id not in config.ALLOWED_OPERATOR_CHAT_IDS:
            audit.append("SYNC_BLOCKED", lead_id, {
                "target": target,
                "reason": "operator_not_allowed",
                "operator_chat_id": operator_chat_id,
            })
            from .agents.lead_capture import SyncBlocked
            raise SyncBlocked(
                f"operator chat id {operator_chat_id} not in "
                f"ALLOWED_OPERATOR_CHAT_IDS; sync refused (INV-1)."
            )

        lead = self._get_lead(lead_id)
        if lead is None:
            from .agents.lead_capture import SyncBlocked
            raise SyncBlocked(f"lead {lead_id} not found")

        audit.append("SYNC_KICKOFF", lead_id, {
            "target": target,
            "operator_chat_id": operator_chat_id,
        })
        if target == "servicem8":
            job = self.lead_capture.sync_to_servicem8(lead)
        else:
            job = self.lead_capture.sync_to_tradify(lead)
        return {
            "status": job.status.value,
            "sync_job_id": job.id,
            "target": job.target_system,
            "external_client_id": job.external_client_id,
            "external_job_id": job.external_job_id,
        }

    def _get_lead(self, lead_id: str):
        from .database import get_connection
        from .models import Lead
        from datetime import datetime as _dt
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM leads WHERE id = ?", (lead_id,)
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        r = dict(row)
        return Lead(
            id=r["id"], name=r["name"] or "", phone=r["phone"] or "",
            email=r["email"], suburb=r["suburb"] or "",
            service_type=r["service_type"] or "",
            source_channel=r["source_channel"] or "",
            consent_status=r["consent_status"], notes=r["notes"] or "",
            created_at=_dt.fromisoformat(r["created_at"]),
        )

    def kickoff_capital_works(self, strata_id: str, suburb: str) -> dict:
        """Draft a Capital Works paint assessment (strata segment, Phase 5+)."""
        check_and_enforce(0.10, "orchestrator")
        audit.append("CONTENT_TASK_KICKOFF", strata_id, {
            "task_type": "capital_works_assessment",
            "suburb": suburb,
        })
        # TODO Phase 5: Worker A (DA/strata signals) -> C -> Gate -> Queue
        return {"status": "stub", "strata_id": strata_id}
