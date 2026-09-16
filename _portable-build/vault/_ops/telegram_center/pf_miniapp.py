#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pf_miniapp.py — کارت‌های read-only ِ Project-F برای Mini App (PROP-D5 فاز ۱).

GO ِ مالک ۲۰۲۶-۰۸-۰۳ («مینی‌اپ رو بساز»). این ماژول **فقط می‌خوانَد**.

قراردادِ مرزی (غیرقابل‌مذاکره — قاعدهٔ قفل‌شدهٔ #۷ پروژه + سندِ SHADOW_ONLY):
  · بیرون از پوشهٔ پروژه فقط **aggregate/count** — صفر متنِ درفت، صفر کپشن،
    صفر بدنهٔ DM، صفر رسانه، صفر هویت. اگر روزی مالک بخواهد متنِ درفت هم در
    مینی‌اپ دیده شود، آن **پهن‌کردنِ مرزِ containment** است و رأیِ جداگانه
    می‌خواهد — این ماژول عمداً هیچ فیلدِ متنی‌ای از صف‌ها نمی‌خوانَد.
  · هیچ import ی از کدِ پروژه (`brain/`، `langar/`، `studio/`، `pf_os/`) —
    فقط خواندنِ JSON از دیسک. پس نه کدِ پروژه در پروسهٔ مرکز اجرا می‌شود، نه
    قانونِ لا‌مزاحمی نقض می‌شود.
  · هیچ نوشتن، هیچ mutate، هیچ اکشنِ بیرونی. صفِ تأیید است، نه افکتور.

fail-closed و سه‌حالتی (درسِ «نبودِ داده حکم نیست»): فایلِ غایب/خراب =
`unknown` با دلیل، **نه** صفرِ جعلی و نه «همه‌چیز امن». هر بولیِ ایمنی که
مبنایش روی دیسک نیست `null` می‌شود و نامش در `unknown_fields` می‌آید.

فلگ: `OCTOPUS_PF_MINIAPP` (پیش‌فرض خاموش). خاموش = مسیرها اصلاً وجود ندارند
(404) و این ماژول هیچ فایلی را حتی باز نمی‌کند — flag-off یعنی no-op.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_VAULT = _OPS.parent

FLAG = "OCTOPUS_PF_MINIAPP"

# نامِ پوشهٔ پروژه فارسی است؛ مسیر با کدِ «Project-F» صدا زده می‌شود.
PF_ROOT = _VAULT / "03 - Projects" / "اونلی فنز"

STALE_AFTER_S = 24 * 3600.0        # snapshot ِ کهنه‌تر از این خاکستری است
KARMA_THRESHOLD_DEFAULT = 20       # هم‌راستا با WarmupGuard پروژه

# آستانه‌های hard-coded ِ داشبورد (drafts-awaiting-gate/kpi-dashboard-spec.md).
# عمداً اینجا **بازتعریف نمی‌شوند** بلکه رونویسیِ همان سند‌اند؛ UI فقط رندر
# می‌کند و حق ندارد منطقِ چراغ را عوض کند.
KPI_THRESHOLDS = {
    "clicks_cumulative": {"green": 200, "red": 100, "dir": "up",
                          "on_red": "ترکیبِ کانال‌ها عوض شود"},
    "click_to_follow_pct": {"green": 10.0, "red": 5.0, "dir": "up",
                            "on_red": "landing بازطراحی شود"},
    "unlock_rate_pct": {"green": 15.0, "red": 5.0, "dir": "up",
                        "on_red": "بازقیمت‌گذاری (دو هفتهٔ متوالی)"},
    "delivery_rate_pct": {"green": 80.0, "red": 50.0, "dir": "up",
                          "on_red": "گفت‌وگوی ساختار با پارتنر"},
    "free_to_paid_pct": {"green": 5.0, "red": 2.0, "dir": "up",
                         "on_red": "بازبینیِ مدل"},
}


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


# ── scrub (کمربندِ دوم؛ خروجی ذاتاً عددی است ولی رشته‌های manifest هم رد می‌شوند)
_TOKEN_RE = re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b")
_SECRET_RE = re.compile(
    r"(?i)(bot_token|api[_-]?key|secret|password|passwd|chat_id|bearer|sk-)"
    r"\s*[:=]\s*[^\s,;\"']+")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def _scrub(text: Any) -> str:
    t = text if isinstance(text, str) else str(text)
    t = _TOKEN_RE.sub("<TOKEN_REDACTED>", t)
    t = _SECRET_RE.sub(r"\1=<REDACTED>", t)
    t = _EMAIL_RE.sub("<EMAIL_REDACTED>", t)
    return t


def _read_json(path: Path) -> "tuple[Any, str | None]":
    """(data, reason_if_unavailable). هرگز استثنا بیرون نمی‌دهد."""
    try:
        if not path.exists():
            return None, "missing"
        raw = path.read_text(encoding="utf-8", errors="replace")
        return json.loads(raw), None
    except json.JSONDecodeError:
        return None, "corrupt"
    except OSError:
        return None, "unreadable"
    except Exception:  # noqa: BLE001 — شک = ناموجود
        return None, "error"


def _age_s(path: Path) -> "float | None":
    try:
        return max(0.0, time.time() - path.stat().st_mtime)
    except Exception:  # noqa: BLE001
        return None


def _freshness(path: Path) -> dict:
    """هر کارت باید بگوید داده‌اش چقدر کهنه است — snapshot ِ کهنه سبز رندر نشود."""
    age = _age_s(path)
    return {"age_s": None if age is None else round(age, 1),
            "stale": True if age is None else bool(age > STALE_AFTER_S)}


def _count_by(items: Any, key: str) -> dict:
    out: dict = {}
    if not isinstance(items, list):
        return out
    for it in items:
        if isinstance(it, dict):
            v = str(it.get(key, "?"))
            out[v] = out.get(v, 0) + 1
    return out


def _items_of(data: Any) -> list:
    """صف‌ها یا لیستِ خام‌اند یا dict ِ دارای کلیدِ items — هر دو را می‌پذیریم."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("items", "queue", "drafts"):
            v = data.get(k)
            if isinstance(v, list):
                return v
    return []


# ── کارت ۱: وضعیت (دقیقاً schema ِ SHADOW_ONLY، نه یک فیلد بیشتر) ──────────
def get_pf_status(root: "Path | None" = None) -> dict:
    pf = Path(root) if root else PF_ROOT
    unknown: list = []

    drafts, r_d = _read_json(pf / "studio" / "drafts.json")
    acq, r_a = _read_json(pf / "brain" / "acq_queue.json")
    dm, r_m = _read_json(pf / "brain" / "dm_queue.json")
    locks, r_l = _read_json(pf / "langar" / "channel_locks.json")
    reddit, r_r = _read_json(pf / "langar" / "reddit_state.json")
    octo, r_o = _read_json(pf / "langar" / "octopus.json")

    def _n(data, reason, field, status_key, wanted):
        if reason is not None:
            unknown.append(f"{field}:{reason}")
            return None
        c = _count_by(_items_of(data), status_key)
        return int(c.get(wanted, 0))

    drafts_count = _n(drafts, r_d, "drafts_count", "status", "pending")
    acq_ready = _n(acq, r_a, "acq_ready", "status", "ready")
    dm_pending = _n(dm, r_m, "dm_pending", "status", "pending_review")

    if r_l is not None:
        unknown.append(f"full_stop:{r_l}")
        full_stop = None
    else:
        full_stop = bool(locks.get("full_stop")) if isinstance(locks, dict) else None
        if full_stop is None:
            unknown.append("full_stop:shape")

    if r_r is not None:
        unknown.append(f"karma_met:{r_r}")
        karma_met = None
    else:
        karma_met = None
        if isinstance(reddit, dict):
            if "threshold_met" in reddit:
                karma_met = bool(reddit.get("threshold_met"))
            elif "reddit_karma" in reddit:
                try:
                    karma_met = int(reddit.get("reddit_karma") or 0) >= KARMA_THRESHOLD_DEFAULT
                except Exception:  # noqa: BLE001
                    karma_met = None
        if karma_met is None:
            unknown.append("karma_met:shape")

    beat = None
    if r_o is None and isinstance(octo, dict):
        for k in ("last_beat", "heartbeat", "updated_at", "ts"):
            if octo.get(k):
                beat = _scrub(octo.get(k))[:40]
                break
    if beat is None:
        unknown.append(f"beat:{r_o or 'shape'}")

    kill = (pf / "langar" / "KILL").exists()
    halt = (pf / "studio" / "HALT").exists()
    paused = (_OPS / "state" / "projectf-paused.flag").exists()
    mode = "killed" if kill else ("halted" if halt else ("paused" if paused else "propose-only"))

    return {
        "status": "ok",
        # ── schema ِ بستهٔ 05_OCTOPUS_ADAPTER_SHADOW — دقیقاً همین هفت فیلد
        "beat": beat,
        "mode": mode,
        "drafts_count": drafts_count,
        "dm_pending": dm_pending,
        "acq_ready": acq_ready,
        "full_stop": full_stop,
        "karma_met": karma_met,
        # ── متادیتای صداقت (نه دادهٔ کسب‌وکار)
        "unknown_fields": unknown,
        "outward_execution": False,
        "content_free": True,
        "freshness": {
            "drafts": _freshness(pf / "studio" / "drafts.json"),
            "acq": _freshness(pf / "brain" / "acq_queue.json"),
            "dm": _freshness(pf / "brain" / "dm_queue.json"),
        },
    }


# ── کارت ۲: گیت‌ها و بلاکرهای انسانی (از MANIFEST ِ صفر-PII) ───────────────
def get_pf_gates(root: "Path | None" = None) -> dict:
    pf = Path(root) if root else PF_ROOT
    mpath = pf / "PROJECT-F-CONTROL-MANIFEST.json"
    data, reason = _read_json(mpath)
    if reason is not None:
        return {"status": "unknown", "reason": f"manifest {reason}",
                "note": "بدونِ manifest هیچ ادعایی دربارهٔ گیت‌ها نمی‌کنیم (fail-closed)"}
    if not isinstance(data, dict):
        return {"status": "unknown", "reason": "manifest shape"}

    snap = data.get("status_snapshot") if isinstance(data.get("status_snapshot"), dict) else {}
    gates_raw = data.get("gates") if isinstance(data.get("gates"), dict) else {}
    gates = {}
    for name, g in gates_raw.items():
        if isinstance(g, dict):
            gates[str(name)] = {
                "status": _scrub(g.get("status", "?"))[:120],
                "condition": _scrub(g.get("condition", ""))[:220],
                "eval": _scrub(g.get("eval", ""))[:60],
            }
    pending = data.get("open_pending_verdicts")
    pending_list = [_scrub(v)[:160] for v in pending][:20] if isinstance(pending, list) else []

    # مهرِ انسانی — تنها فایلی که pf_os/capabilities هم دنبالش می‌گردد.
    stamp_go = (pf / "00 - Control" / "GATE-STAMP-GO").exists()

    return {
        "status": "ok",
        "execution_state": _scrub(snap.get("execution_state", "?"))[:200],
        "primary_blocker": _scrub(snap.get("primary_blocker", "?"))[:220],
        "security_gate": _scrub(snap.get("security_gate", "?"))[:80],
        "pending_human_verdicts": snap.get("pending_human_verdicts"),
        "gates": gates,
        "open_pending_verdicts": pending_list,
        "gate_stamp_go_file": stamp_go,
        "outward_allowed": bool(stamp_go),   # نبودِ مهر = قفل (fail-closed)
        "kill_switches": {
            "langar_KILL": (pf / "langar" / "KILL").exists(),
            "studio_HALT": (pf / "studio" / "HALT").exists(),
            "projectf_paused": (_OPS / "state" / "projectf-paused.flag").exists(),
            "STOP_MINIAPP": (_OPS / "STOP-MINIAPP").exists(),
        },
        "freshness": _freshness(mpath),
    }


# ── کارت ۳: صف‌ها (فقط شمار و شناسه — هیچ متنی) ───────────────────────────
_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,48}$")


def _safe_ids(items: list, limit: int = 12) -> list:
    """فقط شناسه‌هایی که شکلشان id است. هر چیزِ دیگر (که ممکن است متن باشد)
    دور ریخته می‌شود — گاردِ ساختاری در برابرِ نشتِ محتوا."""
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        v = it.get("id") or it.get("item_id") or it.get("draft_id")
        if isinstance(v, str) and _ID_RE.match(v):
            out.append(v)
        if len(out) >= limit:
            break
    return out


def get_pf_queue(root: "Path | None" = None) -> dict:
    pf = Path(root) if root else PF_ROOT
    out: dict = {"status": "ok", "content_free": True,
                 "note": "فقط شمار و شناسه — متنِ درفت عمداً از مرز عبور نمی‌کند"}
    for key, rel, status_key in (
        ("acquisition", pf / "brain" / "acq_queue.json", "status"),
        ("dm", pf / "brain" / "dm_queue.json", "status"),
        ("studio_drafts", pf / "studio" / "drafts.json", "status"),
    ):
        data, reason = _read_json(rel)
        if reason is not None:
            out[key] = {"status": "unknown", "reason": reason,
                        "counts": {}, "ids": []}
            continue
        items = _items_of(data)
        out[key] = {
            "status": "ok",
            "counts": _count_by(items, status_key),
            "total": len(items),
            "flagged": len([i for i in items
                            if isinstance(i, dict) and i.get("flagged")]),
            "ids": _safe_ids(items),
            "freshness": _freshness(rel),
        }
    return out


# ── کارت ۴: KPI با چراغِ آستانه‌ای (منطق از spec، نه بازتعریف در UI) ───────
def _light(name: str, value) -> dict:
    th = KPI_THRESHOLDS.get(name)
    if th is None or value is None:
        return {"light": "unknown", "reason": "no data" if value is None else "no threshold"}
    try:
        v = float(value)
    except Exception:  # noqa: BLE001
        return {"light": "unknown", "reason": "not numeric"}
    if v >= float(th["green"]):
        return {"light": "green"}
    if v < float(th["red"]):
        return {"light": "red", "action": th["on_red"]}
    return {"light": "amber", "action": th["on_red"]}


def _pct(num, den):
    try:
        n, d = float(num), float(den)
        return round(100.0 * n / d, 2) if d > 0 else None
    except Exception:  # noqa: BLE001
        return None


def get_pf_kpi(root: "Path | None" = None) -> dict:
    pf = Path(root) if root else PF_ROOT
    kpath = pf / "langar" / "kpi.json"
    data, reason = _read_json(kpath)
    if reason is not None:
        return {"status": "unknown", "reason": f"kpi {reason}",
                "note": "هیچ عددی جعل نمی‌شود؛ نبودِ فایل یعنی نبودِ داده",
                "thresholds": KPI_THRESHOLDS}
    weeks = data.get("weeks") if isinstance(data, dict) else None
    if not isinstance(weeks, list) or not weeks:
        return {"status": "no_data", "weeks": 0,
                "note": "هنوز هیچ هفته‌ای ثبت نشده — صفرِ صادقانه، نه جعل",
                "thresholds": KPI_THRESHOLDS, "freshness": _freshness(kpath)}
    last = weeks[-1] if isinstance(weeks[-1], dict) else {}
    clicks_cum = 0
    for w in weeks:
        if isinstance(w, dict):
            try:
                clicks_cum += int(w.get("clicks") or 0)
            except Exception:  # noqa: BLE001
                pass
    metrics = {
        "clicks_cumulative": clicks_cum,
        "click_to_follow_pct": _pct(last.get("follows"), last.get("clicks")),
        "unlock_rate_pct": _pct(last.get("ppv_unlocks"), last.get("free_subs")),
        "delivery_rate_pct": (round(float(last.get("delivery_rate") or 0) * 100, 2)
                              if (last.get("delivery_rate") or 0) <= 1
                              else float(last.get("delivery_rate"))),
        "free_to_paid_pct": _pct(last.get("paid_conversions"), last.get("free_subs")),
    }
    lights = {k: _light(k, v) for k, v in metrics.items()}
    return {
        "status": "ok",
        "weeks_recorded": len(weeks),
        "week_start": _scrub(last.get("week_start", "?"))[:32],
        "raw": {k: last.get(k) for k in
                ("revenue_usd", "ppv_unlocks", "posts", "clicks", "follows",
                 "free_subs", "paid_conversions", "new_fans", "fans_total")},
        "metrics": metrics,
        "lights": lights,
        "thresholds": KPI_THRESHOLDS,
        "freshness": _freshness(kpath),
    }


# ── کارت ۵: گاردها (چراغِ ایمنیِ کانال‌ها) ────────────────────────────────
def get_pf_guards(root: "Path | None" = None) -> dict:
    pf = Path(root) if root else PF_ROOT
    locks, r_l = _read_json(pf / "langar" / "channel_locks.json")
    reddit, r_r = _read_json(pf / "langar" / "reddit_state.json")

    if r_l is not None:
        lock_block = {"status": "unknown", "reason": r_l,
                      "note": "نبودِ فایل ≠ «قفلی نیست»"}
    else:
        chans = {}
        raw = locks.get("channels") if isinstance(locks, dict) else None
        if isinstance(raw, dict):
            for ch, c in raw.items():
                if isinstance(c, dict):
                    chans[str(ch)] = {
                        "warnings": len(c.get("warnings") or []),
                        "locked": bool(c.get("locked")),
                    }
        lock_block = {
            "status": "ok",
            "full_stop": bool(locks.get("full_stop")) if isinstance(locks, dict) else None,
            "channels": chans,
            "freshness": _freshness(pf / "langar" / "channel_locks.json"),
        }

    if r_r is not None:
        warm = {"status": "unknown", "reason": r_r}
    else:
        karma = None
        if isinstance(reddit, dict):
            try:
                karma = int(reddit.get("reddit_karma") or 0)
            except Exception:  # noqa: BLE001
                karma = None
        warm = {
            "status": "ok" if karma is not None else "unknown",
            "karma": karma,
            "threshold": KARMA_THRESHOLD_DEFAULT,
            "met": None if karma is None else karma >= KARMA_THRESHOLD_DEFAULT,
            "freshness": _freshness(pf / "langar" / "reddit_state.json"),
        }
    return {"status": "ok", "channel_locks": lock_block, "warmup": warm}


# ── کارت ۶: قابلیت‌ها (هرگز دکمهٔ مرده — هر قفل با دلیل) ──────────────────
_FALLBACK_CAPS = [
    {"name": "account_create", "level": "red", "executable": False},
    {"name": "publish", "level": "red", "executable": False},
    {"name": "dm_send", "level": "red", "executable": False},
    {"name": "money.move", "level": "red", "executable": False},
    {"name": "daemon.start_live", "level": "red", "executable": False},
]


def get_pf_capabilities(root: "Path | None" = None) -> dict:
    """رجیستریِ قابلیت‌ها + دلیلِ پویا. منبعِ ترجیحی فایلِ pf_os؛ در نبودش
    فهرستِ قفلِ محافظه‌کارانه (هیچ‌وقت «باز» فرض نمی‌کنیم)."""
    pf = Path(root) if root else PF_ROOT
    gates = get_pf_gates(pf)
    outward = bool(gates.get("outward_allowed"))
    reason_locked = ("GATE 0 باز است و مهرِ انسانیِ GATE-STAMP-GO روی دیسک نیست"
                     if not outward else "گیت باز است ولی اجرا همچنان دستیِ انسان است")

    caps_data, reason = _read_json(pf / "pf_os" / "PF_STATE" / "capabilities.json")
    items = _items_of(caps_data) if reason is None else []
    if not items:
        items = list(_FALLBACK_CAPS)
        src = f"fallback ({reason or 'empty'})"
    else:
        src = "pf_os/capabilities.json"

    out = []
    for c in items:
        if not isinstance(c, dict):
            continue
        lvl = str(c.get("level", "red"))
        execu = bool(c.get("executable")) and outward and lvl != "red"
        out.append({
            "name": _scrub(c.get("name", "?"))[:48],
            "level": lvl,
            "executable": execu,
            "reason": _scrub(c.get("reason") or reason_locked)[:160],
        })
    return {"status": "ok", "source": src, "outward_allowed": outward,
            "capabilities": out,
            "note": "هیچ دکمهٔ مرده‌ای رندر نمی‌شود؛ هر قفل دلیلِ خودش را دارد"}


# ── dispatcher ────────────────────────────────────────────────────────────
_HANDLERS = {
    "/api/pf/status": get_pf_status,
    "/api/pf/gates": get_pf_gates,
    "/api/pf/queue": get_pf_queue,
    "/api/pf/kpi": get_pf_kpi,
    "/api/pf/guards": get_pf_guards,
    "/api/pf/capabilities": get_pf_capabilities,
}

PATHS = frozenset(_HANDLERS)


def dispatch_api(path: str, root: "Path | None" = None) -> "tuple[int, bytes, str]":
    """(status, body_bytes, content_type). فلگ خاموش = 404 (مسیر وجود ندارد)."""
    ctype = "application/json; charset=utf-8"
    if not enabled():
        return 404, b'{"status":"not_found"}', ctype
    fn = _HANDLERS.get(str(path or "").split("?", 1)[0])
    if fn is None:
        return 404, b'{"status":"not_found"}', ctype
    try:
        data = fn(root)
        return 200, json.dumps(data, ensure_ascii=False, default=str).encode("utf-8"), ctype
    except Exception as exc:  # noqa: BLE001 — fail-closed، هرگز crash
        body = json.dumps({"status": "error", "reason": type(exc).__name__},
                          ensure_ascii=False).encode("utf-8")
        return 500, body, ctype


if __name__ == "__main__":
    import sys
    os.environ.setdefault(FLAG, "1")       # self-test فقط در همین اجرا
    for p in sorted(PATHS):
        st, body, _ = dispatch_api(p)
        sys.stdout.buffer.write(f"=== {p} → {st}\n".encode("utf-8"))
        sys.stdout.buffer.write(body[:700] + b"\n\n")
