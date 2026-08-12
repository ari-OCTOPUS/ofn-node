"""receipt_store.py — ذخیرهٔ append-only و tamper-evident برای EvidenceReceipt (ADR-039 C2).

هر receipt با `prev_hash` به receiptِ قبلی زنجیر می‌خورد (هم‌الگوی emit.py).
امضای segment (HMAC) در پایانِ هر بخش با کلیدی بیرون از process زده می‌شود
(placeholder متقارن؛ امضای نامتقارنِ واقعی = کلیدِ مالک، C7).

سخت‌مرزها:
  - path confinement: نوشتن فقط زیر `_ops/epistemics/` یا `outputs/epistemics/` (§7.3 / §11 #10).
  - append یک‌طرفه: receipt.parent_receipt_hash باید با tipِ زنجیره برابر باشد (§11 #9).
"""
from __future__ import annotations

import hashlib
import hmac
from pathlib import Path
from typing import List, Optional

from .canonical import (
    ChainVerification,
    append_chained,
    canonical_json,
    last_chain_hash,
    verify_hash_chain,
)
from .schemas import EvidenceReceipt, GateDecision

DEFAULT_STORE = Path("_ops/epistemics/receipt_store.jsonl")
# محدودسازی مسیر (ADR-039 §7.3 / §11 #10): نوشتن فقط زیرِ این ریشه‌ها.
_ALLOWED_ROOTS = (Path("_ops/epistemics"), Path("outputs/epistemics"))


def _check_confined(path: Path) -> None:
    p = Path(path).resolve()
    for root in _ALLOWED_ROOTS:
        try:
            p.relative_to(root.resolve())
            return
        except ValueError:
            continue
    raise RuntimeError(
        f"receipt_store path {path} outside allowed roots "
        f"{[str(r) for r in _ALLOWED_ROOTS]} (ADR-039 §7.3 / §11 #10)"
    )


class ReceiptStore:
    """ذخیرهٔ append-only برای receiptها با زنجیرهٔ hash (tamper-evident)."""

    def __init__(self, path=DEFAULT_STORE, *, confine: bool = True):
        self.path = Path(path)
        if confine:
            _check_confined(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def tip(self) -> str:
        """hashِ آخرین receipt در زنجیره (GENESIS اگر خالی)."""
        return last_chain_hash(self.path)

    def append(self, receipt: EvidenceReceipt,
               decision: Optional[GateDecision] = None) -> dict:
        """یک receipt را به انتهای زنجیره بچسبان.

        `receipt.parent_receipt_hash` باید با tipِ فعلی برابر باشد (وگرنه
        chain_break، §11 #9). تصمیمِ گیت (اختیاری) در کنارِ receipt ذخیره می‌شود.
        """
        tip = self.tip()
        if receipt.parent_receipt_hash != tip:
            raise ValueError(
                f"chain_break: receipt.parent_receipt_hash={receipt.parent_receipt_hash} "
                f"!= tip={tip}"
            )
        body = receipt.model_dump(mode="json")
        if decision is not None:
            body["decision"] = decision.model_dump(mode="json")
        return append_chained(self.path, body)

    def verify(self) -> ChainVerification:
        """زنجیرهٔ receipt را بازبینی کن (replay tamper-evidence، §11 #9/#12)."""
        return verify_hash_chain(self.path)


# ---------------------------------------------------------------------------
# امضای segment — پایانِ هر بخش با کلیدی بیرون از process
# ---------------------------------------------------------------------------
def sign_segment(records: List[dict], key: bytes) -> str:
    """امضای HMAC-SHA256 روی یک segment از رکوردها.

    placeholder متقارن: تولیدِ کلید و ذخیرهٔ public key در TCB از عهدهٔ مالک
    برمی‌آید (C7: گزارشِ امضاشده با کلیدِ نامتقارن). تا آن زمان، HMAC یک
    تضمینِ tamper-evidenceٔ قابلِ بازتولید است.
    """
    blob = canonical_json({"records": records}).encode("utf-8")
    return hmac.new(key, blob, hashlib.sha256).hexdigest()


def verify_segment(records: List[dict], key: bytes, signature_hex: str) -> bool:
    """تأییدِ امضای segment با مقایسهٔ ثابت‌زمان (side-channel-safe)."""
    return hmac.compare_digest(sign_segment(records, key), signature_hex)
