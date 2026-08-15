"""PEP سایه (DA-4-P1، مگاپرامپت فاز۰-۱ گام ۲-۵) — طراحی + تست، نه اجرا.

قراردادِ اجارهٔ تک‌مصرفِ متصل به عمل: hashِ پارامترهای دقیق + انقضا + nonce
یک‌بارمصرف + kill توزیع‌شده (لیست ابطال محلی). همهٔ حالت‌های منفی ردِ سخت‌اند.
"""
from __future__ import annotations

import hashlib
import time
import uuid


def _h(action: str, params_sha: str) -> str:
    return hashlib.sha256(f"{action}::{params_sha}".encode()).hexdigest()[:24]


class LeaseToken:
    __slots__ = ("lease_id", "action", "params_sha", "action_hash", "nonce",
                 "expires_at", "consumed")

    def __init__(self, action: str, params_sha: str, ttl_s: float = 30.0):
        self.lease_id = f"lease-{uuid.uuid4().hex[:8]}"
        self.action = action
        self.params_sha = params_sha
        self.action_hash = _h(action, params_sha)
        self.nonce = uuid.uuid4().hex
        self.expires_at = time.monotonic() + ttl_s
        self.consumed = False


class PepEndpoint:
    """نقطهٔ اجرای سایه — consume فقط یک‌بار، فقط تا انقضا، فقط برای همان عمل."""

    def __init__(self):
        self._revoked: set[str] = set()     # kill توزیع‌شده: لیستِ ابطالِ محلی
        self.log: list[dict] = []

    def revoke(self, lease_id: str) -> None:
        self._revoked.add(lease_id)

    def consume(self, token: LeaseToken, action: str, params_sha: str) -> tuple[bool, str]:
        if token.lease_id in self._revoked:
            self.log.append({"lease": token.lease_id, "verdict": "revoked"})
            return False, "ردِ محلی: lease ابطال‌شده (distributed kill)"
        if token.consumed:
            self.log.append({"lease": token.lease_id, "verdict": "replay"})
            return False, "ردِ محلی: replay — lease یک‌بارمصرف است"
        if time.monotonic() > token.expires_at:
            self.log.append({"lease": token.lease_id, "verdict": "expired"})
            return False, "ردِ محلی: lease منقضی"
        if _h(action, params_sha) != token.action_hash:
            self.log.append({"lease": token.lease_id, "verdict": "hash-mismatch"})
            return False, "ردِ محلی: hash عمل/پارامتر با lease نمی‌خواند"
        token.consumed = True
        self.log.append({"lease": token.lease_id, "verdict": "shadow-consumed"})
        # سایه: اثر واقعی اجرا نمی‌شود — فقط ثبت
        return True, "مصرفِ سایه‌ای (بدون اثر بیرونی)"
