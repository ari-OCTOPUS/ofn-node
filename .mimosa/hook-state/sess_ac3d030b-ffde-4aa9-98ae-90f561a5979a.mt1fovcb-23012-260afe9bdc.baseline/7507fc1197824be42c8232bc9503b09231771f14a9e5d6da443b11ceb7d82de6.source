#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""instant_alert_bridge.py — چیزی که تا دایجستِ بعدی نباید صبر کند.

نقصِ ساختاری‌ای که این ماژول می‌بندد (تأییدشده در هر سه گزارشِ ۲۰۲۶-۰۷-۲۶):
اختاپوس هیچ مسیرِ «همین‌که اتفاق افتاد» ندارد. کورتکس 🔴 می‌شود، C6 فرضیهٔ تازه
می‌سازد، کارتی بدهکار می‌ماند — و همه تا دایجستِ ۶ساعته صف می‌شوند.

مرزِ عمدی: این پل **فقط چیزی را فوری می‌کند که فوریتش واقعی است.** «همه‌چیز
فوری» یعنی هیچ‌چیز فوری نیست، و در سیستمی که کمیاب‌ترین منبعش توجهِ مالک است،
آن بدتر از تأخیر است. پس فهرست کوتاه و هر عضوش با دلیل انتخاب شده.

طراحی:
  · throttle از `wiring._dialogue_gate` **قرض گرفته می‌شود، بازنویسی نمی‌شود**
    (قاعدهٔ مخزن: reuse نه rebuild). نبودِ wiring → پل no-opِ امن.
  · مسیر از `send_text(stream=…)` می‌رود، پس هر هشدار در تاپیکِ خودش می‌افتد و
    هر شکستِ مسیریابی به DM برمی‌گردد — نه به سکوت.
  · read-only نسبت به دادهٔ منبع: هیچ سیگنالی را مصرف/پاک نمی‌کند؛ فقط stateِ
    throttleِ خودش را می‌نویسد.
  · fail-soft مطلق: هیچ سیگنالی حق ندارد tick را بکشد.

پیش‌فرض خاموش (`OCTOPUS_TG_INSTANT`).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE / "budget"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import opslib  # noqa: E402

FLAG = "OCTOPUS_TG_INSTANT"
# کفِ فاصله برای هر سیگنال. عددها کوچک‌اند چون این‌ها *فوری*اند؛ ضدِflap واقعی
# در خودِ `_dialogue_gate` است (کفِ سختِ ۳۰۰ ثانیه در حالتِ force).
MIN_INTERVAL_S = 1800.0


def enabled() -> bool:
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def _gate():
    """(_dialogue_gate, _dialogue_mark) از wiring — یا (None, None)."""
    try:
        import wiring as _w  # noqa: WPS433
        return _w._dialogue_gate, _w._dialogue_mark  # noqa: SLF001
    except Exception:  # noqa: BLE001
        return None, None


def _read_json(rel: str):
    try:
        p = opslib.STATE_DIR / rel
        return json.loads(p.read_text("utf-8")) if p.exists() else None
    except (OSError, ValueError):
        return None


def _sha(s: str) -> str:
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()[:16]


# ─── سیگنال‌ها ───────────────────────────────────────────────────────────────
# هرکدام برمی‌گرداند: (متن, stream, hash) یا None. هیچ‌کدام چیزی نمی‌نویسد.

def _sig_fear() -> "tuple | None":
    """ترسِ واقعی: کورتکس یا استرسِ ارگانیسم 🔴 شده و کدام زیرسیستم در ترس است.

    چرا فوری: 🔴 یعنی یک زیرسیستم *الان* در وضعیتِ ترس است. شش ساعت بعد گفتنش
    گزارشِ تاریخ است، نه هشدار."""
    best = None
    for rel, label in (("cortex/cortisol-state.json", "کورتیزول"),
                       ("cortex/stress-latest.json", "استرس")):
        d = _read_json(rel)
        if not isinstance(d, dict):
            continue
        level = str(d.get("level") or "")
        if "🔴" not in level:
            continue
        who = [str(x) for x in (d.get("in_fear") or [])]
        best = (label, level, who, d.get("ts"))
        break
    if best is None:
        return None
    label, level, who, ts = best
    body = ("🔴 <b>ترس — همین حالا</b>\n"
            f"▸ {label}: {level}\n"
            f"▸ در ترس: {'، '.join(who) if who else 'مشخص نشده'}\n"
            f"▸ نکنی: تا دایجستِ بعدی کسی نمی‌گوید و خودش هم برنمی‌گردد\n"
            f"<i>جزئیات: /now</i>")
    return (body, "cortisol", _sha(f"fear|{level}|{sorted(who)}"))


