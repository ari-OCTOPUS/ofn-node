"""test_lead_boundary_http.py — Trust-Engine P0: مرزِ امضاشده (D7).

تست‌های الزامیِ مأموریت: کاندیدِ امضاشدهٔ معتبر پذیرفته · امضای نامعتبر رد · timestamp منقضی رد ·
nonce تکراری رد · idempotency تکراری هیچ لیدِ دوم · halt→503 · بی‌امضا quarantine نمی‌شود ·
negative-n8n (صفر importِ گیت/تأیید/ارسال) · یک smokeِ زندهٔ سوکت.
"""
import ast
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness
ENV = harness.setup("lead-boundary-http")

import importlib                       # noqa: E402
import opslib                          # noqa: E402
import lead_candidate_inbox as lci     # noqa: E402
importlib.reload(lci)
import lead_boundary_http as b         # noqa: E402
importlib.reload(b)

_SRC = "n8n_da"
_SECRET = "test-secret-do-not-ship"


def _setup_env():
    os.environ[lci.FLAG] = "1"
    os.environ[b.FLAG] = "1"
    os.environ["OCTOPUS_INGEST_SOURCES"] = _SRC + ",n8n_domain"
    os.environ["OCTOPUS_INGEST_SECRET_N8N_DA"] = _SECRET
    os.environ.pop("OCTOPUS_INGEST_RATE_PER_MIN", None)


def _body(external_id="DA-1", ctype="market_signal", channel="nsw_da"):
    return json.dumps({
        "schema_version": "1.1",
        "source": {"channel": channel, "source_id": _SRC, "external_id": external_id,
                   "received_at": "2026-07-21T06:00:00Z"},
        "candidate_type": ctype,
        "consent": {"basis": "none"},
        "request": {"scope_text": "DA approved alterations"},
    }).encode("utf-8")


def _headers(body, *, ts=None, nonce="n-1", source=_SRC, secret=_SECRET, sign=True, idem=None):
    ts = str(ts if ts is not None else int(time.time()))
    sig = hmac.new(secret.encode(), f"{ts}.{nonce}.".encode() + body,
                   hashlib.sha256).hexdigest() if sign else "deadbeef"
    hdr = {"X-Octopus-Source": source, "X-Octopus-Timestamp": ts,
           "X-Octopus-Nonce": nonce, "X-Octopus-Signature": sig}
    if idem is not None:
        hdr["Idempotency-Key"] = idem
    return hdr


# VQ-PORT-COLLISION-001 (برشِ ۳، آیتمِ ۲): این پیش‌فرض قبلاً 8774 بود — دقیقاً
# پورتِ miniapp_gateway.PORT. اگر لیدباکس زودتر بالا می‌آمد، bind ِ gateway
# شکست می‌خورد و تونلِ عمومی بی‌صدا به این endpoint می‌رسید نه mini-app.
def t_default_port_never_collides_with_the_miniapp_gateway():
    _tc = str(_HERE.parent / "telegram_center")
    if _tc not in sys.path:
        sys.path.insert(0, _tc)
    _prev = os.environ.pop("OCTOPUS_MINIAPP_PORT", None)
    _prev_lead = os.environ.pop("OCTOPUS_LEAD_INBOX_PORT", None)
    try:
        import miniapp_gateway as mg
        importlib.reload(mg)
        importlib.reload(b)
        assert b.DEFAULT_PORT != mg.PORT, (
            f"lead_boundary_http.DEFAULT_PORT ({b.DEFAULT_PORT}) == "
            f"miniapp_gateway.PORT ({mg.PORT}) — همان تصادمِ ۰۸-۰۳ برگشته")
    finally:
        if _prev is not None:
            os.environ["OCTOPUS_MINIAPP_PORT"] = _prev
        if _prev_lead is not None:
            os.environ["OCTOPUS_LEAD_INBOX_PORT"] = _prev_lead
        importlib.reload(b)


def t_a_valid_signed_accepted():
    _setup_env()
    body = _body(external_id="DA-a")
    code, resp = b.verify_and_dispatch(_headers(body, nonce="na"), body)
    assert code == 202 and resp["ok"], (code, resp)
    assert resp["status"] == "signal_recorded"      # market_signal → digest، نه کارت


def t_b_invalid_signature_rejected():
    _setup_env()
    body = _body(external_id="DA-b")
    code, resp = b.verify_and_dispatch(_headers(body, nonce="nb", sign=False), body)
    assert code == 401 and resp["error"]["code"] == "SIG_INVALID", (code, resp)


