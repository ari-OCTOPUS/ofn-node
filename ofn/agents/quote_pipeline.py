"""quote_pipeline — حلقهٔ E→Q (نقشهٔ راه #64، پیکربندی ۲۰۲۶-۰۹-۰۲).

imap_listener روی لیدِ «scope خواست» برچسبِ next_action='quote requested'
می‌گذارد؛ این پایپ‌لاین هر ۳۰ دقیقه آن لیدها را برمی‌دارد، scope می‌سازد و
موتور کوت را صدا می‌زند. قفلِ rate-card را quote_engine خودش رعایت می‌کند
(تا تأیید مالک: کوتِ بدونِ قیمت + درخواست بازدید — کاملاً خودکار).

idempotent: اگر برای لید در ۷ روزِ گذشته کوتِ sent باشد، دست نمی‌زند.
scope از دادهٔ لید می‌آید (آخرین توصیفِ کارِ OCP)؛ متراژ نداریم پس قیمت‌دار
نمی‌شود — که با قفلِ فعلی هم‌راستاست. بعد از تأییدِ کارت توسط مالک، اگر
متراژ از ایمیل قابل استخراج باشد موتور خودش قیمت‌دار می‌شود.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))

import opslib  # noqa: E402

PAINTING_DB = Path.home() / ".local/share/ofn/painting.sqlite"
CAMPAIGN = "PAINT-L5-001"


def _campaign_killed() -> bool:
    return (opslib.STATE_DIR / f"campaign-halt-{CAMPAIGN}.flag").exists()


def pending_requests() -> list[dict]:
    c = sqlite3.connect(PAINTING_DB)
    c.row_factory = sqlite3.Row
    rows = c.execute(
        "SELECT lead_id, customer_name, email, next_action, notes "
        "FROM painting_leads WHERE next_action='quote requested' AND email != ''"
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]


def recently_quoted(lead_id: str) -> bool:
    c = sqlite3.connect(PAINTING_DB)
    try:
        row = c.execute(
            "SELECT COUNT(*) FROM painting_quotes WHERE lead_id=? AND "
            "status='sent' AND created_at > datetime('now','-7 days')",
            (lead_id,)).fetchone()
        return bool(row and row[0])
    except sqlite3.OperationalError:
        return False  # جدول هنوز ساخته نشده
    finally:
        c.close()


def build_scope(lead: dict, reply_body: str = "") -> dict:
    """scope از دادهٔ شناخته‌شده — هیچ عددی از خودمان اختراع نمی‌شود."""
    works = (lead.get("last_work_description")
             or lead.get("notes")
             or "painting works").strip()[:120]
    scope = {"works": works,
             "location": (lead.get("customer_name") or "")[:80]}
    m2 = None
    text = (reply_body or "") + " " + works
    m = re.search(r"(\d{2,5})\s*(?:m2|m²|sqm|square metres?)", text, re.I)
    if m:
        m2 = int(m.group(1))
    if m2:
        scope["area_m2"] = m2
    return scope


def cycle(dry: bool = True) -> dict:
    out = {"checked": 0, "quoted": 0, "skipped": [], "results": []}
    h = opslib.master_halted()
    if h:
        out["halted"] = h
        return out
    if _campaign_killed():
        out["skipped"].append("campaign-killed")
        return out
    leads = pending_requests()
    out["checked"] = len(leads)
    for lead in leads:
        lid = lead["lead_id"]
        if recently_quoted(lid):
            out["skipped"].append(f"already-quoted:{lid[-25:]}")
            continue
        import quote_engine as qe
        scope = build_scope(lead)
        if dry:
            out["results"].append({"lead": lid[-25:], "scope": scope, "dry": True})
            continue
        res = qe.quote(lid, scope)
        out["results"].append({"lead": lid[-25:], "qt": res.get("qt_number"),
                               "priced": res.get("priced"),
                               "sent": res.get("sent"),
                               "status": res.get("send_status")})
        if res.get("sent"):
            out["quoted"] += 1
        else:
            out["skipped"].append(f"send:{res.get('error') or res.get('send_status')}:{lid[-20:]}")
    return out


def extract_m2_from_events(lead_id: str) -> str:
    """آخرین quote_requested این لید را برمی‌گرداند (برای future use)."""
    ev = opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl"
    try:
        hits = [ln for ln in ev.read_text().splitlines()
                if lead_id in ln and "quote_requested" in ln]
        return hits[-1] if hits else ""
    except Exception:  # noqa: BLE001
        return ""


if __name__ == "__main__":
    # fail-closed: quote_sent / transport binding stays off unless a newer
    # scoped flag is present. --dry still wins if both are passed.
    dry = "--authorize-send" not in sys.argv or "--dry" in sys.argv
    try:
        print(json.dumps(cycle(dry=dry), ensure_ascii=False, indent=1))
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False))
