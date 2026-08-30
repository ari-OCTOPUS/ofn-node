#!/usr/bin/env python3
"""ps_writeback.py — write-backِ کنترل‌شدهٔ دسته‌بندی به PocketSmith (2026-07-16).

رأی مالک (چت 2026-07-16): «می‌خوام همزمان تو پاکت‌اسمیتم ذخیره شه و سینک باشه.»
این ماژول *تنها* استثنای مجازِ دکترینِ صفر-نوشتنِ pocketsmith_api است — و استثنا را
تا حدِ ممکن باریک نگه می‌دارد:

خط‌قرمزهای سخت (choke-point واحدِ _request اجرا می‌کند، نه قرارداد اجتماعی):
  • فقط GET + PUT، و PUT فقط به مسیرِ /transactions/{id} (regex-گارد).
  • بدنهٔ PUT فقط از فیلدهای _WRITABLE_FIELDS = {"labels"} — هرگز مبلغ/تاریخ/payee/
    category/split. فیلدِ خارج از whitelist → درخواست *ارسال نمی‌شود* (blocked).
  • پشتِ فلگِ جداگانهٔ OCTOPUS_WIRE_PS_WRITEBACK (پیش‌فرض خاموش → صفر شبکه، صفر فایل).
  • گیتِ per-item مالک (fail-closed، ۲۰۲۶-۰۷-۲۱): قبل از هر PUT، رأیِ پایدارِ «approve»ِ مالک
    برای دقیقاً همین (tid + فیلد=labels + هشِ محتوایِ برچسب‌های oct) لازم است. نبودِ رأی/عدمِ
    تطبیقِ هش → skipِ صادق، هرگز PUT — حتی با هر سه فلگِ مسلح. رکوردِ رأی فقط با کنشِ صریحِ
    مالک ساخته می‌شود (record_owner_verdict؛ هرگز از مسیرِ خودکار — auto-approve وجود ندارد).
  • سقفِ نوشتن در هر flush (پیش‌فرض ۴۰؛ PS_WRITEBACK_MAX_PER_FLUSH) — ضدِ خسارتِ انبوه.
  • idempotent: قبل از هر PUT یک GET؛ اگر برچسب‌ها از قبل درست‌اند → skip (صفر نوشتن).
  • هر نتیجه در لاگِ ممیزیِ append-onlyِ محلی ثبت می‌شود (gitignored؛ هرگز مبلغ).
  • کلید (همان POCKETSMITH_API_KEY) هرگز log/echo نمی‌شود؛ 403 = کلیدِ فقط‌خواندنی →
    توقفِ صادقانه + صف دست‌نخورده (مالک باید کلیدِ full-access بسازد).
  • fail-soft مطلق نسبت به مرورِ مالک: شکستِ صف/شبکه هرگز /review را نمی‌شکند.

جریان: acct_review.answer() بعد از ثبتِ محلیِ موفق فقط *enqueue* می‌کند (صفر شبکه در
هندلرِ تلگرام)؛ accountant.sync_network() در پایانِ /sync صف را flush می‌کند (batch).
برچسب‌ها: `oct-مالک-<آرمین|عباس|بیزنس>` و `oct-نوع-<درآمد|خرج|حقوق|عبور>` — فقط همین
دو namespace مدیریت می‌شود؛ برچسب‌ها و دسته‌های خودِ مالک در PocketSmith دست‌نخورده.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/legs
_OPS = _HERE.parent
for _p in (str(_HERE), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pocketsmith_api as _ps                     # noqa: E402 — کلید/BASE/backoff مشترک

# ─── ثابت‌ها ─────────────────────────────────────────────────────────────────
FLAG = "OCTOPUS_WIRE_PS_WRITEBACK"                # پیش‌فرض خاموش → no-op کامل
MAX_ENV = "PS_WRITEBACK_MAX_PER_FLUSH"            # سقفِ نوشتن در هر flush
DEADLINE_ENV = "PS_WRITEBACK_DEADLINE_S"          # مهلتِ زمانیِ کلِ flush (ثانیه)
_DEFAULT_MAX = 40
_DEFAULT_DEADLINE_S = 60                          # flush روی threadِ باتِ تلگرام می‌دود —
_REQ_BUDGET_FACTOR = 3                            # /panic نباید پشتِ آن بماند (verify لنز ۴)
_DEFAULT_TIMEOUT = 30
_MAX_RETRIES = 3                                  # فقط برای 429 (مثل pocketsmith_api)
_LOCK_FRESH_S = 900                               # قفلِ کهنه‌تر از ۱۵ دقیقه = رهاشده

_WRITABLE_FIELDS = frozenset({"labels"})          # ← کلِ سطحِ نوشتنِ مجاز v1
_PUT_PATH_RE = re.compile(r"^/transactions/[0-9]+\Z")   # [0-9] نه \d (رقمِ یونیکد ممنوع)

_OWNER_FA = {"armin": "آرمین", "abbas": "عباس", "business": "بیزنس"}   # unknown → برچسب نمی‌گیرد
_PTYPE_FA = {"income": "درآمد", "expense": "خرج", "wage": "حقوق", "transfer": "عبور"}
_NS_OWNER = "oct-مالک-"
_NS_PTYPE = "oct-نوع-"

QUEUE_NAME = "ps-writeback-queue.jsonl"
AUDIT_NAME = "ps-writeback-log.jsonl"
VERDICT_NAME = "ps-writeback-verdicts.jsonl"      # رأیِ پایدارِ per-item مالک (owner-gated)
# D1-hardening (2026-07-21): TTL رأی — رأیِ کهنه‌تر از این منقضی است (fail-closed). عددِ
# owner-tunable/placeholder، نه سیاستِ نهاییِ مالی. رأی همچنین single-use است (پس از PUT مصرف می‌شود).
VERDICT_TTL_SEC = 7 * 24 * 3600
MARK_NAME = "ps-writeback-backfilled.marker"      # auto-backfillِ یک‌باره در اولین flushِ سیمی


def _sleep(seconds: float) -> None:
    """seam برای تست (backoffِ 429 بدونِ خوابِ واقعی override می‌شود)."""
    time.sleep(seconds)


def _valid_tid(tid) -> bool:
    """فقط idِ عددیِ ASCII خودِ PocketSmith (نه رقمِ یونیکد، نه hashِ فایل)."""
    s = str(tid or "")
    return bool(s) and s.isascii() and s.isdigit()


def _halted() -> str | None:
    """مرزِ HALT سراسری (مثل بقیهٔ actuatorها) — دلیل یا None؛ خطا = not-halted (fail-soft)."""
    try:
        import opslib
        return opslib.master_halted()
    except Exception:  # noqa: BLE001
        return None


# ─── فلگ / مسیرها ────────────────────────────────────────────────────────────
def _flag_on() -> bool:
    """آیا OCTOPUS_WIRE_PS_WRITEBACK روشن است؟ (پیش‌فرض خاموش)."""
    return str(os.environ.get(FLAG, "")).strip().lower() in {"1", "true", "yes", "on"}


def _max_writes() -> int:
    try:
        v = int(os.environ.get(MAX_ENV, _DEFAULT_MAX))
        return v if v > 0 else _DEFAULT_MAX
    except (TypeError, ValueError):
        return _DEFAULT_MAX


def _personal_dir() -> Path:
    """همان پوشهٔ gitignoredِ انبار (personal/) — صف و لاگ کنارِ txn-store می‌نشینند."""
    import txn_store
    return txn_store.default_store_path().parent


def _queue_path(p: Path | None = None) -> Path:
    return Path(p) if p else _personal_dir() / QUEUE_NAME


def _audit_path(p: Path | None = None) -> Path:
    return Path(p) if p else _personal_dir() / AUDIT_NAME


def _audit(entry: dict, audit_path: Path | None = None) -> None:
    """یک خطِ ممیزی append کن (fail-soft؛ هرگز مبلغ/کلید در entry)."""
    try:
        p = _audit_path(audit_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **entry}
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — ممیزی نباید جریان را بکشد
        pass


# ─── لایهٔ HTTP (GET + PUTِ گاردشده؛ choke-point واحد) ────────────────────────
def _transport(req: urllib.request.Request, timeout: int):
    """seam برای تست — تنها نقطه‌ای که واقعاً به شبکه می‌رود."""
    return urllib.request.urlopen(req, timeout=timeout)  # noqa: S310 — فقط BASEِ https


def _request(method: str, path: str, body: dict | None = None, *,
             key: str | None = None, timeout: int = _DEFAULT_TIMEOUT) -> dict:
    """GET یا PUTِ گاردشده. خروجی همیشه dictِ صادق {"ok","status","data","note"}.

    گاردها *قبل از* هر شبکه اجرا می‌شوند:
      method ∉ {GET, PUT} → blocked · PUT با مسیرِ غیرِ /transactions/{id} → blocked ·
      PUT با فیلدِ خارج از _WRITABLE_FIELDS → blocked (درخواست ارسال نمی‌شود).
    """
    if not _flag_on():                            # فلگ داخلِ خودِ choke-point (لنز ۱)
        return {"ok": False, "status": 0, "data": None, "blocked": True,
                "note": f"فلگِ {FLAG} خاموش است — درخواست ارسال نشد."}
    if method not in ("GET", "PUT"):
        return {"ok": False, "status": 0, "data": None, "blocked": True,
                "note": f"متدِ {method} مجاز نیست (فقط GET/PUT)."}
    if method == "PUT":
        if not _PUT_PATH_RE.match(path):
            return {"ok": False, "status": 0, "data": None, "blocked": True,
                    "note": "PUT فقط به /transactions/{id} مجاز است — مسیر رد شد."}
        bad = set(body or {}) - _WRITABLE_FIELDS
        if bad or not body:
            return {"ok": False, "status": 0, "data": None, "blocked": True,
                    "note": "فیلد(های) خارج از whitelist: " + ", ".join(sorted(bad)) if bad
                            else "بدنهٔ خالی — PUT بی‌معنی رد شد."}
    key = key or _ps._api_key()
    if not key:
        return {"ok": False, "status": 0, "data": None, "blocked": False,
                "note": f"{_ps.KEY_ENV} تنظیم نیست — no-op."}
    url = _ps.BASE + path
    headers = {"X-Developer-Key": key, "Accept": "application/json",
               "User-Agent": "octopus-accounting-writeback/1.0"}
    data = None
    if method == "PUT":
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    attempt = 0
    while True:
        req = urllib.request.Request(url, method=method, headers=headers, data=data)
        try:
            with _transport(req, timeout) as resp:
                raw = resp.read()
                parsed = json.loads(raw.decode("utf-8")) if raw else None
                return {"ok": True, "status": getattr(resp, "status", 200) or 200,
                        "data": parsed, "blocked": False, "note": "ok"}
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < _MAX_RETRIES:
                attempt += 1
                try:
                    ra = int((e.headers.get("Retry-After") if e.headers else None) or 0)
                except (TypeError, ValueError):
                    ra = 0
                _sleep(min(ra if ra > 0 else 2 ** attempt, 60))
                continue
            note = ("کلید اجازهٔ نوشتن ندارد (403) — کلیدِ full-access لازم است؛ "
                    "صف دست‌نخورده می‌ماند." if e.code == 403 else f"HTTP {e.code} (fail-soft).")
            return {"ok": False, "status": e.code, "data": None, "blocked": False, "note": note}
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            # ValueError پوششِ UnicodeEncodeErrorِ putrequest است — tidِ سمی نباید flush را
            # بکشد و صف را برای همیشه wedge کند (verify لنز ۱)
            return {"ok": False, "status": 0, "data": None, "blocked": False,
                    "note": f"شبکه/timeout — {type(e).__name__} (fail-soft)."}


# ─── برچسب‌ها ─────────────────────────────────────────────────────────────────
def _target_labels(owner: str | None, ptype: str | None) -> list[str]:
    """برچسب‌های هدف برای این تأیید. unknown/ناشناخته → برچسب نمی‌گیرد."""
    out: list[str] = []
    fa = _OWNER_FA.get(str(owner or ""))
    if fa:
        out.append(_NS_OWNER + fa)
    fa = _PTYPE_FA.get(str(ptype or ""))
    if fa:
        out.append(_NS_PTYPE + fa)
    return out


def _merge_labels(existing, targets: list[str]) -> tuple[list[str], bool]:
    """برچسب‌های موجودِ تراکنش + هدف‌های ما → (merged, changed).
    فقط دو namespaceِ خودمان جایگزین می‌شود؛ بقیهٔ برچسب‌های مالک عیناً می‌مانند."""
    existing = existing if isinstance(existing, list) else []   # رشته = تکرارِ کاراکتری، ممنوع
    cur = [str(x).strip() for x in existing if str(x).strip()]
    kept = [x for x in cur if not (x.startswith(_NS_OWNER) or x.startswith(_NS_PTYPE))]
    merged = kept + [t for t in targets if t not in kept]
    return merged, merged != cur


# ─── رأیِ پایدارِ per-item مالک (گیتِ fail-closed پیش از هر PUT) ───────────────────
#
# قرارداد (v1، owner-gated): پیش از هر نوشتنِ بیرونی برای یک تراکنش، باید رکوردِ رأیِ
# پایداری وجود داشته باشد که *دقیقاً همان آیتم* را مجاز کند — گره‌خورده به:
#     (tid, field="labels", content_sha256(هشِ برچسب‌های oct هدف)).
# رکورد فقط با کنشِ صریحِ مالک ساخته می‌شود (record_owner_verdict — CLI مالک/هندلرِ
# owner-gated). هیچ مسیرِ خودکاری (flush/enqueue/backfill) رأی نمی‌سازد → auto-approve
# وجود ندارد. نبودِ رأی/عدمِ تطبیقِ هش/رأیِ غیرِ approve → fail-closed (هیچ PUT).
# هشِ محتوا از mission_contract.content_sha256 بازاستفاده می‌شود (همان anti-TOCTOUِ کانونیِ
# پروژه — «approval را به scopeِ دقیقاً تأییدشده گره می‌زند»).
def _verdict_path(p: Path | None = None, *, queue_path: Path | None = None) -> Path:
    """مسیرِ فایلِ رأی. صریح → همان؛ وگرنه کنارِ صف (per-queue، ایزوله)؛ وگرنه personal/."""
    if p is not None:
        return Path(p)
    if queue_path is not None:
        qp = Path(queue_path)
        return qp.with_name(qp.stem + "-verdicts" + qp.suffix)
    return _personal_dir() / VERDICT_NAME


def _read_verdicts(p: Path) -> list[dict]:
    """خطوطِ فایلِ رأی → رکوردها (خطِ خراب skip؛ fail-soft به خالی)."""
    out: list[dict] = []
    try:
        if p.exists():
            for ln in p.read_text("utf-8").splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    obj = json.loads(ln)
                    if isinstance(obj, dict):
                        out.append(obj)
                except json.JSONDecodeError:
                    continue
    except Exception:  # noqa: BLE001 — خواندنِ رأی نباید flush را بکشد
        pass
    return out


def _verdict_content_hash(tid, field: str, targets: list[str]) -> str | None:
    """هشِ محتوایی که رأی را به «همین tid + همین field + همین برچسب‌های oc‌tِ هدف» گره می‌زند.
    mission_contract.content_sha256 را بازاستفاده می‌کند (stdlib، deterministic). خطا → None
    (بدونِ هش هیچ رأیی تطبیق نمی‌شود → fail-closed)."""
    try:
        if str(_OPS) not in sys.path:
            sys.path.insert(0, str(_OPS))
        import mission_contract as _mc     # noqa: WPS433 — lazy؛ خطا → fail-closed
        return _mc.content_sha256(
            "ps_writeback.put_labels",
            f"pocketsmith/transactions/{tid}",
            {"field": str(field), "targets": sorted(str(t) for t in (targets or []))})
    except Exception:  # noqa: BLE001
        return None


def _owner_verdict_ok(tid, field: str, targets: list[str], *, verdict_file: Path,
                      now: float | None = None) -> bool:
    """آیا رأیِ پایدارِ «approve»ِ مالکِ **معتبر** برای دقیقاً همین (tid, field, هشِ محتوا) هست؟
    fail-closed در هر ابهام. سه قیدِ D1-hardening روی همان بایندِ per-item:
      · **single-use:** اگر برای این هش رکوردِ `consumed` باشد → False (رأی قبلاً خرج شده).
      · **expiry:** رأیِ approveِ کهنه‌تر از VERDICT_TTL_SEC نامعتبر است.
      · **per-item owner-binding:** هش از tid+field+برچسب‌های ocِ owner/ptype مشتق است، پس رأیِ
        یک owner/آیتمِ دیگر هشِ متفاوت دارد و اصلاً تطبیق نمی‌کند (ردِ ساختاریِ non-owner/wrong-item)."""
    want = _verdict_content_hash(tid, field, targets)
    if not want:
        return False
    now = time.time() if now is None else now
    seen_approve = False
    for rec in _read_verdicts(verdict_file):
        if str(rec.get("content_sha256")) != want:
            continue
        v = str(rec.get("verdict", "")).strip().lower()
        if v == "consumed":
            return False   # single-use: این هش قبلاً PUT شده → دیگر مجاز نیست
        if (v == "approve"
                and str(rec.get("tid")) == str(tid)
                and str(rec.get("field")) == str(field)):
            te = rec.get("ts_epoch")
            fresh = True
            if te is not None:
                try:
                    fresh = (now - float(te)) <= VERDICT_TTL_SEC
                except Exception:  # noqa: BLE001 — ts_epochِ خراب = منقضی (fail-closed)
                    fresh = False
            if fresh:
                seen_approve = True
    return seen_approve


def _consume_verdict(tid, field: str, targets: list[str], *, verdict_file: Path) -> None:
    """پس از یک PUTِ موفق، رأیِ همین هش را single-use کن: یک رکوردِ `consumed` append می‌شود
    تا PUTِ دومِ همان محتوا (replay) رد شود. fail-soft — نبودِ مصرف نباید flush را بکشد."""
    want = _verdict_content_hash(tid, field, targets)
    if not want:
        return
    try:
        verdict_file.parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "ts_epoch": time.time(),
               "tid": str(tid), "field": str(field), "content_sha256": want, "verdict": "consumed"}
        with open(verdict_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def record_owner_verdict(tid, owner: str | None, ptype: str | None, *,
                         field: str = "labels", verdict: str = "approve",
                         verdict_path: Path | None = None,
                         queue_path: Path | None = None) -> dict:
    """OWNER-INVOKED ONLY — یک رأیِ پایدارِ per-item ثبت کن که PUTِ برچسب‌ها به همین تراکنش را
    مجاز می‌کند. **هرگز** از مسیرِ خودکارِ flush/enqueue/backfill صدا زده نمی‌شود؛ پرکردنِ این
    store یک کنشِ صریحِ مالک است (CLI مالک/هندلرِ owner-gated تلگرام). auto-approve نیست:
    رکورد فقط با کنشِ مالک ساخته می‌شود و به هشِ محتوا (tid+field+برچسب‌های oct) گره می‌خورد.
    صفر شبکه، صفر پول — فقط یک خط append. خروجی فقط شمارش/هش — هرگز مبلغ/کلید."""
    if not _valid_tid(tid):
        return {"ok": False, "recorded": False, "note": "id غیرِ PocketSmith — رأی ثبت نشد."}
    targets = _target_labels(owner, ptype)
    if not targets:
        return {"ok": False, "recorded": False, "note": "owner/ptype ناشناخته — چیزی برای تأیید نیست."}
    chash = _verdict_content_hash(tid, field, targets)
    if not chash:
        return {"ok": False, "recorded": False, "note": "هشِ محتوا محاسبه نشد (fail-closed)."}
    v = str(verdict or "").strip().lower() or "approve"
    try:
        p = _verdict_path(verdict_path, queue_path=queue_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "ts_epoch": time.time(),
               "tid": str(tid), "field": str(field),
               "owner": owner, "ptype": ptype, "content_sha256": chash, "verdict": v}
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return {"ok": True, "recorded": True, "content_sha256": chash, "verdict": v,
                "note": "رأیِ per-item ثبت شد — PUT فقط برای همین آیتم/هش مجاز است."}
    except Exception as e:  # noqa: BLE001 — ثبتِ رأی نباید صداکننده را بکشد
        return {"ok": False, "recorded": False, "note": f"ثبتِ رأی ناموفق — {type(e).__name__}."}


# ─── صف (enqueue در /review، flush در /sync) ─────────────────────────────────
def enqueue(tid: str, owner: str | None, ptype: str | None, *,
            source: str | None = None, queue_path: Path | None = None) -> dict:
    """تأییدِ مالک را برای write-back صف کن — صفر شبکه؛ فقط یک خط append.
    فلگ خاموش → no-opِ کامل (حتی فایل هم ساخته نمی‌شود).
    source (اگر داده شود) باید خودِ PocketSmith باشد — گاردِ منشأ، نه فقط شکلِ id (لنز ۱)."""
    if not _flag_on():
        return {"ok": False, "queued": False, "note": f"فلگِ {FLAG} خاموش است — no-op."}
    if source is not None and str(source) != _ps.SOURCE:
        return {"ok": True, "queued": False, "note": "منبعِ غیرِ PocketSmith — صف نشد."}
    if not _valid_tid(tid):
        # فقط idِ عددیِ خودِ PocketSmith؛ ردیف‌های xlsx/CSV (idِ content-hash) جای write-back ندارند
        return {"ok": True, "queued": False, "note": "id غیرِ PocketSmith — صف نشد (منبعِ فایل)."}
    targets = _target_labels(owner, ptype)
    if not targets:
        return {"ok": True, "queued": False, "note": "owner/ptype ناشناخته — چیزی برای نوشتن نیست."}
    try:
        p = _queue_path(queue_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        line = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "tid": str(tid), "owner": owner, "ptype": ptype}
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
        return {"ok": True, "queued": True, "note": "صف شد — نوشتن در flushِ بعدی (/sync)."}
    except Exception as e:  # noqa: BLE001 — صف نباید مرور را بکشد
        return {"ok": False, "queued": False, "note": f"صف ناموفق — {type(e).__name__} (fail-soft)."}


def _raw_lines(p: Path) -> list[str]:
    """خطوطِ خامِ غیرخالیِ صف (fail-soft به خالی) — مبنای شمارشِ ضدِ race."""
    try:
        if p.exists():
            return [x for x in p.read_text("utf-8").splitlines() if x.strip()]
    except Exception:  # noqa: BLE001
        pass
    return []


def _parse_items(lines: list[str]) -> list[dict]:
    """خطوط → آیتم‌ها (خطِ خراب skip)."""
    items: list[dict] = []
    for ln in lines:
        try:
            obj = json.loads(ln)
            if isinstance(obj, dict) and obj.get("tid"):
                items.append(obj)
        except json.JSONDecodeError:
            continue
    return items


def _read_queue(p: Path) -> list[dict]:
    """خطوطِ صف → آیتم‌ها (خطِ خراب skip؛ fail-soft به خالی)."""
    return _parse_items(_raw_lines(p))


def _write_queue(p: Path, items: list[dict], read_count: int) -> bool:
    """صف را اتمیک بازنویسی کن؛ خطوطی که *بعد از* خواندنِ ما append شده‌اند حفظ می‌شوند
    (ضدِ raceِ enqueueِ همزمان: خطوطِ بعد از read_count دوباره چسبانده می‌شوند).
    خروجی: موفق شد؟ (شکست = صفِ قدیمی می‌ماند → idempotent، دوباره‌کاری امن — ولی audit شود)."""
    try:
        tail: list[str] = []
        if p.exists():
            lines = [x for x in p.read_text("utf-8").splitlines() if x.strip()]
            tail = lines[read_count:]
        body = "".join(json.dumps(it, ensure_ascii=False) + "\n" for it in items)
        body += "".join(t + "\n" for t in tail)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(body, "utf-8")
        os.replace(tmp, p)
        return True
    except Exception:  # noqa: BLE001
        return False


def _acquire_lock(qp: Path) -> Path | None:
    """قفلِ انحصاریِ flush (فایل O_EXCL کنارِ صف) — دو flusherِ همزمان (بات/CLI/beat)
    با brushِ read_count صف را خراب می‌کردند (verify لنز ۳). قفلِ کهنه (crash) شکسته می‌شود."""
    lock = qp.with_name(qp.name + ".lock")
    for _ in range(2):
        try:
            lock.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("ascii"))
            os.close(fd)
            return lock
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > _LOCK_FRESH_S:
                    lock.unlink()                 # قفلِ رهاشده → بشکن و دوباره بگیر
                    continue
            except OSError:
                pass
            return None
        except OSError:
            return None
    return None


def flush(*, queue_path: Path | None = None, audit_path: Path | None = None,
          store_path: Path | None = None, key: str | None = None,
          timeout: int = _DEFAULT_TIMEOUT, max_writes: int | None = None,
          deadline_s: float | None = None, verdict_path: Path | None = None) -> dict:
    """صفِ write-back را خالی کن: هر آیتم → GET (idempotency) → PUTِ برچسب‌ها.

    قراردادها (سخت‌شده با verify خصمانهٔ ۵-لنزی):
      HALT سراسری → no-op و صف دست‌نخورده · قفلِ انحصاری (دو flusherِ همزمان ممنوع) ·
      سقفِ نوشتن (پیش‌فرض ۴۰) + بودجهٔ کلِ درخواست (۳×سقف) + مهلتِ زمانی (پیش‌فرض ۶۰s —
      flush روی threadِ بات است، /panic نباید منتظر بماند) · 403/شبکه → توقفِ صادق و صف
      دست‌نخورده · 404 → drop · tidِ نامعتبر در صف → drop (نه wedge) · برچسبِ کامادار نزدِ
      مالک → skip (دادهٔ مالک خراب نمی‌شود) · اولین flushِ سیمی → auto-backfillِ یک‌بارهٔ
      تأییدهای قبلی. خروجی فقط شمارش — هرگز مبلغ."""
    if not _flag_on():
        return {"ok": False, "wired": False, "written": 0, "skipped": 0, "kept": 0,
                "note": f"فلگِ {FLAG} خاموش است — no-op (صفر شبکه)."}
    halt = _halted()
    if halt:
        return {"ok": False, "wired": True, "written": 0, "skipped": 0, "kept": 0,
                "note": f"HALT سراسری فعال است ({halt}) — صف دست‌نخورده."}
    key = key or _ps._api_key()
    if not key:
        return {"ok": False, "wired": True, "written": 0, "skipped": 0, "kept": 0,
                "note": f"{_ps.KEY_ENV} تنظیم نیست — صف دست‌نخورده."}
    qp = _queue_path(queue_path)
    lock = _acquire_lock(qp)
    if lock is None:
        return {"ok": False, "wired": True, "written": 0, "skipped": 0, "kept": 0,
                "note": "flushِ دیگری در جریان است — این دور رد شد (صف دست‌نخورده)."}
    try:
        # auto-backfillِ یک‌باره: تأییدهایی که قبل از روشن‌شدنِ فلگ داده شده‌اند (لنز ۵)
        mark = qp.with_name(MARK_NAME)
        if not mark.exists():
            bf = backfill(store_path=store_path, queue_path=qp)
            if bf.get("ok"):
                try:
                    mark.write_text(time.strftime("%Y-%m-%dT%H:%M:%S")
                                    + f" queued={bf.get('queued', 0)}\n", "utf-8")
                except OSError:
                    pass
                if bf.get("queued"):
                    _audit({"result": "auto-backfill", "queued": bf["queued"]}, audit_path)
        lines = _raw_lines(qp)
        read_count = len(lines)                # شمارشِ خطوطِ *خام* — هم‌واحد با برشِ _write_queue
        raw_items = _parse_items(lines)
        if not raw_items:
            note = "صف خالی است." if read_count == 0 else \
                   f"صف آیتمِ معتبر ندارد ولی {read_count} خطِ ناخوانا دارد — بررسیِ دستی."
            return {"ok": True, "wired": True, "written": 0, "skipped": 0, "kept": 0,
                    "unreadable": read_count, "note": note}
        # dedup: آخرین جوابِ مالک برای هر تراکنش می‌بَرد
        by_tid: dict[str, dict] = {}
        for it in raw_items:
            by_tid[str(it["tid"])] = it
        todo = list(by_tid.values())
        cap = max_writes if isinstance(max_writes, int) and max_writes > 0 else _max_writes()
        try:
            dl = float(deadline_s if deadline_s is not None
                       else os.environ.get(DEADLINE_ENV, _DEFAULT_DEADLINE_S))
        except (TypeError, ValueError):
            dl = _DEFAULT_DEADLINE_S
        t0 = time.monotonic()
        req_budget = _REQ_BUDGET_FACTOR * cap  # سقفِ GETها هم — نه فقط PUT (لنز ۴)
        vp = _verdict_path(verdict_path, queue_path=queue_path)   # فایلِ رأیِ per-item
        requests_made = written = skipped = dropped = awaiting = 0
        kept: list[dict] = []
        aborted_note = None
        for it in todo:
            if aborted_note or written >= cap or requests_made >= req_budget \
                    or (time.monotonic() - t0) > dl:
                if aborted_note is None and (written >= cap or requests_made >= req_budget
                                             or (time.monotonic() - t0) > dl):
                    aborted_note = "توقفِ زودهنگام (سقف/بودجهٔ درخواست/مهلت) — بقیه در صفِ دورِ بعد."
                kept.append(it)
                continue
            tid = str(it["tid"])
            if not _valid_tid(tid):            # tidِ دست‌کاری‌شده/سمی → drop، نه wedgeِ ابدی (لنز ۳)
                dropped += 1
                _audit({"tid": tid, "result": "bad-tid-dropped"}, audit_path)
                continue
            requests_made += 1
            g = _request("GET", f"/transactions/{tid}", key=key, timeout=timeout)
            if not g["ok"]:
                if g["status"] == 404:
                    dropped += 1
                    _audit({"tid": tid, "result": "gone-404-dropped"}, audit_path)
                    continue
                kept.append(it)
                aborted_note = "GET ناموفق: " + g["note"]
                continue
            data = g["data"] or {}
            cur_labels = data.get("labels")
            if isinstance(cur_labels, list) and any("," in str(x) for x in cur_labels):
                # برچسبِ کامادارِ خودِ مالک با join دو تکه می‌شود — دست نمی‌زنیم (لنز ۵)
                skipped += 1
                _audit({"tid": tid, "result": "comma-label-skipped"}, audit_path)
                continue
            targets = _target_labels(it.get("owner"), it.get("ptype"))
            merged, changed = _merge_labels(cur_labels, targets)
            if not changed:
                skipped += 1
                _audit({"tid": tid, "result": "already-correct-skipped"}, audit_path)
                continue
            # گیتِ fail-closed per-item: بدونِ رأیِ پایدارِ «approve»ِ مالک برای دقیقاً همین
            # (tid, labels, هشِ محتوا) هیچ PUT — حتی با هر سه فلگ. غیابِ رأی = skipِ صادق و
            # نگه‌داشتنِ آیتم در صف (منتظرِ تأییدِ مالک، نه خطا؛ aborted_note ست نمی‌شود).
            if not _owner_verdict_ok(tid, "labels", targets, verdict_file=vp):
                awaiting += 1
                kept.append(it)
                _audit({"tid": tid, "result": "no-owner-verdict-skipped", "field": "labels"},
                       audit_path)
                continue
            requests_made += 1
            pr = _request("PUT", f"/transactions/{tid}", {"labels": ",".join(merged)},
                          key=key, timeout=timeout)
            if pr["ok"]:
                written += 1
                _consume_verdict(tid, "labels", targets, verdict_file=vp)   # D1: single-use
                _audit({"tid": tid, "result": "written", "labels": targets}, audit_path)
            else:
                kept.append(it)
                aborted_note = pr["note"]
                _audit({"tid": tid, "result": "failed", "status": pr["status"],
                        "note": pr["note"]}, audit_path)
        if not _write_queue(qp, kept, read_count):
            _audit({"result": "queue-rewrite-failed",
                    "note": "بازنویسیِ صف شکست — دورِ بعد دوباره‌کاریِ idempotent."}, audit_path)
        ok = aborted_note is None
        return {"ok": ok, "wired": True, "written": written, "skipped": skipped,
                "dropped": dropped, "kept": len(kept), "awaiting_verdict": awaiting,
                "note": aborted_note or
                        (f"flush ok — {written} نوشته، {skipped} از قبل درست، {dropped} غایب"
                         + (f"، {awaiting} منتظرِ رأیِ مالک" if awaiting else "") + ".")}
    finally:
        try:
            lock.unlink()
        except OSError:
            pass


def backfill(*, store_path: Path | None = None, queue_path: Path | None = None,
             limit: int = 500) -> dict:
    """تأییدهای موجودِ انبار (review=confirmed) را یک‌باره صف کن (برای شروع/جبران).
    شبکه نمی‌رود — فقط صف؛ نوشتنِ واقعی در flush با همان سقف/گاردها."""
    if not _flag_on():
        return {"ok": False, "queued": 0, "note": f"فلگِ {FLAG} خاموش است — no-op."}
    import txn_store
    try:
        p = Path(store_path) if store_path else txn_store.default_store_path()
        doc = json.loads(p.read_text("utf-8")) if p.exists() else {}
        rows = doc.get("txns", []) if isinstance(doc, dict) else []
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "queued": 0, "note": f"خواندنِ انبار ناموفق — {type(e).__name__}."}
    n = 0
    for t in rows:
        if not isinstance(t, dict) or t.get("review") != "confirmed":
            continue
        if str(t.get("source") or "") != _ps.SOURCE:
            continue                              # فقط ردیف‌های خودِ PocketSmith (id معتبرِ API)
        r = enqueue(t.get("id"), t.get("owner"), t.get("ptype"),
                    source=t.get("source"), queue_path=queue_path)
        if r.get("queued"):
            n += 1
            if n >= limit:
                break
    return {"ok": True, "queued": n, "note": f"{n} تأییدِ موجود صف شد — flush در /sync بعدی."}


if __name__ == "__main__":
    _status = {
        "flag_" + FLAG: _flag_on(),
        _ps.KEY_ENV: "set" if _ps._api_key() else "not-set",   # فقط set/not-set
        "writable_fields": sorted(_WRITABLE_FIELDS),
        "max_per_flush": _max_writes(),
        "queue": str(_queue_path()),
        "verdicts": str(_verdict_path()),
        "per_item_owner_verdict": "required (fail-closed) — no PUT without owner approve record",
    }
    if "--backfill" in sys.argv:
        _status["backfill"] = backfill()
    if "--flush" in sys.argv:
        _status["flush"] = flush()
    print(json.dumps(_status, ensure_ascii=False, indent=2))
