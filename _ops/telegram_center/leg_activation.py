#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""leg_activation — قالبِ «پای فعال‌شونده با ایجنتِ موازی» (منشور §۵، موج W4).

حکمِ منشور برای پاهای خلوت (Mining/Crypto/استودیو/…): «ساختِ زیرساخت برای
فعال‌سازی با ایجنت‌های موازی؛ تا آن روز: پیام فقط رخدادِ واقعی، صفر template.»

این ماژول سه چیز می‌دهد و هیچ اثرِ بیرونی ندارد:
  ۱. `manifest_skeleton` — اسکلتِ capability-manifest ِ معتبر (۱۲ فیلدِ
     `validate_contract.py`؛ `registration_is_authorization: false` — ثبت مجوز
     نیست، فعال‌سازی رأیِ جداگانهٔ مالک است).
  ۲. `activation_status` — DORMANT | READY | ACTIVE از سه شاهدِ روی دیسک:
     manifest ِ معتبر + تاپیک در config ِ مرکز + فعالیتِ leg_tasks در ۱۴ روز.
  ۳. `zero_template_guard` — نگهبانِ صفر-template: متنِ boilerplate را علامت
     می‌زند تا پای خلوت ساختاراً نتواند filler بفرستد (درسِ اسکنِ ۰۷-۲۹:
     ~۱۰۰٪ پاسخ‌های گروه template بودند).

`activate` فقط نقشه می‌دهد (propose-only): چه چیزی باید ساخته شود تا پا فعال
شود. **در این موج هرگز تاپیک نمی‌سازد و هیچ callable ِ تزریقی را صدا نمی‌زند** —
ساختن کارِ ایجنتِ موازیِ آینده با رأیِ مالک است.

مرزها: نه شبکه، نه ارسال، نه نوشتن روی دیسک (به‌جز هیچ — این ماژول فقط
می‌خواند). state ِ leg_tasks از `opslib.STATE_DIR` می‌آید (harness ایزوله‌اش
می‌کند). مسیرِ manifest ها با `OCTOPUS_LEG_MANIFEST_DIR` تزریق‌پذیر است.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# ۱۴ روز — پنجرهٔ «این پا واقعاً زنده است»
ACTIVE_WINDOW_S = 14 * 86400.0

DORMANT, READY, ACTIVE = "DORMANT", "READY", "ACTIVE"

# ── قراردادِ manifest (آینهٔ دقیقِ validate_contract.py::validate_manifest) ──
# ⚠️ اگر validate_contract.py فیلدی اضافه/کم کرد، تستِ drift-guard قرمز می‌شود.
MANIFEST_SCHEMA = "octopus.capability-manifest.v1"
MANIFEST_REQUIRED = (
    "schema", "capability_id", "title", "version", "owner_phrases",
    "read_handler", "action_contract", "risk_class", "owner_gate",
    "surface", "runtime_status_probe", "tests",
)
_SURFACES = ("owner_outer_dm", "owner_inner_dm", "legs_forum_group")
_RISKY = ("medium", "high", "forbidden")


