#!/usr/bin/env python3
"""attribution.py — چرخهٔ حیاتِ اعتبارِ دلار per-cell (Track B، offline/paper).

PROPOSAL (mintِ LEAD-YYYYMMDD-NNN + expected[EST]) → CLAIMED (کوت ارسال، {ref, amount}ِ انسانی)
→ CONFIRMED (فقط reconcile.py، تطبیق با feedِ مستقل) → ATTRIBUTED (اعتبار به cell؛ fitness این را می‌خواند).

ناوردی‌ها (قفل‌شده):
  • fitness هرگز چیزی زیرِ CONFIRMED نمی‌خواند.
  • CONFIRMED/ATTRIBUTED را فقط jobِ reconcile می‌نویسد (actor=reconcile-job) — نه ایجنت‌ها.
  • خودگزارشیِ ایجنت هرگز CONFIRMED نمی‌شود؛ ایجنت‌ها فقط PROPOSAL/CLAIMED می‌نویسند.
  • append-only در ledgerِ ژنوم با EVENT_TYPEِ موجودِ MONEY_ATTRIBUTION (v0.4.4).
  • پنجرهٔ انتساب ۷ روز (verdict آری)؛ اعتبار به cellِ زمانِ تصمیم (decision_date روی id).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opslib  # noqa: E402

ATTR_WINDOW_DAYS = 7
STATES = ("PROPOSAL", "CLAIMED", "CONFIRMED", "ATTRIBUTED", "CONFLICT")
RANK = {s: i for i, s in enumerate(STATES)}
CONFIRMED_STATES = ("CONFIRMED", "ATTRIBUTED")   # فقط این‌ها واردِ fitness می‌شوند
RECONCILE_ACTOR = "reconcile-job"


def _ledger():
    return opslib.genome_ledger()


def _partners_for(cell: str, partners=None):
    """partners[]/pct برای یک cell. اگر صریحاً داده نشد، از partners_default در budgets.yaml.
    نرمال‌سازی: مجموعِ pct باید ۱۰۰ باشد. خروجی: [{who, pct}]."""
    if partners is not None:
        # نرمال‌سازیِ صریح
        total = sum(float(p.get("pct", 0)) for p in partners) or 1
        return [{"who": p.get("who", "?"), "pct": round(float(p.get("pct", 0)) / total * 100, 2)}
                for p in partners]
    # از budgets.yaml (partners_default)
    try:
        b = opslib.load_budgets()
        defaults = (b.get("allocation") or {}).get("partners_default", {})
        # cell ممکن است به organ نگاشت شود (cell = lead.doer → organ = ?). سعی با cell مستقیم.
        # partner_defaults بر اساسِ organ هستند؛ اگر cell مستقیم نیست، organ را از organ_table بگیر.
        organs = opslib.organ_table()
        organ_for_cell = None
        for organ, cfg in organs.items():
            cells = cfg.get("cells") or []
            if cell in cells:
                organ_for_cell = organ
                break
        key = organ_for_cell or cell
        ps = defaults.get(key) or defaults.get(cell)
        if ps:
            return [{"who": p.get("who", "?"), "pct": float(p.get("pct", 0))} for p in ps]
    except Exception:  # noqa: BLE001
        pass
    # پیش‌فرض: ۱۰۰٪ صاحبِ نامشخص
    return [{"who": "unknown", "pct": 100.0}]


def mint_id(seq: int, day: str | None = None) -> str:
    return f"LEAD-{(day or opslib.today()).replace('-', '')}-{seq:03d}"


def _next_seq(day: str) -> int:
    """شمارهٔ بعدیِ همان روز از ledger (append-only، بی‌کش — ضدِ تصادمِ id)."""
    prefix = f"LEAD-{day.replace('-', '')}-"
    mx = 0
    for rec in _ledger().filter(event_type="MONEY_ATTRIBUTION"):
        aid = (rec.get("payload") or {}).get("attribution_id", "")
        if aid.startswith(prefix):
            try:
                mx = max(mx, int(aid.rsplit("-", 1)[1]))
            except (ValueError, IndexError):
                continue
    return mx + 1


def propose(cell: str, expected_aud: float, lead: str = "", day: str | None = None,
            partners: list | None = None) -> dict:
    """mintِ id + PROPOSAL. هرگز واردِ fitness نمی‌شود (expected فقط [EST]).
    partners: [{who, pct}] اختیاری — اگر نباشد، از partners_default در budgets.yaml."""
    day = day or opslib.today()
    aid = mint_id(_next_seq(day), day)
    payload = {
        "attribution_id": aid, "state": "PROPOSAL", "cell": cell,
        "expected_aud": round(float(expected_aud), 2), "amount_aud": 0.0,
        "lead": lead, "decision_date": day}
    if partners is not None:
        payload["partners"] = _partners_for(cell, partners)
    return _ledger().append("MONEY_ATTRIBUTION", payload, actor="attribution")


def claim(attribution_id: str, ref: str, amount_aud: float, day: str | None = None) -> dict:
    """کوت ارسال شد (انسان) + گزارشِ {ref, amount}. لازم ولی بی‌ارزش تا reconcile."""
    return _ledger().append("MONEY_ATTRIBUTION", {
        "attribution_id": attribution_id, "state": "CLAIMED",
        "ref": ref, "amount_aud": round(float(amount_aud), 2),
        "claim_date": day or opslib.today()}, actor="attribution")


def confirm(attribution_id: str, cell: str, amount_aud: float, matched: dict,
            partners: list | None = None) -> dict:
    """CONFIRMED (+ATTRIBUTED، single-touch 100٪). فقط reconcile.py صدا می‌زند.
    partners: [{who, pct}] — split سهمِ هر شریک را در ATTRIBUTED ثبت می‌کند."""
    lg = _ledger()
    amt = round(float(amount_aud), 2)
    rec = lg.append("MONEY_ATTRIBUTION", {
        "attribution_id": attribution_id, "state": "CONFIRMED", "cell": cell,
        "amount_aud": amt, "matched": matched, "confirm_date": opslib.today()},
        actor=RECONCILE_ACTOR)
    # partners را resolve کن و split بساز
    ps = _partners_for(cell, partners)
    split = {p["who"]: round(amt * p["pct"] / 100.0, 2) for p in ps}
    lg.append("MONEY_ATTRIBUTION", {
        "attribution_id": attribution_id, "state": "ATTRIBUTED", "cell": cell,
        "amount_aud": amt, "split": split, "partners": ps}, actor=RECONCILE_ACTOR)
    return rec


def conflict(attribution_id: str, reason: str, detail: dict | None = None) -> dict:
    """CONFLICT — مسیرِ اختلافِ انسان‌علامت‌خورده (نه از reconcileِ خودکار: آن، تطبیقِ ناقص را صرفاً
    UNMATCHED گزارش می‌کند و CONFIRMEDِ موجود را دست نمی‌زند). fold() این را چسبنده نگه می‌دارد تا
    رفعِ انسانی — یک id در CONFLICT هرگز واردِ fitness نمی‌شود."""
    return _ledger().append("MONEY_ATTRIBUTION", {
        "attribution_id": attribution_id, "state": "CONFLICT",
        "reason": reason, "detail": detail or {}}, actor=RECONCILE_ACTOR)


def fold() -> dict[str, dict]:
    """آخرین وضعیتِ هر attribution_id از ledger (append-only). CONFLICT چسبنده است."""
    latest: dict[str, dict] = {}
    for rec in _ledger().filter(event_type="MONEY_ATTRIBUTION"):
        p = rec.get("payload") or {}
        aid = p.get("attribution_id")
        if not aid:
            continue
        cur = latest.get(aid)
        if cur is None:
            latest[aid] = dict(p)
            continue
        if cur.get("state") == "CONFLICT":
            continue   # CONFLICT قفل می‌ماند تا رفعِ انسانی
        if p.get("state") == "CONFLICT" or RANK.get(p.get("state"), -1) >= RANK.get(cur.get("state"), -1):
            merged = dict(p)
            # carry-forwardِ فیلدهای هویتی که حالتِ بعدی حملشان نمی‌کند (مثلاً CLAIMED فیلد cell ندارد)
            for k in ("cell", "decision_date", "claim_date", "lead", "expected_aud"):
                if merged.get(k) is None and cur.get(k) is not None:
                    merged[k] = cur.get(k)
            latest[aid] = merged
    return latest


def confirmed_revenue(window_days: int | None = None) -> dict:
    """جمعِ دلارِ CONFIRMED/ATTRIBUTED per-cell + attribution_coverage. تنها سطحی که fitness می‌خواند."""
    latest = fold()
    by_cell: dict[str, float] = {}
    claimed = confirmed = 0
    for p in latest.values():
        st = p.get("state")
        if st == "CLAIMED":
            claimed += 1
        elif st in CONFIRMED_STATES:
            confirmed += 1
            claimed += 1    # CONFIRMED یعنی قبلاً claim شده بود
            c = p.get("cell", "unknown")
            by_cell[c] = round(by_cell.get(c, 0.0) + float(p.get("amount_aud", 0) or 0), 2)
    coverage = round(confirmed / claimed, 3) if claimed else None
    # by_partner: جمعِ AUD per partner از split در ATTRIBUTED
    by_partner: dict[str, float] = {}
    for p in latest.values():
        if p.get("state") in CONFIRMED_STATES:
            split = p.get("split") or {}
            if isinstance(split, dict):
                for who, amt in split.items():
                    by_partner[who] = round(by_partner.get(who, 0.0) + float(amt or 0), 2)
            else:
                # legacy (no split): کل به cell
                pass
    return {"by_cell": by_cell, "by_partner": by_partner,
            "attribution_coverage": coverage,
            "claimed": claimed, "confirmed": confirmed,
            "window_days": window_days or ATTR_WINDOW_DAYS}


if __name__ == "__main__":
    import json
    print(json.dumps(confirmed_revenue(), ensure_ascii=False, indent=2))
