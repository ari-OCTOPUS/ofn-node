#!/usr/bin/env python3
"""lead_leg.py — Phase 4 · L-1: پای Lead-نقاشی (اصلِ صفر، درآمدِ #۱).

حلقهٔ paper کامل (Track B، OCTOPUS-MASTER-PLAN v1):
  intake (فرمِ موجود: تلگرام /lead یا panel /lead — بازاستفاده) →
  draft quote با attribution_id چاپ‌شده روی آن (از attribution.py: mint LEAD-YYYYMMDD-nnn) →
  reconcile.py یک CSVِ دستیِ اپراتور را در پنجرهٔ ۷ روزه match می‌کند →
  fitness فقط CONFIRMEDها را می‌شمارد.

هر تماسِ با مشتری human-gated است (از کانالِ P3). PII محلی می‌ماند، هرگز به LLM بیرونی.
propose-only: پا فقط draft تولید می‌کند؛ ارسال/تماس/پول همگی از کانالِ انسانی.

منبعِ حقیقت (خوانده شد):
  - attribution.py (propose/claim/CONFIRMED-states/fold) — بازاستفاده، از نو ننویس
  - reconcile.py (run: CSV match در پنجرهٔ ۷ روز) — بازاستفاده
  - approval_channel.py (TelegramApprovalChannel /lead) — intake از همان فرم
  - panel/server.py (submit_lead) — intake از همان فرم
additive: $0 آفلاین، stdlib-only. هیچ ماژولِ موجودی تغییر نکرد.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_BUDGET = _OPS / "budget"
for _p in (str(_OPS), str(_BUDGET)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from leg import Leg, Proposal, TaskPacket          # noqa: E402


# cell names هم‌سان با panel/server.py (LEAD_CELLS) و attribution
LEAD_CELLS = ("lead.doer", "ziman.doer", "crypto.doer")


class LeadLeg(Leg):
    """پای Lead-نقاشی. intake → draft_quote → claim. CONFIRMED کارِ reconcile است (نه پا).
    هر تماسِ بیرونی human-gated. این پا هرگز خودش نمی‌فرستد."""

    def __init__(self, packet: TaskPacket, organ_table: dict | None = None,
                 attribution=None, reconcile=None):
        super().__init__(packet, organ_table=organ_table)
        # lazy injection: attribution/reconcile قابل‌تزریق (تست) یا import واقعی
        self._attr = attribution
        self._rec = reconcile

    # -- وصلِ lazy به attribution/reconcile (همان الگوی leg._attribution_propose) --
    def _attr_mod(self):
        if self._attr is not None:
            return self._attr
        import attribution                              # noqa: WPS433
        return attribution

    def _rec_mod(self):
        if self._rec is not None:
            return self._rec
        import reconcile                                # noqa: WPS433
        return reconcile

    # -- intake: از هر منبعی (تلگرام /lead، panel /lead، یا فراخوانیِ مستقیم) -------
    def intake(self, lead_name: str, expected_aud: float, cell: str = "lead.doer",
               description: str = "", day: str | None = None) -> dict:
        """ثبتِ یک لید. فقط PROPOSAL mint می‌کند (attribution.propose) — نه پول، نه ارسال.
        ورودی نامعتبر → fail-closed (دیکشنریِ error، نه exception). cell ناشناخته → پیش‌فرض.
        day = تاریخِ تصمیم (YYYY-MM-DD)؛ None = امروز. برای پنجرهٔ ۷ روزِ reconcile."""
        name = (lead_name or "").strip()
        if not name:
            return {"ok": False, "error": "نام/کارِ لید لازم است"}
        try:
            exp = float(expected_aud)
        except (TypeError, ValueError):
            return {"ok": False, "error": "ارزشِ تخمینی باید عدد باشد (AUD)"}
        if exp < 0:
            return {"ok": False, "error": "ارزشِ تخمینی منفی نمی‌شود"}
        if cell not in LEAD_CELLS:
            cell = "lead.doer"
        try:
            desc = f"{name} — {description.strip()}" if description.strip() else name
            rec = self._attr_mod().propose(cell, exp, lead=desc, day=day)
        except Exception:                               # noqa: BLE001 — fail-closed
            return {"ok": False, "error": "ثبت نشد (خطای داخلی)"}
        aid = (rec.get("payload") or {}).get("attribution_id", "?") if isinstance(rec, dict) else "?"
        return {"ok": True, "attribution_id": aid, "cell": cell, "expected_aud": exp}

    # -- draft_quote: draft با attribution_id چاپ‌شده (Track B خروجیِ سنجش‌پذیر) ----
    def draft_quote(self, attribution_id: str, scope: str, price_range_aud: tuple[float, float],
                    assumptions: list[str] | None = None, hlc: tuple = (0, 0)) -> Proposal:
        """تولیدِ یک draft quote با attribution_id روی آن. فقط proposal — ارسال human-gated.
        format هم‌سان با OPS-01_quoting_estimation_framework.md: scope، included، NOT-included،
        assumptions، price range، legal placeholders. قیمتِ قطعی = تصمیمِ مالک، نه پا."""
        lo, hi = float(price_range_aud[0]), float(price_range_aud[1])
        if lo < 0 or hi < lo:
            lo, hi = 0.0, max(hi, 0.0)
        payload = {
            "attribution_id": attribution_id,            # چاپ‌شده روی quote (Track B carrier)
            "scope": str(scope)[:500],
            "price_range_aud": [round(lo, 2), round(hi, 2)],
            "assumptions": list(assumptions or [])[:20],
            "not_included": [  # ضدِ scope-creep (OPS-01 §6)
                "قراردادِ کتبی (الزامی برای کارهای >AU$5,000)",
                "تأییدِ نهاییِ قیمت (تصمیمِ مالک)",
                "بازدیدِ سایت (مرحلهٔ بعد)"],
            "legal_placeholders": [                       # OPS-09
                "شمارهٔ مجوز، ضمانتِ قانونی، Consumer Building Guide",
                "بیعانهٔ نهایتاً ۱۰٪"],
            "next_step": "تماس/بازدید — human-gated (از کانالِ P3)",
            "draft_only": True,                           # نه قیمتِ قطعی
        }
        return self.emit_proposal("draft_quote", payload, hlc=hlc)

    # -- claim: گزارشِ ارسالِ کوت (انسان) → CLAIMED (نه CONFIRMED) ----------------
    def claim(self, attribution_id: str, ref: str, amount_aud: float, day: str | None = None) -> dict:
        """ثبتِ اینکه کوت ارسال شد + {ref, amount}. فقط CLAIMED — CONFIRMED کارِ reconcile است.
        هرگز fitness نمی‌شود تا CSVِ match‌خور. ورودی نامعتبر → fail-closed."""
        if not attribution_id or not ref:
            return {"ok": False, "error": "attribution_id و ref الزامی‌اند"}
        try:
            amt = float(amount_aud)
        except (TypeError, ValueError):
            return {"ok": False, "error": "مبلغ باید عدد باشد"}
        if amt < 0:
            return {"ok": False, "error": "مبلغ منفی ممنوع"}
        try:
            rec = self._attr_mod().claim(attribution_id, ref, amt, day=day)
        except Exception:                                # noqa: BLE001
            return {"ok": False, "error": "claim ثبت نشد"}
        return {"ok": True, "state": "CLAIMED",
                "attribution_id": (rec.get("payload") or {}).get("attribution_id", attribution_id)}

    # -- reconcile_delegation: بررسیِ نتیجهٔ reconcile (نه خودِ CONFIRMED) ----------
    def confirmed_revenue(self) -> dict:
        """گزارشِ درآمدِ CONFIRMED از attribution.confirmed_revenue.
        پا CONFIRMED نمی‌نویسد — فقط آن را می‌خواند (فقط‌خواندنی)."""
        return self._attr_mod().confirmed_revenue()

    def run_reconcile(self, reconcile_dir=None, write: bool = True) -> dict:
        """اجرای reconcile با CSVِ اپراتور. CONFIRMED را فقط reconcile-job می‌نویسد.
        ⚑ برای معمار: در runtime واقعی، این فقط-readable wrapper است؛ write=True فقط
        در paper-test مجاز است. در production، reconcile یک jobِ جدا است، نه فراخوانیِ پا."""
        return self._rec_mod().run(reconcile_dir=reconcile_dir, write=write)


# ─── آگاهیِ ارگانیسم از این پا (۲۰۲۶-۰۷-۲۵، رأیِ مالک: «آگاهی اختاپوس به این پا») ──
def lead_status() -> dict:
    """snapshotِ فقط‌خواندنیِ پای درآمدیِ نقاشی — برای `business_legs` در ORGANISM-STATE.

    چرا ساخته شد: تا امروز `business_legs` چهار پا داشت (mining/crypto/accounting/
    knowledge) که **هر چهار** skeleton یا کهنه‌اند، و **تنها پای زندهٔ درآمدی — همین پا —
    در آن فهرست نبود.** یعنی خودآگاهیِ ارگانیسم پاهای مرده را می‌شمرد و کسب‌وکارِ واقعی
    را نمی‌دید. این تابع آن نقطهٔ کور را می‌بندد.

    قاعدهٔ صداقت: هر عدد از دیسک می‌آید و هیچ‌چیز حدس زده نمی‌شود. درآمدِ تأییدشده
    عمداً `None` است، نه صفر — چون حساب‌کتاب با رأیِ مالک (۲۰۲۶-۰۷-۲۵) **پارک** است و
    «۰» یک ادعای غلط می‌بود.

    live=True فقط با دو شرطِ ساختاری: (۱) هویتِ قابلِ‌فاکتور موجود باشد (ABN با فرمتِ
    معتبر + GST) و (۲) صندوقِ لید وجود داشته باشد تا لیدی بتواند وارد شود. هیچ‌کدام
    ادعای «درآمد دارد» نیست — ادعای «می‌تواند قانوناً فاکتور بدهد و لید بپذیرد» است.
    $0 · صفر spend · صفر outward · fail-soft کامل."""
    leg = "lead"
    out: dict = {"leg": leg, "live": False, "money_link": "active",
                 "confirmed_revenue_aud": None,
                 "note": "حساب‌کتاب با رأیِ مالک پارک است — درآمد None است نه صفر."}
    # (۱) هویتِ فاکتور — از همان منبعی که invoice.py می‌خواند (profileِ gitignored)
    ident = {"abn_valid": False, "gst_registered": False}
    try:
        import re as _re
        import invoice as _inv                       # noqa: WPS433 — هم‌پوشه
        _cfg = _inv._business_config() or {}
        ident["abn_valid"] = bool(_re.fullmatch(r"\d{2} \d{3} \d{3} \d{3}",
                                                str(_cfg.get("abn", "")).strip()))
        ident["gst_registered"] = bool(_inv._gst_registered())
        ident["has_bank_details"] = bool(str(_cfg.get("bank_details", "")).strip())
    except Exception:  # noqa: BLE001 — نبودِ هویت هرگز beat را نمی‌کشد
        pass
    out["identity"] = ident
    # (۲) صندوقِ لید — بی آن، هیچ لیدی وارد نمی‌شود (علتِ اثبات‌شدهٔ sensed=0)
    box_info = {"exists": False, "pending": 0, "processed": 0, "rejected": 0, "frozen_LD": 0}
    try:
        import opslib as _ol                          # noqa: WPS433
        box = _ol.STATE_DIR / "legs" / "lead-inbox"
        box_info["exists"] = box.is_dir()
        if box_info["exists"]:
            box_info["pending"] = sum(1 for p in box.glob("*.json")
                                      if not p.name.startswith(("_", "LD-")))
            box_info["frozen_LD"] = sum(1 for _ in box.glob("LD-*.json"))
            for sub, key in (("processed", "processed"), ("rejected", "rejected")):
                d = box / sub
                box_info[key] = sum(1 for _ in d.glob("*.json")) if d.is_dir() else 0
    except Exception:  # noqa: BLE001
        pass
    out["inbox"] = box_info
    # (۳) مصنوعاتِ پول روی دیسک — کوت و فاکتورِ ساخته‌شده (شمارش، بدونِ خواندنِ محتوا)
    arts = {"quotes": 0, "invoices": 0}
    try:
        import opslib as _ol2                         # noqa: WPS433
        for sub, key in (("lead-drafts", "quotes"), ("invoices", "invoices")):
            d = _ol2.STATE_DIR / "legs" / sub
            arts[key] = sum(1 for _ in d.glob("*.json")) if d.is_dir() else 0
    except Exception:  # noqa: BLE001
        pass
    out["artifacts"] = arts
    out["live"] = bool(ident["abn_valid"] and ident["gst_registered"]
                       and box_info["exists"])
    bits = [("هویتِ فاکتور ✅" if out["live"] else "هویت/صندوق ناقص"),
            f"صندوق: {box_info['pending']} در انتظار",
            f"کوت/فاکتور روی دیسک: {arts['quotes']}/{arts['invoices']}"]
    if box_info["frozen_LD"]:
        bits.append(f"⚠️ {box_info['frozen_LD']} لیدِ گیرافتاده در inboxِ FROZEN (LD-*)")
    if not ident.get("has_bank_details"):
        bits.append("⚠️ bank_details خالی → فاکتور قابلِ پرداخت نیست")
    out["signal"] = " · ".join(bits)
    return out