def t_c_expired_timestamp_rejected():
    _setup_env()
    body = _body(external_id="DA-c")
    old = int(time.time()) - 10_000
    code, resp = b.verify_and_dispatch(_headers(body, ts=old, nonce="nc"), body)
    assert code == 401 and resp["error"]["code"] == "TS_EXPIRED", (code, resp)


def t_d_replayed_nonce_rejected():
    _setup_env()
    body = _body(external_id="DA-d")
    now = time.time()
    h = _headers(body, nonce="dup-nonce", ts=int(now))
    c1, _ = b.verify_and_dispatch(h, body, now_ts=now)
    c2, r2 = b.verify_and_dispatch(h, body, now_ts=now)   # همان nonce دوباره
    assert c1 == 202, c1
    assert c2 == 409 and r2["error"]["code"] == "NONCE_REPLAY", (c2, r2)


def t_e_unknown_source_rejected():
    _setup_env()
    body = _body(external_id="DA-e")
    code, resp = b.verify_and_dispatch(_headers(body, source="evil_src", nonce="ne"), body)
    assert code == 403 and resp["error"]["code"] == "SRC_UNKNOWN", (code, resp)


def t_f_idempotency_mismatch_and_duplicate():
    _setup_env()
    body = _body(external_id="DA-f")
    # هدرِ idempotency ناسازگار → 422
    code, resp = b.verify_and_dispatch(
        _headers(body, nonce="nf1", idem="wrong:key"), body)
    assert code == 422 and resp["error"]["code"] == "IDEM_MISMATCH", (code, resp)
    # ارسالِ درست دوبار (nonce متفاوت) → دومی duplicate، هیچ لیدِ دوم
    ok_idem = f"{_SRC}:DA-f"
    c1, r1 = b.verify_and_dispatch(_headers(body, nonce="nf2", idem=ok_idem), body)
    c2, r2 = b.verify_and_dispatch(_headers(body, nonce="nf3", idem=ok_idem), body)
    assert c1 == 202 and r1["ok"]
    assert c2 == 202 and r2["status"] == "duplicate", (c2, r2)


def t_g_halt_returns_503_with_receipt():
    _setup_env()
    stop = opslib.STOP_ORGANISM
    stop.parent.mkdir(parents=True, exist_ok=True)
    stop.write_text("stop", "utf-8")
    try:
        body = _body(external_id="DA-g")
        code, resp = b.verify_and_dispatch(_headers(body, nonce="ng"), body)
        assert code == 503 and resp["error"]["code"] == "HALTED", (code, resp)
    finally:
        try:
            stop.unlink()
        except OSError:
            pass


def t_j_nan_timestamp_rejected():
    """رگرسیونِ متخاصم: ts غیرعددی-معتبرِ non-finite (nan/inf) نباید پنجرهٔ ±300s را دور بزند."""
    _setup_env()
    body = _body(external_id="DA-nan")
    now = time.time()
    for bad in ("nan", "NaN", "-nan", "inf", "-inf", "Infinity"):
        code, resp = b.verify_and_dispatch(
            _headers(body, ts=bad, nonce=f"n-{bad}"), body, now_ts=now)
        assert code == 401 and resp["error"]["code"] == "TS_INVALID", (bad, code, resp)


def t_h_negative_n8n_no_gate_imports():
    """اثباتِ ساختاری: مرز هیچ سطحِ گیت/تأیید/ارسال/مغز را import نمی‌کند (تستِ الزامی #10)."""
    src = Path(b.__file__).read_text("utf-8")
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imported.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    forbidden = {"approval_channel", "approval_store", "chrono", "langar_bridge",
                 "model_router", "twilio", "sendgrid", "smtplib", "center",
                 "effector_gate_bridge"}
    leaked = imported & forbidden
    assert not leaked, f"مرز نباید اینها را import کند: {leaked}"


def t_i_live_socket_smoke():
    """یک smokeِ زندهٔ واقعی روی loopback: سرور را بالا بیاور، یک POSTِ امضاشده بزن."""
    import threading
    import urllib.request
    import urllib.error
    from http.server import HTTPServer
    _setup_env()
    srv = HTTPServer(("127.0.0.1", 0), b._make_handler())
    port = srv.server_address[1]
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        body = _body(external_id="DA-live")
        h = _headers(body, nonce="nlive")
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/v1/lead-candidates",
                                     data=body, headers=h, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 202
            out = json.loads(resp.read().decode())
            assert out["ok"] and out["status"] == "signal_recorded", out
        # /health پاسخ می‌دهد
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as hr:
            assert hr.status == 200
    finally:
        srv.shutdown()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_boundary_http: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
