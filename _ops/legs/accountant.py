#!/usr/bin/env python3
"""accountant.py — ارکستراتورِ حسابدارِ مولتی‌ایجنت (2026-07-16، propose-only).

خط‌لولهٔ روش‌های ۲۰۲۷: txn_store.load_all (تجمیع، سنت، dedup، reconcile) →
attributor.attribute (قاعده‌محور: wage/transfer/vendor + صفِ بازبینی) → گزارشِ قطعی
(income/expense به تفکیکِ owner، **transferها حذف** تا دوبار شمرده نشوند؛ حقوقِ آرمین جدا).

مرزها: هرگز پول جابه‌جا نمی‌کند؛ مغز عدد نمی‌سازد (همه از money.py سنت)؛ هر تصمیمِ مبهم =
needs_review برای تأییدِ مالک. مقادیر فقط در فایلِ gitignore، نه echo در چت/بیرون.
$0 · stdlib · fail-soft.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib        # noqa: E402
import money         # noqa: E402
import txn_store     # noqa: E402
import attributor    # noqa: E402


def _store_path() -> Path:
    return opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "txn-store.json"


def _queue_path() -> Path:
    return opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "review-queue.json"


def _cfg_path() -> Path:
    return opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "categorize-config.json"


def apply_category_map(txns: list[dict]) -> list[dict]:
    """نگاشتِ دستهٔ PocketSmith → owner/ptype از configِ gitignore (روش ۶: قاعدهٔ قطعیِ اول).
    مثالِ config: {"category_owner_map": {"ArminNew": {"owner":"armin"},
    "AbbasNew": {"owner":"abbas"}, "salary": {"owner":"armin","ptype":"wage"}}}.
    نبودِ config → بی‌اثر (owner همان unknown). فقط owner/ptypeِ unknown را پر می‌کند."""
    try:
        cmap = json.loads(_cfg_path().read_text("utf-8")).get("category_owner_map", {})
    except (OSError, ValueError):
        cmap = {}
    if not cmap:
        return txns
    for t in txns:
        m = cmap.get(str(t.get("category", "")).strip())
        if not m:
            continue
        if t.get("owner", "unknown") == "unknown" and m.get("owner"):
            t["owner"] = m["owner"]
            t.setdefault("basis", "")
            t["basis"] = (t.get("basis") or "") + " cat-map:owner"
        if t.get("ptype", "unknown") == "unknown" and m.get("ptype"):
            t["ptype"] = m["ptype"]
    return txns


def report(txns: list[dict]) -> dict:
    """گزارشِ قطعیِ سنتی. transferها از income/expense حذف می‌شوند (pass-through).
    خروجی فقط تجمیعی — نه تراکنشِ منفرد."""
    per = {}                       # owner → {income, expense, wage, transfer}(cents)
    def slot(o):
        return per.setdefault(o, {"income_cents": 0, "expense_cents": 0,
                                  "wage_cents": 0, "transfer_cents": 0})
    for t in txns:
        if not isinstance(t, dict):
            continue
        owner = str(t.get("owner", "unknown"))
        pt = str(t.get("ptype", "unknown"))
        amt = _safe_cents(t.get("amount_cents", 0))     # fail-soft (رشتهٔ خراب → 0)
        s = slot(owner)
        if pt == "transfer":
            s["transfer_cents"] += abs(amt)          # فقط برای دید؛ در net نمی‌آید
        elif pt == "wage":
            s["wage_cents"] += abs(amt)
        elif pt == "income" or (pt == "unknown" and amt > 0):
            s["income_cents"] += amt
        elif pt == "expense" or (pt == "unknown" and amt < 0):
            s["expense_cents"] += -amt
    for o, s in per.items():
        s["net_cents"] = s["income_cents"] - s["expense_cents"]   # transfer/wage جدا
        # نمایشِ خوانا (لبِ خروجی)
        s["display"] = {k.replace("_cents", ""): money.fmt(v) for k, v in s.items() if k.endswith("_cents")}
    return per


# ─── خلاصهٔ PII-امن برای کارتِ /finance (هرگز نام/desc/شماره‌حساب/تراکنشِ خام) ─────────
_SAFE_CARD_KEYS = frozenset({
    "live", "unique", "as_of", "reconciled", "armin_net", "abbas_net",
    "assoc_total", "client_revenue", "wage_total", "wage_days", "wage_n",
    "counts", "signal", "note"})

# کفِ k-ناشناسی: هیچ تجمیعی که از کمتر از این تعداد تراکنش ساخته شده به کارت نمی‌رود
# (وگرنه سطلِ تک-تراکنشی = مبلغِ *خامِ* همان تراکنش لو می‌رود — به‌ویژه طرف‌حسابِ بی‌رضایت).
_K_ANON = 2
_MASK = "—"        # نشانگرِ «کم برای نمایشِ امن»


def _safe_cents(x) -> int:
    """amount_cents → int، fail-soft: رشتهٔ نامعتبر/None/اعشاری → 0 (هرگز raise).
    توجه: amount_cents از پیش «سنتِ صحیح» است؛ اینجا فقط int-coerce می‌شود، نه to_cents."""
    try:
        return int(x)
    except (TypeError, ValueError):
        try:
            return int(float(x))     # '12.0' → 12 (سنت)، ولی 'abc' → ValueError → 0
        except (TypeError, ValueError):
            return 0


def network_summary_card(path: Path | None = None, txns: list | None = None) -> dict:
    """تجمیعِ فقط‌خواندنی و **PII-امن** از شبکهٔ حسابدار برای کارتِ تلگرام.

    خروجی *هرگز* شاملِ این‌ها نیست: نامِ مشتری/طرف‌حساب (sume/maliheh/…)، desc، شماره‌حساب،
    یا تراکنشِ منفرد. فقط تجمیع: خالصِ آرمین/عباس (دو طرفِ باتوافق)، جمعِ کلِ طرف‌حساب‌ها
    (بدونِ نام)، جمعِ کلِ درآمدِ مشتری (بدونِ نام)، حقوق+روز، شمارش، وضعیتِ reconcile، تاریخ.
    مبالغ به‌صورتِ رشتهٔ نمایشی (سنت→'x.yy'). منبعِ غایب/خالی → live=False (صفر عددِ ساختگی).

    مرز: از txn-store ذخیره‌شده می‌خواند (نه pullِ زنده) — کارت باید سریع و بی‌شبکه باشد."""
    as_of = ""
    if txns is None:
        p = path or _store_path()
        try:
            doc = json.loads(p.read_text("utf-8")) if p.exists() else None
        except (OSError, ValueError):
            doc = None
        if not isinstance(doc, dict):
            return {"live": False, "signal": "شبکه ذخیره نشده",
                    "note": "txn-store هنوز ساخته نشده — اول شبکه build/persist شود."}
        txns = doc.get("txns") if isinstance(doc.get("txns"), list) else []
        as_of = str(doc.get("generated", ""))[:10]
    # شمارشِ واقعی (فقط dictها — هم‌قرارداد با loop/attributor.counts؛ ردیفِ خرابِ non-dict نشمار)
    real_unique = sum(1 for t in txns if isinstance(t, dict))
    if real_unique < _K_ANON:
        # سطلِ تک-ردیفی = مبلغِ خامِ همان تراکنش؛ برای محافظت اصلاً نمایش نده (صادقانه «کم»)
        return {"live": False, "signal": "دادهٔ کم",
                "note": "کمتر از حدِ k-ناشناسی — برای محافظت از تراکنشِ منفرد نمایش داده نمی‌شود."}

    per: dict = {}                       # owner → net cents (فقط جمعِ داخلی؛ نام‌ها بیرون نمی‌روند)
    per_n: dict = {}                     # owner → تعدادِ تراکنش (برای کفِ k-ناشناسی)
    client_rev = client_n = wage = wage_n = assoc_n = 0
    for t in txns:
        if not isinstance(t, dict):
            continue
        o = str(t.get("owner", "unknown"))
        a = _safe_cents(t.get("amount_cents", 0))   # fail-soft: رشتهٔ خراب → 0، هرگز crash
        pt = str(t.get("ptype", "unknown"))
        per[o] = per.get(o, 0) + a
        per_n[o] = per_n.get(o, 0) + 1
        if pt == "wage":
            wage += abs(a)
            wage_n += 1
        if o == "abbas" and a > 0 and pt in ("income", "unknown"):
            client_rev += a             # پروکسیِ درآمدِ مشتری — فقط جمع، بی‌نام
            client_n += 1
        if o not in ("armin", "abbas", "unknown"):
            assoc_n += 1                # تعدادِ تراکنشِ طرف‌حساب‌ها (شخصِ ثالثِ بی‌رضایت)
    # طرف‌حساب‌ها = هرکس جز armin/abbas/unknown، تجمیع‌شده (نامِ شخصِ ثالث echo نمی‌شود)
    assoc = sum(v for k, v in per.items() if k not in ("armin", "abbas", "unknown"))
    try:
        rec = txn_store.reconcile_report(txns)
        reconciled = bool(rec.get("tie_out_ok", False))
    except Exception:  # noqa: BLE001
        reconciled = False
    try:
        c = attributor.counts(txns)
        counts = {k: int(c.get(k, 0)) for k in ("confirmed", "auto", "needs_review")}
    except Exception:  # noqa: BLE001
        counts = {"confirmed": 0, "auto": 0, "needs_review": 0}

    def _kmask(cents: int, n: int) -> str:
        """مبلغِ تجمیعی فقط اگر از ≥K تراکنش ساخته شده باشد؛ وگرنه ماسک (ضدِ لوِ تک-ردیف)."""
        return money.fmt(cents) if n >= _K_ANON else _MASK

    card = {
        "live": True, "unique": real_unique, "as_of": as_of, "reconciled": reconciled,
        "armin_net": _kmask(per.get("armin", 0), per_n.get("armin", 0)),
        "abbas_net": _kmask(per.get("abbas", 0), per_n.get("abbas", 0)),
        "assoc_total": _kmask(assoc, assoc_n),
        "client_revenue": _kmask(client_rev, client_n),
        "wage_total": _kmask(wage, wage_n),
        "wage_days": (wage // 25000) if wage_n >= _K_ANON else _MASK,
        "wage_n": wage_n,
        "counts": counts,
    }
    # گاردِ سخت: فقط کلیدهای whitelist بیرون بروند (هیچ کلیدِ اتفاقیِ حاوی PII)
    return {k: v for k, v in card.items() if k in _SAFE_CARD_KEYS}


def _ps_flag_on() -> bool:
    """گرامرِ واحدِ فلگ (اسکن #19): 1/true/yes/on — هم‌رفتار با pocketsmith_api._flag_on."""
    return str(os.environ.get("OCTOPUS_WIRE_POCKETSMITH", "") or "").strip().lower() \
        in ("1", "true", "yes", "on")


def _content_hash(t: dict) -> str:
    """کلیدِ dedupِ محتوایی (روش ۳) — بینِ API و فایل که idهاشان فرق دارد.
    date|cents|desc|account — account هم داخل است (اسکن #17: دو تراکنشِ واقعیِ هم‌روز/
    هم‌مبلغ/هم‌desc روی دو حسابِ متفاوت نباید یکی شوند). این hash هرگز persist نمی‌شود
    (هر sync دو طرف را با همین فرمول می‌سازد) → تغییرش migration نمی‌خواهد.

    رفعِ باگِ دو-هش (2026-07-18، فاز ۵.۲): قبلاً این تابع desc را به [:20] و lower()
    می‌کرد و ۴۰ hex برمی‌گرداند، در حالی که txn_store._hash از full desc (case-sensitive)
    و ۱۶ hex استفاده می‌کرد. این تفاوت باعث می‌شد دو تراکنشِ مجزا با desc متفاوت فقط
    بعد از کاراکتر ۲۰، در build_network یکی شوند (suppress). حالا به txn_store._hash
    delegate می‌کنیم تا یک فرمول، یک رفتار."""
    import txn_store as _ts
    desc = str(t.get("desc", "") or "").strip()[:120]   # همان truncateِ _mk
    account = str(t.get("account", "") or "").strip()    # case-sensitive (مثل _hash)
    return _ts._hash(t.get("date", ""), t.get("amount_cents", 0), desc, account)


def _map_source_owner(txns: list[dict]) -> list[dict]:
    """طرف را از منبعِ CSV (csv:behzad→behzad) پر کن — شبکهٔ چند-طرفه. فقط ownerِ unknown."""
    for t in txns:
        if t.get("owner", "unknown") != "unknown":
            continue
        src = str(t.get("source", ""))
        if src.startswith("csv:"):
            name = src[4:].strip().lower().split()[0]
            if name and name != "armin":       # Armin.csv با API همپوشان است → API معتبرتر
                t["owner"] = name
    return txns


def build_network(start: str = "2025-12-08", end: str | None = None,
                  api_raw: list | None = None) -> list[dict]:
    """شبکهٔ کاملِ چند-طرفه: API زندهٔ PocketSmith (armin/abbas معتبر) + فایل‌ها (طرف‌حساب‌ها)،
    با content-dedup. fail-soft. api_raw (اختیاری) = تراکنش‌های از-قبل-fetch‌شده —
    /sync یک‌بار fetch می‌کند و به همه می‌دهد (اسکن #48: دو snapshotِ چندثانیه‌فاصله ≠ هم).
    **گاردِ pullِ ناقص (اسکن #18):** اگر fetch ok=False داد (صفحه‌ای شکست)، APIِ *ناقص*
    مبنای شبکه نمی‌شود — چون شبکهٔ ناقصِ live فایل‌های کامل را کنار می‌زد و تراکنش‌ها
    «ناپدید» می‌شدند. در آن حالت به فایل‌ها برمی‌گردیم + هشدار."""
    api = []
    try:
        if api_raw is not None:
            import pocketsmith_api  # noqa: WPS433
            api = pocketsmith_api.to_store_txns(api_raw)
        elif _ps_flag_on():
            import pocketsmith_api  # noqa: WPS433
            end = end or opslib.today()
            raw = pocketsmith_api.fetch_transactions(start, end)
            if isinstance(raw, dict) and raw.get("ok") is False:
                opslib.alert(["accountant: pullِ PocketSmith ناقص بود (ok=False) — "
                              "شبکه از فایل‌ها ساخته شد تا تراکنشی ناپدید نشود"])
            else:
                api = pocketsmith_api.to_store_txns(
                    raw.get("transactions", []) if isinstance(raw, dict) else raw)
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"accountant: PocketSmith pull خطا: {type(e).__name__}"])
    try:
        files = txn_store.load_all()
    except Exception:  # noqa: BLE001
        files = []
    # اگر API آمد، فایلِ pocketsmith (search قدیمی، زیرمجموعهٔ API) را کنار بگذار
    if api:
        files = [t for t in files if not str(t.get("source", "")).startswith("pocketsmith")]
    txns = apply_category_map(api) + _map_source_owner(files)
    seen, out = set(), []
    for t in txns:
        h = _content_hash(t)
        if h in seen:
            continue
        seen.add(h)
        out.append(t)
    return out


