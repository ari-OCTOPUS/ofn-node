#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decision_receipt.py — رسیدِ تصمیمِ immutable و append-only، join به outcome_store.

قرارداد (رأی مالک 2026-07-20): Decision → immutable receipt → optional approval ref →
execution/test ref → OutcomeRecord → review/verdict event. نسخهٔ اول **فقط ثبت و join**؛
هیچ policy/runner رفتارش را بر اساسِ رسید تغییر نمی‌دهد و هیچ مصرف‌کنندهٔ اجرایی/self-apply
ندارد (inert، بدونِ wiring/Telegram).

قیودِ سخت (enforce‌شده در validate/store):
  - **Chain-of-thought ذخیره نمی‌شود** — فقط خلاصهٔ کوتاهِ تصمیم + reason_codesِ ساختاریافته.
    کلیدهای CoT (reasoning/thoughts/scratchpad/transcript/…) و فیلدهای بلند = رد.
  - رسید پس از ثبت **immutable** است (فقط INSERT؛ صفر UPDATE). test/outcome/review/verdict
    به‌شکلِ رویدادِ جدا در receipt_links اضافه می‌شوند، نه با mutate کردنِ رسید.
  - `approval_ref`/verdict فقط **reference** به Approval Store است، **نه مجوزِ اجرا**.
  - هیچ secret/متن خامِ حافظه/payloadِ حساس داخلِ رسید نیست — فقط hash/reference
    (memories_used فقط content_sha256؛ کلیدِ content/text/token/secret = رد).
  - `outcome_ref` idempotent و replayable (لینک با idempotency_key یکتا).
  - نبودِ memory/outcome **جعلِ موفقیت نمی‌کند** — مقدارِ صریحِ PENDING/UNKNOWN.
  - مدل نمی‌تواند trust حافظه، رأی مالک یا effect_class را خودش ارتقا دهد (صفر مسیرِ mutate).
  - integrity: receipt_sha256 روی فیلدهای رسید؛ verify_integrity دستکاریِ out-of-band را می‌گیرد.
stdlib فقط (sqlite3)؛ single-writer RLock؛ UTC-aware؛ schema-versioned.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
_LOCK = threading.RLock()

# effect_class از taxonomyِ واحد (منبعِ یگانه — همان‌که Memory Gate/Outcome/Spine می‌خوانند).
# fallbackِ خودکفا اگر taxonomy لود نشد (decision_receipt نباید به آن hard-وابسته باشد).
try:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent))
    import taxonomy as _tax
    _EFFECT_CLASSES = _tax.EFFECT_CLASSES

    def _tax_effect_ok(e):
        return _tax.is_effect_class(e)
except Exception:  # noqa: BLE001
    _EFFECT_CLASSES = ("E0", "E1", "E2", "E3", "E4")

    def _tax_effect_ok(e):
        return e in _EFFECT_CLASSES

KNOWN_EFFECT_CLASSES = _EFFECT_CLASSES
LINK_TYPES = ("outcome", "test", "review", "verdict", "approval")

# کلیدهایی که هرگز نباید در رسید باشند (CoT / متنِ خام / secret)
_FORBIDDEN_TOP = {"chain_of_thought", "cot", "reasoning", "thoughts", "scratchpad",
                  "transcript", "raw_prompt", "full_prompt", "prompt", "raw_response"}
_FORBIDDEN_MEM = {"content", "text", "raw", "body", "secret", "token", "password", "prompt"}

# سقفِ اندازه‌ها (ضدِ CoT-dumping)
_CAP = {"objective": 300, "selected_alternative": 200, "alternative": 200,
        "reason_code": 48, "assumption": 240, "predicted_outcome_json": 2000}
_MAX_ITEMS = 30


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha(obj) -> str:
    return hashlib.sha256(_canon(obj).encode("utf-8")).hexdigest()


def _is_hex64(s) -> bool:
    return isinstance(s, str) and len(s) == 64 and all(c in "0123456789abcdef" for c in s.lower())


