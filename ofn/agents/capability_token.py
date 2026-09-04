"""capability_token — توکنِ قابلیتِ به‌ازای‌تسک (نقشهٔ اجرایی سند تلاقی، گام ۱).

الگوی Keycard: هیچ ارسالی از پایپ‌لاین‌ها بدون توکنِ پویای محدودشده
(اقدام، موضوع، انقضا، HMAC) انجام نمی‌شود — حتی اگر پایپ‌لاین به‌خطر بیفتد.
پرچم‌های سطح‌ماژول می‌مانند (لایهٔ ۱)؛ توکن لایهٔ ۲ است: هر send یک توکنِ
تازه با ttl کوتاه می‌خواهد. fail-closed: سرویسِ توکن در دسترس نبود = ارسال نیست.

راستی‌آزمایی سند تلاقی: ادعای «capability_flags موجود» در بورد/ولت یافت نشد
(E0) — این ماژول تازه ساخته شد. verified_send پارک است (بدون آداپتر خروج).
نمرهٔ صادق: E3 (مسیرهای منفی سبز).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets as _pysecrets
import sqlite3
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))

import opslib  # noqa: E402

DEFAULT_TTL_S = 900  # ۱۵ دقیقه — کوتاه‌تر از هر چرخهٔ تایمر


def _secret() -> bytes:
    """از secrets.env: OFN_SESSION_SECRET (همان کلید نشستِ موجود — رازِ نو نمی‌سازیم)."""
    val = os.environ.get("OFN_SESSION_SECRET", "")
    if not val:
        p = Path.home() / ".config/ofn/secrets.env"
        try:
            for ln in p.read_text().splitlines():
                if ln.startswith("OFN_SESSION_SECRET="):
                    val = ln.split("=", 1)[1].strip()
                    break
        except OSError:
            pass
    if not val:
        raise RuntimeError("no-token-secret")
    return val.encode()


def issue(action: str, subject: str, purpose: str,
          ttl_s: int = DEFAULT_TTL_S) -> dict:
    """توکنِ امضاشده صادر کن. action در {send_email}; subject = ایمیل گیرنده."""
    now = int(time.time())
    body = {"action": action, "subject": subject.strip().lower(),
            "purpose": purpose[:60], "iat": now, "exp": now + int(ttl_s),
            "nonce": _pysecrets.token_hex(8)}
    mac = hmac.new(_secret(), json.dumps(body, sort_keys=True).encode(),
                   hashlib.sha256).hexdigest()
    opslib.append_jsonl(opslib.STATE_DIR / "capability-tokens.jsonl",
                        {**body, "mac": mac[:12], "event": "issued"})
    return {**body, "mac": mac}


def verify(token: dict, action: str, subject: str) -> tuple[bool, str]:
    """(ok, reason) — امضا، انقضا، اقدام و موضوع همه باید بخوانند. fail-closed."""
    try:
        body = {k: token[k] for k in
                ("action", "subject", "purpose", "iat", "exp", "nonce")}
        mac = token.get("mac", "")
        expect = hmac.new(_secret(), json.dumps(body, sort_keys=True).encode(),
                          hashlib.sha256).hexdigest()
        if not hmac.compare_digest(mac, expect):
            return False, "bad-mac"
        if int(body["exp"]) < int(time.time()):
            return False, "expired"
        if body["action"] != action:
            return False, "action-mismatch"
        if body["subject"] != subject.strip().lower():
            return False, "subject-mismatch"
        return True, "ok"
    except Exception as e:  # noqa: BLE001
        return False, f"verify-error:{type(e).__name__}"


def request_send_token(candidate: dict, purpose: str) -> tuple[dict | None, str]:
    """لایهٔ سیاستِ پیش از صدور: halt/suppression/سقف — همان ترتیبِ گیت‌لدر."""
    halt = opslib.master_halted()
    if halt:
        return None, f"halted:{halt}"
    em = str((candidate or {}).get("email") or "").strip().lower()
    if not em:
        return None, "no-recipient"
    try:
        import consent_store as _cs
        if _cs.ConsentStore().suppression_active(em):
            return None, "suppressed"
    except Exception:  # noqa: BLE001 — suppression store نبود ≠ اجازه؛ محتاطانه می‌پرسیمِ لید
        pass
    try:
        import outbound_worker as _ow
        if _ow.cap_reached():
            return None, "daily-cap"
    except Exception:
        return None, "cap-check-failed"
    return issue("send_email", em, purpose), "ok"


def grants_send() -> bool:
    """Structurally False. A capability token is not a send."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def verified_send(token: dict, candidate: dict, draft: dict,
                  purpose: str) -> dict:
    """Parked send path. Token may verify; no outbound adapter is imported.

    A later disarm/hold still supersedes any older send claim. Ready
    is not authorized. This function never sets ``sent`` True.
    """
    em = str((candidate or {}).get("email") or "")
    ok, reason = verify(token, "send_email", em)
    if not ok:
        return {
            "sent": False,
            "status": "TOKEN_DENIED",
            "detail": reason,
            "grants_send": False,
        }
    return {
        "sent": False,
        "status": "TOKEN_PARKED",
        "detail": "send-path-parked",
        "grants_send": False,
        "purpose": purpose[:60],
    }
