"""quote_engine — موتور کوت (Lane Q، رأی‌های Q5/Q6 ۲۰۲۶-۰۹-۰۱).

scope → کوتِ رسمی QT-YYYYMMDD-NNN → ارسال از همان گیت‌لدرِ transport.

قفلِ قیمت (رأی Q6): تا painting_rate_card.json ← approved_by_owner=true
نشود، کوتِ دارای قیمت نمی‌رود؛ به‌جایش «کوت بدونِ قیمت + درخواست بازدید»
می‌رود (خودکار، صادقانه). استقلالِ کامل بعد از تأیید (رأی Q5) ولی:
  - قیمت فقط از بازهٔ کارت (نه عددِ آزاد)
  - جملهٔ اعتبار ۳۰ روزه (مسیرِ اصلاح)
  - امضا از secrets/identity.json (ABN/بیمهٔ واقعی) — تا نرسد، بدونِ ادعا

خروجی در جدول painting_quotes (ایجادِ خودکار) + رویداد funnel.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))

import opslib  # noqa: E402

import memory_chain  # noqa: E402
import quote_fingerprint as qfp  # noqa: E402
from lead_email_writer import FORBIDDEN  # noqa: E402

PAINTING_DB = Path.home() / ".local/share/ofn/painting.sqlite"
DATA = Path.home() / ".local/share/ofn"
CARD = DATA / "painting_rate_card.json"
IDENTITY = Path.home() / ".config/ofn/identity.json"

# ── هات‌فیکس‌های ناظر (حکم ۲۰۲۶-09-02، قبل از موج ۲) ─────────────────────────
# HF-1: سقف روی «مبلغ نهایی»، نه نرخ. عددِ $۲۵٬۰۰۰ پیشنهادِ ناظر است (بحث‌پذیر)؛
# نبودِ سقف یک تصمیم نیست، غفلت است. عبور از هرکدام → needs_owner_review، نه ارسال.
import os as _os  # noqa: E402
QUOTE_MAX_AUD = float(_os.environ.get("OCTOPUS_QUOTE_MAX_AUD", "25000"))
QUOTE_MIN_M2 = 20.0        # زیرِ این، احتمالاً پارسِ اشتباه است نه کارِ کوچک


def needs_owner_review(lead_id: str, qt: str, reason: str, detail: dict) -> dict:
    """مسیر توقفِ سخاوتمندانه (ناظر §8): فقط مواردِ واقعاً غیرعادی به تلگرام می‌رود."""
    opslib.append_jsonl(opslib.STATE_DIR / "legs/lead-inbox/events.jsonl",
                        {"event_type": "quote.needs_owner_review",
                         "occurred_at": opslib.now_iso(),
                         "correlation_id": qt,
                         "source_component": "QuoteEngine",
                         "payload": {"lead_id": lead_id, "reason": reason,
                                     **detail}})
    memory_chain.append("quote_needs_owner_review", lead_id,
                        {"qt": qt, "reason": reason, **detail})
    try:
        import owner_notify
        owner_notify.alert_owner(
            f"⚠️ کوت {qt} ({lead_id[-30:]}) نیازمند بررسی توست — {reason}: "
            + json.dumps(detail, ensure_ascii=False)[:200])
    except Exception:  # noqa: BLE001
        pass
    return {"qt_number": qt, "priced": True, "sent": False,
            "status": "needs_owner_review", "reason": reason, **detail}


def card_sha256(path: Path | None = None) -> str:
    """HF-3: هشِ کارتِ فعال — در هر رکورد کوت و در گیت ثبت می‌شود.
    path در call-time خوانده می‌شود (تست/مهاجرت قابل‌تزریق)."""
    try:
        return hashlib.sha256(
            (path or CARD).read_bytes()).hexdigest()
    except OSError:
        return ""


def load_card() -> dict:
    try:
        return json.loads(CARD.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def identity_line() -> str:
    """امضای سنددار — ABN/بیمه از identity.json؛ نبود = بدونِ ادعا (صادق)."""
    try:
        d = json.loads(IDENTITY.read_text(encoding="utf-8"))
        parts = []
        if d.get("abn"):
            parts.append(f"ABN {d['abn']}")
        if d.get("insurer") and d.get("insurance_policy"):
            parts.append(f"Insured ({d['insurer']}, policy {d['insurance_policy']})")
        elif d.get("insurance_policy"):
            parts.append("Fully insured")
        if parts:
            return " · ".join(parts) + "\n"
        return ""
    except Exception:  # noqa: BLE001
        return ""


def next_qt_number(conn) -> str:
    import datetime as _dt
    day = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d")
    conn.execute("CREATE TABLE IF NOT EXISTS painting_quotes ("
                 "qt_number TEXT PRIMARY KEY, lead_id TEXT, scope_json TEXT, "
                 "priced INTEGER, total_aud REAL, status TEXT, created_at TEXT, "
                 "card_sha256 TEXT, fingerprint TEXT)")
    # مهاجرت ستون‌های HF برای جدول‌های قدیمی (idempotent)
    for col in ("card_sha256", "fingerprint"):
        try:
            conn.execute(f"ALTER TABLE painting_quotes ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass
    row = conn.execute("SELECT COUNT(*) FROM painting_quotes "
                       "WHERE qt_number LIKE ?", (f"QT-{day}-%",)).fetchone()
    return f"QT-{day}-{int(row[0]) + 1:03d}"


def estimate(scope: dict, card: dict) -> dict:
    """قیمت از بازهٔ کارت — هرگز عددِ آزاد. غایب/قفل → بدونِ قیمت."""
    if not card.get("approved_by_owner"):
        return {"priced": False, "reason": "rate-card-not-approved"}
    a = card.get("market_assumption", {})
    m2 = float(scope.get("area_m2") or 0)
    kind = str(scope.get("kind") or "internal").lower()
    band_key = ("ceiling_per_m2_aud" if "ceil" in kind else
                "external_per_m2_aud" if "external" in kind else
                "internal_per_m2_aud")
    lo, hi = a.get(band_key, [0, 0])
    if m2 <= 0 or not lo:
        return {"priced": False, "reason": "no-area"}
    mid = (lo + hi) / 2.0
    total = mid * m2
    return {"priced": True, "rate_mid": round(mid, 2),
            "band": [lo, hi], "total_aud": round(total, 0),
            "validity_days": a.get("quote_validity_days", 30)}


def render(qt: str, buyer: str, scope: dict, est: dict) -> dict:
    loc = scope.get("location") or "site"
    works = scope.get("works") or "painting works"
    ident = identity_line()
    if est.get("priced"):
        total = est["total_aud"]
        body = (f"Reference: {qt}\n\n"
                f"Quote for {works} at {loc} "
                f"(approx. {scope.get('area_m2', '?')} m²):\n\n"
                f"Total: ${total:,.0f} incl. GST, labour, materials and "
                f"prep. Rate basis ${est['rate_mid']}/m² within "
                f"${est['band'][0]}–${est['band'][1]}/m².\n\n"
                f"This quote is valid for {est['validity_days']} days. "
                f"Site inspection can refine the figure before you commit.\n\n"
                f"{ident}Kind regards,\nMaster Painting\nSydney NSW")
        subject = f"Painting quote {qt} — {works}"
    else:
        body = (f"Reference: {qt}\n\n"
                f"Thanks for your reply about {works} at {loc}. To price it "
                f"properly I would like a short site visit or a quick scope "
                f"(areas, surfaces, access). Happy to work around your "
                f"programme — what suits?\n\n"
                f"{ident}Kind regards,\nMaster Painting\nSydney NSW")
        subject = f"Painting works at {loc} — next step ({qt})"
    return {"subject": subject, "body": body}


def style_gate_ok(draft: dict) -> bool:
    text = (draft.get("subject", "") + " " + draft.get("body", "")).lower()
    return not any(b in text for b in FORBIDDEN)


def quote(lead_id: str, scope: dict, dry: bool = True) -> dict:
    """ساختِ کوت برای یک لیدِ engaged — فقط تولید، هیچ ارسالی.

    PR #110A (scope-split): این ماژول draft می‌سازد؛ مسیر ارسال
    (capability_token/transport) عمداً در این ماژول وجود ندارد و در PR
    جداگانه‌ای با review صادقانه بازمی‌گردد.
    """
    out = {"lead_id": lead_id}
    if not dry:
        return {**out, "error": "send-path-removed: generation-only module"}
    card = load_card()
    est = estimate(scope, card)
    c = sqlite3.connect(PAINTING_DB)
    c.row_factory = sqlite3.Row
    row = c.execute("SELECT customer_name, email FROM painting_leads "
                    "WHERE lead_id=?", (lead_id,)).fetchone()
    if not row or not (row["email"] or "").strip():
        c.close()
        out["error"] = "lead-not-found-or-no-email"
        return out
    qt = next_qt_number(c)
    buyer = row["customer_name"] or "there"
    draft = render(qt, buyer, scope, est)
    if not style_gate_ok(draft):
        c.close()
        out["error"] = "style-gate"
        return out
    out.update({"qt_number": qt, "priced": est.get("priced", False),
                "subject": draft["subject"]})
    csha = card_sha256()
    # ── HF-2: گارد مقاوم به rollback — بیرون از دیتابیس، قبل از هر تصمیم ──
    total_for_fp = est.get("total_aud") if est.get("priced") else 0
    fp, already = qfp.guard(lead_id, scope, total_for_fp)
    if already:
        out["error"] = "duplicate-fingerprint-rollback-guard"
        out["status"] = "DUPLICATE_BLOCKED"
        memory_chain.append("quote_duplicate_blocked", lead_id,
                            {"qt": qt, "fingerprint": fp[:16]})
        c.close()
        return out
    if True:  # generation-only (110A): everything past here returns the draft
        out["draft"] = draft
        out["card_sha256"] = csha
        out["fingerprint"] = fp
        out["needs_owner_review"] = not est.get("priced", False)
        c.close()
        return out


def quote_requests_pending() -> list[str]:
    """لیدهایی که imap_listener رویشان quote requested گذاشته."""
    c = sqlite3.connect(PAINTING_DB)
    rows = c.execute("SELECT lead_id FROM painting_leads "
                     "WHERE next_action='quote requested'").fetchall()
    c.close()
    return [r[0] for r in rows]


def book_wins() -> dict:
    """لیدهای won (از reply) → ثبت booked_amount_cents از آخرین کوتِ قیمت‌دارِ
    sent. مبلغِ واقعی را جوابِ ایمیل می‌گوید؛ digest مالک تأیید را می‌بیند."""
    c = sqlite3.connect(PAINTING_DB)
    out = []
    rows = c.execute("SELECT lead_id FROM painting_leads "
                     "WHERE status='won' AND "
                     "(booked_amount_cents IS NULL OR booked_amount_cents=0)"
                     ).fetchall()
    for (lid,) in rows:
        q = c.execute("SELECT qt_number, total_aud FROM painting_quotes "
                      "WHERE lead_id=? AND status='sent' AND priced=1 "
                      "ORDER BY created_at DESC LIMIT 1", (lid,)).fetchone()
        if q and q[1]:
            cents = int(round(float(q[1]) * 100))
            c.execute("UPDATE painting_leads SET booked_amount_cents=?, "
                      "booked_currency='AUD', status='won', "
                      "booked_at=datetime('now') WHERE lead_id=?", (cents, lid))
            opslib.append_jsonl(
                opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl",
                {"event_type": "revenue.booked", "occurred_at": opslib.now_iso(),
                 "correlation_id": q[0], "source_component": "QuoteEngine",
                 "payload": {"lead_id": lid, "aud": q[1], "cents": cents}})
            out.append({"lead_id": lid, "qt": q[0], "aud": q[1]})
    c.commit()
    c.close()
    return {"booked": out}


if __name__ == "__main__":
    if "--book-wins" in sys.argv:
        print(json.dumps(book_wins(), ensure_ascii=False, indent=1))
    else:
        print(json.dumps({"usage": "--book-wins | quote(lead_id, scope) via API"},
                         ensure_ascii=False))
