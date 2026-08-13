#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""miniapp_state.py — read-only state helpers for the MiniApp cockpit.

قرارداد (PHASE 4 megaprompt):
  · read-only — هیچ mutate، هیچ side-effect.
  · secret-scrubbed — هرگز token/chat_id/PII در خروجی.
  · fail-closed — اگه فایل غایب/خراب است، status=unknown نه صفرِ جعلی.
  · JSON-safe — خروجی همیشه JSON-serializable.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import threading
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import opslib  # noqa: E402
    STATE_DIR = opslib.STATE_DIR
    ORGAN_STATE = opslib.ORGAN_STATE
    BUDGET_STATE = opslib.BUDGET_STATE
    ORGAN_LOG = opslib.ORGAN_LOG
except Exception:  # noqa: BLE001
    opslib = None  # type: ignore
    STATE_DIR = _OPS / "state"
    ORGAN_STATE = _OPS / "budget" / "organ-state.json"
    BUDGET_STATE = _OPS / "budget" / "budget-state.json"
    ORGAN_LOG = _OPS / "budget" / "organ-gate-log.jsonl"

_ROOT = _OPS.parent
_RUNTIME = _OPS / "agi2027_runtime"
# ⚠️ ثابتِ تاریخ‌دار حذف شد (۲۰۲۶-۰۸-۰۵). قبلاً این‌جا نامِ کوبیدهٔ یک
# پروندهٔ تاریخ‌دار بود که مدت‌ها پیش جابه‌جا شده. مسیر را `_find_truth()`
# پیدا می‌کند، نه حدس. نامِ تاریخ‌دار در کد بمبِ ساعتی است: روزِ نوشتن
# درست است و بعد بی‌صدا می‌پوسد — و «missing» شبیهِ حالتِ عادی دیده
# می‌شود نه شبیهِ خرابی، پس کسی دنبالش نمی‌گردد.

# الگوی scrub — عبارت‌های حساس را پاک می‌کند
_SECRET_RE = re.compile(
    r"(?i)(bot_token|api[_-]?key|secret|password|passwd|chat_id|bearer|sk-|fish_|xoxb-)"
    r"\s*[:=]\s*[^\s,;\"']+")
_TOKEN_RE = re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{20,}\b")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


def _scrub(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    text = _TOKEN_RE.sub("<TOKEN_REDACTED>", text)
    text = _SECRET_RE.sub(r"\1=<REDACTED>", text)
    text = _EMAIL_RE.sub("<EMAIL_REDACTED>", text)
    return text


def _scrub_dict(d: Any) -> Any:
    """بازگشتی secretها را از dict/list/str پاک می‌کند."""
    if isinstance(d, dict):
        out = {}
        for k, v in d.items():
            if isinstance(k, str) and re.search(
                    r"(?i)token|secret|password|passwd|api[_-]?key|chat_id|cookie|session",
                    k):
                out[k] = "<REDACTED>"
            else:
                out[k] = _scrub_dict(v)
        return out
    if isinstance(d, list):
        return [_scrub_dict(x) for x in d]
    if isinstance(d, str):
        return _scrub(_scrub(d))
    return d


def _read_json_safe(path: Path) -> "dict | None":
    try:
        if not path.exists():
            return None
        d = json.loads(path.read_text("utf-8"))
        return d if isinstance(d, dict) else None
    except (OSError, ValueError, TypeError):
        return None
def _miniapp_url_configured() -> bool:
    """Best-effort config check without exposing the URL.
    The gateway may be started before the User env is inherited by the process,
    while run-miniapp-tunnel.ps1 always writes state/telegram/miniapp-url.json.
    Treat either source as configured so the cockpit does not show a false
    CONFIG_NEEDED warning.
    """
    if str(os.environ.get("OCTOPUS_MINIAPP_URL", "") or "").strip():
        return True
    try:
        import subprocess
        code = "[Environment]::GetEnvironmentVariable('OCTOPUS_MINIAPP_URL','User')"
        r = subprocess.run(["powershell", "-NoProfile", "-Command", code],
                           capture_output=True, text=True, timeout=2)
        if (r.stdout or "").strip():
            return True
    except Exception:
        pass
    try:
        d = _read_json_safe(STATE_DIR / "telegram" / "miniapp-url.json")
        return bool(isinstance(d, dict) and str(d.get("url") or "").strip())
    except Exception:
        return False


def _cardiac_vitals() -> dict:
    """بودجهٔ ضربانِ روزانه: خرج، سقف، درصد.

    سقف را **حساب نمی‌کنم** — از خودِ `cardiac.BeatBudget._cap()` می‌پرسم.
    دلیل: سقفِ مؤثر سه منبع دارد (setpointِ مالک → env → پیش‌فرض) و اگر
    این‌جا کپی‌اش کنم، روزی که مالک `/heart set cap` بزند این عدد بی‌صدا
    از واقعیت جدا می‌شود — همان «قانون از کدش عقب می‌افتد».

    گاردِ کهنگی: پرونده `date` دارد. اگر مالِ امروز نباشد، عدد **دیروز**
    است و حلقه‌ای که ۷۰٪ نشان دهد دروغ می‌گوید. در آن حالت
    `stale=True` و درصد `None` — نبودِ رقم بهتر از رقمِ غلط است.
    """
    p = STATE_DIR / "cardiac-budget.json"
    d = _read_json_safe(p)
    if not isinstance(d, dict):
        return {"status": "unknown", "reason": "cardiac-budget missing/unreadable"}
    cap = None
    try:
        import cardiac  # noqa: WPS433 — تنبل: gateway نباید به بوتِ قلب گره بخورد
        cap = int(cardiac.BeatBudget(path=p)._cap())
    except Exception:  # noqa: BLE001
        cap = None
    today = time.strftime("%Y-%m-%d")
    stale = str(d.get("date") or "") != today
    spent = d.get("spent")
    pct = None
    if not stale and isinstance(spent, int) and isinstance(cap, int) and cap > 0:
        pct = round(min(spent / cap, 1.0) * 100, 1)
    return {
        "status": "ok",
        "spent": spent,
        "resting": d.get("resting"),
        "cap": cap,
        "pct": pct,
        "date": d.get("date"),
        "stale": stale,
        "depleted": bool(isinstance(spent, int) and isinstance(cap, int) and cap > 0
                         and spent >= cap and not stale),
    }


def _arbiter_vitals() -> dict:
    """رنگِ داورِ نبض — سه قلبِ موازی که به یک period می‌رسند.

    [اصلاح ۲۰۲۶-۰۸-۰۵: از امشب `OCTOPUS_WIRE_PULSE_ARBITER` مسلح است و
    `state/pulse/arbiter-latest.json` واقعاً وجود دارد و هر ~۵۷ثانیه تازه
    می‌شود — کامنتِ پایین برای پیش از آن است، به‌عنوانِ سابقه نگه داشته شد.]

    نکتهٔ باربر (پیش از امشب): آن فایل وجود نداشت چون `pulse_arbiter.persist()`
    پشتِ همان فلگ بود و خاموش بود. `arbiter_snapshot()` قبل از آن گیت اجرا
    می‌شود و **خالص** است — سنجیدمش: هیچ فایلی نمی‌سازد، ۰.۳۶ms. پس این‌جا
    خودِ محاسبه را صدا می‌زنم نه فایل را (این رفتار عمداً همان‌طور مانْد —
    محاسبهٔ زنده از خواندنِ فایلِ چندثانیه‌کهنه دقیق‌تر است). `wire_open`
    را عیناً پاس می‌دهم تا UI بتواند «سایه» را از «زنده» جدا نشان دهد —
    وگرنه رنگ شبیهِ فرمانِ نافذ دیده می‌شود.
    """
    try:
        from heart import pulse_arbiter as _pa  # noqa: WPS433 — تنبل و اختیاری
    except Exception:  # noqa: BLE001
        return {"status": "unknown", "reason": "pulse_arbiter unavailable"}
    try:
        s = _pa.arbiter_snapshot(beat=0)
    except Exception as exc:  # noqa: BLE001
        return {"status": "unknown", "reason": f"{type(exc).__name__}"}
    return {
        "status": "ok",
        "color": s.get("color"),
        "effective_period_s": s.get("effective_period_s"),
        "driver": s.get("driver"),
        "wire_open": bool(s.get("wire_open")),
        "n_present": s.get("n_present"),
        "n_braking": s.get("n_braking"),
    }


def get_miniapp_state(root: "Path | None" = None) -> dict:
    """Home/Cockpit: system status، flags، pending، risk، Project-F، auth."""
    st = _read_json_safe(STATE_DIR / "ORGANISM-STATE.json")
    if st is None:
        return {"status": "unknown", "reason": "ORGANISM-STATE missing/unreadable"}
    flags = {
        "OCTOPUS_WIRE_TG_CONTROL": os.environ.get("OCTOPUS_WIRE_TG_CONTROL", "0") == "1",
        "OCTOPUS_WIRE_LEAD_OUTBOUND_WAL": os.environ.get("OCTOPUS_WIRE_LEAD_OUTBOUND_WAL", "0") == "1",
        "OCTOPUS_WIRE_VALUE_LEDGER": os.environ.get("OCTOPUS_WIRE_VALUE_LEDGER", "0") == "1",
    }
    # managed_flags.json را هم بخوان
    mf = _read_json_safe(_RUNTIME / "managed_flags.json")
    if isinstance(mf, dict):
        for k, v in mf.items():
            flags[k] = (str(v) == "1")
    # auth status: آیا bot_token + owner_id موجود است؟
    auth_configured = bool(os.environ.get("TG_CENTER_BOT_TOKEN")) and bool(os.environ.get("TELEGRAM_OWNER_CHAT_ID"))
    out = {
        "status": "ok",
        "halted": bool(st.get("halted") or st.get("stop_organism")),
        "frozen": bool(st.get("frozen")),
        "beat": st.get("beat"),
        "epoch_mode": st.get("epoch_mode"),
        "ts": st.get("ts"),
        "month": st.get("month"),
        "today": st.get("today"),
        "conflicts": st.get("conflicts"),
        "suspect_zero_total": st.get("suspect_zero_total"),
        # این سه، از قبل در ORGANISM-STATE بودند و همین allowlist دورشان
        # می‌ریخت — پس مینی‌اپ کورشان بود. حالا عبور می‌کنند.
        "germline_lag_h": st.get("germline_lag_h"),
        "germline_alert": st.get("germline_alert"),
        "recall_reach": st.get("recall_reach"),
        "cardiac": _cardiac_vitals(),
        "arbiter": _arbiter_vitals(),
        "active_flags": flags,
        "auth_status": "configured" if auth_configured else "CONFIG_NEEDED",
        "projectf_status": "BLOCKED_NEEDS_CREDENTIALS",
        "miniapp_url_configured": _miniapp_url_configured(),
        "commit": _git_head_short(root),
    }
    return _scrub_dict(out)


def get_outbound_state(root: "Path | None" = None) -> dict:
    """Outbound/G-03: sent/failed/sending/needs_owner/cancelled counts."""
    db = _RUNTIME / "outbound-effects.sqlite3"
    if not db.exists():
        return {"status": "no_wal_db", "counts": {}, "note": "no outbound effects yet"}
    try:
        conn = sqlite3.connect(str(db))
        rows = conn.execute(
            "SELECT state, COUNT(*) FROM outbound_effects GROUP BY state").fetchall()
        conn.close()
        counts = {r[0]: r[1] for r in rows}
        return {"status": "ok", "counts": counts, "total": sum(counts.values())}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}"}


