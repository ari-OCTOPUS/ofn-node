#!/usr/bin/env python3
"""harvest_austender.py — keyless AusTender OCDS harvester → lead-inbox.

سرِ لولهٔ خشک (DAM-1 نقشهٔ تری‌اسکن): تنها تولیدکنندهٔ `state/legs/lead-inbox`
که هیچ کلید/رازی نمی‌خواهد. AusTender OCDS API عمومی و keyless است — برخلافِ
PlanningAlerts که کلید می‌خواهد. فقط GETِ عمومی + نوشتنِ فایلِ محلی.

پشتِ OCTOPUS_WIRE_HARVEST=1 (پیش‌فرض خاموش، عمداً بیرون از PAPER_FULL_FLAGS چون
تولیدکنندهٔ ورودیِ واقعی است). kill-switch مقدم. صفر ارسال، صفر خرج، صفر راز.
$0 · stdlib urllib · fail-soft · propose-only.

قرارداد صندوق (هم‌شکلِ lead_sense/lead_scorer): یک JSON dict، حداقل `description`
غیرخالی؛ اختیاری address/cost_of_development/lat/lng/applicant/url/source/day.
dedupِ پایین‌دست = هشِ description+address؛ این‌جا هم نامِ فایل هشِ محتوایی است.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib  # noqa: E402

# ─── flag ─────────────────────────────────────────────────────────────────────
FLAG_NAME = "OCTOPUS_WIRE_HARVEST"

# AusTender OCDS — findByDates/atmPublished بازهٔ [start,end]. عمومی، keyless.
_ENDPOINT = "https://api.tenders.gov.au/ocds/findByDates/atmPublished/{start}/{end}"
_MAX_PER_RUN = 25          # کرانِ ضدِ سیلِ صندوق در هر اجرا
_UA = "octopus-austender-harvester/0.1 (propose-only; local vault)"

# پیش‌فیلترِ ربطِ نقاشی — محافظه‌کار (فقط ربطِ روشن). lead_scorer پایین‌دست امتیازِ
# دقیق می‌دهد؛ این‌جا فقط جلوی سیلِ هزاران مناقصهٔ نامرتبطِ دولتی را می‌گیریم.
_PAINT_KW = (
    "paint", "repaint", "painting", "coating", "protective coating",
    "renovat", "refurbish", "restoration", "line marking", "linemarking",
    "surface preparation", "anti-graffiti",
)


def check_flag() -> bool:
    """OCTOPUS_WIRE_HARVEST=1 → فعال. بدون flag → no-op امن."""
    return os.environ.get(FLAG_NAME, "0") == "1"


def _inbox() -> Path:
    """مسیرِ صندوق — در زمانِ فراخوانی خوانده می‌شود (تست STATE_DIR را monkeypatch می‌کند)."""
    return opslib.STATE_DIR / "legs" / "lead-inbox"


def _is_relevant(text: str) -> bool:
    t = (text or "").lower()
    return any(kw in t for kw in _PAINT_KW)


def _get_json(url: str, timeout: int = 30) -> dict:
    """تنها نقطهٔ شبکه — GETِ عمومیِ keyless. در تست تزریق می‌شود (get_json)."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:   # فقط api.tenders.gov.au
        return json.loads(r.read().decode("utf-8"))


def fetch(days: int = 4, get_json=None) -> list:
    """releaseهای OCDSِ پنجرهٔ اخیر. fail-soft → []. get_json تزریق‌پذیر."""
    fetch_fn = get_json or _get_json
    t = date.today()
    s = t - timedelta(days=max(1, int(days)))
    url = _ENDPOINT.format(start=s.isoformat(), end=t.isoformat())
    try:
        d = fetch_fn(url)
    except Exception as e:  # noqa: BLE001 — شبکهٔ بد نباید ضربان را بکشد
        opslib.alert([f"harvest_austender fetch failed (non-fatal): {type(e).__name__}: {e}"])
        return []
    rels = d.get("releases") if isinstance(d, dict) else None
    return rels if isinstance(rels, list) else []


