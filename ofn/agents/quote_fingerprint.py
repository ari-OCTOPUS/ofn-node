"""quote_fingerprint — اثرانگشتِ مقاوم به rollback (هات‌فیکس HF-2، حکم ناظر ۲۰۲۶-09-02).

گارد ۷ روزه در دیتابیس است؛ rollback دیتابیس آن را عقب می‌برد و همان کوت
دوباره می‌رود. این ماژول fingerprint کوت را در فایلِ append-only **بیرون از
دیتابیس** نگه می‌دارد (state dir — همان‌جا که بکاپِ شبانه دیتابیس جداست).
restore دیتابیس این فایل را نمی‌بندد.

fingerprint = sha256(lead_id ‖ scope_canonical_json ‖ rounded_total)
تست پذیرش (ناظر): دیتابیس به بکاپ برگردد + پایپ‌لاین اجرا شود → اگر کوتِ
تکراری تولید شد، هات‌فیکس کار نکرده. تست: test_hf.py::test_rollback_no_resend
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

FP_FILE = opslib.STATE_DIR / "quote-fingerprints.jsonl"


def _canonical(scope: dict, total) -> str:
    s = dict(scope or {})
    for k in ("works", "location"):
        s[k] = str(s.get(k) or "").strip().lower()
    try:
        s["total"] = round(float(total), 0) if total is not None else None
    except (TypeError, ValueError):
        s["total"] = None
    return json.dumps(s, sort_keys=True, ensure_ascii=False)


def fingerprint(lead_id: str, scope: dict, total) -> str:
    body = _canonical(scope, total)
    raw = f"{str(lead_id).strip().lower()}|{body}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def seen(fp: str, path: Path | None = None) -> bool:
    """جست‌وجوی خطی در فایلِ append-only (کوت‌ها کم‌شمارند؛ ساده و صادق).
    path در call-time خوانده می‌شود تا تست/مهاجرت بتواند آن را تزریق کند."""
    p = path or FP_FILE
    try:
        for ln in p.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                if json.loads(ln).get("fingerprint") == fp:
                    return True
            except Exception:  # noqa: BLE001
                continue
    except OSError:
        pass
    return False


def record(fp: str, qt_number: str, lead_id: str, total, path: Path | None = None):
    opslib.append_jsonl(path or FP_FILE, {
        "fingerprint": fp, "qt": qt_number, "lead_id": lead_id[:80],
        "total_aud": total, "ts": opslib.now_iso()})


def guard(lead_id: str, scope: dict, total, path: Path | None = None) -> tuple:
    """(fingerprint, already_seen) — caller در صورت seen ارسال نمی‌کند."""
    fp = fingerprint(lead_id, scope, total)
    return fp, seen(fp, path)