def get_approvals_state(root: "Path | None" = None) -> dict:
    """Approvals: pending proposal cards از outcomes."""
    db = STATE_DIR / "outcomes" / "outcomes.db"
    if not db.exists():
        return {"status": "no_outcomes_db", "pending": []}
    # ⚠️ ۲۰۲۶-۰۸-۰۵ — این تابع **شش تصمیمِ واقعی را نامرئی کرده بود**.
    #
    # نسخهٔ قبلی از جدولی به نامِ `deliveries` می‌خواند که در این پایگاه
    # **اصلاً وجود ندارد**؛ تنها جدول `outcomes` است. کوئری همیشه استثنا
    # می‌داد، `except` آن را می‌بلعید، و `{"status":"unknown_schema",
    # "pending":[]}` برمی‌گشت. کاکپیت هم فقط طولِ `pending` را می‌دید، پس
    # می‌نوشت «صف خالی است» و خانه تیک می‌زد «✓ صفِ تأیید خالی است».
    #
    # یعنی یک `except` ِ بلعنده به مالک **اطمینانِ فعال** می‌داد. این از
    # خطا بدتر است: خطا را می‌بینی، ولی این را نه.
    #
    # تعریفِ «منتظر» از خودِ داده می‌آید: پیشنهادی که آخرین رویدادش
    # `delivered` است و هیچ `verdict` ی ندارد — تحویل داده شده، کسی تصمیم
    # نگرفته. سنجیده روی داده‌ی زنده: ۶ مورد، قدیمی‌ترین ۲۰۲۶-۰۷-۲۳.
    # ⚠️ کارت‌های sandbox از صف بیرون می‌مانند — رأیِ مالک ۲۰۲۶-۰۸-۰۵.
    #
    # سنجش نشان داد **چهار از شش** پیشنهادِ «منتظر» در واقع canary/آزمایشی
    # بودند (`payload_json.channel == "sandbox"`)، پس عددِ صف هر روز چهار
    # واحد تورم داشت و توجهِ مالک را می‌خورد.
    #
    # ⚠️ «حذف از صف» یعنی **فیلترِ نما**، نه حذفِ ردیف: منشور §۰.۱ می‌گوید
    # هرگز حذف نکن. ردیف‌ها سرِ جایشان‌اند و `sandbox_hidden` می‌گوید چندتا
    # پنهان شد — وگرنه اگر روزی کارِ واقعی اشتباهاً برچسبِ sandbox بخورد،
    # بی‌صدا نامرئی می‌شود و کسی نمی‌فهمد.
    sql = """
    WITH latest AS (
      SELECT proposal_id, event_type, verdict, leg_id, value_aud_claimed,
             occurred_at, payload_json,
             ROW_NUMBER() OVER (PARTITION BY proposal_id ORDER BY occurred_at DESC) rn
        FROM outcomes WHERE proposal_id IS NOT NULL)
    SELECT proposal_id, leg_id, value_aud_claimed, occurred_at, payload_json
      FROM latest
     WHERE rn = 1 AND event_type = 'delivered' AND verdict IS NULL
     ORDER BY occurred_at ASC LIMIT 50"""
    conn = None
    try:
        conn = sqlite3.connect(str(db))
        rows = conn.execute(sql).fetchall()
    except Exception as exc:  # noqa: BLE001
        # اسکیما عوض شده یا پایگاه قفل است. **هرگز** صفِ خالی برنگردان —
        # «نمی‌دانم» و «هیچ نیست» دو چیزِ کاملاً متفاوت‌اند و UI باید
        # بتواند فرقشان را بگذارد.
        return {"status": "unknown_schema", "pending": None,
                "reason": f"{type(exc).__name__}"}
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass
    pending, hidden = [], 0
    for r in rows:
        chan = ""
        try:
            chan = str((json.loads(r[4] or "{}") or {}).get("channel") or "")
        except (TypeError, ValueError):
            chan = ""
        if chan.lower() == "sandbox":
            hidden += 1
            continue
        pending.append({"proposal_id": r[0], "kind": r[1],
                        "amount_aud": r[2], "since": r[3]})
    return {"status": "ok", "pending": _scrub_dict(pending), "count": len(pending),
            "sandbox_hidden": hidden,
            # ۲۰۲۶-۰۸-۰۵ — سؤالِ مالک: «دوتا را تأیید کردم؛ عملی از سمتِ تو
            # کار کرد و تأثیر داشت؟» تا امروز پاسخ فقط در چتِ من بود، یعنی
            # فردا دوباره همان سؤال. حالا خودِ صفحه جواب می‌دهد.
            "decisions": _recent_decisions(db)}


def _recent_decisions(db: "Path", limit: int = 8) -> list:
    """تصمیم‌های اخیرِ مالک و اینکه بعدش **واقعاً** چه شد.

    ⚠️ این‌جا هیچ چیزی حدس زده نمی‌شود. تنها چیزی که گزارش می‌شود یک واقعیتِ
    قابلِ مشاهده است: بعد از ثبتِ حکم، رویدادِ دیگری برای همان پیشنهاد آمد
    یا نه. «اثری ثبت نشده» با «اثر ندارد» یکی نیست و UI هم همین را می‌گوید.

    چرا اصلاً لازم است: `owner-decision` **یک نویسنده دارد و صفر خواننده**
    (گرپ روی کلِ `_ops` تأیید کرد). پس تأییدِ مالک ردیف می‌سازد و پیشنهاد را
    از صف بیرون می‌برد، ولی هیچ اثرگری آن را برنمی‌دارد. این نما همان شکاف
    را **مرئی** می‌کند به‌جای اینکه بپوشاندش.
    """
    sql = """
    SELECT d.proposal_id, d.verdict, d.occurred_at, d.leg_id,
           (SELECT COUNT(*) FROM outcomes n
             WHERE n.proposal_id = d.proposal_id
               AND n.occurred_at > d.occurred_at) AS after_n,
           (SELECT n2.event_type FROM outcomes n2
             WHERE n2.proposal_id = d.proposal_id
               AND n2.occurred_at > d.occurred_at
             ORDER BY n2.occurred_at ASC LIMIT 1) AS after_type
      FROM outcomes d
     WHERE d.event_type = 'owner-decision'
     ORDER BY d.occurred_at DESC LIMIT ?"""
    conn = None
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        rows = conn.execute(sql, (int(limit),)).fetchall()
    except Exception:  # noqa: BLE001
        return []      # نبودِ نما نباید کلِ صف را بکشد
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass
    out = []
    for pid, verdict, ts, leg, after_n, after_type in rows:
        out.append({
            "proposal_id": str(pid or "")[:64],
            "verdict": str(verdict or "")[:32],
            "decided_at": str(ts or "")[:32],
            "leg": str(leg or "")[:48],
            "effects_after": int(after_n or 0),
            # نامِ رویدادِ بعدی — اگر بود. `None` یعنی «هنوز هیچ»، نه «هرگز».
            "next_event": (str(after_type)[:32] if after_type else None),
        })
    return _scrub_dict(out)


def get_legs_state(root: "Path | None" = None) -> dict:
    """Legs/Agents: از business_legs در ORGANISM-STATE."""
    st = _read_json_safe(STATE_DIR / "ORGANISM-STATE.json")
    biz = st.get("business_legs") if isinstance(st, dict) else None
    # unwrap double-layer
    if isinstance(biz, dict) and "business_legs" in biz:
        biz = biz.get("business_legs")
    if not isinstance(biz, dict):
        return {"status": "unknown", "reason": "business_legs missing", "legs": {}}
    return {"status": "ok", "legs": _scrub_dict(biz)}


def get_notifications_state(root: "Path | None" = None) -> dict:
    """`/api/notifications` — صندوقِ اعلانِ notif_inbox (۲۰۲۶-۰۸-۰۷، کاهشِ
    فشارِ تلگرام). fail-soft: نبود/خطا در importِ notif_inbox → status=unknown،
    نه استثنا — تبِ هفتم نباید کلِ داشبورد را بترکاند."""
    try:
        import notif_inbox as _ni
    except Exception as exc:  # noqa: BLE001
        return {"status": "unknown", "reason": f"{type(exc).__name__}", "items": [],
                "unread_count": 0}
    try:
        items = _ni.list_items(limit=50)
        return _scrub_dict({"status": "ok", "items": items,
                            "unread_count": _ni.unread_count(),
                            "cap_hit": len(items) >= 50})
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}", "items": [],
                "unread_count": 0}


def get_value_state(root: "Path | None" = None) -> dict:
    """Value Ledger: خلاصه از value-ledger.jsonl (اگر هست)."""
    ledger = _RUNTIME / "value-ledger.jsonl"
    if not ledger.exists():
        return {"status": "no_value_ledger", "note": "value ledger not yet populated"}
    # FIX (deep-scan 2026-08-07): محدودیتِ اندازه — اگر فایل >۵MB شد (رشدِ زنده
    # یا خرابی)، فقط آخرین ۵۰۰۰ خط را بخوان، نه کلِ فایل (جلوگیری از OOM).
    try:
        _fsize = ledger.stat().st_size
        if _fsize > 5_000_000:
            # فقط دمِ فایل را بخوان — فایلِ بزرگ را رویِ مموری لود نکن
            lines = []
            with ledger.open("r", encoding="utf-8", errors="replace") as _fh:
                from collections import deque
                lines = list(deque(_fh, maxlen=5000))
        else:
            lines = ledger.read_text("utf-8", errors="replace").splitlines()
        counts = {}
        for raw in lines:
            raw = raw.strip()
            if not raw:
                continue
            try:
                r = json.loads(raw)
            except ValueError:
                continue
            leg = r.get("leg", "?")
            counts[leg] = counts.get(leg, 0) + 1
        return {"status": "ok", "events_per_leg": counts, "total": sum(counts.values()),
                "auto_delete": False}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}"}


def get_ui_registry(root: "Path | None" = None) -> dict:
    """UI Registry: از ui-registry.json."""
    reg = _read_json_safe(_RUNTIME / "ui-registry.json")
    if reg is None:
        return {"status": "missing", "reason": "ui-registry.json not found"}
    return reg



# ⚠️ بدنهٔ این تابع هم در  بازنویسی شد و چهار بخشِ
# brain/governor/obsidian/next_steps و کلیدِ actions.safe_local_actions را
# از دست داد. graft ِ نامی نمی‌گرفتش چون **نام** در هر دو نسخه بود، فقط
# بدنه فرق داشت — همان کلاسِ گم‌شدنی که دیفِ سطحِ نماد نشان نمی‌دهد.
def get_ops_state(root: "Path | None" = None) -> dict:
    """Ops Studio local summary: leads/tasks/value + owner-auth + action registry
    + چهار بخشِ سطحِ حقیقت (brain / governor / obsidian / next_steps).

    قرارداد: **هیچ کلیدِ موجودی نه نام عوض می‌کند نه معنا.** `owner_auth` و
    `actions.registry`/`actions.blocked_prefixes` مستقیم از خودِ موتور خوانده
    می‌شوند (نه کپیِ دستی) و نام‌های قدیمی‌ترِ همان‌ها (`safe_local_actions`،
    `blocked_external_automation`) هم عمداً می‌مانند — چون دو لِینِ موازی هرکدام
    یکی را نوشته‌اند و حذفِ هرکدام یک breaking change با لباسِ «تمیزکاری» است."""
    out = _engine_summary(root)
    if out.get("status") == "ok":
        try:
            from agi2027_control.ops_actions import (  # noqa: WPS433
                ALLOWED_ACTIONS,
                BLOCKED_PREFIXES,
            )
            has_bot = bool(os.environ.get("TG_CENTER_BOT_TOKEN"))
            has_owner = bool(os.environ.get("TELEGRAM_OWNER_CHAT_ID"))
            out["owner_auth"] = {
                "configured": has_bot and has_owner,
                "bot_token": "set" if has_bot else "missing",
                "owner_id": "set" if has_owner else "missing",
            }
            out["actions"] = {
                "enabled_when": "owner-auth configured + Telegram initData valid",
                "registry": sorted(ALLOWED_ACTIONS),
                "blocked_prefixes": list(BLOCKED_PREFIXES),
                "safe_local_actions": sorted(ALLOWED_ACTIONS),
                "blocked_external_automation": list(BLOCKED_PREFIXES),
            }
        except Exception as exc:  # noqa: BLE001
            out["actions"] = {"status": "error", "reason": f"{type(exc).__name__}"}
    out["brain"] = _section(get_brain_state, root, "brain",
                            {"available": False, "daemon": {}, "consolidation": {}})
    out["governor"] = _section(get_governor_state, root, "governor",
                               {"policy_doc": None, "canonical_provider": None,
                                "drift_status": {"status": "unknown"}, "routes": {}})
    out["obsidian"] = _section(get_obsidian_state, root, "obsidian",
                               {"reference_dir_configured": False, "docs": {}})
    out["next_steps"] = _section(get_next_steps, root, "next_steps", [])
    return _scrub_dict(out)

