"""test_owner_gate.py — پذیرش V2/V4 (گیت مالک: امضا + تپ).

از طراحی `06-EVIDENCE/DESIGNS-NBB-CP-2026-08-16.md` §V2/§V4:
  خاموش = پاریتی بایت‌به‌بایت (بدون هدر کار می‌کند) · روشن = fail-closed:
  نبود هدر رد · بازپخش nonce رد · کهنگی ts رد · بدنهٔ دستکاری‌شده رد ·
  تپ: یک‌بارمصرف + مقید به عمل/هدف.
"""
from __future__ import annotations

import base64
import hashlib
import time

import pytest

from nbb_cp.api.owner_gate import (
    OwnerSignatureGate, OwnerTapGate, canonical_message,
)


@pytest.fixture()
def keypair(tmp_path):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    pub_pem = serialization.load_pem_public_key(
        priv.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return priv, pub_pem, tmp_path


def _signed_headers(priv, body: bytes, nonce="n1", ts=None):
    ts = f"{ts if ts is not None else time.time():.0f}"
    sig = base64.b64encode(priv.sign(canonical_message(ts, nonce, body))).decode()
    return {"x-owner-sig": sig, "x-owner-nonce": nonce, "x-owner-ts": ts}, ts


# ── V4: امضا ─────────────────────────────────────────────────────────────

def test_gate_off_is_passthrough(keypair):
    _, pub, _ = keypair
    gate = OwnerSignatureGate(enabled=False, public_key=None)
    r = gate.check({}, b"{}")
    assert r.allowed and r.reason == "gate-off"


def test_enabled_missing_headers_denied(keypair):
    _, pub, _ = keypair
    gate = OwnerSignatureGate(enabled=True, public_key=pub)
    assert not gate.check({}, b"{}").allowed


def test_valid_signature_passes_and_nonce_consumed(keypair):
    priv, pub, _ = keypair
    gate = OwnerSignatureGate(enabled=True, public_key=pub)
    h, _ = _signed_headers(priv, b'{"a":1}', nonce="n1")
    assert gate.check(h, b'{"a":1}').allowed
    # بازپخش همان nonce = رد
    assert not gate.check(h, b'{"a":1}').allowed


def test_tampered_body_denied(keypair):
    priv, pub, _ = keypair
    gate = OwnerSignatureGate(enabled=True, public_key=pub)
    h, _ = _signed_headers(priv, b'{"a":1}')
    assert not gate.check(h, b'{"a":2}').allowed, "امضا باید به بدنه مقید باشد"


def test_expired_ts_denied(keypair):
    priv, pub, _ = keypair
    gate = OwnerSignatureGate(enabled=True, public_key=pub)
    h, _ = _signed_headers(priv, b"{}", ts=time.time() - 120)
    assert "window" in gate.check(h, b"{}").reason


def test_bad_signature_denied(keypair):
    priv, pub, _ = keypair
    gate = OwnerSignatureGate(enabled=True, public_key=pub)
    h, _ = _signed_headers(priv, b"{}")
    h = {**h, "x-owner-sig": base64.b64encode(b"\x00" * 64).decode()}
    assert not gate.check(h, b"{}").allowed


# ── V2: تپ ────────────────────────────────────────────────────────────────

def test_tap_lifecycle_single_use_and_binding():
    g = OwnerTapGate()
    card = g.request_tap("execute", "prop-1")
    ok = g.tap(card.tap_id, "owner", "execute", "prop-1")
    assert ok.allowed
    # بازپخش همان کارت = رد
    again = g.tap(card.tap_id, "owner", "execute", "prop-1")
    assert not again.allowed and "replay" in again.reason
    # کارت مقید: عمل/هدف دیگر = رد
    c2 = g.request_tap("execute", "prop-2")
    wrong = g.tap(c2.tap_id, "owner", "kill", "prop-2")
    assert not wrong.allowed


def test_tap_action_whitelist():
    g = OwnerTapGate()
    try:
        g.request_tap("grant_money", "x")
        raised = False
    except ValueError:
        raised = True
    assert raised, "فقط execute/kill/resume تپ‌پذیرند"


def test_tap_via_headers():
    g = OwnerTapGate()
    card = g.request_tap("kill", "")
    h = {"x-owner-tap": card.tap_id, "x-owner": "owner"}
    assert g.check(h, "kill", "").allowed
    assert not g.check(h, "kill", "").allowed  # مصرف‌شده


# ── سطح HTTP (fastapi موجود است در محیط تستِ api) ─────────────────────────

def test_http_gate_off_parity():
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from nbb_cp.api.http import create_app
    from nbb_cp.app.service import ControlPlaneService  # noqa: F401 — استاب اگر لازم شد

    # بدون env گیت → همه‌چیز مثل قبل (پاریتی)
    import os
    for k in ("NBB_CP_OWNER_GATE", "NBB_CP_OWNER_PUBKEY"):
        os.environ.pop(k, None)
    # سرویس حداقلی از bootstrap واقعی
    from nbb_cp.app.bootstrap import build_service
    from nbb_cp.app.config import AppConfig
    svc = build_service(AppConfig(), in_memory=True)
    client = TestClient(create_app(svc))
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"
    r2 = client.post("/kill")  # بدون هیچ هدری — باید مثل قبل کار کند (گیت خاموش)
    assert r2.status_code == 200 and r2.json()["recorded"] is True
    client.post("/resume")
