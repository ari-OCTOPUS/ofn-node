#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""outbound_https.py — دسترسیِ محدودِ خروجیِ HTTPS (طراحیِ اسکلت، ۲۰۲۶-۰۸-۰۷).

چرا: خودِ ارگانیسم امشب درخواست کرد — «دسترسیِ HTTPS خروجیِ محدود به API
سرویسِ ایمیل/CRM موجود پروژه، با allow-list دامنه، ثبتِ رسید و تأییدِ مالک
پیش از هر ارسال». این ماژول همان را می‌سازد — فقط اسکلت، **هیچ‌جا وصل نشده**.
وصل‌کردنِ واقعی به outbound_worker.py موکول است به بعد از T7 (consent_store).

قاعدهٔ سخت (fail-closed، دو لایه):
  ۱) پشتِ `OCTOPUS_WIRE_OUTBOUND_HTTPS` (پیش‌فرض خاموش، مستقل از
     OCTOPUS_WIRE_LEAD_OUTBOUND — آن یکی دست‌نخورده می‌ماند).
  ۲) حتی با فلگ روشن، `submit()` قبل از هر تماسِ شبکه‌ای allow-list را چک
     می‌کند: نبودِ فایل/دامنهٔ ناشناس/متدِ غیرمجاز = BLOCKED، **هرگز** allow-all.

معماریِ دومرحله‌ای (چون approval_store.py کارِ آسنکرون است — مالک بعداً از
تلگرام تأیید/رد می‌کند، نه هم‌زمان با submit):
  submit()             → allow-list چک، spec کامل ذخیره، approval_store.add_pending
  execute_if_approved() → approval_store.get، اگر approved یک تلاشِ HTTPS
                          (بدونِ retry)، رسیدِ content-free، mark_done

هیچ صداکننده‌ای در این commit به outbound_worker.py یا هیچ فایلِ
`_ops/legs/**` وصل نمی‌شود — این فایل کاملاً بیرون از آن مرزِ حساس است.

$0 · stdlib-only (urllib) · fail-soft کامل.
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit

_HERE = Path(__file__).resolve().parent          # _ops/integrations
_OPS = _HERE.parent                                # _ops

for _p in (str(_OPS / "budget"), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib          # noqa: E402

# INVARIANT (S1-05): approval_store فقط از داخل telegram_center import می‌شود
# (تک‌مصرف‌کننده، RLock درون‌پروسه‌ای). این ماژول نباید آن را مستقیم import کند.
# به‌جای آن، یک storeِ محلیِ file-based اینجا می‌سازیم (JSON، نه RLock) تا
# invariant نقض نشود. وقتی consent_store (T7) آماده شد، این به آن ارتقا می‌یابد.

class _LocalApprovalStore:
    """File-based approval store (مستقل از telegram_center.approval_store).

    اسکلت: submit → JSON file → execute_if_approved → read JSON.
    هیچ RLock ندارد — file-based، تک‌نویسنده (این ماژول)."""

    def __init__(self, state_dir: Path):
        self._dir = state_dir / "outbound_https" / "approvals"
        self._dir.mkdir(parents=True, exist_ok=True)

    def add_pending(self, spec: dict) -> str:
        import hashlib
        job_id = hashlib.sha256(
            f"{spec.get('url','')}{time.time()}{uuid.uuid4()}".encode()
        ).hexdigest()[:16]
        (self._dir / f"{job_id}.json").write_text(
            json.dumps({"job_id": job_id, "spec": spec, "status": "pending"},
                       ensure_ascii=False), "utf-8")
        return job_id

    def get(self, job_id: str) -> dict | None:
        p = self._dir / f"{job_id}.json"
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text("utf-8"))
        except ValueError:
            return None

    def mark_done(self, job_id: str) -> None:
        p = self._dir / f"{job_id}.json"
        if p.exists():
            try:
                d = json.loads(p.read_text("utf-8"))
                d["status"] = "done"
                p.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
            except (ValueError, OSError):
                pass


# تزریق: کدِ downstream از approval_store استفاده می‌کرد؛ اکنون از storeِ محلی.
def _get_store():
    return _LocalApprovalStore(opslib.STATE_DIR)

FLAG = "OCTOPUS_WIRE_OUTBOUND_HTTPS"

