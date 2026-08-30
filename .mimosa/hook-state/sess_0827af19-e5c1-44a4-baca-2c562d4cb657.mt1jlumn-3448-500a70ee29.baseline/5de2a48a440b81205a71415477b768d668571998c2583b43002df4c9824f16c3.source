"""
Worker F -- Lead Capture (KB-01/09, namespace: sync_*)
speed-to-lead capture + consent + sync to ServiceM8/Tradify.

INV-2 (non-negotiable): ONLY the sync_* methods may push PII to an external
CRM, and ONLY after a confirmed ConsentRecord exists for the lead. PII never
enters audit payloads (audit.py hash-refs; this module also never puts raw
name/phone/email in any payload it logs).

INV-1: pushing a customer's PII to a third party is an external action; the
orchestrator entry-point (sync_lead) requires an allow-listed operator chat id
(human-initiated). There is no automatic code path into _sync().

Offline behaviour: if the target CRM API key is not configured, sync runs in
DRY-RUN mode -- the SyncJob is persisted with mode=dry_run and status=pending,
and NO network call is made. Live mode uses resilience.call_with_retry with an
idempotency key so a retried request cannot create duplicate CRM records.

CRM pricing / lock-in (checked 2026-07, verify before committing):
  ServiceM8 (AU): flat per-business AUD/mo incl GST, unlimited users --
    Free (30 jobs/mo), Starter $29 (50 jobs), Growing $79 (150),
    Premium $149 (500), Premium Plus $349 (1500+). Cheapest for a solo
    painter at low volume.
  Tradify: per-user AUD/mo ex GST -- Lite $48, Pro $52, Plus $62 (+20c/SMS).
    Costs scale per staff member.
  Lock-in: both export jobs/clients to CSV; neither has a hard data hostage,
  but automations/forms/templates do NOT port across. This module keeps the
  sync payload to a minimal whitelist so switching CRM later is a small
  adapter change (_post_servicem8/_post_tradify), not a data-model rewrite.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from ..config import config
from ..database import get_connection
from ..models import Lead, ConsentRecord, ConsentMethod, SyncJob, SyncStatus
from .. import audit
from ..governance import check_and_enforce
from ..resilience import call_with_retry, new_idempotency_key

# Sync is a plain REST call (no LLM) -> ~0 AUD, but still governance-gated
# (kill switch + daily cap must hold for EVERY external action, INV-3).
_EST_SYNC_AUD = 0.0

# KB-01 s5: the ONLY fields that may leave the system. Nothing else, ever.
SYNC_FIELD_WHITELIST = (
    "name", "phone", "email", "suburb", "service_type",
    "source_channel", "consent_status", "notes",
)

_TARGETS = ("servicem8", "tradify")


class SyncBlocked(Exception):
    """Raised when a sync is refused (no consent / bad target / not allowed)."""
    pass


class LeadCaptureAgent:
    """
    Worker F: captures enquiries as Lead + ConsentRecord and syncs approved,
    consented leads to ServiceM8/Tradify (namespace sync_*).
    """
    AGENT_ID = "F_lead_capture"

    # -- capture / consent (no external I/O) ----------------------------------

    def capture(self, raw_enquiry: dict) -> Lead:
        """Capture an incoming enquiry as a Lead record. Sends nothing (INV-1)."""
        lead = Lead(
            id=str(uuid.uuid4()),
            name=raw_enquiry.get("name", ""),
            phone=raw_enquiry.get("phone", ""),
            email=raw_enquiry.get("email"),
            suburb=raw_enquiry.get("suburb", ""),
            service_type=raw_enquiry.get("service_type", ""),
            source_channel=raw_enquiry.get("source_channel", ""),
            consent_status=raw_enquiry.get("consent_status"),
            notes=raw_enquiry.get("notes", ""),
            created_at=datetime.utcnow(),
        )
        self._save_lead(lead)
        audit.append("ENQUIRY_RECEIVED", lead.id, {
            "source_channel": lead.source_channel,
            "service_type":   lead.service_type,
            "suburb":         lead.suburb,
            # no name/phone/email here -- INV-2 (audit.py would hash them,
            # but we do not put them in payloads in the first place)
        })
        return lead

    def record_consent(self, lead_id: str, method: ConsentMethod,
                       evidence: str) -> ConsentRecord:
        """Record consent evidence BEFORE any outbound contact (Spam Act/APP7)."""
        consent = ConsentRecord(
            id=str(uuid.uuid4()),
            lead_id=lead_id,
            method=method,
            timestamp=datetime.utcnow(),
            evidence=evidence,
        )
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO consent_records (id, lead_id, method, timestamp, evidence) "
                "VALUES (?, ?, ?, ?, ?)",
                (consent.id, consent.lead_id, consent.method.value,
                 consent.timestamp.isoformat(), consent.evidence)
            )
            conn.commit()
        finally:
            conn.close()
        audit.append("CONSENT_RECORDED", lead_id, {
            "method": method.value,
            "consent_id": consent.id,
        })
        return consent

    def get_consent(self, lead_id: str) -> Optional[dict]:
        """Latest ConsentRecord row for a lead, or None."""
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM consent_records WHERE lead_id = ? "
                "ORDER BY timestamp DESC LIMIT 1",
                (lead_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # -- sync_* (the ONLY methods allowed to push PII, INV-2) ------------------

    def sync_to_servicem8(self, lead: Lead) -> SyncJob:
        """Push a consented lead to ServiceM8. Blocked without ConsentRecord."""
        return self._sync(lead, "servicem8")

    def sync_to_tradify(self, lead: Lead) -> SyncJob:
        """Push a consented lead to Tradify. Blocked without ConsentRecord."""
        return self._sync(lead, "tradify")

    def _sync(self, lead: Lead, target: str) -> SyncJob:
        check_and_enforce(_EST_SYNC_AUD, self.AGENT_ID)  # INV-3, always first

        if target not in _TARGETS:
            raise SyncBlocked(f"unknown sync target: {target!r}")

        consent = self.get_consent(lead.id)
        if consent is None:
            audit.append("SYNC_BLOCKED", lead.id, {
                "target": target,
                "reason": "no_consent_record",
            })
            raise SyncBlocked(
                f"INV-2: lead {lead.id} has no ConsentRecord; "
                f"refusing to push PII to {target}."
            )

        payload = self._whitelisted_payload(lead)
        idem_key = new_idempotency_key()  # stable across retries below
        api_key = self._api_key(target)
        job = SyncJob(
            id=str(uuid.uuid4()),
            lead_id=lead.id,
            target_system=target,
            status=SyncStatus.PENDING,
        )
        mode = "dry_run"

        if api_key:
            mode = "live"
            result = call_with_retry(
                lambda: self._post(target, api_key, payload, idem_key),
                agent_id=self.AGENT_ID,
                before_attempt=lambda: check_and_enforce(_EST_SYNC_AUD, self.AGENT_ID),
                max_attempts=config.RETRY_MAX_ATTEMPTS,
                base_delay=config.RETRY_BASE_DELAY_SEC,
                max_delay=config.RETRY_MAX_DELAY_SEC,
            )
            job.external_client_id = result.get("client_id")
            job.external_job_id = result.get("job_id")
            job.status = SyncStatus.SYNCED
            job.synced_at = datetime.utcnow()

        self._save_sync_job(job)
        audit.append("SYNC", lead.id, {
            "target": target,
            "sync_job_id": job.id,
            "status": job.status.value,
            "mode": mode,
            "consent_id": consent["id"],
            "idempotency_key": idem_key,
            "fields_sent": list(SYNC_FIELD_WHITELIST),
            # external ids are CRM refs, not PII
            "external_client_id": job.external_client_id,
            "external_job_id": job.external_job_id,
        })
        return job

    # -- transport (live mode only; one attempt per call, retried by wrapper) --

    def _post(self, target: str, api_key: str, payload: dict, idem_key: str) -> dict:
        if target == "servicem8":
            return self._post_servicem8(api_key, payload, idem_key)
        return self._post_tradify(api_key, payload, idem_key)

    def _post_servicem8(self, api_key: str, payload: dict, idem_key: str) -> dict:
        """
        ServiceM8 REST: create client then job (api_1.0). X-Api-Key auth.
        Endpoint/auth per developer.servicem8.com -- verify against current
        docs before first live run (API surface may have changed).
        """
        import httpx
        headers = {
            "X-Api-Key": api_key,
            "Idempotency-Key": idem_key,
            "Content-Type": "application/json",
        }
        base = "https://api.servicem8.com/api_1.0"
        client_resp = httpx.post(f"{base}/client.json", headers=headers, json={
            "name": payload.get("name", ""),
            "mobile": payload.get("phone", ""),
            "email": payload.get("email") or "",
            "address_city": payload.get("suburb", ""),
        }, timeout=15.0)
        client_resp.raise_for_status()
        client_id = client_resp.headers.get("x-record-uuid", "")
        job_resp = httpx.post(f"{base}/job.json", headers=headers, json={
            "company_uuid": client_id,
            "job_description": self._job_description(payload),
            "status": "Quote",
        }, timeout=15.0)
        job_resp.raise_for_status()
        return {"client_id": client_id,
                "job_id": job_resp.headers.get("x-record-uuid", "")}

    def _post_tradify(self, api_key: str, payload: dict, idem_key: str) -> dict:
        """
        Tradify public API: create customer then job. Bearer auth.
        Verify endpoint shape against current Tradify API docs before first
        live run.
        """
        import httpx
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Idempotency-Key": idem_key,
            "Content-Type": "application/json",
        }
        base = "https://api.tradifyhq.com/v1"
        cust_resp = httpx.post(f"{base}/customers", headers=headers, json={
            "name": payload.get("name", ""),
            "phone": payload.get("phone", ""),
            "email": payload.get("email") or "",
            "suburb": payload.get("suburb", ""),
        }, timeout=15.0)
        cust_resp.raise_for_status()
        cust_id = str(cust_resp.json().get("id", ""))
        job_resp = httpx.post(f"{base}/jobs", headers=headers, json={
            "customerId": cust_id,
            "description": self._job_description(payload),
        }, timeout=15.0)
        job_resp.raise_for_status()
        return {"client_id": cust_id,
                "job_id": str(job_resp.json().get("id", ""))}

    # -- internals -------------------------------------------------------------

    @staticmethod
    def _job_description(payload: dict) -> str:
        return (f"{payload.get('service_type', 'painting')} enquiry -- "
                f"{payload.get('suburb', '')} (source: "
                f"{payload.get('source_channel', 'unknown')}). "
                f"{payload.get('notes', '')}").strip()

    @staticmethod
    def _api_key(target: str) -> str:
        if target == "servicem8":
            return config.SERVICEM8_API_KEY
        return config.TRADIFY_API_KEY

    @staticmethod
    def _whitelisted_payload(lead: Lead) -> dict:
        raw = {
            "name": lead.name, "phone": lead.phone, "email": lead.email,
            "suburb": lead.suburb, "service_type": lead.service_type,
            "source_channel": lead.source_channel,
            "consent_status": lead.consent_status, "notes": lead.notes,
        }
        return {k: raw[k] for k in SYNC_FIELD_WHITELIST}

    def _save_sync_job(self, job: SyncJob) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """INSERT INTO sync_jobs
                   (id, lead_id, target_system, status, external_client_id,
                    external_job_id, synced_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (job.id, job.lead_id, job.target_system, job.status.value,
                 job.external_client_id, job.external_job_id,
                 job.synced_at.isoformat() if job.synced_at else None,
                 job.created_at.isoformat())
            )
            conn.commit()
        finally:
            conn.close()

    def _save_lead(self, lead: Lead) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """INSERT INTO leads
                   (id, name, phone, email, suburb, service_type, source_channel,
                    consent_status, notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (lead.id, lead.name, lead.phone, lead.email, lead.suburb,
                 lead.service_type, lead.source_channel, lead.consent_status,
                 lead.notes, lead.created_at.isoformat())
            )
            conn.commit()
        finally:
            conn.close()
