#!/usr/bin/env python3
"""invoice.py — اینویسِ ATO-compliant برای نقاشی سیدنی (propose-only).

PAID مشتق از attribution CONFIRMED است — هرگز state جدیدی در attribution ایجاد نمی‌کند.
اینویس فقط سند است: خواندنِ claim_amount + quote breakdown → ثابت کردنِ قیمت → persist.

ATO Tax Invoice requirements (researched 2026-07-12):
  - "Tax Invoice" label (if GST registered)
  - ABN mandatory
  - GST 10% shown separately
  - >$1000: buyer identity/ABN required
  - Response within 28 days of request

NSW Home Building Act §8: max deposit 10% of contract price.

propose-only: فقط تولید سند. ارسال = دستی (human-gated).
$0 · stdlib + opslib · fail-soft.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib  # noqa: E402

# ─── directories ────────────────────────────────────────────────────────────
def _invoices_dir(state_dir=None) -> Path:
    base = Path(state_dir) if state_dir else opslib.STATE_DIR
    return base / "legs" / "invoices"


def _drafts_dir(state_dir=None) -> Path:
    base = Path(state_dir) if state_dir else opslib.STATE_DIR
    return base / "legs" / "lead-drafts"


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-]", "-", str(name or ""))[:64] or "unknown"


def _read(p: Path) -> dict:
    try:
        d = json.loads(p.read_text("utf-8")) if p.exists() else {}
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


# ─── business config from budgets.yaml ───────────────────────────────────────
def _business_config() -> dict:
    """خواندنِ business section از budgets.yaml. fail-soft."""
    try:
        budgets = opslib.load_budgets()
        biz = budgets.get("business", {})
        return {
            "abn": str(biz.get("abn", "")).strip(),
            "trading_name": str(biz.get("trading_name", "")).strip(),
            "address": str(biz.get("address", "")).strip(),
            "payment_terms": str(biz.get("payment_terms", "Due within 14 days")).strip(),
            "payment_methods": str(biz.get("payment_methods", "Bank Transfer")).strip(),
            "bank_details": str(biz.get("bank_details", "")).strip(),
        }
    except Exception:  # noqa: BLE001
        return {"abn": "", "trading_name": "", "address": "",
                "payment_terms": "Due within 14 days",
                "payment_methods": "Bank Transfer", "bank_details": ""}


# ─── INV number: INV-FY{YY}-{NNN} ────────────────────────────────────────
def _next_inv_num(state_dir=None) -> str:
    """INV-FY26-001 format. fail-soft."""
    today = opslib.today()
    # FY = July-June; if month >= 7, FY year = current year, else year+1
    fy_year = int(today[:4]) if int(today[5:7]) >= 7 else int(today[:4]) + 1
    fy_tag = f"FY{fy_year % 100:02d}"
    prefix = f"INV-{fy_tag}-"
    counter_file = _invoices_dir(state_dir) / f"{_safe('inv_seq')}.json"
    try:
        data = _read(counter_file)
        last_tag = data.get("last_tag")
        seq = int(data.get("seq", 0))
        if last_tag != fy_tag:
            seq = 0  # new FY → reset
        seq += 1
        counter_file.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(counter_file) as lj:
            lj.write({"last_tag": fy_tag, "seq": seq})
        return f"{prefix}{seq:03d}"
    except Exception:  # noqa: BLE001
        return f"{prefix}001"


def _gst_registered() -> bool:
    """گیتِ GST از policy-profileِ حسابداری (auditِ 2026-07-16 #6): فقط `is True`.
    نبودِ profile/ماژول → False (fail-closed: بدونِ تأیید، «TAX INVOICE»/GST ادعا نمی‌شود)."""
    try:
        import ledger_core  # noqa: WPS433 — هم‌پوشه
        for e in ((ledger_core.load_profile() or {}).get("entities") or []):
            if isinstance(e, dict) and e.get("gst_registered") is True:
                return True
    except Exception:  # noqa: BLE001
        pass
    return False


# ─── create_invoice ─────────────────────────────────────────────────────────
def create_invoice(attribution_id: str, fixed_amount: float | None = None,
                    state_dir=None) -> dict:
    """ایجادِ اینویس از attribution_id.
    منبع: quote draft (line_items) + claim_amount.
    fixed_amount: مبلغِ قطعی (اگر None → از claim_amount یا midpoint quote).
    خروجی: {ok, inv_number, path, summary} یا {ok: False, error}.
    propose-only: فقط persist، ارسال = دستی."""
    if not attribution_id:
        return {"ok": False, "error": "attribution_id لازم است"}

    # ── read quote draft ────────────────────────────────────────────────
    draft_path = _drafts_dir(state_dir) / f"{_safe(attribution_id)}.json"
    draft = _read(draft_path)

    # ── determine amounts ──────────────────────────────────────────────
    bd = draft.get("breakdown") or {}
    line_items = bd.get("line_items") or []
    subtotal_lo = float(bd.get("subtotal_excl_gst", [0, 0])[0] if isinstance(bd.get("subtotal_excl_gst"), list) else 0)
    subtotal_hi = float(bd.get("subtotal_excl_gst", [0, 0])[-1] if isinstance(bd.get("subtotal_excl_gst"), list) else 0)

    # گیتِ GST از policy-profile (auditِ 2026-07-16 #6): فقط اگر gst_registered صریحاً
    # True باشد GST محاسبه/ادعا می‌شود؛ وگرنه صفر و سندِ ساده (fail-closed — سیستم
    # خودش نتیجهٔ مالیاتی نمی‌سازد). profile واقعیِ مالک: Pty Ltd، registered=true.
    gst_on = _gst_registered()
    if fixed_amount is not None:
        subtotal_excl = round(float(fixed_amount) / 1.1, 2) if gst_on \
            else round(float(fixed_amount), 2)               # بدونِ ثبتِ GST، reverse-GST بی‌معناست
    elif subtotal_lo > 0:
        subtotal_excl = round((subtotal_lo + subtotal_hi) / 2, 2)  # midpoint
    else:
        subtotal_excl = 0.0

    gst = round(subtotal_excl * 0.10, 2) if gst_on else 0.0
    total_incl = round(subtotal_excl + gst, 2)
    deposit = round(total_incl * 0.10, 2)  # NSW HBA §8

    # ── fix line item amounts (from ranges to single values) ──────────
    fixed_items = []
    if line_items and subtotal_excl > 0:
        # scale factor: midpoint / sum of midpoints
        sum_mid = sum(
            (float(li.get("subtotal_aud", [0, 0])[0]) + float(li.get("subtotal_aud", [0, 0])[-1])) / 2
            for li in line_items
        ) if line_items else 1.0
        scale = subtotal_excl / max(sum_mid, 0.01)
        for li in line_items:
            rate_range = li.get("rate_aud", [0, 0])
            rate_mid = round((float(rate_range[0]) + float(rate_range[-1])) / 2 * scale, 2)
            sub_mid = round(float(li.get("subtotal_aud", [0, 0])[0] + li.get("subtotal_aud", [0, 0])[-1]) / 2 * scale, 2) if isinstance(li.get("subtotal_aud"), list) else round(float(li.get("subtotal_aud", 0)) * scale, 2)
            fixed_items.append({
                "description": li.get("description", ""),
                "qty": li.get("qty", 0),
                "unit": li.get("unit", ""),
                "rate_aud": rate_mid,
                "subtotal_aud": sub_mid,
            })

    # ── business config ───────────────────────────────────────────────
    biz = _business_config()

    # ── inv number ────────────────────────────────────────────────────
    inv_num = _next_inv_num(state_dir)

    # ── build invoice record ──────────────────────────────────────────
    rec = {
        "ts": opslib.now_iso(),
        "schema": "invoice.v1",
        "inv_number": inv_num,
        "attribution_id": str(attribution_id),
        "issue_date": opslib.today(),
        "due_date": _due_date(opslib.today(), biz.get("payment_terms", "Due within 14 days")),
        "line_items": fixed_items,
        "subtotal_excl_gst": subtotal_excl,
        "gst": gst,
        "gst_registered": gst_on,          # گیتِ profile — render عنوان/خطِ GST را از این می‌گیرد
        "total_incl_gst": total_incl,
        "deposit_max": deposit,
        "business": biz,
        "paid": False,
        "paid_ts": None,
        "paid_amount": 0.0,
        "status": "ISSUED",  # ISSUED → PAID (derived from reconcile)
    }

    # ── check if already CONFIRMED/ATTRIBUTED → auto-mark paid ─────────
    paid_info = _check_reconcile_paid(attribution_id, state_dir)
    if paid_info:
        rec["paid"] = True
        rec["paid_ts"] = paid_info.get("ts")
        rec["paid_amount"] = paid_info.get("amount", 0.0)
        rec["status"] = "PAID"

    # ── persist ─────────────────────────────────────────────────────────
    path = _invoices_dir(state_dir) / f"{_safe(attribution_id)}.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(path) as lj:
            lj.write(rec)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"invoice persist failed: {type(e).__name__}: {e}"])
        return {"ok": False, "error": "اینیوذ ذخیره نشد"}

    return {
        "ok": True, "inv_number": inv_num, "path": str(path),
        "summary": render_invoice_html(rec),
        "paid": rec["paid"],
    }


# ─── mark_paid ───────────────────────────────────────────────────────────────
def mark_paid(attribution_id: str, state_dir=None) -> dict:
    """بررسیِ reconcile-latest.json و علامت‌گذاریِ PAID.
    PAID مشتق از CONFIRMED/ATTRIBUTED در attribution — نه state جدید."""
    if not attribution_id:
        return {"ok": False, "error": "attribution_id لازم است"}

    path = _invoices_dir(state_dir) / f"{_safe(attribution_id)}.json"
    rec = _read(path)
    if not rec:
        return {"ok": False, "error": "اینیوذ پیدا نشد"}
    if rec.get("paid"):
        return {"ok": True, "already_paid": True}

    paid_info = _check_reconcile_paid(attribution_id, state_dir)
    if not paid_info:
        return {"ok": False, "error": "هنوز CONFIRMED نشده (PAID نیست)"}

    rec["paid"] = True
    rec["paid_ts"] = paid_info.get("ts")
    rec["paid_amount"] = paid_info.get("amount", 0.0)
    rec["status"] = "PAID"
    try:
        with opslib.LockedJson(path) as lj:
            lj.write(rec)
        return {"ok": True, "inv_number": rec.get("inv_number"), "amount": paid_info.get("amount")}
    except Exception:  # noqa: BLE001
        return {"ok": False, "error": "به‌روزرسانی شکست"}


# ─── invoices_pending ────────────────────────────────────────────────────────
def invoices_pending(state_dir=None) -> list:
    """اینیوذهای ISSUED (نه PAID). fail-soft."""
    out = []
    try:
        for p in sorted(_invoices_dir(state_dir).glob("*.json")):
            r = _read(p)
            if r and r.get("schema") == "invoice.v1" and not r.get("paid"):
                out.append(r)
    except OSError:
        pass
    return out


def invoices_all(state_dir=None) -> dict:
    """خلاصه: N issued, N paid."""
    issued = 0
    paid = 0
    try:
        for p in sorted(_invoices_dir(state_dir).glob("*.json")):
            r = _read(p)
            if r and r.get("schema") == "invoice.v1":
                issued += 1
                if r.get("paid"):
                    paid += 1
    except OSError:
        pass
    return {"n_issued": issued, "n_paid": paid,
            "n_outstanding": issued - paid,
            "line": f"📄 {issued} invoice ({paid} paid, {issued - paid} outstanding)"}


# ─── render_invoice_html ────────────────────────────────────────────────────
def render_invoice_html(rec: dict) -> str:
    """خروجی HTML برای نمایش (Telegram/چاپ). ATO-compliant format."""
    import html
    biz = rec.get("business") or {}
    inv = html.escape(str(rec.get("inv_number") or "?"))
    aid = html.escape(str(rec.get("attribution_id") or "?"))
    abn = html.escape(biz.get("abn", "—"))
    name = html.escape(biz.get("trading_name", "—"))
    addr = html.escape(biz.get("address", "—"))
    total = float(rec.get("total_incl_gst", 0))
    gst = float(rec.get("gst", 0))
    sub = float(rec.get("subtotal_excl_gst", 0))
    dep = float(rec.get("deposit_max", 0))
    status = "✅ PAID" if rec.get("paid") else "📄 ISSUED"
    issue = html.escape(str(rec.get("issue_date", "")))
    due = html.escape(str(rec.get("due_date", "")))

    # عنوانِ «TAX INVOICE» فقط برای entityِ ثبتِ GST (auditِ 2026-07-16 #6 — سندِ مالیاتیِ
    # قانونی بدونِ ثبت، ادعای دروغ است). رکوردهای قدیمی (بدونِ فیلد) از gst>0 استنتاج.
    gst_reg = bool(rec.get("gst_registered", gst > 0))
    title = "TAX INVOICE" if gst_reg else "INVOICE"
    lines = [
        f"<b>{title}</b> {inv} <code>{status}</code>",
        f"<b>{name}</b>",
        f"ABN: <code>{abn}</code>",
        f"Date: {issue} · Due: {due}",
        "",
        f"Ref: <code>{aid}</code>",
        "",
        "<b>Items:</b>",
    ]
    for item in rec.get("line_items", []):
        desc = html.escape(str(item.get("description", ""))[:60])
        rate = float(item.get("rate_aud", 0))
        qty = float(item.get("qty", 0))
        sub_item = float(item.get("subtotal_aud", 0))
        lines.append(f"  {desc}: {qty}×${rate:.2f} = <code>${sub_item:.2f}</code>")

    lines.append("")
    if gst_reg:
        lines.extend([
            f"Subtotal (excl GST): <code>${sub:.2f}</code>",
            f"GST (10%): <code>${gst:.2f}</code>",
            f"<b>TOTAL (incl GST): <code>${total:.2f}</code></b>",
        ])
    else:
        lines.append(f"<b>TOTAL: <code>${total:.2f}</code></b>")
    lines.extend([
        f"Max deposit: <code>${dep:.2f}</code> (10% · NSW §8)",
        "",
        f"Payment: {html.escape(biz.get('payment_methods', ''))}",
    ])
    if biz.get("bank_details"):
        lines.append(f"Bank: <code>{html.escape(biz['bank_details'])}</code>")
    lines.append(f"Terms: {html.escape(biz.get('payment_terms', ''))}")
    return "\n".join(lines)


# ─── helpers ──────────────────────────────────────────────────────────────────
def _due_date(issue_date: str, terms: str) -> str:
    """محاسبهٔ due_date از payment_terms. fail-soft."""
    import datetime
    try:
        d = datetime.date.fromisoformat(issue_date)
    except (ValueError, TypeError):
        return ""
    # parse "Due within N days"
    import re as _re
    m = _re.search(r"(\d+)\s*(?:days?|روز)", terms, _re.IGNORECASE)
    if m:
        delta = int(m.group(1))
        return (d + datetime.timedelta(days=delta)).isoformat()
    return (d + datetime.timedelta(days=14)).isoformat()  # default


def _check_reconcile_paid(attribution_id: str, state_dir=None) -> dict | None:
    """بررسیِ reconcile-latest.json: آیا این attribution_id CONFIRMED شده؟"""
    import attribution  # noqa: WPS433
    try:
        fold = attribution.fold()
        rec = fold.get(attribution_id)
        if rec and rec.get("state") in attribution.CONFIRMED_STATES:
            return {"ts": rec.get("confirm_date") or opslib.now_iso(),
                    "amount": float(rec.get("amount_aud", 0))}
    except Exception:  # noqa: BLE001
        pass
    return None


if __name__ == "__main__":
    import json
    print(json.dumps(invoices_all(), ensure_ascii=False, indent=2))
