#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""notif_inbox.py — صندوقِ اعلانِ مینی‌اپ (کاهشِ فشارِ تلگرام، ۲۰۲۶-۰۸-۰۷).

چرا: امشب دایجست/گزارش‌های مغز-قلب-دکتر/کارتِ RFC/پیشنهادِ پا/هشدارِ فنی مالک را
غرق کردند. این ماژول یک صفِ مشترک است که هر تولیدکننده به‌جایِ ارسالِ مستقیمِ
تلگرام، می‌تواند در آن بنویسد؛ مینی‌اپ آن را در تبِ «اعلان‌ها» می‌خواند.

قاعدهٔ سخت: پشتِ فلگِ خودش (`OCTOPUS_WIRE_NOTIF_INBOX`، پیش‌فرض خاموش). خاموش =
`route()` دقیقاً همان `send_fn()` قبلی را صدا می‌زند — بایت‌به‌بایت رفتارِ امروز.

الگوی ذخیره‌سازی از `approval_store.py` قرض گرفته شده: `opslib.LockedJson` فقط
برای قفلِ بین‌پروسه‌ای (نه read()/write() خودش)، نوشتنِ اتمیک با tmp+os.replace.
این یک صفِ UI است نه لجر — pruneِ آیتم‌های *خوانده‌شده* بعد از سقف مجاز است؛
خوانده‌نشده هرگز prune نمی‌شود.

$0 · stdlib + opslib · fail-soft کامل (هیچ خطایی صداکنندهٔ beat را نمی‌کشد).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/telegram_center
_OPS = _HERE.parent                               # _ops

if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))
import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_NOTIF_INBOX"

_STORE_PATH = opslib.STATE_DIR / "telegram" / "notif-inbox.json"
_MAX_ITEMS = 300
_PING_COOLDOWN_S_DEFAULT = 900.0

_TITLES = {
    "health_digest": "🩺 دایجستِ سلامت",
    "brain_digest": "🧠 مغز (cortex)",
    "doctor_digest": "🩺 دکتر",
    "heart_digest": "🫀 قلب",
    "discovery": "🔍 یادگیری",
    "needs": "🔔 نیازت دارم",
    "rfc_card": "🔧 پیشنهادِ تکامل (RFC)",
    "leg_proposal": "📨 پیشنهادِ پا",
    "tech_alert": "⚠️ هشدارِ فنی",
}


def flag_on() -> bool:
    """env-flag با پیش‌فرض خاموش (allowlistِ truthy، هم‌راستا با ماژول‌های مشابه)."""
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def _empty_state() -> dict:
    return {"schema_version": 1, "items": [], "last_ping_ts": 0.0, "last_ping_marker_ts": 0.0}


def _load() -> dict:
    """fail-soft: نبود/خرابی → ساختارِ خالیِ معتبر (هرگز None/exception)."""
    try:
        if not _STORE_PATH.exists():
            return _empty_state()
        d = json.loads(_STORE_PATH.read_text("utf-8"))
        if not isinstance(d, dict):
            return _empty_state()
        if not isinstance(d.get("items"), list):
            d["items"] = []
        d.setdefault("schema_version", 1)
        d.setdefault("last_ping_ts", 0.0)
        d.setdefault("last_ping_marker_ts", 0.0)
        return d
    except (OSError, ValueError):
        return _empty_state()


def _save(state: dict) -> bool:
    """نوشتنِ اتمیک (tmp + os.replace). شکست → False (هرگز crash)."""
    try:
        _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _STORE_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), "utf-8")
        os.replace(tmp, _STORE_PATH)
        return True
    except (OSError, TypeError, ValueError):
        return False


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())


def _gen_id(category: str) -> str:
    ts = time.strftime("%Y%m%dT%H%M%S", time.localtime())
    h = hashlib.sha1(
        f"{category}{time.time()}{os.getpid()}".encode("utf-8")).hexdigest()[:8]
    safe_cat = str(category or "misc")[:32]
    return f"notif_{safe_cat}_{ts}_{h}"


def push(category: str, title: str = "", body: str = "", *, kind: str = "content",
          meta: "dict | None" = None) -> "str | None":
    """یک اعلان به صندوق اضافه کن. خروجی = id، یا `None` روی شکست (fail-soft).

    عمداً `None` نه رشتهٔ خالی: صداکننده‌هایی مثلِ center.py's health-digest که
    نتیجهٔ ارسال را با `is not None` می‌سنجند (نه فقط truthy) باید شکست را درست
    ببینند — رشتهٔ خالی از `is not None` رد می‌شد و دایجستِ نرسیده را «رسیده»
    علامت می‌زد (همان باگی که کامنتِ خودِ center.py دربارهٔ نشانگرِ flush هشدار
    می‌دهد).

    `title` اگر خالی باشد از `_TITLES[category]` پر می‌شود. `meta` برای آیتم‌های
    `kind="pointer"` استفاده می‌شود (مثلاً `{"goto_tab": "system", "rfc_id": "..."}`)."""
    cat = str(category or "misc")
    item = {
        "id": _gen_id(cat),
        "category": cat,
        "kind": str(kind or "content"),
        "title": str(title or _TITLES.get(cat, cat))[:200],
        "body": str(body or "")[:4000],
        "meta": meta if isinstance(meta, dict) else {},
        "created_at": _now_iso(),
        "created_ts": time.time(),
        "read": False,
        "read_at": None,
    }
    try:
        with opslib.LockedJson(_STORE_PATH):
            state = _load()
            state["items"].append(item)
            # prune: فقط آیتم‌های *خوانده‌شده*، از قدیمی‌ترین، وقتی از سقف رد شدیم —
            # خوانده‌نشده هرگز حذف نمی‌شود (§۹ ناوردیِ vault: هرگز حذفِ چیزی که مالک ندیده).
            if len(state["items"]) > _MAX_ITEMS:
                over = len(state["items"]) - _MAX_ITEMS
                read_idx = [i for i, it in enumerate(state["items"]) if it.get("read")]
                for idx in read_idx[:over]:
                    state["items"][idx] = None
                state["items"] = [it for it in state["items"] if it is not None]
            if not _save(state):
                return None
    except Exception:  # noqa: BLE001 — صندوق هرگز صداکننده را نمی‌کشد
        return None
    return item["id"]