_ALLOWLIST_PATH = opslib.STATE_DIR / "outbound_https" / "domain-allowlist.json"
_JOBS_DIR = opslib.STATE_DIR / "outbound_https" / "jobs"
_EVENTS_PATH = opslib.STATE_DIR / "outbound_https" / "events.jsonl"
_REQUEST_TIMEOUT_S = 20.0

_ALLOWED_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def _receipt(event_type: str, corr: str, payload: dict) -> None:
    """رسیدِ append-only — هم‌الگوی lead_outbound_transport._receipt. هرگز raise.
    content-free: فقط domain/status/طول، هرگز URL/بدنه/headerِ کامل."""
    try:
        opslib.append_jsonl(_EVENTS_PATH, {
            "event_id": uuid.uuid4().hex, "event_type": event_type,
            "occurred_at": opslib.now_iso(), "correlation_id": str(corr or ""),
            "source_component": "outbound_https", "schema_version": "1.0",
            "payload": payload})
    except Exception:  # noqa: BLE001
        pass


def _load_allowlist() -> dict:
    """fail-closed: نبود/خرابی/خالی → دیکشنریِ دامنه‌ی خالی (یعنی هیچ دامنه‌ای
    مجاز نیست) — هرگز allow-all به‌عنوانِ پیش‌فرض."""
    try:
        if not _ALLOWLIST_PATH.exists():
            return {}
        d = json.loads(_ALLOWLIST_PATH.read_text("utf-8"))
        domains = d.get("domains") if isinstance(d, dict) else None
        return domains if isinstance(domains, dict) else {}
    except (OSError, ValueError):
        return {}


def _check_allowlist(domain: str, method: str) -> "str | None":
    """None یعنی مجاز؛ رشته یعنی دلیلِ رد (fail-closed)."""
    allow = _load_allowlist()
    if not allow:
        return "allowlist_empty_or_missing"
    entry = allow.get(domain)
    if not isinstance(entry, dict):
        return "domain_not_allowlisted"
    methods = entry.get("methods")
    if not isinstance(methods, list) or method.upper() not in [str(m).upper() for m in methods]:
        return "method_not_allowlisted_for_domain"
    return None


def _gen_job_id() -> str:
    return f"outhttp_{time.strftime('%Y%m%dT%H%M%S', time.localtime())}_{uuid.uuid4().hex[:8]}"


def _job_path(job_id: str) -> Path:
    safe = "".join(c for c in str(job_id) if c.isalnum() or c in "_-")[:80] or "unknown"
    return _JOBS_DIR / f"{safe}.json"


def submit(method: str, url: str, *, headers: "dict | None" = None,
           body: "str | bytes | None" = None, purpose: str = "",
           correlation_id: str = "") -> dict:
    """اعتبارسنجیِ allow-list + ثبتِ jobِ منتظرِ تأیید. **هرگز** تماسِ شبکه‌ای
    این‌جا رخ نمی‌دهد — فقط submit/execute جدا هستند چون تأیید آسنکرون است.

    خروجی: `{"ok": bool, "status": "PENDING_APPROVAL"|"BLOCKED"|"OFF", "job_id"?, "reason"?}`."""
    if not flag_on():
        return {"ok": False, "status": "OFF", "reason": "flag-off"}
    method = str(method or "").strip().upper()
    if method not in _ALLOWED_METHODS:
        return {"ok": False, "status": "BLOCKED", "reason": "unsupported_method"}
    try:
        parts = urlsplit(str(url or ""))
    except ValueError:
        return {"ok": False, "status": "BLOCKED", "reason": "unparseable_url"}
    if parts.scheme != "https" or not parts.netloc:
        return {"ok": False, "status": "BLOCKED", "reason": "https_only"}
    domain = parts.hostname or ""
    reason = _check_allowlist(domain, method)
    if reason is not None:
        _receipt("outbound_https.blocked", correlation_id,
                 {"domain": domain, "method": method, "reason": reason})
        return {"ok": False, "status": "BLOCKED", "reason": reason, "domain": domain}

    job_id = _gen_job_id()
    spec = {"job_id": job_id, "method": method, "url": str(url),
            "headers": headers if isinstance(headers, dict) else {},
            "body": body if isinstance(body, (str, bytes)) else (
                json.dumps(body, ensure_ascii=False) if body is not None else ""),
            "purpose": str(purpose or "")[:200],
            "correlation_id": str(correlation_id or ""),
            "created_at": opslib.now_iso()}
    try:
        _JOBS_DIR.mkdir(parents=True, exist_ok=True)
        tmp = _job_path(job_id).with_suffix(".json.tmp")
        tmp.write_text(json.dumps(spec, ensure_ascii=False, indent=1), "utf-8")
        os.replace(tmp, _job_path(job_id))
    except OSError as e:
        return {"ok": False, "status": "BLOCKED", "reason": f"job_store_failed:{type(e).__name__}"}

    _store = _get_store()
    aid = _store.add_pending({
        "id": job_id, "type": "outbound_http",
        "title": f"HTTP خروجی به {domain}"[:160],
        "risk": "high", "requires_confirmation": True,
        "dry_run_report": f"{method} https://{domain}{parts.path[:80]}",
        "source": "outbound_https"})
    _receipt("outbound_https.submitted", correlation_id,
             {"domain": domain, "method": method, "job_id": job_id})
    return {"ok": True, "status": "PENDING_APPROVAL", "job_id": aid or job_id}