def _pin_confirmed() -> tuple[dict, str | None]:
    """(keep, error) — برچسب‌های confirmedِ مالک، کلید = **content-hash** (نه id):
    * مهاجرتِ id (فایل→PS-id) تأیید را نمی‌اندازد (همان محتوا → همان hash) — audit #2/#6.
    * محتوای عوض‌شده زیرِ همان id برچسبِ کهنه نمی‌گیرد (hash عوض شده → به /review برمی‌گردد،
      صادقانه) — audit #4.
    * storeِ *موجود ولی ناخوانا* → error (سکوت=پاک‌شدنِ همهٔ تأییدها — audit #3/#12)."""
    p = _store_path()
    if not p.exists():
        return {}, None
    try:
        doc = json.loads(p.read_text("utf-8"))
    except (OSError, ValueError) as e:
        return {}, f"storeِ موجود ناخواناست ({type(e).__name__}) — sync لغو تا تأییدها نپرند"
    keep: dict = {}
    for t in (doc.get("txns") or []) if isinstance(doc, dict) else []:
        if not isinstance(t, dict):
            continue
        if t.get("review") == "confirmed":
            keep[_content_hash(t)] = {k: t.get(k) for k in
                                      ("owner", "ptype", "category", "review", "basis", "note")
                                      if t.get(k) is not None}
        elif isinstance(t.get("suggestion"), dict):
            # ضدِ فراموشی (اسکنِ 2026-07-16): suggestionِ LLM روی ردیف‌های تأییدنشده هم
            # با content-hash سنجاق می‌شود — /sync دیگر پیشنهادهای تولیدشده را گم نمی‌کند.
            keep[_content_hash(t)] = {"suggestion": t["suggestion"]}
    return keep, None


