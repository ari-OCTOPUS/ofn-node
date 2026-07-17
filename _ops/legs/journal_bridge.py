#!/usr/bin/env python3
"""journal_bridge.py — پلِ برچسب→دفتر (فازِ ۱ + سخت‌سازیِ auditِ دومِ 2026-07-16).

زنجیره: تراکنشِ تأییدشدهٔ مالک (/review) → پیشنهادِ ثبتِ دوطرفهٔ متوازن → تأییدِ دومِ
مالک (/books) → ledger_core.post_journal. **هیچ ثبتِ خودکار.**

سخت‌سازی‌های auditِ ۴۴-ایجنتی (۳۳ یافته):
  * **apply هرگز صف را باور نمی‌کند** (#1 قاتلِ مسموم‌سازی): در لحظهٔ ثبت، تراکنش از
    store دوباره لود، confirmed بودنش چک، entry از نو map و با صف مقایسه می‌شود —
    ناهم‌خوان → refresh + stale (نه ثبتِ کور). ikey همیشه بازساخته: txn-<id>.
  * **گاردِ حسابِ entity** (#7): فقط ردیف‌های حسابِ بانکیِ خودِ entity (source=pocketsmith*)
    ثبت‌پذیرند — CSVِ طرف‌حساب‌ها = پولِ حسابِ دیگران، skipِ صادق.
  * **transfer** (#8/#24): فقط برای pass-throughِ آرمین↔عباس (2200)؛ owner=business → skip؛
    کارت هشدارِ «اگر انتقالِ بینِ حساب‌های خودت است، رد کن» می‌گیرد.
  * **ضدِ double-postِ مهاجرتِ id** (#2/#6): قبل از پیشنهاد/ثبت، payload_hashِ entry با
    دفترِ موجود چک می‌شود → possible_dup_of روی کارت (هشدار به مالک، نه بلاکِ کور —
    دو تراکنشِ مشروعِ یکسان همچنان ممکن‌اند).
  * **صفِ قفل‌دار + ضدِ-corrupt** (#11/#13/#19/#20): همهٔ read-modify-writeها زیرِ
    LockedJson؛ فایلِ خرابِ موجود ≠ خالی — mutationها fail-closed، تصمیم‌های ردشده
    هرگز بی‌صدا زنده نمی‌شوند.
  * **بدونِ سرمایه‌سازیِ خاموش** (#16): hintِ ابزار→دارایی حذف شد (تصمیمِ asset-vs-expense
    با حسابدار). **بدونِ tax_code** (RD-002). scrubِ قوی‌ترِ شماره‌ها (#17).
  * rebuild پیشنهادهای proposed را با نگاشتِ تازه sync می‌کند و یتیم‌ها را stale می‌کند
    (#18/#22/#23)؛ _safe_cents فقط intِ خالص (#30)؛ preview از چارتِ profile (#29).
صف: personal/ledger/journal-proposals.json (gitignored). $0 · propose-only.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib       # noqa: E402
import money        # noqa: E402
import ledger_core  # noqa: E402

ENTITY_ID = "armin-abn"
# نگاشتِ owner→حسابِ خرج. قبلاً (تا 2026-07-18) hardcoded بود با نام‌های واقعیِ طرف‌حساب
# (PII در کد). حالا از categorize-config.json (gitignored) لود می‌شود؛ fallback به همین
# مقادیرِ پیش‌فرض اگه config غایب باشد. تغییر در config → تغییر در نگاشت، بدونِ دستِ کد.
_EXPENSE_BY_OWNER_DEFAULT = {"rent": "5200", "sume": "5100", "maliheh": "5100", "behzad": "5100"}
# hintِ دارایی (tool→1500) عمداً حذف شد: سرمایه‌سازی تصمیمِ حسابدار است (audit #16)
_CATEGORY_HINTS = (("material", "5000"), ("مصالح", "5000"), ("bunnings", "5000"))
_ENTITY_SOURCES = ("pocketsmith",)          # فقط حساب‌های بانکیِ خودِ entity ثبت‌پذیرند


def _config_path() -> Path:
    return opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "categorize-config.json"


def _expense_by_owner() -> dict:
    """نگاشتِ owner→account از categorize-config.json (gitignored). fail-soft → default."""
    try:
        d = json.loads(_config_path().read_text("utf-8"))
        m = d.get("expense_account_by_owner") if isinstance(d, dict) else None
        if isinstance(m, dict) and m:
            return {str(k): str(v) for k, v in m.items()}
    except (OSError, ValueError, TypeError):
        pass
    return dict(_EXPENSE_BY_OWNER_DEFAULT)


def _store_path() -> Path:
    return opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "txn-store.json"


def _queue_path() -> Path:
    return opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "ledger" / "journal-proposals.json"


def _load_txns(path: Path | None = None) -> list[dict]:
    p = path or _store_path()
    try:
        doc = json.loads(p.read_text("utf-8")) if p.exists() else None
    except (OSError, ValueError):
        return []
    if isinstance(doc, dict):
        t = doc.get("txns") or []
        return t if isinstance(t, list) else []
    return doc if isinstance(doc, list) else []


def _txn_by_id(tid: str, path: Path | None = None) -> dict | None:
    for t in _load_txns(path):
        if isinstance(t, dict) and str(t.get("id")) == str(tid):
            return t
    return None


def _load_queue(path: Path | None = None) -> tuple[dict, str | None]:
    """(queue, error). فایلِ موجود ولی خراب → error (mutationها fail-closed — audit #20)."""
    p = path or _queue_path()
    if not p.exists():
        return {}, None
    try:
        d = json.loads(p.read_text("utf-8"))
        return (d, None) if isinstance(d, dict) else ({}, "قالبِ صف خراب")
    except (OSError, ValueError) as e:
        return {}, f"صف ناخوانا ({type(e).__name__})"


def _save_queue(q: dict, path: Path | None = None) -> bool:
    p = path or _queue_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(q, ensure_ascii=False, indent=1), "utf-8")
        os.replace(tmp, p)
        return True
    except (OSError, TypeError, ValueError):
        return False


