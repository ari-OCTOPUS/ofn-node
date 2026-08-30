# -*- coding: utf-8 -*-
"""T41 (دستور مالک #۷): تشخیص تغییر PEM مخزن نسبت به TRUST-ANCHOR.

دو حالت: PEM فعلی باید با لنگر بخواند؛ PEM دست‌کاری‌شده (کلید تازه) باید
ANCHOR_MISMATCH بدهد — یعنی سیستم fail-closed است، نه فقط سبز-خوان."""
from pathlib import Path
import subprocess
import sys

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS / "owner-signing"))

from check_anchor import anchor_fingerprint, pem_fingerprint, check  # noqa: E402

SIGNING = _OPS / "owner-signing"
PEM = SIGNING / "octopus-owner-ed25519-public.pem"


def test_anchor_file_pins_expected_fingerprint():
    assert anchor_fingerprint() == \
        "2413e9746f13afc900b31ad4d966a6783d73662f661fa0d6dc578e9b244ab6b2"


def test_repo_pem_matches_anchor():
    ok, want, got = check()
    assert ok, f"repo PEM drifted from anchor: {want} != {got}"


def test_tampered_pem_fails_closed(tmp_path):
    # یک کلید Ed25519 تازه بساز — fingerprint متفاوت خواهد بود
    fake = tmp_path / "fake-public.pem"
    key = subprocess.run(
        ["openssl", "genpkey", "-algorithm", "ed25519"],
        check=True, capture_output=True).stdout
    priv = tmp_path / "fake-private.pem"
    priv.write_bytes(key)
    subprocess.run(
        ["openssl", "pkey", "-in", str(priv), "-pubout", "-out", str(fake)],
        check=True, capture_output=True)
    ok, _, _ = check(fake)
    assert not ok
    # و انگشت‌نگارتی جعلی با لنگر فرق دارد:
    assert pem_fingerprint(fake) != anchor_fingerprint()
