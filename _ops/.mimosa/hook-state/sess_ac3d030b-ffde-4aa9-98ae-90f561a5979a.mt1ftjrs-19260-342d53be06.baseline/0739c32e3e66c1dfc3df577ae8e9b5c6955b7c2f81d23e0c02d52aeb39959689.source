#!/usr/bin/env python3
"""books_xero.py — providerِ Xero برای ریلِ شرکت (تصمیمِ تحقیقِ wf_d09b47b7، 2026-07-16).

چرا Xero (خلاصهٔ رأیِ قاضی): Custom Connection = OAuth2 client_credentials — توکنِ
۳۰دقیقه‌ای، **بدونِ refresh-token** (برای لپ‌تاپِ بی‌مراقب حیاتی)، بدونِ tenant-header؛
endpointِ واقعیِ ایمیلِ اینویس؛ عمیق‌ترین پشتهٔ AU (BAS e-lodge در UI، STP2، Payday Super)؛
مستندترین API + معافیتِ single-org از قیمتِ developerِ ۲۰۲۶.

قراردادِ providerِ company_books:
    connect_check() / list_invoices(status, limit) / create_draft_invoice(inv)

مرزها (هم‌راستا با ARCHITECTURE-TWO-RAILS):
  * نوشتن فقط **DRAFT** (این‌جا هم تحمیل می‌شود، مستقل از caller).
  * ارسالِ ایمیل/approve = داخلِ خودِ Xero توسطِ مالک (endpointِ Email فقط اینویسِ
    approved را می‌فرستد — عمداً این‌جا پیاده نشده تا مرزِ propose-only سفت بماند).
  * هیچ tax-conclusion: TaxType فقط اگر caller صریح بدهد؛ وگرنه پیش‌فرضِ خودِ Xero/حسابدار.
  * secretها (XERO_CLIENT_ID/XERO_CLIENT_SECRET در .env) هرگز echo/log نمی‌شوند.
  * fail-soft: هر خطا → {"ok": False, "note": نوعِ خطا}؛ هرگز crashِ caller.
  * rate-limit: 60/min/org — یک retry روی 429 با Retry-After (سقفِ ۱۰s).

sandbox: با Demo Company (AU) و یک اپِ auth-codeِ رایگان تست کن؛ production فقط
Custom Connection. $0 · stdlib (urllib/json/base64) · بدونِ SDK (سیاستِ stdlib-first).
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

TOKEN_URL = "https://identity.xero.com/connect/token"
API_BASE = "https://api.xero.com/api.xro/2.0"
_TIMEOUT_S = 30
_TOKEN_SKEW_S = 60                      # توکن را یک دقیقه زودتر منقضی فرض کن
_token_cache: dict = {"access_token": None, "expires_at": 0.0}


def _urlopen(req, timeout):
    """جدا برای تزریقِ تست (mock بدونِ شبکه)."""
    return urllib.request.urlopen(req, timeout=timeout)  # noqa: S310 — فقط هاست‌های ثابتِ Xero


def _creds() -> tuple[str, str] | None:
    cid = str(os.environ.get("XERO_CLIENT_ID", "") or "").strip()
    sec = str(os.environ.get("XERO_CLIENT_SECRET", "") or "").strip()
    return (cid, sec) if cid and sec else None


def _get_token(force: bool = False) -> str | None:
    """client_credentials → access_token (کشِ حافظه‌ای تا نزدیکِ انقضا). None = بی‌اعتبار."""
    now = time.monotonic()
    if not force and _token_cache["access_token"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]
    cr = _creds()
    if cr is None:
        return None
    basic = base64.b64encode(f"{cr[0]}:{cr[1]}".encode("utf-8")).decode("ascii")
    body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode("ascii")
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST", headers={
        "Authorization": f"Basic {basic}",
        "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with _urlopen(req, _TIMEOUT_S) as r:
            d = json.loads(r.read().decode("utf-8"))
        tok = str(d.get("access_token") or "")
        if not tok:
            return None
        _token_cache["access_token"] = tok
        _token_cache["expires_at"] = now + float(d.get("expires_in", 1800)) - _TOKEN_SKEW_S
        return tok
    except Exception:  # noqa: BLE001 — جزئیاتِ خطا ممکن است URL/بدنهٔ حساس داشته باشد
        return None


def _call(method: str, path: str, payload: dict | None = None,
          params: dict | None = None, _retried: bool = False) -> tuple[int, dict | None]:
    """یک فراخوانِ API. (status, json|None). 429 → یک retry با Retry-After؛
    401 → یک‌بار توکنِ تازه. هر خطای دیگر → (کد, None) بدونِ leak."""
    tok = _get_token()
    if tok is None:
        return 0, None
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {tok}", "Accept": "application/json",
        **({"Content-Type": "application/json"} if data else {})})
    try:
        with _urlopen(req, _TIMEOUT_S) as r:
            return int(getattr(r, "status", 200)), json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 429 and not _retried:
            try:
                wait = min(float(e.headers.get("Retry-After", "2") or 2), 10.0)
            except (TypeError, ValueError):
                wait = 2.0
            time.sleep(wait)
            return _call(method, path, payload, params, _retried=True)
        if e.code == 401 and not _retried:
            _get_token(force=True)
            return _call(method, path, payload, params, _retried=True)
        return e.code, None
    except Exception:  # noqa: BLE001
        return 0, None


# ─── قراردادِ provider ────────────────────────────────────────────────────────────
def connect_check() -> dict:
    """GET /Organisation → نامِ سازمان (اثباتِ اتصال). بدونِ creds → پیامِ صادق."""
    if _creds() is None:
        return {"ok": False, "org": None,
                "note": "XERO_CLIENT_ID/XERO_CLIENT_SECRET در .env نیست"}
    code, d = _call("GET", "/Organisation")
    if code == 200 and isinstance(d, dict):
        orgs = d.get("Organisations") or []
        name = str((orgs[0] or {}).get("Name", "")) if orgs else ""
        return {"ok": True, "org": name[:60] or "متصل", "note": "client_credentials ✓"}
    return {"ok": False, "org": None, "note": f"اتصال ناموفق (HTTP {code or 'شبکه'})"}


def list_invoices(status: str | None = None, limit: int = 20) -> dict:
    """اینویس‌های اخیر (read-only). خروجیِ کمینه — بدونِ آدرس/جزئیاتِ اضافی."""
    params = {"order": "UpdatedDateUTC DESC", "page": "1"}
    if status:
        safe = str(status).upper().replace('"', "")
        params["where"] = f'Status=="{safe}"'
    code, d = _call("GET", "/Invoices", params=params)
    if code != 200 or not isinstance(d, dict):
        return {"ok": False, "invoices": [], "note": f"HTTP {code or 'شبکه'}"}
    out = []
    for inv in (d.get("Invoices") or [])[: max(1, int(limit))]:
        if not isinstance(inv, dict):
            continue
        out.append({"id": str(inv.get("InvoiceID", "")),
                    "number": str(inv.get("InvoiceNumber", "")),
                    "status": str(inv.get("Status", "")),
                    "contact": str(((inv.get("Contact") or {}).get("Name", "")))[:40],
                    "total": inv.get("Total"),
                    "amount_due": inv.get("AmountDue")})
    return {"ok": True, "invoices": out, "note": ""}


def create_draft_invoice(inv: dict) -> dict:
    """POST /Invoices — **همیشه Status=DRAFT** (تحمیلِ این‌جا، مستقل از ورودی).
    نگاشتِ ورودیِ generic → Xero ACCREC. TaxType فقط اگر caller صریح داده باشد
    (تصمیمِ مالیاتی با Xero/حسابدار — RD-002/RD-003)."""
    items = []
    for li in (inv.get("line_items") or []):
        if not isinstance(li, dict):
            continue
        x = {"Description": str(li.get("description", ""))[:200],
             "Quantity": li.get("quantity", 1),
             "UnitAmount": li.get("unit_amount_aud", 0)}
        if li.get("account_code"):
            x["AccountCode"] = str(li["account_code"])
        if li.get("tax_type"):
            x["TaxType"] = str(li["tax_type"])
        items.append(x)
    if not items:
        return {"ok": False, "draft_id": None, "note": "line_items خالی"}
    payload = {"Invoices": [{
        "Type": "ACCREC", "Status": "DRAFT",              # مرزِ propose-only — hardcoded
        "Contact": {"Name": str(inv.get("contact_name", "مشتری"))[:100]},
        "LineItems": items,
        "Reference": str(inv.get("reference", ""))[:60]}]}
    if inv.get("due_date"):
        payload["Invoices"][0]["DueDate"] = str(inv["due_date"])[:10]
    if inv.get("branding_theme_id"):                       # قالبِ برند صریح (نکتهٔ تحقیق)
        payload["Invoices"][0]["BrandingThemeID"] = str(inv["branding_theme_id"])
    code, d = _call("POST", "/Invoices", payload=payload)
    if code == 200 and isinstance(d, dict):
        created = (d.get("Invoices") or [{}])[0]
        return {"ok": True, "draft_id": str(created.get("InvoiceID", "")) or None,
                "number": str(created.get("InvoiceNumber", "")),
                "note": "DRAFT ساخته شد — approve/ارسال داخلِ Xero با مالک"}
    return {"ok": False, "draft_id": None, "note": f"HTTP {code or 'شبکه'}"}


if __name__ == "__main__":
    print(json.dumps(connect_check(), ensure_ascii=False))