def list_items(unread_only: bool = False, limit: int = 50) -> list:
    """جدیدترین‌ها اول. fail-soft → []."""
    state = _load()
    items = list(state.get("items", []))
    items.sort(key=lambda it: it.get("created_ts", 0) or 0, reverse=True)
    if unread_only:
        items = [it for it in items if not it.get("read")]
    return items[:max(0, int(limit))]


def unread_count() -> int:
    state = _load()
    return sum(1 for it in state.get("items", []) if not it.get("read"))


def mark_read(ids: "list | None" = None) -> int:
    """`ids=None` یعنی همه را خوانده‌شده کن. خروجی = تعدادِ واقعاً تغییریافته."""
    changed = 0
    try:
        with opslib.LockedJson(_STORE_PATH):
            state = _load()
            id_set = set(ids) if ids else None
            for it in state.get("items", []):
                if it.get("read"):
                    continue
                if id_set is not None and it.get("id") not in id_set:
                    continue
                it["read"] = True
                it["read_at"] = _now_iso()
                changed += 1
            if changed:
                if not _save(state):
                    return 0
    except Exception:  # noqa: BLE001
        return 0
    return changed


def route(category: str, title: str, body: str, *, send_fn, kind: str = "content",
           meta: "dict | None" = None):
    """قلابِ مشترکِ هر تولیدکننده: فلگ خاموش → `send_fn()` دقیقاً مثلِ قبل (بدونِ
    لمسِ صندوق). فلگ روشن → push به صندوق، `send_fn` هرگز صدا زده نمی‌شود.

    خروجی: نتیجهٔ `send_fn()` (فلگ خاموش) یا idِ صندوق (فلگ روشن — رشتهٔ غیرخالی
    یعنی موفق، هم‌ارز truthyِ خروجیِ اغلبِ send_fnهای این پروژه) — صداکننده‌هایی
    که خروجی را `is not None`/truthy چک می‌کنند بدونِ تغییر کار می‌کنند."""
    if not flag_on():
        return send_fn()
    return push(category, title, body, kind=kind, meta=meta)


def maybe_ping(send_fn) -> dict:
    """اگر از آخرین پینگ آیتمِ *نویی* رسیده (نه صرفاً خوانده‌نشدهٔ کهنه) و cooldown
    گذشته، یک پینگِ کوتاه (بدونِ محتوا) با `send_fn(text)` بفرست.

    `OCTOPUS_NOTIF_PING_COOLDOWN_S` (پیش‌فرض ۹۰۰) بازهٔ کمینه بینِ دو پینگ است.
    خروجی: `{"pinged": bool, "unread": int, "reason": str}` — fail-soft، هرگز
    exception به بیرون نشت نمی‌کند."""
    if not flag_on():
        return {"pinged": False, "unread": 0, "reason": "flag-off"}
    state = _load()
    items = state.get("items", [])
    marker = float(state.get("last_ping_marker_ts", 0.0) or 0.0)
    fresh = [it for it in items
              if not it.get("read") and float(it.get("created_ts", 0) or 0) > marker]
    if not fresh:
        return {"pinged": False, "unread": unread_count(), "reason": "no-fresh-items"}
    cooldown = float(os.environ.get(
        "OCTOPUS_NOTIF_PING_COOLDOWN_S", str(_PING_COOLDOWN_S_DEFAULT)))
    last_ping = float(state.get("last_ping_ts", 0.0) or 0.0)
    now = time.time()
    if now - last_ping < cooldown:
        return {"pinged": False, "unread": unread_count(), "reason": "cooldown"}
    unread = unread_count()
    text = f"🔔 {unread} چیزِ تازه توی پنل"
    try:
        ok = bool(send_fn(text))
    except Exception:  # noqa: BLE001 — پینگ هرگز beat را نمی‌کشد
        ok = False
    if ok:
        try:
            with opslib.LockedJson(_STORE_PATH):
                fresh_state = _load()
                fresh_state["last_ping_ts"] = now
                newest = max(
                    (float(it.get("created_ts", 0) or 0)
                     for it in fresh_state.get("items", [])),
                    default=marker)
                fresh_state["last_ping_marker_ts"] = max(marker, newest)
                _save(fresh_state)
        except Exception:  # noqa: BLE001
            pass
        return {"pinged": True, "unread": unread, "reason": "sent"}
    return {"pinged": False, "unread": unread, "reason": "send-failed"}


if __name__ == "__main__":   # pragma: no cover — نمای دستیِ اپراتور
    os.environ.setdefault(FLAG, "1")
    nid = push("tech_alert", body="دمو")
    print(json.dumps({"pushed": nid, "unread": unread_count(),
                       "items": list_items()}, ensure_ascii=False, indent=1))