def _safe_cents(x) -> int:
    """فقط intِ خالص (نه bool/float/رشته) — قراردادِ store؛ ناسالم → 0 (skip می‌شود). #30"""
    return x if isinstance(x, int) and not isinstance(x, bool) else 0


def _scrub(desc: object, limit: int = 60) -> str:
    """شماره‌های ۵+رقمی حتی با فاصله/خط‌تیره (BSB/کارت/حساب) → … (audit #17). به دفترِ
    دائمی می‌رود — کمینهٔ عددِ شناسا."""
    s = str(desc or "")
    s = re.sub(r"\d[\d\s\-]{3,}\d", "…", s)
    return re.sub(r"\s+", " ", s).strip()[:limit]


def _expense_account(t: dict) -> str:
    o = str(t.get("owner", ""))
    ebo = _expense_by_owner()                 # از config (gitignored) — نه از hardcoded
    if o in ebo:
        return ebo[o]
    blob = (str(t.get("category", "")) + " " + str(t.get("desc", ""))).lower()
    for kw, acc in _CATEGORY_HINTS:
        if kw in blob:
            return acc
    return "6000"


def map_txn(t: dict) -> dict:
    """تراکنشِ confirmed → پیشنهادِ ثبت یا skipِ صادق."""
    if not isinstance(t, dict) or t.get("review") != "confirmed":
        return {"eligible": False, "reason": "confirmed نیست", "entry": None}
    tid = str(t.get("id") or "")
    if not tid:
        return {"eligible": False, "reason": "بی‌id", "entry": None}
    src = str(t.get("source", "") or "")
    if not any(src.startswith(s) for s in _ENTITY_SOURCES):
        # audit #7: ردیفِ حسابِ غیرِ entity (CSV طرف‌حساب) = پولِ بانکِ دیگران — ثبت در
        # دفترِ entity یعنی جعلِ جریانِ بانکی. دفترِ آن‌ها جداست.
        return {"eligible": False, "reason": "حسابِ غیرِ entity (source=csv) — دفترِ جدا", "entry": None}
    a = _safe_cents(t.get("amount_cents", 0))
    if a == 0:
        return {"eligible": False, "reason": "مبلغِ صفر/ناسالم", "entry": None}
    pt = str(t.get("ptype", ""))
    owner = str(t.get("owner", ""))
    amt = abs(a)
    note = None
    if pt == "income":
        if a < 0:
            return {"eligible": False, "reason": "income با علامتِ خروجی — مبهم", "entry": None}
        lines = [{"account": "1000", "debit_cents": amt, "credit_cents": 0},
                 {"account": "4000", "debit_cents": 0, "credit_cents": amt}]
    elif pt == "expense":
        if a > 0:
            return {"eligible": False, "reason": "expense با علامتِ ورودی — مبهم", "entry": None}
        acc = _expense_account(t)
        lines = [{"account": acc, "debit_cents": amt, "credit_cents": 0},
                 {"account": "1000", "debit_cents": 0, "credit_cents": amt}]
    elif pt == "wage":
        if a > 0:
            return {"eligible": False, "reason": "wageِ ورودی — سمتِ ثبت مبهم", "entry": None}
        lines = [{"account": "5300", "debit_cents": amt, "credit_cents": 0},
                 {"account": "1000", "debit_cents": 0, "credit_cents": amt}]
    elif pt == "transfer":
        if owner == "business":
            # audit #8: transferِ داخلیِ بیزنس ≠ بدهی/طلبِ عباس — نگاشتِ 2200 جعل می‌شود
            return {"eligible": False, "reason": "transferِ داخلی (business) — نگاشتِ دستی", "entry": None}
        note = "عبور → حسابِ خانوادگیِ عباس (2200، تسویهٔ داخلی). اگر انتقال بینِ حساب‌های خودت است، رد کن."
        if a > 0:
            lines = [{"account": "1000", "debit_cents": amt, "credit_cents": 0},
                     {"account": "2200", "debit_cents": 0, "credit_cents": amt}]
        else:
            lines = [{"account": "2200", "debit_cents": amt, "credit_cents": 0},
                     {"account": "1000", "debit_cents": 0, "credit_cents": amt}]
    else:
        return {"eligible": False, "reason": f"ptype ناشناخته: {pt}", "entry": None}
    entry = {"entity_id": ENTITY_ID, "date": str(t.get("date", "")),
             "memo": _scrub(t.get("desc", "")),
             "lines": lines,
             "evidence": [f"txn:{tid}", "review:owner-confirmed"],
             "idempotency_key": f"txn-{tid}"}
    coa = ledger_core.coa(ledger_core.load_profile())        # چارتِ واقعی، نه پیش‌فرض (#29)
    preview = [f"{'Dr' if ln['debit_cents'] else 'Cr'} {ln['account']} "
               f"{coa.get(ln['account'], '?')} {money.fmt(ln['debit_cents'] or ln['credit_cents'])}"
               for ln in lines]
    return {"eligible": True, "reason": None, "entry": entry, "preview": preview,
            "note": note, "gst_pending": True}


