"""test_no_external_send_while_waiver_active — the waiver as code (D-33 §D).

The signed waiver SECRET-ROTATION-WAIVER-20260831 keeps secret rotation
deferred ONLY while "external messaging" and "live-provider execution"
stay in `not_authorized`. A hash reference inside a vault markdown is a
CLAIM; this file is the MECHANISM:

  1. the waiver fixture is pinned by sha256 (any edit = loud failure);
  2. while the waiver is active, the external-send gates must be
     fail-closed BY DEFAULT (env absent, no managed_flags.json);
  3. the REAL host state is then read with no isolation: if any send
     path is armed on the machine running this test while the waiver
     blocks external messaging, the test fails LOUDLY. That red is the
     design — it is the owner's queue, not something to silence by
     editing this test. Resolution belongs to the owner (Q-05 chain).

Signature (.sig) stays in the vault:
F:\\backup\\docs\\octopus-surgery\\receipts\\SECRET-ROTATION-WAIVER-20260831.json.sig
Zero network in this file. No secret values are read, echoed, or needed.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
_AGENTS = _REPO / "ofn" / "agents"
for _p in (str(_AGENTS), str(_AGENTS.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import lead_outbound_transport as _lot   # noqa: E402
import mail_credentials                  # noqa: E402
import outbound_worker                   # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "waiver" / "SECRET-ROTATION-WAIVER-20260831.json"
# Git blob is LF. The Windows vault copy (F:\backup\docs\octopus-surgery\receipts\)
# is the CRLF twin of the same JSON. Both hashes recorded; pin is git-canonical LF
# after \r\n → \n so ubuntu-latest and Windows autocrlf checkouts agree.
# This is NOT a waiver re-sign and does not authorize send.
PINNED_SHA256 = "a21b19a99a93f3b0799eed54ef97bf6de09a69928e2b5c3bf0bfd1cbfbe8fc15"
PINNED_SHA256_CRLF_VAULT = (
    "40578fef4e192ea869ff0d22ab797f483461847b370877637ead64850d6f980f"
)


def _canonical_waiver_bytes(raw: bytes) -> bytes:
    """LF-canonical bytes. A CRLF checkout must not fail the pin."""
    return raw.replace(b"\r\n", b"\n")

SEND_FLAGS = (
    outbound_worker.FLAG,        # OCTOPUS_WIRE_LEAD_OUTBOUND
    _lot.WAL_FLAG,               # OCTOPUS_WIRE_LEAD_OUTBOUND_WAL
    _lot.VALUE_FLAG,             # OCTOPUS_WIRE_VALUE_LEDGER
    mail_credentials.GMAIL_FALLBACK_FLAG,  # OCTOPUS_SMTP_USE_GMAIL
)


def _waiver() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _not_authorized(waiver: dict) -> set:
    return {str(s).strip().lower() for s in waiver.get("not_authorized", [])}


def test_waiver_fixture_matches_pinned_hash():
    raw = FIXTURE.read_bytes()
    digest = hashlib.sha256(_canonical_waiver_bytes(raw)).hexdigest()
    assert digest == PINNED_SHA256, (
        "waiver fixture changed vs pinned git-canonical LF hash — if the owner "
        "re-signed the waiver, update PINNED_SHA256 in the same commit and say why"
    )


def test_waiver_lf_and_crlf_pins_are_both_recorded():
    """Contradiction recorded, not silently picked: LF git blob vs CRLF vault."""
    assert PINNED_SHA256 != PINNED_SHA256_CRLF_VAULT
    lf = _canonical_waiver_bytes(FIXTURE.read_bytes())
    assert hashlib.sha256(lf).hexdigest() == PINNED_SHA256
    crlf_twin = lf.replace(b"\n", b"\r\n")
    assert hashlib.sha256(crlf_twin).hexdigest() == PINNED_SHA256_CRLF_VAULT
    assert crlf_twin != lf


def test_waiver_crlf_checkout_still_matches_lf_pin():
    """ubuntu-latest CI hashed LF; Windows vault hashed CRLF. Same JSON."""
    lf = _canonical_waiver_bytes(FIXTURE.read_bytes())
    crlf_checkout = lf.replace(b"\n", b"\r\n")
    assert hashlib.sha256(crlf_checkout).hexdigest() == PINNED_SHA256_CRLF_VAULT
    assert hashlib.sha256(_canonical_waiver_bytes(crlf_checkout)).hexdigest() == PINNED_SHA256


def test_waiver_pin_rejects_one_byte_mutation():
    lf = _canonical_waiver_bytes(FIXTURE.read_bytes())
    flip = b"Y" if lf[-1:] != b"Y" else b"Z"
    mutated = lf[:-1] + flip
    assert hashlib.sha256(mutated).hexdigest() != PINNED_SHA256
    assert hashlib.sha256(mutated).hexdigest() != PINNED_SHA256_CRLF_VAULT


def test_waiver_keeps_external_messaging_not_authorized():
    w = _waiver()
    assert w.get("status") == "DEFERRED_OWNER_RISK_ACCEPTED"
    na = _not_authorized(w)
    assert "external messaging" in na
    assert "live-provider execution" in na


def test_send_gates_fail_closed_by_default(tmp_path, monkeypatch):
    """Isolated: no env flags, empty runtime dir → every send gate closed."""
    for flag in SEND_FLAGS:
        monkeypatch.delenv(flag, raising=False)
    monkeypatch.setenv("OCTOPUS_AGI2027_RUNTIME_DIR", str(tmp_path / "empty"))

    assert outbound_worker.enabled() is False
    assert _lot._wal_enabled() is False
    assert _lot._managed_flag_enabled(_lot.VALUE_FLAG) is False
    assert mail_credentials.gmail_fallback_enabled() is False


def test_host_send_state_respects_active_waiver():
    """NO isolation — reads the real host. Red here means: this machine has an
    external-send path ARMED while the signed waiver keeps external messaging
    not_authorized (e.g. managed_flags.json or env left armed after a run).
    Escalate to the owner; do not fix by editing this test."""
    w = _waiver()
    if "external messaging" not in _not_authorized(w):
        pytest.skip("waiver no longer blocks external messaging")

    armed = []
    if os.environ.get(outbound_worker.FLAG, "0") == "1":
        armed.append(outbound_worker.FLAG)
    if _lot._managed_flag_enabled(_lot.WAL_FLAG):
        armed.append(_lot.WAL_FLAG)
    if _lot._managed_flag_enabled(_lot.VALUE_FLAG):
        armed.append(_lot.VALUE_FLAG)
    if mail_credentials.gmail_fallback_enabled():
        armed.append(mail_credentials.GMAIL_FALLBACK_FLAG)

    assert not armed, (
        "ACTIVE WAIVER vs ARMED SEND PATHS on this host: "
        f"{armed}. While SECRET-ROTATION-WAIVER-20260831 is in force, "
        "external messaging is not_authorized — disarm or obtain owner GO (Q-05)."
    )
