#!/usr/bin/env python3
"""ziman_phase2.py — Phase 2 · Product/Inventory validators (pure, offline, additive).

قرارداد:
  * هیچ I/O اجباری، هیچ شبکه، هیچ spend — فقط توابع خالص برای validate.
  * fail-closed: دادهٔ نامعلوم → رد یا None، هرگز حدس.
  * invariantها:
      - ATP = max(on_hand - reserved, 0) فقط وقتی on_hand اندازه‌گیری‌شده و measured_at دارد.
      - C4 → policy فقط local_only|pickup.
      - public_price فقط با price_status=owner_approved.
      - product_id باید الگوی ZM-C{1..4}-NNNN باشد.
      - 50 محصول فیزیکی ≠ 50 SKU ≠ ظرفیت هفتگی (گارد ضدتفسیر).
rollback: حذف همین فایل + تستش — هیچ ماژول دیگری به آن وابسته نیست.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

FAMILIES = ("C1", "C2", "C3", "C4")
_ID_RE = re.compile(r"^ZM-C[1-4]-\d{4}$")
_C4_POLICIES = ("local_only", "pickup")
_FRESH_DAYS = 30  # CF-07: پنجرهٔ تازگیِ اندازه‌گیریِ موجودی


def valid_product_id(pid: str) -> bool:
    return bool(_ID_RE.match(pid or ""))


def _parse_iso8601(ts):
    """ISO8601 → datetime آگاه (UTC). None اگر رشته نبود یا غیرقابل‌parse. naive = UTC فرض."""
    if not isinstance(ts, str):
        return None
    s = ts.strip()
    if not s:
        return None
    if s.endswith(("Z", "z")):
        s = s[:-1] + "+00:00"
    dt = None
    for cand in (s, s + "T00:00:00"):
        try:
            dt = datetime.fromisoformat(cand)
            break
        except ValueError:
            dt = None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def compute_atp(quantity_on_hand, quantity_reserved=0, measured_at=None,
                max_age_days=_FRESH_DAYS, _now=None):
    """ATP فقط با کمیتِ اندازه‌گیری‌شده و *تازه*. وگرنه None (fail-closed).

    CF-07: measured_at حالا واقعاً parse می‌شود — timestampِ آینده، کهنه‌تر از
    max_age_days، یا غیرقابل‌parse همگی None برمی‌گردانند (قبلاً هر رشتهٔ truthy
    یک ATP واقعی می‌داد — fail-open). `_now` برای تستِ قطعی تزریق می‌شود.
    """
    if quantity_on_hand is None or not measured_at:
        return None
    dt = _parse_iso8601(measured_at)
    if dt is None:
        return None
    now = _now if _now is not None else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if dt > now:                                    # اندازه‌گیریِ آینده = نامعتبر
        return None
    if now - dt > timedelta(days=max_age_days):     # کهنه‌تر از پنجره = نامعتبر
        return None
    try:
        on_hand = int(quantity_on_hand)
        reserved = int(quantity_reserved or 0)
    except (TypeError, ValueError):
        return None
    if on_hand < 0 or reserved < 0:
        return None
    return max(on_hand - reserved, 0)


def validate_product_card(card: dict) -> list[str]:
    """لیست خطاها — خالی = معتبر. هرگز exception به بیرون."""
    errors: list[str] = []
    if not isinstance(card, dict):
        return ["card is not a dict"]
    pid = card.get("product_id", "")
    fam = card.get("family_id", "")
    if not valid_product_id(pid):
        errors.append(f"invalid product_id: {pid!r}")
    if fam not in FAMILIES:
        errors.append(f"invalid family_id: {fam!r}")
    if valid_product_id(pid) and fam in FAMILIES and f"-{fam}-" not in pid:
        errors.append(f"product_id family mismatch: {pid} vs {fam}")
    # C4 invariants
    cls = card.get("classification") or {}
    ful = card.get("fulfilment") or {}
    if fam == "C4":
        if cls.get("perishable") is not True:
            errors.append("C4 must be perishable=true")
        if ful.get("policy") not in _C4_POLICIES:
            errors.append(f"C4 policy must be local_only|pickup, got {ful.get('policy')!r}")
    # price gate
    com = card.get("commercial") or {}
    if com.get("public_price_aud") is not None and com.get("price_status") != "owner_approved":
        errors.append("public_price without owner_approved price_status")
    # delivery promise never for agents
    if ful.get("delivery_promise_authority"):
        errors.append("delivery_promise_authority must be false")
    # inventory sanity
    inv = card.get("inventory") or {}
    for k in ("quantity_on_hand", "quantity_reserved"):
        v = inv.get(k)
        if v is not None and (not isinstance(v, int) or v < 0):
            errors.append(f"{k} must be non-negative int or null")
    atp = inv.get("available_to_promise")
    if atp is not None:
        expected = compute_atp(inv.get("quantity_on_hand"),
                               inv.get("quantity_reserved", 0),
                               inv.get("measured_at"))
        if expected is None:
            errors.append("ATP set but on_hand unmeasured/stale (fail-closed)")
        elif atp != expected:
            errors.append(f"ATP mismatch: {atp} != {expected}")
    return errors


def anti_misread_guard(claim: str) -> dict:
    """گارد ضدتفسیر: ادعاهای «۵۰ = SKU/ظرفیت» را بلاک می‌کند."""
    text = (claim or "").lower()
    blocked = []
    if re.search(r"50\s*(unique\s*)?sku", text):
        blocked.append("50-products-as-SKUs")
    if re.search(r"50\s*(per|/)\s*week|capacity\s*(of|=)?\s*50", text):
        blocked.append("50-products-as-capacity")
    if re.search(r"30\s*(per|/)\s*week.*(verified|measured|confirmed)", text):
        blocked.append("30/week-claimed-verified (CF-01 open)")
    return {"allowed": not blocked, "blocked_patterns": blocked}


def capacity_fail_closed(ceiling, owner_revalidated: bool = False):
    """تا revalidation مالک، سقف مؤثر پیشنهادی = min(ceiling, 6) — نرخ مشاهده‌شده."""
    if ceiling is None or not isinstance(ceiling, (int, float)) or ceiling <= 0:
        return 0
    if not owner_revalidated:
        return min(int(ceiling), 6)
    return int(ceiling)