def _posted_payload_hashes(ledger_dir: Path | None) -> dict:
    """payload_hash → journal_id از دفترِ موجود (ضدِ double-postِ مهاجرتِ id — #2/#6)."""
    out: dict = {}
    try:
        for j in ledger_core._read_ledger(ledger_dir)["journals"]:
            ph = str(j.get("payload_hash") or "")
            if ph and not j.get("reverses"):
                out.setdefault(ph, str(j.get("journal_id")))
    except Exception:  # noqa: BLE001
        pass
    return out


def _entry_payload_hash(entry: dict) -> str:
    try:
        return ledger_core._payload_hash(entry)
    except Exception:  # noqa: BLE001
        return ""


def rebuild(store_path: Path | None = None, queue_path: Path | None = None,
            ledger_dir: Path | None = None) -> dict:
    """بازسازیِ صف (قفل‌دار): پیشنهادِ نو برای confirmedهای بی‌پیشنهاد + **sync پیشنهادهای
    proposed با نگاشتِ تازه** (تغییرِ برچسب/مبلغ → entry تازه؛ یتیم → stale — #18/#22).
    posted/rejected هرگز دست نمی‌خورند. صفِ خراب → fail-closed (#20)."""
    qp = queue_path or _queue_path()
    try:
        qp.parent.mkdir(parents=True, exist_ok=True)
        lock = opslib.LockedJson(qp)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"lock: {type(e).__name__}"}
    try:
        with lock:
            q, qerr = _load_queue(queue_path)
            if qerr:
                return {"ok": False, "error": qerr + " — بازبینیِ دستی؛ صف بازنویسی نشد"}
            props = q.setdefault("proposals", {})
            if not isinstance(props, dict):
                return {"ok": False, "error": "قالبِ صف خراب — بازبینیِ دستی"}
            txns = {str(t.get("id")): t for t in _load_txns(store_path)
                    if isinstance(t, dict) and t.get("id")}
            posted_hashes = _posted_payload_hashes(ledger_dir)
            built = refreshed = staled = 0
            skipped: dict = {}
            confirmed = 0
            # ۱) sync پیشنهادهای proposed موجود با وضعِ فعلیِ store
            for tid, p in list(props.items()):
                if not isinstance(p, dict) or p.get("status") != "proposed":
                    continue
                t = txns.get(tid)
                m = map_txn(t) if t is not None else {"eligible": False, "reason": "تراکنش غایب"}
                if not m["eligible"]:
                    p["status"] = "stale"
                    p["stale_reason"] = m["reason"]
                    staled += 1
                    continue
                if p.get("entry") != m["entry"]:
                    p.update({"entry": m["entry"], "preview": m["preview"],
                              "note": m.get("note"),
                              "amount": money.fmt(_safe_cents(t.get("amount_cents", 0))),
                              "desc": _scrub(t.get("desc", "")), "date": str(t.get("date", "")),
                              "owner": str(t.get("owner", "")), "ptype": str(t.get("ptype", "")),
                              "updated": opslib.now_iso()})
                    refreshed += 1
                ph = _entry_payload_hash(p.get("entry") or {})
                p["possible_dup_of"] = posted_hashes.get(ph)
            # ۲) پیشنهادِ نو برای confirmedهای بی‌پیشنهاد
            for tid, t in txns.items():
                if t.get("review") != "confirmed":
                    continue
                confirmed += 1
                if tid in props:
                    continue
                m = map_txn(t)
                if not m["eligible"]:
                    skipped[m["reason"]] = skipped.get(m["reason"], 0) + 1
                    continue
                ph = _entry_payload_hash(m["entry"])
                props[tid] = {"txn_id": tid, "status": "proposed",
                              "date": str(t.get("date", "")),
                              "amount": money.fmt(_safe_cents(t.get("amount_cents", 0))),
                              "desc": _scrub(t.get("desc", "")),
                              "owner": str(t.get("owner", "")), "ptype": str(t.get("ptype", "")),
                              "entry": m["entry"], "preview": m["preview"],
                              "note": m.get("note"), "gst_pending": True,
                              "possible_dup_of": posted_hashes.get(ph),
                              "created": opslib.now_iso()}
                built += 1
            ok = _save_queue(q, queue_path)
    except TimeoutError:
        return {"ok": False, "error": "قفلِ صف مشغول است — retry"}
    return {"ok": ok, "built": built, "refreshed": refreshed, "staled": staled,
            "confirmed_total": confirmed, "skipped": skipped,
            "pending": sum(1 for p in props.values()
                           if isinstance(p, dict) and p.get("status") == "proposed")}


