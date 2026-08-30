"""owner_gate.py — گیت مالک برای API تغییردهندهٔ NBB-CP (رأی‌های NBB-V2 + NBB-V4).

دو لایهٔ مستقل، هر دو additive و پیش‌فرض خاموش (byte-parity وقتی خاموش است):

  V4 — امضای Ed25519 مالک (رأی: «باز با گیت امضا»):
      هر درخواست تغییردهنده باید هدرهای X-Owner-Sig / X-Owner-Nonce / X-Owner-Ts
      داشته باشد. امضا روی پیام کنونیکال  f"{ts}|{nonce}|{sha256(body_hex)}"
      با کلید خصوصی مالک زده می‌شود (هرگز در این سرویس نیست) و این‌جا فقط با
      کلید عمومی (env NBB_CP_OWNER_PUBKEY = مسیر فایل یا base64) تأیید می‌شود.
      پنجرهٔ زمانی ۶۰s؛ nonce یک‌بارمصرف (ضدِ بازپخش — درس شورا V4).

  V2 — تپ مالک برای عمل‌های حساس (رأی: «نوشتن با گیت تپ مالک»):
      execute و kill قبل از اجرا به یک «تپ» مالک نیاز دارند:
      X-Owner-Tap = شناسهٔ کارتِ در صف. کارت با request_tap ساخته می‌شود،
      یک‌بارمصرف، مقید به عمل+هدف (الگوی کارت دکتر، ضدِ بازپخش callback_id).

fail-closed وقتی روشن است: هر نبود/کهنگی/نامعتبری = 401. خاموش = no-op.
"""
from __future__ import annotations

import base64
import hashlib
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

TS_WINDOW_S = 60.0

ENV_ENABLED = "NBB_CP_OWNER_GATE"          # "1" = روشن
ENV_PUBKEY = "NBB_CP_OWNER_PUBKEY"         # مسیر فایل یا base64 کلید عمومی


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    reason: str = ""


def _load_public_key(spec: str):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    spec = spec.strip()
    p = Path(spec)
    if p.exists():
        raw = p.read_bytes()
    else:
        raw = base64.b64decode(spec, validate=True)
    key = serialization.load_pem_public_key(raw) if b"PUBLIC KEY" in raw \
        else serialization.load_der_public_key(raw)
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("کلید داده‌شده Ed25519 عمومی نیست")
    return key


def canonical_message(ts: str, nonce: str, body: bytes) -> bytes:
    body_hex = hashlib.sha256(body).hexdigest()
    return f"{ts}|{nonce}|{body_hex}".encode("utf-8")


class OwnerSignatureGate:
    """V4 — تأیید امضای مالک + پنجرهٔ زمانی + nonce یک‌بارمصرف."""

    def __init__(self, enabled: bool, public_key, used_nonces: Optional[set] = None):
        self.enabled = enabled
        self.public_key = public_key
        self._used: set[str] = used_nonces if used_nonces is not None else set()

    @classmethod
    def from_env(cls, env=None) -> "OwnerSignatureGate":
        env = os.environ if env is None else env
        enabled = env.get(ENV_ENABLED, "") == "1"
        if not enabled:
            return cls(enabled=False, public_key=None)
        spec = env.get(ENV_PUBKEY, "").strip()
        if not spec:
            raise RuntimeError(
                f"{ENV_ENABLED}=1 ولی {ENV_PUBKEY} تنظیم نشده — fail-closed، سرویس بالا نمی‌آید"
            )
        return cls(enabled=True, public_key=_load_public_key(spec))

    def check(self, headers: dict, body: bytes, now: Optional[float] = None) -> GateResult:
        if not self.enabled:
            return GateResult(True, "gate-off")

        def deny(reason: str) -> GateResult:
            return GateResult(False, reason)

        sig = (headers.get("x-owner-sig") or "").strip()
        nonce = (headers.get("x-owner-nonce") or "").strip()
        ts = (headers.get("x-owner-ts") or "").strip()
        if not (sig and nonce and ts):
            return deny("missing owner headers (sig/nonce/ts)")
        try:
            ts_val = float(ts)
        except ValueError:
            return deny("bad ts")
        now = time.time() if now is None else now
        if abs(now - ts_val) > TS_WINDOW_S:
            return deny("ts outside window")
        if nonce in self._used:
            return deny("nonce replay")
        try:
            sig_bytes = base64.b64decode(sig, validate=True)
            self.public_key.verify(sig_bytes, canonical_message(ts, nonce, body))
        except Exception:
            return deny("invalid signature")
        self._used.add(nonce)
        return GateResult(True, "ok")


@dataclass
class TapCard:
    tap_id: str
    action: str            # فقط از فهرست سفید
    target: str
    owner: Optional[str] = None
    consumed: bool = False

TAP_ACTIONS = frozenset({"execute", "kill", "resume"})


class OwnerTapGate:
    """V2 — کارت تپ مالک برای عمل‌های حساس؛ یک‌بارمصرف، مقید به عمل+هدف."""

    def __init__(self) -> None:
        self._cards: dict[str, TapCard] = {}

    def request_tap(self, action: str, target: str = "") -> TapCard:
        if action not in TAP_ACTIONS:
            raise ValueError(f"عملِ تپ‌پذیر نیست: {action!r} (فهرست: {sorted(TAP_ACTIONS)})")
        card = TapCard(tap_id=f"tap-{uuid.uuid4().hex[:10]}", action=action, target=str(target))
        self._cards[card.tap_id] = card
        return card

    def tap(self, tap_id: str, owner: str, action: str, target: str) -> GateResult:
        card = self._cards.get(tap_id)
        if card is None:
            return GateResult(False, "unknown tap id")
        if card.consumed:
            return GateResult(False, "tap replay")
        if card.action != action or card.target != str(target):
            return GateResult(False, "tap bound to different action/target")
        card.consumed = True
        card.owner = owner
        return GateResult(True, "tapped")

    def check(self, headers: dict, action: str, target: str) -> GateResult:
        """مسیر HTTP: هدر X-Owner-Tap + X-Owner (نام مالک)."""
        if not self._cards:
            return GateResult(False, "no tap requested")
        tap_id = (headers.get("x-owner-tap") or "").strip()
        owner = (headers.get("x-owner") or "").strip()
        if not (tap_id and owner):
            return GateResult(False, "missing tap headers (X-Owner-Tap / X-Owner)")
        return self.tap(tap_id, owner, action, target)