def _to_candidate(release: dict) -> "dict | None":
    """OCDS release → کاندیدِ صندوق، یا None (نامرتبط یا بی‌description).

    type-safe: فیلدهای OCDS ممکن است اسکالرِ خلافِ spec باشند (مثلاً value=5000 به‌جای
    {amount:5000})؛ `x or {}` فقطِ falsy را می‌گیرد نه wrong-type، پس صریح isinstance
    چک می‌کنیم تا یک releaseِ بدشکل کلِ batch را نکشد (بازبینیِ خصمانه ۲۰۲۶-۰۷-۱۷)."""
    if not isinstance(release, dict):
        return None
    tender = release.get("tender")
    if not isinstance(tender, dict):
        tender = {}
    title = str(tender.get("title") or "").strip()
    body = str(tender.get("description") or "").strip()
    desc = f"{title} — {body}" if title and body else (title or body)
    if not desc:
        return None
    if not _is_relevant(f"{title} {body}"):
        return None
    cand: dict = {"source": "austender", "description": desc[:600]}
    value = tender.get("value")
    val = value.get("amount") if isinstance(value, dict) else None
    if isinstance(val, (int, float)) and val > 0:
        cand["cost_of_development"] = float(val)   # سطحِ ارزشِ lead_scorer
    buyer = release.get("buyer")
    buyer_name = buyer.get("name") if isinstance(buyer, dict) else None
    if buyer_name:
        cand["applicant"] = str(buyer_name)[:120]
    uri = release.get("uri") or tender.get("id")
    if uri:
        cand["url"] = str(uri)[:300]
    dt = release.get("date")
    if dt:
        cand["day"] = str(dt)[:10]
    return cand


def _dedup_name(cand: dict) -> str:
    """نامِ فایلِ قطعی/idempotent — هشِ description+url (هم‌راستا با dedupِ lead_sense)."""
    key = (cand.get("description", "") + "\0" + cand.get("url", "")).encode("utf-8")
    return f"austender-{hashlib.sha256(key).hexdigest()[:16]}.json"


def _write_candidate(cand: dict) -> bool:
    """نوشتنِ اتمیکِ یک کاندید. idempotent؛ fail-soft. خروجی: نوشته شد؟"""
    inbox = _inbox()
    target = inbox / _dedup_name(cand)
    if target.exists() or list((inbox / "processed").glob(f"{target.stem}*")):
        return False   # قبلاً در صندوق یا پردازش‌شده
    try:
        inbox.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(cand, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, target)
        return True
    except (OSError, TypeError, ValueError):
        return False   # fail-soft: یک کاندیدِ خراب بقیه را نکشد


def harvest(days: int = 4, get_json=None) -> dict:
    """یک اجرا: fetch → filter → نوشتنِ صندوق. propose-only، صفر ارسال/خرج.

    این تابع نقطهٔ ورودِ ضربان هم هست — wiring فقط یک خطِ گیت‌دار صدایش می‌زند.
    خروجی: {fetched, relevant, written, note}."""
    if not check_flag():
        return {"fetched": 0, "relevant": 0, "written": 0,
                "note": "OCTOPUS_WIRE_HARVEST not set — no-op"}
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return {"fetched": 0, "relevant": 0, "written": 0, "note": "halted — no-op"}
    releases = fetch(days=days, get_json=get_json)
    relevant = written = 0
    for rel in releases:
        try:
            cand = _to_candidate(rel)
        except Exception:  # noqa: BLE001 — یک releaseِ بدشکل نباید کلِ batch را بکشد
            continue
        if cand is None:
            continue
        relevant += 1
        if written < _MAX_PER_RUN and _write_candidate(cand):
            written += 1
    return {"ts": opslib.now_iso(), "fetched": len(releases),
            "relevant": relevant, "written": written,
            "note": f"{written} lead(s) → lead-inbox از {len(releases)} releaseِ AusTender"}


if __name__ == "__main__":
    print(json.dumps(harvest(), ensure_ascii=False, indent=2))