def pending(queue_path: Path | None = None) -> list[dict]:
    q, qerr = _load_queue(queue_path)
    if qerr:
        return []
    props = q.get("proposals") or {}
    out = [p for p in props.values() if isinstance(p, dict) and p.get("status") == "proposed"]
    out.sort(key=lambda p: (p.get("date", ""), str(p.get("txn_id", ""))))
    return out


def get(txn_id: str, queue_path: Path | None = None) -> dict | None:
    q, qerr = _load_queue(queue_path)
    if qerr:
        return None
    p = (q.get("proposals") or {}).get(str(txn_id))
    return p if isinstance(p, dict) else None


def apply(txn_id: str, profile: dict | None = None, queue_path: Path | None = None,
          ledger_dir: Path | None = None, store_path: Path | None = None,
          actor: str = "owner") -> dict:
    """تأییدِ مالک → ثبت. **صف باور نمی‌شود** (#1): تراکنش از store دوباره لود و confirmed
    چک می‌شود، entry از نو map و باید با صف بخواند (ناهم‌خوان → stale-refresh، نه ثبت).
    قفل‌دار (#11/#19). موفق → status=posted."""
    qp = queue_path or _queue_path()
    try:
        lock = opslib.LockedJson(qp)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "errors": [f"lock: {type(e).__name__}"]}
    try:
        with lock:
            q, qerr = _load_queue(queue_path)
            if qerr:
                return {"ok": False, "errors": [qerr + " — بازبینیِ دستی"]}
            props = q.get("proposals") or {}
            p = props.get(str(txn_id))
            if not isinstance(p, dict) or p.get("status") != "proposed":
                return {"ok": False, "errors": ["پیشنهادِ ناشناخته یا قبلاً تصمیم‌گرفته"]}
            # بازاشتقاق از منبعِ حقیقت — نه از صف
            t = _txn_by_id(txn_id, store_path)
            if t is None or t.get("review") != "confirmed":
                p["status"] = "stale"
                p["stale_reason"] = "تراکنش دیگر confirmed/موجود نیست"
                _save_queue(q, queue_path)
                return {"ok": False, "stale": True,
                        "errors": ["تراکنش دیگر تأییدشده نیست — پیشنهاد stale شد"]}
            m = map_txn(t)
            if not m["eligible"]:
                p["status"] = "stale"
                p["stale_reason"] = m["reason"]
                _save_queue(q, queue_path)
                return {"ok": False, "stale": True, "errors": [f"دیگر ثبت‌پذیر نیست: {m['reason']}"]}
            if p.get("entry") != m["entry"]:
                # آنچه مالک روی کارت دید ≠ آنچه الان درست است → refresh و دوباره نشان بده
                p.update({"entry": m["entry"], "preview": m["preview"],
                          "note": m.get("note"), "updated": opslib.now_iso(),
                          "amount": money.fmt(_safe_cents(t.get("amount_cents", 0))),
                          "desc": _scrub(t.get("desc", ""))})
                _save_queue(q, queue_path)
                return {"ok": False, "stale": True,
                        "errors": ["تراکنش از زمانِ کارت عوض شده — کارتِ تازه را ببین و دوباره تأیید کن"]}
            prof = profile if profile is not None else ledger_core.load_profile()
            r = ledger_core.post_journal(m["entry"], prof, ledger_dir,
                                         reason=f"books-approve txn:{txn_id}", actor=actor)
            if not r.get("ok"):
                return r
            p["status"] = "posted"
            p["journal_id"] = r.get("journal_id")
            p["decided"] = opslib.now_iso()
            saved = _save_queue(q, queue_path)
    except TimeoutError:
        return {"ok": False, "errors": ["قفلِ صف مشغول است — retry"]}
    out = {"ok": True, "journal_id": r.get("journal_id"),
           "duplicate": bool(r.get("duplicate", False))}
    if not saved:
        out["warn"] = "صف ذخیره نشد — ikey=txn-id ثبتِ دوباره را می‌بندد؛ رفرشِ بعدی ترمیم می‌کند"
    return out


