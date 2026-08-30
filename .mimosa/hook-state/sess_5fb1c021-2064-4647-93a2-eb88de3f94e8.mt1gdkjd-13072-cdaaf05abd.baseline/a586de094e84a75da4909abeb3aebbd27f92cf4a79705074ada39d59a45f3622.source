#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_anchor.py — تطبیق fail-closed انگشت‌نگارتی PEM عمومی با TRUST-ANCHOR.

دستور مالک #۷ §۲ (T41): هیچ verify ای پیش از این تطبیق انجام نشود.
CLI:  python _ops/owner-signing/check_anchor.py [path-to-pub.pem]
خروجی: exit 0 + چاپ انگشت‌نگارتی (تطبیق) · exit 5 + ANCHOR_MISMATCH (توقف).
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
ANCHOR_MD = _HERE / "TRUST-ANCHOR.md"
DEFAULT_PEM = _HERE / "octopus-owner-ed25519-public.pem"


def anchor_fingerprint(path: Path = ANCHOR_MD) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^\s*([0-9a-f]{64})\s*$", text, re.M)
    if not m:
        raise SystemExit(f"ANCHOR_MISSING: {path}")
    return m.group(1)


def pem_fingerprint(pem: Path) -> str:
    der = subprocess.run(
        ["openssl", "pkey", "-pubin", "-in", str(pem), "-outform", "DER"],
        check=True, capture_output=True).stdout
    return hashlib.sha256(der).hexdigest()


def check(pem: Path = DEFAULT_PEM, anchor: Path = ANCHOR_MD) -> tuple[bool, str, str]:
    want = anchor_fingerprint(anchor)
    got = pem_fingerprint(pem)
    return got == want, want, got


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PEM
    ok, want, got = check(target)
    print(f"anchor={want}")
    print(f"pem   ={got}")
    if not ok:
        print("ANCHOR_MISMATCH — verify ممنوع (fail-closed)")
        sys.exit(5)
    print("ANCHOR_OK")
