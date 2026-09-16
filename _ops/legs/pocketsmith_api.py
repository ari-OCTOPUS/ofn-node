#!/usr/bin/env python3
"""pocketsmith_api.py — کلاینتِ فقط‌خواندنیِ PocketSmith API v2 (2026-07-16).

منبعِ زندهٔ حسابداری: PocketSmith تراکنش‌های *نیمه‌دسته‌بندی‌شده* مالک را نگه می‌دارد
(هر تراکنش category + labels دارد — همان دسته‌بندیِ دستیِ خودِ مالک). این کلاینت آن‌ها را
می‌کشد و به schemaِ txn_store می‌ریزد تا اختاپوس روی «حقیقتِ زمینیِ خودِ مالک» بنشیند، نه حدس.

خط‌قرمزهای سخت (این ماژول هرگز نقض نمی‌کند):
  • فقط GET — هرگز POST/PUT/DELETE به PocketSmith. صفر حرکتِ مالی، صفر نوشتن روی حساب.
  • کلید (POCKETSMITH_API_KEY) فقط از os.environ (بعد از env_loader.load_env) خوانده می‌شود؛
    مقدارش هرگز log/echo/print/return نمی‌شود — نه در note، نه در exception، نه در __main__.
  • پشتِ فلگِ OCTOPUS_WIRE_POCKETSMITH (پیش‌فرض خاموش → no-op، صفر شبکه).
  • fail-soft مطلق: نبودِ کلید / rate-limit / timeout / خطای شبکه → خروجیِ خالیِ صادق،
    هرگز crash. propose-only: sync فقط فایلِ انبار را می‌نویسد؛ صفر side-effect بیرونی.

هدر احراز: `X-Developer-Key: <POCKETSMITH_API_KEY>` (developer key فقط‌خواندنی).
پایه: https://api.pocketsmith.com/v2
$0 آفلاین در تست · stdlib-only (urllib) · بدونِ SDK/requests.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/legs
_OPS = _HERE.parent
for _p in (str(_HERE), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import money                                       # noqa: E402 — موتورِ سنتِ صحیح (integer cents)

# ─── ثابت‌ها ─────────────────────────────────────────────────────────────────
BASE = "https://api.pocketsmith.com/v2"
FLAG = "OCTOPUS_WIRE_POCKETSMITH"                  # پیش‌فرض خاموش → no-op
KEY_ENV = "POCKETSMITH_API_KEY"                    # نامِ متغیر (فقط نام؛ مقدار هرگز echo نمی‌شود)
SOURCE = "pocketsmith-api"                         # برچسبِ منبع در انبار (جدا از اکسپورتِ xlsx)
_DEFAULT_TIMEOUT = 30                              # ثانیه
_MAX_RETRIES = 3                                   # سقفِ backoffِ 429
_MAX_PAGES = 1000                                  # گاردِ ضدِ حلقهٔ بی‌پایانِ pagination


def _sleep(seconds: float) -> None:
    """seam برای تست (backoffِ 429 بدونِ خوابِ واقعی override می‌شود)."""
    time.sleep(seconds)


# ─── فلگ + کلید ──────────────────────────────────────────────────────────────
def _flag_on() -> bool:
    """آیا OCTOPUS_WIRE_POCKETSMITH روشن است؟ (پیش‌فرض خاموش)."""
    return str(os.environ.get(FLAG, "")).strip().lower() in {"1", "true", "yes", "on"}


def _api_key() -> str | None:
    """کلید را از os.environ بخوان (بعد از تلاش برای load_env). هرگز مقدار را برنمی‌گرداند
    به‌جز به‌عنوانِ هدرِ داخلی؛ اگر نبود → None (فراخوان‌ها fail-soft می‌شوند)."""
    try:
        import env_loader
        env_loader.load_env()
    except Exception:  # noqa: BLE001 — نبودِ .env نباید کلاینت را بکشد
        pass
    val = os.environ.get(KEY_ENV)
    return val or None


# ─── لایهٔ HTTP (فقط GET) ─────────────────────────────────────────────────────
def _build_url(path: str, params: dict | None = None) -> str:
    """path نسبی → BASE+path؛ URLِ کاملِ (http…) دست‌نخورده. paramهای None حذف می‌شوند."""
    url = path if path.startswith("http") else BASE + path
    if params:
        q = {k: v for k, v in params.items() if v is not None}
        if q:
            sep = "&" if "?" in url else "?"
            url = url + sep + urllib.parse.urlencode(q)
    return url


def _get(path: str, params: dict | None = None, *, key: str | None = None,
         timeout: int = _DEFAULT_TIMEOUT, max_retries: int = _MAX_RETRIES) -> dict:
    """یک GETِ فقط‌خواندنی. خروجی همیشه dictِ صادق:
      {"ok":bool, "status":int, "data":<json|None>, "link":<Link header|None>, "note":str}
    429 → backoff (Retry-After را محترم می‌شمارد)؛ timeout/شبکه/HTTP-error → ok=False fail-soft.
    کلید در هدرِ X-Developer-Key می‌رود و هرگز در خروجی/note ظاهر نمی‌شود."""
    key = key or _api_key()
    if not key:
        return {"ok": False, "status": 0, "data": None, "link": None,
                "note": f"{KEY_ENV} تنظیم نیست — no-op (کلیدِ فقط‌خواندنی لازم است)."}
    url = _build_url(path, params)
    attempt = 0
    while True:
        req = urllib.request.Request(url, method="GET", headers={
            "X-Developer-Key": key,
            "Accept": "application/json",
            "User-Agent": "octopus-accounting-readonly/1.0",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                try:
                    link = resp.headers.get("Link")
                except Exception:  # noqa: BLE001
                    link = None
                data = json.loads(body.decode("utf-8")) if body else None
                return {"ok": True, "status": getattr(resp, "status", 200) or 200,
                        "data": data, "link": link, "note": "ok"}
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries:
                attempt += 1
                try:
                    ra = int((e.headers.get("Retry-After") if e.headers else None) or 0)
                except (TypeError, ValueError):
                    ra = 0
                _sleep(min(ra if ra > 0 else 2 ** attempt, 60))
                continue
            reason = "rate-limit (429)" if e.code == 429 else f"HTTP {e.code}"
            return {"ok": False, "status": e.code, "data": None, "link": None,
                    "note": f"خطای API — {reason} (fail-soft)."}
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            return {"ok": False, "status": 0, "data": None, "link": None,
                    "note": f"شبکه/timeout ناموفق — {type(e).__name__} (fail-soft)."}


def _parse_next_link(link_header: str | None) -> str | None:
    """هدرِ Link را برای rel="next" پارس کن → URLِ صفحهٔ بعد یا None.
    قالب: '<https://…?page=2>; rel="next", <…>; rel="last"'."""
    if not link_header:
        return None
    for part in link_header.split(","):
        seg = part.strip()
        if 'rel="next"' in seg or "rel=next" in seg:
            lt, gt = seg.find("<"), seg.find(">")
            if lt != -1 and gt != -1 and gt > lt:
                return seg[lt + 1:gt]
    return None


# ─── endpointهای عمومی (همه فقط GET، همه پشتِ فلگ) ────────────────────────────
def me(*, key: str | None = None, timeout: int = _DEFAULT_TIMEOUT) -> dict:
    """GET /me — تأییدِ کارکردِ کلید + گرفتنِ user id.
    خروجی: {"ok","wired","user_id","note"}. فلگ خاموش → wired=False no-op."""
    if not _flag_on():
        return {"ok": False, "wired": False, "user_id": None,
                "note": f"فلگِ {FLAG} خاموش است — no-op (صفر شبکه)."}
    r = _get("/me", key=key, timeout=timeout)
    if not r["ok"]:
        return {"ok": False, "wired": True, "user_id": None, "note": r["note"]}
    data = r["data"] or {}
    uid = data.get("id")
    return {"ok": uid is not None, "wired": True, "user_id": uid,
            "note": "ok" if uid is not None else "پاسخِ /me بدونِ id."}


def list_accounts(user_id, *, key: str | None = None, timeout: int = _DEFAULT_TIMEOUT) -> dict:
    """GET /users/{id}/transaction_accounts — فقط برای تأیید/نگاشتِ عنوانِ حساب.
    خروجی PII-امن: فقط id/title/type/currency (هرگز موجودی/balance echo نمی‌شود).
    خروجی: {"ok","wired","count","accounts":[...],"note"}. فلگ خاموش → no-op."""
    if not _flag_on():
        return {"ok": False, "wired": False, "count": 0, "accounts": [],
                "note": f"فلگِ {FLAG} خاموش است — no-op."}
    r = _get(f"/users/{user_id}/transaction_accounts", key=key, timeout=timeout)
    if not r["ok"]:
        return {"ok": False, "wired": True, "count": 0, "accounts": [], "note": r["note"]}
    rows = r["data"] or []
    safe = []
    for a in rows if isinstance(rows, list) else []:
        if not isinstance(a, dict):
            continue
        safe.append({                                # ⚠️ صفر balance/موجودی — فقط شناسه/عنوان
            "id": a.get("id"),
            "title": str(a.get("title") or a.get("name") or "").strip(),
            "type": a.get("type"),
            "currency": a.get("currency_code"),
        })
    return {"ok": True, "wired": True, "count": len(safe), "accounts": safe, "note": "ok"}


def fetch_transactions(start_date, end_date, *, user_id=None, key: str | None = None,
                       timeout: int = _DEFAULT_TIMEOUT, per_page: int = 100,
                       max_pages: int = _MAX_PAGES) -> dict:
    """GET /users/{id}/transactions?start_date=&end_date=&per_page=100 با دنبال‌کردنِ
    pagination (هدرِ Link rel="next")، لیستِ خامِ تراکنش‌ها را برمی‌گرداند.
    user_id نیامده → از me() حل می‌شود. فلگ خاموش/بی‌کلید → لیستِ خالیِ صادق.
    خروجی: {"ok","wired","transactions":[...],"pages":int,"note"}."""
    if not _flag_on():
        return {"ok": False, "wired": False, "transactions": [], "pages": 0,
                "note": f"فلگِ {FLAG} خاموش است — no-op (صفر شبکه)."}
    key = key or _api_key()
    if not key:
        return {"ok": False, "wired": True, "transactions": [], "pages": 0,
                "note": f"{KEY_ENV} تنظیم نیست — لیستِ خالی (کلید لازم است)."}
    if user_id is None:
        m = me(key=key, timeout=timeout)
        if not m["ok"]:
            return {"ok": False, "wired": True, "transactions": [], "pages": 0,
                    "note": "me() ناموفق: " + m["note"]}
        user_id = m["user_id"]
    txns: list[dict] = []
    url = _build_url(f"/users/{user_id}/transactions",
                     {"start_date": start_date, "end_date": end_date, "per_page": per_page})
    pages = 0
    while url and pages < max_pages:
        r = _get(url, key=key, timeout=timeout)
        if not r["ok"]:
            return {"ok": False, "wired": True, "transactions": txns, "pages": pages,
                    "note": f"صفحهٔ {pages + 1} ناموفق: " + r["note"]}
        page = r["data"] or []
        if isinstance(page, list):
            txns.extend(x for x in page if isinstance(x, dict))
        pages += 1
        url = _parse_next_link(r["link"])
    return {"ok": True, "wired": True, "transactions": txns, "pages": pages, "note": "ok"}


# ─── نگاشت به schemaِ txn_store ───────────────────────────────────────────────
def to_store_txns(raw) -> list[dict]:
    """هر تراکنشِ خامِ PocketSmith → یک ردیفِ schemaِ txn_store.

    نکتهٔ کلیدی (دقتِ کل سیستم): `category` (transaction.category.title) و `labels`
    (لیست) — دسته‌بندیِ *موجودِ خودِ مالک* (نیمه‌دسته‌بندی‌شده) — عیناً حمل می‌شوند تا
    اختاپوس روی حقیقتِ زمینیِ مالک بنشیند، نه حدسِ خودش.

    مبلغ با money.to_cents (integer cents، هرگز float). علامتِ PocketSmith حفظ می‌شود:
    مثبت = بستانکار/بازپرداخت، منفی = بدهکار (خروج)."""
    out: list[dict] = []
    for t in (raw or []):
        if not isinstance(t, dict):
            continue
        cat_obj = t.get("category")
        category = str(cat_obj.get("title") or "").strip() if isinstance(cat_obj, dict) else ""
        acc_obj = t.get("transaction_account")
        account = (str(acc_obj.get("title") or acc_obj.get("name") or "").strip()
                   if isinstance(acc_obj, dict) else "")
        labels = t.get("labels")
        labels = [str(x) for x in labels] if isinstance(labels, list) else []
        desc = str(t.get("payee") or t.get("merchant") or t.get("memo") or "").strip()[:120]
        out.append({
            "id": str(t.get("id") or ""),              # idِ پایدارِ PocketSmith → dedup میان‌sync
            "date": str(t.get("date") or "")[:10],     # PocketSmith از پیش ISO (YYYY-MM-DD) می‌دهد
            "amount_cents": money.to_cents(t.get("amount")),   # علامت‌دار: منفی=خروج، مثبت=ورود
            "desc": desc,
            "source": SOURCE,
            "account": account,
            "owner": "unknown",                        # مالکیت بعداً با مرورِ مالک
            "ptype": "unknown",                        # income/expense/transfer — نامشخص تا مرور
            "category": category,                      # ← دسته‌بندیِ خودِ مالک
            "labels": labels,                          # ← برچسب‌های خودِ مالک
            "review": "pending",
            "note": "",
        })
    return out


# ─── sync: fetch + map + merge → انبار (شمارش/تراز، هرگز مقدارِ خام) ───────────
def _load_existing_store(store_path: Path | None) -> list[dict]:
    """انبارِ موجود (txn-store.json) را بخوان → لیستِ txns (fail-soft به خالی)."""
    import txn_store
    p = Path(store_path) if store_path else txn_store.default_store_path()
    try:
        if p.exists():
            doc = json.loads(p.read_text("utf-8"))
            rows = doc.get("txns", [])
            return list(rows) if isinstance(rows, list) else []
    except Exception:  # noqa: BLE001 — انبارِ خراب نباید sync را بکشد
        pass
    return []


def sync(start_date, end_date, persist: bool = True, *, store_path: Path | None = None,
         key: str | None = None, timeout: int = _DEFAULT_TIMEOUT) -> dict:
    """fetch + map + merge (dedup by id) → انبارِ txn_store. propose-only، صفر حرکتِ مالی.

    خروجی فقط شمارش + تراز (هرگز مقدار/ردیفِ خام): fetched/mapped/new_added/total + reconcile.
    فلگ خاموش → no-op. dedup با txn_store._dedup روی id (idِ PocketSmith) → sync دوباره
    idempotent است (تراکنشِ تکراری دوباره اضافه نمی‌شود)."""
    if not _flag_on():
        return {"ok": False, "wired": False, "fetched": 0, "mapped": 0, "new_added": 0,
                "note": f"فلگِ {FLAG} خاموش است — no-op (صفر شبکه، صفر نوشتن)."}
    fetched = fetch_transactions(start_date, end_date, key=key, timeout=timeout)
    if not fetched["ok"]:
        return {"ok": False, "wired": True, "fetched": 0, "mapped": 0, "new_added": 0,
                "note": "fetch ناموفق: " + fetched["note"]}
    import txn_store
    raw = fetched["transactions"]
    mapped = to_store_txns(raw)
    existing = _load_existing_store(store_path)
    combined = txn_store._dedup(existing + mapped)     # dedup by id (اولین بروز می‌ماند)
    new_added = len(combined) - len(existing)
    if persist:
        txn_store.save(combined, path=store_path)      # نوشتِ اتمیک (tmp+replace)
    rep = txn_store.reconcile_report(combined)
    return {
        "ok": True,
        "wired": True,
        "fetched": len(raw),
        "mapped": len(mapped),
        "existing": len(existing),
        "new_added": new_added,
        "total_after_merge": len(combined),
        "persisted": bool(persist),
        "reconcile": {                                 # تجمیعیِ امن — هرگز تراکنشِ خام
            "total_rows": rep["total_rows"],
            "source_count": rep["source_count"],
            "per_source_rows": {k: v["row_count"] for k, v in rep["per_source"].items()},
            "total_net_cents": rep["total_net_cents"],  # aggregate (مجاز)، نه مبلغِ فردی
            "tie_out_ok": rep["tie_out_ok"],
        },
        "note": "sync ok — نگاشت + merge (dedup by id) روی انبار انجام شد.",
    }


if __name__ == "__main__":
    # اجرای واقعی: فقط وضعیتِ فلگ/کلید (set/not-set، هرگز مقدار) + گزارشِ تجمیعی.
    _status = {
        "flag_" + FLAG: _flag_on(),
        KEY_ENV: "set" if _api_key() else "not-set",   # فقط set/not-set — هرگز مقدار
        "base": BASE,
        "read_only": True,
    }
    print(json.dumps(_status, ensure_ascii=False, indent=2))
