"""followup_worker — مجریِ فالوآپ (Lane E5، رأی مالک Q4: حداکثر ۲ یادآوری، فاصلهٔ ۷ روز).

هر روز (systemd timer) لیدهایی را برمی‌دارد که:
  status='contacted' AND next_action_at <= now AND follow_up_count < 2
و برایشان یادآوری می‌فرستد از همان گیت‌لدرِ transport (suppression/WAL/سقف).
بعد از یادآوری دوم + ۷ روز سکوت → status='nurture' (بازگشت در ۹۰ روز، نه حذف).

پیش‌شرط‌ها (هر شکست = skipِ سالم، نه crash):
  - کمپین کِیل نشده باشد (flag campaign-halt)
  - suppression فعال نباشد (consent_store)
  - سقف روزانه (outbound_worker.sends_today < cap)
  - wire flag روشن (OCTOPUS_WIRE_LEAD_OUTBOUND)
idempotent: idem_key = lead-followup:{lead_id}:{n}
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))

import opslib  # noqa: E402
import lead_outbound_transport as transport  # noqa: E402
import capability_token as cap  # noqa: E402
import memory_chain  # noqa: E402
from lead_email_writer import write_followup, check_followup  # noqa: E402

PAINTING_DB = Path.home() / ".local/share/ofn/painting.sqlite"
CAMPAIGN = "PAINT-L5-001"


def _halted() -> str | None:
    h = opslib.master_halted()
    if h:
        return h
    f = opslib.STATE_DIR / f"campaign-halt-{CAMPAIGN}.flag"
    return f"campaign-killed" if f.exists() else None


def _suppressed(em: str) -> bool:
    try:
        import consent_store as _cs
        return bool(_cs.ConsentStore().suppression_active(em.strip().lower()))
    except Exception:  # noqa: BLE001
        return False


def due_leads(now_iso: str) -> list[dict]:
    c = sqlite3.connect(PAINTING_DB)
    c.row_factory = sqlite3.Row
    rows = c.execute(
        "SELECT lead_id, customer_name, email, follow_up_count, "
        "next_action_at, budget_text FROM painting_leads "
        "WHERE status='contacted' AND next_action_at IS NOT NULL "
        "AND next_action_at <= ? AND follow_up_count < 2 AND email != ''",
        (now_iso,)).fetchall()
    c.close()
    return [dict(r) for r in rows]


def cycle(now_iso: str | None = None, dry: bool = False) -> dict:
    import datetime as _dt
    now = now_iso or opslib.now_iso()
    out = {"now": now, "due": 0, "sent": 0, "skipped": [], "results": []}
    halt = _halted()
    if halt:
        out["halted"] = halt
        return out
    try:
        import outbound_worker as _ow
        if _ow.cap_reached():
            out["skipped"].append("daily-cap")
            return out
    except Exception:  # noqa: BLE001 — سقف خوانده نشد = محتاطانه ادامه نده
        out["skipped"].append("cap-check-failed")
        return out
    if not dry and os.environ.get("OCTOPUS_WIRE_LEAD_OUTBOUND") != "1":
        out["skipped"].append("wire-flag-off")
        return out
    leads = due_leads(now)
    out["due"] = len(leads)
    for lead in leads:
        n = int(lead.get("follow_up_count") or 0) + 1
        em = (lead.get("email") or "").strip()
        if _suppressed(em):
            out["skipped"].append(f"suppressed:{em[:30]}")
            continue
        draft = write_followup(lead["lead_id"], lead.get("customer_name", ""),
                               nth=n)
        errs = check_followup(draft)
        if errs:  # گیت سبک — یادآوریِ ناقص هرگز نمی‌رود
            out["skipped"].append(f"style-gate:{lead['lead_id'][-20:]}:{errs}")
            continue
        if dry:
            out["results"].append({"lead": lead["lead_id"][-30:], "nth": n, "dry": True})
            continue
        tok, tok_reason = cap.request_send_token(
            {"email": em}, f"followup#{n}:{lead['lead_id'][-30:]}")
        if tok is None:
            out["skipped"].append(f"token:{tok_reason}:{lead['lead_id'][-20:]}")
            continue
        res = cap.verified_send(tok, {"lead_id": lead["lead_id"], "email": em},
                                {"subject": draft["subject"], "body": draft["body"]},
                                f"followup#{n}")
        memory_chain.append("followup_sent" if res.get("sent") else "followup_denied",
                            lead["lead_id"],
                            {"nth": n, "status": res.get("status")})
        c = sqlite3.connect(PAINTING_DB)
        if res.get("sent"):
            c.execute("UPDATE painting_leads SET follow_up_count=?, "
                      "last_follow_up_at=?, "
                      "next_action_at=datetime(next_action_at, '+7 days') "
                      "WHERE lead_id=?", (n, now, lead["lead_id"]))
            out["sent"] += 1
        else:
            # ارسال نشد (سقف/سرکوب/WAL) — فردا دوباره امتحان؛ effect نسوخته
            out["skipped"].append(
                f"send:{res.get('status')}:{lead['lead_id'][-20:]}")
        # بعد از یادآوریِ دوم، ساعتِ nurture را بگذار (۷ روز بعد)
        if n >= 2:
            c.execute("UPDATE painting_leads SET next_action='nurture after 7d silence' "
                      "WHERE lead_id=?", (lead["lead_id"],))
        c.commit()
        c.close()
        out["results"].append({"lead": lead["lead_id"][-30:], "nth": n,
                               "status": res.get("status")})
    # nurture: دومین یادآوری رفت و ۷ روز گذشت و هنوز contacted؟ → آرشیوِ مراقبت
    c = sqlite3.connect(PAINTING_DB)
    c.execute("UPDATE painting_leads SET status='archived', "
              "next_action='nurture revisit 2026-12 (90d)', "
              "next_action_at=datetime('now') "
              "WHERE status='contacted' AND follow_up_count>=2 "
              "AND last_follow_up_at IS NOT NULL "
              "AND last_follow_up_at < datetime('now', '-7 days')")
    nurtured = c.total_changes
    c.commit()
    c.close()
    if nurtured:
        out["nurtured"] = nurtured
    return out


def sweep_to_nurture() -> int:
    """جدایی از cycle برای تست آفلاین."""
    c = sqlite3.connect(PAINTING_DB)
    c.execute("UPDATE painting_leads SET status='archived', "
              "next_action='nurture revisit 90d', "
              "next_action_at=datetime('now') "
              "WHERE status='contacted' AND follow_up_count>=2 "
              "AND last_follow_up_at < datetime('now', '-7 days')")
    n = c.total_changes
    c.commit()
    c.close()
    return n


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    try:
        print(json.dumps(cycle(dry=dry), ensure_ascii=False, indent=1))
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False))
