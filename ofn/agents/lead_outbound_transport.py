"""lead_outbound_transport — the real email transport for lead effects.

Lane G transport (owner vote 17, armed in deploy env). Contract called by
outbound_worker._transport_for:

  send(cand, draft, now=None) -> dict   # {sent, status, channel, ...}

Honesty rules:
  · No resolvable SMTP credential  → {"sent": False, "status": "NOT_ARMED"}
    — never an exception, never a fake success.
  · Suppressed recipient           → {"sent": False, "status": "SUPPRESSED"}
    (checked against the consent store's suppression table, freshly opened).
  · Server accepted                → {"sent": True, "status": "SENT"}
    and the effect row is reconciled via lead_effect_gate.mark_outcome.
  · Disconnect/timeout after DATA  → {"sent": False, "status":
    "UNKNOWN_OUTCOME"} — the provider may or may not have delivered;
    reconciliation, not a retry, decides (A09: no automatic resend).
  · Clean failure                  → {"sent": False, "status": "SEND_FAILED"}.

The Message-ID is derived from the stable effect_id so providers and
threads can dedupe. Recipient address comes from the candidate dict only;
nothing here invents contact data. Secrets are read through
mail_credentials (env) and never logged.
"""

from __future__ import annotations

import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import mail_credentials  # noqa: E402
import opslib  # noqa: E402

SCHEMA = "octopus.lead-outbound-transport.v1"


def _not_armed(reason: str) -> dict:
    return {"sent": False, "status": "NOT_ARMED", "channel": "email",
            "reason": reason}


def _recipient_of(cand: dict) -> str:
    contact = (cand or {}).get("contact") or {}
    return str(contact.get("email") or (cand or {}).get("email") or "").strip()


def _store_suppressed(channel_value_norm: str, channel_kind: str, reason: str,
                      store=None) -> bool:
    """Append a suppression row (never purged; lift is nullable column)."""
    s = store
    own = False
    if s is None:
        import consent_store as _cs  # noqa: WPS433
        s = _cs.ConsentStore()
        own = True
    try:
        s.insert_suppression(str(channel_value_norm), str(channel_kind),
                             str(reason))
        return True
    except Exception:  # noqa: BLE001 — recording a suppression must not crash the worker
        return False
    finally:
        if own:
            try:
                s.close()
            except Exception:  # noqa: BLE001
                pass


def _feed_suppression(cand: dict, reason: str, store=None) -> bool:
    """Suppress the candidate's own email (STOP replies, bounces)."""
    addr = _recipient_of(cand)
    if not addr:
        return False
    import consent_gate  # noqa: WPS433 — same-directory normalize
    return _store_suppressed(consent_gate.normalize_email(addr), "email",
                             reason, store)


def send(cand: dict, draft: str, now=None) -> dict:
    cand = cand or {}
    effect_id = str(cand.get("effect_id") or "")
    addr = _recipient_of(cand)
    if not addr:
        return {"sent": False, "status": "NO_RECIPIENT", "channel": "email"}
    cr = mail_credentials.resolve()
    if not cr or not cr.get("ok"):
        return _not_armed(str((cr or {}).get("reason") or "credentials-unresolved"))
    import consent_gate  # noqa: WPS433
    norm = consent_gate.normalize_email(addr)
    store = None
    try:
        import consent_store as _cs  # noqa: WPS433
        store = _cs.ConsentStore()
        active = store.suppression_active(norm)
    except Exception:  # noqa: BLE001 — cannot verify suppression → refuse
        return {"sent": False, "status": "SUPPRESSION_CHECK_UNAVAILABLE",
                "channel": "email"}
    finally:
        if store is not None:
            try:
                store.close()
            except Exception:  # noqa: BLE001
                pass
    if active:
        return {"sent": False, "status": "SUPPRESSED", "channel": "email",
                "reason": str(active)}

    host = str(cr.get("host") or "")
    port = int(cr.get("port") or 0)
    user = str(cr.get("user") or "")
    # the password travels by env NAME only (never a value through resolve)
    import os
    password = os.environ.get(str(cr.get("secret_env") or ""), "")
    from_addr = str(cr.get("from_addr") or user)
    if not host or not port:
        return _not_armed("smtp-host-unset")

    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = addr
    msg["Subject"] = str(cand.get("subject") or "Quote from our team")
    if effect_id:
        msg["Message-ID"] = f"<{effect_id}@ofn.lead>"
    msg.set_content(str(draft or ""))

    accepted = False
    outcome: str | None = None
    sent = False
    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.ehlo()
            try:
                smtp.starttls()
                smtp.ehlo()
            except smtplib.SMTPException:
                pass  # some LAN relays are plaintext by design
            if user and password:
                smtp.login(user, password)
            refused = smtp.send_message(msg)
            accepted = not refused
    except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError,
            TimeoutError, OSError):
        outcome = "connection-lost"
    except smtplib.SMTPAuthenticationError:
        outcome = "auth-failed"
    except smtplib.SMTPException:
        outcome = "smtp-error"

    if accepted:
        sent = True
        status = "SENT"
        provider = "smtp_accepted"
    elif outcome == "connection-lost":
        # A09: crash window — the provider outcome is genuinely unknown.
        status = "UNKNOWN_OUTCOME"
        provider = "unknown_after_data"
    else:
        status = "SEND_FAILED"
        provider = outcome or "smtp-failed"

    if effect_id:
        try:
            import lead_effect_gate as _leg  # noqa: WPS433
            _leg.mark_outcome(effect_id, sent if accepted else (None if
                              status == "UNKNOWN_OUTCOME" else False),
                              provider)
        except Exception:  # noqa: BLE001 — receipt failure must not fake success
            pass
    return {"sent": sent, "status": status, "channel": "email",
            "provider": provider}