def _restore_confirmed(txns: list, keep: dict) -> int:
    restored = 0
    for t in txns:
        if isinstance(t, dict):
            lbl = keep.get(_content_hash(t))
            if lbl:
                t.update(lbl)
                restored += 1
    return restored


def sync_network(start: str = "2025-12-08", end: str | None = None,
                 persist: bool = True, api_raw: list | None = None) -> dict:
    """رفرشِ شبکه **بدونِ ازدست‌دادنِ تأییدهای مالک**: attribute() هر ردیف را از نو مهر
    می‌زند؛ برچسب‌های مالک با content-hash سنجاق و بعدِ رفرش برگردانده می‌شوند.
    api_raw = fetchِ از-قبل (تک-pull در /sync — اسکن #48)."""
    keep, kerr = _pin_confirmed()
    if kerr:
        return {"ok": False, "error": kerr}
    txns = build_network(start, end, api_raw=api_raw)
    txns = apply_category_map(txns)
    txns = attributor.attribute(txns)
    restored = _restore_confirmed(txns, keep)
    rec = txn_store.reconcile_report(txns)
    if persist:
        try:
            txn_store.save(txns, _store_path())
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"save: {type(e).__name__}",
                    "restored_confirmed": restored}
    psw = {"ok": False, "note": "dry (persist=False) — write-back اجرا نشد."}
    if persist:  # رفرشِ dry نباید هیچ side-effectِ بیرونی داشته باشد (verify لنز ۴)
        try:  # write-backِ صف‌شدهٔ برچسب‌ها به PocketSmith (فلگ‌خاموش پیش‌فرض = no-op صادق)
            import ps_writeback
            psw = ps_writeback.flush()
        except Exception as e:  # noqa: BLE001 — write-back هرگز sync را نمی‌شکند
            psw = {"ok": False, "note": f"ps_writeback error — {type(e).__name__} (fail-soft)."}
    return {"ok": True, "unique": len(txns), "restored_confirmed": restored,
            "kept_from_before": len(keep), "counts": attributor.counts(txns),
            "reconciled": bool(rec.get("tie_out_ok")),
            "ps_writeback": {"ok": psw.get("ok"), "written": psw.get("written", 0),
                             "kept": psw.get("kept", 0), "note": psw.get("note", "")}}


