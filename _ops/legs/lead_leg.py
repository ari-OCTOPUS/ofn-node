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