def _sig_c6_new() -> "tuple | None":
    """فرضیهٔ تازهٔ خودبهبودی که هنوز آزمایش نشده.

    چرا فوری: صفِ C6 روزی یک آزمایش می‌دود. فرضیهٔ نو یعنی ارگانیسم چیزی در
    خودش دیده — و مالک باید بداند *چه چیزی* دیده، نه فقط نتیجه‌اش را فردا."""
    try:
        q = opslib.STATE_DIR / "c6" / "hypothesis-queue.jsonl"
        if not q.exists():
            return None
        rows = []
        for ln in q.read_text("utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                rows.append(json.loads(ln))
            except ValueError:
                continue
        pend = [r for r in rows if str(r.get("status") or "") == "PENDING"]
        if not pend:
            return None
        top = pend[0]
        probe = str(top.get("probe") or top.get("kind") or "?")
        q_txt = str(top.get("question") or top.get("hypothesis") or "")[:220]
        body = ("🔬 <b>یک چیزِ تازه در خودم دیدم</b>\n"
                f"▸ {q_txt}\n"
                f"▸ سنجه: {probe} · اندازه: {top.get('baseline_count')} "
                f"{top.get('unit', '')} (کف {top.get('floor')})\n"
                f"▸ نکنی: در صف می‌ماند تا آزمایشِ بعدی؛ چیزی خودکار عوض نمی‌شود\n"
                f"<i>{len(pend)} فرضیه در صف</i>")
        return (body, "c6", _sha(f"c6new|{top.get('id')}|{len(pend)}"))
    except Exception:  # noqa: BLE001
        return None


def _sig_card_debt() -> "tuple | None":
    """آزمایشی که تمام شد و حکمش هرگز نرسید — بدهیِ ۲۵ جولا، به‌عنوان سیگنال.

    چرا فوری: این دقیقاً کلاسِ نقصی است که یک شبانه‌روز نامرئی ماند. حالا خودش
    خبر می‌دهد."""
    try:
        import c6_trigger as _c6  # noqa: WPS433
        owed = _c6.pending_cards()
    except Exception:  # noqa: BLE001
        return None
    if not owed:
        return None
    body = ("📬 <b>نتیجه‌ای دارم که به دستت نرسیده</b>\n"
            f"▸ {len(owed)} آزمایشِ تمام‌شده هست که کارتش نرفته\n"
            f"▸ نکنی: همان‌جا می‌ماند؛ هیچ‌کس دوباره نمی‌فرستد\n"
            f"<i>نخستین: {str((owed[0] or {}).get('id'))[:40]}</i>")
    return (body, "c6", _sha(f"debt|{len(owed)}"))


SIGNALS = {
    "fear": _sig_fear,
    "c6_new": _sig_c6_new,
    "card_debt": _sig_card_debt,
}


# ─── حلقه ────────────────────────────────────────────────────────────────────
def check(channel=None, min_interval_s: float = MIN_INTERVAL_S) -> dict:
    """یک دورِ ارزیابیِ سیگنال‌ها. خروجی: شمارشِ صادق، هرگز استثنا."""
    if not enabled():
        return {"ran": False, "reason": "flag-off"}
    gate, mark = _gate()
    if gate is None or mark is None:
        return {"ran": False, "reason": "no-throttle"}
    if channel is None or not hasattr(channel, "send_text"):
        return {"ran": False, "reason": "no-channel"}
    sent, held, quiet, failed = [], [], [], []
    for name, fn in SIGNALS.items():
        try:
            out = fn()
        except Exception:  # noqa: BLE001 — یک سیگنالِ خراب بقیه را نمی‌کشد
            failed.append(name)
            continue
        if out is None:
            quiet.append(name)
            continue
        body, stream, sig_hash = out
        state_name = f"instant-{name}.json"
        try:
            if not gate(state_name, sig_hash, min_interval_s):
                held.append(name)
                continue
            ok = bool(channel.send_text(body, None, stream=stream))
        except TypeError:
            # channelِ قدیمی بدونِ stream — به DM بفرست، نه هیچ
            try:
                ok = bool(channel.send_text(body))
            except Exception:  # noqa: BLE001
                ok = False
        except Exception:  # noqa: BLE001
            ok = False
        if ok:
            try:
                mark(state_name, sig_hash)
            except Exception:  # noqa: BLE001
                pass
            sent.append(name)
        else:
            failed.append(name)
    return {"ran": True, "sent": sent, "held": held, "quiet": quiet,
            "failed": failed}


if __name__ == "__main__":  # pragma: no cover — پیش‌نمایشِ بی‌ارسال
    print(f"flag {FLAG} = {'on' if enabled() else 'off'}")
    for _n, _f in SIGNALS.items():
        try:
            _o = _f()
        except Exception as _e:  # noqa: BLE001
            print(f"\n--- {_n}: RAISED {type(_e).__name__}: {_e}")
            continue
        if _o is None:
            print(f"\n--- {_n}: ساکت (سیگنالی نیست)")
            continue
        print(f"\n--- {_n} → topic '{_o[1]}'\n{_o[0]}")
