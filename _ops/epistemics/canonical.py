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
from dataclasses import dataclass
from pathlib import Path
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


# ---------------------------------------------------------------------------
# Hash-chain store helpers — append-only JSONL (ADR-039 C2)
#
# الگوی مشترک برای receipt_store و autonomy_provenance: هر رکورد
# `prev_hash` (← hashِ رکوردِ قبلی، GENESIS برای اولین) و `hash`
# (← chain_hash(prev_hash, body)) می‌گیرد. هم‌الگو با epistemics/emit.py.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ChainVerification:
    """نتیجهٔ بازبینیِ زنجیرهٔ hash-chained."""
    ok: bool
    n_records: int
    broken_at: Optional[int]    # ایندکسِ اولین رکوردِ شکسته (None اگر سالم)
    reason: str


def last_chain_hash(path) -> str:
    """آخرین `hash` زنجیره (GENESIS اگر خالی/غایب/خراب)."""
    p = Path(path)
    if not p.exists():
        return GENESIS
    last = None
    with p.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last = line.strip()
    if not last:
        return GENESIS
    try:
        return json.loads(last).get("hash", GENESIS)
    except json.JSONDecodeError:
        return GENESIS


def append_chained(path, body: Mapping[str, Any]) -> dict:
    """یک رکورد را به زنجیرهٔ append-only اضافه کن و رکوردِ کامل را برگردان.

    `hash = chain_hash(prev_hash, body)`؛ `prev_hash` و `hash` به رکورد اضافه
    می‌شوند. body نباید خودش `hash`/`prev_hash` داشته باشد (metadataِ زنجیره است).
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if "hash" in body or "prev_hash" in body:
        raise ValueError("body must not contain hash/prev_hash (chain metadata)")
    parent = last_chain_hash(p)
    h = chain_hash(parent, body)
    record = dict(body)
    record["prev_hash"] = parent
    record["hash"] = h
    with p.open("a", encoding="utf-8") as f:
        f.write(canonical_json(record) + "\n")
    return record


def verify_hash_chain(path) -> ChainVerification:
    """زنجیره را بازبینی کن: هر رکورد باید prev_hash و hashِ درست داشته باشد.

    هر تغییری در محتوای یک رکورد (حتی یک بایت) ⇒ hash_mismatch؛ هر گسست در
    پیوندِ prev_hash ⇒ chain_break. §11 #9 (chain) + #12 (replay).
    """
    p = Path(path)
    if not p.exists():
        return ChainVerification(ok=True, n_records=0, broken_at=None, reason="empty/missing store")
    prev = GENESIS
    idx = 0
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                return ChainVerification(ok=False, n_records=idx, broken_at=idx,
                                         reason=f"unparseable@{idx}")
            ph = rec.get("prev_hash")
            h = rec.get("hash")
            if ph != prev:
                return ChainVerification(ok=False, n_records=idx, broken_at=idx,
                                         reason=f"chain_break@{idx}: prev_hash!=tip")
            body = {k: v for k, v in rec.items() if k not in ("hash", "prev_hash")}
            if chain_hash(prev, body) != h:
                return ChainVerification(ok=False, n_records=idx, broken_at=idx,
                                         reason=f"hash_mismatch@{idx}")
            prev = h
            idx += 1
    return ChainVerification(ok=True, n_records=idx, broken_at=None, reason="ok")