def run(persist: bool = True, network: bool = True) -> dict:
    """کلِ خط‌لوله را اجرا کن و خلاصه بده (فقط شمارش/تجمیع). network=True → API+فایل شبکه.
    **حفظِ تأییدها (audit #5/#21):** run هم مثلِ sync_network برچسب‌های confirmedِ مالک را
    سنجاق/برمی‌گرداند — یک اجرای اتفاقیِ CLI دیگر هیچ تأییدی را پاک نمی‌کند."""
    keep, kerr = _pin_confirmed()
    if kerr and persist:
        return {"ok": False, "error": kerr}
    try:
        txns = build_network() if network else txn_store.load_all()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"load: {type(e).__name__}"}
    txns = apply_category_map(txns)          # PocketSmith دسته→owner اول (قطعی)
    txns = attributor.attribute(txns)
    _restore_confirmed(txns, keep)
    rec = txn_store.reconcile_report(txns)
    q = attributor.review_queue(txns)
    if persist:
        try:
            txn_store.save(txns, _store_path())
            # صفِ بازبینی برای مالک — فیلدهای برچسب‌زنی خالی، مهم‌ترین اول
            qp = _queue_path()
            qp.parent.mkdir(parents=True, exist_ok=True)
            slim = [{"id": t.get("id"), "date": t.get("date"),
                     "amount": money.fmt(t.get("amount_cents", 0)),
                     "desc": str(t.get("desc", ""))[:80],
                     "guess": {"owner": t.get("owner"), "ptype": t.get("ptype")},
                     "basis": t.get("basis", ""),
                     "__fill__": {"owner": "armin|abbas|business", "ptype": "income|expense|wage|transfer"}}
                    for t in q]
            tmp = qp.with_suffix(".json.tmp")
            tmp.write_text(json.dumps({"_note": "owner: هر ردیف را با owner/ptype درست پر کن، بعد apply کن",
                                       "count": len(slim), "items": slim}, ensure_ascii=False, indent=2), "utf-8")
            import os
            os.replace(tmp, qp)
        except Exception as e:  # noqa: BLE001
            opslib.alert([f"accountant persist خطا: {type(e).__name__}: {e}"])
    return {"ok": True, "counts": attributor.counts(txns),
            "reconcile": rec, "review_queue_size": len(q),
            "report": report(txns)}


