#!/usr/bin/env python3
"""test_books_xero.py — providerِ Xero (2026-07-16). صفر شبکه (mockِ _urlopen).
اثبات: بدونِ creds صادق · توکن client_credentials + کش · connect_check نامِ سازمان ·
create_draft همیشه Status=DRAFT حتی با ورودیِ مخرب · 429 یک retry · 401 توکنِ تازه ·
هیچ secret در خروجی‌ها."""
import io
import json
import os
import sys
import urllib.error
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "legs"))
import books_xero as bx  # noqa: E402


class _Resp:
    def __init__(self, payload, status=200):
        self._b = json.dumps(payload).encode("utf-8")
        self.status = status

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _Fake:
    """صفِ پاسخ‌ها + ضبطِ درخواست‌ها."""
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, req, timeout):
        self.requests.append(req)
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def _reset(creds=True):
    bx._token_cache.update({"access_token": None, "expires_at": 0.0})
    for k in ("XERO_CLIENT_ID", "XERO_CLIENT_SECRET"):
        os.environ.pop(k, None)
    if creds:
        os.environ["XERO_CLIENT_ID"] = "cid-test"
        os.environ["XERO_CLIENT_SECRET"] = "SECRET-test-xyz"


TOK = _Resp({"access_token": "tok-1", "expires_in": 1800})


def t_a_no_creds_honest():
    _reset(creds=False)
    r = bx.connect_check()
    assert not r["ok"] and ".env" in r["note"], r


def t_b_connect_and_token_cache():
    _reset()
    fake = _Fake([TOK, _Resp({"Organisations": [{"Name": "ARMIN PTY LTD"}]}),
                  _Resp({"Organisations": [{"Name": "ARMIN PTY LTD"}]})])
    orig = bx._urlopen
    bx._urlopen = fake
    try:
        r = bx.connect_check()
        assert r["ok"] and r["org"] == "ARMIN PTY LTD", r
        r2 = bx.connect_check()                      # توکن از کش — فقط ۱ فراخوانِ دیگر
        assert r2["ok"], r2
        assert len(fake.requests) == 3               # 1 token + 2 org
        # درخواستِ توکن Basic دارد و URL درست
        assert fake.requests[0].full_url == bx.TOKEN_URL
        assert fake.requests[0].get_header("Authorization", "").startswith("Basic ")
    finally:
        bx._urlopen = orig


def t_c_draft_always_draft_even_malicious():
    _reset()
    fake = _Fake([TOK, _Resp({"Invoices": [{"InvoiceID": "xid-1", "InvoiceNumber": "INV-0001"}]})])
    orig = bx._urlopen
    bx._urlopen = fake
    try:
        r = bx.create_draft_invoice({"contact_name": "Client", "status": "AUTHORISED",
                                     "line_items": [{"description": "نقاشی", "quantity": 1,
                                                     "unit_amount_aud": 450.0}]})
        assert r["ok"] and r["draft_id"] == "xid-1", r
        body = json.loads(fake.requests[-1].data.decode("utf-8"))
        assert body["Invoices"][0]["Status"] == "DRAFT", body       # مرز، مستقل از ورودی
        assert body["Invoices"][0]["Type"] == "ACCREC"
        assert "TaxType" not in body["Invoices"][0]["LineItems"][0]  # هیچ حکمِ مالیاتی
    finally:
        bx._urlopen = orig


def t_d_429_retries_once():
    _reset()
    err = urllib.error.HTTPError("u", 429, "rate", {"Retry-After": "0"}, io.BytesIO(b""))
    fake = _Fake([TOK, err, _Resp({"Invoices": []})])
    orig = bx._urlopen
    orig_sleep = bx.time.sleep
    bx._urlopen = fake
    bx.time.sleep = lambda s: None
    try:
        r = bx.list_invoices()
        assert r["ok"] and r["invoices"] == [], r
    finally:
        bx._urlopen = orig
        bx.time.sleep = orig_sleep


def t_e_401_refreshes_token_once():
    _reset()
    err = urllib.error.HTTPError("u", 401, "unauth", {}, io.BytesIO(b""))
    fake = _Fake([TOK, err, TOK, _Resp({"Organisations": [{"Name": "ORG"}]})])
    orig = bx._urlopen
    bx._urlopen = fake
    try:
        r = bx.connect_check()
        assert r["ok"] and r["org"] == "ORG", r
    finally:
        bx._urlopen = orig


def t_f_no_secret_leak_anywhere():
    _reset()
    fake = _Fake([TOK, _Resp({"Organisations": [{"Name": "ORG"}]}),
                  _Resp({"Invoices": []})])
    orig = bx._urlopen
    bx._urlopen = fake
    try:
        blob = repr(bx.connect_check()) + repr(bx.list_invoices())
        assert "SECRET-test" not in blob and "cid-test" not in blob, blob
    finally:
        bx._urlopen = orig


if __name__ == "__main__":
    for f in (t_a_no_creds_honest, t_b_connect_and_token_cache,
              t_c_draft_always_draft_even_malicious, t_d_429_retries_once,
              t_e_401_refreshes_token_once, t_f_no_secret_leak_anywhere):
        f()
        print("ok", f.__name__)
    print("PASS test_books_xero")