def _safe_key(leg_key: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", str(leg_key or "").lower()) or "unknown"


def manifest_skeleton(leg_key: str, title: str) -> dict:
    """اسکلتِ manifest ِ قراردادی برای یک پای خلوت — همین‌طور که هست از
    `validate_contract.py` پاس می‌شود. ثبتِ manifest **مجوز نیست**."""
    key = _safe_key(leg_key)
    t = str(title or key).strip()[:80] or key
    return {
        "schema": MANIFEST_SCHEMA,
        "capability_id": f"leg.{key}.activation",
        "version": "0.1.0",
        "title": t,
        "owner_phrases": [f"وضعیت {t}", f"گزارش {t}", f"صف {t}"],
        "read_handler": "telegram_center/leg_tasks.py:card_text",
        "action_contract": {"actions": [], "default_unknown_action": "BLOCK"},
        "risk_class": "low",
        "owner_gate": "فعال‌سازی فقط با رأیِ صریحِ مالک — ثبتِ این فایل مجوزِ هیچ اجرایی نیست",
        "surface": "legs_forum_group",
        "leg_key": key,
        "runtime_status_probe": "telegram_center/leg_activation.py:activation_status",
        "tests": ["_ops/tests/test_tg_leg_activation.py"],
        "registration_is_authorization": False,
        "status": "DORMANT_BY_DESIGN",
    }


def manifest_errors(d: dict) -> list:
    """همان چک‌های validate_contract.validate_manifest، روی dict به‌جای مسیر.
    خروجیِ خالی = معتبر. (آینه است نه جایگزین — تستِ drift هر دو را می‌سنجد.)"""
    errors: list = []
    if not isinstance(d, dict):
        return ["manifest is not a dict"]
    missing = sorted(set(MANIFEST_REQUIRED) - set(d))
    if missing:
        errors.append("missing: " + ",".join(missing))
    if d.get("schema") != MANIFEST_SCHEMA:
        errors.append("bad schema")
    if d.get("registration_is_authorization") is not False:
        errors.append("manifest may grant authorization")
    surface = d.get("surface")
    if surface not in _SURFACES:
        errors.append(f"bad surface: {surface}")
    if surface == "legs_forum_group" and not d.get("leg_key"):
        errors.append("group capability lacks leg_key")
    if d.get("risk_class") in _RISKY and not d.get("owner_gate"):
        errors.append("risky capability lacks owner gate")
    return errors


# ── شاهدهای روی دیسک ───────────────────────────────────────────────────────
def manifest_path(leg_key: str, *, base: "Path | None" = None) -> Path:
    """جای قراردادیِ manifest ِ هر پا. تزریق: `OCTOPUS_LEG_MANIFEST_DIR`."""
    if base is None:
        override = os.environ.get("OCTOPUS_LEG_MANIFEST_DIR", "").strip()
        base = Path(override) if override else (_HERE / "manifests")
    return Path(base) / _safe_key(leg_key) / "capability-manifest.json"


def _has_valid_manifest(leg_key: str) -> bool:
    p = manifest_path(leg_key)
    try:
        d = json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        return False
    return not manifest_errors(d)


def _last_leg_activity(leg_key: str) -> float:
    """آخرین لمسِ Task ِ این پا (فقط از API عمومیِ leg_tasks — بدونِ ارسال)."""
    try:
        import sys as _s
        if str(_HERE) not in _s.path:
            _s.path.insert(0, str(_HERE))
        import leg_tasks as _lt
        rows = _lt.queue(leg_key) + _lt.recent_done(leg_key, 50)
        return max((float(t.get("updated") or 0) for t in rows), default=0.0)
    except Exception:  # noqa: BLE001 — نبودِ state = صفر فعالیت، نه crash
        return 0.0


def activation_status(leg_key: str, cfg: dict, *,
                      now: "float | None" = None) -> str:
    """DORMANT | READY | ACTIVE — از سه شاهد، بدونِ حدس:
      · manifest ِ معتبر روی دیسک؟
      · تاپیکِ پا در config ِ مرکز هست؟
      · فعالیتِ leg_tasks در ۱۴ روزِ اخیر؟
    manifest یا تاپیک نبود ⇒ DORMANT. هر دو بود ولی فعالیت نه ⇒ READY.
    هر سه ⇒ ACTIVE."""
    import time as _t
    now = float(now if now is not None else _t.time())
    topics = (cfg or {}).get("topics") or {}
    has_topic = bool(topics.get(str(leg_key)))
    if not (_has_valid_manifest(leg_key) and has_topic):
        return DORMANT
    if now - _last_leg_activity(leg_key) <= ACTIVE_WINDOW_S:
        return ACTIVE
    return READY


# ── نگهبانِ صفر-template ───────────────────────────────────────────────────
# امضاهای boilerplate ِ شناخته (اسکنِ ۰۷-۲۹) + مارکرهای قالبِ پرنشده.
DEFAULT_TEMPLATE_SIGNATURES = (
    "هیچ فعالیتی ثبت نشده",
    "گزارش خودکار",
    "پیام آزمایشی",
    "این یک پیام تستی",
    "placeholder", "lorem ipsum", "sample text", "test message",
    "todo:", "tbd",
)
_UNFILLED = ("{{", "}}", "%s", "{0}", "<placeholder", "<لطفا", "<اینجا")


def zero_template_guard(text: str, *, blocklist=None) -> bool:
    """True یعنی «این متن template/filler است — نفرست».

    قاعدهٔ منشور: از پای خلوت «پیام فقط رخدادِ واقعی، صفر template». متنِ
    خالی، متنِ حاویِ امضایِ boilerplate، و قالبِ پرنشده همه رد می‌شوند.
    False یعنی متن از این نگهبان گذشت (رخدادِ واقعی به نظر می‌رسد)."""
    t = str(text or "").strip()
    if not t:
        return True
    low = t.casefold()
    for sig in tuple(blocklist) if blocklist is not None else DEFAULT_TEMPLATE_SIGNATURES:
        if str(sig).casefold() in low:
            return True
    for marker in _UNFILLED:
        if marker in t:
            return True
    return False


# ── نقشهٔ فعال‌سازی (propose-only) ─────────────────────────────────────────
def activate(leg_key: str, *, cfg: dict, create_topic_fn=None,
             title: "str | None" = None,
             now: "float | None" = None) -> dict:
    """نقشهٔ آنچه ایجنتِ موازی باید بسازد تا این پا فعال شود.

    ⚠️ propose-only در این موج: `create_topic_fn` فقط برای قراردادِ آیندهٔ
    wiring در امضاست و **هرگز این‌جا صدا زده نمی‌شود** — نه تاپیک ساخته
    می‌شود، نه manifest نوشته می‌شود، نه پیامی می‌رود."""
    key = _safe_key(leg_key)
    topics = (cfg or {}).get("topics") or {}
    has_manifest = _has_valid_manifest(key)
    has_topic = bool(topics.get(key))
    return {
        "leg_key": key,
        "current_status": activation_status(key, cfg or {}, now=now),
        "propose_only": True,
        "steps": [
            {"step": "manifest", "needed": not has_manifest,
             "path": str(manifest_path(key)),
             "note": "اسکلت در همین plan است؛ ثبت = مجوز نیست"},
            {"step": "topic", "needed": not has_topic,
             "note": "ساختِ تاپیک کارِ لِینِ wiring با رأیِ مالک — این موج نمی‌سازد"},
            {"step": "first_real_event", "needed": True,
             "note": "اولین پیام باید رخدادِ واقعی باشد و از zero_template_guard بگذرد"},
        ],
        "manifest_skeleton": manifest_skeleton(key, title or key),
    }