def _find_truth() -> "Path | None":
    """پروندهٔ «حقیقتِ جاری» را **پیدا** کن، نه اینکه نامش را حدس بزن.

    ⚠️ باگی که دیباگِ ۰۸-۰۵ گرفت: `_TRUTH` روی نامِ **تاریخ‌دارِ** ثابتِ
    `OCTOPUS-CURRENT-TRUTH-2026-08-02.md` کوبیده بود. آن فایل دیگر آن‌جا
    نیست (حالا `OCTOPUS/CURRENT-TRUTH.md`)، پس تبِ حقیقت از روزی که فایل
    جابه‌جا شد **مرده** بود و هیچ‌کس نفهمید — چون «missing» شبیهِ یک حالتِ
    عادی دیده می‌شد نه شبیهِ خرابی.

    نامِ تاریخ‌دار در کد یعنی بمبِ ساعتی: روزِ نوشته‌شدن درست است و بعد
    بی‌صدا می‌پوسد. ترتیب: مسیرِ صریحِ env → نامِ بی‌تاریخ → تازه‌ترین
    نسخهٔ تاریخ‌دار.
    """
    cands = []
    envp = os.environ.get("OCTOPUS_CURRENT_TRUTH", "").strip()
    if envp:
        cands.append(Path(envp))
    cands.append(_ROOT / "OCTOPUS" / "CURRENT-TRUTH.md")
    cands.append(_ROOT / "OCTOPUS-CURRENT-TRUTH.md")
    for p in cands:
        try:
            if p.is_file():
                return p
        except OSError:
            continue
    # تازه‌ترین نسخهٔ تاریخ‌دار، اگر هنوز از آن الگو استفاده می‌شود
    try:
        dated = sorted(_ROOT.glob("OCTOPUS-CURRENT-TRUTH-*.md"))
        if dated:
            return dated[-1]
    except OSError:
        pass
    return None


def get_current_truth(root: "Path | None" = None) -> dict:
    """Current Truth: خلاصهٔ پروندهٔ «حقیقتِ جاری»."""
    truth = _find_truth()
    if truth is None:
        return {"status": "missing",
                "reason": "OCTOPUS-CURRENT-TRUTH file not found",
                "looked_in": ["OCTOPUS/CURRENT-TRUTH.md",
                              "OCTOPUS-CURRENT-TRUTH.md",
                              "OCTOPUS-CURRENT-TRUTH-*.md"]}
    _TRUTH = truth
    try:
        text = _TRUTH.read_text("utf-8", errors="replace")
        # اولین ~۲۰ خطِ غیر-frontmatter را بگیر
        lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("---")][:25]
        # 2026-08-12 fix: این تنها handlerِ این فایل بود که سنِ فایل را
        # برنمی‌گرداند — _cardiac_vitals و get_selfmap_state همین‌جا هر دو
        # عمداً age_s/stale می‌دهند («نبودِ رقمِ بهتر از رقمِ غلط است») ولی
        # CURRENT-TRUTH، دقیقاً فایلی که قرار است «جاری» باشد، همیشه
        # status:"ok" بدونِ هیچ نشانهٔ کهنگی برمی‌گرداند.
        age_s = time.time() - _TRUTH.stat().st_mtime
        return {"status": "ok", "preview": _scrub("\n".join(lines)),
                "path": str(_TRUTH.name), "age_s": round(age_s, 1),
                "stale": age_s > 86400}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}"}


def get_money_caps_state(root: "Path | None" = None) -> dict:
    """قدم ۵/۷ — ماتریس سقف + armed≠productive. fail-soft."""
    try:
        import sys
        ops = Path(__file__).resolve().parent.parent
        if str(ops) not in sys.path:
            sys.path.insert(0, str(ops))
        import money_caps_snapshot as _mcs  # noqa: WPS433
        snap = _mcs.snapshot()
        snap["status"] = "ok"
        return snap
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}: {exc}",
                "may_authorize": False, "claimed_is_income": False}


def get_epistemic_state(root: "Path | None" = None) -> dict:
    """ADR-039 (C6) — پنلِ فقط‌خواندنیِ کابینِ epistemic. fail-soft، $0، هیچ اجرا.

    owner override 2026-08-13: دروازهٔ Go روی دادهٔ synthetic NO-GO بود (نیمهٔ
    کارایی) ولی نیمهٔ ایمنی (leakage/external-effect/budget) pass شده بود. مالک
    با آگاهی از این override کرد. این پنل صرفاً وضعیت را **نشان** می‌دهد —
    `may_execute` همیشه False؛ هیچ claim/آزمونی از این مسیر اجرا نمی‌شود."""
    try:
        import sys
        ops = Path(__file__).resolve().parent.parent
        if str(ops) not in sys.path:
            sys.path.insert(0, str(ops))
        import epistemics.invariants as _inv  # noqa: WPS433
        import epistemics.policy as _pol  # noqa: WPS433
        from epistemics.receipt_store import ReceiptStore  # noqa: WPS433
        cfg = _pol.load_policy()
        chain = ReceiptStore().verify()
        structural = _inv.structural_invariants()
        return {
            "status": "ok",
            "schema_version": "epistemic.panel.v1",
            "adr": "ADR-039",
            "accepted": True,
            "owner_override": "2026-08-13 (efficacy NO-GO on synthetic; safety passed)",
            "wired_to_cortex": "EPISTEMIC_TESTS=" + os.environ.get("EPISTEMIC_TESTS", "0"),
            "policy": {
                "default_off": cfg.default_off,
                "max_authority": cfg.max_authority,
                "sandbox_profile": cfg.sandbox_profile,
                "caps": {"max_runs": cfg.caps.max_runs,
                         "max_wall_seconds": cfg.caps.max_wall_seconds,
                         "max_cost_aud": cfg.caps.max_cost_aud},
            },
            "invariants": {
                "count": _inv.count(),
                "names": list(_inv.names()),
                "structural_enforced": [i.name for i in structural],
            },
            "receipt_chain": {
                "ok": chain.ok,
                "n_records": chain.n_records,
                "broken_at": chain.broken_at,
            },
            "world_mode_labels": ["reality", "hypothesis", "simulation",
                                  "counterfactual", "fictional"],
            "may_execute": False,   # hard invariant — هرگز True از این مسیر
            "gate": {
                "benchmark_verdict": "NO-GO (synthetic, 8 cases)",
                "safety_criteria_passed": True,
                "efficacy_threshold_met": False,
                "c6_panel": "read-only (this endpoint)",
                "c7_shadow_run": "harness ready; 10h run owner-timed",
            },
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}: {exc}",
                "may_execute": False}


