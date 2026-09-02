"""campaign_envelope — بستهٔ آمادهٔ ارسالِ کمپین (Lane درآمد، مرزِ مجاز).

زنجیرهٔ دستور ادامهٔ مالک: harvest → normalize → dedupe → qualify →
score → quote_drafted → policy_checked → campaign_envelope_ready. موتور کوت
(quote_engine) تا quote_drafted را دارد؛ این ماژول فقط دو حلقهٔ آخر را
می‌بندد.

quote_sent ممنوع و پابرجا: خروجی این ماژول یک artifact ممیزی‌پذیر است،
نه یک ارسال. send_status در این نسخه همیشه «FORBIDDEN_UNTIL_OWNER_GO»
است و هیچ مسیری از این فایل به transport وصل نیست — گشودنِ آن زنجیرهٔ
مالک است (Q-05/چرخش راز)، نه اینجا.

طراحی: وابستگی تزریقی (quote_fn) — تست‌ها fixture می‌دهند و به
PAINTING_DB/CARD واقعی (مسیرهای home) دست نمی‌زنند. صفر شبکه.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable, Dict, Mapping, Optional

# سوختِ مسیر درآمد سمتِ تقاضاست؛ نشانگرهای سمت عرضه (آگهی استخدام)
# گیرندهٔ غلط‌اند — همان wrong_recipient / PAINT-L5-001.
SUPPLY_SIDE_MARKERS = ("lead:seek:", "seek:", "job-ad", "employer:")

DEFAULT_MAX_QUOTES = 10          # هم‌قوارهٔ سقف روزانهٔ ارسال لید
QUOTE_MAX_AUD = 25_000.0         # هم‌قوارهٔ HF-1 موتور کوت


def _is_demand_side(lead_id: str) -> bool:
    lid = str(lead_id or "").lower()
    return not any(m in lid for m in SUPPLY_SIDE_MARKERS)


def _check_policy(draft: Mapping, *, card_approved: bool,
                  seen_leads: set) -> Dict[str, object]:
    """هر کوت شش چک می‌خرد؛ نتیجه با دلیل، نه بولی لاک‌پشت."""
    lead_id = str(draft.get("lead_id") or "")
    priced = bool(draft.get("priced"))
    total = float(draft.get("total_aud") or 0)
    checks: Dict[str, object] = {
        "direction_demand_side": {
            "ok": _is_demand_side(lead_id),
            "reason": "" if _is_demand_side(lead_id)
            else "supply-side lead id — wrong_recipient class (PAINT-L5-001)"},
        "dedupe_one_quote_per_lead": {
            "ok": lead_id not in seen_leads,
            "reason": "" if lead_id not in seen_leads
            else "duplicate lead in this envelope"},
        "rate_card_lock": {
            "ok": (not priced) or card_approved,
            "reason": "" if (not priced) or card_approved
            else "priced quote while rate card not owner-approved (vote Q6)"},
        "total_cap": {
            "ok": (not priced) or total <= QUOTE_MAX_AUD,
            "reason": "" if (not priced) or total <= QUOTE_MAX_AUD
            else f"total {total} over cap {QUOTE_MAX_AUD} (HF-1)"},
        "style_subject_present": {
            "ok": bool(str(draft.get("subject") or "").strip()),
            "reason": "" if str(draft.get("subject") or "").strip()
            else "missing subject — style gate"},
        "no_send_wiring": {   # ساختاری: این ماژول ارسال ندارد
            "ok": True, "reason": ""},
    }
    return checks


def build_campaign_envelope(
    campaign_id: str,
    lead_scopes: Mapping[str, Mapping],
    *,
    quote_fn: Callable[[str, Mapping], Mapping],
    card_approved: bool,
    now_iso: str,
    out_path: Optional[Path] = None,
    max_quotes: int = DEFAULT_MAX_QUOTES,
) -> Dict[str, object]:
    """quote_fn(lead_id, scope) باید draft موتور کوت را برگرداند
    (quote_engine.quote با dry=True). هیچ چیزی فرستاده نمی‌شود."""
    quotes = []
    duplicates = []
    seen: set = set()
    for lead_id, scope in dict(lead_scopes).items():
        if lead_id in seen:
            duplicates.append(lead_id)
            continue
        seen.add(lead_id)
        draft = dict(quote_fn(lead_id, scope) or {})
        if draft.get("error"):
            quotes.append({"lead_id": lead_id, "engine_error": draft["error"],
                           "policy_checked": False})
            continue
        checks = _check_policy(draft, card_approved=card_approved,
                               seen_leads=seen - {lead_id} | {lead_id})
        # dedupe باید نسبت به بقیهٔ leadهای همین envelope سنجیده شود:
        checks["dedupe_one_quote_per_lead"] = {
            "ok": True, "reason": ""}  # تکرارها بالاتر فیلتر شدند
        quotes.append({
            "lead_id": lead_id,
            "qt_number": draft.get("qt_number"),
            "priced": bool(draft.get("priced")),
            "total_aud": draft.get("total_aud"),
            "subject": draft.get("subject"),
            "policy": checks,
            "policy_checked": all(c["ok"] for c in checks.values()),
        })
    cap_ok = len(quotes) <= max_quotes
    envelope: Dict[str, object] = {
        "schema": "octopus.campaign_envelope.v1",
        "campaign_id": campaign_id,
        "built_at": now_iso,
        "card_approved": card_approved,
        "quotes": quotes,
        "counts": {"quotes": len(quotes), "duplicates_filtered": duplicates},
        "cap_ok": cap_ok,
        "policy_checked": bool(quotes) and cap_ok and
        all(q.get("policy_checked") for q in quotes),
        "send_status": "FORBIDDEN_UNTIL_OWNER_GO",
        "quote_sent_forbidden": True,
    }
    if out_path is not None:
        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(envelope, ensure_ascii=False,
                             sort_keys=True).encode("utf-8")
        envelope["sha256"] = hashlib.sha256(payload).hexdigest()
        p.write_text(json.dumps(envelope, ensure_ascii=False, indent=1,
                                sort_keys=True), encoding="utf-8")
    return envelope