def _reject_forbidden_deep(obj, forbidden, where: str):
    """کلیدهای ممنوعه را **بازگشتی** رد کن (CoT/متنِ خام نمی‌تواند در dictِ تودرتو پنهان شود)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in forbidden:
                raise ReceiptValidationError(f"{where} forbidden key (nested) {k!r}")
            _reject_forbidden_deep(v, forbidden, where)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _reject_forbidden_deep(v, forbidden, where)


class ReceiptValidationError(ValueError):
    pass


def _validate(rec: dict) -> dict:
    """رسیدِ ورودی را اعتبارسنجی و نرمال می‌کند؛ در نقضِ قید ReceiptValidationError.
    خروجی = رسیدِ نرمال‌شده (فقط فیلدهای مجاز، PENDING برای join‌های غایب)."""
    if not isinstance(rec, dict):
        raise ReceiptValidationError("receipt must be a dict")
    for k in rec:
        if str(k).lower() in _FORBIDDEN_TOP:
            raise ReceiptValidationError(f"forbidden CoT/raw key in receipt: {k!r}")

    objective = str(rec.get("objective") or "").strip()
    if not objective:
        raise ReceiptValidationError("objective required (short summary, not CoT)")
    if len(objective) > _CAP["objective"]:
        raise ReceiptValidationError(f"objective too long ({len(objective)}>{_CAP['objective']}) — no CoT dumps")

    effect_class = str(rec.get("effect_class") or "").strip()
    if not _tax_effect_ok(effect_class):
        raise ReceiptValidationError(
            f"effect_class must be one of the unified taxonomy classes {tuple(_EFFECT_CLASSES)}")

    def _list_capped(key, item_cap):
        vals = rec.get(key) or []
        if not isinstance(vals, list):
            raise ReceiptValidationError(f"{key} must be a list")
        if len(vals) > _MAX_ITEMS:
            raise ReceiptValidationError(f"{key} too many items (>{_MAX_ITEMS})")
        out = []
        for v in vals:
            s = str(v)
            if len(s) > item_cap:
                raise ReceiptValidationError(
                    f"{key} item too long ({len(s)}>{item_cap}) — must be structured code, not CoT")
            out.append(s)
        return out

    alternatives = _list_capped("alternatives", _CAP["alternative"])
    reason_codes = _list_capped("reason_codes", _CAP["reason_code"])
    assumptions = _list_capped("assumptions", _CAP["assumption"])

    # memories_used: فقط hash/reference — هرگز متنِ خام
    mem_out = []
    mems = rec.get("memories_used") or []
    if not isinstance(mems, list):
        raise ReceiptValidationError("memories_used must be a list")
    if len(mems) > _MAX_ITEMS:
        raise ReceiptValidationError("memories_used too many items")
    for m in mems:
        if not isinstance(m, dict):
            raise ReceiptValidationError("memories_used item must be a dict")
        for k in m:
            if str(k).lower() in _FORBIDDEN_MEM:
                raise ReceiptValidationError(f"memories_used must be hash/ref only — forbidden key {k!r}")
        csha = m.get("content_sha256")
        if not _is_hex64(csha):
            raise ReceiptValidationError("memories_used item needs a valid content_sha256 (hex64), not raw content")
        mid = str(m.get("memory_id") or "")
        tg = str(m.get("trust_grade") or "UNKNOWN")
        ra = str(m.get("retrieved_at") or "")
        # سقفِ طول روی هر فیلد — تا کسی متنِ خام/CoT در memory_id/trust نریزد
        if len(mid) > 128 or len(tg) > 32 or len(ra) > 40:
            raise ReceiptValidationError("memories_used field too long — refs/grades only, not raw content")
        mem_out.append({"memory_id": mid, "content_sha256": str(csha).lower(),
                        "trust_grade": tg, "retrieved_at": ra})

    predicted = rec.get("predicted_outcome")
    predicted = predicted if isinstance(predicted, dict) else {}
    # چکِ بازگشتیِ کلیدهای ممنوعه (CoT/raw نمی‌تواند در dictِ تودرتو پنهان شود)
    _reject_forbidden_deep(predicted, _FORBIDDEN_MEM | _FORBIDDEN_TOP, "predicted_outcome")
    if len(_canon(predicted)) > _CAP["predicted_outcome_json"]:
        raise ReceiptValidationError("predicted_outcome too large — no raw payload/CoT")

    created_at = str(rec.get("created_at") or _utc_now_iso())
    norm = {
        "schema_version": SCHEMA_VERSION,
        "trace_id": str(rec.get("trace_id") or ""),
        "mission_id": str(rec.get("mission_id") or ""),
        "created_at": created_at,
        "objective": objective,
        "alternatives": alternatives,
        "selected_alternative": str(rec.get("selected_alternative") or "")[:_CAP["selected_alternative"]],
        "reason_codes": reason_codes,
        "assumptions": assumptions,
        "memories_used": mem_out,
        "predicted_outcome": predicted,
        "effect_class": effect_class,
        "policy_sha256": str(rec.get("policy_sha256") or ""),
        # join‌ها در زمانِ ثبت PENDING‌اند و هرگز روی خودِ رسید mutate نمی‌شوند (لینک‌ها جدا):
        "approval_ref": rec.get("approval_ref") if rec.get("approval_ref") else None,
        "status": "RECORDED",
    }
    return norm


def _receipt_id(norm: dict) -> str:
    return "dr_" + _sha({"o": norm["objective"], "m": norm["mission_id"],
                         "t": norm["trace_id"], "c": norm["created_at"],
                         "s": norm["selected_alternative"]})[:16]


class DecisionReceiptStore:
    """storeِ رسیدِ تصمیم: رسیدها immutable (INSERT-only)، لینک‌ها append-only."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        with _LOCK:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS receipts("
                "receipt_id TEXT PRIMARY KEY, schema_version INTEGER NOT NULL,"
                "created_at TEXT NOT NULL, recorded_at TEXT NOT NULL,"
                "receipt_json TEXT NOT NULL, receipt_sha256 TEXT NOT NULL)")
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS receipt_links("
                "idempotency_key TEXT PRIMARY KEY, receipt_id TEXT NOT NULL,"
                "link_type TEXT NOT NULL, ref TEXT, note TEXT, recorded_at TEXT NOT NULL)")
            self._conn.commit()

    def record(self, receipt: dict) -> str:
        """اعتبارسنجی → رسیدِ immutable را INSERT کن (idempotent by receipt_id). خروجی receipt_id.
        اگر همان receipt_id قبلاً بود، دست‌نخورده می‌ماند (immutable). نقضِ قید → ReceiptValidationError."""
        norm = _validate(receipt)
        rid = _receipt_id(norm)
        rjson = _canon(norm)
        rsha = hashlib.sha256(rjson.encode("utf-8")).hexdigest()
        with _LOCK:
            self._conn.execute(
                "INSERT OR IGNORE INTO receipts(receipt_id,schema_version,created_at,recorded_at,"
                "receipt_json,receipt_sha256) VALUES(?,?,?,?,?,?)",
                (rid, SCHEMA_VERSION, norm["created_at"], _utc_now_iso(), rjson, rsha))
            self._conn.commit()
        return rid

    def link(self, receipt_id: str, link_type: str, ref: str, note=None) -> bool:
        """یک رویدادِ لینک (append-only) اضافه کن؛ **هرگز رسید را mutate نمی‌کند**.
        idempotent: همان (receipt,type,ref) دوباره = یک رکورد. True اگر رکوردِ نو نوشته شد."""
        if link_type not in LINK_TYPES:
            raise ReceiptValidationError(f"unknown link_type {link_type!r}")
        idem = _sha({"r": receipt_id, "t": link_type, "f": ref})
        with _LOCK:
            # رسید باید وجود داشته باشد (وگرنه لینکِ یتیم)
            exists = self._conn.execute(
                "SELECT 1 FROM receipts WHERE receipt_id=?", (receipt_id,)).fetchone()
            if not exists:
                raise ReceiptValidationError("cannot link to a non-existent receipt")
            cur = self._conn.execute(
                "INSERT OR IGNORE INTO receipt_links(idempotency_key,receipt_id,link_type,ref,note,recorded_at)"
                " VALUES(?,?,?,?,?,?)",
                (idem, receipt_id, link_type, str(ref), (str(note)[:200] if note else None), _utc_now_iso()))
            self._conn.commit()
            return cur.rowcount == 1

    def link_outcome(self, receipt_id: str, outcome_ref: str, note=None) -> bool:
        """join به outcome_store (idempotent، replayable). outcome_ref = event_id/idempotency_key آن‌جا."""
        return self.link(receipt_id, "outcome", outcome_ref, note)

    def resolve(self, receipt_id: str) -> dict:
        """رسیدِ immutable + وضعِ جاریِ لینک‌ها (folded). join‌های غایب = PENDING (هرگز جعلِ موفقیت).
        {} اگر رسید نباشد."""
        with _LOCK:
            row = self._conn.execute(
                "SELECT receipt_json, receipt_sha256 FROM receipts WHERE receipt_id=?",
                (receipt_id,)).fetchone()
            if not row:
                return {}
            links = self._conn.execute(
                "SELECT link_type, ref, recorded_at FROM receipt_links WHERE receipt_id=?"
                " ORDER BY recorded_at, idempotency_key", (receipt_id,)).fetchall()
        rec = json.loads(row[0])
        folded = {"outcome_ref": None, "test_result_ref": None, "review_ref": None,
                  "verdict_ref": None, "approval_link_ref": None}
        key = {"outcome": "outcome_ref", "test": "test_result_ref", "review": "review_ref",
               "verdict": "verdict_ref", "approval": "approval_link_ref"}
        for lt, ref, _ts in links:
            folded[key.get(lt, lt)] = ref            # آخرین لینکِ هر نوع
        # نبودِ outcome/verdict = PENDING صریح، نه جعلِ موفقیت
        rec["links"] = {k: (v if v is not None else "PENDING") for k, v in folded.items()}
        rec["receipt_id"] = receipt_id
        rec["integrity_ok"] = self.verify_integrity(receipt_id)
        return rec

    def verify_integrity(self, receipt_id: str) -> bool:
        """receipt_sha256 را دوباره محاسبه کن؛ دستکاریِ out-of-bandِ رسید را می‌گیرد."""
        with _LOCK:
            row = self._conn.execute(
                "SELECT receipt_json, receipt_sha256 FROM receipts WHERE receipt_id=?",
                (receipt_id,)).fetchone()
        if not row:
            return False
        return hashlib.sha256(row[0].encode("utf-8")).hexdigest() == row[1]

    def close(self):
        with _LOCK:
            try:
                self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")   # WALِ ویندوز را جمع کن
            except Exception:  # noqa: BLE001
                pass
            try:
                self._conn.close()
            except Exception:  # noqa: BLE001
                pass