def execute_if_approved(job_id: str) -> dict:
    """اگر job تأییدشده باشد، دقیقاً یک تلاشِ HTTPS (بدونِ retry). ایمن در
    برابرِ چندبارصدازدن: قبل از تلاشِ شبکه، وضعیت را دوباره از approval_store
    می‌خواند — اگر از قبل done شده (یعنی تلاشِ قبلی رسیده)، دوباره نمی‌فرستد.

    خروجی: `{"status": "NOT_FOUND"|"PENDING"|"REJECTED"|"ALREADY_DONE"|"SENT"|"FAILED", ...}`."""
    _store = _get_store()
    rec = _store.get(job_id)
    if rec is None:
        return {"status": "NOT_FOUND"}
    st = str(rec.get("status") or "")
    if st == "pending":
        return {"status": "PENDING"}
    if st == "rejected":
        return {"status": "REJECTED"}
    if st == "done":
        return {"status": "ALREADY_DONE"}
    if st != "approved":
        return {"status": "UNKNOWN", "raw_status": st}

    spec_path = _job_path(job_id)
    try:
        spec = json.loads(spec_path.read_text("utf-8"))
    except (OSError, ValueError):
        return {"status": "FAILED", "reason": "job_spec_missing"}

    domain = urlsplit(spec.get("url", "")).hostname or ""
    method = spec.get("method", "GET")
    reason = _check_allowlist(domain, method)
    if reason is not None:
        # ری‌چک: بینِ submit و approve، allow-list ممکن است عوض شده باشد
        # (مالک با دست ویرایش کرد) — گیت باید همیشه *الان* را بسنجد، نه لحظهٔ submit.
        _receipt("outbound_https.blocked_at_execute", spec.get("correlation_id", ""),
                 {"domain": domain, "method": method, "reason": reason})
        return {"status": "FAILED", "reason": f"allowlist_changed:{reason}"}

    http_status = None
    ok = False
    try:
        import urllib.request
        req = urllib.request.Request(
            spec["url"], method=method,
            data=(spec.get("body") or "").encode("utf-8") if spec.get("body") else None,
            headers=spec.get("headers") or {})
        with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT_S) as resp:  # noqa: S310
            http_status = int(getattr(resp, "status", 200) or 200)
            ok = 200 <= http_status < 300
    except Exception as e:  # noqa: BLE001 — یک تلاش، بدونِ retry، شکست ثبت می‌شود نه raise
        _receipt("outbound_https.failed", spec.get("correlation_id", ""),
                 {"domain": domain, "method": method, "error": type(e).__name__})
        _store.mark_done(job_id)
        return {"status": "FAILED", "reason": type(e).__name__}

    _receipt("outbound_https.sent" if ok else "outbound_https.failed",
             spec.get("correlation_id", ""),
             {"domain": domain, "method": method, "http_status": http_status})
    _store.mark_done(job_id)
    return {"status": "SENT" if ok else "FAILED", "http_status": http_status}


if __name__ == "__main__":   # pragma: no cover — نمای دستیِ اپراتور
    os.environ.setdefault(FLAG, "1")
    print(json.dumps({"flag": FLAG, "enabled": flag_on(),
                      "allowlist": _load_allowlist()}, ensure_ascii=False, indent=1))
