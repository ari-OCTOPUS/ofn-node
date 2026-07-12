#!/usr/bin/env python3
"""email_inbound.py — Gmail OAuth readonly skeleton (P3، flag-off، propose-only).

فقط می‌خواند — هرگز نمی‌فرستد. ارسال ایمیل = پشتِ تحقیق.
بدون OCTOPUS_WIRE_EMAIL=1 → return [] بدون خطا (no-op).
بدون token → return [] بدون خطا (fail-soft).

Gmail API scope: https://www.googleapis.com/auth/gmail.readonly
Free tier: 1B quota units/day, 250/sec/user.
Internal app (Testing status): no verification needed for <100 users.

$0 · stdlib + opslib · fail-soft · propose-only.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib  # noqa: E402

# ─── flag ─────────────────────────────────────────────────────────────────────
FLAG_NAME = "OCTOPUS_WIRE_EMAIL"


def check_flag() -> bool:
    """OCTOPUS_WIRE_EMAIL=1 → فعال. بدون flag → no-op."""
    return os.environ.get(FLAG_NAME, "0") == "1"


# ─── config from budgets.yaml ───────────────────────────────────────────────
def _email_config() -> dict:
    """خواندنِ email section از budgets.yaml. fail-soft."""
    try:
        budgets = opslib.load_budgets()
        em = budgets.get("email", {})
        return {
            "client_id": str(em.get("gmail_client_id", "")).strip(),
            "client_secret": str(em.get("gmail_client_secret", "")).strip(),
            "token_path": str(em.get("gmail_token_path", "state/email/gmail_token.json")).strip(),
            "polling_interval": int(em.get("polling_interval_minutes", 30)),
        }
    except Exception:  # noqa: BLE001
        return {"client_id": "", "client_secret": "",
                "token_path": "state/email/gmail_token.json", "polling_interval": 30}


# ─── token persistence ───────────────────────────────────────────────────────
def _read_token(token_path: str | None = None) -> dict:
    """خواندنِ OAuth token از فایل. fail-soft."""
    cfg = _email_config()
    path = Path(token_path or cfg["token_path"])
    if not path.is_absolute():
        path = opslib.STATE_DIR / path
    try:
        d = json.loads(path.read_text("utf-8")) if path.exists() else {}
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _has_valid_token() -> bool:
    """آیا token موجود و غیرخالی؟"""
    t = _read_token()
    return bool(t.get("access_token") or t.get("refresh_token"))


# ─── fetch_unread ────────────────────────────────────────────────────────────
def fetch_unread(subject_filter: str | None = None,
                 max_results: int = 10) -> list[dict]:
    """Gmail API readonly: خواندنِ unreadها.
    ورودی: فیلترِ subject (اختیاری)، خروجی: [{subject, from, date, snippet, id}]
    بدون flag یا بدون token → return [] بدون خطا. propose-only."""
    if not check_flag():
        return []
    if not _has_valid_token():
        opslib.alert(["email_inbound: no valid token — configure OAuth first"])
        return []

    cfg = _email_config()
    if not cfg.get("client_id") or not cfg.get("client_secret"):
        opslib.alert(["email_inbound: gmail_client_id/secret not configured"])
        return []

    token = _read_token()
    access_token = token.get("access_token", "")
    if not access_token:
        return []

    # ── Gmail API REST call (stdlib urllib) ───────────────────────────
    import urllib.request
    import urllib.parse
    import urllib.error

    # Build query: unread + optional subject filter
    query_parts = ["is:unread", "in:inbox"]
    if subject_filter:
        query_parts.append(f"subject:{subject_filter}")
    q = urllib.parse.urlencode({"q": " ".join(query_parts), "maxResults": str(max_results)})

    url = f"https://www.googleapis.com/gmail/v1/users/me/messages?{q}"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        opslib.alert([f"email_inbound Gmail API error: {e.code} {e.reason}"])
        return []
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"email_inbound fetch failed: {type(e).__name__}: {e}"])
        return []

    messages = data.get("messages", [])
    results = []
    for msg_meta in messages[:max_results]:
        msg_id = msg_meta.get("id", "")
        msg = _fetch_message_detail(msg_id, access_token)
        if msg:
            results.append(msg)
    return results


def _fetch_message_detail(msg_id: str, access_token: str) -> dict | None:
    """خواندنِ جزئیاتِ یک پیام. fail-soft."""
    import urllib.request
    import urllib.error

    url = f"https://www.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=metadata&metadataHeaders=From%2CSubject%2CDate"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:  # noqa: BLE001
        return None

    headers = {}
    for h in data.get("payload", {}).get("headers", []):
        headers[h["name"].lower()] = h["value"]

    return {
        "id": msg_id,
        "subject": headers.get("subject", ""),
        "from": headers.get("from", ""),
        "date": headers.get("date", ""),
        "snippet": data.get("snippet", "")[:500],
        "labelIds": data.get("labelIds", []),
    }


# ─── parse_lead_from_email ───────────────────────────────────────────────────
def parse_lead_from_email(msg: dict) -> dict | None:
    """استخراجِ intake از محتوای ایمیل (پیش‌نویس، propose-only).
    فقط keyword-based ساده — بدون LLM. ارگانیسم هرگز ایمیل واقعی به LLM بیرونی نمی‌فرستد (D-26).

    Pattern: "painting" or "quote" in subject/snippet → return minimal QuoteIntake dict.
    Otherwise → None (not a lead)."""
    subject = (msg.get("subject") or "").lower()
    snippet = (msg.get("snippet") or "").lower()
    text = f"{subject} {snippet}"

    # Keywords that suggest a painting inquiry
    lead_keywords = ("paint", "quote", "painting", "renovat", "interior", "exterior",
                     "repaint", "touch-up", "room", "house", "apartment", "unit")

    if not any(kw in text for kw in lead_keywords):
        return None

    return {
        "source": "email",
        "email_id": msg.get("id"),
        "from": msg.get("from", ""),
        "date": msg.get("date", ""),
        "subject": msg.get("subject", ""),
        "snippet": msg.get("snippet", ""),
        "confidence": "keyword-match",  # not LLM — just keyword
    }


# ─── poll_and_digest ────────────────────────────────────────────────────────
def poll_and_digest() -> dict:
    """یک بار چک → لیستِ ایمیل‌های جدید + خلاصه. propose-only.
    خروجی: {n_unread, leads: [...], messages: [...]}"""
    if not check_flag():
        return {"n_unread": 0, "leads": [], "messages": [],
                "note": "OCTOPUS_WIRE_EMAIL not set — no-op"}

    messages = fetch_unread()
    leads = []
    for msg in messages:
        lead = parse_lead_from_email(msg)
        if lead:
            leads.append(lead)

    return {
        "ts": opslib.now_iso(),
        "n_unread": len(messages),
        "leads": leads,
        "messages": [{"subject": m.get("subject"), "from": m.get("from")} for m in messages],
        "note": f"{len(leads)} potential leads from {len(messages)} unread emails",
    }


if __name__ == "__main__":
    print(json.dumps(poll_and_digest(), ensure_ascii=False, indent=2))
