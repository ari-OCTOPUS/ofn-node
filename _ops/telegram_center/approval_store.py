#!/usr/bin/env python3
r"""approval_store.py — پلِ صفِ تأیید بینِ دو دنیا (فاز E اختاپوس).

دو منبعِ تأیید در این پروژه وجود دارد و هر دو باید زنده بمانند:

  ۱. ``_ops/state/telegram/approvals/*.json`` — تاریخچهٔ verdictهای ثبت‌شدهٔ مالک
     (قراردادِ قدیمیِ center.py: یک فایل per-decision با فیلدهای id/verdict/ts).
  ۲. ``_octopus/state/approvals.json`` — pending queue اختاپوس (فاز ۱): لیستی از
     jobهایی که منتظرِ تصمیمِ انسان‌اند، با risk/dry_run_report/requires_confirmation.

این ماژول یک **adapter** است: jobها را در صفِ اختاپوس می‌سازد/تغییر می‌دهد و در عین
حالت تاریخچهٔ verdict را در مسیرِ قدیمی هم می‌نویسد (برای سازگاریِ ابزارهای قدیمی).

قوانین ایمنی (همان ناوردی‌های telegram_center):
  - idها sanitize می‌شوند (ضدِ path-traversal؛ فقط ``[A-Za-z0-9_-.]``).
  - هر write اتمیک است (tmp + os.replace).
  - محتوای کاربر هرگز در job ذخیره نمی‌شود — فقط title/type/risk/content-free.
  - تأیید/رد فقط status را عوض می‌کند؛ اجرای واقعیِ job (اگر risk=high) به power.py
    یا handlerهای مرکز واگذار می‌شود — این لایه فقط state است.
  - fail-soft: هر خطا → پیش‌فرضِ امن (False / [] )، هرگز crashِ صداکننده.

$0 · stdlib-only · import-time خالص. مصرف‌کننده: center.py (callbackهای ap:*).
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent                # _ops
_ROOT = _OPS.parent                                           # F:\backup

# مسیرِ قدیمی (تاریخچهٔ verdict) — قراردادِ center._record_approval
_LEGACY_DIR = _OPS / "state" / "telegram" / "approvals"

# مسیرِ نو (pending queue) — فاز ۱ اختاپوس
_OCTOPUS_STATE = _ROOT / "_octopus" / "state"
_APPROVALS_JSON = _OCTOPUS_STATE / "approvals.json"
_AUDIT_PATH = _ROOT / "_octopus" / "logs" / "audit.log"

_ID_SAFE = re.compile(r"[^A-Za-z0-9_.\-]")
STATUS_ORDER = ("pending", "approved", "rejected", "done")


def _sanitize_id(raw: str) -> str:
    """id از کاربر/کهکشان می‌آید — هرگز خام واردِ نامِ فایل نمی‌شود."""
    clean = _ID_SAFE.sub("-", str(raw or ""))[:64].strip("-_.")
    return clean or "unknown"


_CB_TTL_SECONDS = 24 * 3600   # P3: عمرِ توکنِ callback (۲۴ ساعت)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())


def _now_ts() -> str:
    return time.strftime("%Y%m%dT%H%M%S", time.localtime())


# ─── خواندن/نوشتنِ approvals.json اختاپوس (اتمیک) ──────────────────────────────
def _load_octopus_approvals() -> dict:
    """ساختارِ فاز ۱: {schema_version, pending:[], approved:[], rejected:[], done:[]}.

    fail-soft: نبود/خرابی → ساختارِ خالیِ معتبر (هرگز None)."""
    try:
        if not _APPROVALS_JSON.exists():
            return _empty_state()
        d = json.loads(_APPROVALS_JSON.read_text("utf-8"))
        if not isinstance(d, dict):
            return _empty_state()
        for k in ("pending", "approved", "rejected", "done"):
            if not isinstance(d.get(k), list):
                d[k] = []
        return d
    except (OSError, ValueError):
        return _empty_state()


def _empty_state() -> dict:
    return {"schema_version": 1, "pending": [], "approved": [], "rejected": [], "done": []}


def _save_octopus_approvals(state: dict) -> bool:
    """نوشتنِ اتمیک. شکست → False (هرگز crash)."""
    try:
        _APPROVALS_JSON.parent.mkdir(parents=True, exist_ok=True)
        tmp = _APPROVALS_JSON.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, _APPROVALS_JSON)
        return True
    except (OSError, TypeError, ValueError):
        return False


def _audit(event: str, detail: str = "") -> None:
    try:
        _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": _now_iso(), "event": event, "result": detail}
        with open(_AUDIT_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ─── API عمومی ──────────────────────────────────────────────────────────────────
def _gen_id(job_type: str) -> str:
    """idِ پایدار و خوانا: ``job_<type>_<ts>`` (sanitize شده)."""
    base = _sanitize_id(f"{job_type}_{_now_ts()}")
    return f"job_{base}"


def add_pending(job: dict) -> str:
    """افزودنِ یک job به صفِ pending. خروجی = id.

    job باید حداقل ``type`` و ``title`` داشته باشد؛ ``risk`` پیش‌فرض ``read``،
    ``requires_confirmation`` پیش‌فرض True. id اگر داده نشود ساخته می‌شود.
    id به‌همین‌شکل در verdictِ قدیمی هم (پس از approve/reject) ثبت می‌شود."""
    if not isinstance(job, dict):
        return ""
    jtype = _sanitize_id(str(job.get("type") or "task"))
    raw_id = str(job.get("id") or "").strip()
    jid = _sanitize_id(raw_id) if raw_id else _gen_id(jtype)
    rec = {
        "id": jid,
        "type": jtype,
        "title": str(job.get("title") or job.get("type") or "job")[:160],
        "status": "pending",
        "risk": str(job.get("risk") or "read"),
        "created_at": _now_iso(),
        # P3 (2026-07-20 Stage-1): مهرِ انقضا برای توکنِ callback (پیش‌فرض ۲۴ ساعت).
        # همیشه ثبت می‌شود (بی‌خطر وقتی فلگ توکن خاموش است — هیچ مصرف‌کننده‌ای ندارد).
        "expires_epoch": int(time.time()) + _CB_TTL_SECONDS,
        "requires_confirmation": bool(job.get("requires_confirmation", True)),
        "dry_run_report": str(job.get("dry_run_report") or "")[:500] or None,
        "source": str(job.get("source") or "telegram"),
    }
    state = _load_octopus_approvals()
    # id تکراری → یکی نشو (جلوگیری از spam)
    if any(item.get("id") == jid for item in state["pending"]):
        return jid
    state["pending"].append(rec)
    if _save_octopus_approvals(state):
        _audit("approval.add_pending", f"id={jid} risk={rec['risk']}")
    return jid


def _move(jid: str, from_list: str, to_list: str) -> bool:
    """انتقالِ یک job از یک bucket به دیگری (atomic)."""
    jid = _sanitize_id(jid)
    state = _load_octopus_approvals()
    src = state.get(from_list, [])
    dst = state.get(to_list, [])
    moved = None
    for i, item in enumerate(src):
        if isinstance(item, dict) and item.get("id") == jid:
            moved = src.pop(i)
            break
    if moved is None:
        return False
    moved["status"] = to_list
    moved[f"{to_list}_at"] = _now_iso()
    dst.append(moved)
    ok = _save_octopus_approvals(state)
    if ok:
        _audit(f"approval.{to_list}", f"id={jid} from={from_list}")
    return ok


def approve(jid: str) -> bool:
    """pending → approved. خروجی = موفق؟"""
    return _move(jid, "pending", "approved")


def reject(jid: str) -> bool:
    """pending → rejected. خروجی = موفق؟"""
    return _move(jid, "pending", "rejected")


def mark_done(jid: str) -> bool:
    """approved → done (پس از اجرای واقعی). هر status → done مجاز نیست (fail-soft)."""
    # اول از approved، اگر نبود از pending (اجرای مستقیم بدون approve)
    return _move(jid, "approved", "done") or _move(jid, "pending", "done")


def load_pending() -> list:
    """لیستِ jobهای pending (content-free: id/type/risk فقط)."""
    state = _load_octopus_approvals()
    return [item for item in state.get("pending", []) if isinstance(item, dict)]


def get(jid: str) -> "dict | None":
    """یک job را از هر bucket پیدا کن. fail-soft → None."""
    jid = _sanitize_id(jid)
    state = _load_octopus_approvals()
    for bucket in STATUS_ORDER:
        for item in state.get(bucket, []):
            if isinstance(item, dict) and item.get("id") == jid:
                return item
    return None


def summary() -> dict:
    """شمارشِ هر bucket برای نمایش در کارت. fail-soft → صفرها."""
    state = _load_octopus_approvals()
    return {bucket: len(state.get(bucket, [])) for bucket in STATUS_ORDER}


# ─── bridge با دنیایِ قدیمی (_ops/state/telegram/approvals/*.json) ────────────────
def sync_to_octopus_state() -> dict:
    """خواندنِ verdictهای قدیمی و بازگرداندنِ خلاصه برای کارت.

    این تابع state قدیمی را تغییر نمی‌دهد — فقط می‌خواند تا UI بتواند تاریخچه را
    کنارِ pending queue نشان دهد. fail-soft → {} اگر مسیر غایب است."""
    try:
        if not _LEGACY_DIR.exists():
            return {"count": 0, "recent": []}
        files = sorted(_LEGACY_DIR.glob("*.json"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        recent = []
        for p in files[:6]:
            try:
                rec = json.loads(p.read_text("utf-8"))
                if isinstance(rec, dict):
                    recent.append({
                        "id": str(rec.get("id", "?"))[:64],
                        "verdict": str(rec.get("verdict", "?"))[:12],
                        "ts": str(rec.get("ts", "?"))[:25],
                    })
            except (OSError, ValueError):
                continue
        return {"count": len(files), "recent": recent}
    except OSError:
        return {"count": 0, "recent": []}


def record_legacy_verdict(jid: str, verdict: str, source: str = "tg-center") -> bool:
    """ثبتِ verdict در مسیرِ قدیمی (هم‌شکلِ center._record_approval) برای ابزارهای قدیمی.

    این تابع زمانی صدا زده می‌شود که approve/reject از کارتِ اختاپوس رخ دهد، تا
    تاریخچه در هر دو دنیا یکسان بماند. fail-soft → False."""
    jid = _sanitize_id(jid)
    verdict = str(verdict)[:12]
    rec = {"id": jid, "verdict": verdict, "ts": _now_iso(), "source": source}
    try:
        _LEGACY_DIR.mkdir(parents=True, exist_ok=True)
        p = _LEGACY_DIR / f"{jid}.json"
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, p)
        # append به jsonl تاریخچه (قراردادِ قدیمی)
        with open(_LEGACY_DIR / "approvals.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


if __name__ == "__main__":
    # دمو — ساخت/تأیید/رد در sandbox واقعی (روی approvals.json اختاپوس)
    s_before = summary()
    jid = add_pending({"type": "metadata_scan", "title": "نقشه‌برداری کامل",
                       "risk": "read"})
    print("added:", jid, "pending now:", len(load_pending()))
    print("approve:", approve(jid), "summary:", summary())
    print("legacy sync:", sync_to_octopus_state()["count"], "verdicts")