def reject(txn_id: str, reason: str = "", queue_path: Path | None = None) -> dict:
    qp = queue_path or _queue_path()
    try:
        lock = opslib.LockedJson(qp)
        with lock:
            q, qerr = _load_queue(queue_path)
            if qerr:
                return {"ok": False, "errors": [qerr]}
            p = (q.get("proposals") or {}).get(str(txn_id))
            if not isinstance(p, dict) or p.get("status") != "proposed":
                return {"ok": False, "errors": ["پیشنهادِ ناشناخته یا قبلاً تصمیم‌گرفته"]}
            p["status"] = "rejected"
            p["reject_reason"] = str(reason or "")[:120]
            p["decided"] = opslib.now_iso()
            return {"ok": _save_queue(q, queue_path)}
    except TimeoutError:
        return {"ok": False, "errors": ["قفلِ صف مشغول است — retry"]}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "errors": [f"خطا: {type(e).__name__}"]}


def stats(queue_path: Path | None = None) -> dict:
    q, qerr = _load_queue(queue_path)
    props = (q.get("proposals") or {}) if not qerr else {}
    c: dict = {"proposed": 0, "posted": 0, "rejected": 0, "stale": 0,
               "posted_gst_pending": 0, "queue_error": qerr}
    for p in props.values():
        if isinstance(p, dict):
            st = str(p.get("status"))
            c[st] = c.get(st, 0) + 1
            if st == "posted" and p.get("gst_pending"):
                c["posted_gst_pending"] += 1
    return c


if __name__ == "__main__":
    print(json.dumps({"stats": stats(), "pending": len(pending())}, ensure_ascii=False))
