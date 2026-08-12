"""canonical.py — Canonical JSON serialization + SHA-256 for the epistemics cabin (ADR-039 C1).

تمامِ hashها از رویِ representationِ کانونیکالِ JSON محاسبه می‌شوند:
  sort_keys=True · ensure_ascii=False · separators=(",", ":") · default=str
فیلدهای خودارجاع (hash/parent_receipt_hash/canonical_payload_hash/signature/identifier)
قبل از هش‌کردن حذف می‌شوند تا در content-hash دورِ باطل نسازند.

این ماژول stdlib-only است — هیچ Pydantic. Pydantic فقط در schemas.py مجاز است
(ADR-037 amend: دومین کابینِ Pydanticِ _ops، هم‌الگو با hypothesis_engine/impl/schemas.py).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping, Optional

# ---------------------------------------------------------------------------
# فیلدهای خودارجاع: یا از خودِ محتوا مشتق می‌شوند (hashها) یا metadataٔ امضا /
# identifier هستند. نباید در content-hash باشند، وگرنه هش به خودش وابسته می‌شود.
# ---------------------------------------------------------------------------
SELF_REFERENTIAL_FIELDS = frozenset({
    "hash", "prev_hash",
    "parent_receipt_hash", "canonical_payload_hash",
    "signature_b64", "signature",
    "produced_at", "decided_at",
    "receipt_id", "decision_id",
})

GENESIS = "GENESIS"


def canonical_json(obj: Any, *, exclude: Optional[Iterable[str]] = None) -> str:
    """JSON کانونیکال: sort_keys + separator ثابت + حفظِ UTF-8.

    اگر obj یک mapping باشد و exclude داده شده، کلیدهای exclude پیش از serialization
    حذف می‌شوند ( فقط در سطحِ بالا — کلیدهای تودرتو مثل binds نگه داشته می‌شوند).
    """
    drop = set(exclude) if exclude else set()
    if isinstance(obj, Mapping) and drop:
        clean = {k: v for k, v in obj.items() if k not in drop}
    else:
        clean = obj
    return json.dumps(
        clean,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )


def canonical_hash(obj: Any, *, exclude: Optional[Iterable[str]] = None) -> str:
    """SHA-256(hex کامل، قطع‌نشده) از canonical_json.

    برخلاف `_config_hash`/`environment_hash` در hypothesis_engine که ۱۶ کاراکتر
    truncated هستند، اینجا hex کامل بازمی‌گردد — هم‌الگو با emit.py (زنجیرهٔ tamper-evident).
    """
    return hashlib.sha256(canonical_json(obj, exclude=exclude).encode("utf-8")).hexdigest()


def payload_hash(record: Mapping[str, Any]) -> str:
    """canonical_payload_hash یک receipt/decision.

    content-hash بدونِ فیلدهای خودارجاع. این همان مقداری است که producer در
    `canonical_payload_hash` receipt می‌نویسد و validator آن را باز-محاسبه و مقایسه می‌کند.
    """
    return canonical_hash(record, exclude=SELF_REFERENTIAL_FIELDS)


def chain_hash(parent_hash: str, body: Mapping[str, Any]) -> str:
    """هشِ زنجیره‌ای هم‌الگو با epistemics/emit.py و receipt_store (C2):

        SHA-256(parent_hash + canonical_json(body))

    parent_hash مقدارِ فیلدِ `parent_receipt_hash` receiptِ جدید است (GENESIS برای اولین).
    body خودِ receipt است (بدونِ نیاز به exclude — caller بدنهٔ نهایی را می‌دهد).
    """
    blob = (parent_hash + canonical_json(body)).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def material_hash_of(file_contents: Mapping[str, str]) -> str:
    """material_hash از source-tree واقعیِ آزمون (نه فقط HEAD).

    ورودی: نگاشتِ {relative_path: file_content_as_string}.
    C3 (sandbox runner) فایل‌های source را می‌خواند و این تابعِ pure را صدا می‌زند.
    ترتیب-independent: کلیدها در canonical_json به‌هرحال sort می‌شوند.
    هر فایل به‌صورت جداگانه SHA-256 می‌شود تا manifest فشرده بماند.
    """
    manifest = {
        path: hashlib.sha256(content.encode("utf-8")).hexdigest()
        for path, content in file_contents.items()
    }
    return canonical_hash(manifest)