def _git_head_short(root: "Path | None" = None) -> str:
    """short commit hash، fail-soft."""
    import subprocess
    r = root if root is not None else _ROOT
    try:
        out = subprocess.run(["git", "-C", str(r), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# C6 — نمای **خواندنیِ** چرخهٔ عمرِ تصمیم (UNIFICATION-DESIGN-2026-08-03، گامِ ۱۹)
#
# مینی‌اپ یک سطحِ **خواندنیِ اضافی** است و حق ندارد به صفحهٔ فرمانِ دوم تبدیل
# شود. پس این بخش عمداً سه قید دارد:
#
#   ۱. هیچ verb ِ نوشتنی. نه POST، نه PUT، نه DELETE، نه هیچ effector. دیوارِ
#      405 ِ `miniapp_gateway._handle_core` دست‌نخورده می‌ماند و تستِ خواهرِ
#      این ماژول متنِ آن دیوار را بایت‌به‌بایت pin می‌کند.
#   ۲. whitelist ِ سختِ بدنه: فقط **شمارش و timestamp**. صفر متنِ کارت، صفر
#      هویتِ مالک، صفر مادهٔ توکن. `pending-cards.json` روی درختِ زنده این
#      فیلدها را دارد: token_sha256 / nonce / owner / summary / expires_at —
#      و تنها مقصدِ تونلِ cloudflared همین gateway است، پس یک باگِ projection
#      این تونل را به سطحِ اعتبارنامه تبدیل می‌کند. دو دیوارِ مستقل: ساختِ
#      گزینشی، به‌علاوهٔ `_lifecycle_enforce` که هر کلید/رشتهٔ ممنوع را
#      **استثنا** می‌کند (نه sanitize ِ بی‌صدا).
#   ۳. غیاب ⇒ UNKNOWN، هرگز صفر. یک ذخیرهٔ غایب و «صفر کارتِ راکد» دو چیزِ
#      متفاوت‌اند؛ stampِ UNKNOWN عمداً کلیدِ `value` ندارد.
#
# فلگ: `OCTOPUS_PF_MINIAPP` (پیش‌فرض خاموش — رأیِ مالک، گامِ ۲۴). خاموش یعنی
# مسیر اصلاً وجود ندارد (۴۰۴) و این ماژول حتی یک فایل هم باز نمی‌کند.
LIFECYCLE_FLAG = "OCTOPUS_PF_MINIAPP"
LIFECYCLE_PATH = "/api/lifecycle"
#: ریتمِ اعلام‌شدهٔ همان تاشدگی (lifecycle_fold.CADENCE_S) — کارت‌ها رویدادمحورند.
LIFECYCLE_CADENCE_S = 6 * 3600.0

#: تنها شمارش‌هایی که project می‌شوند.
LIFECYCLE_COUNTS = ("proposed", "delivered", "decided", "effected",
                    "stalled", "unknown", "reconcile_required")
#: تنها زیرکلیدهایی که از یک stampِ provenance عبور می‌کنند.
LIFECYCLE_STAMP_KEYS = ("value", "mode", "reason", "source",
                        "observed_ts", "age_s", "cadence_s", "dof")
#: زیررشته‌های ممنوع (case-insensitive) در **هر** کلید یا رشتهٔ خروجی.
#: قاعدهٔ #۷ منشور: بیرون از مرزِ پروژه فقط aggregate ِ بی‌محتوا.
LIFECYCLE_FORBIDDEN = ("token", "nonce", "summary", "owner", "chat",
                       "user", "secret", "rfc_id", "expires", "verdict")
#: استثنای **دقیق** (نه زیررشته‌ای) روی نامِ کلید — ۲۰۲۶-۰۸-۰۵.
#:
#: چرا اصلاً استثنا: طرحِ اولیه «فقط شمارش، صفر هویت» بود و آن روز درست بود.
#: ولی نتیجه‌اش این شد که مالک عددِ «۲۹ کارتِ راکد» را می‌دید و **هیچ‌جا**
#: نمی‌توانست تصمیم بگیرد — یک دکمه به چیزی باید بچسبد. رأیِ صریحِ مالک
#: (۲۰۲۶-۰۸-۰۵): «کارت‌های راکد … آدم ببیند از راکدی درش بیاورد.»
#:
#: چرا این استثنا امن است: `rfc_id` یک شناسهٔ مبهمِ hash-مانند است
#: (`RFC-aa01e8ff`) — نه محتوای کارت، نه اعتبارنامه، نه دادهٔ مشتری. مقصدِ
#: این تونل فقط دستگاهِ خودِ مالک پشتِ HMAC ِ init-data است.
#:
#: چرا **دقیق** و نه زیررشته‌ای: با تطابقِ دقیق، کلیدی مثلِ `rfc_id_summary`
#: یا `owner_rfc_id` همچنان می‌افتد. قاعده باریک شد، نه سست. و مقادیر اصلاً
#: از این در رد نمی‌شوند — اسکنِ زیررشته‌ای روی رشته‌ها دست‌نخورده ماند.
LIFECYCLE_KEY_EXCEPTIONS = frozenset({"rfc_id"})
#: مسیرهای اعلام‌شدهٔ منبع. عمداً یک allowlist ِ **دقیق** است نه یک اسکنِ
#: زیررشته‌ای: نامِ فایلِ دفترِ حکم‌ها خودش شاملِ «verdict» است، ولی یک مسیرِ
#: ثابتِ کدنویسی‌شده هرگز محتوای کارت نیست. هر رشتهٔ دیگری که ادعای منبع کند
#: به `unlisted-source` تقلیل می‌یابد — پس یک مسیرِ مشتق‌شده از داده نمی‌تواند
#: از این در بیرون برود.
LIFECYCLE_DECLARED_SOURCES = (
    "_ops/state/pulse/pending-cards.json",
    "_ops/state/doctor/rfc-verdicts.db::rfc_decision",
)
_LIFECYCLE_FALLBACK_SOURCE = LIFECYCLE_DECLARED_SOURCES[0]


def lifecycle_enabled() -> bool:
    """فلگِ پیش‌فرض‌خاموش. خاموش = no-op مطلق (هیچ فایلی باز نمی‌شود)."""
    return os.environ.get(LIFECYCLE_FLAG, "0") == "1"


def _lifecycle_state_dir(root: "Path | None" = None,
                         state_dir: "Path | None" = None) -> Path:
    """`state_dir` صریح برنده است. پیش‌فرضِ ضمنی به ذخیرهٔ **زنده** می‌خورد."""
    if state_dir is not None:
        return Path(state_dir)
    if root is not None:
        return Path(root) / "_ops" / "state"
    return Path(STATE_DIR)


def _lifecycle_forbidden_hit(text: Any) -> str:
    low = str(text).lower()
    for bad in LIFECYCLE_FORBIDDEN:
        if bad in low:
            return bad
    return ""


def _lifecycle_enforce(node: Any, where: str = "$") -> Any:
    """دیوارِ دومِ whitelist: هر کلید/رشتهٔ ممنوع **استثنا** می‌دهد.

    عمداً raise و نه sanitize: یک نشتِ خاموشِ پاک‌شده همان باگ را فردا
    برمی‌گرداند، ولی یک ۵۰۰ ِ بلند صداکننده را می‌شکند. صداقتِ fail-closed.
    """
    if isinstance(node, dict):
        for k, v in node.items():
            # استثنا فقط روی **نامِ کلید** و فقط با تطابقِ دقیق. مقادیر هرگز
            # از این‌جا معاف نمی‌شوند — یک کلیدِ مجاز با مقدارِ آلوده باز هم
            # پایین‌تر توسطِ اسکنِ رشته گرفته می‌شود.
            if str(k) not in LIFECYCLE_KEY_EXCEPTIONS:
                hit = _lifecycle_forbidden_hit(k)
                if hit:
                    raise ValueError(f"lifecycle projection leaked key {where}.{k} (~{hit})")
            _lifecycle_enforce(v, f"{where}.{k}")
        return node
    if isinstance(node, (list, tuple)):
        for i, v in enumerate(node):
            _lifecycle_enforce(v, f"{where}[{i}]")
        return node
    if isinstance(node, str):
        hit = _lifecycle_forbidden_hit(node)
        if hit:
            raise ValueError(f"lifecycle projection leaked text at {where} (~{hit})")
        return node
    if node is None or isinstance(node, (int, float, bool)):
        return node
    raise ValueError(f"lifecycle projection carries {type(node).__name__} at {where}")


def _lifecycle_stalled_rows(folded: Any, ts_now: float) -> list:
    """هویتِ کارت‌های راکد — allowlist ِ صریح، نه پاک‌کردنِ چند فیلدِ بد.

    ⚠️ چرا allowlist: رکوردِ خامِ کارت `nonce` و `token_sha256` دارد. یک
    denylist با افزودنِ فیلدِ تازه به تولیدکننده **بی‌صدا** می‌شکند و آن روز
    اعتبارنامه از این مرز رد می‌شود. این‌جا فقط سه فیلد ساخته می‌شود و هیچ
    چیزی از رکوردِ ورودی کپی نمی‌شود.

    مرتب‌سازی: قدیمی‌ترین اول. کارتی که ۱۰ روز مانده فوری‌تر از دیروزی است و
    ترتیبِ فهرست خودش پیام است.
    """
    rows = folded.get("stalled_list") if isinstance(folded, dict) else None
    if not isinstance(rows, list):
        return []
    out = []
    for rec in rows:
        if not isinstance(rec, dict):
            continue
        rid = rec.get("rfc_id")
        if not rid:
            continue                      # بی‌شناسه = بی‌دکمه؛ ردیفِ بی‌اقدام نساز
        created = rec.get("created_ts")
        try:
            age_d = (float(ts_now) - float(created)) / 86400.0 if created else None
        except (TypeError, ValueError):
            age_d = None
        out.append({
            "rfc_id": str(rid)[:64],
            "created_ts": float(created) if created else None,
            # سن را همین‌جا حساب می‌کنم نه در JS: مرورگرِ تلگرام ساعتِ خودش را
            # دارد و یک انحرافِ ساعتِ دستگاه، «۱۰ روز» را «۹ روز» نشان می‌داد.
            "age_days": None if age_d is None else round(age_d, 1),
        })
    out.sort(key=lambda r: (r["created_ts"] is None, r["created_ts"] or 0.0))
    return out


def _lifecycle_public_stalled_rows(folded: Any, ts_now: float) -> list:
    """نمای **بیرون‌مرزیِ** فهرستِ راکد — بدونِ `rfc_id`.

    ۲۰۲۶-۰۸-۰۶ — رفعِ نشت: `_lifecycle_stalled_rows` عمداً هویتِ کارت را نگه
    می‌دارد چون مصرف‌کنندهٔ داخلیِ تصمیم‌گیر (`decide_rfc`) به همان شناسهٔ خام
    نیاز دارد و `LIFECYCLE_KEY_EXCEPTIONS` دقیقاً برای همان مسیر ساخته شد.
    ولی خودِ `/api/lifecycle` یک تونلِ **خواندنیِ** بیرونی است — قراردادِ
    صریحِ همین ماژول (بندِ ۲ بالای فایل) می‌گوید «فقط شمارش و timestamp،
    صفر هویت». یک شناسهٔ RFC خام (`RFC-aa01e8ff`) دقیقاً همان چیزی است که آن
    قرارداد منع کرده، پس این‌جا — و فقط این‌جا، درست پیش از رفتن به بدنهٔ
    HTTP — فیلدِ هویت‌دار حذف می‌شود؛ تابعِ داخلی و تست‌های تصمیم‌گیرش
    دست‌نخورده می‌مانند.
    """
    return [{"created_ts": r["created_ts"], "age_days": r["age_days"]}
            for r in _lifecycle_stalled_rows(folded, ts_now)]


def _lifecycle_safe_sources(sources: Any) -> list:
    """فقط مسیرهای اعلام‌شده عبور می‌کنند؛ هر رشتهٔ دیگر `unlisted-source`."""
    out = []
    for s in (sources or []):
        out.append(str(s) if str(s) in LIFECYCLE_DECLARED_SOURCES else "unlisted-source")
    return out or [_LIFECYCLE_FALLBACK_SOURCE]


def _lifecycle_prov():
    """`provenance` را تنبل import می‌کند — ماژولِ خالصِ بی‌مسیر و بی‌نوشتن."""
    import provenance as _prov  # noqa: WPS433 — _OPS از قبل روی sys.path است
    return _prov


def _lifecycle_stamp_view(stamped: Any) -> dict:
    """یک stamp را به زیرمجموعهٔ whitelist تقلیل می‌دهد. UNKNOWN بی‌`value`."""
    if not isinstance(stamped, dict):
        return {"mode": "UNKNOWN", "reason": "not-a-stamp"}
    out = {k: stamped[k] for k in LIFECYCLE_STAMP_KEYS if k in stamped}
    if out.get("mode") == "UNKNOWN":
        out.pop("value", None)          # ناوردیِ ۲ ِ provenance
    return out


def _lifecycle_count_stamp(n: Any, source: str, ts_now: float) -> dict:
    """شمارش را تمبر می‌زند. `None`/منفی ⇒ UNKNOWN — هرگز صفر."""
    prov = _lifecycle_prov()
    try:
        value = None if n is None else int(n)
    except (TypeError, ValueError):
        value = None
    if value is not None and value < 0:
        value = None                    # قراردادِ `-1` ِ stalled_cards = UNKNOWN
    return prov.stamp(value, source, ts_now, LIFECYCLE_CADENCE_S, now=ts_now)


def get_lifecycle_state(root: "Path | None" = None,
                        state_dir: "Path | None" = None, *,
                        now: "float | None" = None,
                        _fold=None, _stalled=None) -> dict:
    """نمای خواندنیِ «این تصمیم کجاست» — فقط شمارش و timestamp.

    منبع: `_ops/lifecycle_fold.fold()` (همان مدلِ خواندنِ C1). عددِ `stalled`
    و `oldest_stalled_ts` عمداً از `stalled_cards()` می‌آیند نه از fold: آن
    مسیر **فقط** فایلِ کارت‌ها را می‌خواند و به دفترِ حکم‌ها دست نمی‌زند، پس
    عددی که کارتِ مالک را می‌سازد به هیچ side-effect ی وابسته نیست و دقیقاً
    با پروبِ C2 برابر می‌ماند.
    """
    if not lifecycle_enabled():
        # قراردادِ pf_miniapp: فلگ خاموش ⇒ مسیر وجود ندارد و صفر فایل باز می‌شود.
        return {"status": "disabled", "flag": LIFECYCLE_FLAG,
                "reason": "flag-off: nothing was read"}

    fold_fn, stalled_fn = _fold, _stalled
    if fold_fn is None or stalled_fn is None:
        import lifecycle_fold as _lf  # noqa: WPS433 — تنبل: خطای import مسیرِ دیگر را نکشد
        fold_fn = fold_fn or _lf.fold
        stalled_fn = stalled_fn or _lf.stalled_cards

    sd = _lifecycle_state_dir(root, state_dir)
    import time as _time  # noqa: WPS433
    ts_now = float(now) if now is not None else _time.time()

    folded = fold_fn(sd, now=ts_now)
    n_stalled, oldest, total = stalled_fn(sd, now=ts_now)

    sources = _lifecycle_safe_sources(folded.get("sources"))
    src0 = _LIFECYCLE_FALLBACK_SOURCE
    readable = bool(folded.get("readable"))

    counts = {}
    for name in LIFECYCLE_COUNTS:
        counts[name] = _lifecycle_stamp_view(folded.get(name))
    # «راکد» از پروبِ بی‌DB — همان عددی که C2 منتشر می‌کند.
    counts["stalled"] = _lifecycle_stamp_view(
        _lifecycle_count_stamp(n_stalled, src0, ts_now))

    by_stage: dict
    if readable and isinstance(folded.get("by_stage"), dict):
        by_stage = {"mode": "LIVE", "source": src0,
                    "value": {str(k): int(v) for k, v in folded["by_stage"].items()}}
    else:
        by_stage = {"mode": "UNKNOWN", "reason": "store-unreadable", "source": src0}

    if oldest is None:
        oldest_view = {"mode": "UNKNOWN", "reason": "no-timestamp", "source": src0}
    else:
        oldest_view = {"mode": "LIVE", "source": src0, "value": float(oldest)}

    out = {
        "status": "ok",
        "flag": LIFECYCLE_FLAG,
        "readable": readable,
        "counts": counts,
        "by_stage": by_stage,
        "oldest_stalled_ts": oldest_view,
        "total_cards": _lifecycle_stamp_view(
            _lifecycle_count_stamp(total if n_stalled is not None and int(n_stalled) >= 0
                                   else None, src0, ts_now)),
        # ۲۰۲۶-۰۸-۰۵ — رأیِ مالک: «کارت‌های راکد گزینش هست کار نمی‌کند؛ آدم
        # ببیند و از راکدی درش بیاورد.» تا آن روز این نما فقط **عدد** می‌داد،
        # پس ۲۹ کارتِ راکد (قدیمی‌ترین ~۱۰ روز) هیچ سطحی برای تصمیم نداشتند.
        # ۲۰۲۶-۰۸-۰۶ — رفعِ نشت: فهرستِ آن روز مستقیماً `rfc_id` خام را رد
        # می‌کرد و whitelist ِ سختِ همین نما (بندِ ۲) را دور می‌زد —
        # `test_miniapp_lifecycle_view` هر دو جهت را می‌گرفت. حالا فقط سن و
        # timestamp رد می‌شوند؛ کلیدِ تصمیم‌گیر (`rfc_id`) در تابعِ داخلیِ
        # `_lifecycle_stalled_rows` می‌ماند برای مصرف‌کنندهٔ backend، نه این
        # تونلِ خواندنیِ بیرونی.
        "stalled_list": _lifecycle_public_stalled_rows(folded, ts_now),
        "stalled_list_truncated": int(folded.get("stalled_list_truncated") or 0),
    }
    _lifecycle_enforce(out)
    # `sources` پس از دیوار سوار می‌شود چون allowlist ِ دقیقِ خودش را دارد
    # (نامِ فایلِ دفترِ حکم‌ها شاملِ «verdict» است ولی محتوای کارت نیست).
    out["sources"] = sources
    return out


# dispatcher برای gateway
# ── کشِ اسنپ‌شات (۲۰۲۶-۰۸-۰۴) ────────────────────────────────────────────────
# `test_miniapp_ops_readmodel` این کش را از ۰۸-۰۳ مشخص کرده بود ولی هرگز
# پیاده نشد: ۲۵ از ۲۸ تستش با `AttributeError: no attribute 'cache_clear'`
# می‌مردند و همان‌طور در `run_all` ثبت مانده بود. `OCTOPUS_MINIAPP_CACHE_TTL_S`
# هم صفر خوانندهٔ تولیدی داشت — یعنی «فلگِ فقط-تست» در دفترِ phantom_guards
# در واقع علامتِ همین قابلیتِ ساخته‌نشده بود.
#
# چرا اصلاً کش: هر `GET /api/*` چند فایلِ حالت و یک SQLite را می‌خواند، روی یک
# دیسکِ مکانیکیِ ۵۴۰۰ دور. شِلِ mini-app چند مسیر را پشتِ‌سرهم صدا می‌زند.
#
# ⚠️ مرزِ احراز: `dispatch_api` فقط بعد از `_read_api_authorized` صدا زده
# می‌شود (`miniapp_gateway`)، و آن allowlist **تک‌نفره** است (فقط owner id).
# پس محتوای کش‌شده هرگز از مرزِ کاربر عبور نمی‌کند — این کش برای یک نفر است.
_CACHE: dict = {}
_CACHE_LOCK = threading.RLock()

#: ساعتِ یکنواخت، **ماژول‌سطح** تا تست بتواند تزریقش کند. هرگز ساعتِ دیوار:
#: پرشِ ساعت نباید کش را ابدی یا فوراً منقضی کند.
_mono = time.monotonic

#: پیش‌فرض و **سقف**. سقف باربر است: یک عددِ بزرگ در env نباید دادهٔ کهنه سرو
#: کند. کفِ ۰ عمداً مجاز است تا بشود کش را کاملاً خاموش کرد.
_CACHE_TTL_DEFAULT = 3.0
_CACHE_TTL_MAX = 5.0


def _cache_ttl() -> float:
    raw = str(os.environ.get("OCTOPUS_MINIAPP_CACHE_TTL_S", "") or "").strip()
    if not raw:
        return _CACHE_TTL_DEFAULT
    try:
        return max(0.0, min(_CACHE_TTL_MAX, float(raw)))
    except (TypeError, ValueError):
        return _CACHE_TTL_DEFAULT      # ورودیِ بد = پیش‌فرض، نه استثنا


def cache_clear() -> None:
    """کش را خالی کن. تست‌ها بینِ کیس‌ها صدایش می‌زنند؛ تولید بعد از هر
    اقدامی که حالت را عوض می‌کند می‌تواند صدایش بزند."""
    with _CACHE_LOCK:
        _CACHE.clear()


def get_cognitive_scan_state(root: "Path | None" = None) -> dict:
    """اسکنای شناختیِ زنده: self-model، doctor، pulse، governor، semantic — یک‌جا.

    تبِ «اسکن‌ها» این داده را می‌خواند. فقط‌خواندنی، fail-soft، content-free.

    ⚠️ DEEP-SCAN ۲۰۲۶-۰۸-۰۸: نسخهٔ نخست `_runtime(root)` و `_read_json()` صد
    می‌زد — هر دو ناموجود. توابعِ درست `_RUNTIME` (ثابت) و `_read_json_safe()`
    هستند که بقیهٔ همین فایل استفاده می‌کنند. یعنی تبِ اسکن‌ها تا امروز ۵۰۰
    می‌داد و کاربر «خطا: name '_runtime' is not defined» می‌دید."""
    rt = STATE_DIR
    out = {"status": "ok", "schema": "cognitive-scan.v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    # ۱) self-model — خودآگاهیِ کد
    sm = _read_json_safe(rt / "cortex" / "self-model.json")
    if isinstance(sm, dict):
        # 2026-08-12 fix: updated_at از قبل برمی‌گشت ولی renderCognitiveScan
        # در app.js هیچ‌جا نمی‌خواندش — یک self-model کهنه همیشه با درصدِ
        # سبز/به‌ظاهر-تازه نشان داده می‌شد. age_s از mtimeِ خودِ فایل
        # مستقیم‌تر و مستقل از فرمتِ رشتهٔ ts است.
        try:
            sm_age_s = time.time() - (rt / "cortex" / "self-model.json").stat().st_mtime
        except OSError:
            sm_age_s = None
        out["self_model"] = {
            "modules": sm.get("n_modules"),
            "self_awareness_pct": sm.get("self_awareness_pct"),
            "total_lines": sm.get("total_lines"),
            "n_tests": sm.get("n_tests"),
            "undocumented": len(sm.get("undocumented_modules", []) or []),
            "updated_at": sm.get("updated_at", sm.get("ts", "")),
            "age_s": round(sm_age_s, 1) if sm_age_s is not None else None,
        }
    else:
        out["self_model"] = {"error": True}
    # ۲) doctor self-knowledge
    sk = _read_json_safe(rt / "doctor" / "self-knowledge-latest.json")
    if isinstance(sk, dict):
        # self_accuracy در فایل یک **object** است ({accuracy, confidence, drifts, ...})
        # نه یک عدد. استخراجِ عددِ ساده برای UI:
        sa_raw = sk.get("self_accuracy")
        if isinstance(sa_raw, dict):
            sa_pct = sa_raw.get("accuracy")
        elif isinstance(sa_raw, (int, float)):
            sa_pct = sa_raw
        else:
            sa_pct = None
        out["doctor"] = {
            "version": sk.get("version"),
            "stable_cycles": sk.get("stable_cycles"),
            "self_accuracy": sa_pct,
            "deep_dive_ran": sk.get("deep_dive_ran"),
            "owner_corrections": len(sk.get("owner_corrections", []) or []),
        }
    else:
        out["doctor"] = {"error": True}
    # ۳) pulse-arbiter — قلب
    pa = _read_json_safe(rt / "pulse" / "arbiter-latest.json")
    if isinstance(pa, dict):
        out["pulse"] = {
            "effective_period_s": pa.get("effective_period_s"),
            "driver": pa.get("driver"),
            "color": pa.get("color"),
            "n_present": pa.get("n_present"),
            "n_moving": pa.get("n_moving"),
        }
    else:
        out["pulse"] = {"error": True}
    # ۴) BCM — یادگیری. مسیرِ واقعی bcm-weights.json نیست؛ state زیرِ
    # memory/ است. هر دو را می‌آزما تا داده‌ای را که پروسهٔ زنده نوشته پیدا کن.
    bcm = _read_json_safe(rt / "memory" / "bcm-weights.json") \
          or _read_json_safe(rt / "bcm-weights.json")
    if isinstance(bcm, dict):
        steps = bcm.get("step", 0)
        keys = [k for k in bcm if k.startswith("cycle-")]
        out["bcm"] = {"step": steps, "cycles": len(keys)} if keys else {"step": steps}
    else:
        out["bcm"] = {"error": True}
    # ۵) semantic memory — آخرین reflections
    try:
        sem = rt / "memory" / "semantic_memory.jsonl"
        if not sem.exists():
            sem = rt / "semantic_memory.jsonl"
        n = 0
        latest_gist = ""
        if sem.exists():
            lines = sem.read_text("utf-8").splitlines()
            n = len(lines)
            if lines:
                latest_gist = str(json.loads(lines[-1]).get("gist", ""))[:80]
        out["semantic"] = {"total": n, "latest_gist": latest_gist}
    except Exception:  # noqa: BLE001
        out["semantic"] = {"error": True}
    # ۶) consolidation
    cur = _read_json_safe(rt / "cortex" / "consolidate-cursor.json")
    if isinstance(cur, dict):
        out["consolidation"] = {
            "last_run": cur.get("ts", ""),
            "n_in": cur.get("n_in", 0),
            "n_semantic": cur.get("n_semantic", 0),
        }
    else:
        out["consolidation"] = {"error": True}
    return out


def get_agent_log_state(root: "Path | None" = None) -> dict:
    """لاگِ تغییراتِ ایجنت — آخرین commitهای git (نوشته‌ی ایجنت‌ها).

    تبِ «اسکن‌ها» این داده را می‌خواند. فقط‌خواندنی، content-free (نه diff)."""
    import subprocess
    out = {"status": "ok", "schema": "agent-log.v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "commits": []}
    try:
        repo = _OPS.parent  # vault root
        result = subprocess.run(
            ["git", "log", "--oneline", "--no-decorate", "-20",
             "--format=%h|%an|%s|%ci"],
            cwd=str(repo), capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                parts = line.split("|", 3)
                if len(parts) >= 4:
                    out["commits"].append({
                        "hash": parts[0][:7],
                        "author": str(parts[1])[:30],
                        "message": str(parts[2])[:100],
                        "date": str(parts[3])[:16],
                    })
    except Exception:  # noqa: BLE001
        out["commits"] = []
        out["status"] = "error"
    return out


def dispatch_api(path: str, root: "Path | None" = None) -> "tuple[int, bytes, str]":
    """GET /api/* dispatcher. خروجی: (status, body_bytes, content_type)."""
    p = str(path or "").split("?", 1)[0]
    handlers = {
        "/api/state": get_miniapp_state,
        "/api/outbound": get_outbound_state,
        "/api/approvals": get_approvals_state,
        "/api/legs": get_legs_state,
        "/api/notifications": get_notifications_state,
        "/api/value": get_value_state,
        "/api/money-caps": get_money_caps_state,
        "/api/ui-registry": get_ui_registry,
        "/api/current-truth": get_current_truth,
        "/api/ops": get_ops_state,
        # سه زیرمسیرِ برشِ سبک — این‌ها هم در `935e8b0` از جدول افتادند در حالی
        # که هر سه در `READ_API_PATHS` ِ gateway مانده بودند ⇒ سه مسیرِ اعلام‌شده
        # که ۴۰۴ می‌دادند. توابعشان بالاتر بازیابی شدند.
        "/api/ops/brain": get_ops_brain,
        "/api/ops/leads": get_ops_leads,
        "/api/ops/tasks": get_ops_tasks,
        # ۲۰۲۶-۰۸-۰۴ — دو تابعِ **یتیم**: `get_governor_state` و
        # `get_obsidian_state` نوشته شده بودند و هیچ مسیری نداشتند، پس تبِ
        # متناظرشان در مینی‌اپ هیچ‌وقت داده‌ای برای نشان‌دادن نداشت. سمتِ
        # سرور چیزی ساخته نشد؛ فقط چیزی که از قبل کار می‌کرد **قابلِ صدا
        # زدن** شد.
        "/api/governor": get_governor_state,
        "/api/obsidian": get_obsidian_state,
        # نقشهٔ خودآگاهی — مالک گفت تعاملِ اصلی‌اش وب‌اپ است، پس آنچه
        # تا امروز فقط در خطِ فرمان دیده می‌شد باید این‌جا باشد.
        "/api/selfmap": get_selfmap_state,
        # ۲۰۲۶-۰۸-۰۸ — تبِ «اسکن‌ها»: شناختیِ زنده + لاگِ ایجنت
        "/api/cognitive-scan": get_cognitive_scan_state,
        "/api/agent-log": get_agent_log_state,
        # ۲۰۲۶-۰۸-۱۳ (ADR-039 C6) — پنلِ فقط‌خواندنیِ epistemic (owner override)
        "/api/epistemic": get_epistemic_state,
        LIFECYCLE_PATH: get_lifecycle_state,
    }
    fn = handlers.get(p)
    if fn is None:
        return 404, b'{"status":"not_found"}', "application/json; charset=utf-8"
    if p == LIFECYCLE_PATH and not lifecycle_enabled():
        # فلگ خاموش ⇒ مسیر **وجود ندارد**؛ همان قراردادِ pf_miniapp، نه ۲۰۰ ِ تهی.
        return 404, b'{"status":"not_found"}', "application/json; charset=utf-8"
    # کش فقط برای فراخوانِ پیش‌فرض (`root=None`). با root ِ صریح دور زده می‌شود:
    # دو ریشهٔ متفاوت هرگز نباید یک ورودیِ کش را به اشتراک بگذارند.
    ttl = _cache_ttl()
    use_cache = root is None and ttl > 0.0
    if use_cache:
        with _CACHE_LOCK:
            hit = _CACHE.get(p)
        if hit is not None and (_mono() - hit[0]) < ttl:
            return 200, hit[1], "application/json; charset=utf-8"
    try:
        data = fn(root)
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        # ⚠️ خطا هرگز کش نمی‌شود. دو دلیل: (۱) یک قطعیِ گذرا نباید تا انقضای
        # TTL به‌عنوان حقیقت سرو شود؛ (۲) وقتی منبع برگشت، همان تیک باید حقیقت
        # را بگوید نه خطای کهنه را.
        if use_cache and str((data or {}).get("status", "ok")) != "error":
            with _CACHE_LOCK:
                _CACHE[p] = (_mono(), body)
        return 200, body, "application/json; charset=utf-8"
    except Exception as exc:  # noqa: BLE001 — fail-closed، هرگز crash
        # استثنا هم وارد کش نمی‌شود — یک ثانیهٔ بد نباید چند ثانیه دروغ بسازد.
        return 500, json.dumps({"status": "error", "reason": f"{type(exc).__name__}"}).encode("utf-8"), \
            "application/json; charset=utf-8"



# ══ بازیابی‌شده از کامیتِ 3a8cb2d (۲۰۲۶-۰۸-۰۴) ══════════════════════════
# کامیتِ  (لِینِ موازیِ unification) این فایل را از ۸۶۴ خط به ۵۳۹ خط
# برد و ۳۵ نمادِ سطح‌بالا را با خودش برد — کلِ read-model ِ 
# (brain/governor/obsidian/next_steps) که خودش در  با ۵۵۷ خط تست
# ساخته شده بود. نه revert بود نه تصمیم؛ یک بازنویسیِ فایل.
# نشانه‌اش ۲۵ تستِ قرمز بود که ماه‌ها «تستِ جلوتر از کد» تفسیر می‌شد.
# افزوده‌های خودِ 935e8b0 (کلِ سطحِ lifecycle، ۱۸ نماد) دست‌نخورده بالا مانده‌اند.
_4D_ROOT = _ROOT / "4d_system"

_4D_OUTPUTS = _4D_ROOT / "outputs"

_4D_CONSOLIDATION_PY = _4D_ROOT / "brain" / "consolidation.py"

_NEURAL_CONSOLIDATION = _OPS / "neural" / "consolidation.json"

# ۲۰۲۶-۰۸-۰۵ — نقشهٔ G1: مغزِ زندهٔ cortex (۸۷۷۲)، ثابتِ سطحِ‌ماژول مثلِ
# `_4D_OUTPUTS` تا تست‌ها بتوانند مسیرش را monkey-patch کنند.
_CORTEX_STATE_PATH = _OPS / "state" / "cortex" / "cortex-state.json"

_BUDGETS_YAML = _OPS / "budget" / "budgets.yaml"

_FUGU_POLICY_REL = "docs/fugu_usage_policy.md"

_CANONICAL_PROVIDER_REL = "_ops/cortex/model_router.py"

_CANONICAL_CHOKE_POINT = "ask()"

_PATH_ROOTS = ("", "_ops", "4d_system")

_OBSIDIAN_DOCS = (
    # SoT دستورالعمل ریشه نیست — زیر agent-prompts است (فیکس ۲۰۲۶-۰۸-۱۲)
    "agent-prompts/_PROJECT_INSTRUCTIONS.md",
    "CLAUDE.md",
    ".agentignore",
    "01 - Dashboard/HANDOFF.md",
    "01 - Dashboard/Home.md",
    "06 - Architecture Maps/ECOSYSTEM.md",
    "06 - Architecture Maps/Property Schema.md",
    "10 - Telegram processing/SOP.md",
    "10 - Telegram processing/ROUTING.md",
    _FUGU_POLICY_REL,
)

def _read_json_any(path: Path):
    """مثلِ `_read_json_safe` ولی list را هم می‌پذیرد (فایل‌های append-only ِ چرخه)."""
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text("utf-8"))
    except (OSError, ValueError, TypeError):
        return None

def _as_int(v):
    """int یا None — هرگز صفرِ جعلی به‌جای «نمی‌دانم»."""
    if isinstance(v, bool) or v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None

def _iso(ts):
    """timestamp عددی → ISO ِ محلی؛ هر چیزِ دیگر → None (نه رشتهٔ ساختگی)."""
    try:
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(float(ts)))
    except (TypeError, ValueError, OSError):
        return None

def _exists(p: Path) -> bool:
    try:
        return p.exists()
    except OSError:
        return False

def _brain_daemon() -> dict:
    """پاهای daemon ِ مغزِ 4D — منبع: همان فایلی که خودش می‌نویسد.

    `4d_system/brain/daemon.py:_save_state` → `<OUTPUT_DIR>/daemon_state.json`.
    عمداً `config.settings` را import نمی‌کنیم: آن ماژول در import ِ خودش
    `OUTPUT_DIR.mkdir()` می‌زند و یک سطحِ **فقط‌خواندنی** حق ندارد پوشه بسازد."""
    p = _4D_OUTPUTS / "daemon_state.json"
    src = "4d_system/outputs/daemon_state.json"
    d = _read_json_safe(p)
    if d is None:
        return {"reachable": False, "ticks": None, "errors": None,
                "last_tick": None, "generation": None,
                "reason": f"unreadable or absent: {src}", "source": src}
    fields = {"ticks": _as_int(d.get("total_ticks")),
              "errors": _as_int(d.get("errors_this_run")),
              "last_tick": d.get("last_tick_at") or None,
              "generation": _as_int(d.get("generation"))}
    missing = sorted(k for k, v in fields.items() if v is None)
    return {"reachable": True, "reason": None, "source": src,
            "missing_fields": missing, **fields}

def _brain_consolidation() -> dict:
    """تثبیت مغز — primary = neural live؛ 4d secondary (DEPRECATED/ممکن خالی).

    DW-06 2026-08-12: قبلاً available فقط وقتی موتور 4d + فایل‌های self_evolved
    زنده بودند → پنل سبز/قرمز دروغین. الان neural/_ops اول است."""
    sd = _4D_OUTPUTS / "self_evolved"
    src_c = "4d_system/outputs/self_evolved/conclusions.json"
    src_f = "4d_system/outputs/self_evolved/frontier.json"
    src_y = "4d_system/outputs/self_evolved/consolidation.json"
    src_n = "_ops/neural/consolidation.json"
    engine_present = _exists(_4D_CONSOLIDATION_PY)
    concl = _read_json_safe(sd / "conclusions.json")
    front = _read_json_safe(sd / "frontier.json")
    cycles = _read_json_any(sd / "consolidation.json")
    neural = _read_json_any(_NEURAL_CONSOLIDATION)

    reasons = []
    n_concl = None
    if isinstance(concl, dict) and isinstance(concl.get("conclusions_fa"), list):
        n_concl = len(concl["conclusions_fa"])
    else:
        reasons.append(f"no conclusions_fa list in {src_c}")
    n_front = None
    if isinstance(front, dict):
        n_front = len(front)
    else:
        reasons.append(f"no cell archive in {src_f}")
    last_verified, last_sources = None, None
    if isinstance(cycles, list) and cycles and isinstance(cycles[-1], dict):
        last_verified = _iso(cycles[-1].get("timestamp"))
        vs = cycles[-1].get("verified_sources")
        last_sources = vs if isinstance(vs, list) else None
    else:
        reasons.append(f"no cycle history in {src_y}")

    neural_cycles = None
    neural_insights = None
    if isinstance(neural, list):
        neural_cycles = len(neural)
    elif isinstance(neural, dict):
        insights = neural.get("insights")
        if isinstance(insights, list):
            neural_insights = len(insights)
        # some writers store cycles under history/cycles
        for key in ("cycles", "history", "records"):
            if isinstance(neural.get(key), list):
                neural_cycles = len(neural[key])
                break
        if neural_cycles is None and neural:
            neural_cycles = 1  # non-empty dict counts as present
    if neural_cycles is None and neural_insights is None:
        reasons.append(f"no neural consolidation payload in {src_n}")
    if not engine_present:
        reasons.append("4d_system/brain/consolidation.py absent (expected; DEPRECATED)")

    neural_ok = (neural_cycles is not None) or (neural_insights is not None)
    four_d_ok = bool(engine_present and (n_concl is not None or n_front is not None
                                         or last_verified is not None))
    available = bool(neural_ok or four_d_ok)
    primary = "neural" if neural_ok else ("4d" if four_d_ok else "none")
    return {
        "available": available,
        "primary": primary,
        "conclusions_count": n_concl,
        "frontier_count": n_front,
        "last_verified": last_verified,
        "last_verified_sources": last_sources,
        "neural_cycles": neural_cycles,
        "neural_insights": neural_insights,
        "four_d_available": four_d_ok,
        "reason": None if available and not reasons else ("; ".join(reasons) or None),
        "sources": {"conclusions": src_c, "frontier": src_f,
                    "cycles": src_y, "neural_cycles": src_n,
                    "primary": src_n if primary == "neural" else src_y,
                    "engine": "4d_system/brain/consolidation.py"},
    }

def _cortex_state() -> dict:
    """مغزِ زندهٔ cortex (پورت ۸۷۷۲، پروسهٔ جدا از organism) — منبع:
    `state/cortex/cortex-state.json`، نوشتهٔ خودِ دیمن هر چرخه (~هر ۱-۲ دقیقه).

    ⚠️ ۲۰۲۶-۰۸-۰۵ — این فایل تا امروز اصلاً در ریدمدلِ brain نبود؛ `daemon`ِ
    زیر همیشه سیستمِ ۴D را می‌خواند که مغزِ **دیگری** است (نقشهٔ کامل:
    `07 - Knowledge/شناخت-اختاپوس/12-BRAIN-HEART-CONTROL-PANEL-MAP-2026-08-05.md`،
    یافتهٔ G1). این تابع اضافه شد، `daemon`/`consolidation` دست‌نخورده ماندند —
    UI ِ زنده نباید بشکند."""
    p = _CORTEX_STATE_PATH
    src = "_ops/state/cortex/cortex-state.json"
    d = _read_json_safe(p)
    if d is None:
        return {"reachable": False, "reason": f"unreadable or absent: {src}", "source": src}
    return {
        "reachable": True, "reason": None, "source": src,
        "ts": d.get("ts"), "cycle": _as_int(d.get("cycle")),
        "coherence": d.get("coherence"),
        "thought": d.get("thought"),
        "stress": d.get("stress") if isinstance(d.get("stress"), dict) else None,
        "hypothesis_brain": d.get("hypothesis_brain"),
        "schema": d.get("schema"),
    }

def get_brain_state(root: "Path | None" = None) -> dict:
    """بخشِ brain ِ /api/ops — fail-soft: نخواندن هرگز پاسخ را نمی‌کشد."""
    daemon = _brain_daemon()
    cons = _brain_consolidation()
    cortex = _cortex_state()
    available = bool(daemon.get("reachable") or cons.get("available") or cortex.get("reachable"))
    reason = None
    if not available:
        reason = "; ".join(x for x in (daemon.get("reason"), cons.get("reason"), cortex.get("reason")) if x) \
            or "brain sources unreadable"
    return {"available": available, "reason": reason,
            "cortex": cortex, "daemon": daemon, "consolidation": cons}

def _resolve_declared(rel: str, r: Path) -> "str | None":
    """مسیرِ کوتاه‌نویسیِ سند را زیرِ ریشه‌های ممکن پیدا کن؛ نبود = None."""
    rel = rel.rstrip("/")
    for base in _PATH_ROOTS:
        cand = (r / base / rel) if base else (r / rel)
        try:
            if cand.exists():
                return (f"{base}/{rel}" if base else rel)
        except OSError:
            continue
    return None

def _policy_declared_paths(doc: Path, r: Path) -> list:
    """مسیرهایی که خودِ سندِ سیاست نام می‌برد + سنجشِ وجودِ هرکدام."""
    try:
        text = doc.read_text("utf-8", errors="replace")
    except OSError:
        return []
    out, seen = [], set()
    for m in re.finditer(r"`([^`\n]{3,120})`", text):
        s = m.group(1).strip()
        if "/" not in s or s.startswith("http"):
            continue
        if not (s.endswith(".py") or s.endswith(".ts") or s.endswith(".js")
                or s.endswith("/")):
            continue
        if s in seen:
            continue
        seen.add(s)
        found = _resolve_declared(s, r)
        out.append({"declared": s, "exists": found is not None, "resolved": found})
    return out

def _governor_drift(r: Path, policy: "Path | None", canonical_ok: bool) -> dict:
    """drift **مشتق** است نه اعلامی: سند را می‌خوانیم و مسیرهایش را می‌سنجیم."""
    if policy is None:
        return {"status": "unknown", "reason": f"policy doc absent: {_FUGU_POLICY_REL}",
                "declared_paths": [], "missing": [], "notes": []}
    declared = _policy_declared_paths(policy, r)
    if not declared:
        return {"status": "unknown", "reason": "no provider paths parsed from policy doc",
                "declared_paths": [], "missing": [], "notes": []}
    missing = [d["declared"] for d in declared if not d["exists"]]
    notes = [f"policy names `{m}` but it does not exist in this tree" for m in missing]
    try:
        text = policy.read_text("utf-8", errors="replace")
    except OSError:
        text = ""
    for line in text.splitlines():
        if _CANONICAL_PROVIDER_REL in line and "migrate" in line.lower():
            notes.append(f"policy marks the measured choke point "
                         f"`{_CANONICAL_PROVIDER_REL}` as pending migration")
            break
    if not canonical_ok:
        notes.append(f"canonical provider absent: {_CANONICAL_PROVIDER_REL}")
    return {"status": "drift" if (missing or not canonical_ok) else "aligned",
            "reason": None, "declared_paths": declared,
            "missing": missing, "notes": notes}

def _router_tier_roles(r: Path) -> "dict | None":
    """نگاشتِ tier→role ِ `model_router._TIER_ROLE` با خواندنِ **متنِ** خودِ فایل.

    عمداً import نمی‌کنیم: model_router به opslib/circuit_breaker/local_llm
    وصل است و این ماژول قراردادِ «صفر side-effect» دارد."""
    try:
        src = (r / _CANONICAL_PROVIDER_REL).read_text("utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(r"_TIER_ROLE\s*=\s*\{([^}]*)\}", src)
    if not m:
        return None
    return dict(re.findall(r"[\"'](\w+)[\"']\s*:\s*[\"'](\w+)[\"']", m.group(1)))

def _budget_role_models(path: Path) -> dict:
    """role → model از `budgets.yaml` (بدونِ وابستگی به pyyaml)."""
    try:
        text = path.read_text("utf-8", errors="replace")
    except OSError:
        return {}
    out, role, in_routing = {}, None, False
    for line in text.splitlines():
        if re.match(r"^routing:\s*(#.*)?$", line):
            in_routing = True
            continue
        if in_routing and line and not line.startswith(" "):
            break
        if not in_routing:
            continue
        m = re.match(r"^  ([A-Za-z_][A-Za-z0-9_]*):\s*(#.*)?$", line)
        if m:
            role = m.group(1)
            continue
        m2 = re.match(r"^\s{3,}model:\s*\"?([^\"#\s]+)\"?", line)
        if m2 and role:
            out.setdefault(role, m2.group(1))
    return out

_ROUTE_SPEC = (("local", "local"), ("fugu", "orchestr"),
               ("fugu_ultra", "premium"), ("fugu_cyber", None))

def _governor_routes(r: Path) -> dict:
    """چهار مسیرِ اعلام‌شده + این‌که آیا واقعاً از `ask()` دست‌یافتنی‌اند.

    «دست‌یافتنی» یعنی role اش در `_TIER_ROLE` باشد (یا local که fallback ِ
    ساختاریِ مسیریاب است). هر ادعای دیگری بدونِ شاهد = null با دلیل."""
    roles = _router_tier_roles(r)
    models = _budget_role_models(_BUDGETS_YAML)
    role_to_tier = {v: k for k, v in (roles or {}).items()}
    out = {}
    for name, role in _ROUTE_SPEC:
        model = models.get(role) if role else None
        if roles is None:
            out[name] = {"role": role, "model": model, "tier": None,
                         "reachable_from_ask": None,
                         "reason": f"could not parse _TIER_ROLE from {_CANONICAL_PROVIDER_REL}"}
            continue
        if role == "local":
            out[name] = {"role": "local", "model": model, "tier": "local",
                         "reachable_from_ask": True, "reason": None}
            continue
        tier = role_to_tier.get(role) if role else None
        reach = tier is not None
        reason = None
        if role is None:
            reason = ("no 'cyber' role in budgets.yaml routing and no cyber tier in "
                      f"{_CANONICAL_PROVIDER_REL}:_TIER_ROLE")
        elif not reach:
            reason = (f"role '{role}' is not mapped by "
                      f"{_CANONICAL_PROVIDER_REL}:_TIER_ROLE — unreachable from ask()")
        out[name] = {"role": role, "model": model, "tier": tier,
                     "reachable_from_ask": reach, "reason": reason}
    return out

def get_governor_state(root: "Path | None" = None) -> dict:
    """بخشِ governor — هیچ مسیری بدونِ سنجشِ وجود ادعا نمی‌شود."""
    r = Path(root) if root is not None else _ROOT
    policy = r / _FUGU_POLICY_REL
    canon = r / _CANONICAL_PROVIDER_REL
    policy_ok = _exists(policy)
    canon_ok = _exists(canon)
    return {
        "policy_doc": _FUGU_POLICY_REL if policy_ok else None,
        "policy_doc_reason": None if policy_ok else f"not found: {_FUGU_POLICY_REL}",
        "canonical_provider": _CANONICAL_PROVIDER_REL if canon_ok else None,
        "canonical_provider_reason": None if canon_ok else
            f"not found: {_CANONICAL_PROVIDER_REL}",
        "canonical_choke_point": _CANONICAL_CHOKE_POINT if canon_ok else None,
        "drift_status": _governor_drift(r, policy if policy_ok else None, canon_ok),
        "routes": _governor_routes(r),
    }

def get_obsidian_state(root: "Path | None" = None) -> dict:
    """بخشِ obsidian — **هر** مسیر سنجیده می‌شود.

    سطحِ حقیقتی که فایلِ غایب را «هست» اعلام کند، دقیقاً همان drift ای است که
    برای جلوگیری‌اش ساخته شده. مقدارِ خامِ REFERENCE_DIR بیرون نمی‌رود؛ فقط
    «پیکربندی شده یا نه»."""
    r = Path(root) if root is not None else _ROOT
    raw = str(os.environ.get("REFERENCE_DIR", "") or "").strip()
    ref_ok = False
    if raw:
        try:
            rp = Path(raw)
            rp = rp if rp.is_absolute() else (r / raw)
            ref_ok = rp.is_dir()
        except (OSError, ValueError):
            ref_ok = False
    docs = {}
    # ⚠️ رگرسیونِ ۲۰۲۶-۰۸-۰۵ (خودساخته): وقتی ثابتِ تاریخ‌دارِ `_TRUTH` حذف شد
    # تا تبِ حقیقت درست شود، این مصرف‌کننده جا ماند ⇒ هر فراخوانِ
    # `/api/obsidian` یک `NameError` می‌داد. و بدتر: `renderObsidian` خطا را
    # به «کامل — همهٔ سندهای مرجع سرِ جایشان‌اند» ترجمه می‌کرد، یعنی یک
    # ۵۰۰ ِ خاموش به **اطمینانِ سبز** تبدیل می‌شد.
    # حالا از همان یابنده استفاده می‌شود؛ نبودِ فایل هم یک ردیفِ صادق است نه crash.
    #
    # ⚠️ ۲۰۲۶-۰۸-۱۲: قبلاً فقط `_t.name` (=CURRENT-TRUTH.md) چک می‌شد →
    # مسیر ریشهٔ vault غایب دیده می‌شد در حالی که فایل در OCTOPUS/ بود.
    for rel in _OBSIDIAN_DOCS:
        docs[rel] = {"exists": _exists(r / rel)}
    _t = _find_truth()
    if _t is not None:
        try:
            rel_truth = _t.resolve().relative_to(r.resolve()).as_posix()
        except ValueError:
            rel_truth = "OCTOPUS/CURRENT-TRUTH.md"
        docs[rel_truth] = {"exists": True}
    else:
        docs["OCTOPUS/CURRENT-TRUTH.md"] = {"exists": False}
    missing = sorted(k for k, v in docs.items() if not v["exists"])
    return {
        "reference_dir_configured": bool(raw and ref_ok),
        "reference_dir_reason": None if (raw and ref_ok) else (
            "REFERENCE_DIR env not set" if not raw
            else "REFERENCE_DIR set but the directory does not exist"),
        "vault_config_dir": _exists(r / ".obsidian"),
        "docs": docs,
        "missing": missing,
        "missing_count": len(missing),
        "checked": len(docs),
        "status": "ok" if not missing else "incomplete",
    }

def _ui_has(name: str, needles: tuple, need_all: bool = False) -> "bool | None":
    """آیا فایلِ UI ِ کاکپیت این نشانه‌ها را دارد؟ نخواندن = None (نه False).

    `need_all=True` وقتی نشانه‌ها **فهرستِ لازم**اند (چهار تب)، نه املاهای جایگزین."""
    try:
        text = (_HERE / "miniapp" / name).read_text("utf-8", errors="replace")
    except OSError:
        return None
    hits = [n in text for n in needles]
    return all(hits) if need_all else any(hits)

def _step(sid: str, title: str, status: str, evidence: str) -> dict:
    return {"id": sid, "title": title, "status": status, "evidence": evidence}

def get_next_steps(root: "Path | None" = None) -> list:
    """ترتیبِ ساختِ فعلی — وضعیتِ هر قدم **سنجیده** می‌شود نه اعلام.

    قدم‌های UI با خواندنِ خودِ `miniapp/index.html` و `miniapp/app.js` سنجیده
    می‌شوند (لِینِ دیگری مالکِ آن‌هاست؛ این‌جا فقط خوانده می‌شود)."""
    r = Path(root) if root is not None else _ROOT
    tabs = _ui_has("index.html", ('data-tab="brain"', 'data-tab="governor"',
                                  'data-tab="obsidian"', 'data-tab="next"'),
                   need_all=True)
    palette = _ui_has("app.js", ("palette", "Palette"))
    nba = _ui_has("app.js", ("nextBest", "next_best", "next-best"))
    policy = r / _FUGU_POLICY_REL
    drift = _governor_drift(r, policy if _exists(policy) else None,
                            _exists(r / _CANONICAL_PROVIDER_REL))

    def tri(v: "bool | None") -> str:
        return "unknown" if v is None else ("done" if v else "open")

    return [
        _step("ops-read-model",
              "/api/ops = تنها سطحِ صادقِ خواندنی (brain/governor/obsidian/next_steps)",
              "done", "miniapp_state.get_ops_state"),
        _step("ops-subendpoints",
              "زیرمسیرهای /api/ops/brain · /api/ops/leads · /api/ops/tasks",
              "done", "miniapp_state.dispatch_api handlers"),
        _step("ops-snapshot-cache", "کشِ ۲–۵ ثانیه‌ایِ اسنپ‌شات (خطا هرگز کش نمی‌شود)",
              "done", f"miniapp_state cache ttl={_cache_ttl():g}s"),
        _step("miniapp-tabs", "تب‌های Brain/Governor/Obsidian/Next در کاکپیت",
              tri(tabs), "miniapp/index.html data-tab"),
        _step("command-palette", "پالتِ فرمان در کاکپیت", tri(palette), "miniapp/app.js"),
        _step("next-best-action", "کارتِ «بهترین اقدامِ بعدی»", tri(nba), "miniapp/app.js"),
        _step("fugu-policy-drift",
              "بستنِ drift ِ سندِ سیاستِ Fugu (مسیرهای اعلام‌شدهٔ ناموجود)",
              "open" if drift.get("status") == "drift" else
              ("unknown" if drift.get("status") == "unknown" else "done"),
              f"governor.drift_status={drift.get('status')}"),
    ]

def _engine_summary(root: "Path | None" = None) -> dict:
    """خلاصهٔ خامِ موتورِ Ops — تنها نقطهٔ تماس با SQLite ِ محلی.

    جدا شد تا `/api/ops/leads` و `/api/ops/tasks` بتوانند **بدونِ** ساختنِ
    بخش‌های سنگینِ brain/governor/obsidian جواب بدهند."""
    try:
        import sys as _sys
        ops_path = str(_OPS)
        if ops_path not in _sys.path:
            _sys.path.insert(0, ops_path)
        from agi2027_control.ops_actions import OpsActionEngine  # noqa: WPS433
        eng = OpsActionEngine(Path(root) if root is not None else _ROOT)
        try:
            return dict(eng.summary())
        finally:
            eng.close()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "reason": f"{type(exc).__name__}"}

def _section(fn, root, name: str, empty):
    """هر بخش در قرنطینهٔ خودش — یک بخشِ خراب هرگز کلِ /api/ops را نمی‌کشد."""
    try:
        return fn(root)
    except Exception as exc:  # noqa: BLE001
        if isinstance(empty, list):
            return []
        out = dict(empty)
        out["reason"] = f"{name}_read_failed: {type(exc).__name__}"
        return out

def get_ops_brain(root: "Path | None" = None) -> dict:
    """`/api/ops/brain` — دقیقاً همان بخشِ brain ِ /api/ops، بدونِ بقیه."""
    return _scrub_dict({"status": "ok", "section": "brain",
                        "brain": _section(get_brain_state, root, "brain",
                                          {"available": False, "daemon": {},
                                           "consolidation": {}})})

#: تنها ستون‌هایی که از هر ردیف بیرون می‌آیند. **allowlist**، نه حذفِ چندتا
#: ستونِ بد: ستونِ تازه‌ای که فردا اضافه شود باید عمداً این‌جا نوشته شود،
#: وگرنه خودبه‌خود روی تونل نمی‌رود. عمداً `notes` و `tags_json` نیستند —
#: متنِ آزادِ مالک می‌تواند هر چیزی داشته باشد.
_TASK_COLS = ("id", "title", "kind", "status", "priority", "due_at")
_LEAD_COLS = ("id", "handle", "stage", "value_estimate")
#: سقفِ ردیف — مینی‌اپ فهرستِ کار است نه صادرکنندهٔ پایگاه‌داده.
_ITEMS_MAX = 50


def _ops_items(table: str, cols: "tuple[str, ...]", where: str,
               order: str, root: "Path | None" = None) -> "list[dict] | None":
    """چند ردیفِ اول از یک جدولِ ops — فقط ستون‌های allowlist‌شده.

    چرا لازم شد: خواندنیِ قبلی فقط **شمارش** می‌داد. با شمارشِ تنها،
    `task.done` هیچ هدفی برای انتخاب ندارد و دکمه‌اش می‌شود یک ورودیِ
    متنیِ شناسه — یعنی عملاً بی‌استفاده.

    غیبت ⇒ `None` (نه `[]`): «پایگاه‌داده نیست» و «هیچ کاری نیست» دو چیزِ
    متفاوت‌اند و UI باید بتواند فرقشان را بگذارد.
    """
    try:
        from agi2027_control.ops_actions import OpsActionEngine  # noqa: WPS433
    except Exception:  # noqa: BLE001
        return None
    eng = None
    try:
        eng = OpsActionEngine(root=Path(root)) if root else OpsActionEngine()
        sql = (f"SELECT {','.join(cols)} FROM {table} "  # noqa: S608 — cols ثابت‌اند
               f"{where} ORDER BY {order} LIMIT {int(_ITEMS_MAX)}")
        rows = eng.db.conn.execute(sql).fetchall()
        return [dict(zip(cols, r)) for r in rows]
    except Exception:  # noqa: BLE001
        return None
    finally:
        if eng is not None:
            try:
                eng.close()
            except Exception:  # noqa: BLE001
                pass


def get_selfmap_state(root: "Path | None" = None) -> dict:
    """`/api/selfmap` — «اختاپوس دربارهٔ خودش چه می‌داند؟»

    مالک گفت تعاملِ اصلی‌اش وب‌اپ است، پس چیزهایی که تا امروز فقط در خطِ
    فرمان دیده می‌شدند باید این‌جا باشند. سه منبع، همه از قبل موجود:

      · `reach_probe`      — چه چیزی **واقعاً دوید** (زمانِ اجرا، قطعی)
      · `orphan_scan`      — چه چیزی به هیچ‌چیز وصل نیست (ایستا، محافظه‌کار)
      · `dark_capabilities`— کدام فلگ کد دارد و در هیچ پروسه‌ای روشن نیست

    ⚠️ اسکنِ ایستا این‌جا **دوباره اجرا نمی‌شود**: `orphan_scan` ۷.۸ ثانیه و
    `self_scan` ۴۶ ثانیه طول می‌کشند و این مسیر باید در چند صد میلی‌ثانیه
    جواب بدهد. مغزِ کاکپیت آن‌ها را ساعتی/روزانه می‌دواند و نتیجه را در
    حافظه‌اش می‌گذارد؛ این‌جا فقط همان حافظه خوانده می‌شود، با سنِ صریح تا
    عددِ کهنه شبیهِ تازه دیده نشود.

    ⚠️⚠️ و قیدِ باربر: **غیاب ≠ «نپرید»**. اگر پروب در پروسه‌ای نصب نبوده،
    دفترش خالی است — که هیچ چیزی دربارهٔ اجرا نمی‌گوید. پس فهرستِ
    پروسه‌های پروب‌دار جدا برمی‌گردد و UI باید بدونِ آن UNKNOWN بگوید، نه
    «یتیم». همان صفرِ جعلی است با لباسِ تازه.
    """
    out: dict = {"status": "ok"}

    # ── ۱) دسترسیِ زمانِ اجرا ────────────────────────────────────────────
    try:
        sys.path.insert(0, str(_OPS)) if str(_OPS) not in sys.path else None
        import reach_probe  # noqa: WPS433
        procs = reach_probe.probed_processes()
        hits = reach_probe.reached()
        by_proc: dict = {}
        for p, rows in procs.items():
            by_proc[p] = {"probes": len(rows),
                          "last_boot": max(float(r.get("ts") or 0) for r in rows)}
        out["reach"] = {
            "armed": reach_probe.enabled(),
            "probed_processes": by_proc,
            "functions_seen": len(hits),
            # ⚠️ نامِ فایل‌ها آری، نامِ توابع نه — فهرستِ کامل چند هزار ردیف
            # است و کارت را می‌کشد. شمارِ هر فایل کافی است تا بفهمی کدام
            # ماژول زنده است.
            "files": _reach_by_file(hits),
        }
    except Exception as exc:  # noqa: BLE001
        out["reach"] = {"status": "unknown", "reason": f"{type(exc).__name__}"}

    # ── ۲) حافظهٔ مغز: اسکن‌های ایستا با سنِ صریح ────────────────────────
    mem = _read_json_safe(STATE_DIR / "cockpit_brain" / "latest.json")
    if isinstance(mem, dict):
        now = time.time()
        scans = {}
        for key in ("dark", "orphan", "self"):
            ts = mem.get(f"_scan_{key}_ts")
            scans[key] = {
                "values": mem.get(f"_scan_{key}"),
                "age_s": round(now - float(ts), 1) if isinstance(ts, (int, float)) else None,
            }
        out["scans"] = scans
    else:
        # مغز هنوز ندویده یا حافظه‌اش خوانده نشد. **صفر نمی‌سازم.**
        out["scans"] = {"status": "unknown",
                        "reason": "cockpit_brain memory missing/unreadable"}

    # ── ۳) حافظهٔ بلندمدت: چیزی که تا امشب هیچ سطحی نشانش نمی‌داد ─────────
    # ⚠️ ۲۰۲۶-۰۸-۰۵ — یافتهٔ ممیزیِ «آیا اختاپوس داده ذخیره می‌کند؟»:
    # `memory.db` واقعاً می‌نویسد (رفعِ امشب: قدیمی‌ترین ۱۰ روز، ۲۸ ردیفِ
    # واقعی) ولی MemoryStore.metrics() — که از قبل ساخته و تست شده بود —
    # هیچ صداکنندهٔ تولیدی نداشت. همان الگوی کلِ این چند روز، این‌بار
    # روی خودِ حافظه.
    try:
        sys.path.insert(0, str(_OPS)) if str(_OPS) not in sys.path else None
        import memory.memory_store as _mst  # noqa: WPS433
        _store = _mst.MemoryStore()
        try:
            out["memory"] = _store.metrics()
        finally:
            _store.close()
    except Exception as exc:  # noqa: BLE001
        out["memory"] = {"status": "unknown", "reason": f"{type(exc).__name__}"}

    return _scrub_dict(out)


def _reach_by_file(hits) -> dict:
    """`file::qual` → شمارِ توابعِ دیده‌شده در هر فایل. سقفِ ۴۰ فایلِ اول."""
    from collections import Counter
    c = Counter()
    for h in hits:
        f = str(h).split("::", 1)[0]
        if f:
            c[f] += 1
    return dict(c.most_common(40))


def get_ops_leads(root: "Path | None" = None) -> dict:
    """`/api/ops/leads` — برشِ لیدها با همان نام‌کلیدهای /api/ops."""
    s = _engine_summary(root)
    if s.get("status") != "ok":
        return _scrub_dict({"status": s.get("status") or "error", "section": "leads",
                            "reason": s.get("reason"),
                            "leads_total": None, "lead_stages": None})
    return _scrub_dict({"status": "ok", "section": "leads",
                        "leads_total": s.get("leads_total"),
                        "lead_stages": s.get("lead_stages"),
                        "items": _ops_items("leads", _LEAD_COLS, "",
                                            "created_at DESC", root)})

def get_ops_tasks(root: "Path | None" = None) -> dict:
    """`/api/ops/tasks` — برشِ کارها با همان نام‌کلیدهای /api/ops."""
    s = _engine_summary(root)
    if s.get("status") != "ok":
        return _scrub_dict({"status": s.get("status") or "error", "section": "tasks",
                            "reason": s.get("reason"),
                            "tasks_total": None, "task_status": None})
    return _scrub_dict({"status": "ok", "section": "tasks",
                        "tasks_total": s.get("tasks_total"),
                        "task_status": s.get("task_status"),
                        # کارهای بسته‌شده بالای فهرست ننشینند — «باز» یعنی
                        # هرچه done نیست، نه فقط یک وضعِ نام‌برده.
                        "items": _ops_items("tasks", _TASK_COLS,
                                            "WHERE status != 'done'",
                                            "priority ASC, created_at DESC", root)})

def _cached(key: str, fn, root) -> dict:
    ttl = _cache_ttl()
    now = _mono()
    with _CACHE_LOCK:
        hit = _CACHE.get(key)
    if hit is not None and ttl > 0 and (now - hit[0]) < ttl:
        return hit[1]
    data = fn(root)                    # استثنا اصلاً به این‌جا نمی‌رسد ⇒ کش نمی‌شود
    with _CACHE_LOCK:
        if isinstance(data, dict) and data.get("status") == "ok":
            _CACHE[key] = (now, data)
        else:
            _CACHE.pop(key, None)
    return data

if __name__ == "__main__":
    # self-test: همه‌ی helpers را فراخوانی کن و خروجی JSON چاپ کن
    for name, fn in [("miniapp", get_miniapp_state), ("outbound", get_outbound_state),
                     ("approvals", get_approvals_state), ("legs", get_legs_state),
                     ("value", get_value_state), ("ops", get_ops_state), ("ui-registry", get_ui_registry),
                     ("current-truth", get_current_truth)]:
        print(f"=== {name} ===")
        print(json.dumps(fn(), ensure_ascii=False, indent=2)[:600])
        print()
