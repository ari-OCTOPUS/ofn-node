"""tg_mining.py — UIِ تلگرامِ Mining برای تاپیکِ ⛏ (namespace ``mo:``).

خودبسنده: beat را از mining_os می‌سازد، متن + inline-keyboard (list-of-rows، هم‌قراردادِ
render.py) برمی‌گرداند. ``center.py`` این را فقط پشتِ فلگِ ``OCTOPUS_WIRE_MINING_UI`` صدا می‌زند.
callback_data همیشه ASCII و ≤64 بایت (قراردادِ center/تلگرام). verdict به لاگِ mining-owned
می‌رود؛ سینکِ canonical به VERDICT_QUEUE.md پیاده شد ولی فقط پشتِ فلگِ
``OCTOPUS_WIRE_MINING_VERDICT_SYNC`` (flag-off = دست‌نخورده)، append-only در یک بلوکِ
auto-managed با نشانگرِ BEGIN/END (هرگز دستکاریِ کورِ جدولِ انسانی).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from ..core import mining_beat
from ..state import load_state

_PKG = Path(__file__).resolve().parents[1]
_STATE_FILE = _PKG / "state" / "MINING-STATE.json"
_VERDICT_LOG = _PKG / "state" / "verdict-actions.jsonl"
_QUEUE_FILE = _PKG.parents[2] / "VERDICT_QUEUE.md"   # ریشهٔ vault (صفِ canonical مالک)
_SYNC_FLAG = "OCTOPUS_WIRE_MINING_VERDICT_SYNC"
_Q_BEGIN = "<!-- MINING-AUTO-VERDICTS:BEGIN (auto-managed by mining_os; do not edit inside) -->"
_Q_END = "<!-- MINING-AUTO-VERDICTS:END -->"

_PANES = ("fleet", "coins", "power", "dec", "risk", "report")
_BACK = [{"text": "🔙 منو", "callback_data": "mo:menu"}]


def current_beat() -> dict:
    """beatِ فعلی از MINING-STATE.json (نبود → skeleton صادق)."""
    return mining_beat(load_state(_STATE_FILE))


def _menu_kb(beat: dict) -> list:
    kb = [
        [{"text": "🛠 ناوگان", "callback_data": "mo:fleet"},
         {"text": "⛏ کوین‌ها", "callback_data": "mo:coins"}],
        [{"text": "🔋 برق", "callback_data": "mo:power"},
         {"text": "🧠 تصمیم‌ها", "callback_data": "mo:dec"}],
        [{"text": "⚠️ ریسک", "callback_data": "mo:risk"},
         {"text": "📊 گزارش", "callback_data": "mo:report"}],
    ]
    # D-014: دکمهٔ توقف (ثبتِ نیت، نه SSH). همیشه موجود چون مالک ممکن است بخواهد.
    kb.append([{"text": "⏹ توقفِ نودها", "callback_data": "mo:stop"}])
    # D-016: دکمه‌های swap فقط برای پیشنهادهای pending
    try:
        import sys as _sys
        _legs = str(_PKG.parents[2] / "_ops" / "legs")
        if _legs not in _sys.path:
            _sys.path.insert(0, _legs)
        from mining_swap_card import card_text as _sc  # noqa: WPS433
        _s = _sc()
        if _s:
            # کارتِ swap متن دارد ولی دکمه‌هایش را ما اینجا می‌سازیم
            from mining_swap_card import _load as _sload  # noqa: WPS433
            for d in _sload():
                if d.get("status") == "pending":
                    sid = d.get("id", "?")
                    fr = d.get("from", "?")
                    to = d.get("to", "?")
                    kb.append([{"text": f"💰 swap {fr}→{to} (تأیید)",
                                "callback_data": f"mo:swap:{sid}"}])
    except Exception:  # noqa: BLE001 — نباید منو را بکشد
        pass
    for vid in beat.get("open_verdict_ids", []):
        if vid and str(vid).isascii():
            kb.append([{"text": f"✅ {vid}", "callback_data": f"mo:vok:{vid}"},
                       {"text": f"❌ {vid}", "callback_data": f"mo:vno:{vid}"}])
    return kb


def render_menu():
    """(text, kb) برای /mining و mo:menu — کارتِ زنده + منوی ۶-گزینه‌ای."""
    beat = current_beat()
    f = beat.get("fleet", {})
    r = beat.get("readiness", {})
    halt = "⛔HALT" if beat.get("halt_proposal") else "OK"
    txt = (f"⛏ Mining · فاز {beat.get('phase', '?')}\n"
           f"نود {f.get('running', 0)}/{f.get('nodes_total', 0)} · برق {halt} · "
           f"آمادگی {r.get('score', 0)}٪ · live={beat.get('live')} ({beat.get('signal')})")
    return txt, _menu_kb(beat)


def render_pane(pane: str):
    """(text, kb) برای هر یک از ۶ pane. kb = فقط دکمهٔ بازگشت."""
    beat = current_beat()
    if pane == "fleet":
        f = beat.get("fleet", {})
        txt = (f"🛠 ناوگان\nکل {f.get('nodes_total', 0)} · running {f.get('running', 0)} · "
               f"broken {f.get('broken', 0)} · نامعلوم {f.get('unknown', 0)}\n"
               f"هشدارِ حرارت: {', '.join(map(str, f.get('thermal_warn', []))) or '—'}")
    elif pane == "coins":
        c = beat.get("coins", {})
        lines = "\n".join(f"• {t.get('symbol', '?')} ({t.get('survival_score', 0)})"
                          for t in c.get("top", [])) or "—"
        txt = f"⛏ کوین‌ها ({c.get('count', 0)} کاندید)\n{lines}"
    elif pane == "power":
        e = beat.get("electricity", {})
        txt = (f"🔋 برق\nگیت: {e.get('gate', '?')} — {e.get('reason', '')}\n"
               f"HALT: {'بله' if beat.get('halt_proposal') else 'نه'}")
    elif pane == "dec":
        txt = (f"🧠 تصمیم‌ها\nverdictهای باز: {beat.get('verdicts_open', 0)}\n"
               f"بلاکرها: {len(beat.get('blockers', []))}")
    elif pane == "risk":
        txt = ("⚠️ ریسک/خط‌قرمز\npropose-only · $0 · secrets=() · spawn=0\n"
               "D-10 صفر اجرای مالی · D-11 صفر wallet · D-20 صفر SSH · پول P7")
    else:  # report
        r = beat.get("readiness", {})
        reasons = "\n".join(f"• {x}" for x in r.get("reasons", [])) or "—"
        txt = f"📊 گزارش\nآمادگی {r.get('score', 0)}٪\n{reasons}"
    return txt, [_BACK]


def record_verdict(vid: str, decision: str) -> bool:
    """append به لاگِ mining-owned (fail-soft).

    VERDICT_QUEUE.md فقط وقتی لمس می‌شود که فلگِ ``OCTOPUS_WIRE_MINING_VERDICT_SYNC``
    روشن باشد؛ flag-off = رفتارِ قبلی (فقط jsonl، هیچ سینک).
    """
    try:
        _VERDICT_LOG.parent.mkdir(parents=True, exist_ok=True)
        rec = {"id": vid, "decision": decision, "source": "tg-mining",
               "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        with open(_VERDICT_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        return False
    # سینکِ canonical فقط پشتِ فلگ (flag-off = هیچ لمسِ VERDICT_QUEUE.md)
    if os.environ.get(_SYNC_FLAG) == "1":
        try:
            sync_verdicts_to_queue()
        except Exception:  # noqa: BLE001 — سینک هرگز نباید ثبتِ verdict را بشکند
            pass
    return True


def _load_latest_verdicts(verdict_log: Path) -> list:
    """آخرین decision به‌ازای هر id از jsonl (fail-soft؛ رکوردِ خراب نادیده)."""
    latest: dict = {}
    try:
        text = verdict_log.read_text(encoding="utf-8")
    except OSError:
        return []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except (ValueError, TypeError):
            continue
        vid = str(rec.get("id", "")).strip()
        if not vid:
            continue
        prev = latest.get(vid)
        if prev is None or str(rec.get("ts", "")) >= str(prev.get("ts", "")):
            latest[vid] = rec
    return [latest[k] for k in sorted(latest)]


def _render_verdict_block(records: list) -> str:
    """بلوکِ Markdownِ auto-managed (content-free: فقط id/فعل/منبع/زمان)."""
    dec_map = {"ok": "✅ ok", "no": "❌ no", "later": "⏳ later"}
    rows = [f"| {r.get('id', '?')} | {dec_map.get(str(r.get('decision', '')), '• ' + str(r.get('decision', '?')))}"
            f" | {r.get('source', '?')} | {r.get('ts', '?')} |" for r in records]
    body = "\n".join(rows) if rows else "| — | — | — | — |"
    return (f"{_Q_BEGIN}\n"
            "## Mining — Auto-Verdicts (mining_os)\n\n"
            "> خودکار از `mining_os/state/verdict-actions.jsonl` ساخته می‌شود — دستی ویرایش نکنید.\n"
            "> content-free (فقط id/فعل/منبع/زمان)؛ آخرین تصمیم به‌ازای هر id.\n\n"
            "| ID | verdict | منبع | آخرین‌زمان |\n"
            "|---|---|---|---|\n"
            f"{body}\n\n"
            f"{_Q_END}")


def sync_verdicts_to_queue(verdict_log: Path | None = None,
                           queue_path: Path | None = None) -> bool:
    """سینکِ canonical: آخرین verdictها → بلوکِ auto-managed در VERDICT_QUEUE.md.

    فقط داخلِ نشانگرهای BEGIN/END را جایگزین می‌کند؛ بقیهٔ فایل (جدولِ انسانی) دست‌نخورده
    می‌ماند. idempotent · atomic (tmp + os.replace) · fail-soft (هر خطا → False، هرگز crash).
    اگر فایلِ صف موجود نباشد، چیزی نمی‌سازد (return False).
    """
    verdict_log = verdict_log or _VERDICT_LOG
    queue_path = queue_path or _QUEUE_FILE
    try:
        if not queue_path.exists():
            return False
        block = _render_verdict_block(_load_latest_verdicts(verdict_log))
        text = queue_path.read_text(encoding="utf-8")
        i, j = text.find(_Q_BEGIN), text.find(_Q_END)
        if i != -1 and j != -1 and j > i:
            new_text = text[:i] + block + text[j + len(_Q_END):]
        else:
            sep = "" if text.endswith("\n") else "\n"
            new_text = f"{text}{sep}\n{block}\n"
        tmp = queue_path.with_name(queue_path.name + ".tmp")
        tmp.write_text(new_text, encoding="utf-8")
        os.replace(tmp, queue_path)
        return True
    except OSError:
        return False


def handle_callback(data: str):
    """(text, kb, toast) برای callbackِ mo:*. هرگز استثنا برنمی‌گرداند (center wrap دارد)."""
    if data.startswith("mo:vok:") or data.startswith("mo:vno:"):
        decision = "ok" if data.startswith("mo:vok:") else "no"
        vid = data.split(":", 2)[2] if data.count(":") >= 2 else "?"
        ok = record_verdict(vid, decision)
        txt, kb = render_menu()
        toast = (f"verdict {decision} ثبت شد: {vid}" if ok else "ثبت نشد (fail-soft)")
        return txt, kb, toast
    # ── D-014: ثبتِ نیتِ توقف (از مسیرِ ثبت، نه SSH — D-20) ─────────────────────
    # صادقانه: امروز هیچ نودی زنده نیست، پس «۰ نود تأیید کرد».
    if data == "mo:stop":
        toast = ""
        try:
            import sys as _sys
            _legs = str(_PKG.parents[2] / "_ops" / "legs")
            if _legs not in _sys.path:
                _sys.path.insert(0, _legs)
            from mining_stop_intent import register_stop_intent as _rsi  # noqa: WPS433
            r = _rsi(reason="owner tap: stop all nodes")
            acked = r.get("acked_count", 0)
            toast = f"ثبت شد · {acked} نود تأیید کرد"
        except Exception:  # noqa: BLE001 — نباید callback را بکشد
            toast = "ثبت نشد (fail-soft)"
        txt, kb = render_menu()
        return txt, kb, toast
    # ── D-016: تأییدِ یک‌ضربه‌ایِ swap (D-11: اجرا با خودت) ────────────────────────
    if data.startswith("mo:swap:"):
        sid = data.split(":", 2)[2] if data.count(":") >= 2 else "?"
        toast = ""
        try:
            import sys as _sys
            _legs = str(_PKG.parents[2] / "_ops" / "legs")
            if _legs not in _sys.path:
                _sys.path.insert(0, _legs)
            from mining_swap_card import owner_approved as _oa, owner_approval_text as _oat  # noqa: WPS433
            _oa(sid)
            toast = _oat(sid)   # صادقانه: «اجرا با خودت (D-11)»
        except Exception:  # noqa: BLE001
            toast = "ثبت نشد (fail-soft)"
        txt, kb = render_menu()
        return txt, kb, toast
    pane = data.split(":", 1)[1] if ":" in data else "menu"
    if pane in ("", "menu"):
        txt, kb = render_menu()
        return txt, kb, ""
    if pane in _PANES:
        txt, kb = render_pane(pane)
        return txt, kb, ""
    txt, kb = render_menu()
    return txt, kb, "نادیده"
