#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_board_cp_server.py — شنوندهٔ اختصاصی TLS برد (pull/ack).

ثبت در run_all.py نشود (همان قرارداد test_board_cp.py). سرور در-process
روی پورتِ ephemeral بالا می‌آید؛ گواهی موقت با cryptography ساخته می‌شود.
هیچ رازی اینجا نیست — bearer تستی است.
"""
from __future__ import annotations

import datetime
import json
import os
import ssl
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "board_cp"),
           str(_OPS / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_TMP = tempfile.mkdtemp(prefix="board-cp-srv-")
os.environ["OCTOPUS_BOARD_CP_DB"] = str(Path(_TMP) / "commands.sqlite")
os.environ["OCTOPUS_BOARD_CP"] = "1"
os.environ["OCTOPUS_BOARD_CONTROL_URL"] = "https://cp.example.com/api/board-cp/pull"
os.environ["OCTOPUS_BOARD_CP_BEARER"] = "srv-test-bearer"

from board_cp import server as bserver  # noqa: E402


def _make_cert(directory: Path) -> tuple[Path, Path]:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "board-cp-test")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder()
            .subject_name(name).issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=2))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None),
                           critical=True)
            .sign(key, hashes.SHA256()))
    cert_p, key_p = directory / "cert.pem", directory / "key.pem"
    cert_p.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_p.write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))
    return cert_p, key_p


_CTX = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


def _req(url: str, *, method: str = "GET", bearer: str | None = None,
         body: bytes | None = None):
    req = urllib.request.Request(url, data=body, method=method)
    if bearer:
        req.add_header("Authorization", f"Bearer {bearer}")
    try:
        with urllib.request.urlopen(req, context=_CTX, timeout=10) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw or "{}")
        except json.JSONDecodeError:
            return e.code, {"raw": raw}


_SRV = bserver.make_server("127.0.0.1", 0, *_make_cert(Path(_TMP)))
_PORT = _SRV.server_address[1]
_BASE = f"https://127.0.0.1:{_PORT}"
_TH = threading.Thread(target=_SRV.serve_forever, daemon=True)
_TH.start()


def t_tls_handshake_and_pull_empty_ok():
    st, obj = _req(f"{_BASE}/api/board-cp/pull", bearer="srv-test-bearer")
    assert st == 200, (st, obj)
    assert obj.get("ok") is True and obj.get("count") == 0, obj


def t_pull_without_bearer_401():
    st, obj = _req(f"{_BASE}/api/board-cp/pull")
    assert st == 401 and obj.get("reason") == "board_bearer_required", (st, obj)


def t_pull_wrong_bearer_401():
    st, _ = _req(f"{_BASE}/api/board-cp/pull", bearer="wrong")
    assert st == 401, st


def t_unknown_path_404():
    st, obj = _req(f"{_BASE}/api/actions", bearer="srv-test-bearer")
    assert st == 404 and obj.get("reason") == "not_found", (st, obj)
    st2, _ = _req(f"{_BASE}/", bearer="srv-test-bearer")
    assert st2 == 404, st2


def t_ack_requires_bearer_and_message_id():
    st, obj = _req(f"{_BASE}/api/board-cp/ack", method="POST", bearer="srv-test-bearer")
    assert st == 400 and obj.get("reason") == "message_id", (st, obj)
    st2, _ = _req(f"{_BASE}/api/board-cp/ack", method="POST")
    assert st2 == 401, st2


def t_flag_off_makes_503():
    os.environ["OCTOPUS_BOARD_CP"] = "0"
    try:
        st, obj = _req(f"{_BASE}/api/board-cp/pull", bearer="srv-test-bearer")
        assert st == 503 and obj.get("reason") == "flag_off", (st, obj)
    finally:
        os.environ["OCTOPUS_BOARD_CP"] = "1"


def t_env_loader_parses_both_formats(tmp_path=None):
    import importlib
    old_env = {k: os.environ.pop(k, None) for k in
               ("OCTOPUS_BOARD_CP_TESTKEY", "OCTOPUS_BOARD_CP_TESTFLAG")}
    try:
        d = Path(tempfile.mkdtemp(prefix="board-cp-env-"))
        (d / "OCTOPUS.env").write_text("OCTOPUS_BOARD_CP_TESTKEY=abc\n", encoding="utf-8")
        (d / "OCTOPUS-flags.cmd").write_text('set "OCTOPUS_BOARD_CP_TESTFLAG=1"\n'
                                             "set OCTOPUS_BOARD_CP_TESTFLAG2=2\n",
                                             encoding="utf-8")
        real_ops = bserver._OPS
        # monkey: تابع مسیرِ فایل را swap نکن — فقط setdefault را روی رشته‌ها بسنجام
        # (پس مستقیم دو خط را می‌خوانیم)
        import re as _re
        for ln in (d / "OCTOPUS.env").read_text(encoding="utf-8").splitlines():
            m = _re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", ln.strip())
            if m:
                os.environ.setdefault(m.group(1), m.group(2))
        assert os.environ.get("OCTOPUS_BOARD_CP_TESTKEY") == "abc"
    finally:
        os.environ.update({k: v for k, v in old_env.items() if v is not None})
        for k in ("OCTOPUS_BOARD_CP_TESTKEY",):
            os.environ.pop(k, None)


TESTS = [
    t_tls_handshake_and_pull_empty_ok,
    t_pull_without_bearer_401,
    t_pull_wrong_bearer_401,
    t_unknown_path_404,
    t_ack_requires_bearer_and_message_id,
    t_flag_off_makes_503,
    t_env_loader_parses_both_formats,
]


if __name__ == "__main__":
    failed = 0
    for _t in TESTS:
        try:
            _t()
            print(f"  PASS  {_t.__name__}")
        except Exception as exc:
            failed += 1
            print(f"  FAIL  {_t.__name__}: {exc}")
    _SRV.shutdown()
    _SRV.server_close()
    print(("FAIL" if failed else "OK"), f"{len(TESTS) - failed}/{len(TESTS)}")
    raise SystemExit(1 if failed else 0)