def apply_review(corrections: dict, persist: bool = True) -> dict:
    """تصحیحاتِ مالک را اعمال کن (مسیرِ یادگیری). corrections = {id:{owner,ptype,category?}}."""
    txns = txn_store.load_all_from(_store_path()) if hasattr(txn_store, "load_all_from") else \
        json.loads(_store_path().read_text("utf-8")) if _store_path().exists() else []
    if isinstance(txns, dict):
        txns = txns.get("txns", txns.get("items", []))
    txns = attributor.apply_corrections(txns, corrections)
    if persist and _store_path().exists():
        txn_store.save(txns, _store_path())
    try:  # مسیرِ دومِ تأیید (review-queue.json) هم باید به PocketSmith سینک شود (verify لنز ۵)
        import ps_writeback
        by_id = {str(t.get("id")): t for t in txns if isinstance(t, dict)}
        for _tid, _corr in corrections.items():
            _row = by_id.get(str(_tid)) or {}
            ps_writeback.enqueue(_tid, (_corr or {}).get("owner"), (_corr or {}).get("ptype"),
                                 source=_row.get("source"))
    except Exception:  # noqa: BLE001 — write-back هرگز apply را نمی‌شکند
        pass
    return {"ok": True, "applied": len(corrections), "report": report(txns)}


if __name__ == "__main__":
    # پیش‌فرضِ CLI حالا dry است (audit #5: یک اجرای اتفاقی نباید store را بازنویسی کند)
    print(json.dumps(run(persist=("--persist" in sys.argv)), ensure_ascii=False, indent=2))
