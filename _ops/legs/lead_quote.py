#!/usr/bin/env python3
"""lead_quote.py — چرخهٔ حیاتِ کوتیشنِ ساختاریافته (self-contained؛ جانشینِ lead_draft).

منبعِ حقیقتِ persist = state/legs/lead-drafts/ (همان مسیرِ lead_draftِ حذف‌شده). OPS-01 را
زمین می‌زند: intake ساختاریافته → pricing → line_items → Proposal → persist → render.
(LEG-04 2026-07-13: pending/mark_sent/summary دیگر importِ مردهٔ lead_draft ندارند.)

افزوده نسبت به lead_draft:
  - QuoteIntake (dataclass): فیلدهای ساختاریافته بجای scope ساده
  - pricing.estimate_price(): نرخ‌های تحقیق‌شده + ضریب‌ها
  - line_items: ردیف‌های تفصیلی (labor, material, prep, access)
  - شماره‌گذاریِ QT-YYYYMMDD-NNN (پشتِ attribution_id)
  - نسخه‌بندی: revise_quote → نسخهٔ جدید، قدیمی حفظ (append-only)
  - render_quote_html: خروجی قابل‌خواندن برای Telegram/چاپ

propose-only مطلق: فقط draft تولید و persist. ارسال/تماس/پول human-gated.
$0 · stdlib + opslib · fail-soft.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib  # noqa: E402
from pricing import QuoteIntake, estimate_price, PriceBreakdown  # noqa: E402

# ─── quote directory (همان lead_draft) ─────────────────────────────────────
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


# ─── QT number: QT-YYYYMMDD-NNN ─────────────────────────────────────────────
_QT_SEQ_KEY = "_qt_seq"


def _next_qt_num(state_dir=None) -> str:
    """شمارهٔ بعدی: QT-YYYYMMDD-NNN. fail-soft: اگر شمارنده شکست خورد → NNN=001."""
    today = opslib.today()
    prefix = f"QT-{today}-"
    counter_file = _drafts_dir(state_dir) / f"{_safe(_QT_SEQ_KEY)}.json"
    try:
        data = _read(counter_file)
        last = data.get("last_date")
        seq = int(data.get("seq", 0))
        if last != today:
            seq = 0  # روز جدید → reset
        seq += 1
        counter_file.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(counter_file) as lj:
            lj.write({"last_date": today, "seq": seq})
        return f"{prefix}{seq:03d}"
    except Exception:  # noqa: BLE001
        return f"{prefix}001"


# ─── create_quote ──────────────────────────────────────────────────────────
def create_quote(leg, attribution_id: str, intake: QuoteIntake,
                 state_dir=None) -> dict:
    """intake ساختاریافته → pricing → Proposal → persist.
    خروجی: {ok, path, qt_number, proposal_id, breakdown, summary}
    یا {ok: False, error}. propose-only."""
    if leg is None or not attribution_id:
        return {"ok": False, "error": "leg/attribution_id لازم است"}

    # ── pricing ─────────────────────────────────────────────────────────
    breakdown = estimate_price(intake)
    bd_dict = breakdown.to_dict()

    # ── quote number ────────────────────────────────────────────────────
    qt_num = _next_qt_num(state_dir)

    # ── call leg.draft_quote (backward-compat) ─────────────────────────
    price_range = bd_dict["total_incl_gst"]  # [lo, hi]
    # merge assumptions: auto + any from intake scope
    assumptions = list(breakdown.assumptions_auto)
    if intake.scope:
        assumptions.insert(0, f"Scope: {intake.scope[:300]}")

    try:
        prop = leg.draft_quote(
            attribution_id,
            scope=intake.scope or f"{intake.area_type} painting ({intake.size_m2:.0f}m²)",
            price_range_aud=tuple(price_range),
            assumptions=assumptions,
        )
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"lead_quote draft_quote failed: {type(e).__name__}: {e}"])
        return {"ok": False, "error": "draft تولید نشد"}

    pdict = prop.to_dict() if hasattr(prop, "to_dict") else {"payload": {}}

    # ── enrich payload with structured data ─────────────────────────────
    pdict["payload"]["qt_number"] = qt_num
    pdict["payload"]["intake"] = intake.to_dict()
    pdict["payload"]["line_items"] = bd_dict["line_items"]
    pdict["payload"]["breakdown"] = {
        "labor_aud": bd_dict["labor_aud"],
        "material_aud": bd_dict["material_aud"],
        "subtotal_excl_gst": bd_dict["subtotal_excl_gst"],
        "gst": bd_dict["gst"],
        "total_incl_gst": bd_dict["total_incl_gst"],
        "max_deposit_nsw": bd_dict["max_deposit_nsw"],
    }

    # ── persist ────────────────────────────────────────────────────────
    rec = {
        "ts": opslib.now_iso(),
        "schema": "lead-quote.v1",
        "qt_number": qt_num,
        "version": 1,
        "attribution_id": str(attribution_id),
        "intake": intake.to_dict(),
        "breakdown": bd_dict,
        "proposal": pdict,
        "draft_only": True,
        "sent": False,
        "versions": [],  # append-only: previous versions stored here
    }
    path = _drafts_dir(state_dir) / f"{_safe(attribution_id)}.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(path) as lj:
            lj.write(rec)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"lead_quote persist failed: {type(e).__name__}: {e}"])
        return {"ok": False, "error": "draft ذخیره نشد"}

    return {
        "ok": True, "path": str(path), "qt_number": qt_num,
        "proposal_id": pdict.get("proposal_id"),
        "breakdown": bd_dict, "summary": render_quote_html(rec),
    }


# ─── revise_quote ───────────────────────────────────────────────────────────
def revise_quote(attribution_id: str, changes: dict,
                 state_dir=None) -> dict:
    """نسخهٔ جدید از یک کوتیشن. نسخهٔ قدیمی در versions[] حفظ (append-only).
    changes می‌تواند هر فیلدِ intake باشد (مثلاً {"size_m2": 150, "coat_count": 3}).
    خروجی: {ok, qt_number, version, breakdown, summary} یا {ok: False, error}."""
    if not attribution_id:
        return {"ok": False, "error": "attribution_id لازم است"}

    path = _drafts_dir(state_dir) / f"{_safe(attribution_id)}.json"
    rec = _read(path)
    if not rec:
        return {"ok": False, "error": "کوتیشن پیدا نشد"}

    # ── snapshot current into versions[] ────────────────────────────────
    versions = list(rec.get("versions") or [])
    versions.append({
        "version": rec.get("version", 1),
        "ts": rec.get("ts"),
        "qt_number": rec.get("qt_number"),
        "intake": rec.get("intake"),
        "breakdown": rec.get("breakdown"),
    })
    rec["versions"] = versions

    # ── apply changes to intake ───────────────────────────────────────
    old_intake = rec.get("intake") or {}
    new_intake_data = {**old_intake, **changes}
    new_intake = QuoteIntake(**{
        k: v for k, v in new_intake_data.items()
        if k in QuoteIntake.__dataclass_fields__
    })

    # ── re-estimate ───────────────────────────────────────────────────
    breakdown = estimate_price(new_intake)
    bd_dict = breakdown.to_dict()
    qt_num = _next_qt_num(state_dir)
    new_version = rec.get("version", 1) + 1

    # ── rebuild proposal payload ───────────────────────────────────────
    assumptions = list(breakdown.assumptions_auto)
    if new_intake.scope:
        assumptions.insert(0, f"Scope: {new_intake.scope[:300]}")

    rec["ts"] = opslib.now_iso()
    rec["qt_number"] = qt_num
    rec["version"] = new_version
    rec["intake"] = new_intake.to_dict()
    rec["breakdown"] = bd_dict
    rec["proposal"]["payload"].update({
        "qt_number": qt_num,
        "intake": new_intake.to_dict(),
        "line_items": bd_dict["line_items"],
        "scope": new_intake.scope or f"{new_intake.area_type} painting ({new_intake.size_m2:.0f}m²)",
        "price_range_aud": bd_dict["total_incl_gst"],
        "assumptions": assumptions,
        "breakdown": {
            "labor_aud": bd_dict["labor_aud"],
            "material_aud": bd_dict["material_aud"],
            "subtotal_excl_gst": bd_dict["subtotal_excl_gst"],
            "gst": bd_dict["gst"],
            "total_incl_gst": bd_dict["total_incl_gst"],
            "max_deposit_nsw": bd_dict["max_deposit_nsw"],
        },
    })

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(path) as lj:
            lj.write(rec)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"lead_quote revise persist failed: {type(e).__name__}: {e}"])
        return {"ok": False, "error": "نسخهٔ جدید ذخیره نشد"}

    return {
        "ok": True, "qt_number": qt_num, "version": new_version,
        "breakdown": bd_dict, "summary": render_quote_html(rec),
    }


# ─── quote_history ─────────────────────────────────────────────────────────
def quote_history(attribution_id: str, state_dir=None) -> dict:
    """تمام نسخ‌های یک کوتیشن. خروجی: {ok, versions: [...]} یا {ok: False, error}."""
    if not attribution_id:
        return {"ok": False, "error": "attribution_id لازم است"}
    path = _drafts_dir(state_dir) / f"{_safe(attribution_id)}.json"
    rec = _read(path)
    if not rec:
        return {"ok": False, "error": "کوتیشن پیدا نشد"}
    current = {
        "version": rec.get("version", 1),
        "ts": rec.get("ts"),
        "qt_number": rec.get("qt_number"),
        "breakdown": rec.get("breakdown"),
    }
    versions = list(rec.get("versions") or [])
    versions.append(current)
    return {"ok": True, "versions": versions, "n_versions": len(versions)}


# ─── render_quote_html ─────────────────────────────────────────────────────
def render_quote_html(rec: dict) -> str:
    """خلاصهٔ HTML برای تلگرام (پیش‌نویس — دستی بفرست)."""
    import html
    bd = rec.get("breakdown") or {}
    payload = (rec.get("proposal") or {}).get("payload") or {}
    try:
        lo, hi = float(bd.get("total_incl_gst", [0, 0])[0]), float(bd.get("total_incl_gst", [0, 0])[1])
    except (TypeError, ValueError, IndexError):
        lo, hi = 0.0, 0.0
    qt = html.escape(str(rec.get("qt_number") or "?"))
    aid = html.escape(str(rec.get("attribution_id") or "?"))
    ver = rec.get("version", 1)
    items = bd.get("line_items") or []
    intake = rec.get("intake") or {}

    lines = [
        f"📄 <b>کوت #{qt}</b> (v{ver} — draft، دستی بفرست)",
        f"• <b>قیمت (incl GST):</b> <code>AU${lo:,.0f} – {hi:,.0f}</code>",
        f"• attribution: <code>{aid}</code>",
    ]
    # line items summary
    for item in items[:5]:
        desc = html.escape(str(item.get("description", ""))[:60])
        sub = item.get("subtotal_aud") or [0, 0]
        try:
            slo, shi = float(sub[0]), float(sub[1])
        except (TypeError, ValueError, IndexError):
            slo, shi = 0.0, 0.0
        lines.append(f"  ↳ {desc}: <code>${slo:,.0f}–{shi:,.0f}</code>")
    if len(items) > 5:
        lines.append(f"  … +{len(items) - 5} ردیف دیگر")

    # deposit cap
    try:
        dep = float(bd.get("max_deposit_nsw", 0))
    except (TypeError, ValueError):
        dep = 0.0
    if dep > 0:
        lines.append(f"• <b>بیعانهٔ نهایتاً:</b> <code>AU${dep:,.0f}</code> (۱۰٪ · NSW §8)")

    lines.append("<i>قیمتِ قطعی و ارسال = تصمیمِ تو (پا فقط پیش‌نویس داد).</i>")
    return "\n".join(lines)


# ─── dashboard/lifecycle helpers (lead_draft API — حالا self-contained) ──────────
# LEG-04 (2026-07-13): ماژولِ lead_draft.py حذف شده بود؛ این wrapperها هنگام فراخوانی
# آن ماژولِ حذف‌شده را lazy-import می‌کردند و ImportError می‌دادند (pending/mark_sent/
# summary/__main__). منبعِ حقیقتِ همان wrapperها — دقیقاً همان persistence که
# create_quote اینجا می‌نویسد: state/legs/lead-drafts/*.json با کلیدِ `sent`. پس به‌جای
# import مرده، مستقیم روی همان دایرکتوری کار می‌کنیم (route to real persistence, بدونِ
# منطقِ کسب‌وکارِ نو). fail-soft مطلق. counterِ _qt_seq.json کوت نیست → رد می‌شود.
def pending(state_dir=None) -> list:
    """draftهای ارسال‌نشده (sent=False). fail-soft. (جایگزینِ lead_draft.pending.)"""
    out = []
    counter_name = f"{_safe(_QT_SEQ_KEY)}.json"
    try:
        for p in sorted(_drafts_dir(state_dir).glob("*.json")):
            if p.name == counter_name:
                continue                       # شمارندهٔ QT، نه draft
            r = _read(p)
            if r and r.get("schema") == "lead-quote.v1" and not r.get("sent"):
                out.append(r)
    except OSError:
        pass
    return out


def mark_sent(attribution_id: str, state_dir=None) -> bool:
    """draft را «ارسال‌شده» علامت بزن (وقتی مالک دستی فرستاد). idempotent، fail-soft.
    (جایگزینِ lead_draft.mark_sent.) هیچ ارسالِ واقعی — فقط علامتِ محلی."""
    if not attribution_id:
        return False
    path = _drafts_dir(state_dir) / f"{_safe(attribution_id)}.json"
    rec = _read(path)
    if not rec or rec.get("sent"):             # نبود یا قبلاً ارسال‌شده → idempotent
        return False
    rec["sent"] = True
    rec["sent_ts"] = opslib.now_iso()
    try:
        with opslib.LockedJson(path) as lj:
            lj.write(rec)
        return True
    except Exception:  # noqa: BLE001
        return False


def summary(state_dir=None) -> dict:
    """یک‌خطِ داشبورد: «N پیش‌نویسِ کوت منتظرِ ارسالِ دستی». (جایگزینِ lead_draft.summary.)"""
    n = len(pending(state_dir))
    line = (f"📄 {n} پیش‌نویسِ کوت منتظرِ ارسالِ دستی" if n
            else "📄 پیش‌نویسِ کوتِ معطلی نیست — 🟢")
    return {"n_pending": n, "line": line}


if __name__ == "__main__":
    print(json.dumps(pending(), ensure_ascii=False, indent=2))
