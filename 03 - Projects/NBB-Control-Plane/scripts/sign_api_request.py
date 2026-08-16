"""sign_api_request.py — ابزار امضای درخواست‌های API برای مالک (فقط روی ماشین مالک).

رأی NBB-V4: API باز با گیت امضای Ed25519. این ابزار بدنهٔ درخواست را می‌گیرد و
سه هدرِ لازم (X-Owner-Sig / X-Owner-Nonce / X-Owner-Ts) را چاپ می‌کند. کلید
خصوصی فقط همین‌جا خوانده می‌شود — هرگز در سرویس.

استفاده (روی ماشین مالک):
    python scripts/sign_api_request.py --key ~/.octopus-signing/ed25519.pem \
        --body '{"action":"execute"}' --nonce "$(uuidgen)" --ts "$(date +%s)"

سرویس با کلید عمومی همان جفت‌کلید تأیید می‌کند (env: NBB_CP_OWNER_PUBKEY).
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import sys
import time
import uuid
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def load_private_key(path: str) -> Ed25519PrivateKey:
    raw = Path(path).expanduser().read_bytes()
    key = serialization.load_pem_private_key(raw, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise SystemExit("کلید داده‌شده Ed25519 خصوصی نیست")
    return key


def main() -> int:
    ap = argparse.ArgumentParser(description="امضای درخواست API مالک (V4)")
    ap.add_argument("--key", required=True, help="مسیر کلید خصوصی Ed25519 (PEM)")
    ap.add_argument("--body", required=True, help="بدنهٔ خام درخواست (رشته)")
    ap.add_argument("--nonce", default=None, help="پیش‌فرض: uuid تازه")
    ap.add_argument("--ts", type=float, default=None, help="پیش‌فرض: اکنون (ثانیه)")
    a = ap.parse_args()

    key = load_private_key(a.key)
    nonce = a.nonce or uuid.uuid4().hex
    ts = f"{a.ts if a.ts is not None else time.time():.0f}"
    body = a.body.encode("utf-8")
    msg = f"{ts}|{nonce}|{hashlib.sha256(body).hexdigest()}".encode("utf-8")
    sig = base64.b64encode(key.sign(msg)).decode("ascii")

    print(f"X-Owner-Ts: {ts}")
    print(f"X-Owner-Nonce: {nonce}")
    print(f"X-Owner-Sig: {sig}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
