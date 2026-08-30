#!/usr/bin/env python3
"""acct_review.py — موتورِ گفتگوی حسابداریِ تلگرام (دونه‌دونه، propose-only، 2026-07-16).

هدف (خواستهٔ مالک «یه حسابدارِ حرفه‌ای که فلکسبل سوال بپرسه»): از صفِ مرورِ حسابدار
مهم‌ترین تراکنش را می‌آورد، در تلگرام از مالک می‌پرسد «مالِ کیه؟ درآمد/خرج/حقوق/عبور؟»،
جوابِ مالک (دکمه یا متنِ آزاد) را با `attributor.apply_corrections` اعمال می‌کند
(review→confirmed = مسیرِ یادگیری)، بعد سراغِ بعدی. حالتِ جلسه در فایلِ gitignore.

معماری: این ماژول فقط **منطق + دادهٔ ساختاریافته** می‌دهد (question/result payload)؛
رندرِ متن/کیبوردِ تلگرام در approval_channel است (هم‌الگو با بقیهٔ کارت‌ها).

مرزهای سخت (تغییرناپذیر):
  * فقط پیشنهاد/ثبت — **هرگز** پولی جابه‌جا نمی‌شود، رمزِ بانک وارد نمی‌شود.
  * **هیچ مبلغی به هیچ LLM نمی‌رود.** تجزیهٔ متنِ آزاد اول قطعی (کلیدواژه)؛ اگر لازم شد
    fallbackِ ollamaِ محلی فقط descِ روی‌دستگاه را می‌بیند (مبلغ هرگز در prompt).
  * فقط مالک (whitelist در لایهٔ تلگرام) هدایت می‌کند.
  * نمایشِ تراکنش فقط به کانالِ خصوصیِ خودِ مالک (دادهٔ خودش، برای دسته‌بندی لازم) —
    شماره‌حسابِ ۸+رقمی از descِ نمایشی scrub می‌شود؛ هرگز به بیرون/LLMِ ابری نمی‌رود.
$0 · stdlib + opslib/money/txn_store/attributor · fail-soft.
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
import opslib        # noqa: E402
import money         # noqa: E402
import attributor    # noqa: E402

# کدهای کوتاه برای callback_data (کرانِ ۶۴بایتیِ تلگرام) ↔ مقدارِ کامل
OWNER_CODES = {"a": "armin", "b": "abbas", "z": "business", "u": "unknown"}
PTYPE_CODES = {"i": "income", "e": "expense", "w": "wage", "t": "transfer"}
OWNER_LABEL = {"armin": "آرمین", "abbas": "عباس", "business": "بیزنس", "unknown": "نامعلوم"}
PTYPE_LABEL = {"income": "درآمد", "expense": "خرج", "wage": "حقوق", "transfer": "عبور"}

# تجزیهٔ قطعیِ متنِ آزاد (اول این؛ مبلغ هرگز دخیل نیست — فقط تطبیقِ نیت)
_OWNER_KW = {
    "armin": ("armin", "آرمین", "ارمین", "من", "خودم", "mine", "me"),
    "abbas": ("abbas", "عباس", "همکار", "شریک"),
    "business": ("business", "بیزنس", "شرکت", "کار", "کسب"),
}
_PTYPE_KW = {
    "income": ("income", "درآمد", "درامد", "دریافت", "پول اومد", "واریز", "revenue"),
    "expense": ("expense", "خرج", "هزینه", "خرید", "پرداخت", "cost", "spend"),
    "wage": ("wage", "حقوق", "دستمزد", "مزد", "salary"),
    "transfer": ("transfer", "عبور", "انتقال", "pass", "passthrough", "رد کردم", "فرستادم برا عباس"),
}


def _session_path() -> Path:
    return opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "review-session.json"


def _store_path() -> Path:
    return opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "txn-store.json"


# ─── I/O (fail-soft, atomic) ─────────────────────────────────────────────────
def _load_store(path: Path | None = None) -> list[dict]:
    p = path or _store_path()
    try:
        doc = json.loads(p.read_text("utf-8")) if p.exists() else None
    except (OSError, ValueError):
        return []
    if isinstance(doc, dict):
        t = doc.get("txns") or doc.get("items") or []
        return t if isinstance(t, list) else []
    return doc if isinstance(doc, list) else []


def _save_store(txns: list[dict], path: Path | None = None) -> bool:
    try:
        import txn_store
        txn_store.save(txns, path or _store_path())
        return True
    except Exception:  # noqa: BLE001
        return False


def _load_session(path: Path | None = None) -> dict:
    p = path or _session_path()
    try:
        d = json.loads(p.read_text("utf-8")) if p.exists() else {}
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_session(sess: dict, path: Path | None = None) -> bool:
    p = path or _session_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(sess, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, p)
        return True
    except (OSError, TypeError, ValueError):
        return False


# ─── نمایشِ امنِ desc (فقط به مالک؛ شماره‌حسابِ بلند scrub) ──────────────────────
def _safe_desc(desc: object, limit: int = 60) -> str:
    s = str(desc or "")
    s = re.sub(r"\d{8,}", "…", s)          # شماره‌حساب‌مانند → حذف (مالک به vendor نیاز دارد نه شماره)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit]


# ─── انتخابِ صف (مهم‌ترین اول: |amount| نزولی) ─────────────────────────────────
def _queue_ids(txns: list[dict]) -> list[str]:
    q = [t for t in txns if isinstance(t, dict) and t.get("review") == "needs_review" and t.get("id")]
    q.sort(key=lambda t: -abs(int(_safe_cents(t.get("amount_cents", 0)))))
    return [str(t["id"]) for t in q]


def _safe_cents(x) -> int:
    try:
        return int(x)
    except (TypeError, ValueError):
        try:
            return int(float(x))
        except (TypeError, ValueError):
            return 0


def _by_id(txns: list[dict], tid: str) -> dict | None:
    for t in txns:
        if isinstance(t, dict) and str(t.get("id")) == str(tid):
            return t
    return None


# ─── API عمومی ───────────────────────────────────────────────────────────────
def start(store_path: Path | None = None, session_path: Path | None = None) -> dict:
    """جلسهٔ مرور را شروع/ری‌استارت کن. صف = needs_review به ترتیبِ |مبلغ|. اولین سوال را می‌دهد."""
    txns = _load_store(store_path)
    order = _queue_ids(txns)
    total_txns = sum(1 for t in txns if isinstance(t, dict))
    sess = {"active": bool(order), "idx": 0, "order": order,
            "started": opslib.now_iso(), "done": 0, "awaiting_free": False,
            "total_at_start": len(order), "network_size": total_txns}
    _save_session(sess, session_path)
    if not order:
        return {"kind": "empty", "message": "صفِ مرور خالی است — همه‌چیز دسته‌بندی شده ✅",
                "network_size": total_txns}
    return question(store_path=store_path, session_path=session_path)


def question(store_path: Path | None = None, session_path: Path | None = None) -> dict:
    """سوالِ فعلی (PII-کمینه، فقط برای مالک). kind=question | done | empty."""
    sess = _load_session(session_path)
    order = sess.get("order") if isinstance(sess.get("order"), list) else []
    txns = _load_store(store_path)                 # یک‌بار (نه در هر پرش)
    index = {str(t.get("id")): t for t in txns if isinstance(t, dict) and t.get("id")}
    idx = int(sess.get("idx", 0) or 0)
    # پرشِ iterative روی تراکنش‌های غیب‌شده (store عوض شده) — بدونِ recursion و بدونِ O(n²) disk
    moved = False
    while sess.get("active") and idx < len(order) and index.get(str(order[idx])) is None:
        idx += 1
        moved = True
    if moved:
        sess["idx"] = idx
        _save_session(sess, session_path)
    if not sess.get("active") or idx >= len(order):
        return {"kind": "done", "done": int(sess.get("done", 0)),
                "total": int(sess.get("total_at_start", 0)),
                "message": "این دور تمام شد ✅ — گزارش را با /finance ببین."}
    t = index.get(str(order[idx]))
    amt = _safe_cents(t.get("amount_cents", 0))
    # نردبانِ حدس (همه propose-only — مالک همیشه تأیید می‌کند):
    # ۱) attributorِ قطعی → ۲) حافظهٔ قواعدِ merchant (acct_memory، از تأییدهای خودِ مالک)
    # → ۳) suggestionِ ماندگارِ LLM (اگر قبلاً تولید شده) → ۴) LLMِ زنده (فقط با فلگ)
    guess_owner = str(t.get("owner", "unknown"))
    guess_pt = str(t.get("ptype", "unknown"))
    guess_basis = str(t.get("basis", ""))[:40]
    if guess_owner == "unknown" or guess_pt == "unknown":
        mem = _memory_suggest(t.get("desc"))
        if mem:
            guess_owner = mem["owner"] if guess_owner == "unknown" else guess_owner
            guess_pt = mem["ptype"] if guess_pt == "unknown" else guess_pt
            guess_basis = mem["basis"]
    if guess_owner == "unknown" or guess_pt == "unknown":
        sug = t.get("suggestion") if isinstance(t.get("suggestion"), dict) else None
        if sug:
            guess_owner = str(sug.get("owner", guess_owner)) if guess_owner == "unknown" else guess_owner
            guess_pt = str(sug.get("ptype", guess_pt)) if guess_pt == "unknown" else guess_pt
            guess_basis = str(sug.get("basis", "llm"))[:40]
    return {
        "kind": "question",
        "idx": idx, "n": idx + 1, "total": int(sess.get("total_at_start", len(order))),
        "done": int(sess.get("done", 0)),
        "txn_id": str(t.get("id")),
        "date": str(t.get("date", "")),
        "amount": money.fmt(amt),
        "sign": "ورودی" if amt > 0 else "خروجی",
        "desc": _safe_desc(t.get("desc", "")),
        "guess": {"owner": guess_owner, "ptype": guess_pt,
                  "owner_fa": OWNER_LABEL.get(guess_owner, guess_owner),
                  "ptype_fa": PTYPE_LABEL.get(guess_pt, "?"),
                  "basis": guess_basis},
    }


def _memory_suggest(desc) -> dict | None:
    """پیشنهادِ حافظهٔ قواعد (acct_memory) — fail-soft، propose-only."""
    try:
        import acct_memory  # noqa: WPS433 — هم‌پوشه
        return acct_memory.suggest(desc)
    except Exception:  # noqa: BLE001
        return None


def answer(owner_code: str, ptype_code: str, tid_token: str | None = None,
           note: str | None = None, store_path: Path | None = None,
           session_path: Path | None = None) -> dict:
    """جوابِ مالک را اعمال کن (apply_corrections = confirmed = یادگیری) و سوالِ بعدی را بده.

    **گاردِ هویت (فیکسِ audit HIGH):** tid_token = idِ همان تراکنشی که رویِ کارت نمایش داده شد.
    چون هر /review صف را از نو می‌سازد و idx را صفر می‌کند، گاردِ صرفاً موقعیتی (idx) می‌گذاشت
    تپِ یک کارتِ *قدیمی* به تراکنشِ *اشتباهِ* فعلی اعمال شود. حالا اگر tid_token با تراکنشِ
    فعلیِ صف نخواند → stale (کارتِ فعلی دوباره نشان داده می‌شود)، نه اعمالِ اشتباه."""
    owner = OWNER_CODES.get(str(owner_code))
    ptype = PTYPE_CODES.get(str(ptype_code))
    if owner is None or ptype is None:
        return {"kind": "error", "message": "پاسخِ نامعتبر."}
    sess = _load_session(session_path)
    cur = int(sess.get("idx", 0) or 0)
    order = sess.get("order") if isinstance(sess.get("order"), list) else []
    if not sess.get("active") or cur >= len(order):
        return {"kind": "done", "message": "این دور تمام شده."}
    tid = str(order[cur])
    # گاردِ هویت: توکنِ کارت باید *دقیقاً* با تراکنشِ فعلی بخواند (نه فقط موقعیت)
    if tid_token is not None and str(tid_token) != tid:
        r = question(store_path=store_path, session_path=session_path)
        return {**{k: v for k, v in r.items() if k != "kind"}, "kind": "stale",
                "message": "این پاسخ برای سوالِ گذشته بود — این سوالِ فعلی است، دوباره جواب بده."}
    txns = _load_store(store_path)
    if _by_id(txns, tid) is None:            # تراکنش غیب شده → پیش برو، بدونِ شمارش/«ثبت شد»ِ دروغ
        sess["idx"] = cur + 1
        sess["awaiting_free"] = False
        _save_session(sess, session_path)
        return {"kind": "vanished",
                "next": question(store_path=store_path, session_path=session_path)}
    corr = {tid: {"owner": owner, "ptype": ptype}}
    if note:
        corr[tid]["note"] = str(note)[:120]
    txns = attributor.apply_corrections(txns, corr)
    if not _save_store(txns, store_path):    # نوشتن شکست خورد → صداقت: نه پیش‌رفتن، نه «ثبت شد»
        return {"kind": "save-failed",
                "message": "❌ ثبت نشد (خطای نوشتنِ فایل) — دوباره همین را جواب بده."}
    sess["idx"] = cur + 1
    sess["done"] = int(sess.get("done", 0)) + 1
    sess["awaiting_free"] = False
    _save_session(sess, session_path)
    try:  # write-back به PocketSmith — فقط صفِ محلی (صفر شبکه اینجا)؛ فلگ‌خاموش = no-op کامل
        import ps_writeback
        _row = _by_id(txns, tid) or {}
        ps_writeback.enqueue(tid, owner, ptype, source=_row.get("source"))
    except Exception:  # noqa: BLE001 — write-back هرگز مرورِ مالک را نمی‌شکند
        pass
    nxt = question(store_path=store_path, session_path=session_path)
    return {"kind": "applied",
            "applied": {"owner": owner, "ptype": ptype,
                        "owner_fa": OWNER_LABEL.get(owner, owner),
                        "ptype_fa": PTYPE_LABEL.get(ptype, ptype)},
            "next": nxt}


def parse_free(text: str, store_path: Path | None = None,
               session_path: Path | None = None, use_local_llm: bool | None = None) -> dict:
    """متنِ آزادِ مالک → پیشنهادِ {owner, ptype} (مالک باید تأیید کند؛ auto-apply نمی‌شود).
    اول قطعی (کلیدواژه)؛ اگر مبهم و پرچمِ محلی روشن → fallbackِ ollamaِ محلی (descِ روی‌دستگاه،
    مبلغ هرگز در prompt). خروجی kind=proposal (نیاز به تأییدِ دکمه‌ای) یا need-clarify."""
    low = str(text or "").lower()
    owner = _match_kw(low, _OWNER_KW)
    ptype = _match_kw(low, _PTYPE_KW)
    src = "keyword"
    if (owner is None or ptype is None) and _local_llm_on(use_local_llm):
        g = _llm_guess(store_path, session_path)          # descِ روی‌دستگاه فقط
        owner = owner or g.get("owner")
        ptype = ptype or g.get("ptype")
        src = "keyword+local-llm"
    if owner is None and ptype is None:
        return {"kind": "need-clarify",
                "message": "نفهمیدم — بگو مالِ کیه (آرمین/عباس/بیزنس) و چیه (درآمد/خرج/حقوق/عبور)."}
    return {"kind": "proposal", "source": src,
            "owner": owner, "ptype": ptype,
            "owner_fa": OWNER_LABEL.get(owner, "?") if owner else "؟",
            "ptype_fa": PTYPE_LABEL.get(ptype, "?") if ptype else "؟",
            "owner_code": _code_of(owner, OWNER_CODES),
            "ptype_code": _code_of(ptype, PTYPE_CODES)}


def skip(store_path: Path | None = None, session_path: Path | None = None) -> dict:
    """این تراکنش را رها کن (بدونِ تغییر) و سراغِ بعدی برو."""
    sess = _load_session(session_path)
    sess["idx"] = int(sess.get("idx", 0) or 0) + 1
    sess["awaiting_free"] = False
    _save_session(sess, session_path)
    return question(store_path=store_path, session_path=session_path)


def stop(session_path: Path | None = None) -> dict:
    sess = _load_session(session_path)
    done = int(sess.get("done", 0))
    sess["active"] = False
    sess["awaiting_free"] = False           # هم‌راستا با answer/skip — پرچمِ سرگردان نماند
    _save_session(sess, session_path)
    return {"kind": "stopped", "done": done,
            "message": f"جلسه ایستاد. {done} تراکنش تأیید شد. هروقت خواستی /review بزن."}


def set_awaiting_free(flag: bool, session_path: Path | None = None) -> bool:
    sess = _load_session(session_path)
    if not sess:
        return False
    sess["awaiting_free"] = bool(flag)
    return _save_session(sess, session_path)


def is_awaiting_free(session_path: Path | None = None) -> bool:
    return bool(_load_session(session_path).get("awaiting_free"))


def is_active(session_path: Path | None = None) -> bool:
    return bool(_load_session(session_path).get("active"))


def progress(session_path: Path | None = None) -> dict:
    sess = _load_session(session_path)
    return {"active": bool(sess.get("active")), "done": int(sess.get("done", 0)),
            "idx": int(sess.get("idx", 0) or 0),
            "total": int(sess.get("total_at_start", 0))}


# ─── داخلی‌ها ─────────────────────────────────────────────────────────────────
def _match_kw(low: str, table: dict) -> str | None:
    for val, kws in table.items():
        if any(k in low for k in kws):
            return val
    return None


def _code_of(value, codes: dict) -> str | None:
    for c, v in codes.items():
        if v == value:
            return c
    return None


def _local_llm_on(override: bool | None) -> bool:
    if override is not None:
        return bool(override)
    return os.environ.get("OCTOPUS_WIRE_ACCT_REVIEW_LLM") == "1"


def _llm_guess(store_path, session_path) -> dict:
    """fallbackِ ollamaِ محلی (فقط با OCTOPUS_WIRE_ACCT_REVIEW_LLM=1): descِ تراکنشِ فعلی
    (روی‌دستگاه، **بدونِ مبلغ** — قراردادِ txn_categorize) → پیشنهادِ {owner, ptype}.
    نتیجه روی txn ذخیره می‌شود (suggestion) تا با pinِ sync ماندگار بماند — یک‌بار فکر،
    همیشه یادش. هر خطا → {} (نردبانِ قطعی برنده می‌ماند)."""
    try:
        sess = _load_session(session_path)
        order = sess.get("order") or []
        idx = int(sess.get("idx", 0) or 0)
        if idx >= len(order):
            return {}
        txns = _load_store(store_path)
        t = _by_id(txns, order[idx])
        if not t:
            return {}
        if isinstance(t.get("suggestion"), dict):        # قبلاً فکر شده — از حافظه
            return dict(t["suggestion"])
        import txn_categorize  # noqa: WPS433 — هم‌پوشه؛ مبلغ هرگز در prompt (قراردادش)
        txn_categorize.suggest([t], use_cloud=False)     # فقط ollamaِ محلی، propose-only
        sug = t.get("suggestion")
        if isinstance(sug, dict):
            _save_store(txns, store_path)                # ماندگار — ضدِ فراموشی
            return dict(sug)
        return {}
    except Exception:  # noqa: BLE001
        return {}


if __name__ == "__main__":
    print(json.dumps(progress(), ensure_ascii=False, indent=2))
